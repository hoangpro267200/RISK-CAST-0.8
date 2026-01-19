# app/api/__init__.py
from fastapi import APIRouter, Request
from .v1.analyze import router as analyze_router
from .v1.risk_routes import router as risk_router
from datetime import datetime

# Create main API router
router = APIRouter()

# Include v1 router
router.include_router(analyze_router, prefix="/v1", tags=["v1"])
router.include_router(risk_router, prefix="/v1", tags=["risk"])

# Climate Data Endpoint
@router.post("/climate_data")
async def get_climate_data(request: Request):
    """
    Fetch climate data for transit window.
    Returns seasonal defaults if NOAA/NASA APIs unavailable.
    """
    try:
        from app.core.services.climate_service import get_climate_data
        
        data = await request.json()
        route = data.get('route', '')
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        pol = data.get('pol', '')
        pod = data.get('pod', '')
        
        climate_data = get_climate_data(route, start_date, end_date, pol, pod)
        return climate_data
        
    except Exception as e:
        # Return safe defaults on error
        return {
            'enso': 0.0,
            'typhoon_freq': 0.5,
            'sst_anomaly': 0.0,
            'port_stress': 5.0,
            'volatility': 50
        }

