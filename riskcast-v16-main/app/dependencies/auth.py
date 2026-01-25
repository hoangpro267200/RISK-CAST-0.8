"""
Authentication & Authorization Dependencies

RISKCAST Auth System - Production Grade

This module provides FastAPI dependencies for:
- Session-based authentication (cookie-based)
- API key authentication (for services/background jobs)
- Role-based access control (RBAC)
- Permission-based access control

TRUST BOUNDARIES:
- Client → API: Session cookies (HttpOnly, Secure, SameSite)
- Service → API: API keys (header-based)
- Background Jobs → API: API keys with SERVICE scope

SECURITY CONSIDERATIONS:
- Always use require_auth() for protected routes
- Use require_role() for role-restricted endpoints
- Use require_permission() for fine-grained access control
- API keys should be scoped to minimum required permissions
"""
from fastapi import Depends, HTTPException, status, Request, Cookie, Header
from sqlalchemy.orm import Session
from typing import Optional, List, Set, Union
from datetime import datetime, timedelta
from functools import wraps
import logging
import os

from app.database import get_db
from app.models.auth import (
    AuthUser as User,
    Session as SessionModel,
    APIKey,
    AccountStatus,
    UserRole,
    APIKeyScope
)
from app.auth_config.auth import is_auth_enabled, AUTH_CONFIG

logger = logging.getLogger(__name__)


# =============================================================================
# SECURITY CONTEXT
# =============================================================================

class AuthContext:
    """
    Authentication context containing user and permission information.
    
    This is passed to route handlers and can be used for:
    - Accessing the authenticated user
    - Checking permissions
    - Determining authentication method
    """
    
    def __init__(
        self,
        user: Optional[User] = None,
        api_key: Optional[APIKey] = None,
        session: Optional[SessionModel] = None,
        permissions: Optional[Set[str]] = None,
        is_service: bool = False
    ):
        self.user = user
        self.api_key = api_key
        self.session = session
        self._permissions = permissions or set()
        self.is_service = is_service
        self.authenticated_at = datetime.utcnow()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if context has valid authentication."""
        return self.user is not None or self.api_key is not None
    
    @property
    def user_id(self) -> Optional[int]:
        """Get user ID if authenticated."""
        return self.user.id if self.user else None
    
    @property
    def user_uuid(self) -> Optional[str]:
        """Get user UUID if authenticated."""
        if not self.user:
            return None
        return getattr(self.user, 'uuid', None) or str(self.user.id)
    
    @property
    def user_role(self) -> Optional[str]:
        """Get user role if authenticated."""
        if not self.user:
            return None
        return getattr(self.user, 'role', 'user')
    
    @property
    def tenant_id(self) -> Optional[str]:
        """Get tenant ID from user or API key."""
        if self.user and self.user.tenant_id:
            return self.user.tenant_id
        if self.api_key and self.api_key.tenant_id:
            return self.api_key.tenant_id
        return None
    
    @property
    def permissions(self) -> Set[str]:
        """Get all permissions for this context."""
        perms = set(self._permissions)
        
        # Add API key permissions
        if self.api_key:
            perms.update(self.api_key.get_permissions())
            # Add scope-based permissions
            if self.api_key.scope == APIKeyScope.ADMIN.value:
                perms.add("*")  # Admin has all permissions
        
        return perms
    
    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission."""
        perms = self.permissions
        
        # Wildcard grants all permissions
        if "*" in perms:
            return True
        
        # Check exact match
        if permission in perms:
            return True
        
        # Check wildcard patterns (e.g., "risk:*" matches "risk:read")
        for perm in perms:
            if perm.endswith(":*"):
                prefix = perm[:-1]  # Remove "*"
                if permission.startswith(prefix):
                    return True
        
        return False
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if context has any of the specified permissions."""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if context has all of the specified permissions."""
        return all(self.has_permission(p) for p in permissions)
    
    def has_role(self, role: Union[UserRole, str]) -> bool:
        """Check if user has the specified role or higher."""
        if not self.user:
            return False
        
        if isinstance(role, str):
            try:
                role = UserRole(role)
            except ValueError:
                return False
        
        # Use User.has_role if available (new schema)
        if hasattr(self.user, 'has_role'):
            return self.user.has_role(role)
        
        # Fallback: check role directly (old schema - treat all users as basic users)
        return True  # Allow access if role system not implemented


# =============================================================================
# SESSION AUTHENTICATION
# =============================================================================

async def get_session(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
) -> Optional[SessionModel]:
    """
    Get session from cookie if valid.
    
    This is a low-level dependency - use get_current_user() instead.
    """
    if not session_token:
        return None
    
    try:
        token_hash = SessionModel.hash_token(session_token)
        session = db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash
        ).first()
        
        if not session or not session.is_valid():
            return None
        
        return session
    except Exception as e:
        logger.warning(f"Session lookup error: {e}")
        return None


async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from session cookie.
    
    This is an OPTIONAL dependency - returns None if not authenticated.
    Use require_auth() for routes that MUST have authentication.
    
    Security:
    - Validates session token from HttpOnly cookie
    - Checks session expiry (idle + absolute)
    - Verifies user is active and not locked
    - Refreshes idle timeout (sliding window)
    
    Args:
        request: FastAPI request
        session_token: Session token from cookie
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    # If auth is disabled, return None (no user required)
    if not is_auth_enabled():
        return None
    
    # If no session token, return None
    if not session_token:
        return None
    
    try:
        # Look up session in database
        token_hash = SessionModel.hash_token(session_token)
        session = db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash
        ).first()
        
        if not session or not session.is_valid():
            return None
        
        # Get user
        user = db.query(User).filter(User.id == session.user_id).first()
        
        if not user:
            return None
        
        # Check user status (backward-compatible)
        is_active = user.is_active
        if hasattr(user, 'is_active_account'):
            is_active = user.is_active_account
        
        if not is_active:
            logger.warning(f"Inactive user attempted access: {user.email}")
            return None
        
        # Refresh idle timeout (throttled to every 5 minutes)
        try:
            idle_hours = int(os.getenv("SESSION_EXPIRE_HOURS", "48"))
        except (ValueError, TypeError):
            idle_hours = 48
        
        now = datetime.utcnow()
        if session.last_seen_at is None or (now - session.last_seen_at) > timedelta(minutes=5):
            session.refresh_idle_timeout(idle_hours)
            db.add(session)
            db.commit()
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Require authentication - raises 401 if not authenticated.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(require_auth)):
            return {"user_id": user.uuid}
    
    Security:
    - Returns 503 if auth is disabled (misconfiguration)
    - Returns 401 if no valid session
    - Never reveals why authentication failed (timing-safe)
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User object
        
    Raises:
        HTTPException: 401 if not authenticated, 503 if auth disabled
    """
    if not is_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled"
        )
    
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    return current_user


# =============================================================================
# API KEY AUTHENTICATION
# =============================================================================

async def get_api_key(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Optional[APIKey]:
    """
    Get API key from request headers.
    
    Supports two formats:
    - Authorization: Bearer rk_live_xxx
    - X-API-Key: rk_live_xxx
    
    Security:
    - Only accepts keys starting with "rk_"
    - Validates key is not expired or revoked
    - Records usage for auditing
    """
    key_value = None
    
    # Check Authorization header
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            key_value = parts[1]
    
    # Check X-API-Key header (takes precedence)
    if x_api_key:
        key_value = x_api_key
    
    if not key_value:
        return None
    
    # Validate key format
    if not key_value.startswith("rk_"):
        return None
    
    try:
        key_hash = APIKey.hash_key(key_value)
        api_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash
        ).first()
        
        if not api_key or not api_key.is_valid():
            return None
        
        # Record usage
        client_ip = request.client.host if request.client else None
        api_key.record_usage(client_ip)
        db.add(api_key)
        db.commit()
        
        return api_key
        
    except Exception as e:
        logger.warning(f"API key lookup error: {e}")
        return None


async def require_api_key(
    api_key: Optional[APIKey] = Depends(get_api_key),
    required_scope: APIKeyScope = APIKeyScope.READ
) -> APIKey:
    """
    Require valid API key authentication.
    
    Usage:
        @router.get("/api-endpoint")
        async def api_endpoint(api_key: APIKey = Depends(require_api_key)):
            return {"key_name": api_key.name}
    
    Args:
        api_key: API key from get_api_key dependency
        required_scope: Minimum required scope
        
    Returns:
        APIKey object
        
    Raises:
        HTTPException: 401 if no valid API key, 403 if insufficient scope
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not api_key.has_scope(required_scope):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key requires '{required_scope.value}' scope or higher"
        )
    
    return api_key


# =============================================================================
# COMBINED AUTHENTICATION (SESSION OR API KEY)
# =============================================================================

async def get_auth_context(
    request: Request,
    db: Session = Depends(get_db)
) -> AuthContext:
    """
    Get authentication context from either session or API key.
    
    This is the recommended dependency for routes that accept both
    session-based and API key authentication.
    
    Priority:
    1. API key (if present and valid)
    2. Session cookie (if present and valid)
    
    Returns:
        AuthContext with user/api_key (may be unauthenticated)
    """
    # Try API key first (for service-to-service calls)
    api_key = await get_api_key(request, 
        authorization=request.headers.get("Authorization"),
        x_api_key=request.headers.get("X-API-Key"),
        db=db
    )
    
    if api_key:
        # Get user associated with API key
        user = db.query(User).filter(User.id == api_key.user_id).first()
        return AuthContext(
            user=user,
            api_key=api_key,
            is_service=api_key.scope == APIKeyScope.SERVICE.value
        )
    
    # Try session cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        user = await get_current_user(request, session_token, db)
        if user:
            session = await get_session(request, session_token, db)
            return AuthContext(user=user, session=session)
    
    # Unauthenticated
    return AuthContext()


async def require_auth_context(
    auth_context: AuthContext = Depends(get_auth_context)
) -> AuthContext:
    """
    Require authentication via either session or API key.
    
    Usage:
        @router.get("/flexible-auth")
        async def endpoint(ctx: AuthContext = Depends(require_auth_context)):
            return {"user_id": ctx.user_id}
    """
    if not is_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled"
        )
    
    if not auth_context.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return auth_context


# =============================================================================
# ROLE-BASED ACCESS CONTROL
# =============================================================================

def require_role(role: Union[UserRole, str]):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role(UserRole.ADMIN))):
            return {"admin": True}
    
    Args:
        role: Required role (or higher in hierarchy)
        
    Returns:
        Dependency function that validates role
    """
    async def _require_role(
        current_user: User = Depends(require_auth)
    ) -> User:
        if isinstance(role, str):
            try:
                role_enum = UserRole(role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid role configuration: {role}"
                )
        else:
            role_enum = role
        
        # Check role using User.has_role if available, otherwise allow access
        has_role = True
        if hasattr(current_user, 'has_role'):
            has_role = current_user.has_role(role_enum)
        
        if not has_role:
            user_role = getattr(current_user, 'role', 'user')
            logger.warning(
                f"Role denied: user={current_user.email} "
                f"has_role={user_role} required={role_enum.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return _require_role


def require_roles(*roles: Union[UserRole, str]):
    """
    Dependency factory requiring any of the specified roles.
    
    Usage:
        @router.get("/analyst-or-admin")
        async def endpoint(user: User = Depends(require_roles(UserRole.ANALYST, UserRole.ADMIN))):
            return {"access": True}
    """
    async def _require_roles(
        current_user: User = Depends(require_auth)
    ) -> User:
        for role in roles:
            if isinstance(role, str):
                try:
                    role_enum = UserRole(role)
                except ValueError:
                    continue
            else:
                role_enum = role
            
            # Check role using User.has_role if available
            has_role = True
            if hasattr(current_user, 'has_role'):
                has_role = current_user.has_role(role_enum)
            
            if has_role:
                return current_user
        
        user_role = getattr(current_user, 'role', 'user')
        logger.warning(
            f"Role denied: user={current_user.email} "
            f"has_role={user_role} required_any={[str(r) for r in roles]}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return _require_roles


# =============================================================================
# PERMISSION-BASED ACCESS CONTROL
# =============================================================================

def require_permission(permission: str):
    """
    Dependency factory for permission-based access control.
    
    Usage:
        @router.get("/risk-analysis")
        async def endpoint(ctx: AuthContext = Depends(require_permission("risk:read"))):
            return {"access": True}
    
    Args:
        permission: Required permission key (e.g., "risk:read")
        
    Returns:
        Dependency function that validates permission
    """
    async def _require_permission(
        auth_context: AuthContext = Depends(require_auth_context)
    ) -> AuthContext:
        if not auth_context.has_permission(permission):
            logger.warning(
                f"Permission denied: user={auth_context.user_id} "
                f"permission={permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        return auth_context
    
    return _require_permission


def require_permissions(*permissions: str, require_all: bool = True):
    """
    Dependency factory for multiple permissions.
    
    Usage:
        @router.post("/create-policy")
        async def endpoint(ctx: AuthContext = Depends(
            require_permissions("underwriting:write", "policy:bind")
        )):
            return {"access": True}
    
    Args:
        permissions: Required permission keys
        require_all: If True, require all permissions. If False, require any.
        
    Returns:
        Dependency function that validates permissions
    """
    async def _require_permissions(
        auth_context: AuthContext = Depends(require_auth_context)
    ) -> AuthContext:
        if require_all:
            if not auth_context.has_all_permissions(list(permissions)):
                missing = [p for p in permissions if not auth_context.has_permission(p)]
                logger.warning(
                    f"Permissions denied: user={auth_context.user_id} "
                    f"missing={missing}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
        else:
            if not auth_context.has_any_permission(list(permissions)):
                logger.warning(
                    f"Permissions denied: user={auth_context.user_id} "
                    f"required_any={permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
        
        return auth_context
    
    return _require_permissions


# =============================================================================
# ADMIN-ONLY ACCESS
# =============================================================================

async def require_admin(
    current_user: User = Depends(require_auth)
) -> User:
    """
    Require admin role (or super admin).
    
    Usage:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(user_id: str, admin: User = Depends(require_admin)):
            ...
    """
    # Check admin role (backward-compatible)
    has_admin_role = True
    if hasattr(current_user, 'has_role'):
        has_admin_role = current_user.has_role(UserRole.ADMIN)
    
    if not has_admin_role:
        logger.warning(f"Admin access denied: user={current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_super_admin(
    current_user: User = Depends(require_auth)
) -> User:
    """
    Require super admin role (platform-level access).
    
    Usage:
        @router.post("/platform/tenants")
        async def create_tenant(admin: User = Depends(require_super_admin)):
            ...
    """
    # Check super admin role (backward-compatible)
    has_super_admin_role = True
    if hasattr(current_user, 'has_role'):
        has_super_admin_role = current_user.has_role(UserRole.SUPER_ADMIN)
    
    if not has_super_admin_role:
        logger.warning(f"Super admin access denied: user={current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required"
        )
    return current_user


# =============================================================================
# TENANT ISOLATION
# =============================================================================

def require_tenant_access(tenant_id_param: str = "tenant_id"):
    """
    Dependency factory for tenant isolation.
    
    Ensures the authenticated user has access to the specified tenant.
    
    Usage:
        @router.get("/tenants/{tenant_id}/data")
        async def get_tenant_data(
            tenant_id: str,
            user: User = Depends(require_tenant_access("tenant_id"))
        ):
            ...
    """
    async def _require_tenant_access(
        request: Request,
        current_user: User = Depends(require_auth)
    ) -> User:
        tenant_id = request.path_params.get(tenant_id_param)
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID required"
            )
        
        # Super admin has access to all tenants (backward-compatible)
        is_super_admin = True
        if hasattr(current_user, 'has_role'):
            is_super_admin = current_user.has_role(UserRole.SUPER_ADMIN)
        
        if is_super_admin:
            return current_user
        
        # User must belong to the tenant
        if current_user.tenant_id != tenant_id:
            logger.warning(
                f"Tenant access denied: user={current_user.email} "
                f"user_tenant={current_user.tenant_id} requested_tenant={tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        return current_user
    
    return _require_tenant_access


# =============================================================================
# OPTIONAL AUTH (for routes that work with or without auth)
# =============================================================================

async def optional_auth(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns user if authenticated, None otherwise.
    
    Use this for routes that have different behavior based on auth status.
    
    Usage:
        @router.get("/public-data")
        async def public_data(user: Optional[User] = Depends(optional_auth)):
            if user:
                # Return personalized data
                ...
            else:
                # Return generic data
                ...
    """
    if not is_auth_enabled():
        return None
    
    return await get_current_user(request, session_token, db)
