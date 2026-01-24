"""
Risk Runs Router
FastAPI routes for risk calculation runs
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse
from app.shared.dependencies import require_user, require_tenant
from app.modules.risk_runs.service import RiskRunService
from app.modules.risk_runs.schemas import RiskRunResponse

router = APIRouter(prefix="/risk-runs", tags=["Risk Runs"])


@router.get("/{run_id}", response_model=StandardResponse)
async def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Get risk run by ID"""
    service = RiskRunService(db)
    run = service.get_run(run_id, tenant_id)
    return StandardResponse(
        success=True,
        data=run.dict(),
        message="Risk run retrieved"
    )
