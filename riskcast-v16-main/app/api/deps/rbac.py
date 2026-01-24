"""
RBAC Dependencies
FastAPI dependencies for permission checking.
"""
from __future__ import annotations

from typing import Callable
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.shared.dependencies import resolve_tenant_context, TenantContext, get_current_user
from app.services.rbac_service import RBACService
from app.database import get_db
from app.modules.tenancy.models import User


def PermissionChecker(permission: str):
    """
    FastAPI dependency factory for permission checking.
    
    Usage:
        @router.post("/risk/assessments")
        async def create_assessment(
            ...,
            _: None = Depends(PermissionChecker("risk:write"))
        ):
            ...
    
    Args:
        permission: Permission name (e.g., "risk:write")
        
    Returns:
        FastAPI dependency function (not wrapped in Depends)
    """
    async def check(
        request: Request,
        context: TenantContext = Depends(resolve_tenant_context),
        db: Session = Depends(get_db)
    ) -> None:
        """
        Check if user has required permission.
        
        Raises:
            HTTPException: 403 if permission missing
        """
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
    
    return check


def AnyPermissionChecker(*permissions: str):
    """
    FastAPI dependency factory for checking any of multiple permissions.
    
    Usage:
        @router.get("/risk/assessments")
        async def list_assessments(
            ...,
            _: None = Depends(AnyPermissionChecker("risk:read", "risk:write"))
        ):
            ...
    
    Args:
        *permissions: One or more permission names
        
    Returns:
        FastAPI dependency function
    """
    async def check(
        request: Request,
        context: TenantContext = Depends(resolve_tenant_context),
        db: Session = Depends(get_db)
    ) -> None:
        """Check if user has at least one of the permissions"""
        rbac_service = RBACService(db)
        has_any = False
        
        if context.actor_type == 'API_KEY':
            has_any = any(p in context.permissions for p in permissions)
        else:
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
    
    return check


def AllPermissionsChecker(*permissions: str):
    """
    FastAPI dependency factory for checking all of multiple permissions.
    
    Usage:
        @router.post("/risk/assessments/export")
        async def export_assessments(
            ...,
            _: None = Depends(AllPermissionsChecker("risk:read", "audit:export"))
        ):
            ...
    
    Args:
        *permissions: One or more permission names
        
    Returns:
        FastAPI dependency function
    """
    async def check(
        request: Request,
        context: TenantContext = Depends(resolve_tenant_context),
        db: Session = Depends(get_db)
    ) -> None:
        """Check if user has all of the permissions"""
        rbac_service = RBACService(db)
        missing_permissions = []
        
        if context.actor_type == 'API_KEY':
            for perm in permissions:
                if perm not in context.permissions:
                    missing_permissions.append(perm)
        else:
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
    
    return check
