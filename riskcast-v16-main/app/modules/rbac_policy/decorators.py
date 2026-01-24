"""
RBAC Permission Decorators
Decorator-based permission checking for FastAPI routes
RISKCAST V3 - Modular Monolith
"""
from functools import wraps
from typing import Callable, List
from fastapi import Request, HTTPException, status
import logging

from app.shared.dependencies import get_tenant_context
from app.modules.rbac_policy.constants import has_permission, has_any_permission, has_all_permissions

logger = logging.getLogger(__name__)


def permissions_required(*perms: str, require_all: bool = True):
    """
    Decorator that requires specific permissions.
    
    Usage:
        @router.get("/endpoint")
        @permissions_required("risk:read", "risk:write")
        async def endpoint(request: Request):
            ...
    
    Args:
        *perms: Permission keys required
        require_all: If True, require all permissions. If False, require any permission.
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get("request")
            
            if not request:
                raise ValueError("Request object not found in function arguments")
            
            # Get tenant context from request state
            context = get_tenant_context(request)
            if not context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tenant context not resolved"
                )
            
            user_permissions = context.permissions
            
            # Check permissions
            if require_all:
                # Require all permissions
                missing = []
                for perm in perms:
                    if not has_permission(user_permissions, perm):
                        missing.append(perm)
                
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required permissions: {', '.join(missing)}"
                    )
            else:
                # Require any permission
                if not has_any_permission(user_permissions, list(perms)):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required permission (need any of): {', '.join(perms)}"
                    )
            
            logger.debug(
                f"Permission check passed for {context.actor_type}/{context.actor_id}: {perms}"
            )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_all_permissions(*perms: str):
    """
    Decorator that requires ALL specified permissions.
    
    Usage:
        @router.get("/endpoint")
        @require_all_permissions("risk:read", "risk:write")
        async def endpoint(request: Request):
            ...
    """
    return permissions_required(*perms, require_all=True)


def require_any_permission(*perms: str):
    """
    Decorator that requires ANY of the specified permissions.
    
    Usage:
        @router.get("/endpoint")
        @require_any_permission("risk:read", "risk:write")
        async def endpoint(request: Request):
            ...
    """
    return permissions_required(*perms, require_all=False)


def check_permission(request: Request, permission: str) -> bool:
    """
    Helper function to check permission in route handlers.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(request: Request):
            if not check_permission(request, "risk:read"):
                raise HTTPException(403, "Permission denied")
            ...
    
    Args:
        request: FastAPI request object
        permission: Permission key to check
        
    Returns:
        True if user has permission
    """
    context = get_tenant_context(request)
    if not context:
        return False
    
    return has_permission(context.permissions, permission)
