from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.schemas.customs import (
    HSSuggestionRequest,
    HSSuggestionResponse,
    CustomsDeclarationResponse,
    CustomsProfileResponse,
)
from app.engines.customs.core import CustomsEngine
from app.services.customs_service import CustomsService
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/customs", tags=["customs"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


def _engine(db: Session) -> CustomsEngine:
    return CustomsEngine(CustomsService(db), ShipmentService(db))


@router.get("/ui", include_in_schema=False)
def customs_ui(request: Request):
    return templates.TemplateResponse("customs/customs_center.html", {"request": request})


@router.post("/hs-suggest", response_model=HSSuggestionResponse)
async def suggest_hs_codes(request: HSSuggestionRequest, db: Session = Depends(get_db)):
    """Suggest HS codes from item descriptions using rules."""
    return _engine(db).suggest_hs_code(request)


@router.post("/{shipment_id}/declaration-xml", response_model=CustomsDeclarationResponse)
async def generate_customs_declaration(shipment_id: UUID, db: Session = Depends(get_db)):
    """Generate customs declaration XML (VNACCS format)."""
    try:
        return _engine(db).generate_declaration_xml(shipment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{shipment_id}", response_model=CustomsProfileResponse)
async def get_customs_profile(shipment_id: UUID, db: Session = Depends(get_db)):
    """Retrieve customs profile for a shipment."""
    svc = CustomsService(db)
    profile = svc.get_customs_profile(shipment_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

