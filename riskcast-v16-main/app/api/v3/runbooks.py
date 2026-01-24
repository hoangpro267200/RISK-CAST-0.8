"""
Operational runbook API endpoints.

Runbooks and their executions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker
from app.services.runbook_service import (
    RunbookService,
    RunbookNotFoundError,
    RunbookExistsError,
    InvalidRunbookStateError,
    InvalidRunbookError,
    ExecutionNotFoundError,
    InvalidExecutionStateError
)
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runbooks", tags=["Operational Runbooks"])


def get_runbook_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> RunbookService:
    """Dependency to get RunbookService."""
    audit = AuditLedger(db)
    return RunbookService(db, audit)


# ==================== Runbooks ====================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_runbook(
    runbook_id: str = Query(..., description="Unique runbook identifier"),
    title: str = Query(...),
    category: str = Query(..., description="INCIDENT_RESPONSE, DISASTER_RECOVERY, MAINTENANCE, DEPLOYMENT, SECURITY"),
    steps: List[Dict[str, Any]] = Body(..., description="List of step dictionaries"),
    description: Optional[str] = Body(None),
    severity_level: Optional[str] = Query(None, description="P1, P2, P3, P4"),
    trigger_conditions: Optional[str] = Body(None),
    prerequisites: Optional[Dict[str, Any]] = Body(None),
    rollback_steps: Optional[List[Dict[str, Any]]] = Body(None),
    escalation_path: Optional[Dict[str, Any]] = Body(None),
    estimated_duration_minutes: Optional[int] = Query(None),
    owner_user_id: Optional[str] = Query(None),
    reviewer_user_id: Optional[str] = Query(None),
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:write"))
) -> dict:
    """
    Create a new runbook.
    """
    created_by = context.user_id or context.actor_id
    
    if not created_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        runbook = service.create_runbook(
            runbook_id=runbook_id,
            title=title,
            category=category,
            steps=steps,
            created_by=created_by,
            description=description,
            severity_level=severity_level,
            trigger_conditions=trigger_conditions,
            prerequisites=prerequisites,
            rollback_steps=rollback_steps,
            escalation_path=escalation_path,
            estimated_duration_minutes=estimated_duration_minutes,
            owner_user_id=owner_user_id,
            reviewer_user_id=reviewer_user_id
        )
        
        return {
            "id": runbook.id,
            "runbook_id": runbook.runbook_id,
            "title": runbook.title,
            "category": runbook.category,
            "status": runbook.status,
            "version": runbook.version,
            "created_at": runbook.created_at.isoformat() if runbook.created_at else None
        }
    except (RunbookExistsError, InvalidRunbookError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("")
async def list_runbooks(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="DRAFT, PUBLISHED, DEPRECATED"),
    severity_level: Optional[str] = Query(None),
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:read"))
) -> List[dict]:
    """
    List runbooks with filters.
    """
    runbooks = service.list_runbooks(
        category=category,
        status=status,
        severity_level=severity_level
    )
    
    return [
        {
            "id": r.id,
            "runbook_id": r.runbook_id,
            "title": r.title,
            "category": r.category,
            "severity_level": r.severity_level,
            "status": r.status,
            "version": r.version,
            "estimated_duration_minutes": r.estimated_duration_minutes,
            "owner_user_id": r.owner_user_id
        }
        for r in runbooks
    ]


@router.get("/{runbook_id}")
async def get_runbook(
    runbook_id: str,
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:read"))
) -> dict:
    """
    Get runbook details.
    """
    try:
        runbook = service.get_runbook(runbook_id)
        return {
            "id": runbook.id,
            "runbook_id": runbook.runbook_id,
            "title": runbook.title,
            "description": runbook.description,
            "category": runbook.category,
            "severity_level": runbook.severity_level,
            "status": runbook.status,
            "version": runbook.version,
            "trigger_conditions": runbook.trigger_conditions,
            "prerequisites": runbook.prerequisites_json,
            "steps": runbook.steps_json,
            "rollback_steps": runbook.rollback_steps_json,
            "escalation_path": runbook.escalation_path_json,
            "estimated_duration_minutes": runbook.estimated_duration_minutes,
            "last_tested_at": runbook.last_tested_at.isoformat() if runbook.last_tested_at else None,
            "owner_user_id": runbook.owner_user_id,
            "reviewer_user_id": runbook.reviewer_user_id,
            "created_at": runbook.created_at.isoformat() if runbook.created_at else None,
            "published_at": runbook.published_at.isoformat() if runbook.published_at else None
        }
    except RunbookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{runbook_id}/publish", status_code=status.HTTP_200_OK)
async def publish_runbook(
    runbook_id: str,
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:write"))
) -> dict:
    """
    Publish a runbook.
    
    Moves runbook from DRAFT to PUBLISHED status.
    """
    published_by = context.user_id or context.actor_id
    
    if not published_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        runbook = service.publish_runbook(
            runbook_id=runbook_id,
            published_by=published_by
        )
        
        return {
            "id": runbook.id,
            "runbook_id": runbook.runbook_id,
            "status": runbook.status,
            "published_at": runbook.published_at.isoformat() if runbook.published_at else None
        }
    except (RunbookNotFoundError, InvalidRunbookStateError, InvalidRunbookError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Executions ====================

@router.post("/{runbook_id}/executions", status_code=status.HTTP_201_CREATED)
async def start_execution(
    runbook_id: str,
    execution_type: str = Query("INCIDENT", description="INCIDENT, TEST, MAINTENANCE"),
    incident_reference: Optional[str] = Query(None),
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:execute"))
) -> dict:
    """
    Start a runbook execution.
    """
    executed_by = context.user_id or context.actor_id
    
    if not executed_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        execution = service.start_execution(
            runbook_id=runbook_id,
            executed_by=executed_by,
            execution_type=execution_type,
            incident_reference=incident_reference
        )
        
        return {
            "id": execution.id,
            "runbook_id": execution.runbook_id,
            "execution_type": execution.execution_type,
            "status": execution.status,
            "current_step": execution.current_step,
            "started_at": execution.started_at.isoformat()
        }
    except (RunbookNotFoundError, InvalidRunbookStateError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/executions/{execution_id}/steps/{step_number}/complete")
async def complete_step(
    execution_id: str,
    step_number: int,
    status: str = Body(..., description="COMPLETED, FAILED, SKIPPED"),
    notes: Optional[str] = Body(None),
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:execute"))
) -> dict:
    """
    Complete a step in the execution.
    """
    completed_by = context.user_id or context.actor_id
    
    if not completed_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        execution = service.complete_step(
            execution_id=execution_id,
            step_number=step_number,
            status=status,
            completed_by=completed_by,
            notes=notes
        )
        
        return {
            "id": execution.id,
            "current_step": execution.current_step,
            "step_results": execution.step_results_json,
            "status": execution.status
        }
    except (ExecutionNotFoundError, InvalidExecutionStateError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/executions/{execution_id}/complete")
async def complete_execution(
    execution_id: str,
    success: bool = Body(...),
    lessons_learned: Optional[str] = Body(None),
    deviations: Optional[List[str]] = Body(None),
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:execute"))
) -> dict:
    """
    Complete a runbook execution.
    """
    completed_by = context.user_id or context.actor_id
    
    if not completed_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        execution = service.complete_execution(
            execution_id=execution_id,
            success=success,
            completed_by=completed_by,
            lessons_learned=lessons_learned,
            deviations=deviations
        )
        
        return {
            "id": execution.id,
            "status": execution.status,
            "outcome": execution.outcome_json,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    except ExecutionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/executions/{execution_id}/abort")
async def abort_execution(
    execution_id: str,
    reason: Optional[str] = Body(None),
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:execute"))
) -> dict:
    """
    Abort a runbook execution.
    """
    aborted_by = context.user_id or context.actor_id
    
    if not aborted_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        execution = service.abort_execution(
            execution_id=execution_id,
            aborted_by=aborted_by,
            reason=reason
        )
        
        return {
            "id": execution.id,
            "status": execution.status,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    except (ExecutionNotFoundError, InvalidExecutionStateError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:read"))
) -> dict:
    """
    Get execution details.
    """
    try:
        execution = service.get_execution(execution_id)
        runbook = service.get_runbook(execution.runbook_id)
        
        return {
            "id": execution.id,
            "runbook": {
                "id": runbook.id,
                "runbook_id": runbook.runbook_id,
                "title": runbook.title
            },
            "execution_type": execution.execution_type,
            "incident_reference": execution.incident_reference,
            "status": execution.status,
            "current_step": execution.current_step,
            "step_results": execution.step_results_json,
            "outcome": execution.outcome_json,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "executed_by_user_id": execution.executed_by_user_id
        }
    except (ExecutionNotFoundError, RunbookNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{runbook_id}/executions")
async def get_execution_history(
    runbook_id: str,
    limit: int = Query(10, ge=1, le=100),
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:read"))
) -> List[dict]:
    """
    Get execution history for a runbook.
    """
    try:
        executions = service.get_execution_history(runbook_id, limit=limit)
        
        return [
            {
                "id": e.id,
                "execution_type": e.execution_type,
                "incident_reference": e.incident_reference,
                "status": e.status,
                "current_step": e.current_step,
                "outcome": e.outcome_json,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "executed_by_user_id": e.executed_by_user_id
            }
            for e in executions
        ]
    except RunbookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/executions/active")
async def get_active_executions(
    execution_type: Optional[str] = Query(None, description="INCIDENT, TEST, MAINTENANCE"),
    service: RunbookService = Depends(get_runbook_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("runbook:read"))
) -> List[dict]:
    """
    Get active (in-progress) executions.
    """
    executions = service.get_active_executions(execution_type=execution_type)
    
    return [
        {
            "id": e.id,
            "runbook_id": e.runbook_id,
            "execution_type": e.execution_type,
            "incident_reference": e.incident_reference,
            "status": e.status,
            "current_step": e.current_step,
            "started_at": e.started_at.isoformat(),
            "executed_by_user_id": e.executed_by_user_id
        }
        for e in executions
    ]
