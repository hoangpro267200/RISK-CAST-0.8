"""
Market Data API Endpoints

Provides:
1. Market rates for cargo/route combinations
2. Market indices (Baltic, Container, Insurance)
3. Competitive analysis and benchmarking
4. Market trends and forecasts
"""

from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
import logging

from app.dependencies.auth import get_current_user
from app.integrations.market import (
    MarketDataService,
    LloydsListClient,
    CargoCategory,
    RouteCategory
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market", tags=["Market Data"])


# Singleton service
_market_service: Optional[MarketDataService] = None


def get_market_service() -> MarketDataService:
    """Get or create market data service."""
    global _market_service
    if _market_service is None:
        lloyds = LloydsListClient()
        _market_service = MarketDataService(lloyds_client=lloyds)
    return _market_service


# ============================================================================
# Response Models
# ============================================================================

class MarketRateResponse(BaseModel):
    """Market rate response."""
    rate_id: str
    cargo_category: str
    route_category: str
    min_rate: float
    max_rate: float
    avg_rate: float
    market_hardness: str
    trend: str
    source: str


class MarketIndexResponse(BaseModel):
    """Market index response."""
    index_name: str
    index_value: float
    change_1d: float
    change_7d: float
    change_30d: float
    as_of_date: str


class BenchmarkResponse(BaseModel):
    """Market benchmark response."""
    your_rate: float
    market_avg: float
    market_min: float
    market_max: float
    percentile: float
    competitiveness: str
    recommendation: str


class PremiumEstimateResponse(BaseModel):
    """Premium estimate response."""
    cargo_value_usd: float
    min_premium_usd: float
    max_premium_usd: float
    avg_premium_usd: float
    market_hardness: str
    trend: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/rates", response_model=List[MarketRateResponse])
async def get_market_rates(
    cargo_category: Optional[str] = Query(None, description="Cargo category filter"),
    route_category: Optional[str] = Query(None, description="Route category filter"),
    current_user = Depends(get_current_user),
    service: MarketDataService = Depends(get_market_service)
):
    """
    Get current market rates.
    
    - Filter by cargo_category and/or route_category
    - Returns all rates if no filter specified
    """
    try:
        if cargo_category and route_category:
            # Single rate
            rate = await service.get_market_rate(
                CargoCategory(cargo_category),
                RouteCategory(route_category)
            )
            return [MarketRateResponse(
                rate_id=rate.rate_id,
                cargo_category=rate.cargo_category.value,
                route_category=rate.route_category.value,
                min_rate=float(rate.min_rate),
                max_rate=float(rate.max_rate),
                avg_rate=float(rate.avg_rate),
                market_hardness=rate.market_hardness,
                trend=rate.trend,
                source=rate.source
            )]
        elif cargo_category:
            # Rates for cargo category
            rates = await service.get_rates_by_cargo(CargoCategory(cargo_category))
        elif route_category:
            # Rates for route category
            rates = await service.get_rates_by_route(RouteCategory(route_category))
        else:
            # All rates
            rates = await service.get_all_market_rates()
        
        return [
            MarketRateResponse(
                rate_id=r.rate_id,
                cargo_category=r.cargo_category.value,
                route_category=r.route_category.value,
                min_rate=float(r.min_rate),
                max_rate=float(r.max_rate),
                avg_rate=float(r.avg_rate),
                market_hardness=r.market_hardness,
                trend=r.trend,
                source=r.source
            )
            for r in rates
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {e}")


@router.get("/indices", response_model=List[MarketIndexResponse])
async def get_market_indices(
    current_user = Depends(get_current_user),
    service: MarketDataService = Depends(get_market_service)
):
    """
    Get current market indices.
    
    Returns:
    - Baltic Dry Index
    - Baltic Clean/Dirty Tanker Index
    - Container Freight Index
    - Marine Insurance Premium Index
    """
    indices = await service.get_market_indices()
    return [
        MarketIndexResponse(
            index_name=i.index_name,
            index_value=i.index_value,
            change_1d=i.change_1d,
            change_7d=i.change_7d,
            change_30d=i.change_30d,
            as_of_date=i.as_of_date.isoformat()
        )
        for i in indices
    ]


@router.get("/benchmark", response_model=BenchmarkResponse)
async def compare_to_market(
    your_rate: float = Query(..., description="Your rate per mille"),
    cargo_category: str = Query(..., description="Cargo category"),
    route_category: str = Query(..., description="Route category"),
    current_user = Depends(get_current_user),
    service: MarketDataService = Depends(get_market_service)
):
    """
    Compare your rate to market benchmarks.
    
    Returns percentile position and competitiveness assessment.
    """
    try:
        benchmark = await service.compare_to_market(
            Decimal(str(your_rate)),
            CargoCategory(cargo_category),
            RouteCategory(route_category)
        )
        
        return BenchmarkResponse(
            your_rate=float(benchmark.your_rate),
            market_avg=float(benchmark.market_avg),
            market_min=float(benchmark.market_min),
            market_max=float(benchmark.market_max),
            percentile=benchmark.percentile,
            competitiveness=benchmark.competitiveness,
            recommendation=benchmark.recommendation
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {e}")


@router.get("/trend/{cargo_category}")
async def get_market_trend(
    cargo_category: str,
    days: int = Query(30, ge=7, le=90, description="Number of days for trend analysis"),
    current_user = Depends(get_current_user),
    service: MarketDataService = Depends(get_market_service)
):
    """
    Get market trend for a cargo category.
    
    Returns historical rate data and trend direction.
    """
    try:
        return await service.get_market_trend(
            CargoCategory(cargo_category),
            days
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid cargo category: {e}")


@router.get("/competitive-analysis")
async def get_competitive_analysis(
    your_rate: float = Query(..., description="Your rate per mille"),
    cargo_category: str = Query(..., description="Cargo category"),
    route_category: str = Query(..., description="Route category"),
    current_user = Depends(get_current_user),
    service: MarketDataService = Depends(get_market_service)
):
    """
    Get comprehensive competitive analysis.
    
    Combines market rates, benchmarking, and trend data.
    """
    try:
        return await service.get_competitive_analysis(
            CargoCategory(cargo_category),
            RouteCategory(route_category),
            Decimal(str(your_rate))
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {e}")


@router.get("/premium-estimate", response_model=PremiumEstimateResponse)
async def estimate_premium(
    cargo_value_usd: float = Query(..., gt=0, description="Cargo value in USD"),
    cargo_category: str = Query(..., description="Cargo category"),
    route_category: str = Query(..., description="Route category"),
    current_user = Depends(get_current_user),
    service: MarketDataService = Depends(get_market_service)
):
    """
    Estimate premium based on market rates.
    
    Returns min/max/avg premium estimates for given cargo value.
    """
    try:
        result = await service.get_premium_estimate(
            Decimal(str(cargo_value_usd)),
            CargoCategory(cargo_category),
            RouteCategory(route_category)
        )
        
        return PremiumEstimateResponse(
            cargo_value_usd=result["cargo_value_usd"],
            min_premium_usd=result["premium_estimate"]["min_usd"],
            max_premium_usd=result["premium_estimate"]["max_usd"],
            avg_premium_usd=result["premium_estimate"]["avg_usd"],
            market_hardness=result["market_conditions"]["hardness"],
            trend=result["market_conditions"]["trend"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {e}")


@router.get("/categories")
async def get_categories():
    """
    Get available cargo and route categories.
    
    Use these values for filtering and queries.
    """
    return {
        "cargo_categories": [c.value for c in CargoCategory],
        "route_categories": [r.value for r in RouteCategory]
    }


@router.get("/health")
async def market_service_health():
    """Check market data service health."""
    try:
        service = get_market_service()
        lloyds_configured = service.lloyds.is_configured() if service.lloyds else False
        
        return {
            "status": "healthy",
            "lloyds_api_configured": lloyds_configured,
            "cache_entries": len(service._rate_cache),
            "available_cargo_categories": len(CargoCategory),
            "available_route_categories": len(RouteCategory)
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }
