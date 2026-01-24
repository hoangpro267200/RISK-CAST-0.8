"""
Risk Assessment Service
Business logic for risk assessment management with canonicalization and deduplication.
"""
from __future__ import annotations

from typing import Dict, Any, Tuple, Optional

from sqlalchemy.orm import Session

from app.core.risk_input.canonicalization import (
    canonicalize_input,
    compute_input_hash,
    validate_input_schema,
)
from app.core.audit_ledger.ledger import AuditLedger
from app.models.risk_assessment import RiskAssessment
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.shared.exceptions import NotFoundError


class RiskAssessmentService:
    """Service for risk assessment management with input canonicalization and deduplication."""

    DEFAULT_SCHEMA_VERSION = "v1"

    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize service.

        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.repository = RiskAssessmentRepository(db)
        self.audit = audit or AuditLedger(db)

    def create_assessment(
        self,
        tenant_id: str,
        raw_input: Dict[str, Any],
        schema_version: Optional[str] = None,
        shipment_id: Optional[str] = None,
        corridor_id: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
    ) -> RiskAssessment:
        """
        Create a new risk assessment.

        Steps:
        1. Canonicalize input
        2. Compute hash
        3. Check for existing (deduplication)
        4. Create and return

        Args:
            tenant_id: Tenant ID
            raw_input: Raw input data dictionary
            schema_version: Schema version (defaults to "v1")
            shipment_id: Optional shipment ID
            corridor_id: Optional corridor ID
            created_by_user_id: Optional user ID

        Returns:
            Created RiskAssessment instance (or existing if duplicate)

        Raises:
            ValueError: If input validation fails
        """
        # Validate schema if provided
        sv = schema_version or self.DEFAULT_SCHEMA_VERSION
        validation_result = validate_input_schema(raw_input, sv)
        if not validation_result.valid:
            raise ValueError(
                f"Input validation failed: {', '.join(validation_result.errors)}"
            )

        # Canonicalize input
        canonical_input = canonicalize_input(raw_input)

        # Compute hash for deduplication check
        input_hash = compute_input_hash(canonical_input)

        # Check for existing assessment (deduplication)
        existing = self.repository.get_by_input_hash(tenant_id, input_hash)
        if existing:
            # Return existing assessment
            return existing

        # Create new assessment (repository computes hash internally)
        return self.repository.create(
            tenant_id=tenant_id,
            input_data=canonical_input,
            schema_version=sv,
            shipment_id=shipment_id,
            corridor_id=corridor_id,
            created_by_user_id=created_by_user_id,
        )

    def get_or_create(
        self,
        tenant_id: str,
        raw_input: Dict[str, Any],
        schema_version: Optional[str] = None,
        shipment_id: Optional[str] = None,
        corridor_id: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
    ) -> Tuple[RiskAssessment, bool]:
        """
        Get existing assessment or create new one.

        Args:
            tenant_id: Tenant ID
            raw_input: Raw input data dictionary
            schema_version: Schema version (defaults to "v1")
            shipment_id: Optional shipment ID
            corridor_id: Optional corridor ID
            created_by_user_id: Optional user ID

        Returns:
            Tuple of (RiskAssessment, was_created) where was_created is True if newly created

        Raises:
            ValueError: If input validation fails
        """
        # Canonicalize and hash
        sv = schema_version or self.DEFAULT_SCHEMA_VERSION
        validation_result = validate_input_schema(raw_input, sv)
        if not validation_result.valid:
            raise ValueError(
                f"Input validation failed: {', '.join(validation_result.errors)}"
            )

        canonical_input = canonicalize_input(raw_input)
        input_hash = compute_input_hash(canonical_input)

        # Check for existing
        existing = self.repository.get_by_input_hash(tenant_id, input_hash)
        if existing:
            return existing, False

        # Create new (repository computes hash internally)
        assessment = self.repository.create(
            tenant_id=tenant_id,
            input_data=canonical_input,
            schema_version=sv,
            shipment_id=shipment_id,
            corridor_id=corridor_id,
            created_by_user_id=created_by_user_id,
        )
        
        # Emit audit event (only if newly created)
        try:
            self.audit.append_event(
                tenant_id=tenant_id,
                event_type="RISK_ASSESSMENT",
                action="CREATED",
                entity_type="risk_assessment",
                entity_id=assessment.id,
                actor_type="USER" if created_by_user_id else "SYSTEM",
                actor_id=created_by_user_id,
                payload={
                    "input_hash": assessment.input_hash,
                    "schema_version": assessment.schema_version,
                },
            )
        except Exception as e:
            # Log error but don't fail the operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to emit audit event for assessment {assessment.id}: {e}")
        
        return assessment, True

    def get_assessment(
        self, tenant_id: str, assessment_id: str
    ) -> RiskAssessment:
        """
        Get assessment by ID (tenant-scoped).

        Args:
            tenant_id: Tenant ID
            assessment_id: Assessment ID

        Returns:
            RiskAssessment instance

        Raises:
            NotFoundError: If assessment not found or not accessible
        """
        assessment = self.repository.get_by_id(tenant_id, assessment_id)
        if not assessment:
            raise NotFoundError(
                resource="risk_assessment",
                resource_id=assessment_id,
            )
        return assessment

    def list_by_shipment(
        self, tenant_id: str, shipment_id: str
    ) -> list[RiskAssessment]:
        """
        List assessments for a shipment (tenant-scoped).

        Args:
            tenant_id: Tenant ID
            shipment_id: Shipment ID

        Returns:
            List of RiskAssessment instances
        """
        return self.repository.list_by_shipment(tenant_id, shipment_id)
