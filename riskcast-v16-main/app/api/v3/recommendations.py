"""
Recommendations API Endpoints

Provides:
1. Coverage recommendations
2. Route recommendations
3. Pricing recommendations
4. Risk mitigation recommendations
5. Carrier recommendations
"""

from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum
import logging

from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# ============================================================================
# Enums and Models
# ============================================================================

class CoverageType(str, Enum):
    """Coverage types."""
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    COMPREHENSIVE = "COMPREHENSIVE"
    ALL_RISKS = "ALL_RISKS"


class RiskLevel(str, Enum):
    """Risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Request Models
class CoverageRequest(BaseModel):
    """Coverage recommendation request."""
    cargo_type: str
    cargo_value_usd: float = Field(..., gt=0)
    origin_port: str
    destination_port: str
    transport_mode: str = "OCEAN"
    perishable: bool = False
    hazardous: bool = False
    high_value: bool = False


class RouteRequest(BaseModel):
    """Route recommendation request."""
    origin_port: str
    destination_port: str
    cargo_type: str
    cargo_value_usd: float = Field(..., gt=0)
    priority: str = Field("BALANCED", pattern="^(SPEED|COST|SAFETY|BALANCED)$")
    max_transit_days: Optional[int] = None


class PricingRequest(BaseModel):
    """Pricing recommendation request."""
    cargo_type: str
    cargo_value_usd: float = Field(..., gt=0)
    route: str
    coverage_type: CoverageType
    risk_score: Optional[float] = None


class MitigationRequest(BaseModel):
    """Risk mitigation recommendation request."""
    risk_factors: List[str]
    cargo_type: str
    route: str
    current_risk_score: float = Field(..., ge=0, le=1)


# Response Models
class CoverageRecommendation(BaseModel):
    """Coverage recommendation."""
    coverage_type: str
    name: str
    description: str
    premium_estimate_usd: float
    deductible_usd: float
    coverage_limit_usd: float
    confidence: float
    rationale: str
    included_perils: List[str]
    excluded_perils: List[str]


class RouteRecommendation(BaseModel):
    """Route recommendation."""
    route_id: str
    name: str
    transit_days: int
    risk_score: float
    estimated_cost_usd: float
    waypoints: List[str]
    pros: List[str]
    cons: List[str]
    recommended: bool


class PricingRecommendation(BaseModel):
    """Pricing recommendation."""
    recommended_rate: float  # per mille
    min_rate: float
    max_rate: float
    premium_usd: float
    market_position: str
    factors: List[Dict[str, str]]
    competitiveness: str


class MitigationRecommendation(BaseModel):
    """Risk mitigation recommendation."""
    risk_factor: str
    current_impact: str
    recommendation: str
    expected_risk_reduction: float
    implementation_cost: str
    priority: str


class CarrierRecommendation(BaseModel):
    """Carrier recommendation."""
    carrier_name: str
    carrier_id: str
    reliability_score: float
    on_time_rate: float
    price_index: float
    coverage_areas: List[str]
    pros: List[str]
    cons: List[str]
    recommended: bool


# ============================================================================
# Coverage Recommendations
# ============================================================================

@router.post("/coverage", response_model=List[CoverageRecommendation])
async def get_coverage_recommendations(
    request: CoverageRequest,
    current_user = Depends(get_current_user)
):
    """
    Get coverage recommendations based on shipment details.
    
    Returns ranked coverage options with rationale.
    """
    cargo_value = request.cargo_value_usd
    
    # Base rates per mille
    base_rates = {
        CoverageType.BASIC: 0.15,
        CoverageType.STANDARD: 0.25,
        CoverageType.COMPREHENSIVE: 0.40,
        CoverageType.ALL_RISKS: 0.55
    }
    
    # Adjust for risk factors
    risk_multiplier = 1.0
    if request.perishable:
        risk_multiplier *= 1.3
    if request.hazardous:
        risk_multiplier *= 1.5
    if request.high_value:
        risk_multiplier *= 1.2
    
    recommendations = []
    
    # Basic coverage
    if not request.hazardous and not request.perishable:
        basic_rate = base_rates[CoverageType.BASIC] * risk_multiplier
        recommendations.append(CoverageRecommendation(
            coverage_type=CoverageType.BASIC.value,
            name="Basic Coverage",
            description="Essential protection for standard cargo shipments",
            premium_estimate_usd=round(cargo_value * basic_rate / 1000, 2),
            deductible_usd=round(cargo_value * 0.02, 2),
            coverage_limit_usd=cargo_value,
            confidence=0.7 if risk_multiplier == 1.0 else 0.5,
            rationale="Suitable for low-risk, general cargo" if risk_multiplier == 1.0 else "Consider higher coverage due to risk factors",
            included_perils=["Fire", "Sinking", "Collision"],
            excluded_perils=["Theft", "Damage", "Delay", "War"]
        ))
    
    # Standard coverage
    standard_rate = base_rates[CoverageType.STANDARD] * risk_multiplier
    recommendations.append(CoverageRecommendation(
        coverage_type=CoverageType.STANDARD.value,
        name="Standard Coverage",
        description="Balanced protection for most shipments",
        premium_estimate_usd=round(cargo_value * standard_rate / 1000, 2),
        deductible_usd=round(cargo_value * 0.015, 2),
        coverage_limit_usd=cargo_value * 1.1,
        confidence=0.85,
        rationale="Recommended for standard commercial shipments",
        included_perils=["Fire", "Sinking", "Collision", "Theft", "Piracy", "Jettison"],
        excluded_perils=["Delay", "War", "Strikes"]
    ))
    
    # Comprehensive coverage
    comp_rate = base_rates[CoverageType.COMPREHENSIVE] * risk_multiplier
    recommendations.append(CoverageRecommendation(
        coverage_type=CoverageType.COMPREHENSIVE.value,
        name="Comprehensive Coverage",
        description="Extensive protection including damage and partial loss",
        premium_estimate_usd=round(cargo_value * comp_rate / 1000, 2),
        deductible_usd=round(cargo_value * 0.01, 2),
        coverage_limit_usd=cargo_value * 1.2,
        confidence=0.9 if request.high_value or request.perishable else 0.8,
        rationale="Recommended for high-value or sensitive cargo" if request.high_value else "Good balance of coverage and cost",
        included_perils=["Fire", "Sinking", "Collision", "Theft", "Piracy", "Damage", "Contamination", "Temperature variation"],
        excluded_perils=["War", "Nuclear"]
    ))
    
    # All Risks coverage
    all_risk_rate = base_rates[CoverageType.ALL_RISKS] * risk_multiplier
    recommendations.append(CoverageRecommendation(
        coverage_type=CoverageType.ALL_RISKS.value,
        name="All Risks Coverage",
        description="Maximum protection against all perils except specifically excluded",
        premium_estimate_usd=round(cargo_value * all_risk_rate / 1000, 2),
        deductible_usd=round(cargo_value * 0.005, 2),
        coverage_limit_usd=cargo_value * 1.25,
        confidence=0.95,
        rationale="Highest level of protection - recommended for critical shipments",
        included_perils=["All physical loss or damage from any external cause"],
        excluded_perils=["Inherent vice", "Willful misconduct", "Delay (unless added)"]
    ))
    
    # Sort by confidence (most recommended first)
    recommendations.sort(key=lambda x: x.confidence, reverse=True)
    
    return recommendations


# ============================================================================
# Route Recommendations
# ============================================================================

@router.post("/routes", response_model=List[RouteRecommendation])
async def get_route_recommendations(
    request: RouteRequest,
    current_user = Depends(get_current_user)
):
    """
    Get route recommendations with risk and cost analysis.
    """
    # Mock route data - in production, this would query routing services
    routes = []
    
    # Direct route
    routes.append(RouteRecommendation(
        route_id="RT001",
        name=f"Direct: {request.origin_port} → {request.destination_port}",
        transit_days=21,
        risk_score=0.35,
        estimated_cost_usd=round(request.cargo_value_usd * 0.02, 2),
        waypoints=[request.origin_port, request.destination_port],
        pros=["Fastest transit time", "Fewer handling points", "Lower damage risk"],
        cons=["Higher shipping cost", "Less schedule flexibility"],
        recommended=request.priority in ["SPEED", "BALANCED"]
    ))
    
    # Via transshipment hub
    hub = "SGSIN" if "CN" in request.origin_port else "NLRTM"
    routes.append(RouteRecommendation(
        route_id="RT002",
        name=f"Via Hub: {request.origin_port} → {hub} → {request.destination_port}",
        transit_days=28,
        risk_score=0.42,
        estimated_cost_usd=round(request.cargo_value_usd * 0.015, 2),
        waypoints=[request.origin_port, hub, request.destination_port],
        pros=["Lower shipping cost", "More schedule options", "Established routes"],
        cons=["Additional handling", "Longer transit", "Transshipment risk"],
        recommended=request.priority == "COST"
    ))
    
    # Alternative route (avoiding high-risk areas)
    routes.append(RouteRecommendation(
        route_id="RT003",
        name=f"Safe Route: {request.origin_port} → {request.destination_port} (Avoiding high-risk zones)",
        transit_days=32,
        risk_score=0.22,
        estimated_cost_usd=round(request.cargo_value_usd * 0.025, 2),
        waypoints=[request.origin_port, "ZACPT", request.destination_port],  # Via Cape
        pros=["Lowest risk score", "Avoids piracy zones", "Stable weather patterns"],
        cons=["Longest transit", "Higher fuel cost"],
        recommended=request.priority == "SAFETY"
    ))
    
    # Filter by max transit days if specified
    if request.max_transit_days:
        routes = [r for r in routes if r.transit_days <= request.max_transit_days]
    
    # Sort by priority
    if request.priority == "SPEED":
        routes.sort(key=lambda x: x.transit_days)
    elif request.priority == "COST":
        routes.sort(key=lambda x: x.estimated_cost_usd)
    elif request.priority == "SAFETY":
        routes.sort(key=lambda x: x.risk_score)
    
    return routes


# ============================================================================
# Pricing Recommendations
# ============================================================================

@router.post("/pricing", response_model=PricingRecommendation)
async def get_pricing_recommendation(
    request: PricingRequest,
    current_user = Depends(get_current_user)
):
    """
    Get pricing recommendations based on market data.
    """
    # Base rate by coverage type
    base_rates = {
        CoverageType.BASIC: Decimal("0.15"),
        CoverageType.STANDARD: Decimal("0.25"),
        CoverageType.COMPREHENSIVE: Decimal("0.40"),
        CoverageType.ALL_RISKS: Decimal("0.55")
    }
    
    base_rate = base_rates.get(request.coverage_type, Decimal("0.25"))
    
    # Adjust for risk score
    risk_adjustment = Decimal("1.0")
    if request.risk_score:
        if request.risk_score > 0.7:
            risk_adjustment = Decimal("1.4")
        elif request.risk_score > 0.5:
            risk_adjustment = Decimal("1.2")
        elif request.risk_score > 0.3:
            risk_adjustment = Decimal("1.1")
    
    recommended_rate = float(base_rate * risk_adjustment)
    min_rate = float(base_rate * Decimal("0.85"))
    max_rate = float(base_rate * Decimal("1.25") * risk_adjustment)
    
    premium = request.cargo_value_usd * recommended_rate / 1000
    
    # Determine market position
    if recommended_rate < float(base_rate):
        market_position = "BELOW_MARKET"
        competitiveness = "HIGHLY_COMPETITIVE"
    elif recommended_rate > float(base_rate * Decimal("1.1")):
        market_position = "ABOVE_MARKET"
        competitiveness = "PREMIUM_POSITIONING"
    else:
        market_position = "AT_MARKET"
        competitiveness = "COMPETITIVE"
    
    factors = [
        {"factor": "Base rate", "impact": str(float(base_rate)), "description": f"Standard rate for {request.coverage_type.value}"},
        {"factor": "Risk adjustment", "impact": str(float(risk_adjustment)), "description": "Based on route and cargo risk"},
        {"factor": "Market conditions", "impact": "1.0", "description": "Current market is neutral"}
    ]
    
    return PricingRecommendation(
        recommended_rate=round(recommended_rate, 4),
        min_rate=round(min_rate, 4),
        max_rate=round(max_rate, 4),
        premium_usd=round(premium, 2),
        market_position=market_position,
        factors=factors,
        competitiveness=competitiveness
    )


# ============================================================================
# Risk Mitigation Recommendations
# ============================================================================

@router.post("/mitigation", response_model=List[MitigationRecommendation])
async def get_mitigation_recommendations(
    request: MitigationRequest,
    current_user = Depends(get_current_user)
):
    """
    Get risk mitigation recommendations.
    """
    recommendations = []
    
    mitigation_strategies = {
        "weather": MitigationRecommendation(
            risk_factor="Weather Risk",
            current_impact="HIGH",
            recommendation="Schedule shipment during favorable weather window. Consider weather-resistant packaging.",
            expected_risk_reduction=0.25,
            implementation_cost="LOW",
            priority="HIGH"
        ),
        "piracy": MitigationRecommendation(
            risk_factor="Piracy Risk",
            current_impact="CRITICAL",
            recommendation="Use armed escort service. Register with UKMTO. Consider alternative routing via Cape.",
            expected_risk_reduction=0.40,
            implementation_cost="HIGH",
            priority="CRITICAL"
        ),
        "theft": MitigationRecommendation(
            risk_factor="Theft Risk",
            current_impact="MEDIUM",
            recommendation="Use GPS tracking. Seal containers with tamper-evident seals. Require signature confirmations.",
            expected_risk_reduction=0.30,
            implementation_cost="MEDIUM",
            priority="MEDIUM"
        ),
        "damage": MitigationRecommendation(
            risk_factor="Damage Risk",
            current_impact="MEDIUM",
            recommendation="Upgrade packaging. Use shock indicators. Request careful handling labels.",
            expected_risk_reduction=0.20,
            implementation_cost="LOW",
            priority="MEDIUM"
        ),
        "delay": MitigationRecommendation(
            risk_factor="Delay Risk",
            current_impact="LOW",
            recommendation="Build buffer into schedule. Use premium shipping option. Pre-clear customs.",
            expected_risk_reduction=0.15,
            implementation_cost="MEDIUM",
            priority="LOW"
        ),
        "port_congestion": MitigationRecommendation(
            risk_factor="Port Congestion",
            current_impact="MEDIUM",
            recommendation="Use alternative ports. Schedule off-peak arrival. Pre-book terminal slots.",
            expected_risk_reduction=0.20,
            implementation_cost="LOW",
            priority="MEDIUM"
        ),
        "carrier_reliability": MitigationRecommendation(
            risk_factor="Carrier Reliability",
            current_impact="MEDIUM",
            recommendation="Switch to higher-rated carrier. Use backup carrier clause. Monitor vessel schedule.",
            expected_risk_reduction=0.25,
            implementation_cost="MEDIUM",
            priority="HIGH"
        )
    }
    
    for factor in request.risk_factors:
        factor_lower = factor.lower().replace(" ", "_")
        if factor_lower in mitigation_strategies:
            recommendations.append(mitigation_strategies[factor_lower])
        else:
            # Generic recommendation
            recommendations.append(MitigationRecommendation(
                risk_factor=factor,
                current_impact="MEDIUM",
                recommendation=f"Review {factor} exposure and implement standard mitigation controls.",
                expected_risk_reduction=0.15,
                implementation_cost="MEDIUM",
                priority="MEDIUM"
            ))
    
    # Sort by priority
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recommendations.sort(key=lambda x: priority_order.get(x.priority, 2))
    
    return recommendations


# ============================================================================
# Carrier Recommendations
# ============================================================================

@router.get("/carriers", response_model=List[CarrierRecommendation])
async def get_carrier_recommendations(
    origin_port: str = Query(..., description="Origin port code"),
    destination_port: str = Query(..., description="Destination port code"),
    cargo_type: str = Query("GENERAL", description="Cargo type"),
    current_user = Depends(get_current_user)
):
    """
    Get carrier recommendations for a route.
    """
    # Mock carrier data
    carriers = [
        CarrierRecommendation(
            carrier_name="Maersk Line",
            carrier_id="MAEU",
            reliability_score=0.92,
            on_time_rate=0.88,
            price_index=1.1,
            coverage_areas=["Global", "Trans-Pacific", "Asia-Europe"],
            pros=["Excellent reliability", "Wide coverage", "Good tracking"],
            cons=["Premium pricing", "Limited flexibility"],
            recommended=True
        ),
        CarrierRecommendation(
            carrier_name="MSC",
            carrier_id="MSCU",
            reliability_score=0.88,
            on_time_rate=0.85,
            price_index=0.95,
            coverage_areas=["Global", "Mediterranean", "Americas"],
            pros=["Competitive pricing", "Good capacity", "Flexible schedules"],
            cons=["Slightly lower on-time rate"],
            recommended=True
        ),
        CarrierRecommendation(
            carrier_name="CMA CGM",
            carrier_id="CMDU",
            reliability_score=0.90,
            on_time_rate=0.86,
            price_index=1.0,
            coverage_areas=["Global", "Africa", "Indian Ocean"],
            pros=["Good Africa coverage", "Reefer expertise", "Environmental focus"],
            cons=["Limited transshipment options"],
            recommended=cargo_type == "REEFER"
        ),
        CarrierRecommendation(
            carrier_name="Evergreen",
            carrier_id="EGLV",
            reliability_score=0.86,
            on_time_rate=0.84,
            price_index=0.9,
            coverage_areas=["Trans-Pacific", "Asia", "Americas"],
            pros=["Best value", "Good Asia coverage"],
            cons=["Limited Europe coverage", "Basic tracking"],
            recommended=False
        )
    ]
    
    # Sort by reliability
    carriers.sort(key=lambda x: x.reliability_score, reverse=True)
    
    return carriers


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def recommendations_health():
    """Check recommendations service health."""
    return {
        "status": "healthy",
        "services": {
            "coverage": "operational",
            "routes": "operational",
            "pricing": "operational",
            "mitigation": "operational",
            "carriers": "operational"
        },
        "models_loaded": True
    }
