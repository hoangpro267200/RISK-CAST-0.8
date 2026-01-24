"""
Risk Run Service
Business logic for risk run management and execution.
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.risk_run import RiskRun, RiskRunStatus
from app.models.risk_assessment import RiskAssessment
from app.repositories.risk_run_repository import RiskRunRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.core.audit_ledger.ledger import AuditLedger
from app.modules.risk_engine_v3.service import RiskEngineV3
from app.modules.risk_engine_v3.schemas import (
    RiskEngineInputV3,
    RiskEngineRunConfig,
    RiskEngineResultV3,
)
from app.shared.exceptions import NotFoundError


@dataclass
class RiskRunWithProvenance:
    """Risk run with full provenance information"""
    run: RiskRun
    assessment: RiskAssessment
    provenance: Dict[str, Any]


class RiskRunService:
    """Service for risk run management and execution."""

    DEFAULT_ITERATIONS = 10000
    DEFAULT_ENGINE_VERSION = "v3.0.0"

    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize service.

        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.repository = RiskRunRepository(db)
        self.assessment_repository = RiskAssessmentRepository(db)
        self.engine = RiskEngineV3()
        self.audit = audit or AuditLedger(db)

    def create_run(
        self,
        tenant_id: str,
        assessment_id: str,
        seed: Optional[int] = None,
        seed_strategy: str = "HASH_BASED",
        iterations: int = 10000,
        model_version_id: Optional[str] = None,
    ) -> RiskRun:
        """
        Create a new risk run.

        Steps:
        1. Load assessment
        2. Resolve seed based on strategy
        3. Create run record
        4. Emit audit event
        5. Return run

        Args:
            tenant_id: Tenant ID
            assessment_id: Risk assessment ID
            seed: Optional explicit seed (required if seed_strategy=USER_PROVIDED)
            seed_strategy: Seed strategy (HASH_BASED or USER_PROVIDED)
            iterations: Number of Monte Carlo iterations
            model_version_id: Optional model version ID

        Returns:
            Created RiskRun instance

        Raises:
            NotFoundError: If assessment not found
            ValueError: If seed resolution fails
        """
        # Load assessment
        assessment = self.assessment_repository.get_by_id(tenant_id, assessment_id)
        if not assessment:
            raise NotFoundError(
                resource="risk_assessment",
                resource_id=assessment_id,
            )

        # Resolve seed
        if seed_strategy == "HASH_BASED":
            # Compute deterministic seed from input hash
            final_seed = self.engine.compute_deterministic_seed(
                assessment.input_hash,
                model_version_id,
                iterations,
                self.engine.RESULT_SCHEMA_VERSION,
            )
        elif seed_strategy == "USER_PROVIDED":
            if seed is None:
                raise ValueError(
                    "seed is required when seed_strategy is USER_PROVIDED"
                )
            final_seed = seed
        else:
            raise ValueError(f"Invalid seed_strategy: {seed_strategy}")

        # Get engine version
        engine_version = self.engine.engine_version or self.DEFAULT_ENGINE_VERSION

        # Create run record
        config = {
            "seed": final_seed,
            "seed_strategy": seed_strategy,
            "iterations": iterations,
            "engine_version": engine_version,
            "model_version_id": model_version_id,
        }
        run = self.repository.create(tenant_id, assessment_id, config)

        # Emit audit event
        try:
            self.audit.append_event(
                tenant_id=tenant_id,
                event_type="RISK_RUN",
                action="CREATED",
                entity_type="risk_run",
                entity_id=run.id,
                actor_type="SYSTEM",
                payload={
                    "assessment_id": assessment_id,
                    "seed": final_seed,
                    "seed_strategy": seed_strategy,
                    "iterations": iterations,
                    "engine_version": engine_version,
                    "model_version_id": model_version_id,
                },
            )
        except Exception as e:
            # Log error but don't fail the operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to emit audit event for run {run.id}: {e}")

        return run

    def execute_run(self, run_id: str) -> RiskRun:
        """
        Execute a risk run.

        Steps:
        1. Load run and assessment
        2. Update status to RUNNING
        3. Emit STARTED audit event
        4. Run engine with seeded RNG
        5. Store result and hash
        6. Update status to SUCCEEDED
        7. Emit COMPLETED audit event
        8. Return updated run

        Args:
            run_id: Run ID

        Returns:
            Updated RiskRun instance with result

        Raises:
            NotFoundError: If run not found
            RuntimeError: If engine execution fails
        """
        # Load run (need to get tenant_id first)
        # Since we don't have tenant_id, query without tenant filter
        run = self.db.query(RiskRun).filter(RiskRun.id == run_id).first()
        if not run:
            raise NotFoundError(
                resource="risk_run",
                resource_id=run_id,
            )

        tenant_id = run.tenant_id

        # Load assessment
        assessment = self.assessment_repository.get_by_id(
            tenant_id, run.assessment_id
        )
        if not assessment:
            raise NotFoundError(
                resource="risk_assessment",
                resource_id=run.assessment_id,
            )

        # Update status to RUNNING
        started_at = datetime.utcnow()
        run = self.repository.update_status(
            run_id=run_id,
            status=RiskRunStatus.RUNNING,
            started_at=started_at,
        )

        # Emit STARTED audit event
        try:
            self.audit.append_event(
                tenant_id=tenant_id,
                event_type="RISK_RUN",
                action="STARTED",
                entity_type="risk_run",
                entity_id=run_id,
                actor_type="SYSTEM",
                payload={
                    "started_at": started_at.isoformat(),
                },
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to emit audit event for run {run_id} started: {e}")

        # Run engine with seeded RNG
        try:
            # Build input DTO
            input_dto = RiskEngineInputV3(
                tenant_id=tenant_id,
                risk_assessment_id=assessment.id,
                input_schema_version=assessment.input_schema_version,
                input_snapshot=assessment.input_snapshot_json,
                input_hash=assessment.input_hash,
                corridor_id=assessment.corridor_id,
            )

            # Build run config
            run_config = RiskEngineRunConfig(
                engine_version=run.engine_version,
                model_version_id=run.model_version_id,
                seed=run.seed,
                iterations=run.iterations,
            )

            # Execute engine (async, but we'll await it)
            import asyncio
            result_dto, result_hash = asyncio.run(
                self.engine.run(input_dto, run_config)
            )

            # Store result
            result_json = result_dto.model_dump(exclude_none=True, mode="json")
            run = self.repository.set_result(
                run_id=run_id,
                result_json=result_json,
                result_hash=result_hash,
            )

            # Emit COMPLETED audit event
            try:
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="RISK_RUN",
                    action="COMPLETED",
                    entity_type="risk_run",
                    entity_id=run_id,
                    actor_type="SYSTEM",
                    payload={
                        "result_hash": result_hash,
                        "completed_at": run.completed_at.isoformat()
                        if run.completed_at
                        else None,
                    },
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to emit audit event for run {run_id} completed: {e}"
                )

            return run

        except Exception as e:
            # Set error and emit FAILED audit event
            error_message = str(e)
            error_details = {
                "type": type(e).__name__,
                "message": error_message,
            }

            run = self.repository.set_error(
                run_id=run_id,
                error_message=error_message,
                error_details=error_details,
            )

            # Emit FAILED audit event
            try:
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="RISK_RUN",
                    action="FAILED",
                    entity_type="risk_run",
                    entity_id=run_id,
                    actor_type="SYSTEM",
                    payload={
                        "error_type": type(e).__name__,
                        "error_message": error_message,
                        "completed_at": run.completed_at.isoformat()
                        if run.completed_at
                        else None,
                    },
                )
            except Exception as audit_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to emit audit event for run {run_id} failed: {audit_error}"
                )

            raise RuntimeError(f"Engine execution failed: {error_message}") from e

    def get_run_with_provenance(
        self, tenant_id: str, run_id: str
    ) -> RiskRunWithProvenance:
        """
        Get run with full provenance information.

        Returns run, assessment, and provenance metadata.

        Args:
            tenant_id: Tenant ID
            run_id: Run ID

        Returns:
            RiskRunWithProvenance with run, assessment, and provenance

        Raises:
            NotFoundError: If run or assessment not found
        """
        # Get run
        run = self.repository.get_by_id(tenant_id, run_id)
        if not run:
            raise NotFoundError(
                resource="risk_run",
                resource_id=run_id,
            )

        # Get assessment
        assessment = self.assessment_repository.get_by_id(
            tenant_id, run.assessment_id
        )
        if not assessment:
            raise NotFoundError(
                resource="risk_assessment",
                resource_id=run.assessment_id,
            )

        # Build provenance
        provenance = {
            "run_id": run.id,
            "assessment_id": assessment.id,
            "input_hash": assessment.input_hash,
            "input_schema_version": assessment.input_schema_version,
            "seed": run.seed,
            "seed_strategy": run.seed_strategy,
            "iterations": run.iterations,
            "engine_version": run.engine_version,
            "model_version_id": run.model_version_id,
            "result_hash": run.result_hash,
            "status": run.status.value if hasattr(run.status, "value") else str(run.status),
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }

        return RiskRunWithProvenance(
            run=run,
            assessment=assessment,
            provenance=provenance,
        )
