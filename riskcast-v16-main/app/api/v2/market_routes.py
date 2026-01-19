"""
RISKCAST Market Value API Routes
=================================
API endpoints for ROI calculation, case studies, and insurance premiums.

Pipeline E: Market Value Proof & ROI Logic

Author: RISKCAST Team
Version: 2.0
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field
import logging

from app.services.roi_calculator import (
    ROICalculator,
    ROIScenario,
    CompanyProfile,
    CostAssumptions,
    BenefitAssumptions,
    calculate_roi,
    get_default_assumptions
)
from app.services.case_study_generator import (
    CaseStudyGenerator,
    generate_case_study,
    list_templates
)
from app.services.insurance_premium_calculator import (
    InsurancePremiumCalculator,
    calculate_premium,
    calculate_portfolio_premium,
    estimate_savings
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market", tags=["Market Value"])


# =============================================================================
# Request Models
# =============================================================================

class CompanyProfileRequest(BaseModel):
    """Company profile for ROI calculation."""
    company_name: str = "Sample Company"
    industry: str = "logistics"
    annual_shipments: int = Field(default=1000, ge=1)
    avg_cargo_value_usd: float = Field(default=100000, ge=0)
    annual_revenue_usd: float = Field(default=50000000, ge=0)
    current_delay_rate: float = Field(default=0.15, ge=0, le=1)
    current_loss_rate: float = Field(default=0.05, ge=0, le=1)
    current_insurance_rate: float = Field(default=0.008, ge=0, le=0.1)
    analyst_count: int = Field(default=5, ge=0)


class CostAssumptionsRequest(BaseModel):
    """RISKCAST cost assumptions."""
    annual_subscription_usd: float = Field(default=12000, ge=0)
    implementation_cost_usd: float = Field(default=25000, ge=0)
    training_cost_usd: float = Field(default=5000, ge=0)
    integration_cost_usd: float = Field(default=15000, ge=0)
    annual_support_usd: float = Field(default=3000, ge=0)


class BenefitAssumptionsRequest(BaseModel):
    """Expected benefit assumptions."""
    delay_reduction_pct: float = Field(default=0.30, ge=0, le=1)
    loss_reduction_pct: float = Field(default=0.25, ge=0, le=1)
    insurance_rate_reduction_pct: float = Field(default=0.15, ge=0, le=1)
    avg_delay_cost_usd: float = Field(default=5000, ge=0)
    avg_loss_severity_pct: float = Field(default=0.10, ge=0, le=1)
    analyst_hours_before: float = Field(default=4.0, ge=0)
    analyst_hours_after: float = Field(default=0.5, ge=0)
    analyst_hourly_rate_usd: float = Field(default=75, ge=0)


class ROIRequest(BaseModel):
    """Full ROI calculation request."""
    company_profile: CompanyProfileRequest
    cost_assumptions: Optional[CostAssumptionsRequest] = None
    benefit_assumptions: Optional[BenefitAssumptionsRequest] = None
    years: int = Field(default=3, ge=1, le=10)


class CaseStudyRequest(BaseModel):
    """Case study generation request."""
    template_type: str = Field(..., description="Template type: forwarder, manufacturer, insurance")
    company_data: Optional[Dict] = None
    anonymize: bool = True


class PremiumRequest(BaseModel):
    """Insurance premium calculation request."""
    cargo_value: float = Field(..., gt=0, description="Cargo value in USD")
    transport_mode: str = Field(..., description="Transport mode: ocean, air, rail, road, multimodal")
    risk_score: float = Field(..., ge=0, le=100, description="RISKCAST risk score")
    cargo_type: str = Field(default="general", description="Type of cargo")
    additional_factors: Optional[Dict] = None


class ShipmentItem(BaseModel):
    """Single shipment for portfolio calculation."""
    shipment_id: Optional[str] = None
    cargo_value: float = Field(..., gt=0)
    transport_mode: str
    risk_score: float = Field(..., ge=0, le=100)
    cargo_type: str = "general"
    additional_factors: Optional[Dict] = None


class PortfolioPremiumRequest(BaseModel):
    """Portfolio premium calculation request."""
    shipments: List[ShipmentItem] = Field(..., min_length=1)


class SavingsEstimateRequest(BaseModel):
    """Savings estimate request."""
    current_risk_score: float = Field(..., ge=0, le=100)
    projected_risk_score: float = Field(..., ge=0, le=100)
    cargo_value: float = Field(..., gt=0)
    transport_mode: str


# =============================================================================
# ROI Calculator Endpoints
# =============================================================================

@router.post("/roi/calculate", response_model=Dict[str, Any])
async def calculate_roi_endpoint(request: ROIRequest):
    """
    Calculate comprehensive ROI for RISKCAST adoption.
    
    Returns:
    - Total cost and benefit over analysis period
    - Net benefit and ROI percentage
    - Payback period in months
    - NPV with 10% discount rate
    - Year-by-year breakdown
    - Cost and benefit breakdown by category
    - Sensitivity analysis
    - Executive recommendation
    """
    try:
        company = CompanyProfile(
            company_name=request.company_profile.company_name,
            industry=request.company_profile.industry,
            annual_shipments=request.company_profile.annual_shipments,
            avg_cargo_value_usd=request.company_profile.avg_cargo_value_usd,
            annual_revenue_usd=request.company_profile.annual_revenue_usd,
            current_delay_rate=request.company_profile.current_delay_rate,
            current_loss_rate=request.company_profile.current_loss_rate,
            current_insurance_rate=request.company_profile.current_insurance_rate,
            analyst_count=request.company_profile.analyst_count
        )
        
        costs = CostAssumptions()
        if request.cost_assumptions:
            costs = CostAssumptions(
                annual_subscription_usd=request.cost_assumptions.annual_subscription_usd,
                implementation_cost_usd=request.cost_assumptions.implementation_cost_usd,
                training_cost_usd=request.cost_assumptions.training_cost_usd,
                integration_cost_usd=request.cost_assumptions.integration_cost_usd,
                annual_support_usd=request.cost_assumptions.annual_support_usd
            )
        
        benefits = BenefitAssumptions()
        if request.benefit_assumptions:
            benefits = BenefitAssumptions(
                delay_reduction_pct=request.benefit_assumptions.delay_reduction_pct,
                loss_reduction_pct=request.benefit_assumptions.loss_reduction_pct,
                insurance_rate_reduction_pct=request.benefit_assumptions.insurance_rate_reduction_pct,
                avg_delay_cost_usd=request.benefit_assumptions.avg_delay_cost_usd,
                avg_loss_severity_pct=request.benefit_assumptions.avg_loss_severity_pct,
                analyst_hours_before=request.benefit_assumptions.analyst_hours_before,
                analyst_hours_after=request.benefit_assumptions.analyst_hours_after,
                analyst_hourly_rate_usd=request.benefit_assumptions.analyst_hourly_rate_usd
            )
        
        scenario = ROIScenario(
            company_profile=company,
            cost_assumptions=costs,
            benefit_assumptions=benefits,
            years=request.years
        )
        
        result = ROICalculator.calculate_roi(scenario)
        
        logger.info(f"ROI calculated: {result.summary['roi_percentage']:.1f}% for {company.company_name}")
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"ROI calculation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/roi/defaults", response_model=Dict[str, Any])
async def get_roi_defaults():
    """
    Get default ROI calculation assumptions.
    
    Useful for pre-populating forms or understanding baseline assumptions.
    """
    return get_default_assumptions()


@router.get("/roi/quick", response_model=Dict[str, Any])
async def quick_roi_estimate(
    annual_shipments: int = Query(1000, ge=1, description="Number of shipments per year"),
    avg_cargo_value: float = Query(100000, ge=0, description="Average cargo value in USD"),
    current_delay_rate: float = Query(0.15, ge=0, le=1, description="Current delay rate (0-1)")
):
    """
    Quick ROI estimate with minimal inputs.
    
    Uses industry-standard assumptions for other values.
    """
    profile = {
        'annual_shipments': annual_shipments,
        'avg_cargo_value_usd': avg_cargo_value,
        'current_delay_rate': current_delay_rate
    }
    
    result = calculate_roi(profile)
    
    # Return simplified summary
    return {
        'quick_estimate': True,
        'inputs': profile,
        'summary': result['summary'],
        'recommendation': result['recommendation'],
        'note': 'This is a quick estimate. Use /roi/calculate for detailed analysis.'
    }


# =============================================================================
# Case Study Endpoints
# =============================================================================

@router.get("/case-studies/templates", response_model=List[Dict])
async def get_case_study_templates():
    """
    List available case study templates.
    
    Returns template types with descriptions and key metrics.
    """
    return list_templates()


@router.post("/case-studies/generate", response_model=Dict[str, Any])
async def generate_case_study_endpoint(request: CaseStudyRequest):
    """
    Generate a case study from template.
    
    Can use:
    - Synthetic data (default)
    - Real company data (anonymized if flag set)
    
    Available templates:
    - forwarder: Freight forwarder focused on delay reduction
    - manufacturer: Manufacturer focused on cargo protection
    - insurance: Insurance underwriter focused on pricing accuracy
    """
    try:
        valid_templates = ['forwarder', 'manufacturer', 'insurance']
        if request.template_type not in valid_templates:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid template type. Must be one of: {valid_templates}"
            )
        
        result = CaseStudyGenerator.generate_case_study(
            template_type=request.template_type,
            company_data=request.company_data,
            anonymize=request.anonymize
        )
        
        logger.info(f"Case study generated: {request.template_type}")
        
        return result.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Case study generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate case study")


@router.get("/case-studies/sample/{template_type}", response_model=Dict[str, Any])
async def get_sample_case_study(
    template_type: str,
    seed: int = Query(None, description="Random seed for reproducibility")
):
    """
    Get a sample case study for a specific template type.
    
    Use seed parameter for reproducible results in demos.
    """
    valid_templates = ['forwarder', 'manufacturer', 'insurance']
    if template_type not in valid_templates:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template type. Must be one of: {valid_templates}"
        )
    
    result = CaseStudyGenerator.generate_case_study(
        template_type=template_type,
        anonymize=True,
        seed=seed
    )
    
    return result.to_dict()


# =============================================================================
# Insurance Premium Endpoints
# =============================================================================

@router.post("/insurance/premium/calculate", response_model=Dict[str, Any])
async def calculate_premium_endpoint(request: PremiumRequest):
    """
    Calculate insurance premium based on RISKCAST risk score.
    
    Returns:
    - Premium amount and rate
    - Risk class and multipliers
    - Recommended deductible
    - Comparison to baseline (without risk adjustment)
    - Actionable recommendations
    """
    try:
        result = InsurancePremiumCalculator.calculate_premium(
            cargo_value=request.cargo_value,
            transport_mode=request.transport_mode,
            risk_score=request.risk_score,
            cargo_type=request.cargo_type,
            additional_factors=request.additional_factors
        )
        
        logger.info(
            f"Premium calculated: ${result.premium_usd:,.2f} for "
            f"${request.cargo_value:,.0f} cargo, risk score {request.risk_score}"
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Premium calculation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/insurance/premium/portfolio", response_model=Dict[str, Any])
async def calculate_portfolio_premium_endpoint(request: PortfolioPremiumRequest):
    """
    Calculate total premium for a portfolio of shipments.
    
    Includes:
    - Volume discounts (based on shipment count)
    - Diversification benefits
    - Risk distribution analysis
    - Portfolio-level recommendations
    """
    try:
        shipments = [s.model_dump() for s in request.shipments]
        
        result = InsurancePremiumCalculator.calculate_portfolio_premium(shipments)
        
        logger.info(
            f"Portfolio premium calculated: ${result.total_premium_after_discount:,.2f} "
            f"for {result.shipment_count} shipments"
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Portfolio premium calculation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/insurance/savings/estimate", response_model=Dict[str, Any])
async def estimate_savings_endpoint(request: SavingsEstimateRequest):
    """
    Estimate premium savings from risk score improvement.
    
    Useful for demonstrating RISKCAST value:
    - Current premium at current risk score
    - Projected premium at improved risk score
    - Estimated savings amount and percentage
    """
    try:
        if request.projected_risk_score >= request.current_risk_score:
            raise HTTPException(
                status_code=400,
                detail="Projected risk score must be lower than current risk score"
            )
        
        result = InsurancePremiumCalculator.estimate_savings_with_riskcast(
            current_premium=0,  # Calculated internally
            current_risk_score=request.current_risk_score,
            projected_risk_score=request.projected_risk_score,
            cargo_value=request.cargo_value,
            transport_mode=request.transport_mode
        )
        
        logger.info(
            f"Savings estimate: ${result['estimated_savings']:,.2f} "
            f"from {request.current_risk_score} -> {request.projected_risk_score}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Savings estimation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/insurance/rates", response_model=Dict[str, Any])
async def get_insurance_rates():
    """
    Get baseline insurance rates and risk class definitions.
    
    Useful for understanding rate structure and risk classifications.
    """
    from app.services.insurance_premium_calculator import RiskClass
    
    return {
        'baseline_rates': InsurancePremiumCalculator.BASELINE_RATES,
        'risk_classes': {
            rc.value: {
                'description': rc.description,
                'multiplier': rc.multiplier,
                'score_range': InsurancePremiumCalculator.RISK_CLASS_BOUNDARIES.get(rc)
            }
            for rc in RiskClass
        },
        'cargo_adjustments': InsurancePremiumCalculator.CARGO_ADJUSTMENTS,
        'note': 'Rates are indicative and may vary based on specific underwriting criteria'
    }
