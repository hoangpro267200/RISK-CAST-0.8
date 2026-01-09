from fastapi import APIRouter
from app.api.shipment_api import router as shipment_router
from app.api.analysis_api import router as analysis_router
from app.api.transport_api import router as transport_router
from app.api.cargo_api import router as cargo_router
from app.api.insights_api import router as insights_router
from app.api.kpi_api import router as kpi_router
from app.api.v1.state_routes import router as state_router
from app.api.v1.ai_advisor_routes import router as ai_advisor_router

router = APIRouter()
router.include_router(shipment_router, prefix="/api/v1")
router.include_router(analysis_router, prefix="/api/v1")
router.include_router(transport_router, prefix="/api/v1")
router.include_router(cargo_router, prefix="/api/v1")
router.include_router(insights_router, prefix="/api/v1")
router.include_router(kpi_router, prefix="/api/v1")
router.include_router(state_router, prefix="/api/v1")
router.include_router(ai_advisor_router, prefix="/api/v1", tags=["AI Advisor"])




