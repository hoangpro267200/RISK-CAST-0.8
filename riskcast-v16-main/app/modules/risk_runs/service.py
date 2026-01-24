"""
Risk Runs Service
Business logic for risk calculation run orchestration
RISKCAST V3 - Modular Monolith
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import logging

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession

from app.modules.risk_runs.models import (
    RiskRun, RiskRunJob, RiskRunStatus, RiskRunJobStatus, SeedStrategy
)
from app.modules.risk_runs.schemas import RiskRunCreate
from app.modules.risk_runs.exceptions import RunNotFoundError, RunValidationError
from app.modules.risk_assessments.models import RiskAssessment
from app.modules.risk_assessments.exceptions import AssessmentNotFoundError
from app.modules.risk_engine_v3.service import RiskEngineV3
from app.modules.risk_engine_v3.schemas import RiskEngineResultV3
from app.core.audit_ledger.ledger import AuditLedger
from app.modules.audit_ledger.schemas import AuditContext
from app.modules.audit_ledger.models import ActorType as LegacyActorType

logger = logging.getLogger(__name__)


class RiskRunService:
    """
    Risk Run Orchestration Service.
    
    Handles:
    - Creating and enqueueing risk runs
    - Managing run lifecycle (queued, running, succeeded, failed)
    - Integrating with RiskEngineV3
    - Audit event logging
    """
    
    DEFAULT_ITERATIONS = 10000
    
    def __init__(self, db: 'TenantScopedSession', audit: Optional[AuditLedger] = None):
        """
        Initialize risk run service.
        
        Args:
            db: Tenant-scoped database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.engine = RiskEngineV3()
        # Audit ledger needs raw session, not tenant-scoped
        self.audit = audit or AuditLedger(db._raw_session)
        logger.debug(f"RiskRunService initialized for tenant_id={db.tenant_id}")
    
    async def create_run(
        self,
        assessment_id: str,
        user_id: str,
        context: AuditContext,
        model_version_id: Optional[str] = None,
        iterations: Optional[int] = None,
        seed_strategy: SeedStrategy = SeedStrategy.DETERMINISTIC_INPUT_HASH,
        seed: Optional[int] = None,
        options: Optional[dict] = None
    ) -> RiskRun:
        """
        Create and enqueue a new risk run.
        
        Steps:
        1. Load assessment
        2. Determine iterations
        3. Compute seed based on strategy
        4. Create run record
        5. Create job record
        6. Emit audit event
        
        Args:
            assessment_id: Risk assessment ID
            user_id: User ID creating the run
            context: Audit context
            model_version_id: Optional model version ID
            iterations: Number of Monte Carlo iterations (default: DEFAULT_ITERATIONS)
            seed_strategy: Seed strategy (DETERMINISTIC_INPUT_HASH or USER_PROVIDED)
            seed: User-provided seed (required if seed_strategy=USER_PROVIDED)
            options: Additional options (scenario_set_id, toggles, etc.)
            
        Returns:
            Created RiskRun instance
            
        Raises:
            AssessmentNotFoundError: If assessment not found
            RunValidationError: If validation fails
        """
        # Load assessment
        assessment = self.db.query(RiskAssessment).filter(
            RiskAssessment.id == assessment_id
        ).first()
        
        if not assessment:
            raise AssessmentNotFoundError(assessment_id)
        
        # Determine iterations
        final_iterations = iterations or self.DEFAULT_ITERATIONS
        
        if final_iterations <= 0:
            raise RunValidationError("iterations must be positive", field="iterations")
        
        # Compute seed based on strategy
        if seed_strategy == SeedStrategy.DETERMINISTIC_INPUT_HASH:
            final_seed = self.engine.compute_deterministic_seed(
                assessment.input_hash,
                model_version_id,
                final_iterations,
                self.engine.RESULT_SCHEMA_VERSION
            )
        elif seed_strategy == SeedStrategy.USER_PROVIDED:
            if seed is None:
                raise RunValidationError(
                    "USER_PROVIDED seed strategy requires seed parameter",
                    field="seed"
                )
            final_seed = seed
        else:
            raise RunValidationError(
                f"Invalid seed strategy: {seed_strategy}",
                field="seed_strategy"
            )
        
        # Create run record
        run = RiskRun(
            tenant_id=self.db.tenant_id,  # Auto-set by TenantScopedSession
            risk_assessment_id=assessment_id,
            status=RiskRunStatus.QUEUED,
            engine_version=self.engine.engine_version,
            model_version_id=model_version_id,
            result_schema_version=self.engine.RESULT_SCHEMA_VERSION,
            seed_strategy=seed_strategy,
            seed=final_seed,
            iterations=final_iterations,
            options_json=options
        )
        
        self.db.add(run)
        self.db.flush()  # Get ID without committing
        
        # Create job record
        job = RiskRunJob(
            tenant_id=self.db.tenant_id,
            risk_run_id=run.id,
            status=RiskRunJobStatus.QUEUED
        )
        self.db.add(job)
        
        self.db.commit()
        
        logger.info(
            f"Created risk run {run.id} for assessment {assessment_id} "
            f"with seed={final_seed}, iterations={final_iterations}"
        )
        
        # Emit audit event
        try:
            self.audit.append_event(
                tenant_id=self.db.tenant_id,
                event_type="RISK_RUN",
                action="CREATED",
                entity_type="risk_run",
                entity_id=run.id,
                actor_type="USER",
                actor_id=str(user_id),
                payload={
                    "assessment_id": assessment_id,
                    "model_version_id": model_version_id,
                    "iterations": final_iterations,
                    "seed_strategy": seed_strategy.value if hasattr(seed_strategy, 'value') else str(seed_strategy),
                    "seed": final_seed,
                },
            )
        except Exception as e:
            # Log audit failure but don't fail the run creation
            logger.error(f"Failed to emit audit event for run {run.id}: {e}")
        
        return run
    
    async def get_run(self, run_id: str) -> RiskRun:
        """
        Get run by ID (tenant-scoped automatically).
        
        Args:
            run_id: Run ID (ULID)
            
        Returns:
            RiskRun instance
            
        Raises:
            RunNotFoundError: If run not found
        """
        run = self.db.query(RiskRun).filter(RiskRun.id == run_id).first()
        
        if not run:
            raise RunNotFoundError(run_id)
        
        return run
    
    async def update_run_started(self, run_id: str) -> None:
        """
        Mark run as started.
        
        Args:
            run_id: Run ID
            
        Raises:
            RunNotFoundError: If run not found
        """
        run = await self.get_run(run_id)
        
        if run.status != RiskRunStatus.QUEUED:
            raise RunValidationError(
                f"Cannot start run in status {run.status}",
                field="status"
            )
        
        run.status = RiskRunStatus.RUNNING
        run.started_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Marked run {run_id} as RUNNING")
        
        # Emit audit event
        try:
            self.audit.append_event(
                tenant_id=self.db.tenant_id,
                event_type="RISK_RUN",
                action="STARTED",
                entity_type="risk_run",
                entity_id=run_id,
                actor_type="SYSTEM",
                payload={
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event for run {run_id} started: {e}")
    
    async def update_run_completed(
        self,
        run_id: str,
        result: RiskEngineResultV3,
        result_hash: str
    ) -> None:
        """
        Mark run as completed with result.
        
        Args:
            run_id: Run ID
            result: Engine result DTO
            result_hash: SHA256 hash of canonical result
            
        Raises:
            RunNotFoundError: If run not found
            RunValidationError: If run is not in RUNNING status
        """
        run = await self.get_run(run_id)
        
        if run.status != RiskRunStatus.RUNNING:
            raise RunValidationError(
                f"Cannot complete run in status {run.status}",
                field="status"
            )
        
        run.status = RiskRunStatus.SUCCEEDED
        run.result_json = result.model_dump(exclude_none=True, mode='json')
        run.result_hash = result_hash
        run.completed_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(
            f"Marked run {run_id} as SUCCEEDED with result_hash {result_hash[:16]}..."
        )
        
        # Emit audit event
        try:
            self.audit.append_event(
                tenant_id=self.db.tenant_id,
                event_type="RISK_RUN",
                action="COMPLETED",
                entity_type="risk_run",
                entity_id=run_id,
                actor_type="SYSTEM",
                payload={
                    "result_hash": result_hash,
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event for run {run_id} completed: {e}")
    
    async def update_run_failed(
        self,
        run_id: str,
        error: Exception
    ) -> None:
        """
        Mark run as failed.
        
        Args:
            run_id: Run ID
            error: Exception that caused the failure
            
        Raises:
            RunNotFoundError: If run not found
        """
        run = await self.get_run(run_id)
        
        run.status = RiskRunStatus.FAILED
        run.error_json = {
            'type': type(error).__name__,
            'message': str(error),
            'traceback': None  # Could include traceback if needed
        }
        run.completed_at = datetime.utcnow()
        self.db.commit()
        
        logger.error(
            f"Marked run {run_id} as FAILED: {type(error).__name__}: {str(error)}"
        )
        
        # Emit audit event
        try:
            self.audit.append_event(
                tenant_id=self.db.tenant_id,
                event_type="RISK_RUN",
                action="FAILED",
                entity_type="risk_run",
                entity_id=run_id,
                actor_type="SYSTEM",
                payload={
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event for run {run_id} failed: {e}")
    
    async def cancel_run(self, run_id: str, user_id: str, context: AuditContext) -> None:
        """
        Cancel a queued or running run.
        
        Args:
            run_id: Run ID
            user_id: User ID canceling the run
            context: Audit context
            
        Raises:
            RunNotFoundError: If run not found
            RunValidationError: If run cannot be canceled
        """
        run = await self.get_run(run_id)
        
        if run.status not in [RiskRunStatus.QUEUED, RiskRunStatus.RUNNING]:
            raise RunValidationError(
                f"Cannot cancel run in status {run.status}",
                field="status"
            )
        
        run.status = RiskRunStatus.CANCELED
        run.completed_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Canceled run {run_id}")
        
        # Emit audit event
        try:
            self.audit.append_event(
                tenant_id=self.db.tenant_id,
                event_type="RISK_RUN",
                action="CANCELED",
                entity_type="risk_run",
                entity_id=run_id,
                actor_type="USER",
                actor_id=str(user_id),
                payload={
                    "canceled_at": run.completed_at.isoformat() if run.completed_at else None,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event for run cancellation: {e}")
    
    async def list_runs(
        self,
        assessment_id: Optional[str] = None,
        status: Optional[RiskRunStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> list[RiskRun]:
        """
        List runs for tenant.
        
        Args:
            assessment_id: Optional filter by assessment ID
            status: Optional filter by status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of RiskRun instances
        """
        query = self.db.query(RiskRun).order_by(RiskRun.created_at.desc())
        
        if assessment_id:
            query = query.filter(RiskRun.risk_assessment_id == assessment_id)
        
        if status:
            query = query.filter(RiskRun.status == status)
        
        runs = query.offset(skip).limit(limit).all()
        
        logger.debug(
            f"Listed {len(runs)} runs for tenant {self.db.tenant_id} "
            f"(assessment_id={assessment_id}, status={status})"
        )
        
        return runs
