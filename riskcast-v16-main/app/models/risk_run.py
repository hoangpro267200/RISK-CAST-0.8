"""
Risk Run Model
SQLAlchemy model for risk calculation runs
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, BigInteger, Integer, DateTime, ForeignKey, JSON, Text,
    Enum as SQLEnum, Index
)

from app.database import Base


class RiskRunStatus(str, enum.Enum):
    """Risk run execution status"""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RiskRun(Base):
    """
    Risk Run Model
    
    Represents a single execution of the risk engine for a risk assessment.
    
    Fields:
    - id: UUID primary key
    - tenant_id: FK to tenants (ULID String(26))
    - assessment_id: FK to risk_assessments (ULID String(26))
    - status: Execution status (PENDING, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED)
    - seed: Random seed for reproducibility
    - seed_strategy: Strategy for seed generation
    - iterations: Number of Monte Carlo iterations
    - engine_version: Engine version identifier
    - model_version_id: Model version ID (UUID, nullable)
    - result_json: Full result payload (JSON, nullable)
    - result_hash: SHA256 hash of canonical result (nullable)
    - error_message: Error message if failed (TEXT, nullable)
    - error_details: Error details (JSON, nullable)
    - created_at: Creation timestamp
    - started_at: Start timestamp (nullable)
    - completed_at: Completion timestamp (nullable)
    - attempt_count: Number of retry attempts
    - max_attempts: Maximum retry attempts
    """
    
    __tablename__ = "legacy_risk_runs"
    
    # Primary key (UUID)
    id = Column(String(36), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tenant association
    tenant_id = Column(
        String(26),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Association with risk assessment
    assessment_id = Column(
        String(26),
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Status
    status = Column(
        SQLEnum(RiskRunStatus, native_enum=False),
        default=RiskRunStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Configuration
    seed = Column(BigInteger, nullable=False)
    seed_strategy = Column(String(20), nullable=False)
    iterations = Column(Integer, nullable=False, server_default="10000")
    
    # Versioning
    engine_version = Column(String(50), nullable=False)
    model_version_id = Column(String(36), nullable=True)  # UUID (FK added later)
    
    # Results (populated on completion)
    result_json = Column(JSON, nullable=True)
    result_hash = Column(String(64), nullable=True)
    
    # Error info (if failed)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    
    # Retry tracking
    attempt_count = Column(Integer, nullable=False, server_default="0")
    max_attempts = Column(Integer, nullable=False, server_default="3")
    
    # Indexes
    __table_args__ = (
        Index("idx_risk_runs_tenant", "tenant_id"),
        Index("idx_risk_runs_assessment", "assessment_id"),
        Index("idx_risk_runs_status", "status"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<RiskRun(id={self.id!r}, tenant_id={self.tenant_id!r}, "
            f"assessment_id={self.assessment_id!r}, status={self.status.value})>"
        )
