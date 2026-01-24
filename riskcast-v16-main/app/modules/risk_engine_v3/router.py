"""
Risk Engine V3 Router
FastAPI routes for risk calculation
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.shared.schemas import StandardResponse
from app.shared.dependencies import require_user, require_tenant
from app.modules.risk_engine_v3.service import RiskEngineV3Service

router = APIRouter(prefix="/risk-engine", tags=["Risk Engine V3"])


@router.post("/calculate", response_model=StandardResponse)
async def calculate_risk(
    input_data: Dict[str, Any],
    model_version: str = None,
    random_seed: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Calculate risk with deterministic engine"""
    service = RiskEngineV3Service(db)
    result = service.calculate_risk(input_data, model_version, random_seed)
    return StandardResponse(
        success=True,
        data=result,
        message="Risk calculation completed"
    )
