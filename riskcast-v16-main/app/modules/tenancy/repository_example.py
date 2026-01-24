"""
Example Usage of Tenancy Repositories

This file demonstrates how to use the repository classes.
"""
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.modules.tenancy.repository import (
    TenantRepository, UserRepository, MembershipRepository
)
from app.modules.tenancy.models import TenantStatus, UserStatus, MembershipStatus
from app.modules.tenancy.schemas import (
    TenantCreate, UserCreate, MembershipCreate
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def example_create_tenant(db: Session):
    """Example: Create a tenant"""
    repo = TenantRepository()
    
    tenant_data = {
        "name": "Acme Corp",
        "status": TenantStatus.ACTIVE,
        "subscription_tier": "enterprise",
        "features_json": {"risk_engine": True, "audit_trail": True}
    }
    
    tenant = repo.create(db, tenant_data)
    print(f"Created tenant: {tenant.id} - {tenant.name}")
    return tenant


def example_create_user(db: Session):
    """Example: Create a user"""
    repo = UserRepository()
    
    user_data = {
        "email": "admin@acme.com",
        "password_hash": pwd_context.hash("password123"),
        "status": UserStatus.ACTIVE
    }
    
    user = repo.create(db, user_data)
    print(f"Created user: {user.id} - {user.email}")
    return user


def example_create_membership(db: Session, tenant_id: str, user_id: str, role_id: str):
    """Example: Create a membership"""
    repo = MembershipRepository()
    
    membership_data = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "role_id": role_id,
        "status": MembershipStatus.ACTIVE
    }
    
    membership = repo.create(db, membership_data)
    print(f"Created membership: {membership.id}")
    return membership


def example_get_user_permissions(db: Session, tenant_id: str, user_id: str):
    """Example: Get user permissions"""
    repo = MembershipRepository()
    
    permissions = repo.get_user_permissions(db, tenant_id, user_id)
    print(f"User permissions: {permissions}")
    return permissions


def example_list_tenants(db: Session):
    """Example: List tenants with filters"""
    repo = TenantRepository()
    
    # List all active tenants
    filters = {"status": TenantStatus.ACTIVE}
    tenants = repo.list_all(db, filters=filters, skip=0, limit=10)
    
    print(f"Found {len(tenants)} tenants")
    for tenant in tenants:
        print(f"  - {tenant.name} ({tenant.status.value})")
    
    return tenants


def example_get_tenant_members(db: Session, tenant_id: str):
    """Example: Get all members of a tenant"""
    repo = MembershipRepository()
    
    members = repo.get_tenant_members(db, tenant_id, status=MembershipStatus.ACTIVE)
    print(f"Tenant has {len(members)} active members")
    
    for member in members:
        print(f"  - User {member.user_id} with role {member.role_id}")
    
    return members
