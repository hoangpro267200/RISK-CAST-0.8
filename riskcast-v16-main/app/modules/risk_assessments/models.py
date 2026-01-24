"""
Risk Assessments Models
SQLAlchemy models for risk assessments
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    Index
)
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin
from app.shared.utils import generate_ulid


class AssessmentStatus(str, enum.Enum):
    """Risk assessment status"""
    DRAFT = "DRAFT"
    READY = "READY"
    ARCHIVED = "ARCHIVED"


class RiskAssessment(Base, BaseMixin, TenantScopedMixin):
    """
    Risk Assessment model.
    
    Represents a risk assessment request with normalized input data.
    This is the primary entity for risk calculations in RISKCAST V3.
    """
    __tablename__ = 'risk_assessments'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # User who created the assessment
    created_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Status
    status = Column(
        SQLEnum(AssessmentStatus, native_enum=False),
        default=AssessmentStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Input schema and data
    input_schema_version = Column(String(50), nullable=False)  # e.g., 'risk_input_v3.0'
    input_snapshot_json = Column(JSON, nullable=False)  # Canonical normalized input
    input_hash = Column(String(64), nullable=False, index=True)  # SHA256 hex
    
    # Optional links
    shipment_id = Column(String(26), nullable=True, index=True)  # Legacy link
    corridor_id = Column(String(100), nullable=True, index=True)  # Stage 2+
    
    # Relationships
    # One assessment can have multiple risk runs
    runs = relationship(
        'RiskRun',
        back_populates='assessment',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    created_by_user = relationship(
        'User',
        foreign_keys=[created_by_user_id],
        lazy='select'
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_risk_assessments_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_risk_assessments_tenant_hash', 'tenant_id', 'input_hash'),
        Index('ix_risk_assessments_tenant_status', 'tenant_id', 'status'),
    )
    
    def __repr__(self):
        return (
            f"<RiskAssessment(id={self.id}, tenant_id={self.tenant_id}, "
            f"status={self.status.value if hasattr(self.status, 'value') else self.status}, "
            f"input_schema_version={self.input_schema_version})>"
        )
