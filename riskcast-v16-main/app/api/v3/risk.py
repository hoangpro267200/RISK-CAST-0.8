"""
Risk Assessment and Run API Endpoints
API v3 endpoints for risk assessments and runs
RISKCAST V3 - Modular Monolith
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import logging

# Import dependencies
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.shared.utils import build_audit_context
from app.modules.rbac_policy.service import require_permission
from app.modules.rbac_policy.constants import Permissions
from app.modules.risk_assessments.service import RiskAssessmentService
from app.modules.risk_assessments.schemas import (
    RiskAssessmentCreate,
    RiskAssessmentResponse,
    RiskAssessmentListResponse
)
from app.modules.risk_runs.service import RiskRunService
from app.modules.risk_runs.schemas import (
    RiskRunCreate,
    RiskRunResponse,
    RiskRunDetailResponse,
    RiskRunListResponse
)
from app.schemas.risk_run import (
    RiskRunConfig,
    RiskRunStatusResponse,
    RiskRunResultResponse,
    RiskRunStatus,
)
from app.workers.job_scheduler import JobScheduler
from app.modules.audit_ledger.schemas import AuditContext

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession, get_tenant_scoped_db

logger = logging.getLogger(__name__)

# Risk assessments router
router = APIRouter(prefix="/risk-assessments", tags=["risk"])


@router.post(
    "",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create risk assessment",
    description="Create a new risk assessment with normalized input data"
)
async def create_risk_assessment(
    data: RiskAssessmentCreate,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.RISK_WRITE))
):
    """
    Create a new risk assessment.
    
    The assessment will be created with status READY and input data will be
    hashed for deduplication.
    """
    # Get tenant-scoped DB session
    from app.database import get_tenant_scoped_db, get_db
    
    # Get raw DB session
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        # Get tenant-scoped session (request has context in state from resolve_tenant_context)
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = RiskAssessmentService(db)
        assessment = await service.create_assessment(
            data=data,
            user_id=context.user_id,
            context=audit_context
        )
        
        return RiskAssessmentResponse(
            id=assessment.id,
            tenant_id=assessment.tenant_id,
            created_by_user_id=assessment.created_by_user_id,
            status=assessment.status.value if hasattr(assessment.status, 'value') else str(assessment.status),
            input_schema_version=assessment.input_schema_version,
            input_hash=assessment.input_hash,
            shipment_id=assessment.shipment_id,
            corridor_id=assessment.corridor_id,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at
        )
    finally:
        db_session.close()


@router.get(
    "/{assessment_id}",
    response_model=RiskAssessmentResponse,
    summary="Get risk assessment",
    description="Get risk assessment by ID"
)
async def get_risk_assessment(
    assessment_id: str,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """Get risk assessment by ID"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        service = RiskAssessmentService(db)
        assessment = await service.get_assessment(assessment_id)
        
        return RiskAssessmentResponse(
            id=assessment.id,
            tenant_id=assessment.tenant_id,
            created_by_user_id=assessment.created_by_user_id,
            status=assessment.status.value if hasattr(assessment.status, 'value') else str(assessment.status),
            input_schema_version=assessment.input_schema_version,
            input_hash=assessment.input_hash,
            shipment_id=assessment.shipment_id,
            corridor_id=assessment.corridor_id,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at
        )
    finally:
        db_session.close()


@router.get(
    "",
    response_model=RiskAssessmentListResponse,
    summary="List risk assessments",
    description="List risk assessments for the current tenant"
)
async def list_risk_assessments(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    request: Request = None,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """List risk assessments with pagination"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        service = RiskAssessmentService(db)
        assessments = await service.list_assessments(
            skip=skip,
            limit=limit,
            status=status
        )
        
        # TODO: Get total count for pagination
        total = len(assessments)  # Placeholder
        
        return RiskAssessmentListResponse(
            items=[
                RiskAssessmentResponse(
                    id=a.id,
                    tenant_id=a.tenant_id,
                    created_by_user_id=a.created_by_user_id,
                    status=a.status.value if hasattr(a.status, 'value') else str(a.status),
                    input_schema_version=a.input_schema_version,
                    input_hash=a.input_hash,
                    shipment_id=a.shipment_id,
                    corridor_id=a.corridor_id,
                    created_at=a.created_at,
                    updated_at=a.updated_at
                )
                for a in assessments
            ],
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit,
            has_next=len(assessments) == limit,
            has_prev=skip > 0
        )
    finally:
        db_session.close()


@router.post(
    "/{assessment_id}/runs",
    response_model=RiskRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue risk run",
    description="Queue a new risk run for an assessment"
)
async def create_risk_run(
    assessment_id: str,
    data: RiskRunCreate,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.RISK_RUN))
):
    """
    Queue a new risk run for an assessment.
    
    The run will be created with status QUEUED and a job will be created
    for background processing by workers.
    """
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        audit_context = build_audit_context(request)
        
        service = RiskRunService(db)
        run = await service.create_run(
            assessment_id=assessment_id,
            user_id=context.user_id,
            context=audit_context,
            model_version_id=data.model_version_id,
            iterations=data.iterations,
            seed_strategy=data.seed_strategy,
            seed=data.seed,
            options=data.options
        )
        
        return RiskRunResponse(
            id=run.id,
            tenant_id=run.tenant_id,
            risk_assessment_id=run.risk_assessment_id,
            status=run.status,
            engine_version=run.engine_version,
            model_version_id=run.model_version_id,
            result_schema_version=run.result_schema_version,
            seed_strategy=run.seed_strategy,
            seed=run.seed,
            iterations=run.iterations,
            options_json=run.options_json,
            result_json=run.result_json,
            result_hash=run.result_hash,
            error_json=run.error_json,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
            updated_at=run.updated_at,
            result=None,
            duration_seconds=None
        )
    finally:
        db_session.close()


# Separate router for runs (can query directly)
runs_router = APIRouter(prefix="/risk/runs", tags=["risk"])


@runs_router.post(
    "",
    response_model=RiskRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create risk run",
    description="Create a new risk run and enqueue it for async processing"
)
async def create_risk_run(
    assessment_id: str,
    config: Optional[RiskRunConfig] = None,
    request: Request = None,
    context: TenantContext = Depends(require_permission(Permissions.RISK_RUN))
):
    """
    Create a new risk run and enqueue it for async processing.
    
    Returns 202 Accepted with run_id and status URL.
    The run will be processed asynchronously by background workers.
    """
    from app.database import get_db
    from app.services.risk_run_service import RiskRunService
    from app.workers.job_scheduler import JobScheduler
    
    db = next(get_db())
    try:
        # Default config
        if config is None:
            config = RiskRunConfig()
        
        # Create run record
        run_service = RiskRunService(db, audit=None)  # Audit handled by worker
        run = run_service.create_run(
            tenant_id=context.tenant_id,
            assessment_id=assessment_id,
            seed=config.seed,
            seed_strategy=config.seed_strategy,
            iterations=config.iterations,
            model_version_id=config.model_version_id,
        )
        
        # Enqueue job
        scheduler = JobScheduler(db)
        job = scheduler.enqueue_risk_run(
            run_id=run.id,
            priority=config.priority,
            max_attempts=config.max_attempts
        )
        
        return RiskRunResponse(
            id=run.id,
            status=RiskRunStatus.PENDING,
            status_url=f"/api/v3/risk/runs/{run.id}/status"
        )
    finally:
        db.close()


@runs_router.get(
    "/{run_id}",
    response_model=RiskRunDetailResponse,
    summary="Get risk run",
    description="Get risk run details including results"
)
async def get_risk_run(
    run_id: str,
    request: Request = None,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """Get risk run details including results"""
    from app.database import get_db
    from app.services.risk_run_service import RiskRunService
    from app.repositories.risk_run_repository import RiskRunRepository
    from app.models.risk_run_job import RiskRunJob
    from app.workers.job_scheduler import JobScheduler
    
    db = next(get_db())
    try:
        # Get run
        run_repo = RiskRunRepository(db)
        run = run_repo.get_by_id(context.tenant_id, run_id)
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )
        
        # Get job info if exists
        job = db.query(RiskRunJob).filter(RiskRunJob.run_id == run_id).first()
        job_id = job.id if job else None
        job_status = job.status.value if job and hasattr(job.status, 'value') else (str(job.status) if job else None)
        
        return RiskRunDetailResponse(
            id=run.id,
            tenant_id=run.tenant_id,
            assessment_id=run.assessment_id,
            status=RiskRunStatus(run.status.value if hasattr(run.status, 'value') else str(run.status)),
            seed=run.seed,
            seed_strategy=run.seed_strategy,
            iterations=run.iterations,
            engine_version=run.engine_version,
            model_version_id=run.model_version_id,
            result_json=run.result_json,
            result_hash=run.result_hash,
            error_message=run.error_message,
            error_details=run.error_details,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            job_id=job_id,
            job_status=job_status
        )
    finally:
        db.close()


@runs_router.get(
    "/{run_id}/result",
    response_model=RiskRunResultResponse,
    summary="Get risk run result",
    description="Get risk run result (only if SUCCEEDED)"
)
async def get_risk_run_result(
    run_id: str,
    request: Request = None,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """
    Get risk run result.
    
    Returns result only if run status is SUCCEEDED.
    Returns 404 if run not found.
    Returns 409 if run not yet complete.
    """
    from app.database import get_db
    from app.repositories.risk_run_repository import RiskRunRepository
    from app.models.risk_run import RiskRunStatus
    
    db = next(get_db())
    try:
        run_repo = RiskRunRepository(db)
        run = run_repo.get_by_id(context.tenant_id, run_id)
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )
        
        run_status = RiskRunStatus(run.status.value if hasattr(run.status, 'value') else str(run.status))
        
        if run_status != RiskRunStatus.SUCCEEDED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Run {run_id} is not yet complete. Status: {run_status.value}"
            )
        
        if not run.result_json or not run.result_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Run completed but result data is missing"
            )
        
        return RiskRunResultResponse(
            id=run.id,
            status=run_status,
            result_json=run.result_json,
            result_hash=run.result_hash,
            completed_at=run.completed_at
        )
    finally:
        db.close()


@runs_router.get(
    "/{run_id}/status",
    response_model=RiskRunStatusResponse,
    summary="Get risk run status",
    description="Get risk run status with progress and ETA"
)
async def get_run_status(
    run_id: str,
    request: Request = None,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """
    Get risk run status with progress and ETA.
    
    Returns current status, progress estimate, and estimated time to completion.
    """
    from app.database import get_db
    from app.repositories.risk_run_repository import RiskRunRepository
    from app.models.risk_run import RiskRunStatus
    
    db = next(get_db())
    try:
        run_repo = RiskRunRepository(db)
        run = run_repo.get_by_id(context.tenant_id, run_id)
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )
        
        # Convert model status to schema enum
        model_status_str = run.status.value if hasattr(run.status, 'value') else str(run.status)
        run_status = RiskRunStatus(model_status_str)
        
        # Estimate progress
        progress = None
        eta_seconds = None
        
        if run_status == RiskRunStatus.SUCCEEDED:
            progress = 1.0
            eta_seconds = 0
        elif run_status == RiskRunStatus.FAILED:
            progress = 1.0
            eta_seconds = None
        elif run_status == RiskRunStatus.RUNNING and run.started_at:
            # Estimate based on typical execution time
            # Assume average execution time is 60 seconds
            elapsed = (datetime.utcnow() - run.started_at).total_seconds()
            estimated_total = 60.0  # seconds
            progress = min(0.95, elapsed / estimated_total)  # Cap at 95% until complete
            eta_seconds = max(0, int(estimated_total - elapsed))
        elif run_status == RiskRunStatus.PENDING:
            progress = 0.0
            eta_seconds = None
        
        return RiskRunStatusResponse(
            status=run_status,
            progress=progress,
            eta_seconds=eta_seconds,
            started_at=run.started_at,
            completed_at=run.completed_at
        )
    finally:
        db.close()


@runs_router.get(
    "",
    response_model=RiskRunListResponse,
    summary="List risk runs",
    description="List risk runs for the current tenant"
)
async def list_risk_runs(
    assessment_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    request: Request = None,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """List risk runs with pagination"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        service = RiskRunService(db)
        
        status_enum = None
        if status:
            try:
                status_enum = RiskRunStatus(status.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )
        
        runs = await service.list_runs(
            assessment_id=assessment_id,
            status=status_enum,
            skip=skip,
            limit=limit
        )
        
        # TODO: Get total count for pagination
        total = len(runs)  # Placeholder
        
        return RiskRunListResponse(
            items=[
                RiskRunResponse.from_orm_with_result(run)
                for run in runs
            ],
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit,
            has_next=len(runs) == limit,
            has_prev=skip > 0
        )
    finally:
        db_session.close()
