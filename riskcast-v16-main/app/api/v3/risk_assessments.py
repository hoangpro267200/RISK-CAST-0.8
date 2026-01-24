"""
Risk Assessment API v3
Complete CRUD API for risk assessments with runs linking.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
from uuid import UUID
import logging

from app.api.deps.rbac import PermissionChecker
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.database import get_db
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.risk_run_service import RiskRunService
from app.repositories.risk_run_repository import RiskRunRepository
from app.schemas.risk_assessment import (
    RiskAssessmentCreateRequest,
    RiskAssessmentResponse,
    RiskAssessmentDetailResponse,
    RiskRunSummaryResponse,
)
from app.schemas.risk_run import RiskRunConfig, RiskRunResponse, RiskRunStatus
from app.workers.job_scheduler import JobScheduler
from app.shared.exceptions import NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk/assessments", tags=["Risk Assessments"])


@router.post(
    "",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create risk assessment",
    description="Create a new risk assessment with canonicalized input and deduplication"
)
async def create_assessment(
    data: RiskAssessmentCreateRequest,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:write"))
) -> RiskAssessmentResponse:
    """
    Create a new risk assessment.
    
    Steps:
    1. Canonicalize input data
    2. Compute input hash
    3. Check for existing assessment (deduplication)
    4. Create or return existing assessment
    5. Return with input_hash
    """
    db = next(get_db())
    try:
        service = RiskAssessmentService(db)
        
        # Create assessment (or get existing if duplicate)
        assessment = service.create_assessment(
            tenant_id=context.tenant_id,
            raw_input=data.shipment_data,
            schema_version=data.schema_version,
            corridor_id=data.corridor_id,
            created_by_user_id=context.user_id
        )
        
        return RiskAssessmentResponse(
            id=assessment.id,
            tenant_id=assessment.tenant_id,
            input_hash=assessment.input_hash,
            schema_version=assessment.input_schema_version,
            shipment_id=assessment.shipment_id,
            corridor_id=assessment.corridor_id,
            created_by_user_id=assessment.created_by_user_id,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        db.close()


@router.get(
    "/{assessment_id}",
    response_model=RiskAssessmentDetailResponse,
    summary="Get risk assessment",
    description="Get risk assessment details including input snapshot and linked runs"
)
async def get_assessment(
    assessment_id: str,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:read"))
) -> RiskAssessmentDetailResponse:
    """
    Get risk assessment details.
    
    Includes:
    - Full input snapshot (canonicalized)
    - Input hash
    - Linked risk runs
    """
    db = next(get_db())
    try:
        service = RiskAssessmentService(db)
        try:
            assessment = service.get_assessment(context.tenant_id, assessment_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment {assessment_id} not found"
            )
        
        # Get linked runs
        run_repo = RiskRunRepository(db)
        runs = run_repo.list_by_assessment(context.tenant_id, assessment_id)
        
        # Convert runs to summary responses
        run_summaries = [
            RiskRunSummaryResponse(
                id=run.id,
                status=run.status.value if hasattr(run.status, 'value') else str(run.status),
                engine_version=run.engine_version,
                iterations=run.iterations,
                created_at=run.created_at,
                started_at=run.started_at,
                completed_at=run.completed_at,
                result_hash=run.result_hash
            )
            for run in runs
        ]
        
        return RiskAssessmentDetailResponse(
            id=assessment.id,
            tenant_id=assessment.tenant_id,
            input_hash=assessment.input_hash,
            schema_version=assessment.input_schema_version,
            input_snapshot=assessment.input_snapshot_json or {},
            shipment_id=assessment.shipment_id,
            corridor_id=assessment.corridor_id,
            created_by_user_id=assessment.created_by_user_id,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            runs=run_summaries
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    finally:
        db.close()


@router.get(
    "/{assessment_id}/runs",
    response_model=List[RiskRunSummaryResponse],
    summary="List assessment runs",
    description="List all risk runs for an assessment"
)
async def list_assessment_runs(
    assessment_id: str,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:read"))
) -> List[RiskRunSummaryResponse]:
    """
    List all risk runs for an assessment.
    
    Returns summary information for each run.
    """
    db = next(get_db())
    try:
        # Verify assessment exists and tenant access
        assessment_service = RiskAssessmentService(db)
        try:
            assessment = assessment_service.get_assessment(context.tenant_id, assessment_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment {assessment_id} not found"
            )
        
        # Get runs
        run_repo = RiskRunRepository(db)
        runs = run_repo.list_by_assessment(context.tenant_id, assessment_id)
        
        # Convert to summary responses
        return [
            RiskRunSummaryResponse(
                id=run.id,
                status=run.status.value if hasattr(run.status, 'value') else str(run.status),
                engine_version=run.engine_version,
                iterations=run.iterations,
                created_at=run.created_at,
                started_at=run.started_at,
                completed_at=run.completed_at,
                result_hash=run.result_hash
            )
            for run in runs
        ]
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    finally:
        db.close()


@router.post(
    "/{assessment_id}/runs",
    response_model=RiskRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create run for assessment",
    description="Create and enqueue a risk run for an assessment"
)
async def create_run_for_assessment(
    assessment_id: str,
    config: Optional[RiskRunConfig] = None,
    request: Request = None,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:run"))
) -> RiskRunResponse:
    """
    Create and enqueue a risk run for an assessment.
    
    Returns 202 Accepted with run_id and status URL.
    The run will be processed asynchronously by background workers.
    """
    db = next(get_db())
    try:
        # Verify assessment exists and tenant access
        assessment_service = RiskAssessmentService(db)
        try:
            assessment = assessment_service.get_assessment(context.tenant_id, assessment_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment {assessment_id} not found"
            )
        
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
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    finally:
        db.close()


@router.get(
    "",
    response_model=List[RiskAssessmentResponse],
    summary="List risk assessments",
    description="List risk assessments for the current tenant"
)
async def list_assessments(
    skip: int = 0,
    limit: int = 50,
    request: Request = None,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:read"))
) -> List[RiskAssessmentResponse]:
    """
    List risk assessments with pagination.
    
    Returns assessments for the current tenant.
    """
    db = next(get_db())
    try:
        # List assessments - query repository directly since service doesn't have list method
        from app.repositories.risk_assessment_repository import RiskAssessmentRepository
        repo = RiskAssessmentRepository(db)
        
        # Get all assessments for tenant (with pagination)
        all_assessments = repo.list_by_shipment(context.tenant_id, None) if hasattr(repo, 'list_by_shipment') else []
        
        # Simple pagination (in production, use proper pagination)
        assessments = all_assessments[skip:skip + limit] if all_assessments else []
        
        return [
            RiskAssessmentResponse(
                id=a.id,
                tenant_id=a.tenant_id,
                input_hash=a.input_hash,
                schema_version=a.input_schema_version,
                shipment_id=a.shipment_id,
                corridor_id=a.corridor_id,
                created_by_user_id=a.created_by_user_id,
                created_at=a.created_at,
                updated_at=a.updated_at
            )
            for a in assessments
        ]
    finally:
        db.close()
