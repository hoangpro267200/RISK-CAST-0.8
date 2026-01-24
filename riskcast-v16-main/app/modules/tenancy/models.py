"""
Tenancy Models
SQLAlchemy models for tenant, user, role, permission, and membership management
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import ENUM
import enum

from app.database import Base
from app.shared.models import BaseMixin


class TenantStatus(str, enum.Enum):
    """Tenant status"""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class Tenant(Base, BaseMixin):
    """Tenant/Organization model"""
    __tablename__ = "tenants"
    
    name = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(
        SQLEnum(TenantStatus, native_enum=False),
        default=TenantStatus.ACTIVE,
        nullable=False,
        index=True
    )
    subscription_tier = Column(String(100), nullable=True)  # free, standard, enterprise
    features_json = Column(JSON, nullable=True, default=dict)  # Feature flags per tenant
    
    # Relationships
    memberships = relationship("Membership", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, status={self.status.value})>"


class UserStatus(str, enum.Enum):
    """User status"""
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class User(Base, BaseMixin):
    """User model"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(
        SQLEnum(UserStatus, native_enum=False),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Relationships
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, status={self.status.value})>"


class RoleScope(str, enum.Enum):
    """Role scope"""
    TENANT = "TENANT"
    PLATFORM = "PLATFORM"


class Role(Base, BaseMixin):
    """Role model"""
    __tablename__ = "roles"
    
    name = Column(String(100), nullable=False, index=True)
    scope = Column(
        SQLEnum(RoleScope, native_enum=False),
        nullable=False,
        index=True
    )
    
    # Unique constraint: (name, scope)
    __table_args__ = (
        UniqueConstraint('name', 'scope', name='uq_role_name_scope'),
    )
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name}, scope={self.scope.value})>"


class Permission(Base, BaseMixin):
    """Permission model"""
    __tablename__ = "permissions"
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, key={self.key})>"


class RolePermission(Base):
    """Role-Permission association table"""
    __tablename__ = "role_permissions"
    
    role_id = Column(String(26), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(String(26), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class MembershipStatus(str, enum.Enum):
    """Membership status"""
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"


class Membership(Base, BaseMixin):
    """Membership model - User-Tenant-Role association"""
    __tablename__ = "memberships"
    
    tenant_id = Column(String(26), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(26), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(26), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(
        SQLEnum(MembershipStatus, native_enum=False),
        default=MembershipStatus.INVITED,
        nullable=False,
        index=True
    )
    
    # Unique constraint: (tenant_id, user_id) - one role per user per tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', name='uq_membership_tenant_user'),
        Index('idx_membership_tenant_role', 'tenant_id', 'role_id'),
    )
    
    # Relationships
    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User", back_populates="memberships")
    role = relationship("Role", back_populates="memberships")
    
    def __repr__(self):
        return f"<Membership(id={self.id}, tenant_id={self.tenant_id}, user_id={self.user_id}, role_id={self.role_id}, status={self.status.value})>"
