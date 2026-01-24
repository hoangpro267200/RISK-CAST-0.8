"""
Audit Ledger Router
FastAPI routes for audit trail
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse, PaginationParams
from app.shared.dependencies import require_user, require_tenant
from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.schemas import AuditLedgerResponse, AuditEventType

router = APIRouter(prefix="/audit", tags=["Audit Ledger"])


@router.get("", response_model=StandardResponse)
async def list_audit_events(
    event_type: AuditEventType = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """List audit events"""
    service = AuditLedgerService(db)
    events = service.list_events(tenant_id, event_type, pagination.offset, pagination.limit)
    return StandardResponse(
        success=True,
        data={"events": [e.dict() for e in events]},
        message="Audit events retrieved"
    )
