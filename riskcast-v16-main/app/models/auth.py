"""
Authentication Models - User, Session, PasswordResetToken

RISKCAST Auth System - Phase 1
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Index
from sqlalchemy.dialects.mysql import VARCHAR, DATETIME
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
import hmac

# Use app.database.Base for consistency with database initialization
try:
    from app.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class User(Base):
    """
    User model for authentication.
    
    Stores user account information with secure password hashing.
    """
    __tablename__ = "auth_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Argon2 hash
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)  # Future: email verification
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary for API response."""
        result = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sensitive:
            # Only include in admin contexts
            result["password_hash"] = "***"  # Never expose actual hash
        return result


class Session(Base):
    """
    Session model for tracking active user sessions.
    
    Each login creates a new session with a unique token stored in an HttpOnly cookie.
    """
    __tablename__ = "auth_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DATETIME, nullable=False, index=True)  # idle expiry
    absolute_expires_at = Column(DATETIME, nullable=True, index=True)  # absolute lifetime
    revoked_at = Column(DATETIME, nullable=True)
    revoke_reason = Column(String(128), nullable=True)
    rotated_from_session_id = Column(Integer, nullable=True, index=True)
    csrf_token_hash = Column(String(64), nullable=True)
    last_seen_at = Column(DATETIME, nullable=True, index=True)
    user_agent_hash = Column(String(64), nullable=True, index=True)
    ip_prefix = Column(String(64), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    
    # Composite index for efficient lookups
    __table_args__ = (
        Index("idx_user_expires", "user_id", "expires_at"),
    )
    
    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure session token.
        
        Returns:
            43-character URL-safe token (secrets.token_urlsafe(32))
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a session token for storage in database.
        
        Args:
            token: Plain session token
            
        Returns:
            SHA-256 hash (hex string, 64 chars)
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def hash_csrf(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def hash_user_agent(ua: str) -> str:
        return hashlib.sha256(ua.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Check if session is still valid (not revoked and not expired)."""
        if self.revoked_at is not None:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        if self.absolute_expires_at and self.absolute_expires_at < datetime.utcnow():
            return False
        return True
    
    def revoke(self):
        """Revoke this session."""
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_valid": self.is_valid(),
        }


class PasswordResetToken(Base):
    """
    Password reset token model.
    
    Stores one-time tokens for password reset flows.
    Tokens expire after 1 hour and are single-use.
    """
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DATETIME, nullable=False, index=True)
    used_at = Column(DATETIME, nullable=True)
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    
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
    
    def mark_used(self):
        """Mark token as used."""
        if self.used_at is None:
            self.used_at = datetime.utcnow()
    
    @staticmethod
    def create_for_user(user_id: int, expires_in_hours: int = 1) -> tuple["PasswordResetToken", str]:
        """
        Create a new password reset token for a user.
        
        Args:
            user_id: User ID
            expires_in_hours: Token expiration time in hours (default: 1)
            
        Returns:
            (PasswordResetToken instance, plain token string)
        """
        token = PasswordResetToken.generate_token()
        token_hash = PasswordResetToken.hash_token(token)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        reset_token = PasswordResetToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at
        )
        
        return reset_token, token
