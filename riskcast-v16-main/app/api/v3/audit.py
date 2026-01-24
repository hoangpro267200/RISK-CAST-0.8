"""
Audit Trail Viewer API

Endpoints for viewing and searching the audit trail:
- Search events with filters
- View event details
- Export for compliance
- Verify chain integrity
- Get audit statistics
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps import get_audit
from app.api.deps.rbac import PermissionChecker
from app.core.audit import (
    ImmutableAuditLedger,
    AuditEventImmutable,
    EventType,
    ChainVerificationResult,
)

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


# ============================================================================
# Schemas
# ============================================================================


class AuditEventSummary(BaseModel):
    """Summary of an audit event."""

    id: str
    sequence_number: int
    event_type: str
    action: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: Optional[str]
    event_timestamp: datetime
    event_hash: str


class AuditEventDetail(BaseModel):
    """Detailed audit event."""

    id: str
    sequence_number: int
    event_type: str
    action: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: Optional[str]
    tenant_id: Optional[str]
    payload: Optional[dict]
    event_timestamp: datetime
    server_timestamp: datetime
    prev_event_hash: str
    event_hash: str
    hmac_signature: str
    source_ip: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]


class AuditSearchResponse(BaseModel):
    """Response for audit search."""

    total_count: int
    page: int
    page_size: int
    events: List[AuditEventSummary]


class ChainVerificationResponse(BaseModel):
    """Response for chain verification."""

    is_valid: bool
    events_checked: int
    first_event_sequence: int
    last_event_sequence: int
    broken_at_sequence: Optional[int]
    error_message: Optional[str]
    verification_hash: str
    verified_at: datetime


class AuditExportRequest(BaseModel):
    """Request for audit export."""

    start_date: datetime
    end_date: datetime
    event_types: Optional[List[str]] = None
    include_verification: bool = True


class AuditStatistics(BaseModel):
    """Audit trail statistics."""

    total_events: int
    events_today: int
    events_this_week: int
    events_this_month: int
    by_event_type: dict
    by_actor_type: dict
    chain_status: str
    last_event_timestamp: Optional[datetime]


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/events", response_model=AuditSearchResponse)
async def search_audit_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    action: Optional[str] = Query(None, description="Filter by action"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    actor_type: Optional[str] = Query(None, description="Filter by actor type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("audit:read")),
):
    """
    Search audit events with filters.

    Supports pagination and multiple filter criteria.
    """
    query = db.query(AuditEventImmutable)

    if context.tenant_id:
        query = query.filter(AuditEventImmutable.tenant_id == context.tenant_id)

    if event_type:
        query = query.filter(AuditEventImmutable.event_type == event_type)
    if action:
        query = query.filter(AuditEventImmutable.action == action)
    if entity_type:
        query = query.filter(AuditEventImmutable.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEventImmutable.entity_id == entity_id)
    if actor_type:
        query = query.filter(AuditEventImmutable.actor_type == actor_type)
    if actor_id:
        query = query.filter(AuditEventImmutable.actor_id == actor_id)
    if start_date:
        query = query.filter(AuditEventImmutable.event_timestamp >= start_date)
    if end_date:
        query = query.filter(AuditEventImmutable.event_timestamp <= end_date)

    total_count = query.count()
    offset = (page - 1) * page_size
    events = (
        query.order_by(AuditEventImmutable.sequence_number.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return AuditSearchResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        events=[_to_summary(e) for e in events],
    )


@router.get("/events/{event_id}", response_model=AuditEventDetail)
async def get_audit_event(
    event_id: str,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("audit:read")),
):
    """
    Get detailed information about a specific audit event.
    """
    query = db.query(AuditEventImmutable).filter(AuditEventImmutable.id == event_id)
    if context.tenant_id:
        query = query.filter(AuditEventImmutable.tenant_id == context.tenant_id)
    event = query.first()

    if not event:
        raise HTTPException(status_code=404, detail=f"Audit event {event_id} not found")

    return AuditEventDetail(
        id=str(event.id),
        sequence_number=event.sequence_number,
        event_type=event.event_type,
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        actor_type=event.actor_type,
        actor_id=event.actor_id,
        tenant_id=event.tenant_id,
        payload=event.payload_json,
        event_timestamp=event.event_timestamp,
        server_timestamp=event.server_timestamp,
        prev_event_hash=event.prev_event_hash,
        event_hash=event.event_hash,
        hmac_signature=event.hmac_signature,
        source_ip=event.source_ip,
        user_agent=event.user_agent,
        request_id=event.request_id,
    )


@router.get("/events/by-entity/{entity_type}/{entity_id}")
async def get_events_for_entity(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("audit:read")),
):
    """
    Get all audit events for a specific entity.

    Useful for seeing complete history of an entity.
    """
    events = audit.get_events_for_entity(
        entity_type=entity_type,
        entity_id=entity_id,
        tenant_id=context.tenant_id,
    )

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "event_count": len(events),
        "events": [_to_summary(e) for e in events],
    }


@router.get("/events/by-actor/{actor_type}/{actor_id}")
async def get_events_by_actor(
    actor_type: str,
    actor_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("audit:read")),
):
    """
    Get all audit events by a specific actor.

    Useful for user activity reports.
    """
    events = audit.get_events_by_actor(
        actor_type=actor_type,
        actor_id=actor_id,
        start_time=start_date,
        end_time=end_date,
    )

    if context.tenant_id:
        events = [e for e in events if e.tenant_id == context.tenant_id]

    return {
        "actor_type": actor_type,
        "actor_id": actor_id,
        "event_count": len(events),
        "events": [_to_summary(e) for e in events[:limit]],
    }


@router.post("/verify-chain", response_model=ChainVerificationResponse)
async def verify_audit_chain(
    start_sequence: Optional[int] = Query(None, description="Start sequence number"),
    end_sequence: Optional[int] = Query(None, description="End sequence number"),
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("audit:read")),
):
    """
    Verify integrity of the audit hash chain.

    This proves the audit trail has not been tampered with.
    """
    result = audit.verify_chain(
        start_sequence=start_sequence,
        end_sequence=end_sequence,
    )

    return ChainVerificationResponse(
        is_valid=result.is_valid,
        events_checked=result.events_checked,
        first_event_sequence=result.first_event_sequence,
        last_event_sequence=result.last_event_sequence,
        broken_at_sequence=result.broken_at_sequence,
        error_message=result.error_message,
        verification_hash=result.verification_hash,
        verified_at=result.verified_at,
    )


@router.post("/export")
async def export_audit_trail(
    request: AuditExportRequest,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("audit:read")),
):
    """
    Export audit trail for compliance/regulatory review.

    Returns a JSON file with events and verification proof.
    """
    export = audit.export_for_compliance(
        start_date=request.start_date,
        end_date=request.end_date,
        tenant_id=context.tenant_id,
        event_types=request.event_types,
    )

    return export


@router.get("/statistics", response_model=AuditStatistics)
async def get_audit_statistics(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("audit:read")),
):
    """
    Get audit trail statistics.

    Overview of audit activity.
    """
    query = db.query(AuditEventImmutable)
    if context.tenant_id:
        query = query.filter(AuditEventImmutable.tenant_id == context.tenant_id)

    total = query.count()

    today = datetime.utcnow().date()
    events_today = (
        query.filter(func.date(AuditEventImmutable.event_timestamp) == today).count()
    )

    week_ago = datetime.utcnow() - timedelta(days=7)
    events_week = (
        query.filter(AuditEventImmutable.event_timestamp >= week_ago).count()
    )

    month_ago = datetime.utcnow() - timedelta(days=30)
    events_month = (
        query.filter(AuditEventImmutable.event_timestamp >= month_ago).count()
    )

    by_type = (
        query.with_entities(
            AuditEventImmutable.event_type, func.count(AuditEventImmutable.id)
        )
        .group_by(AuditEventImmutable.event_type)
        .all()
    )

    by_actor = (
        query.with_entities(
            AuditEventImmutable.actor_type, func.count(AuditEventImmutable.id)
        )
        .group_by(AuditEventImmutable.actor_type)
        .all()
    )

    last_event = (
        query.order_by(AuditEventImmutable.sequence_number.desc()).first()
    )

    chain_status = "HEALTHY"
    if last_event:
        recent_events = (
            query.order_by(AuditEventImmutable.sequence_number.desc())
            .limit(10)
            .all()
        )

        prev_hash = None
        for event in reversed(recent_events):
            if prev_hash and event.prev_event_hash != prev_hash:
                chain_status = "BROKEN"
                break
            prev_hash = event.event_hash

    return AuditStatistics(
        total_events=total,
        events_today=events_today,
        events_this_week=events_week,
        events_this_month=events_month,
        by_event_type={t: c for t, c in by_type},
        by_actor_type={a: c for a, c in by_actor},
        chain_status=chain_status,
        last_event_timestamp=last_event.event_timestamp if last_event else None,
    )


@router.get("/event-types")
async def get_event_types(
    _: None = Depends(PermissionChecker("audit:read")),
):
    """
    Get list of all event types for filtering.
    """
    return {
        "event_types": [e.value for e in EventType],
        "descriptions": {
            "RISK_ASSESSMENT": "Risk assessment calculations",
            "UNDERWRITING": "Underwriting decisions",
            "QUOTE": "Quote generation and updates",
            "POLICY": "Policy lifecycle events",
            "CLAIM": "Claim filing and updates",
            "CLAIM_ADJUDICATION": "Claim adjudication decisions",
            "PAYOUT": "Payout processing",
            "DATA_FETCH": "External data fetches",
            "DATA_IMPORT": "Data imports",
            "DATA_COLLECTION": "Data collection activities",
            "DATA_REFRESH": "Data refresh operations",
            "DATA_VALIDATION": "Data validation checks",
            "MODEL_CALIBRATION": "Model calibration runs",
            "MODEL_VERSION": "Model version management",
            "MODEL_PUBLISH": "Model publishing",
            "EVIDENCE": "Evidence collection and management",
            "EVIDENCE_SEAL": "Evidence sealing",
            "COMPLIANCE": "Compliance-related events",
            "GDPR": "GDPR requests",
            "AUTHENTICATION": "Login/logout events",
            "AUTHORIZATION": "Permission changes",
            "SYSTEM": "System events",
            "ALERT": "System alerts",
        },
    }


# ============================================================================
# Helper Functions
# ============================================================================


def _to_summary(event: AuditEventImmutable) -> AuditEventSummary:
    """Convert AuditEventImmutable to summary."""
    return AuditEventSummary(
        id=str(event.id),
        sequence_number=event.sequence_number,
        event_type=event.event_type,
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        actor_type=event.actor_type,
        actor_id=event.actor_id,
        event_timestamp=event.event_timestamp,
        event_hash=event.event_hash,
    )
