from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.engines.pricing.core import PricingEngine
from app.schemas.pricing import PricingQuoteRequest, PricingQuoteResponse
from app.services.risk_service import RiskService
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/quote", response_model=PricingQuoteResponse)
async def get_pricing_quote(request: PricingQuoteRequest, db: Session = Depends(get_db)):
    """Generate a pricing quote for a shipment."""
    risk_service = RiskService(db)
    shipment_service = ShipmentService(db) if db else None
    engine = PricingEngine(db, risk_service=risk_service, shipment_service=shipment_service)
    return engine.quote(request)


@router.get("/health")
async def pricing_health():
    return {"status": "ok"}

