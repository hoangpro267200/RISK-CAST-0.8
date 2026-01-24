"""
Risk Runs Models
SQLAlchemy models for risk calculation runs and job queue
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Integer, BigInteger,
    Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin
from app.shared.utils import generate_ulid


class RiskRunStatus(str, enum.Enum):
    """Risk run execution status"""
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    CANCELED = 'CANCELED'


class SeedStrategy(str, enum.Enum):
    """Strategy for generating random seed"""
    DETERMINISTIC_INPUT_HASH = 'DETERMINISTIC_INPUT_HASH'
    USER_PROVIDED = 'USER_PROVIDED'


class RiskRun(Base, BaseMixin, TenantScopedMixin):
    """
    Risk Run model.
    
    Represents a single execution of the risk engine for a risk assessment.
    Multiple runs can exist for the same assessment (e.g., different engine versions,
    different seeds, different model versions).
    """
    __tablename__ = 'risk_runs'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Association with risk assessment
    risk_assessment_id = Column(
        String(26),
        ForeignKey('risk_assessments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Execution status
    status = Column(
        SQLEnum(RiskRunStatus, native_enum=False),
        default=RiskRunStatus.QUEUED,
        nullable=False,
        index=True
    )
    
    # Engine and model versioning
    engine_version = Column(String(100), nullable=False, index=True)  # Git SHA or semver+build
    model_version_id = Column(String(26), nullable=True, index=True)  # FK to risk_model_versions (Stage 2)
    
    # Result schema versioning
    result_schema_version = Column(String(50), nullable=False)  # e.g., 'risk_result_v3.0'
    
    # Random seed configuration
    seed_strategy = Column(
        SQLEnum(SeedStrategy, native_enum=False),
        nullable=False
    )
    seed = Column(BigInteger, nullable=False)  # Random seed for reproducibility
    iterations = Column(Integer, nullable=False)  # Number of Monte Carlo iterations
    
    # Execution options
    options_json = Column(JSON, nullable=True)  # scenario_set_id, toggles, etc.
    
    # Results (populated on completion)
    result_json = Column(JSON, nullable=True)  # Full result payload
    result_hash = Column(String(64), nullable=True, index=True)  # SHA256 of canonical result
    error_json = Column(JSON, nullable=True)  # Error details (populated on failure)
    
    # Execution timestamps
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    assessment = relationship(
        'RiskAssessment',
        back_populates='runs',
        lazy='select'
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_risk_runs_tenant_assessment', 'tenant_id', 'risk_assessment_id', 'created_at'),
        Index('ix_risk_runs_tenant_status', 'tenant_id', 'status'),
        Index('ix_risk_runs_assessment_status', 'risk_assessment_id', 'status'),
    )
    
    def __repr__(self):
        return (
            f"<RiskRun(id={self.id}, assessment_id={self.risk_assessment_id}, "
            f"status={self.status.value if hasattr(self.status, 'value') else self.status}, "
            f"engine_version={self.engine_version})>"
        )


class RiskRunJobStatus(str, enum.Enum):
    """Risk run job queue status"""
    QUEUED = 'QUEUED'
    LOCKED = 'LOCKED'
    DONE = 'DONE'
    FAILED = 'FAILED'


class RiskRunJob(Base, BaseMixin):
    """
    Risk Run Job model.
    
    Job queue for asynchronous risk run execution.
    Workers pick up jobs from this queue and execute the corresponding risk runs.
    """
    __tablename__ = 'risk_run_jobs'
    
    # ID is inherited from BaseMixin (ULID String(26))
    # created_at, updated_at are inherited from BaseMixin
    
    # Tenant association (not using TenantScopedMixin to allow cross-tenant job processing)
    tenant_id = Column(
        String(26),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # One-to-one relationship with risk run
    risk_run_id = Column(
        String(26),
        ForeignKey('risk_runs.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Job status
    status = Column(
        SQLEnum(RiskRunJobStatus, native_enum=False),
        default=RiskRunJobStatus.QUEUED,
        nullable=False,
        index=True
    )
    
    # Locking for worker coordination
    locked_by = Column(String(100), nullable=True)  # Worker identity (hostname, worker_id, etc.)
    locked_at = Column(DateTime, nullable=True)
    
    # Retry logic
    attempt_count = Column(Integer, default=0, nullable=False)
    available_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)  # For retry backoff
    
    # Relationships
    risk_run = relationship(
        'RiskRun',
        foreign_keys=[risk_run_id],
        lazy='select'
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_risk_run_jobs_status_available', 'status', 'available_at'),
        Index('ix_risk_run_jobs_tenant_status', 'tenant_id', 'status'),
    )
    
    def __repr__(self):
        return (
            f"<RiskRunJob(id={self.id}, risk_run_id={self.risk_run_id}, "
            f"status={self.status.value if hasattr(self.status, 'value') else self.status}, "
            f"attempt_count={self.attempt_count})>"
        )
