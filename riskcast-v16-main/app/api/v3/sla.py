"""
SLA monitoring API endpoints.

SLA definitions, measurements, breaches, and compliance reporting.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker
from app.services.sla_monitoring_service import (
    SLAMonitoringService,
    SLANotFoundError,
    BreachNotFoundError,
    InvalidBreachStateError
)
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sla", tags=["SLA Monitoring"])


def get_sla_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> SLAMonitoringService:
    """Dependency to get SLAMonitoringService."""
    audit = AuditLedger(db)
    return SLAMonitoringService(db, audit)


# ==================== SLA Definitions ====================

@router.post("/definitions", status_code=status.HTTP_201_CREATED)
async def create_sla(
    name: str = Query(...),
    category: str = Query(..., description="AVAILABILITY, RESPONSE_TIME, PROCESSING_TIME, DATA_QUALITY"),
    metric_name: str = Query(...),
    target_value: float = Query(...),
    comparison: str = Query(..., description=">=, <=, =="),
    description: Optional[str] = Query(None),
    metric_unit: Optional[str] = Query(None),
    warning_threshold: Optional[float] = Query(None),
    critical_threshold: Optional[float] = Query(None),
    measurement_window: Optional[str] = Query(None, description="HOURLY, DAILY, WEEKLY, MONTHLY"),
    measurement_config: Optional[Dict[str, Any]] = Body(None),
    contract_reference: Optional[str] = Query(None),
    penalty_config: Optional[Dict[str, Any]] = Body(None),
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:write"))
) -> dict:
    """
    Create a new SLA definition.
    """
    created_by = context.user_id or context.actor_id
    
    if not created_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        sla = service.create_sla(
            name=name,
            category=category,
            metric_name=metric_name,
            target_value=target_value,
            comparison=comparison,
            created_by=created_by,
            tenant_id=context.tenant_id,
            description=description,
            metric_unit=metric_unit,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            measurement_window=measurement_window,
            measurement_config=measurement_config,
            contract_reference=contract_reference,
            penalty_config=penalty_config
        )
        
        return {
            "id": sla.id,
            "name": sla.name,
            "category": sla.category,
            "metric_name": sla.metric_name,
            "target_value": sla.target_value,
            "status": sla.status,
            "created_at": sla.created_at.isoformat() if sla.created_at else None
        }
    except Exception as e:
        logger.error(f"Failed to create SLA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SLA: {str(e)}"
        )


@router.get("/definitions")
async def list_sla_definitions(
    category: Optional[str] = Query(None),
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:read"))
) -> List[dict]:
    """
    List active SLA definitions.
    """
    slas = service.get_active_slas(
        tenant_id=context.tenant_id,
        category=category
    )
    
    return [
        {
            "id": sla.id,
            "name": sla.name,
            "category": sla.category,
            "metric_name": sla.metric_name,
            "target_value": sla.target_value,
            "comparison": sla.comparison,
            "status": sla.status,
            "created_at": sla.created_at.isoformat() if sla.created_at else None
        }
        for sla in slas
    ]


@router.get("/definitions/{sla_id}")
async def get_sla_definition(
    sla_id: str,
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:read"))
) -> dict:
    """
    Get SLA definition details.
    """
    try:
        sla = service.get_sla(sla_id)
        return {
            "id": sla.id,
            "name": sla.name,
            "description": sla.description,
            "category": sla.category,
            "metric_name": sla.metric_name,
            "metric_unit": sla.metric_unit,
            "target_value": sla.target_value,
            "warning_threshold": sla.warning_threshold,
            "critical_threshold": sla.critical_threshold,
            "comparison": sla.comparison,
            "measurement_window": sla.measurement_window,
            "measurement_config": sla.measurement_config_json,
            "contract_reference": sla.contract_reference,
            "penalty_config": sla.penalty_config_json,
            "status": sla.status,
            "created_at": sla.created_at.isoformat() if sla.created_at else None
        }
    except SLANotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==================== Measurements ====================

@router.post("/measurements", status_code=status.HTTP_201_CREATED)
async def record_measurement(
    sla_definition_id: str = Query(...),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    measured_value: float = Query(...),
    sample_count: Optional[int] = Query(None),
    details: Optional[Dict[str, Any]] = Body(None),
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:write"))
) -> dict:
    """
    Record an SLA measurement.
    
    Automatically evaluates against SLA and creates breach if violated.
    """
    try:
        measurement = service.record_measurement(
            sla_definition_id=sla_definition_id,
            period_start=period_start,
            period_end=period_end,
            measured_value=measured_value,
            tenant_id=context.tenant_id,
            sample_count=sample_count,
            details=details
        )
        
        return {
            "id": measurement.id,
            "sla_definition_id": measurement.sla_definition_id,
            "measured_value": measurement.measured_value,
            "target_value": measurement.target_value,
            "status": measurement.status,
            "period_start": measurement.period_start.isoformat(),
            "period_end": measurement.period_end.isoformat(),
            "measured_at": measurement.measured_at.isoformat() if measurement.measured_at else None
        }
    except SLANotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==================== Breaches ====================

@router.get("/breaches")
async def list_breaches(
    status: Optional[str] = Query(None, description="OPEN, ACKNOWLEDGED, RESOLVED, CREDITED"),
    severity: Optional[str] = Query(None, description="WARNING, CRITICAL"),
    sla_definition_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:read"))
) -> List[dict]:
    """
    List SLA breaches with filters.
    """
    breaches = service.list_breaches(
        tenant_id=context.tenant_id,
        status=status,
        severity=severity,
        sla_definition_id=sla_definition_id,
        limit=limit
    )
    
    return [
        {
            "id": b.id,
            "sla_definition_id": b.sla_definition_id,
            "severity": b.severity,
            "target_value": b.target_value,
            "actual_value": b.actual_value,
            "variance": b.variance,
            "status": b.status,
            "occurred_at": b.occurred_at.isoformat(),
            "acknowledged_at": b.acknowledged_at.isoformat() if b.acknowledged_at else None,
            "resolved_at": b.resolved_at.isoformat() if b.resolved_at else None,
            "penalty_applied": b.penalty_applied,
            "penalty_amount_cents": b.penalty_amount_cents,
            "penalty_currency": b.penalty_currency
        }
        for b in breaches
    ]


@router.post("/breaches/{breach_id}/acknowledge")
async def acknowledge_breach(
    breach_id: str,
    notes: Optional[str] = Body(None),
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:write"))
) -> dict:
    """
    Acknowledge a breach.
    
    Moves breach from OPEN to ACKNOWLEDGED.
    """
    acknowledged_by = context.user_id or context.actor_id
    
    if not acknowledged_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        breach = service.acknowledge_breach(
            breach_id=breach_id,
            acknowledged_by=acknowledged_by,
            notes=notes
        )
        
        return {
            "id": breach.id,
            "status": breach.status,
            "acknowledged_at": breach.acknowledged_at.isoformat() if breach.acknowledged_at else None
        }
    except BreachNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidBreachStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/breaches/{breach_id}/resolve")
async def resolve_breach(
    breach_id: str,
    root_cause: str = Body(...),
    resolution_notes: str = Body(...),
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:write"))
) -> dict:
    """
    Resolve a breach.
    
    Moves breach from OPEN/ACKNOWLEDGED to RESOLVED.
    """
    resolved_by = context.user_id or context.actor_id
    
    if not resolved_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        breach = service.resolve_breach(
            breach_id=breach_id,
            resolved_by=resolved_by,
            root_cause=root_cause,
            resolution_notes=resolution_notes
        )
        
        return {
            "id": breach.id,
            "status": breach.status,
            "resolved_at": breach.resolved_at.isoformat() if breach.resolved_at else None,
            "root_cause": breach.root_cause
        }
    except BreachNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidBreachStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/breaches/{breach_id}/penalty")
async def apply_penalty(
    breach_id: str,
    amount_cents: int = Body(...),
    currency: str = Body(..., description="Currency code (e.g., USD)"),
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:penalty"))
) -> dict:
    """
    Apply penalty for a breach.
    
    Moves breach to CREDITED status.
    """
    applied_by = context.user_id or context.actor_id
    
    if not applied_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        breach = service.apply_penalty(
            breach_id=breach_id,
            amount_cents=amount_cents,
            currency=currency,
            applied_by=applied_by
        )
        
        return {
            "id": breach.id,
            "status": breach.status,
            "penalty_applied": breach.penalty_applied,
            "penalty_amount_cents": breach.penalty_amount_cents,
            "penalty_currency": breach.penalty_currency
        }
    except BreachNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==================== Reporting ====================

@router.get("/compliance-report")
async def get_compliance_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    service: SLAMonitoringService = Depends(get_sla_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("sla:read"))
) -> dict:
    """
    Generate SLA compliance report.
    
    Returns overall compliance percentage and detailed breakdown by SLA.
    """
    try:
        report = service.get_sla_compliance_report(
            tenant_id=context.tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        return report
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )
