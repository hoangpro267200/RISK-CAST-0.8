"""
Authentication Models - User, Session, PasswordResetToken, EmailVerificationToken, APIKey

RISKCAST Auth System - Production Grade

IMPORTANT: Auth models use a SEPARATE declarative_base to avoid SQLAlchemy
class name conflicts with other modules (tenancy.User, tenant.Tenant, rbac.Role, etc.)

SECURITY CONSIDERATIONS:
- All tokens are stored as SHA-256 hashes (never plaintext)
- Password hashes use Argon2id (memory-hard, GPU-resistant)
- Sessions support rotation, revocation, and absolute expiry
- API keys are scoped and revocable
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Index, Enum, Text
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Optional, List, Set
from enum import Enum as PyEnum
import secrets
import hashlib
import uuid as uuid_module
import hmac

# IMPORTANT: Create a SEPARATE declarative base for auth models
# This prevents SQLAlchemy mapper conflicts with duplicate class names in other modules
AuthBase = declarative_base()

# Also keep reference to main Base for those who need it
try:
    from app.database import Base as MainBase
except ImportError:
    MainBase = None

# Alias for backward compatibility - but use AuthBase for auth models
Base = AuthBase


class AccountStatus(PyEnum):
    """Account status enumeration for user lifecycle management."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DELETED = "deleted"
    LOCKED = "locked"  # Locked due to security concerns (e.g., too many failed attempts)


class UserRole(PyEnum):
    """
    Built-in user roles for basic RBAC.
    For fine-grained permissions, use the RBAC module.
    """
    USER = "user"                   # Standard user
    OPERATOR = "operator"           # Can perform operations
    ANALYST = "analyst"             # Can view and analyze data
    UNDERWRITER = "underwriter"     # Can make underwriting decisions
    ADMIN = "admin"                 # Tenant administrator
    SUPER_ADMIN = "super_admin"     # Platform administrator


class AuthUser(Base):
    """
    AuthUser model for authentication.
    
    Stores user account information with secure password hashing.
    Note: Named AuthUser to avoid conflict with tenancy User model.
    
    Security Features:
    - UUID-based public ID for external references (prevents enumeration)
    - Email is indexed and unique (case-insensitive comparison should be done in queries)
    - Password hash uses Argon2id (memory-hard, resistant to GPU attacks)
    - Account status tracks lifecycle (active, suspended, deleted, etc.)
    - Role provides basic RBAC (for fine-grained, use RBAC module)
    - Tracks last login and failed attempts for security monitoring
    """
    __tablename__ = "auth_users"
    
    # Primary key (internal)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Public UUID (use this in APIs to prevent ID enumeration attacks)
    uuid = Column(String(36), unique=True, nullable=False, index=True, 
                  default=lambda: str(uuid_module.uuid4()))
    
    # Core identity
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Argon2id hash
    name = Column(String(255), nullable=True)
    
    # Account status and role
    status = Column(
        Enum(AccountStatus, values_callable=lambda x: [e.value for e in x]),
        default=AccountStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.USER.value,
        nullable=False,
        index=True
    )
    
    # Legacy fields (kept for backward compatibility)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Security tracking
    last_login_at = Column(DATETIME, nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 support
    failed_login_count = Column(Integer, default=0, nullable=False)
    last_failed_login_at = Column(DATETIME, nullable=True)
    locked_until = Column(DATETIME, nullable=True)  # Account lock expiry
    password_changed_at = Column(DATETIME, nullable=True)
    
    # Multi-tenancy support (optional)
    tenant_id = Column(String(36), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DATETIME, nullable=True)  # Soft delete support
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index("idx_auth_user_status_role", "status", "role"),
        Index("idx_auth_user_tenant", "tenant_id", "status"),
    )
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        # Handle both enum and string comparisons
        status = self.status
        if status == AccountStatus.LOCKED or status == AccountStatus.LOCKED.value or status == 'locked':
            return True
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    @property
    def is_active_account(self) -> bool:
        """Check if account is active and not locked/suspended/deleted."""
        # Handle both enum and string comparisons
        status = self.status
        is_active_status = (
            status == AccountStatus.ACTIVE or 
            status == AccountStatus.ACTIVE.value or
            status == 'active'
        )
        return (
            is_active_status and
            self.is_active and
            not self.is_locked and
            self.deleted_at is None
        )
    
    def record_login_success(self, ip_address: Optional[str] = None):
        """Record successful login - resets failed attempts."""
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        self.failed_login_count = 0
        self.last_failed_login_at = None
        # Clear lock if it was temporary
        if self.locked_until and self.locked_until <= datetime.utcnow():
            self.locked_until = None
            if self.status == AccountStatus.LOCKED.value:
                self.status = AccountStatus.ACTIVE.value
    
    def record_login_failure(self, max_attempts: int = 5, lockout_minutes: int = 15):
        """
        Record failed login attempt.
        Returns True if account is now locked.
        """
        self.failed_login_count += 1
        self.last_failed_login_at = datetime.utcnow()
        
        if self.failed_login_count >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            self.status = AccountStatus.LOCKED.value
            return True
        return False
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has the specified role or higher."""
        role_hierarchy = {
            UserRole.USER: 0,
            UserRole.OPERATOR: 1,
            UserRole.ANALYST: 2,
            UserRole.UNDERWRITER: 3,
            UserRole.ADMIN: 4,
            UserRole.SUPER_ADMIN: 5,
        }
        user_level = role_hierarchy.get(UserRole(self.role), 0)
        required_level = role_hierarchy.get(role, 0)
        return user_level >= required_level
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary for API response."""
        result = {
            "id": self.uuid,  # Return UUID, not internal ID
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "is_active": self.is_active_account,
            "email_verified": self.email_verified,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sensitive:
            # Only include in admin contexts
            result["internal_id"] = self.id
            result["tenant_id"] = self.tenant_id
            result["failed_login_count"] = self.failed_login_count
            result["is_locked"] = self.is_locked
        return result


# Alias for backward compatibility
User = AuthUser


class Session(Base):
    """
    Session model for tracking active user sessions.
    
    Each login creates a new session with a unique token stored in an HttpOnly cookie.
    
    Security Features:
    - Token stored as SHA-256 hash (never plaintext)
    - Supports idle timeout (sliding window) and absolute expiry
    - Tracks rotation chain for detecting token reuse attacks
    - Binds CSRF token to session for double-submit cookie pattern
    - Captures device fingerprint (user agent hash, IP prefix) for anomaly detection
    """
    __tablename__ = "auth_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Expiration management
    expires_at = Column(DATETIME, nullable=False, index=True)  # Idle expiry (sliding window)
    absolute_expires_at = Column(DATETIME, nullable=True, index=True)  # Absolute lifetime cap
    
    # Revocation tracking
    revoked_at = Column(DATETIME, nullable=True)
    revoke_reason = Column(String(128), nullable=True)  # e.g., "logout", "rotated", "security", "admin"
    
    # Session rotation chain (for detecting token reuse attacks)
    rotated_from_session_id = Column(Integer, nullable=True, index=True)
    rotated_to_session_id = Column(Integer, nullable=True)  # Forward pointer
    
    # CSRF binding
    csrf_token_hash = Column(String(64), nullable=True)
    
    # Activity tracking
    last_seen_at = Column(DATETIME, nullable=True, index=True)
    request_count = Column(Integer, default=0, nullable=False)  # Track usage
    
    # Device fingerprint (for anomaly detection)
    user_agent_hash = Column(String(64), nullable=True, index=True)
    ip_prefix = Column(String(64), nullable=True, index=True)  # Privacy-preserving
    user_agent = Column(String(500), nullable=True)  # Full UA for admin review
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    
    # Geolocation (optional, for security alerts)
    country_code = Column(String(2), nullable=True)
    
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("AuthUser", back_populates="sessions")
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index("idx_session_user_expires", "user_id", "expires_at"),
        Index("idx_session_valid", "token_hash", "revoked_at", "expires_at"),
    )
    
    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure session token.
        
        Uses secrets.token_urlsafe(32) which provides:
        - 256 bits of entropy
        - URL-safe base64 encoding (43 characters)
        - Suitable for secure session identifiers
        
        Returns:
            43-character URL-safe token
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a session token for storage in database.
        
        Uses SHA-256 which provides:
        - 256-bit output (64 hex characters)
        - Collision resistance
        - One-way function (cannot recover token from hash)
        
        Args:
            token: Plain session token
            
        Returns:
            SHA-256 hash (hex string, 64 chars)
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def hash_csrf(token: str) -> str:
        """Hash CSRF token for session binding."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def hash_user_agent(ua: str) -> str:
        """Hash user agent for fingerprinting (privacy-preserving)."""
        return hashlib.sha256(ua.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """
        Check if session is still valid.
        
        A session is invalid if:
        - It has been revoked
        - Idle timeout has passed (expires_at)
        - Absolute lifetime has passed (absolute_expires_at)
        """
        now = datetime.utcnow()
        if self.revoked_at is not None:
            return False
        if self.expires_at < now:
            return False
        if self.absolute_expires_at and self.absolute_expires_at < now:
            return False
        return True
    
    def revoke(self, reason: str = "logout"):
        """
        Revoke this session.
        
        Args:
            reason: Reason for revocation (logout, rotated, security, admin)
        """
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()
            self.revoke_reason = reason
    
    def refresh_idle_timeout(self, idle_hours: int = 48):
        """
        Refresh the idle timeout (sliding window).
        
        Called when user makes a request to extend session.
        Does NOT extend beyond absolute_expires_at.
        """
        now = datetime.utcnow()
        new_expires = now + timedelta(hours=idle_hours)
        
        # Don't extend beyond absolute expiry
        if self.absolute_expires_at and new_expires > self.absolute_expires_at:
            self.expires_at = self.absolute_expires_at
        else:
            self.expires_at = new_expires
        
        self.last_seen_at = now
        self.request_count += 1
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary for API response."""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_valid": self.is_valid(),
        }
        if include_sensitive:
            result["ip_address"] = self.ip_address
            result["country_code"] = self.country_code
            result["request_count"] = self.request_count
            result["revoke_reason"] = self.revoke_reason
        return result


class PasswordResetToken(Base):
    """
    Password reset token model.
    
    Stores one-time tokens for password reset flows.
    
    Security Features:
    - Token stored as SHA-256 hash
    - Single-use (marked used after consumption)
    - Short expiry (1 hour default)
    - Tracks IP for security auditing
    """
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DATETIME, nullable=False, index=True)
    used_at = Column(DATETIME, nullable=True)
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    
    # Security tracking
    requested_ip = Column(String(45), nullable=True)
    used_ip = Column(String(45), nullable=True)
    
    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure reset token.
        
        Returns:
            43-character URL-safe token
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a reset token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Check if token is still valid (not used and not expired)."""
        if self.used_at is not None:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        return True
    
    def mark_used(self, ip_address: Optional[str] = None):
        """Mark token as used."""
        if self.used_at is None:
            self.used_at = datetime.utcnow()
            self.used_ip = ip_address
    
    @staticmethod
    def create_for_user(
        user_id: int, 
        expires_in_hours: int = 1,
        requested_ip: Optional[str] = None
    ) -> tuple["PasswordResetToken", str]:
        """
        Create a new password reset token for a user.
        
        Args:
            user_id: User ID
            expires_in_hours: Token expiration time in hours (default: 1)
            requested_ip: IP address that requested the reset
            
        Returns:
            (PasswordResetToken instance, plain token string)
        """
        token = PasswordResetToken.generate_token()
        token_hash = PasswordResetToken.hash_token(token)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        reset_token = PasswordResetToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            requested_ip=requested_ip
        )
        
        return reset_token, token


class EmailVerificationToken(Base):
    """
    Email verification token model.
    
    Used to verify user email addresses after registration.
    
    Security Features:
    - Token stored as SHA-256 hash
    - Single-use
    - 24-hour expiry (longer than password reset for usability)
    """
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False)  # Email being verified (in case user changes it)
    expires_at = Column(DATETIME, nullable=False, index=True)
    verified_at = Column(DATETIME, nullable=True)
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    
    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure verification token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a verification token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Check if token is still valid (not used and not expired)."""
        if self.verified_at is not None:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        return True
    
    def mark_verified(self):
        """Mark email as verified."""
        if self.verified_at is None:
            self.verified_at = datetime.utcnow()
    
    @staticmethod
    def create_for_user(
        user_id: int,
        email: str,
        expires_in_hours: int = 24
    ) -> tuple["EmailVerificationToken", str]:
        """
        Create a new email verification token.
        
        Args:
            user_id: User ID
            email: Email address to verify
            expires_in_hours: Token expiration time in hours (default: 24)
            
        Returns:
            (EmailVerificationToken instance, plain token string)
        """
        token = EmailVerificationToken.generate_token()
        token_hash = EmailVerificationToken.hash_token(token)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        verification_token = EmailVerificationToken(
            token_hash=token_hash,
            user_id=user_id,
            email=email,
            expires_at=expires_at
        )
        
        return verification_token, token


class APIKeyScope(PyEnum):
    """Scopes for API key permissions."""
    READ = "read"           # Read-only access
    WRITE = "write"         # Read and write access
    ADMIN = "admin"         # Full administrative access
    WEBHOOK = "webhook"     # Webhook delivery only
    SERVICE = "service"     # Service-to-service communication


class APIKey(Base):
    """
    API Key model for service authentication.
    
    Used for:
    - Background jobs
    - Service-to-service communication
    - Third-party integrations
    - Webhook verification
    
    Security Features:
    - Key stored as SHA-256 hash (only prefix shown to user)
    - Scoped permissions
    - Expiration support
    - Usage tracking
    - Rate limiting support
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Key identification
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(8), nullable=False)  # First 8 chars for identification
    name = Column(String(255), nullable=False)  # Human-readable name
    description = Column(Text, nullable=True)
    
    # Ownership
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    
    # Permissions
    scope = Column(
        Enum(APIKeyScope, values_callable=lambda x: [e.value for e in x]),
        default=APIKeyScope.READ.value,
        nullable=False
    )
    permissions = Column(Text, nullable=True)  # JSON array of specific permissions
    
    # Restrictions
    allowed_ips = Column(Text, nullable=True)  # JSON array of allowed IP ranges
    allowed_origins = Column(Text, nullable=True)  # JSON array of allowed origins
    
    # Lifecycle
    expires_at = Column(DATETIME, nullable=True, index=True)
    revoked_at = Column(DATETIME, nullable=True)
    revoke_reason = Column(String(255), nullable=True)
    
    # Usage tracking
    last_used_at = Column(DATETIME, nullable=True)
    last_used_ip = Column(String(45), nullable=True)
    use_count = Column(Integer, default=0, nullable=False)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, nullable=True)  # None = no limit
    rate_limit_per_day = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("AuthUser", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index("idx_api_key_user_scope", "user_id", "scope"),
    )
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a cryptographically secure API key.
        
        Format: rk_[live|test]_[random]
        Example: rk_live_a1b2c3d4e5f6g7h8i9j0...
        
        Returns:
            Full API key string
        """
        random_part = secrets.token_urlsafe(32)
        return f"rk_live_{random_part}"
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @staticmethod
    def get_prefix(key: str) -> str:
        """Extract the prefix from an API key for identification."""
        return key[:8] if len(key) >= 8 else key
    
    def is_valid(self) -> bool:
        """Check if API key is still valid."""
        if self.revoked_at is not None:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def revoke(self, reason: str = "manual"):
        """Revoke this API key."""
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()
            self.revoke_reason = reason
    
    def record_usage(self, ip_address: Optional[str] = None):
        """Record API key usage."""
        self.last_used_at = datetime.utcnow()
        self.last_used_ip = ip_address
        self.use_count += 1
    
    def has_scope(self, required_scope: APIKeyScope) -> bool:
        """Check if API key has required scope."""
        scope_hierarchy = {
            APIKeyScope.READ: 0,
            APIKeyScope.WEBHOOK: 1,
            APIKeyScope.WRITE: 2,
            APIKeyScope.SERVICE: 3,
            APIKeyScope.ADMIN: 4,
        }
        key_level = scope_hierarchy.get(APIKeyScope(self.scope), 0)
        required_level = scope_hierarchy.get(required_scope, 0)
        return key_level >= required_level
    
    def get_permissions(self) -> Set[str]:
        """Get specific permissions as a set."""
        if not self.permissions:
            return set()
        try:
            import json
            return set(json.loads(self.permissions))
        except (json.JSONDecodeError, TypeError):
            return set()
    
    @staticmethod
    def create_for_user(
        user_id: int,
        name: str,
        scope: APIKeyScope = APIKeyScope.READ,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        tenant_id: Optional[str] = None,
        permissions: Optional[List[str]] = None,
    ) -> tuple["APIKey", str]:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            name: Human-readable name
            scope: Permission scope
            description: Optional description
            expires_in_days: Optional expiration in days
            tenant_id: Optional tenant ID
            permissions: Optional list of specific permissions
            
        Returns:
            (APIKey instance, plain key string)
        """
        import json
        
        key = APIKey.generate_key()
        key_hash = APIKey.hash_key(key)
        key_prefix = APIKey.get_prefix(key)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        permissions_json = None
        if permissions:
            permissions_json = json.dumps(permissions)
        
        api_key = APIKey(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            description=description,
            user_id=user_id,
            tenant_id=tenant_id,
            scope=scope.value,
            permissions=permissions_json,
            expires_at=expires_at
        )
        
        return api_key, key
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary for API response."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "key_prefix": self.key_prefix,
            "scope": self.scope,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_valid": self.is_valid(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "use_count": self.use_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            result["user_id"] = self.user_id
            result["tenant_id"] = self.tenant_id
            result["revoked_at"] = self.revoked_at.isoformat() if self.revoked_at else None
            result["revoke_reason"] = self.revoke_reason
        return result


class RefreshToken(Base):
    """
    Refresh token model for JWT-based authentication (optional).
    
    While the primary auth uses session cookies, this supports
    JWT refresh tokens for mobile apps or API clients.
    
    Security Features:
    - Token stored as SHA-256 hash
    - Rotation support (detect token reuse)
    - Device binding
    - Family tracking for revocation
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Token family for rotation tracking
    family_id = Column(String(36), nullable=False, index=True)
    
    # Lifecycle
    expires_at = Column(DATETIME, nullable=False, index=True)
    revoked_at = Column(DATETIME, nullable=True)
    revoke_reason = Column(String(128), nullable=True)
    
    # Rotation chain
    rotated_from_id = Column(Integer, nullable=True)
    
    # Device binding
    device_id = Column(String(64), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    
    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure refresh token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a refresh token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def generate_family_id() -> str:
        """Generate a unique family ID for token rotation tracking."""
        return str(uuid_module.uuid4())
    
    def is_valid(self) -> bool:
        """Check if refresh token is still valid."""
        if self.revoked_at is not None:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        return True
    
    def revoke(self, reason: str = "logout"):
        """Revoke this refresh token."""
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()
            self.revoke_reason = reason
    
    @staticmethod
    def create_for_user(
        user_id: int,
        expires_in_days: int = 30,
        device_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        family_id: Optional[str] = None,
        rotated_from_id: Optional[int] = None,
    ) -> tuple["RefreshToken", str]:
        """
        Create a new refresh token for a user.
        
        Args:
            user_id: User ID
            expires_in_days: Token expiration in days (default: 30)
            device_id: Optional device identifier
            user_agent: Optional user agent string
            ip_address: Optional IP address
            family_id: Token family ID (for rotation)
            rotated_from_id: Previous token ID (if rotating)
            
        Returns:
            (RefreshToken instance, plain token string)
        """
        token = RefreshToken.generate_token()
        token_hash = RefreshToken.hash_token(token)
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        refresh_token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            family_id=family_id or RefreshToken.generate_family_id(),
            expires_at=expires_at,
            device_id=device_id,
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address,
            rotated_from_id=rotated_from_id
        )
        
        return refresh_token, token
