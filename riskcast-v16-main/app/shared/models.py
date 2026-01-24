"""
Shared Model Mixins
Base classes and mixins for SQLAlchemy models
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import declared_attr
from datetime import datetime
from typing import Optional

from app.database import Base
from app.shared.utils import generate_ulid


class BaseMixin:
    """
    Base mixin with common fields for all models.
    
    Provides:
    - id: ULID primary key
    - created_at: Creation timestamp
    - updated_at: Last update timestamp (auto-updated)
    """
    
    id = Column(String(26), primary_key=True, default=generate_ulid, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self):
        """Default repr implementation"""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id})>"


class TenantScopedMixin:
    """
    Mixin for tenant-scoped models.
    
    Provides:
    - tenant_id: Foreign key to tenants table
    - __tenant_scoped__: Marker attribute for tenant isolation
    
    Models using this mixin will automatically have tenant isolation
    applied in queries and access control.
    """
    
    __tenant_scoped__ = True  # Marker for tenant isolation
    
    @declared_attr
    def tenant_id(cls):
        """Tenant ID foreign key"""
        return Column(
            String(26),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
    
    def __repr__(self):
        """Default repr with tenant_id"""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id}, tenant_id={self.tenant_id})>"


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    
    Provides:
    - deleted_at: Timestamp when record was soft-deleted (None = active)
    """
    
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self):
        """Mark record as deleted"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restore soft-deleted record"""
        self.deleted_at = None


class TimestampMixin:
    """
    Simple timestamp mixin (without ID).
    Useful for join tables or when you need timestamps without BaseMixin.
    """
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
