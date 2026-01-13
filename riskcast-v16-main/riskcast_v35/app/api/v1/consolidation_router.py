from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.engines.consolidation.core import ConsolidationEngine
from app.schemas.consolidation import ConsolidationPlanRequest, ConsolidationPlanResponse
from app.services.consolidation_service import ConsolidationPlanService
from app.services.rate_service import RateService
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/consolidation", tags=["consolidation"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


def _engine(db: Session) -> ConsolidationEngine:
    shipment_service = ShipmentService(db)
    rate_service = RateService(db)
    return ConsolidationEngine(db, shipment_service=shipment_service, rate_service=rate_service)


@router.get("/ui", include_in_schema=False)
def consolidation_ui(request: Request):
    return templates.TemplateResponse("consolidation/consolidation_center.html", {"request": request})


@router.post("/plan", response_model=ConsolidationPlanResponse)
async def create_consolidation_plan(request: ConsolidationPlanRequest, db: Session = Depends(get_db)):
    """Create a consolidation plan for multiple LCL shipments."""
    try:
        return _engine(db).build_plan(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/plan/{plan_id}", response_model=ConsolidationPlanResponse)
async def get_consolidation_plan(plan_id: UUID, db: Session = Depends(get_db)):
    """Retrieve details of an existing consolidation plan."""
    svc = ConsolidationPlanService(db)
    plan = svc.get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return ConsolidationPlanResponse(
        planId=plan.id,
        pol=plan.pol,
        pod=plan.pod,
        containers=plan.containers or [],
        baselineLclCost=float(plan.baseline_lcl_cost or 0),
        optimizedFclCost=float(plan.optimized_fcl_cost or 0),
        savingAmount=float(plan.saving_amount or 0),
        savingPercent=float(plan.saving_percent or 0),
        createdAt=plan.created_at,
    )

