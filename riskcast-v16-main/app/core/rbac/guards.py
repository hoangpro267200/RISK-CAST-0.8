"""
RBAC Guards
Decorators for permission checking in route handlers.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status

from app.shared.dependencies import resolve_tenant_context, TenantContext
from app.services.rbac_service import RBACService
from app.database import get_db


def require_permission(permission: str):
    """
    Decorator for route permission checking.
    
    Usage:
        @router.post("/endpoint")
        @require_permission("risk:write")
        async def create_assessment(...):
            ...
    
    Args:
        permission: Permission name (e.g., "risk:write")
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get database session from kwargs or create new
            db = kwargs.get('db')
            if not db:
                # Try to get from get_db dependency
                db_gen = get_db()
                db = next(db_gen)
                kwargs['db'] = db
            
            # Get tenant context
            context = kwargs.get('context')
            if not context:
                # Try to resolve from request
                request = kwargs.get('request')
                if request:
                    context = await resolve_tenant_context(
                        request=request,
                        db=db
                    )
                    kwargs['context'] = context
            
            if not context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tenant context required for permission checking"
                )
            
            # Check permission
            rbac_service = RBACService(db)
            
            # For API key auth, check permissions from context
            if context.actor_type == 'API_KEY':
                has_perm = permission in context.permissions
            else:
                # For user auth, check via RBAC service
                if not context.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User authentication required"
                    )
                has_perm = rbac_service.has_permission(
                    context.user_id,
                    context.tenant_id,
                    permission
                )
            
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission: {permission}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    Require at least one of the specified permissions.
    
    Usage:
        @router.get("/endpoint")
        @require_any_permission("risk:read", "risk:write")
        async def get_assessment(...):
            ...
    
    Args:
        *permissions: One or more permission names
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get database session
            db = kwargs.get('db')
            if not db:
                db_gen = get_db()
                db = next(db_gen)
                kwargs['db'] = db
            
            # Get tenant context
            context = kwargs.get('context')
            if not context:
                request = kwargs.get('request')
                if request:
                    context = await resolve_tenant_context(
                        request=request,
                        db=db
                    )
                    kwargs['context'] = context
            
            if not context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tenant context required for permission checking"
                )
            
            # Check permissions
            rbac_service = RBACService(db)
            has_any = False
            
            if context.actor_type == 'API_KEY':
                # Check in context permissions
                has_any = any(p in context.permissions for p in permissions)
            else:
                # Check via RBAC service
                if not context.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User authentication required"
                    )
                for perm in permissions:
                    if rbac_service.has_permission(
                        context.user_id,
                        context.tenant_id,
                        perm
                    ):
                        has_any = True
                        break
            
            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission. Need one of: {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_all_permissions(*permissions: str):
    """
    Require all of the specified permissions.
    
    Usage:
        @router.post("/endpoint")
        @require_all_permissions("risk:write", "audit:read")
        async def create_assessment(...):
            ...
    
    Args:
        *permissions: One or more permission names
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get database session
            db = kwargs.get('db')
            if not db:
                db_gen = get_db()
                db = next(db_gen)
                kwargs['db'] = db
            
            # Get tenant context
            context = kwargs.get('context')
            if not context:
                request = kwargs.get('request')
                if request:
                    context = await resolve_tenant_context(
                        request=request,
                        db=db
                    )
                    kwargs['context'] = context
            
            if not context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tenant context required for permission checking"
                )
            
            # Check permissions
            rbac_service = RBACService(db)
            missing_permissions = []
            
            if context.actor_type == 'API_KEY':
                # Check in context permissions
                for perm in permissions:
                    if perm not in context.permissions:
                        missing_permissions.append(perm)
            else:
                # Check via RBAC service
                if not context.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User authentication required"
                    )
                for perm in permissions:
                    if not rbac_service.has_permission(
                        context.user_id,
                        context.tenant_id,
                        perm
                    ):
                        missing_permissions.append(perm)
            
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
