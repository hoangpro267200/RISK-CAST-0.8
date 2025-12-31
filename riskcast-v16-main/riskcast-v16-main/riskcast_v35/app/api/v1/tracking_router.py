from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.engines.tracking.core import TrackingEngine
from app.schemas.tracking import (
    TrackingEventCreateRequest,
    TrackingEventResponse,
    TrackingTimelineResponse,
)
from app.schemas.risk import RiskSnapshotResponse
from app.services.tracking_service import TrackingService
from app.services.risk_service import RiskService
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/tracking", tags=["tracking"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


def _engine(db: Session) -> TrackingEngine:
    return TrackingEngine(
        tracking_service=TrackingService(db),
        risk_service=RiskService(db),
        shipment_service=ShipmentService(db),
    )


@router.get("/ui", include_in_schema=False)
def tracking_ui(request: Request):
    return templates.TemplateResponse("tracking/tracking_center.html", {"request": request})


@router.get("/health")
async def tracking_health():
    return {"status": "ok"}


@router.post("/event", response_model=TrackingEventResponse)
async def ingest_event(request: TrackingEventCreateRequest, db: Session = Depends(get_db)):
    engine = _engine(db)
    return engine.ingest_event(request)


@router.get("/shipment/{shipment_id}", response_model=TrackingTimelineResponse)
async def get_shipment_timeline(shipment_id: UUID, db: Session = Depends(get_db)):
    engine = _engine(db)
    return engine.get_shipment_timeline(shipment_id)


@router.post("/{shipment_id}/recompute-risk", response_model=RiskSnapshotResponse)
async def recompute_risk(shipment_id: UUID, db: Session = Depends(get_db)):
    engine = _engine(db)
    return engine.recompute_risk_for_shipment(shipment_id)

