"""
RBAC & Policy Repository
Data access layer for role-based access control
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.modules.rbac_policy.models import Role, Permission, UserRole
from app.shared.exceptions import NotFoundError, ConflictError


class RBACRepository:
    """Repository for RBAC data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Role methods
    def create_role(self, role_data: dict, permission_ids: List[str] = None) -> Role:
        """Create a new role"""
        # Check if name exists
        existing = self.db.query(Role).filter(Role.name == role_data["name"]).first()
        if existing:
            raise ConflictError(f"Role '{role_data['name']}' already exists", resource="role")
        
        permissions = []
        if permission_ids:
            permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        
        role = Role(**role_data)
        role.permissions = permissions
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        return self.db.query(Role).filter(Role.name == name).first()
    
    def list_roles(self, tenant_id: Optional[str] = None) -> List[Role]:
        """List roles (optionally filtered by tenant)"""
        query = self.db.query(Role)
        if tenant_id:
            query = query.filter(
                (Role.tenant_id == tenant_id) | (Role.tenant_id.is_(None))
            )
        return query.all()
    
    # Permission methods
    def create_permission(self, permission_data: dict) -> Permission:
        """Create a new permission"""
        existing = self.db.query(Permission).filter(Permission.name == permission_data["name"]).first()
        if existing:
            raise ConflictError(f"Permission '{permission_data['name']}' already exists", resource="permission")
        
        permission = Permission(**permission_data)
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission
    
    def get_permission_by_id(self, permission_id: str) -> Optional[Permission]:
        """Get permission by ID"""
        return self.db.query(Permission).filter(Permission.id == permission_id).first()
    
    def list_permissions(self) -> List[Permission]:
        """List all permissions"""
        return self.db.query(Permission).all()
    
    # User-Role assignment
    def assign_role_to_user(self, user_id: str, role_id: str, assigned_by: Optional[str] = None,
                           expires_at: Optional[datetime] = None) -> UserRole:
        """Assign role to user"""
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        return user_role
    
    def get_user_roles(self, user_id: str, tenant_id: Optional[str] = None) -> List[Role]:
        """Get all roles for a user"""
        query = self.db.query(Role).join(UserRole).filter(
            UserRole.user_id == user_id,
            (UserRole.expires_at.is_(None) | (UserRole.expires_at > datetime.utcnow()))
        )
        if tenant_id:
            query = query.filter(
                (Role.tenant_id == tenant_id) | (Role.tenant_id.is_(None))
            )
        return query.all()
    
    def user_has_permission(self, user_id: str, resource: str, action: str,
                           tenant_id: Optional[str] = None) -> bool:
        """Check if user has permission"""
        roles = self.get_user_roles(user_id, tenant_id)
        for role in roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        return False
