"""
SQLAlchemy model for risk_assessments table.

Matches migration 004 (create) + 012 (schema_version, UNIQUE(tenant_id, input_hash)).
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON

from app.database import Base


class AssessmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    ARCHIVED = "ARCHIVED"


class RiskAssessment(Base):
    """
    Risk assessment record: normalized input snapshot, hash, and links.

    - id: PK (ULID String(26))
    - tenant_id: FK tenants.id
    - input_snapshot_json: canonical JSON input
    - input_hash: SHA256 hex (64 chars)
    - schema_version: input schema version (e.g. v1)
    - shipment_id, corridor_id: optional links
    - created_by_user_id: FK users.id
    - created_at, updated_at
    - UNIQUE(tenant_id, input_hash)
    """

    __tablename__ = "legacy_risk_assessments"

    id = Column(String(26), primary_key=True, nullable=False)
    tenant_id = Column(
        String(26),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id = Column(
        String(26),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(
        SQLEnum(AssessmentStatus, native_enum=False),
        default=AssessmentStatus.DRAFT,
        nullable=False,
        index=True,
    )
    input_schema_version = Column(String(50), nullable=False)
    input_snapshot_json = Column(JSON, nullable=False)
    input_hash = Column(String(64), nullable=False, index=True)
    schema_version = Column(String(20), nullable=False)
    shipment_id = Column(String(26), nullable=True, index=True)
    corridor_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "input_hash",
            name="uq_risk_assessments_tenant_input_hash",
        ),
        Index("idx_risk_assessments_tenant", "tenant_id"),
        Index("idx_risk_assessments_input_hash", "input_hash"),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<RiskAssessment(id={self.id!r}, tenant_id={self.tenant_id!r}, input_hash={self.input_hash!r})>"
