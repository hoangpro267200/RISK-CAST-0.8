"""
Identity & Access Service
Business logic for authentication (login, sessions, API keys)
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy.orm import Session
from typing import Optional, Tuple
from datetime import datetime, timedelta
import secrets
import hashlib
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.modules.identity_access.models import Session, ApiKey, ApiKeyStatus
from app.modules.identity_access.schemas import (
    LoginRequest, LoginResponse, SessionResponse,
    ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse,
    TokenPayload, TokenValidationResult
)
from app.modules.tenancy.models import User, UserStatus
from app.modules.tenancy.repository import UserRepository
from app.modules.tenancy.exceptions import UserNotFoundError
from app.shared.exceptions import UnauthorizedError, ForbiddenError

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication and authorization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def _hash_token(self, token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def _create_jwt_token(self, user_id: str, tenant_id: Optional[str], session_id: str,
                         expires_delta: timedelta) -> str:
        """Create JWT token"""
        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    async def login(self, email: str, password: str, tenant_id: Optional[str] = None,
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> LoginResponse:
        """
        Authenticate user and create session.
        
        Args:
            email: User email
            password: User password
            tenant_id: Optional tenant ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            LoginResponse with session token
            
        Raises:
            UnauthorizedError: If credentials are invalid
            ForbiddenError: If user is disabled
        """
        # Find user by email
        user = self.user_repo.get_by_email(self.db, email)
        if not user:
            raise UnauthorizedError("Invalid email or password")
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        
        # Check user status
        if user.status != UserStatus.ACTIVE:
            raise ForbiddenError("User account is disabled")
        
        # Generate session token
        session_token = self._generate_session_token()
        token_hash = self._hash_token(session_token)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Create session
        session = Session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(session)
        
        # Update user last login
        user.last_login_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        
        # Create JWT token
        jwt_token = self._create_jwt_token(
            user_id=user.id,
            tenant_id=tenant_id,
            session_id=session.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        logger.info(f"User {user.id} logged in from {ip_address}")
        
        return LoginResponse(
            session_id=session.id,
            token=jwt_token,
            expires_at=expires_at,
            user_id=user.id,
            tenant_id=tenant_id
        )
    
    async def logout(self, session_id: str) -> None:
        """
        Invalidate session (logout).
        
        Args:
            session_id: Session ID
            
        Raises:
            NotFoundError: If session not found
        """
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            from app.shared.exceptions import NotFoundError
            raise NotFoundError("Session", session_id)
        
        # Delete session
        self.db.delete(session)
        self.db.commit()
        
        logger.info(f"Session {session_id} invalidated (logout)")
    
    async def validate_session(self, token: str) -> User:
        """
        Validate session token and return user.
        
        Args:
            token: Session token (JWT)
            
        Returns:
            User instance
            
        Raises:
            UnauthorizedError: If token is invalid or expired
        """
        try:
            # Decode JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            session_id = payload.get("session_id")
            user_id = payload.get("sub")
            
            if not session_id or not user_id:
                raise UnauthorizedError("Invalid token payload")
            
            # Get session
            session = self.db.query(Session).filter(Session.id == session_id).first()
            if not session:
                raise UnauthorizedError("Session not found")
            
            # Check expiration
            if session.is_expired:
                raise UnauthorizedError("Session expired")
            
            # Get user
            user = self.user_repo.get_by_id(self.db, user_id)
            if not user:
                raise UnauthorizedError("User not found")
            
            # Check user status
            if user.status != UserStatus.ACTIVE:
                raise ForbiddenError("User account is disabled")
            
            # Update last seen
            session.last_seen_at = datetime.utcnow()
            self.db.commit()
            
            return user
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise UnauthorizedError("Invalid token")
    
    async def create_api_key(
        self,
        tenant_id: str,
        data: ApiKeyCreate,
        creator_id: str
    ) -> Tuple[ApiKey, str]:
        """
        Create API key.
        
        Args:
            tenant_id: Tenant ID
            data: API key creation data
            creator_id: User ID who creates the key
            
        Returns:
            Tuple of (ApiKey instance, raw_key string)
            Raw key is shown only once and should be stored securely by client
            
        Raises:
            NotFoundError: If tenant or creator not found
        """
        # Generate API key
        # Format: sk_live_<random>
        random_part = secrets.token_urlsafe(32)
        raw_key = f"sk_live_{random_part}"
        key_prefix = f"sk_live_{random_part[:8]}..."
        
        # Hash key for storage
        key_hash = self._hash_token(raw_key)
        
        # Create API key
        api_key = ApiKey(
            tenant_id=tenant_id,
            name=data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes_json=data.scopes,
            status=ApiKeyStatus.ACTIVE,
            expires_at=data.expires_at,
            created_by_user_id=creator_id
        )
        
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        logger.info(f"Created API key {api_key.id} for tenant {tenant_id}")
        
        return api_key, raw_key
    
    async def validate_api_key(self, raw_key: str) -> Tuple[ApiKey, any]:
        """
        Validate API key and return key and tenant.
        
        Args:
            raw_key: Raw API key string
            
        Returns:
            Tuple of (ApiKey instance, Tenant instance)
            
        Raises:
            UnauthorizedError: If key is invalid, revoked, or expired
        """
        # Hash the provided key
        key_hash = self._hash_token(raw_key)
        
        # Find API key
        api_key = self.db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        if not api_key:
            raise UnauthorizedError("Invalid API key")
        
        # Check status
        if api_key.status != ApiKeyStatus.ACTIVE:
            raise UnauthorizedError("API key has been revoked")
        
        # Check expiration
        if api_key.is_expired:
            raise UnauthorizedError("API key has expired")
        
        # Get tenant
        from app.modules.tenancy.repository import TenantRepository
        tenant_repo = TenantRepository()
        tenant = tenant_repo.get_by_id(self.db, api_key.tenant_id)
        if not tenant:
            raise UnauthorizedError("Tenant not found")
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        self.db.commit()
        
        return api_key, tenant
    
    async def revoke_api_key(self, api_key_id: str, tenant_id: str) -> ApiKey:
        """
        Revoke an API key.
        
        Args:
            api_key_id: API key ID
            tenant_id: Tenant ID (for authorization check)
            
        Returns:
            Updated ApiKey instance
            
        Raises:
            NotFoundError: If API key not found
            ForbiddenError: If API key doesn't belong to tenant
        """
        api_key = self.db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
        if not api_key:
            from app.shared.exceptions import NotFoundError
            raise NotFoundError("ApiKey", api_key_id)
        
        if api_key.tenant_id != tenant_id:
            raise ForbiddenError("API key does not belong to this tenant")
        
        api_key.status = ApiKeyStatus.REVOKED
        self.db.commit()
        self.db.refresh(api_key)
        
        logger.info(f"Revoked API key {api_key_id}")
        
        return api_key
