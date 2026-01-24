"""
Tenancy Service
Business logic layer for tenant and membership management
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy.orm import Session
from typing import Optional, Set
import logging

from app.modules.tenancy.repository import (
    TenantRepository, UserRepository, MembershipRepository
)
from app.modules.tenancy.schemas import TenantCreate, TenantUpdate
from app.modules.tenancy.models import (
    Tenant, User, Membership, Role,
    TenantStatus, MembershipStatus, RoleScope
)
from app.modules.tenancy.exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError,
    MembershipNotFoundError, InvalidMembershipError,
    UserNotFoundError, RoleNotFoundError
)

logger = logging.getLogger(__name__)


class TenantService:
    """Service for tenant management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tenant_repo = TenantRepository()
        self.user_repo = UserRepository()
        self.membership_repo = MembershipRepository()
    
    async def create_tenant(
        self,
        data: TenantCreate,
        creator_user_id: Optional[str] = None
    ) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            data: Tenant creation data
            creator_user_id: Optional user ID who creates the tenant
            
        Returns:
            Created Tenant instance
            
        Raises:
            TenantAlreadyExistsError: If tenant name already exists
            UserNotFoundError: If creator_user_id provided but user not found
            RoleNotFoundError: If tenant_admin role not found
        """
        # Validate name uniqueness (repository will check, but we can check here too)
        existing = self.tenant_repo.get_by_name(self.db, data.name)
        if existing:
            raise TenantAlreadyExistsError(data.name)
        
        # Prepare tenant data
        tenant_data = data.dict(exclude_unset=True)
        
        # Create tenant
        tenant = self.tenant_repo.create(self.db, tenant_data)
        logger.info(f"Created tenant: {tenant.id} - {tenant.name}")
        
        # Create initial admin membership if creator provided
        if creator_user_id:
            await self._create_initial_admin_membership(tenant.id, creator_user_id)
        
        # TODO: Emit audit event
        # await self._emit_audit_event("tenant.created", tenant_id=tenant.id, user_id=creator_user_id)
        
        return tenant
    
    async def _create_initial_admin_membership(self, tenant_id: str, user_id: str):
        """Create initial admin membership for tenant creator"""
        # Verify user exists
        user = self.user_repo.get_by_id(self.db, user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Find tenant_admin role (TENANT scope)
        role = self.db.query(Role).filter(
            Role.name == "tenant_admin",
            Role.scope == RoleScope.TENANT
        ).first()
        
        if not role:
            raise RoleNotFoundError("tenant_admin role not found")
        
        # Create membership
        try:
            membership = self.membership_repo.create(self.db, {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "role_id": role.id,
                "status": MembershipStatus.ACTIVE
            })
            logger.info(f"Created initial admin membership: {membership.id} for tenant {tenant_id}")
        except Exception as e:
            logger.error(f"Failed to create initial admin membership: {e}")
            # Don't fail tenant creation if membership creation fails
            # Just log the error
    
    async def get_tenant(self, tenant_id: str) -> Tenant:
        """
        Get tenant by ID.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant instance
            
        Raises:
            TenantNotFoundError: If tenant not found
        """
        tenant = self.tenant_repo.get_by_id(self.db, tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        return tenant
    
    async def update_tenant(self, tenant_id: str, data: TenantUpdate) -> Tenant:
        """
        Update tenant.
        
        Args:
            tenant_id: Tenant ID
            data: Update data
            
        Returns:
            Updated Tenant instance
            
        Raises:
            TenantNotFoundError: If tenant not found
            TenantAlreadyExistsError: If new name conflicts
        """
        # Get tenant first
        tenant = await self.get_tenant(tenant_id)
        
        # Prepare update data
        update_data = data.dict(exclude_unset=True)
        
        # Check name conflict if name is being updated
        if "name" in update_data and update_data["name"] != tenant.name:
            existing = self.tenant_repo.get_by_name(self.db, update_data["name"])
            if existing:
                raise TenantAlreadyExistsError(update_data["name"])
        
        # Update tenant
        updated_tenant = self.tenant_repo.update(self.db, tenant_id, update_data)
        logger.info(f"Updated tenant: {tenant_id}")
        
        # TODO: Emit audit event
        # await self._emit_audit_event("tenant.updated", tenant_id=tenant_id, changes=update_data)
        
        return updated_tenant
    
    async def suspend_tenant(self, tenant_id: str, reason: str) -> Tenant:
        """
        Suspend a tenant.
        
        Args:
            tenant_id: Tenant ID
            reason: Reason for suspension
            
        Returns:
            Updated Tenant instance
            
        Raises:
            TenantNotFoundError: If tenant not found
        """
        # Get tenant
        tenant = await self.get_tenant(tenant_id)
        
        # Update status
        updated_tenant = self.tenant_repo.update(self.db, tenant_id, {
            "status": TenantStatus.SUSPENDED
        })
        
        logger.warning(f"Suspended tenant: {tenant_id} - Reason: {reason}")
        
        # TODO: Emit audit event
        # await self._emit_audit_event("tenant.suspended", tenant_id=tenant_id, reason=reason)
        
        return updated_tenant
    
    async def activate_tenant(self, tenant_id: str) -> Tenant:
        """
        Activate a suspended tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Updated Tenant instance
            
        Raises:
            TenantNotFoundError: If tenant not found
        """
        tenant = await self.get_tenant(tenant_id)
        
        updated_tenant = self.tenant_repo.update(self.db, tenant_id, {
            "status": TenantStatus.ACTIVE
        })
        
        logger.info(f"Activated tenant: {tenant_id}")
        
        return updated_tenant


class MembershipService:
    """Service for membership management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.membership_repo = MembershipRepository()
        self.user_repo = UserRepository()
        self.tenant_repo = TenantRepository()
    
    async def add_member(
        self,
        tenant_id: str,
        user_id: str,
        role_id: str
    ) -> Membership:
        """
        Add a member to a tenant.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            role_id: Role ID
            
        Returns:
            Created Membership instance
            
        Raises:
            TenantNotFoundError: If tenant not found
            UserNotFoundError: If user not found
            RoleNotFoundError: If role not found
            InvalidMembershipError: If membership already exists
        """
        # Validate tenant exists
        tenant = self.tenant_repo.get_by_id(self.db, tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        
        # Validate user exists
        user = self.user_repo.get_by_id(self.db, user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Validate role exists
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise RoleNotFoundError(role_id)
        
        # Check if membership already exists
        existing = self.membership_repo.get_membership(self.db, tenant_id, user_id)
        if existing:
            raise InvalidMembershipError(
                f"User {user_id} is already a member of tenant {tenant_id}"
            )
        
        # Create membership
        membership = self.membership_repo.create(self.db, {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "role_id": role_id,
            "status": MembershipStatus.ACTIVE
        })
        
        logger.info(f"Added member {user_id} to tenant {tenant_id} with role {role_id}")
        
        # TODO: Emit audit event
        # await self._emit_audit_event("membership.created", tenant_id=tenant_id, user_id=user_id, role_id=role_id)
        
        return membership
    
    async def remove_member(self, tenant_id: str, user_id: str) -> None:
        """
        Remove a member from a tenant.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            
        Raises:
            MembershipNotFoundError: If membership not found
        """
        # Get membership
        membership = self.membership_repo.get_membership(self.db, tenant_id, user_id)
        if not membership:
            raise MembershipNotFoundError(tenant_id, user_id)
        
        # Delete membership
        self.db.delete(membership)
        self.db.commit()
        
        logger.info(f"Removed member {user_id} from tenant {tenant_id}")
        
        # TODO: Emit audit event
        # await self._emit_audit_event("membership.deleted", tenant_id=tenant_id, user_id=user_id)
    
    async def change_role(
        self,
        tenant_id: str,
        user_id: str,
        new_role_id: str
    ) -> Membership:
        """
        Change a member's role in a tenant.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            new_role_id: New role ID
            
        Returns:
            Updated Membership instance
            
        Raises:
            MembershipNotFoundError: If membership not found
            RoleNotFoundError: If role not found
        """
        # Get membership
        membership = self.membership_repo.get_membership(self.db, tenant_id, user_id)
        if not membership:
            raise MembershipNotFoundError(tenant_id, user_id)
        
        # Validate new role exists
        role = self.db.query(Role).filter(Role.id == new_role_id).first()
        if not role:
            raise RoleNotFoundError(new_role_id)
        
        # Update role
        old_role_id = membership.role_id
        updated_membership = self.membership_repo.update_membership(self.db, membership.id, {
            "role_id": new_role_id
        })
        
        logger.info(f"Changed role for user {user_id} in tenant {tenant_id} from {old_role_id} to {new_role_id}")
        
        # TODO: Emit audit event
        # await self._emit_audit_event("membership.role_changed", tenant_id=tenant_id, user_id=user_id, old_role_id=old_role_id, new_role_id=new_role_id)
        
        return updated_membership
    
    async def get_user_permissions(self, tenant_id: str, user_id: str) -> Set[str]:
        """
        Get all permissions for a user in a tenant.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Set of permission keys
            
        Raises:
            TenantNotFoundError: If tenant not found
            UserNotFoundError: If user not found
        """
        # Validate tenant exists
        tenant = self.tenant_repo.get_by_id(self.db, tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        
        # Validate user exists
        user = self.user_repo.get_by_id(self.db, user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Get permissions from repository
        permissions = self.membership_repo.get_user_permissions(self.db, tenant_id, user_id)
        
        return permissions
    
    async def update_membership_status(
        self,
        tenant_id: str,
        user_id: str,
        status: MembershipStatus
    ) -> Membership:
        """
        Update membership status.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            status: New status
            
        Returns:
            Updated Membership instance
            
        Raises:
            MembershipNotFoundError: If membership not found
        """
        membership = self.membership_repo.get_membership(self.db, tenant_id, user_id)
        if not membership:
            raise MembershipNotFoundError(tenant_id, user_id)
        
        updated = self.membership_repo.update_membership(self.db, membership.id, {
            "status": status
        })
        
        logger.info(f"Updated membership status for user {user_id} in tenant {tenant_id} to {status.value}")
        
        return updated
