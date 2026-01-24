"""
Example Usage of Shared Model Mixins

This file demonstrates how to use BaseMixin, TenantScopedMixin, and other mixins
in your SQLAlchemy models.
"""
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin, SoftDeleteMixin


# Example 1: Simple model with BaseMixin
class ExampleModel(Base, BaseMixin):
    """Example model with base fields (id, created_at, updated_at)"""
    __tablename__ = "example_models"
    
    name = Column(String(255), nullable=False)
    value = Column(Integer, nullable=False)
    
    # Automatically gets:
    # - id (ULID primary key)
    # - created_at (timestamp)
    # - updated_at (auto-updated timestamp)


# Example 2: Tenant-scoped model
class TenantScopedModel(Base, BaseMixin, TenantScopedMixin):
    """Example tenant-scoped model"""
    __tablename__ = "tenant_scoped_models"
    
    name = Column(String(255), nullable=False)
    data = Column(String(500), nullable=True)
    
    # Automatically gets:
    # - id (ULID primary key)
    # - tenant_id (foreign key to tenants, with __tenant_scoped__ marker)
    # - created_at, updated_at (timestamps)
    
    # Relationships can reference tenant
    # tenant = relationship("Tenant", back_populates="tenant_scoped_models")


# Example 3: Model with soft delete
class SoftDeletableModel(Base, BaseMixin, TenantScopedMixin, SoftDeleteMixin):
    """Example model with soft delete capability"""
    __tablename__ = "soft_deletable_models"
    
    name = Column(String(255), nullable=False)
    
    # Automatically gets:
    # - id, tenant_id, created_at, updated_at
    # - deleted_at (for soft delete)
    # - is_deleted property
    # - soft_delete() and restore() methods
    
    # Usage:
    # model.soft_delete()  # Mark as deleted
    # model.restore()       # Restore
    # if model.is_deleted:  # Check status
    #     ...


# Example 4: Custom primary key (if you don't want ULID)
class CustomIdModel(Base):
    """Example with custom ID (not using BaseMixin)"""
    __tablename__ = "custom_id_models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(String(50), nullable=False)  # Custom timestamp format


# Example 5: Join table with TimestampMixin (no ID needed)
class AssociationModel(Base, TenantScopedMixin, SoftDeleteMixin):
    """Example association/junction table"""
    __tablename__ = "association_models"
    
    # Composite primary key
    __table_args__ = (
        {'extend_existing': True}
    )
    
    model_a_id = Column(String(26), primary_key=True)
    model_b_id = Column(String(26), primary_key=True)
    
    # Gets tenant_id, deleted_at, but no id/created_at/updated_at
    # (unless you add TimestampMixin)
