from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    ShipmentSummaryResponse,
)
from app.schemas.risk import RiskSnapshotResponse
from app.services.shipment_service import ShipmentService
from app.services.risk_service import RiskService
from app.services.document_service import DocumentService
from app.services.tracking_service import TrackingService
from app.services.customs_service import CustomsService
from app.services.consolidation_service import ConsolidationPlanService

router = APIRouter(prefix="/shipments", tags=["Shipments"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


@router.post("/", response_model=ShipmentResponse, status_code=201)
async def create_shipment(shipment: ShipmentCreate, db: Session = Depends(get_db)):
    """Create a new shipment record."""
    return None


@router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a single shipment by ID."""
    return None


@router.patch("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(shipment_id: UUID, update: ShipmentUpdate, db: Session = Depends(get_db)):
    """Update shipment fields (status, price_info, etc.)."""
    return None


@router.get("/", response_model=List[ShipmentResponse])
async def list_shipments(status: Optional[str] = Query(None), pol_code: Optional[str] = Query(None), pod_code: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """List shipments with optional filters."""
    return []


@router.get("/{shipment_id}/risk", response_model=RiskSnapshotResponse)
async def get_shipment_risk(shipment_id: UUID, db: Session = Depends(get_db)):
    """Get the latest risk snapshot for a shipment."""
    return None


@router.get("/{shipment_id}/summary", response_model=ShipmentSummaryResponse)
async def get_shipment_summary(shipment_id: UUID, db: Session = Depends(get_db)):
    shipment_service = ShipmentService(db)
    shipment = shipment_service.get_shipment_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    document_service = DocumentService(db)
    tracking_service = TrackingService(db)
    risk_service = RiskService(db)
    customs_service = CustomsService(db)
    consolidation_service = ConsolidationPlanService(db)

    docs = document_service.get_documents_by_shipment(shipment_id)
    tracking_events = tracking_service.get_tracking_for_shipment(shipment_id)
    latest_risk = risk_service.get_latest_snapshot(shipment_id)
    customs_profile = customs_service.get_customs_profile(shipment_id)

    latest_event = tracking_events[0] if tracking_events else None

    # Pricing info
    price_info = shipment.price_info or {}
    best_option = price_info.get("best_option") or price_info.get("bestRate") or None
    pricing_available = bool(best_option)

    # Consolidation
    consolidation_available = bool(shipment.consolidation_info)
    plan_id = None
    containers_count = None
    saving_percent = None
    if shipment.consolidation_info:
        plan_id = shipment.consolidation_info.get("plan_id")
        containers_count = shipment.consolidation_info.get("containers_count")
        saving_percent = shipment.consolidation_info.get("saving_percent")
    else:
        plan = consolidation_service.get_latest_plan_for_shipment(shipment_id)
        if plan:
            consolidation_available = True
            plan_id = plan.id
            containers_count = len(plan.containers or [])
            saving_percent = float(plan.saving_percent or 0)

    # Documents existence
    def has_doc(doc_type: str) -> bool:
        return any(d.doc_type == doc_type for d in docs)

    documents_info = {
        "si_exists": has_doc("SI"),
        "bl_draft_exists": has_doc("BL_DRAFT"),
        "bl_final_exists": has_doc("BL_FINAL"),
    }

    tracking_info = {
        "has_tracking": bool(tracking_events),
        "latest_position": latest_event,
        "latest_risk": latest_risk,
    }

    customs_info = {
        "has_customs_profile": bool(customs_profile),
        "hs_code": customs_profile.hs_code if customs_profile else None,
    }

    summary = ShipmentSummaryResponse(
        shipment={
            "id": shipment.id,
            "refCode": shipment.ref_code,
            "shipperName": shipment.shipper_name,
            "consigneeName": shipment.consignee_name,
            "pol": shipment.pol,
            "pod": shipment.pod,
            "etd": shipment.etd,
            "eta": shipment.eta,
            "status": shipment.status,
        },
        pricing={
            "available": pricing_available,
            "bestOption": best_option,
        },
        consolidation={
            "available": consolidation_available,
            "planId": plan_id,
            "containersCount": containers_count,
            "savingPercent": saving_percent,
        },
        documents=documents_info,
        tracking=tracking_info,
        customs=customs_info,
    )
    return summary


@router.get("/{shipment_id}/ui", include_in_schema=False)
async def shipment_detail_ui(shipment_id: UUID, request: Request):
    return templates.TemplateResponse(
        "shipments/shipment_detail.html",
        {"request": request, "shipment_id": str(shipment_id)},
    )

