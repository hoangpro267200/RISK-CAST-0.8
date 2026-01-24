"""
RBAC Service
Service for role-based access control operations.
"""
from __future__ import annotations

from typing import Set, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.rbac import Role, Permission
from app.models.tenant import Membership, MembershipStatus
from app.shared.exceptions import NotFoundError


class RBACService:
    """Service for RBAC operations"""
    
    def __init__(self, db: Session):
        """
        Initialize RBAC service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_user_permissions(
        self,
        user_id: str,
        tenant_id: str
    ) -> Set[str]:
        """
        Get all permissions for a user in a tenant.
        
        Permissions come from:
        1. User's role in the tenant (from Membership)
        2. System roles (if user has system role membership)
        
        Args:
            user_id: User ID (UUID string)
            tenant_id: Tenant ID (UUID string)
            
        Returns:
            Set of permission names (e.g., {'risk:read', 'risk:write'})
        """
        permissions = set()
        
        # Get user's membership in tenant
        membership = (
            self.db.query(Membership)
            .filter(
                and_(
                    Membership.user_id == user_id,
                    Membership.tenant_id == tenant_id,
                    Membership.status == MembershipStatus.ACTIVE
                )
            )
            .first()
        )
        
        if not membership:
            # No active membership - return empty set
            return permissions
        
        # Get role by name (could be tenant-specific or system role)
        role = self._get_role_by_name(membership.role, tenant_id)
        
        if role:
            # Get permissions from role
            for permission in role.permissions:
                permissions.add(permission.name)
        
        return permissions
    
    def has_permission(
        self,
        user_id: str,
        tenant_id: str,
        permission: str
    ) -> bool:
        """
        Check if user has a specific permission in tenant.
        
        Args:
            user_id: User ID (UUID string)
            tenant_id: Tenant ID (UUID string)
            permission: Permission name (e.g., 'risk:read')
            
        Returns:
            True if user has permission, False otherwise
        """
        user_permissions = self.get_user_permissions(user_id, tenant_id)
        return permission in user_permissions
    
    def assign_role(
        self,
        user_id: str,
        tenant_id: str,
        role_name: str
    ) -> None:
        """
        Assign a role to a user in a tenant.
        
        Creates or updates the membership with the specified role.
        
        Args:
            user_id: User ID (UUID string)
            tenant_id: Tenant ID (UUID string)
            role_name: Role name (e.g., 'admin', 'viewer')
            
        Raises:
            NotFoundError: If role not found
        """
        # Verify role exists (tenant-specific or system role)
        role = self._get_role_by_name(role_name, tenant_id)
        if not role:
            raise NotFoundError(
                resource="role",
                resource_id=role_name,
                detail=f"Role '{role_name}' not found for tenant {tenant_id}"
            )
        
        # Get or create membership
        membership = (
            self.db.query(Membership)
            .filter(
                and_(
                    Membership.user_id == user_id,
                    Membership.tenant_id == tenant_id
                )
            )
            .first()
        )
        
        if membership:
            # Update existing membership
            membership.role = role_name
            membership.status = MembershipStatus.ACTIVE
        else:
            # Create new membership
            membership = Membership(
                user_id=user_id,
                tenant_id=tenant_id,
                role=role_name,
                status='ACTIVE'
            )
            self.db.add(membership)
        
        self.db.commit()
    
    def _get_role_by_name(
        self,
        role_name: str,
        tenant_id: Optional[str] = None
    ) -> Optional[Role]:
        """
        Get role by name, checking tenant-specific first, then system roles.
        
        Args:
            role_name: Role name
            tenant_id: Optional tenant ID (for tenant-specific roles)
            
        Returns:
            Role instance or None if not found
        """
        # First, try tenant-specific role
        if tenant_id:
            role = (
                self.db.query(Role)
                .filter(
                    and_(
                        Role.name == role_name,
                        Role.tenant_id == tenant_id
                    )
                )
                .first()
            )
            if role:
                return role
        
        # Fall back to system role
        role = (
            self.db.query(Role)
            .filter(
                and_(
                    Role.name == role_name,
                    Role.is_system_role == True
                )
            )
            .first()
        )
        
        return role
    
    def get_role_permissions(self, role_name: str, tenant_id: Optional[str] = None) -> Set[str]:
        """
        Get permissions for a role.
        
        Args:
            role_name: Role name
            tenant_id: Optional tenant ID (for tenant-specific roles)
            
        Returns:
            Set of permission names
        """
        role = self._get_role_by_name(role_name, tenant_id)
        if not role:
            return set()
        
        return {p.name for p in role.permissions}
    
    def list_roles(self, tenant_id: Optional[str] = None, include_system: bool = True) -> List[Role]:
        """
        List available roles.
        
        Args:
            tenant_id: Optional tenant ID (to filter tenant-specific roles)
            include_system: Whether to include system roles
            
        Returns:
            List of Role instances
        """
        query = self.db.query(Role)
        
        if tenant_id:
            # Include tenant-specific roles and optionally system roles
            if include_system:
                query = query.filter(
                    or_(
                        Role.tenant_id == tenant_id,
                        Role.is_system_role == True
                    )
                )
            else:
                query = query.filter(Role.tenant_id == tenant_id)
        else:
            # No tenant filter - return all or just system roles
            if include_system:
                query = query.filter(Role.is_system_role == True)
            else:
                # No roles if no tenant and not including system
                return []
        
        return query.all()
    
    def list_permissions(self) -> List[Permission]:
        """
        List all permissions.
        
        Returns:
            List of Permission instances
        """
        return self.db.query(Permission).all()
