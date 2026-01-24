"""
Shared FastAPI Dependencies
Tenant context resolution and authentication
RISKCAST V3 - Modular Monolith
"""
from dataclasses import dataclass
from fastapi import Request, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional, List, Set
import logging

from app.database import get_db
from app.config import settings
from app.modules.identity_access.service import AuthService
from app.modules.identity_access.models import ActorType
from app.modules.tenancy.models import User, Membership, MembershipStatus
from app.modules.tenancy.repository import MembershipRepository
from app.modules.tenancy.repository import TenantRepository
from app.shared.exceptions import UnauthorizedError, ForbiddenError, NotFoundError

logger = logging.getLogger(__name__)

# Import observability functions (with fallback if not available)
try:
    from app.modules.observability.logging import set_request_context
except ImportError:
    # Fallback if observability module not available
    def set_request_context(**kwargs):
        pass


@dataclass
class TenantContext:
    """Tenant context with user, membership, and permissions"""
    tenant_id: str
    user_id: Optional[str]
    membership_id: Optional[str]
    role_names: List[str]
    permissions: Set[str]
    actor_type: str  # 'USER' or 'API_KEY'
    actor_id: str


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extract and validate user from session token or API key.
    
    Checks:
    1. Authorization header with Bearer token (session auth)
    2. X-API-Key header (API key auth)
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User instance if authenticated, None otherwise
        
    Raises:
        UnauthorizedError: If token/key is invalid
    """
    auth_service = AuthService(db)
    
    # Check for Bearer token (session auth)
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.replace("Bearer ", "")
            user = await auth_service.validate_session(token)
            # Store actor info in request state
            request.state.actor_type = ActorType.USER.value
            request.state.actor_id = user.id
            return user
        except Exception as e:
            logger.warning(f"Session token validation failed: {e}")
            raise UnauthorizedError("Invalid or expired session token")
    
    # Check for API key (API key auth)
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        try:
            api_key, tenant = await auth_service.validate_api_key(api_key_header)
            # Store actor info in request state
            request.state.actor_type = ActorType.API_KEY.value
            request.state.actor_id = api_key.id
            request.state.api_key = api_key
            request.state.api_key_tenant = tenant
            # API key auth doesn't have a user
            return None
        except Exception as e:
            logger.warning(f"API key validation failed: {e}")
            raise UnauthorizedError("Invalid or expired API key")
    
    # No authentication provided
    return None


async def resolve_tenant_context(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
) -> TenantContext:
    """
    Resolve tenant context from request.
    
    For session auth:
    - Read X-Tenant-Id header
    - Validate user has active membership in tenant
    - Load permissions from membership role
    
    For API key auth:
    - Tenant comes from API key
    - Permissions come from API key scopes
    
    Store in request.state for downstream use.
    
    Args:
        request: FastAPI request object
        db: Database session
        user: Authenticated user (None for API key auth)
        
    Returns:
        TenantContext with tenant, user, membership, and permissions
        
    Raises:
        UnauthorizedError: If authentication required but not provided
        ForbiddenError: If user doesn't have access to tenant
        NotFoundError: If tenant or membership not found
    """
    membership_repo = MembershipRepository()
    tenant_repo = TenantRepository()
    
    # Determine actor type
    actor_type = getattr(request.state, "actor_type", None)
    actor_id = getattr(request.state, "actor_id", None)
    
    if not actor_type:
        raise UnauthorizedError("Authentication required")
    
    # Handle API key auth
    if actor_type == ActorType.API_KEY.value:
        api_key = getattr(request.state, "api_key", None)
        tenant = getattr(request.state, "api_key_tenant", None)
        
        if not api_key or not tenant:
            raise UnauthorizedError("Invalid API key context")
        
        # Get permissions from API key scopes
        permissions = set(api_key.scopes_json or [])
        role_names = []  # API keys don't have roles
        
        context = TenantContext(
            tenant_id=tenant.id,
            user_id=None,
            membership_id=None,
            role_names=role_names,
            permissions=permissions,
            actor_type=actor_type,
            actor_id=api_key.id
        )
        
        # Store in request state
        request.state.tenant_id = context.tenant_id
        request.state.actor_type = context.actor_type
        request.state.actor_id = context.actor_id
        request.state.permissions = context.permissions
        request.state.tenant_context = context
        
        return context
    
    # Handle session auth (user)
    if not user:
        raise UnauthorizedError("User authentication required")
    
    # Get tenant ID from header
    x_tenant_id = request.headers.get("X-Tenant-Id")
    
    if not x_tenant_id:
        # Try to get from default tenant if isolation disabled
        if not settings.TENANT_ISOLATION_ENABLED and settings.DEFAULT_TENANT_ID:
            x_tenant_id = settings.DEFAULT_TENANT_ID
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Tenant-Id header is required"
            )
    
    # Validate tenant exists
    tenant = tenant_repo.get_by_id(db, x_tenant_id)
    if not tenant:
        raise NotFoundError("Tenant", x_tenant_id)
    
    # Get user's membership in tenant
    membership = membership_repo.get_membership(db, x_tenant_id, user.id)
    
    if not membership:
        raise ForbiddenError(f"User {user.id} is not a member of tenant {x_tenant_id}")
    
    if membership.status != MembershipStatus.ACTIVE:
        raise ForbiddenError(f"Membership is not active (status: {membership.status.value})")
    
    # Get permissions from membership role
    permissions = membership_repo.get_user_permissions(db, x_tenant_id, user.id)
    
    # Get role names from membership
    # Eager load role relationship
    from sqlalchemy.orm import joinedload
    membership_with_role = db.query(Membership).options(
        joinedload(Membership.role)
    ).filter(Membership.id == membership.id).first()
    
    role_names = []
    if membership_with_role and membership_with_role.role:
        role_names = [membership_with_role.role.name]
    
    context = TenantContext(
        tenant_id=x_tenant_id,
        user_id=user.id,
        membership_id=membership.id,
        role_names=role_names,
        permissions=permissions,
        actor_type=actor_type,
        actor_id=user.id
    )
    
    # Store in request state
    request.state.tenant_id = context.tenant_id
    request.state.user_id = context.user_id
    request.state.actor_type = context.actor_type
    request.state.actor_id = context.actor_id
    request.state.permissions = context.permissions
    request.state.membership_id = context.membership_id
    request.state.tenant_context = context
    
    # Update observability context (tenant_id and actor_id)
    set_request_context(
        tenant_id=context.tenant_id,
        actor_id=context.actor_id
    )
    
    return context


def require_tenant() -> TenantContext:
    """
    Dependency that ensures tenant context is resolved.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(context: TenantContext = Depends(require_tenant)):
            ...
    """
    return Depends(resolve_tenant_context)


def require_user() -> User:
    """
    Dependency that requires authenticated user.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(user: User = Depends(require_user)):
            ...
    """
    async def _require_user(
        request: Request,
        db: Session = Depends(get_db)
    ) -> User:
        user = await get_current_user(request, db)
        if not user:
            raise UnauthorizedError("User authentication required")
        return user
    
    return Depends(_require_user)


def require_permission(permission: str):
    """
    Dependency factory that requires specific permission.
    
    DEPRECATED: Use app.modules.rbac_policy.service.require_permission() instead.
    This is kept for backward compatibility.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(context: TenantContext = Depends(require_permission("risk:read"))):
            ...
    """
    async def _require_permission(
        context: TenantContext = Depends(require_tenant())
    ) -> TenantContext:
        from app.modules.rbac_policy.constants import has_permission
        if not has_permission(context.permissions, permission):
            raise ForbiddenError(f"Permission required: {permission}")
        return context
    
    return Depends(_require_permission)


def get_tenant_context(request: Request) -> Optional[TenantContext]:
    """
    Get tenant context from request state.
    
    Use this in route handlers to access tenant context without dependency injection.
    
    Args:
        request: FastAPI request object
        
    Returns:
        TenantContext if resolved, None otherwise
    """
    return getattr(request.state, "tenant_context", None)
