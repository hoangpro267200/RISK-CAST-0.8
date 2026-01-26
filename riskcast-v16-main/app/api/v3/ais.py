"""
AIS Vessel Tracking API Endpoints
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.integrations.ais import AISService, MarineTrafficAISClient
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/ais", tags=["AIS Vessel Tracking"])


# Request/Response Models
class VesselPositionResponse(BaseModel):
    mmsi: str
    imo: Optional[str]
    vessel_name: str
    latitude: float
    longitude: float
    speed_knots: float
    course: float
    heading: float
    navigation_status: str
    destination: Optional[str]
    eta: Optional[datetime]
    timestamp: datetime
    data_source: str


class VesselInfoResponse(BaseModel):
    mmsi: str
    imo: Optional[str]
    vessel_name: str
    vessel_type: str
    length_meters: float
    width_meters: float
    gross_tonnage: Optional[int]
    deadweight_tonnage: Optional[int]
    flag_country: str
    year_built: Optional[int]
    owner: Optional[str]
    operator: Optional[str]


class VesselRiskResponse(BaseModel):
    mmsi: str
    imo: Optional[str]
    vessel_name: str
    risk_score: float
    risk_grade: str
    risk_factors: dict
    zone_alerts: List[dict]
    position: dict
    timestamp: str


class AreaSearchRequest(BaseModel):
    min_lat: float = Field(..., ge=-90, le=90)
    max_lat: float = Field(..., ge=-90, le=90)
    min_lon: float = Field(..., ge=-180, le=180)
    max_lon: float = Field(..., ge=-180, le=180)
    vessel_types: Optional[List[str]] = None


# Dependency
def get_ais_service() -> AISService:
    client = MarineTrafficAISClient()
    return AISService(marine_traffic_client=client)


# Endpoints
@router.get("/vessel/position", response_model=VesselPositionResponse)
async def get_vessel_position(
    mmsi: Optional[str] = Query(None, description="Vessel MMSI (9 digits)"),
    imo: Optional[str] = Query(None, description="Vessel IMO (7 digits)"),
    vessel_name: Optional[str] = Query(None, description="Vessel name"),
    current_user = Depends(get_current_user),
    ais_service: AISService = Depends(get_ais_service)
):
    """
    Get real-time vessel position.
    
    Provide at least one of: mmsi, imo, or vessel_name
    """
    if not any([mmsi, imo, vessel_name]):
        raise HTTPException(400, "Provide mmsi, imo, or vessel_name")
    
    position = await ais_service.get_vessel_position(
        mmsi=mmsi, imo=imo, vessel_name=vessel_name
    )
    
    if not position:
        raise HTTPException(404, "Vessel not found")
    
    return VesselPositionResponse(
        mmsi=position.mmsi,
        imo=position.imo,
        vessel_name=position.vessel_name,
        latitude=position.latitude,
        longitude=position.longitude,
        speed_knots=position.speed_knots,
        course=position.course,
        heading=position.heading,
        navigation_status=position.navigation_status.value,
        destination=position.destination,
        eta=position.eta,
        timestamp=position.timestamp,
        data_source=position.data_source
    )


@router.get("/vessel/info", response_model=VesselInfoResponse)
async def get_vessel_info(
    mmsi: Optional[str] = Query(None),
    imo: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    ais_service: AISService = Depends(get_ais_service)
):
    """Get static vessel information."""
    if not mmsi and not imo:
        raise HTTPException(400, "Provide mmsi or imo")
    
    info = await ais_service.get_vessel_info(mmsi=mmsi, imo=imo)
    
    if not info:
        raise HTTPException(404, "Vessel not found")
    
    return VesselInfoResponse(
        mmsi=info.mmsi,
        imo=info.imo,
        vessel_name=info.vessel_name,
        vessel_type=info.vessel_type.value,
        length_meters=info.length_meters,
        width_meters=info.width_meters,
        gross_tonnage=info.gross_tonnage,
        deadweight_tonnage=info.deadweight_tonnage,
        flag_country=info.flag_country,
        year_built=info.year_built,
        owner=info.owner,
        operator=info.operator
    )


@router.get("/vessel/risk", response_model=VesselRiskResponse)
async def assess_vessel_risk(
    mmsi: Optional[str] = Query(None),
    imo: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    ais_service: AISService = Depends(get_ais_service)
):
    """
    Comprehensive vessel risk assessment.
    
    Includes:
    - Current position
    - High-risk zone proximity
    - Vessel age and condition factors
    - Flag state risk
    - Sanctions check
    """
    if not mmsi and not imo:
        raise HTTPException(400, "Provide mmsi or imo")
    
    risk_assessment = await ais_service.assess_vessel_risk(mmsi=mmsi, imo=imo)
    
    if risk_assessment.get("error"):
        raise HTTPException(404, risk_assessment["error"])
    
    return VesselRiskResponse(**risk_assessment)


@router.post("/vessels/search")
async def search_vessels_in_area(
    request: AreaSearchRequest,
    current_user = Depends(get_current_user),
    ais_service: AISService = Depends(get_ais_service)
):
    """Search for vessels in a geographic area."""
    positions = await ais_service.search_vessels_in_area(
        min_lat=request.min_lat,
        min_lon=request.min_lon,
        max_lat=request.max_lat,
        max_lon=request.max_lon
    )
    
    return {
        "count": len(positions),
        "vessels": [
            {
                "mmsi": p.mmsi,
                "vessel_name": p.vessel_name,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "speed_knots": p.speed_knots,
                "heading": p.heading
            }
            for p in positions
        ]
    }


@router.get("/vessel/track")
async def get_vessel_track(
    mmsi: str,
    hours: int = Query(24, ge=1, le=168),
    current_user = Depends(get_current_user),
    ais_service: AISService = Depends(get_ais_service)
):
    """Get historical vessel track."""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    track = await ais_service.get_historical_track(
        mmsi=mmsi,
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "mmsi": mmsi,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "points_count": len(track),
        "track": [
            {
                "lat": p.latitude,
                "lon": p.longitude,
                "timestamp": p.timestamp.isoformat(),
                "speed": p.speed_knots,
                "course": p.course
            }
            for p in track
        ]
    }


@router.get("/zones/high-risk")
async def get_high_risk_zones(
    current_user = Depends(get_current_user)
):
    """Get list of predefined high-risk zones."""
    from app.integrations.ais.ais_service import AISService
    
    return {
        "zones": [
            {
                "id": zone_id,
                "name": info["name"],
                "risk_level": info["risk_level"],
                "polygon": info["polygon"]
            }
            for zone_id, info in AISService.HIGH_RISK_ZONES.items()
        ]
    }
