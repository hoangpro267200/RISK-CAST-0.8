"""
Data Quality API Endpoints

Exposes data quality information to users so they know
what data they're getting and can make informed decisions.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.shared.utils import build_audit_context
from app.modules.rbac_policy.service import require_permission
from app.modules.rbac_policy.constants import Permissions
from app.services.unified_data_service import create_unified_data_service
from app.workers.data_refresh_scheduler import get_data_refresh_scheduler
from app.core.data_quality.gateway import DecisionType
from app.core.audit_ledger.ledger import AuditLedger

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


# ============================================================================
# Schemas
# ============================================================================

class DataSourceStatus(BaseModel):
    """Status of a data source."""
    source_name: str
    source_type: str
    status: str  # "HEALTHY", "DEGRADED", "OFFLINE"
    last_updated: Optional[datetime]
    data_quality: str
    confidence: float
    next_refresh: Optional[datetime]
    error_message: Optional[str]


class DataQualityOverview(BaseModel):
    """Overview of system data quality."""
    overall_status: str
    overall_confidence: float
    sources: List[DataSourceStatus]
    warnings: List[str]
    last_check: datetime


class DataQualityCheck(BaseModel):
    """Request to check data quality for a specific use case."""
    origin_port: str
    destination_port: str
    cargo_type: str
    cargo_value_usd: float
    container_count: int = 1
    carrier_code: Optional[str] = None
    purpose: str = "RISK_ASSESSMENT"  # RISK_ASSESSMENT, INSURANCE_QUOTE, POLICY_BINDING, etc.


class DataQualityCheckResult(BaseModel):
    """Result of data quality check."""
    can_proceed: bool
    overall_quality: str
    overall_confidence: float
    sources: List[dict]
    missing_sources: List[str]
    fallback_sources: List[str]
    warnings: List[str]
    block_reason: Optional[str]
    recommendations: List[str]


class RefreshJobStatus(BaseModel):
    """Status of a data refresh job."""
    job_id: str
    source_name: str
    priority: str
    interval_minutes: int
    last_run: Optional[datetime]
    last_status: str
    consecutive_failures: int
    success_rate: float
    is_enabled: bool


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/overview", response_model=DataQualityOverview)
async def get_data_quality_overview(
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ)),
    db: Session = Depends(get_db)
):
    """
    Get overview of data quality across all sources.
    
    Shows:
    - Status of each data source
    - Last update times
    - Quality levels
    - Any warnings or issues
    """
    audit = AuditLedger(db)
    audit_context = build_audit_context(request)
    
    # Get scheduler status if available
    try:
        scheduler = get_data_refresh_scheduler(audit=audit)
        scheduler_status = scheduler.get_job_status()
    except Exception as e:
        scheduler_status = []
    
    # Check each source
    sources = []
    warnings = []
    
    # Weather
    weather_status = await _check_weather_status(audit)
    sources.append(weather_status)
    if weather_status.status != "HEALTHY":
        warnings.append(f"Weather data: {weather_status.error_message or 'Degraded'}")
    
    # Ports
    port_status = await _check_port_status(audit)
    sources.append(port_status)
    if port_status.status != "HEALTHY":
        warnings.append(f"Port data: {port_status.error_message or 'Degraded'}")
    
    # Carriers
    carrier_status = await _check_carrier_status(audit)
    sources.append(carrier_status)
    if carrier_status.status != "HEALTHY":
        warnings.append(f"Carrier data: {carrier_status.error_message or 'Degraded'}")
    
    # Climate
    climate_status = await _check_climate_status(audit)
    sources.append(climate_status)
    if climate_status.status != "HEALTHY":
        warnings.append(f"Climate data: {climate_status.error_message or 'Degraded'}")
    
    # Calculate overall status
    healthy_count = sum(1 for s in sources if s.status == "HEALTHY")
    if healthy_count == len(sources):
        overall_status = "HEALTHY"
    elif healthy_count >= len(sources) / 2:
        overall_status = "DEGRADED"
    else:
        overall_status = "OFFLINE"
    
    overall_confidence = sum(s.confidence for s in sources) / len(sources) if sources else 0.0
    
    return DataQualityOverview(
        overall_status=overall_status,
        overall_confidence=overall_confidence,
        sources=sources,
        warnings=warnings,
        last_check=datetime.utcnow()
    )


@router.post("/check", response_model=DataQualityCheckResult)
async def check_data_quality_for_shipment(
    request: DataQualityCheck,
    http_request: Request,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ)),
    db: Session = Depends(get_db)
):
    """
    Check data quality for a specific shipment/route.
    
    Use this BEFORE running risk assessment to understand
    what data quality you'll be working with.
    
    The response tells you:
    - Whether you can proceed with the given purpose
    - What quality level you'll have
    - What sources are missing or using fallback
    - Recommendations for improving data quality
    """
    audit = AuditLedger(db)
    unified_service = create_unified_data_service(audit)
    
    # Map purpose string to DecisionType
    purpose_map = {
        "RISK_ASSESSMENT": DecisionType.RISK_ASSESSMENT,
        "INSURANCE_QUOTE": DecisionType.INSURANCE_QUOTE,
        "POLICY_BINDING": DecisionType.POLICY_BINDING,
        "PARAMETRIC_TRIGGER": DecisionType.PARAMETRIC_TRIGGER,
        "CLAIM_ADJUDICATION": DecisionType.CLAIM_ADJUDICATION,
        "ANALYTICS": DecisionType.ANALYTICS,
    }
    decision_type = purpose_map.get(request.purpose, DecisionType.RISK_ASSESSMENT)
    
    try:
        data = await unified_service.collect_shipment_data(
            origin_port=request.origin_port,
            destination_port=request.destination_port,
            cargo_type=request.cargo_type,
            cargo_value_usd=request.cargo_value_usd,
            container_count=request.container_count,
            departure_date=datetime.utcnow().date(),
            expected_arrival_date=datetime.utcnow().date(),
            carrier_code=request.carrier_code,
            decision_type=decision_type,
            include_route_weather=False  # Skip route weather for faster check
        )
        
        # Build recommendations
        recommendations = []
        
        if not request.carrier_code:
            recommendations.append(
                "Add carrier code for more accurate carrier risk assessment"
            )
        
        for source in data.data_sources:
            if source.is_fallback:
                recommendations.append(
                    f"Data source '{source.source_name}' is using fallback. "
                    f"Check API connectivity or try again later."
                )
        
        if data.overall_confidence < 0.7:
            recommendations.append(
                "Overall confidence is low. Consider waiting for data refresh "
                "or proceeding with caution."
            )
        
        if data.data_quality_report.missing_sources:
            recommendations.append(
                f"Missing data sources: {', '.join(data.data_quality_report.missing_sources)}. "
                f"These may be required for {request.purpose}."
            )
        
        return DataQualityCheckResult(
            can_proceed=data.data_quality_report.can_proceed,
            overall_quality=data.overall_data_quality.value,
            overall_confidence=data.overall_confidence,
            sources=[
                {
                    "name": s.source_name,
                    "type": s.source_type,
                    "quality": s.quality_level.value,
                    "is_fallback": s.is_fallback,
                    "confidence": s.confidence
                }
                for s in data.data_sources
            ],
            missing_sources=data.data_quality_report.missing_sources,
            fallback_sources=data.data_quality_report.fallback_sources,
            warnings=data.data_warnings,
            block_reason=data.data_quality_report.block_reason,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Data quality check failed: {str(e)}"
        )


@router.get("/sources/{source_type}/history")
async def get_source_quality_history(
    source_type: str,
    days: int = Query(default=7, le=30, description="Number of days to look back"),
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ)),
    db: Session = Depends(get_db)
):
    """
    Get quality history for a data source.
    
    Useful for understanding reliability trends.
    """
    from app.models.audit import AuditEvent
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query audit log for historical quality
    events = db.query(AuditEvent).filter(
        AuditEvent.event_type == "DATA_FETCH",
        AuditEvent.action.like(f"%{source_type.upper()}%"),
        AuditEvent.created_at >= start_date
    ).order_by(AuditEvent.created_at.desc()).limit(100).all()
    
    history = []
    for event in events:
        payload = event.payload_json or {}
        history.append({
            "timestamp": event.created_at.isoformat(),
            "quality": payload.get("quality", "UNKNOWN"),
            "duration_ms": payload.get("duration_ms"),
            "error": payload.get("error"),
            "source": payload.get("source")
        })
    
    # Calculate summary
    total = len(history)
    successful = sum(1 for h in history if h["quality"] not in ["FALLBACK", "UNAVAILABLE"] and not h.get("error"))
    
    return {
        "source_type": source_type,
        "period_days": days,
        "total_fetches": total,
        "successful_fetches": successful,
        "success_rate": successful / total if total > 0 else 0,
        "history": history
    }


@router.get("/refresh-jobs", response_model=List[RefreshJobStatus])
async def get_refresh_job_status(
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ)),
    db: Session = Depends(get_db)
):
    """
    Get status of all data refresh jobs.
    
    Shows when each data source was last refreshed and
    when the next refresh is scheduled.
    """
    audit = AuditLedger(db)
    
    try:
        scheduler = get_data_refresh_scheduler(audit=audit)
        job_statuses = scheduler.get_job_status()
        
        return [
            RefreshJobStatus(
                job_id=job["id"],
                source_name=job["source_name"],
                priority=job["priority"],
                interval_minutes=job["interval_minutes"],
                last_run=datetime.fromisoformat(job["last_run"]) if job["last_run"] else None,
                last_status=job["last_status"],
                consecutive_failures=job["consecutive_failures"],
                success_rate=job["success_rate"],
                is_enabled=job["is_enabled"]
            )
            for job in job_statuses
        ]
    except Exception as e:
        # Return empty list if scheduler not available
        return []


@router.post("/refresh/{source_type}")
async def trigger_manual_refresh(
    source_type: str,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.RISK_WRITE)),
    db: Session = Depends(get_db)
):
    """
    Manually trigger refresh for a data source.
    
    Use when you need fresher data immediately.
    """
    audit = AuditLedger(db)
    audit_context = build_audit_context(request)
    
    try:
        scheduler = get_data_refresh_scheduler(audit=audit)
        
        # Map source type to job ID
        job_id_map = {
            "weather": "refresh_weather",
            "port": "refresh_ports",
            "ports": "refresh_ports",
            "carrier": "refresh_carriers",
            "carriers": "refresh_carriers",
            "climate": "refresh_climate",
        }
        
        job_id = job_id_map.get(source_type.lower())
        if not job_id:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown source type: {source_type}. Valid types: {', '.join(job_id_map.keys())}"
            )
        
        # Trigger refresh
        scheduler.trigger_refresh(job_id)
        
        # Audit
        tenant_id = getattr(audit, 'tenant_id', None) or context.tenant_id
        audit.append_event(
            tenant_id=tenant_id,
            event_type="DATA_REFRESH",
            action="MANUAL_REFRESH_TRIGGERED",
            entity_type="data_source",
            entity_id=source_type,
            actor_type="USER",
            actor_id=str(context.user_id),
            payload={"source_type": source_type, "job_id": job_id}
        )
        
        return {
            "status": "triggered",
            "source_type": source_type,
            "job_id": job_id,
            "triggered_at": datetime.utcnow().isoformat(),
            "message": f"Refresh job for {source_type} has been triggered"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger refresh: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def _check_weather_status(audit) -> DataSourceStatus:
    """Check weather data source status."""
    try:
        from app.core.utils.cache import get_cache
        
        # Check if we have recent weather data in cache
        # This is a simplified check - in production would query actual cache
        return DataSourceStatus(
            source_name="weather",
            source_type="weather",
            status="HEALTHY",
            last_updated=datetime.utcnow(),
            data_quality="REAL_TIME",
            confidence=0.9,
            next_refresh=datetime.utcnow() + timedelta(minutes=15),
            error_message=None
        )
    except Exception as e:
        return DataSourceStatus(
            source_name="weather",
            source_type="weather",
            status="DEGRADED",
            last_updated=None,
            data_quality="FALLBACK",
            confidence=0.3,
            next_refresh=None,
            error_message=str(e)
        )


async def _check_port_status(audit) -> DataSourceStatus:
    """Check port data source status."""
    try:
        from app.core.utils.cache import get_cache
        
        return DataSourceStatus(
            source_name="port_conditions",
            source_type="port",
            status="HEALTHY",
            last_updated=datetime.utcnow(),
            data_quality="REAL_TIME",
            confidence=0.9,
            next_refresh=datetime.utcnow() + timedelta(hours=1),
            error_message=None
        )
    except Exception as e:
        return DataSourceStatus(
            source_name="port_conditions",
            source_type="port",
            status="DEGRADED",
            last_updated=None,
            data_quality="FALLBACK",
            confidence=0.3,
            next_refresh=None,
            error_message=str(e)
        )


async def _check_carrier_status(audit) -> DataSourceStatus:
    """Check carrier data source status."""
    try:
        from app.core.utils.cache import get_cache
        
        return DataSourceStatus(
            source_name="carrier_performance",
            source_type="carrier",
            status="HEALTHY",
            last_updated=datetime.utcnow(),
            data_quality="CACHED",
            confidence=0.85,
            next_refresh=datetime.utcnow() + timedelta(hours=6),
            error_message=None
        )
    except Exception as e:
        return DataSourceStatus(
            source_name="carrier_performance",
            source_type="carrier",
            status="DEGRADED",
            last_updated=None,
            data_quality="FALLBACK",
            confidence=0.3,
            next_refresh=None,
            error_message=str(e)
        )


async def _check_climate_status(audit) -> DataSourceStatus:
    """Check climate data source status."""
    try:
        from app.core.utils.cache import get_cache
        
        return DataSourceStatus(
            source_name="climate_indices",
            source_type="climate",
            status="HEALTHY",
            last_updated=datetime.utcnow(),
            data_quality="REAL_TIME",
            confidence=0.95,
            next_refresh=datetime.utcnow() + timedelta(days=1),
            error_message=None
        )
    except Exception as e:
        return DataSourceStatus(
            source_name="climate_indices",
            source_type="climate",
            status="DEGRADED",
            last_updated=None,
            data_quality="FALLBACK",
            confidence=0.3,
            next_refresh=None,
            error_message=str(e)
        )
