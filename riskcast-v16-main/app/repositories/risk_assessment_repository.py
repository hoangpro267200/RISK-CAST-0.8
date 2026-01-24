"""
Risk Assessment Repository
Data access layer for risk assessments with tenant isolation.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.risk_input.canonicalization import compute_input_hash
from app.models.risk_assessment import RiskAssessment
from app.shared.utils import generate_ulid


class RiskAssessmentRepository:
    """Repository for risk assessment data access with tenant isolation."""

    def __init__(self, db: Session):
        """
        Initialize repository.

        Args:
            db: Database session
        """
        self.db = db

    def create(
        self,
        tenant_id: str,
        input_data: dict,
        schema_version: str,
        shipment_id: Optional[str] = None,
        corridor_id: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
    ) -> RiskAssessment:
        """
        Create a new risk assessment.

        Computes input hash from canonicalized input_data internally.

        Args:
            tenant_id: Tenant ID
            input_data: Canonical input data (dict)
            schema_version: Schema version (e.g., "v1")
            shipment_id: Optional shipment ID
            corridor_id: Optional corridor ID
            created_by_user_id: Optional user ID who created this

        Returns:
            Created RiskAssessment instance

        Raises:
            IntegrityError: If UNIQUE(tenant_id, input_hash) constraint violated
        """
        # Compute hash from canonicalized input
        input_hash = compute_input_hash(input_data)
        
        assessment = RiskAssessment(
            id=generate_ulid(),
            tenant_id=tenant_id,
            input_snapshot_json=input_data,
            input_hash=input_hash,
            schema_version=schema_version,
            input_schema_version=schema_version,  # Keep for backward compatibility
            shipment_id=shipment_id,
            corridor_id=corridor_id,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_by_id(self, tenant_id: str, assessment_id: str) -> Optional[RiskAssessment]:
        """
        Get assessment by ID (tenant-scoped).

        Args:
            tenant_id: Tenant ID
            assessment_id: Assessment ID

        Returns:
            RiskAssessment if found, None otherwise
        """
        return (
            self.db.query(RiskAssessment)
            .filter(
                and_(
                    RiskAssessment.id == assessment_id,
                    RiskAssessment.tenant_id == tenant_id,
                )
            )
            .first()
        )

    def get_by_input_hash(
        self, tenant_id: str, input_hash: str
    ) -> Optional[RiskAssessment]:
        """
        Get assessment by input hash (tenant-scoped).

        Args:
            tenant_id: Tenant ID
            input_hash: SHA256 hash of canonical input

        Returns:
            RiskAssessment if found, None otherwise
        """
        return (
            self.db.query(RiskAssessment)
            .filter(
                and_(
                    RiskAssessment.input_hash == input_hash,
                    RiskAssessment.tenant_id == tenant_id,
                )
            )
            .order_by(RiskAssessment.created_at.desc())
            .first()
        )

    def list_by_shipment(
        self, tenant_id: str, shipment_id: str
    ) -> List[RiskAssessment]:
        """
        List assessments for a shipment (tenant-scoped).

        Args:
            tenant_id: Tenant ID
            shipment_id: Shipment ID

        Returns:
            List of RiskAssessment instances
        """
        return (
            self.db.query(RiskAssessment)
            .filter(
                and_(
                    RiskAssessment.shipment_id == shipment_id,
                    RiskAssessment.tenant_id == tenant_id,
                )
            )
            .order_by(RiskAssessment.created_at.desc())
            .all()
        )
