"""
RBAC & Policy Models
SQLAlchemy models for role-based access control
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

# Many-to-many relationship tables
user_role_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("role_id", String(36), ForeignKey("rbac_roles.id"), primary_key=True),
    Column("assigned_at", DateTime, default=datetime.utcnow),
    Column("assigned_by", String(36), ForeignKey("users.id")),
    extend_existing=True
)

role_permission_table = Table(
    "rbac_role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("rbac_roles.id"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("rbac_permissions.id"), primary_key=True),
    extend_existing=True
)


class Role(Base):
    """Role model"""
    __tablename__ = "rbac_roles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Scope
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)  # None = global role
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", secondary=user_role_table, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permission_table, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base):
    """Permission model"""
    __tablename__ = "rbac_permissions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)  # e.g., "risk_assessment", "underwriting"
    action = Column(String(50), nullable=False)  # e.g., "read", "write", "delete"
    description = Column(Text, nullable=True)
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    roles = relationship("Role", secondary=role_permission_table, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name}, resource={self.resource}, action={self.action})>"


class UserRole(Base):
    """User-Role association (with metadata)"""
    __tablename__ = "user_role_associations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("rbac_roles.id"), nullable=False, index=True)
    
    # Metadata
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Temporary role assignment
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role", foreign_keys=[role_id])
