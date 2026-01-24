"""
Tenancy Repository
Data access layer for tenant, user, and membership management
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import Optional, List, Set, Dict, Any
from datetime import datetime

from app.modules.tenancy.models import (
    Tenant, User, Membership, Role, Permission, RolePermission,
    TenantStatus, UserStatus, MembershipStatus
)
from app.shared.exceptions import NotFoundError, ConflictError


class TenantRepository:
    """Repository for tenant data access"""
    
    def create(self, db: Session, tenant_data: Dict[str, Any]) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            db: Database session
            tenant_data: Dictionary with tenant data
            
        Returns:
            Created Tenant instance
            
        Raises:
            ConflictError: If tenant name already exists
        """
        # Check if name exists
        existing = db.query(Tenant).filter(Tenant.name == tenant_data["name"]).first()
        if existing:
            raise ConflictError(
                f"Tenant with name '{tenant_data['name']}' already exists",
                resource="tenant"
            )
        
        tenant = Tenant(**tenant_data)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant
    
    def get_by_id(self, db: Session, tenant_id: str) -> Optional[Tenant]:
        """
        Get tenant by ID.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            Tenant instance or None
        """
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[Tenant]:
        """
        Get tenant by name.
        
        Args:
            db: Database session
            name: Tenant name
            
        Returns:
            Tenant instance or None
        """
        return db.query(Tenant).filter(Tenant.name == name).first()
    
    def update(self, db: Session, tenant_id: str, data: Dict[str, Any]) -> Tenant:
        """
        Update tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            data: Dictionary with fields to update
            
        Returns:
            Updated Tenant instance
            
        Raises:
            NotFoundError: If tenant not found
            ConflictError: If new name conflicts with existing tenant
        """
        tenant = self.get_by_id(db, tenant_id)
        if not tenant:
            raise NotFoundError("Tenant", tenant_id)
        
        # Check name conflict if name is being updated
        if "name" in data and data["name"] != tenant.name:
            existing = self.get_by_name(db, data["name"])
            if existing:
                raise ConflictError(
                    f"Tenant with name '{data['name']}' already exists",
                    resource="tenant"
                )
        
        # Update fields
        for key, value in data.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tenant)
        return tenant
    
    def list_all(self, db: Session, filters: Optional[Dict[str, Any]] = None, 
                 skip: int = 0, limit: int = 100) -> List[Tenant]:
        """
        List all tenants with optional filters.
        
        Args:
            db: Database session
            filters: Dictionary with filter criteria
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Tenant instances
        """
        query = db.query(Tenant)
        
        if filters:
            if filters.get("status"):
                query = query.filter(Tenant.status == filters["status"])
            
            if filters.get("subscription_tier"):
                query = query.filter(Tenant.subscription_tier == filters["subscription_tier"])
            
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(Tenant.name.like(search_term))
        
        return query.order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()


class UserRepository:
    """Repository for user data access"""
    
    def create(self, db: Session, user_data: Dict[str, Any]) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: Dictionary with user data (must include password_hash)
            
        Returns:
            Created User instance
            
        Raises:
            ConflictError: If email already exists
        """
        # Check if email exists
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            raise ConflictError(
                f"User with email '{user_data['email']}' already exists",
                resource="user"
            )
        
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def get_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User instance or None
        """
        return db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User instance or None
        """
        return db.query(User).filter(User.email == email).first()
    
    def update(self, db: Session, user_id: str, data: Dict[str, Any]) -> User:
        """
        Update user.
        
        Args:
            db: Database session
            user_id: User ID
            data: Dictionary with fields to update
            
        Returns:
            Updated User instance
            
        Raises:
            NotFoundError: If user not found
            ConflictError: If new email conflicts with existing user
        """
        user = self.get_by_id(db, user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        # Check email conflict if email is being updated
        if "email" in data and data["email"] != user.email:
            existing = self.get_by_email(db, data["email"])
            if existing:
                raise ConflictError(
                    f"User with email '{data['email']}' already exists",
                    resource="user"
                )
        
        # Update fields
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user


class MembershipRepository:
    """Repository for membership data access"""
    
    def create(self, db: Session, membership_data: Dict[str, Any]) -> Membership:
        """
        Create a new membership.
        
        Args:
            db: Database session
            membership_data: Dictionary with membership data
            
        Returns:
            Created Membership instance
            
        Raises:
            ConflictError: If membership already exists (unique constraint: tenant_id, user_id)
        """
        # Check if membership already exists
        existing = db.query(Membership).filter(
            Membership.tenant_id == membership_data["tenant_id"],
            Membership.user_id == membership_data["user_id"]
        ).first()
        
        if existing:
            raise ConflictError(
                f"Membership already exists for tenant {membership_data['tenant_id']} and user {membership_data['user_id']}",
                resource="membership"
            )
        
        membership = Membership(**membership_data)
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership
    
    def get_user_memberships(self, db: Session, user_id: str) -> List[Membership]:
        """
        Get all memberships for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of Membership instances
        """
        return db.query(Membership).filter(
            Membership.user_id == user_id
        ).options(
            joinedload(Membership.tenant),
            joinedload(Membership.role)
        ).all()
    
    def get_tenant_members(self, db: Session, tenant_id: str, 
                          status: Optional[MembershipStatus] = None) -> List[Membership]:
        """
        Get all members for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            status: Optional status filter
            
        Returns:
            List of Membership instances
        """
        query = db.query(Membership).filter(Membership.tenant_id == tenant_id)
        
        if status:
            query = query.filter(Membership.status == status)
        
        return query.options(
            joinedload(Membership.user),
            joinedload(Membership.role)
        ).all()
    
    def get_membership(self, db: Session, tenant_id: str, user_id: str) -> Optional[Membership]:
        """
        Get membership for a user in a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Membership instance or None
        """
        return db.query(Membership).filter(
            Membership.tenant_id == tenant_id,
            Membership.user_id == user_id
        ).options(
            joinedload(Membership.tenant),
            joinedload(Membership.user),
            joinedload(Membership.role)
        ).first()
    
    def get_user_permissions(self, db: Session, tenant_id: str, user_id: str) -> Set[str]:
        """
        Get all permissions for a user in a tenant.
        
        This method:
        1. Gets the user's membership in the tenant
        2. Gets the role from the membership
        3. Gets all permissions associated with that role
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Set of permission keys (strings)
        """
        # Get membership
        membership = self.get_membership(db, tenant_id, user_id)
        if not membership or membership.status != MembershipStatus.ACTIVE:
            return set()
        
        # Get role permissions
        role_permissions = db.query(RolePermission).filter(
            RolePermission.role_id == membership.role_id
        ).options(
            joinedload(RolePermission.permission)
        ).all()
        
        # Extract permission keys
        permissions = {rp.permission.key for rp in role_permissions if rp.permission}
        
        return permissions
    
    def update_membership(self, db: Session, membership_id: str, 
                         data: Dict[str, Any]) -> Membership:
        """
        Update membership.
        
        Args:
            db: Database session
            membership_id: Membership ID
            data: Dictionary with fields to update
            
        Returns:
            Updated Membership instance
            
        Raises:
            NotFoundError: If membership not found
        """
        membership = db.query(Membership).filter(Membership.id == membership_id).first()
        if not membership:
            raise NotFoundError("Membership", membership_id)
        
        # Update fields
        for key, value in data.items():
            if hasattr(membership, key):
                setattr(membership, key, value)
        
        membership.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(membership)
        return membership
