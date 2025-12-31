from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.engines.documents.core import DocumentsEngine
from app.schemas.documents import DocumentResponse
from app.services.document_service import DocumentService
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/documents", tags=["documents"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


def _engine(db: Session) -> DocumentsEngine:
    document_service = DocumentService(db)
    shipment_service = ShipmentService(db)
    return DocumentsEngine(document_service=document_service, shipment_service=shipment_service)


@router.get("/ui", include_in_schema=False)
def documents_ui(request: Request):
    return templates.TemplateResponse("documents/documents_center.html", {"request": request})


@router.post("/{shipment_id}/si", response_model=DocumentResponse)
async def generate_shipping_instruction(shipment_id: UUID, db: Session = Depends(get_db)):
    """Generate a Shipping Instruction (SI) from shipment data."""
    try:
        return _engine(db).generate_si(shipment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{shipment_id}/bl-draft", response_model=DocumentResponse)
async def generate_draft_bl(shipment_id: UUID, db: Session = Depends(get_db)):
    """Generate a Draft Bill of Lading from an SI."""
    try:
        return _engine(db).generate_draft_bl(shipment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{shipment_id}/validate-bl")
async def validate_bl(shipment_id: UUID, db: Session = Depends(get_db)):
    """Compare SI vs Draft B/L for a shipment."""
    return _engine(db).validate_bl_against_si(shipment_id)


@router.get("/shipment/{shipment_id}/documents", response_model=list[DocumentResponse])
async def get_shipment_documents(shipment_id: UUID, db: Session = Depends(get_db)):
    """Retrieve all documents for a shipment."""
    docs = DocumentService(db).get_documents_by_shipment(shipment_id)
    return docs

