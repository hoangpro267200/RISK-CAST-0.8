"""
Sanctions Screening API Endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.integrations.sanctions import SanctionsService, OFACClient, ComplyAdvantageClient
from app.integrations.sanctions.models import EntityType, RiskLevel
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/sanctions", tags=["Sanctions Screening"])


# Singleton
_sanctions_service: Optional[SanctionsService] = None


def get_sanctions_service() -> SanctionsService:
    global _sanctions_service
    if _sanctions_service is None:
        ofac = OFACClient()
        comply = ComplyAdvantageClient()
        _sanctions_service = SanctionsService(
            ofac_client=ofac,
            comply_advantage_client=comply
        )
    return _sanctions_service


# Response Models
class SanctionsMatchResponse(BaseModel):
    match_id: str
    list_name: str
    matched_name_original: str
    match_strength: str
    match_score: float
    program: Optional[str]


class ScreeningResultResponse(BaseModel):
    screening_id: str
    query: str
    entity_type: str
    total_matches: int
    high_risk_matches: int
    risk_level: str
    risk_score: float
    risk_factors: List[str]
    recommendation: str
    matches: List[SanctionsMatchResponse]
    cached: bool


class VesselScreeningResponse(BaseModel):
    screening_id: str
    vessel_name: str
    vessel_sanctioned: bool
    owner_sanctioned: bool
    operator_sanctioned: bool
    flag_country_risk: str
    overall_risk: str
    risk_factors: List[str]
    recommendation: str


# Endpoints
@router.post("/screen/entity", response_model=ScreeningResultResponse)
async def screen_entity(
    name: str,
    entity_type: str = Query("COMPANY", description="INDIVIDUAL, COMPANY, or VESSEL"),
    country: Optional[str] = Query(None, description="Country code"),
    current_user = Depends(get_current_user),
    service: SanctionsService = Depends(get_sanctions_service)
):
    """
    Screen an entity against sanctions lists.
    
    Checks: OFAC, EU, UN, UK sanctions lists
    """
    try:
        entity_enum = EntityType(entity_type.upper())
    except ValueError:
        raise HTTPException(400, f"Invalid entity type: {entity_type}")
    
    result = await service.screen_entity(
        name=name,
        entity_type=entity_enum,
        country=country
    )
    
    return ScreeningResultResponse(
        screening_id=result.screening_id,
        query=result.query,
        entity_type=result.entity_type.value,
        total_matches=result.total_matches,
        high_risk_matches=result.high_risk_matches,
        risk_level=result.risk_level.value,
        risk_score=result.risk_score,
        risk_factors=result.risk_factors,
        recommendation=result.recommendation,
        matches=[
            SanctionsMatchResponse(
                match_id=m.match_id,
                list_name=m.list_name.value,
                matched_name_original=m.matched_name_original,
                match_strength=m.match_strength.value,
                match_score=m.match_score,
                program=m.program
            )
            for m in result.matches
        ],
        cached=result.cached
    )


@router.post("/screen/vessel", response_model=VesselScreeningResponse)
async def screen_vessel(
    vessel_name: str,
    imo: Optional[str] = Query(None, description="Vessel IMO number"),
    mmsi: Optional[str] = Query(None, description="Vessel MMSI"),
    flag_country: Optional[str] = Query(None, description="Flag country code"),
    owner_name: Optional[str] = Query(None, description="Owner company name"),
    operator_name: Optional[str] = Query(None, description="Operator company name"),
    current_user = Depends(get_current_user),
    service: SanctionsService = Depends(get_sanctions_service)
):
    """
    Comprehensive vessel sanctions screening.
    
    Checks vessel, owner, operator, and flag country.
    """
    result = await service.screen_vessel(
        vessel_name=vessel_name,
        imo=imo,
        mmsi=mmsi,
        flag_country=flag_country,
        owner_name=owner_name,
        operator_name=operator_name
    )
    
    return VesselScreeningResponse(
        screening_id=result.screening_id,
        vessel_name=result.vessel_name,
        vessel_sanctioned=result.vessel_sanctioned,
        owner_sanctioned=result.owner_sanctioned,
        operator_sanctioned=result.operator_sanctioned,
        flag_country_risk=result.flag_country_risk.value,
        overall_risk=result.overall_risk.value,
        risk_factors=result.risk_factors,
        recommendation=result.recommendation
    )


@router.get("/country/{country_code}")
async def check_country_sanctions(
    country_code: str,
    current_user = Depends(get_current_user),
    service: SanctionsService = Depends(get_sanctions_service)
):
    """Check if a country is under sanctions."""
    return await service.check_country(country_code)


@router.get("/lists")
async def get_sanctions_lists():
    """Get list of sanctions lists we check against."""
    from app.integrations.sanctions.models import SanctionsList
    return {
        "lists": [
            {"code": l.value, "name": l.name.replace("_", " ")}
            for l in SanctionsList
        ]
    }


@router.get("/sanctioned-countries")
async def get_sanctioned_countries(
    service: SanctionsService = Depends(get_sanctions_service)
):
    """Get list of sanctioned countries."""
    return {
        "countries": [
            {"code": code, "name": name}
            for code, name in service.SANCTIONED_COUNTRIES.items()
        ]
    }
