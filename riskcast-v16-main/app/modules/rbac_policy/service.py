"""
RBAC & Policy Service
Business logic for role-based access control and permission checking
RISKCAST V3 - Modular Monolith
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Callable
import logging
import functools
import inspect

from app.modules.rbac_policy.repository import RBACRepository
from app.modules.rbac_policy.schemas import RoleCreate, RoleUpdate, RoleResponse, PermissionCreate, PermissionResponse
from app.modules.rbac_policy.constants import (
    Permissions, has_permission, has_any_permission, has_all_permissions
)
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.shared.exceptions import NotFoundError, ForbiddenError

logger = logging.getLogger(__name__)


class RBACService:
    """Service for RBAC management"""
    
    def __init__(self, db: Session):
        self.repository = RBACRepository(db)
        self.db = db
    
    def create_role(self, role_data: RoleCreate) -> RoleResponse:
        """Create a new role"""
        role = self.repository.create_role(
            role_data.dict(exclude={"permission_ids"}),
            role_data.permission_ids
        )
        return RoleResponse.from_orm(role)
    
    def get_role(self, role_id: str) -> RoleResponse:
        """Get role by ID"""
        role = self.repository.get_role_by_id(role_id)
        if not role:
            raise NotFoundError("Role", role_id)
        return RoleResponse.from_orm(role)
    
    def list_roles(self, tenant_id: Optional[str] = None) -> List[RoleResponse]:
        """List roles"""
        roles = self.repository.list_roles(tenant_id)
        return [RoleResponse.from_orm(r) for r in roles]
    
    def create_permission(self, permission_data: PermissionCreate) -> PermissionResponse:
        """Create a new permission"""
        permission = self.repository.create_permission(permission_data.dict())
        return PermissionResponse.from_orm(permission)
    
    def list_permissions(self) -> List[PermissionResponse]:
        """List all permissions"""
        permissions = self.repository.list_permissions()
        return [PermissionResponse.from_orm(p) for p in permissions]
    
    def assign_role_to_user(self, user_id: str, role_id: str, assigned_by: Optional[str] = None) -> bool:
        """Assign role to user"""
        self.repository.assign_role_to_user(user_id, role_id, assigned_by)
        return True
    
    def check_permission(self, user_id: str, resource: str, action: str, tenant_id: Optional[str] = None) -> bool:
        """Check if user has permission"""
        return self.repository.user_has_permission(user_id, resource, action, tenant_id)


class PermissionChecker:
    """
    Permission checker for FastAPI dependencies.
    
    Checks if tenant context has required permissions.
    """
    
    def __init__(self, required_permissions: List[str], require_all: bool = True):
        """
        Initialize permission checker.
        
        Args:
            required_permissions: List of required permission keys
            require_all: If True, require all permissions. If False, require any permission.
        """
        self.required_permissions = required_permissions
        self.require_all = require_all
    
    async def __call__(self, context: TenantContext = Depends(resolve_tenant_context)) -> TenantContext:
        """
        Check if current context has required permissions.
        
        Args:
            context: Tenant context with permissions
            
        Returns:
            TenantContext if check passes
            
        Raises:
            HTTPException: If permissions are missing
        """
        if not self.required_permissions:
            return context
        
        user_permissions = context.permissions
        
        # Check permissions
        if self.require_all:
            # Require all permissions
            missing = []
            for perm in self.required_permissions:
                if not has_permission(user_permissions, perm):
                    missing.append(perm)
            
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing)}",
                    headers={"X-Required-Permissions": ", ".join(self.required_permissions)}
                )
        else:
            # Require any permission
            if not has_any_permission(user_permissions, self.required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission (need any of): {', '.join(self.required_permissions)}",
                    headers={"X-Required-Permissions": ", ".join(self.required_permissions)}
                )
        
        logger.debug(
            f"Permission check passed for {context.actor_type}/{context.actor_id} "
            f"in tenant {context.tenant_id}: {self.required_permissions}"
        )
        
        return context


def _check_permissions_all(permissions: List[str], context: TenantContext) -> TenantContext:
    """Internal function to check all permissions"""
    if not permissions:
        return context
    
    user_permissions = context.permissions
    
    # Check permissions - require all
    missing = []
    for perm in permissions:
        if not has_permission(user_permissions, perm):
            missing.append(perm)
    
    if missing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permissions: {', '.join(missing)}",
            headers={"X-Required-Permissions": ", ".join(permissions)}
        )
    
    logger.debug(
        f"Permission check passed for {context.actor_type}/{context.actor_id} "
        f"in tenant {context.tenant_id}: {permissions}"
    )
    
    return context


def require_permission(*permissions: str) -> Callable:
    """
    Dependency factory that checks for specific permissions (ALL required).
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            context: TenantContext = Depends(require_permission("risk:read", "risk:write"))
        ):
            ...
    
    Args:
        *permissions: Permission keys (all must be present)
        
    Returns:
        Callable function for FastAPI dependency
    """
    perms_list = list(permissions)
    checker = PermissionChecker(perms_list, require_all=True)
    
    # Create a proper async function that FastAPI can inspect
    async def check_permissions(context: TenantContext = Depends(resolve_tenant_context)) -> TenantContext:
        return await checker(context)
    
    # Copy attributes for better debugging
    check_permissions.__name__ = f"require_permission_{'_'.join(perms_list)}"
    check_permissions.__module__ = __name__
    
    return check_permissions


def _check_permissions_any(permissions: List[str], context: TenantContext) -> TenantContext:
    """Internal function to check any permission"""
    if not permissions:
        return context
    
    user_permissions = context.permissions
    
    # Check permissions - require any
    if not has_any_permission(user_permissions, permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission (need any of): {', '.join(permissions)}",
            headers={"X-Required-Permissions": ", ".join(permissions)}
        )
    
    logger.debug(
        f"Permission check passed for {context.actor_type}/{context.actor_id} "
        f"in tenant {context.tenant_id}: {permissions}"
    )
    
    return context


def require_any_permission(*permissions: str) -> Callable:
    """
    Dependency factory that checks for any of the specified permissions (OR logic).
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            context: TenantContext = Depends(require_any_permission("risk:read", "risk:write"))
        ):
            ...
    
    Args:
        *permissions: Permission keys (at least one must be present)
        
    Returns:
        Callable function for FastAPI dependency
    """
    perms_list = list(permissions)
    checker = PermissionChecker(perms_list, require_all=False)
    
    # Create a proper async function that FastAPI can inspect
    async def check_permissions(context: TenantContext = Depends(resolve_tenant_context)) -> TenantContext:
        return await checker(context)
    
    # Copy attributes for better debugging
    check_permissions.__name__ = f"require_any_permission_{'_'.join(perms_list)}"
    check_permissions.__module__ = __name__
    
    return check_permissions
