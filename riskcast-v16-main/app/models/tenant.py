"""
Tenant and Membership Models
SQLAlchemy models for multi-tenancy support.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON

from app.database import Base


class TenantStatus(str, enum.Enum):
    """Tenant status"""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class LegacyTenant(Base):
    """
    Legacy Tenant/Organization model (renamed to avoid conflict with tenancy.models.Tenant)
    
    Represents a tenant in the multi-tenant system.
    Uses UUID for primary key (as per requirements).
    """
    __tablename__ = "legacy_tenants"
    __table_args__ = {'extend_existing': True}
    
    # Primary key (UUID)
    id = Column(
        String(36),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    
    # Basic fields
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=True, index=True)
    
    # Status
    status = Column(
        SQLEnum(TenantStatus, native_enum=False),
        default=TenantStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Settings (JSON)
    settings_json = Column(JSON, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    memberships = relationship(
        "LegacyMembership",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_tenants_name", "name"),
        Index("idx_tenants_slug", "slug"),
        Index("idx_tenants_status", "status"),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<LegacyTenant(id={self.id}, name={self.name!r}, slug={self.slug!r}, status={self.status.value})>"


class MembershipStatus(str, enum.Enum):
    """Membership status"""
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"


class LegacyMembership(Base):
    """
    Legacy Membership model - User-Tenant-Role association (renamed to avoid conflict)
    
    Links users to tenants with a role.
    Uses UUID for primary key (as per requirements).
    """
    __tablename__ = "legacy_memberships"
    __table_args__ = {'extend_existing': True}
    
    # Primary key (UUID)
    id = Column(
        String(36),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign keys
    tenant_id = Column(
        String(36),  # UUID (matches legacy_tenants.id)
        ForeignKey("legacy_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36),  # UUID (matches users.id)
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Role (VARCHAR as per requirements)
    role = Column(String(50), nullable=False, default="member", index=True)
    
    # Status
    status = Column(
        SQLEnum(MembershipStatus, native_enum=False),
        default=MembershipStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("LegacyTenant", back_populates="memberships")
    # Note: User relationship would be defined in User model
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),
        Index("idx_memberships_user", "user_id"),
        Index("idx_memberships_tenant", "tenant_id"),
        Index("idx_memberships_role", "role"),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return (
            f"<LegacyMembership(id={self.id}, tenant_id={self.tenant_id!r}, "
            f"user_id={self.user_id!r}, role={self.role!r}, status={self.status.value})>"
        )


# Backward compatibility aliases (not registering new SQLAlchemy mappers)
# These aliases allow old imports to work without causing SQLAlchemy registry conflicts
# since they point to the same class object (not a new class)
Tenant = LegacyTenant
Membership = LegacyMembership
