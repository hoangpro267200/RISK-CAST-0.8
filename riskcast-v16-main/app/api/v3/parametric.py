"""
Parametric API Endpoints
API v3 endpoints for parametric insurance
RISKCAST V3 - Modular Monolith
"""
from fastapi import APIRouter, Depends, Request, status
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field
import logging

# Import dependencies
from app.shared.dependencies import TenantContext
from app.shared.utils import build_audit_context
from app.modules.rbac_policy.service import require_permission
from app.modules.rbac_policy.constants import Permissions
from app.modules.parametric.service import ParametricService
from app.modules.parametric.models import (
    TriggerDefinition,
    OracleEvent,
    TriggerEvent,
    TriggerDefinitionStatus,
    TriggerEventStatus
)

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession, get_tenant_scoped_db

logger = logging.getLogger(__name__)

# Parametric router
router = APIRouter(prefix="/parametric", tags=["parametric"])


# Schemas
class TriggerCreate(BaseModel):
    """Schema for creating trigger definition"""
    type: str = Field(..., description="Trigger type")
    params_json: Dict[str, Any] = Field(..., description="Trigger parameters")


class TriggerResponse(BaseModel):
    """Schema for trigger definition response"""
    id: str
    tenant_id: str
    status: str
    type: str
    version: int
    params_json: Dict[str, Any]
    created_by_user_id: Optional[str]
    published_at: Optional[str]
    immutable_hash: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class OracleEventCreate(BaseModel):
    """Schema for creating oracle event"""
    source: str = Field(..., description="Event source")
    captured_at: datetime = Field(..., description="Capture timestamp")
    payload_json: Dict[str, Any] = Field(..., description="Event payload")


class OracleEventResponse(BaseModel):
    """Schema for oracle event response"""
    id: str
    tenant_id: Optional[str]
    source: str
    captured_at: str
    payload_json: Dict[str, Any]
    payload_hash: str
    created_at: str
    
    class Config:
        from_attributes = True


@router.post(
    "/triggers",
    response_model=TriggerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create trigger",
    description="Create a new trigger definition"
)
async def create_trigger(
    data: TriggerCreate,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.PARAMETRIC_WRITE))
):
    """Create a new trigger definition"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = ParametricService(db)
        trigger = await service.create_trigger_definition(
            trigger_type=data.type,
            params=data.params_json,
            user_id=context.user_id,
            context=audit_context
        )
        
        return TriggerResponse(
            id=trigger.id,
            tenant_id=trigger.tenant_id,
            status=trigger.status.value,
            type=trigger.type,
            version=trigger.version,
            params_json=trigger.params_json,
            created_by_user_id=trigger.created_by_user_id,
            published_at=trigger.published_at.isoformat() + 'Z' if trigger.published_at else None,
            immutable_hash=trigger.immutable_hash,
            created_at=trigger.created_at.isoformat() + 'Z'
        )
    finally:
        db_session.close()


@router.post(
    "/oracle-events",
    response_model=OracleEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest oracle event",
    description="Ingest oracle event from external source"
)
async def ingest_oracle_event(
    data: OracleEventCreate,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.PARAMETRIC_WRITE))
):
    """Ingest oracle event"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = ParametricService(db)
        event = await service.ingest_oracle_event(
            source=data.source,
            captured_at=data.captured_at,
            payload=data.payload_json,
            context=audit_context
        )
        
        return OracleEventResponse(
            id=event.id,
            tenant_id=event.tenant_id,
            source=event.source,
            captured_at=event.captured_at.isoformat() + 'Z',
            payload_json=event.payload_json,
            payload_hash=event.payload_hash,
            created_at=event.created_at.isoformat() + 'Z'
        )
    finally:
        db_session.close()


@router.post(
    "/trigger-events/{id}/approve-payout",
    summary="Approve trigger payout",
    description="Approve payout for trigger event"
)
async def approve_trigger_payout(
    id: str,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.PAYOUT_APPROVE))
):
    """Approve payout for trigger event"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = ParametricService(db)
        trigger_event = await service.approve_payout(
            trigger_event_id=id,
            user_id=context.user_id,
            context=audit_context
        )
        
        return {
            "id": trigger_event.id,
            "status": trigger_event.status.value,
            "payout_id": trigger_event.payout_id
        }
    finally:
        db_session.close()
