"""
Example Usage of Tenancy Services

This file demonstrates how to use the service classes.
"""
from sqlalchemy.orm import Session
from app.modules.tenancy.service import TenantService, MembershipService
from app.modules.tenancy.schemas import TenantCreate
from app.modules.tenancy.models import MembershipStatus
import asyncio


async def example_create_tenant_with_admin(db: Session, creator_user_id: str):
    """Example: Create tenant with initial admin"""
    service = TenantService(db)
    
    tenant_data = TenantCreate(
        name="Acme Corp",
        subscription_tier="enterprise",
        features_json={"risk_engine": True}
    )
    
    tenant = await service.create_tenant(tenant_data, creator_user_id=creator_user_id)
    print(f"Created tenant: {tenant.id} - {tenant.name}")
    return tenant


async def example_suspend_tenant(db: Session, tenant_id: str):
    """Example: Suspend a tenant"""
    service = TenantService(db)
    
    tenant = await service.suspend_tenant(tenant_id, reason="Payment overdue")
    print(f"Suspended tenant: {tenant.id} - Status: {tenant.status.value}")
    return tenant


async def example_add_member(db: Session, tenant_id: str, user_id: str, role_id: str):
    """Example: Add member to tenant"""
    service = MembershipService(db)
    
    membership = await service.add_member(tenant_id, user_id, role_id)
    print(f"Added member: {membership.id}")
    return membership


async def example_change_role(db: Session, tenant_id: str, user_id: str, new_role_id: str):
    """Example: Change member role"""
    service = MembershipService(db)
    
    membership = await service.change_role(tenant_id, user_id, new_role_id)
    print(f"Changed role: {membership.role_id}")
    return membership


async def example_get_permissions(db: Session, tenant_id: str, user_id: str):
    """Example: Get user permissions"""
    service = MembershipService(db)
    
    permissions = await service.get_user_permissions(tenant_id, user_id)
    print(f"User permissions: {permissions}")
    return permissions


async def example_remove_member(db: Session, tenant_id: str, user_id: str):
    """Example: Remove member from tenant"""
    service = MembershipService(db)
    
    await service.remove_member(tenant_id, user_id)
    print(f"Removed member {user_id} from tenant {tenant_id}")


if __name__ == "__main__":
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Example usage
        # tenant = asyncio.run(example_create_tenant_with_admin(db, "user_id_here"))
        pass
    finally:
        db.close()
