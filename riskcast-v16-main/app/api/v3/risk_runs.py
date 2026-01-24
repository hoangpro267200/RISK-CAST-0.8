"""
Risk Run API v3
Complete API for risk runs with provenance, replay, and evidence linking.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
from uuid import UUID
import logging

from app.api.deps.rbac import PermissionChecker
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.database import get_db
from app.services.risk_run_service import RiskRunService
from app.repositories.risk_run_repository import RiskRunRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.core.risk_runs.replay import RiskRunReplayer
from app.services.evidence_service import EvidenceService
from app.schemas.risk_run import (
    RiskRunDetailResponse,
    RiskRunProvenanceResponse,
    ReplayResultResponse,
    RiskRunStatus,
)
from app.schemas.evidence import EvidenceObjectResponse, EvidenceLinkResponse
from app.models.evidence_link import EvidenceLink
from app.shared.exceptions import NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk/runs", tags=["Risk Runs"])


@router.get(
    "/{run_id}",
    response_model=RiskRunDetailResponse,
    summary="Get risk run",
    description="Get full risk run details with provenance"
)
async def get_run(
    run_id: str,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:read"))
) -> RiskRunDetailResponse:
    """
    Get full risk run details with provenance.
    
    Includes:
    - Full run configuration
    - Results (if completed)
    - Error info (if failed)
    - Job status
    """
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
        from app.models.risk_run_job import RiskRunJob
        job = db.query(RiskRunJob).filter(RiskRunJob.run_id == run_id).first()
        job_id = job.id if job else None
        job_status = job.status.value if job and hasattr(job.status, 'value') else (str(job.status) if job else None)
        
        # Convert model status to schema enum
        model_status_str = run.status.value if hasattr(run.status, 'value') else str(run.status)
        run_status = RiskRunStatus(model_status_str)
        
        return RiskRunDetailResponse(
            id=run.id,
            tenant_id=run.tenant_id,
            assessment_id=run.assessment_id,
            status=run_status,
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
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    finally:
        db.close()


@router.get(
    "/{run_id}/provenance",
    response_model=RiskRunProvenanceResponse,
    summary="Get run provenance",
    description="Get detailed provenance information for audit and reproducibility"
)
async def get_run_provenance(
    run_id: str,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:read"))
) -> RiskRunProvenanceResponse:
    """
    Get detailed provenance information for audit and reproducibility.
    
    Includes all fields needed to reproduce the run:
    - Input hash from assessment
    - Seed and seed strategy
    - Engine and model versions
    - Result hash (if completed)
    """
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
        
        # Get assessment for input_hash
        assessment_repo = RiskAssessmentRepository(db)
        assessment = assessment_repo.get_by_id(context.tenant_id, run.assessment_id)
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment {run.assessment_id} not found"
            )
        
        return RiskRunProvenanceResponse(
            run_id=run.id,
            assessment_id=run.assessment_id,
            input_hash=assessment.input_hash,
            seed=run.seed,
            seed_strategy=run.seed_strategy,
            iterations=run.iterations,
            engine_version=run.engine_version,
            model_version_id=run.model_version_id,
            result_hash=run.result_hash,
            computed_at=run.completed_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    finally:
        db.close()


@router.post(
    "/{run_id}/replay",
    response_model=ReplayResultResponse,
    summary="Replay risk run",
    description="Trigger replay verification to check reproducibility"
)
async def replay_run(
    run_id: str,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:read"))
) -> ReplayResultResponse:
    """
    Trigger replay verification to check reproducibility.
    
    Re-executes the run with the same parameters and compares results.
    Returns verification status and diff if mismatch.
    """
    db = next(get_db())
    try:
        # Verify run exists and tenant access
        run_repo = RiskRunRepository(db)
        run = run_repo.get_by_id(context.tenant_id, run_id)
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )
        
        # Replay run
        replayer = RiskRunReplayer(db)
        replay_result = replayer.replay(run_id)
        
        return ReplayResultResponse(
            run_id=replay_result.run_id,
            matches=replay_result.matches,
            original_hash=replay_result.original_hash,
            replay_hash=replay_result.replay_hash,
            diff_summary=replay_result.diff_summary,
            error=replay_result.error,
            replay_duration_seconds=replay_result.replay_duration_seconds
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error replaying run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error replaying run: {str(e)}"
        )
    finally:
        db.close()


@router.get(
    "/{run_id}/evidence",
    response_model=List[EvidenceObjectResponse],
    summary="Get run evidence",
    description="Get all evidence linked to a risk run"
)
async def get_run_evidence(
    run_id: str,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:read"))
) -> List[EvidenceObjectResponse]:
    """
    Get all evidence linked to a risk run.
    
    Returns list of evidence objects with their metadata.
    """
    db = next(get_db())
    try:
        # Verify run exists and tenant access
        run_repo = RiskRunRepository(db)
        run = run_repo.get_by_id(context.tenant_id, run_id)
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )
        
        # Get evidence for entity
        evidence_service = EvidenceService(db)
        evidence_list = evidence_service.get_evidence_for_entity(
            tenant_id=context.tenant_id,
            entity_type="risk_run",
            entity_id=run_id
        )
        
        # Convert to response
        return [
            EvidenceObjectResponse(
                id=evidence.id,
                tenant_id=evidence.tenant_id,
                content_hash=evidence.content_hash,
                content_type=evidence.content_type,
                content_size_bytes=evidence.content_size_bytes,
                storage_uri=evidence.storage_uri,
                storage_provider=evidence.storage_provider,
                filename=evidence.filename,
                description=evidence.description,
                metadata_json=evidence.metadata_json or {},
                evidence_type=evidence.evidence_type,
                is_pii=evidence.is_pii,
                retention_class=evidence.retention_class,
                created_by_user_id=evidence.created_by_user_id,
                created_at=evidence.created_at,
                expires_at=evidence.expires_at,
                deleted_at=evidence.deleted_at
            )
            for evidence in evidence_list
        ]
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    finally:
        db.close()


@router.post(
    "/{run_id}/evidence",
    response_model=EvidenceLinkResponse,
    summary="Attach evidence to run",
    description="Attach evidence object to a risk run"
)
async def attach_evidence(
    run_id: str,
    evidence_id: str,
    link_type: str = "ATTACHMENT",
    description: Optional[str] = None,
    request: Request = None,
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("risk:write"))
) -> EvidenceLinkResponse:
    """
    Attach evidence object to a risk run.
    
    Creates a link between the evidence and the run.
    """
    db = next(get_db())
    try:
        # Verify run exists and tenant access
        run_repo = RiskRunRepository(db)
        run = run_repo.get_by_id(context.tenant_id, run_id)
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )
        
        # Link evidence
        evidence_service = EvidenceService(db)
        link = evidence_service.link_evidence(
            tenant_id=context.tenant_id,
            evidence_id=evidence_id,
            entity_type="risk_run",
            entity_id=run_id,
            link_type=link_type,
            description=description,
            created_by_user_id=context.user_id
        )
        
        return EvidenceLinkResponse(
            id=link.id,
            tenant_id=link.tenant_id,
            evidence_id=link.evidence_id,
            entity_type=link.entity_type,
            entity_id=link.entity_id,
            link_type=link.link_type,
            description=link.description,
            created_at=link.created_at
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        if "IntegrityError" in str(type(e).__name__) or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Evidence already linked to this run"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error attaching evidence: {str(e)}"
        )
    finally:
        db.close()
