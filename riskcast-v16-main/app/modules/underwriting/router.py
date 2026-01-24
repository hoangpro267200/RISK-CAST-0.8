"""
Underwriting Router
FastAPI routes for underwriting
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse
from app.shared.dependencies import require_user, require_tenant
from app.modules.underwriting.service import UnderwritingService
from app.modules.underwriting.schemas import UnderwritingDecisionCreate, UnderwritingDecisionResponse

router = APIRouter(prefix="/underwriting", tags=["Underwriting"])


@router.post("/decisions", response_model=StandardResponse)
async def create_decision(
    decision_data: UnderwritingDecisionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Create underwriting decision"""
    service = UnderwritingService(db)
    decision = service.create_decision(decision_data, tenant_id)
    return StandardResponse(
        success=True,
        data=decision.dict(),
        message="Underwriting decision created"
    )


@router.post("/decisions/{decision_id}/approve", response_model=StandardResponse)
async def approve_decision(
    decision_id: str,
    decision: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Approve underwriting decision"""
    service = UnderwritingService(db)
    decision_obj = service.approve(decision_id, current_user.id, decision)
    return StandardResponse(
        success=True,
        data=decision_obj.dict(),
        message="Decision approved"
    )


@router.post("/decisions/{decision_id}/reject", response_model=StandardResponse)
async def reject_decision(
    decision_id: str,
    reason: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Reject underwriting decision"""
    service = UnderwritingService(db)
    decision_obj = service.reject(decision_id, current_user.id, reason)
    return StandardResponse(
        success=True,
        data=decision_obj.dict(),
        message="Decision rejected"
    )
