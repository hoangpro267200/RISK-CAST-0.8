"""
RBAC Models
SQLAlchemy models for Role-Based Access Control.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean, Text, UniqueConstraint, Index,
    Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON

from app.database import Base


# Association table for role-permission many-to-many relationship
role_permission_table = Table(
    'legacy_rbac_role_permissions',
    Base.metadata,
    Column('role_id', String(36), ForeignKey('legacy_rbac_roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', String(36), ForeignKey('legacy_rbac_permissions.id', ondelete='CASCADE'), primary_key=True),
    extend_existing=True
)


class Role(Base):
    """
    Role model
    
    Represents a role in the RBAC system.
    Can be tenant-specific (tenant_id set) or system-wide (tenant_id NULL).
    """
    __tablename__ = "legacy_rbac_roles"
    __table_args__ = {'extend_existing': True}
    
    # Primary key (UUID)
    id = Column(
        String(36),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    
    # Tenant association (NULL for system roles)
    tenant_id = Column(
        String(36),  # UUID (matches tenants.id)
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Role details
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # System role flag
    is_system_role = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    permissions = relationship(
        "Permission",
        secondary=role_permission_table,
        back_populates="roles"
    )
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_rbac_roles_tenant_name"),
        Index("ix_rbac_roles_tenant_id", "tenant_id"),
        Index("ix_rbac_roles_name", "name"),
        Index("ix_rbac_roles_is_system_role", "is_system_role"),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return (
            f"<Role(id={self.id}, name={self.name!r}, "
            f"tenant_id={self.tenant_id!r}, is_system_role={self.is_system_role})>"
        )


class Permission(Base):
    """
    Permission model
    
    Represents a permission in the RBAC system.
    Permissions are global (not tenant-specific).
    """
    __tablename__ = "legacy_rbac_permissions"
    __table_args__ = {'extend_existing': True}
    
    # Primary key (UUID)
    id = Column(
        String(36),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    
    # Permission details
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permission_table,
        back_populates="permissions"
    )
    
    __table_args__ = (
        Index("ix_rbac_permissions_name", "name"),
        Index("ix_rbac_permissions_resource", "resource"),
        Index("ix_rbac_permissions_action", "action"),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return (
            f"<Permission(id={self.id}, name={self.name!r}, "
            f"resource={self.resource!r}, action={self.action!r})>"
        )
