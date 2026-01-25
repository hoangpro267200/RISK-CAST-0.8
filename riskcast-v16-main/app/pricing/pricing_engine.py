"""
Dynamic Pricing Engine

Calculates insurance premium from risk assessment.

Pricing formula:
Premium = Base Rate × Risk Factor × Cargo Factor × Route Factor × Duration Factor
        + Loading/Surcharges
        - Discounts
        + Expenses
        + Profit Margin

Key principles:
1. Risk-based pricing (higher risk = higher premium)
2. Actuarially sound (expected loss + expenses + margin)
3. Competitive (market-aware adjustments)
4. Transparent (clear breakdown for customers)
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import logging
import hashlib

from app.core.risk_engine.v16.risk_engine_calibrated import CalibratedRiskResult


class PricingTier(Enum):
    """Pricing tiers for different customer segments."""
    STANDARD = "STANDARD"
    PREFERRED = "PREFERRED"      # Good loss history
    PREMIER = "PREMIER"          # High volume, excellent history
    HIGH_RISK = "HIGH_RISK"      # Elevated risk profile


class CoverageType(Enum):
    """Types of coverage."""
    ALL_RISKS = "ALL_RISKS"
    NAMED_PERILS = "NAMED_PERILS"
    TOTAL_LOSS_ONLY = "TOTAL_LOSS_ONLY"


class DeductibleType(Enum):
    """Deductible calculation methods."""
    FIXED = "FIXED"              # Fixed amount
    PERCENTAGE = "PERCENTAGE"    # % of cargo value
    FRANCHISE = "FRANCHISE"      # Full loss if exceeds threshold


@dataclass
class PricingInput:
    """Inputs for pricing calculation."""
    # Risk assessment (required)
    risk_result: CalibratedRiskResult
    
    # Cargo details (required)
    cargo_value_usd: Decimal
    cargo_type: str
    
    # Route details (required)
    origin_port: str
    destination_port: str
    transit_days: int
    
    # Policy details (required)
    policy_start_date: date
    policy_end_date: date
    
    # Optional fields with defaults
    packaging_quality: str = "STANDARD"  # BASIC, STANDARD, PREMIUM
    
    # Coverage details
    coverage_type: CoverageType = CoverageType.ALL_RISKS
    coverage_limit_usd: Optional[Decimal] = None  # If different from cargo value
    deductible_type: DeductibleType = DeductibleType.PERCENTAGE
    deductible_value: Decimal = Decimal("0.01")  # 1% default
    
    # Customer details
    customer_id: Optional[str] = None
    pricing_tier: PricingTier = PricingTier.STANDARD
    loss_history_years: int = 0
    loss_ratio_3yr: Optional[float] = None


@dataclass
class PricingComponent:
    """A component of the premium calculation."""
    name: str
    description: str
    amount: Decimal
    rate: Optional[Decimal] = None
    is_credit: bool = False  # True = reduces premium


@dataclass
class PremiumBreakdown:
    """Detailed breakdown of premium calculation."""
    # Inputs
    cargo_value: Decimal
    coverage_limit: Decimal
    
    # Core premium
    base_rate: Decimal
    base_premium: Decimal
    
    # Risk adjustments
    risk_factor: Decimal
    risk_adjusted_premium: Decimal
    
    # Other factors
    cargo_factor: Decimal
    route_factor: Decimal
    duration_factor: Decimal
    coverage_factor: Decimal
    
    # Loadings and surcharges
    loadings: List[PricingComponent]
    total_loadings: Decimal
    
    # Discounts
    discounts: List[PricingComponent]
    total_discounts: Decimal
    
    # Final calculation
    net_premium: Decimal
    expenses_loading: Decimal
    profit_margin: Decimal
    
    # Taxes (if applicable)
    tax_rate: Decimal
    tax_amount: Decimal
    
    # Final premium
    total_premium: Decimal
    premium_per_unit: Decimal  # Per $1000 of value
    
    # Deductible
    deductible_amount: Decimal
    deductible_description: str
    
    # Metadata
    pricing_version: str
    calculated_at: datetime
    valid_until: datetime


@dataclass
class PricingResult:
    """Complete pricing result."""
    # Summary
    total_premium_usd: Decimal
    premium_rate_per_mille: Decimal  # Per $1000
    
    # Breakdown
    breakdown: PremiumBreakdown
    
    # Risk info
    risk_score: float
    risk_grade: str  # A, B, C, D, F
    expected_loss_ratio: float
    
    # Competitiveness
    is_competitive: bool
    market_position: str  # BELOW_MARKET, AT_MARKET, ABOVE_MARKET
    
    # Recommendations
    recommendations: List[str]
    
    # Quote validity
    quote_id: str
    valid_from: datetime
    valid_until: datetime


class PricingEngine:
    """
    Dynamic pricing engine for marine cargo insurance.
    
    Pricing methodology:
    1. Start with base rate for cargo type
    2. Apply risk multiplier from risk assessment
    3. Apply cargo, route, duration adjustments
    4. Add loadings (war risk, high-value, etc.)
    5. Apply discounts (volume, loyalty, etc.)
    6. Add expenses and profit margin
    7. Apply taxes
    """
    
    # Base rates per $1000 (per mille) by cargo type
    BASE_RATES = {
        "ELECTRONICS": Decimal("2.50"),
        "MACHINERY": Decimal("1.80"),
        "TEXTILES": Decimal("1.20"),
        "FOOD_PERISHABLE": Decimal("3.00"),
        "FOOD_DRY": Decimal("1.50"),
        "CHEMICALS": Decimal("2.20"),
        "PHARMACEUTICALS": Decimal("2.80"),
        "AUTOMOTIVE": Decimal("2.00"),
        "RAW_MATERIALS": Decimal("1.00"),
        "GENERAL": Decimal("1.50"),
    }
    
    # Risk score to factor mapping
    RISK_FACTORS = {
        (0.0, 0.2): Decimal("0.70"),   # Very low risk
        (0.2, 0.4): Decimal("0.85"),   # Low risk
        (0.4, 0.6): Decimal("1.00"),   # Medium risk
        (0.6, 0.8): Decimal("1.30"),   # High risk
        (0.8, 1.0): Decimal("1.80"),   # Very high risk
    }
    
    # Coverage type factors
    COVERAGE_FACTORS = {
        CoverageType.ALL_RISKS: Decimal("1.00"),
        CoverageType.NAMED_PERILS: Decimal("0.75"),
        CoverageType.TOTAL_LOSS_ONLY: Decimal("0.50"),
    }
    
    # Tier discounts
    TIER_DISCOUNTS = {
        PricingTier.STANDARD: Decimal("0.00"),
        PricingTier.PREFERRED: Decimal("0.10"),    # 10% discount
        PricingTier.PREMIER: Decimal("0.20"),      # 20% discount
        PricingTier.HIGH_RISK: Decimal("-0.25"),   # 25% loading
    }
    
    # Expense and margin rates
    EXPENSE_RATE = Decimal("0.25")      # 25% expenses
    PROFIT_MARGIN_RATE = Decimal("0.10") # 10% margin
    
    # Minimum premium
    MINIMUM_PREMIUM = Decimal("50.00")
    
    def __init__(
        self,
        audit=None,
        market_data_service=None
    ):
        self.audit = audit
        self.market_data = market_data_service
        self.logger = logging.getLogger(__name__)
        self.pricing_version = "2.0.0"
    
    async def calculate_premium(
        self,
        input: PricingInput
    ) -> PricingResult:
        """
        Calculate premium for given inputs.
        """
        self.logger.info(
            f"Calculating premium for cargo value ${input.cargo_value_usd:,.2f}"
        )
        
        # 1. Get base rate
        base_rate = self._get_base_rate(input.cargo_type)
        
        # 2. Determine coverage limit
        coverage_limit = input.coverage_limit_usd or input.cargo_value_usd
        
        # 3. Calculate base premium
        base_premium = (coverage_limit / Decimal("1000")) * base_rate
        
        # 4. Get risk factor from risk score
        risk_score = input.risk_result.overall_risk_score
        risk_factor = self._get_risk_factor(risk_score)
        risk_adjusted = base_premium * risk_factor
        
        # 5. Apply other factors
        cargo_factor = self._get_cargo_factor(input)
        route_factor = self._get_route_factor(input)
        duration_factor = self._get_duration_factor(input.transit_days)
        coverage_factor = self.COVERAGE_FACTORS[input.coverage_type]
        
        adjusted_premium = (
            risk_adjusted * 
            cargo_factor * 
            route_factor * 
            duration_factor * 
            coverage_factor
        )
        
        # 6. Calculate loadings
        loadings = self._calculate_loadings(input)
        total_loadings = sum(l.amount for l in loadings)
        
        # 7. Calculate discounts
        discounts = self._calculate_discounts(input)
        total_discounts = sum(d.amount for d in discounts)
        
        # 8. Net premium
        net_premium = adjusted_premium + total_loadings - total_discounts
        
        # 9. Add expenses and margin
        expenses = net_premium * self.EXPENSE_RATE
        margin = net_premium * self.PROFIT_MARGIN_RATE
        
        premium_before_tax = net_premium + expenses + margin
        
        # 10. Apply minimum
        premium_before_tax = max(premium_before_tax, self.MINIMUM_PREMIUM)
        
        # 11. Tax (placeholder - varies by jurisdiction)
        tax_rate = Decimal("0.00")  # No tax for now
        tax_amount = premium_before_tax * tax_rate
        
        # 12. Total premium
        total_premium = (premium_before_tax + tax_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        # 13. Calculate rate per mille
        rate_per_mille = (total_premium / coverage_limit * Decimal("1000")).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        ) if coverage_limit > 0 else Decimal("0")
        
        # 14. Calculate deductible
        deductible_amount, deductible_desc = self._calculate_deductible(
            input, coverage_limit
        )
        
        # 15. Determine risk grade
        risk_grade = self._get_risk_grade(risk_score)
        
        # 16. Check competitiveness
        is_competitive, market_position = await self._check_competitiveness(
            rate_per_mille, input
        )
        
        # 17. Generate recommendations
        recommendations = self._generate_recommendations(input, risk_score)
        
        # Build breakdown
        breakdown = PremiumBreakdown(
            cargo_value=input.cargo_value_usd,
            coverage_limit=coverage_limit,
            base_rate=base_rate,
            base_premium=base_premium,
            risk_factor=risk_factor,
            risk_adjusted_premium=risk_adjusted,
            cargo_factor=cargo_factor,
            route_factor=route_factor,
            duration_factor=duration_factor,
            coverage_factor=coverage_factor,
            loadings=loadings,
            total_loadings=total_loadings,
            discounts=discounts,
            total_discounts=total_discounts,
            net_premium=net_premium,
            expenses_loading=expenses,
            profit_margin=margin,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_premium=total_premium,
            premium_per_unit=rate_per_mille,
            deductible_amount=deductible_amount,
            deductible_description=deductible_desc,
            pricing_version=self.pricing_version,
            calculated_at=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=7)
        )
        
        # Generate quote ID
        quote_data = f"{input.cargo_value_usd}:{input.cargo_type}:{datetime.utcnow().isoformat()}"
        quote_id = f"Q-{hashlib.sha256(quote_data.encode()).hexdigest()[:12].upper()}"
        
        result = PricingResult(
            total_premium_usd=total_premium,
            premium_rate_per_mille=rate_per_mille,
            breakdown=breakdown,
            risk_score=risk_score,
            risk_grade=risk_grade,
            expected_loss_ratio=input.risk_result.expected_loss_pct,
            is_competitive=is_competitive,
            market_position=market_position,
            recommendations=recommendations,
            quote_id=quote_id,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=7)
        )
        
        # Audit
        if self.audit:
            self.audit.append_event(
                event_type="QUOTE",
                action="PREMIUM_CALCULATED",
                entity_type="quote",
                entity_id=quote_id,
                actor_type="SYSTEM",
                payload={
                    "cargo_value": float(input.cargo_value_usd),
                    "total_premium": float(total_premium),
                    "rate_per_mille": float(rate_per_mille),
                    "risk_score": risk_score,
                    "risk_grade": risk_grade
                }
            )
        
        return result
    
    def _get_base_rate(self, cargo_type: str) -> Decimal:
        """Get base rate for cargo type."""
        return self.BASE_RATES.get(
            cargo_type.upper(), 
            self.BASE_RATES["GENERAL"]
        )
    
    def _get_risk_factor(self, risk_score: float) -> Decimal:
        """Convert risk score to pricing factor."""
        for (low, high), factor in self.RISK_FACTORS.items():
            if low <= risk_score < high:
                return factor
        return Decimal("2.00")  # Very high risk default
    
    def _get_cargo_factor(self, input: PricingInput) -> Decimal:
        """Get factor based on cargo characteristics."""
        factor = Decimal("1.00")
        
        # Packaging quality
        if input.packaging_quality == "BASIC":
            factor *= Decimal("1.10")  # 10% loading for basic packaging
        elif input.packaging_quality == "PREMIUM":
            factor *= Decimal("0.95")  # 5% credit for premium packaging
        
        return factor
    
    def _get_route_factor(self, input: PricingInput) -> Decimal:
        """Get factor based on route characteristics."""
        # This would use route data in production
        # For now, simple heuristic
        factor = Decimal("1.00")
        
        # High-risk routes (simplified)
        high_risk_regions = ["SOML", "ADEN", "SING"]  # Somalia, Aden, Malacca
        if any(r in input.origin_port.upper() or r in input.destination_port.upper() 
               for r in high_risk_regions):
            factor *= Decimal("1.25")
        
        return factor
    
    def _get_duration_factor(self, transit_days: int) -> Decimal:
        """Get factor based on transit duration."""
        if transit_days <= 7:
            return Decimal("0.90")
        elif transit_days <= 14:
            return Decimal("1.00")
        elif transit_days <= 30:
            return Decimal("1.10")
        else:
            return Decimal("1.25")
    
    def _calculate_loadings(self, input: PricingInput) -> List[PricingComponent]:
        """Calculate premium loadings/surcharges."""
        loadings = []
        
        # War risk surcharge (if applicable)
        # Would check against war risk zones
        war_risk_zones = ["UA", "RU", "YE"]  # Example
        if any(z in input.origin_port.upper() or z in input.destination_port.upper()
               for z in war_risk_zones):
            loadings.append(PricingComponent(
                name="War Risk Surcharge",
                description="Additional coverage for war/civil unrest zones",
                amount=input.cargo_value_usd * Decimal("0.005"),  # 0.5%
                rate=Decimal("0.005")
            ))
        
        # High value surcharge
        if input.cargo_value_usd > Decimal("1000000"):
            loadings.append(PricingComponent(
                name="High Value Surcharge",
                description="Additional coverage for high-value shipments",
                amount=Decimal("500.00"),
                rate=None
            ))
        
        # Refrigerated cargo
        if "PERISHABLE" in input.cargo_type.upper() or "REFRIGERATED" in input.cargo_type.upper():
            loadings.append(PricingComponent(
                name="Refrigeration Breakdown Coverage",
                description="Coverage for temperature-controlled cargo",
                amount=input.cargo_value_usd * Decimal("0.003"),
                rate=Decimal("0.003")
            ))
        
        return loadings
    
    def _calculate_discounts(self, input: PricingInput) -> List[PricingComponent]:
        """Calculate premium discounts."""
        discounts = []
        
        # Tier discount
        tier_discount = self.TIER_DISCOUNTS[input.pricing_tier]
        if tier_discount > 0:
            base_for_discount = input.cargo_value_usd * Decimal("0.002")  # Approximate
            discounts.append(PricingComponent(
                name=f"{input.pricing_tier.value} Tier Discount",
                description=f"Customer tier discount ({tier_discount*100:.0f}%)",
                amount=base_for_discount * tier_discount,
                rate=tier_discount,
                is_credit=True
            ))
        
        # No-claims discount
        if input.loss_ratio_3yr is not None and input.loss_ratio_3yr < 0.3:
            ncd_rate = Decimal("0.10")  # 10% for good loss history
            discounts.append(PricingComponent(
                name="No-Claims Discount",
                description="Discount for favorable loss history",
                amount=input.cargo_value_usd * Decimal("0.002") * ncd_rate,
                rate=ncd_rate,
                is_credit=True
            ))
        
        # Volume discount (would check annual volume)
        # Placeholder
        
        return discounts
    
    def _calculate_deductible(
        self, 
        input: PricingInput,
        coverage_limit: Decimal
    ) -> Tuple[Decimal, str]:
        """Calculate deductible amount."""
        if input.deductible_type == DeductibleType.FIXED:
            amount = input.deductible_value
            desc = f"Fixed deductible of ${amount:,.2f}"
        
        elif input.deductible_type == DeductibleType.PERCENTAGE:
            amount = coverage_limit * input.deductible_value
            desc = f"{input.deductible_value*100:.1f}% of coverage (${amount:,.2f})"
        
        elif input.deductible_type == DeductibleType.FRANCHISE:
            amount = input.deductible_value
            desc = f"Franchise deductible of ${amount:,.2f} (waived if loss exceeds)"
        
        else:
            amount = Decimal("0")
            desc = "No deductible"
        
        return amount.quantize(Decimal("0.01")), desc
    
    def _get_risk_grade(self, risk_score: float) -> str:
        """Convert risk score to letter grade."""
        if risk_score < 0.2:
            return "A"
        elif risk_score < 0.4:
            return "B"
        elif risk_score < 0.6:
            return "C"
        elif risk_score < 0.8:
            return "D"
        else:
            return "F"
    
    async def _check_competitiveness(
        self,
        rate_per_mille: Decimal,
        input: PricingInput
    ) -> Tuple[bool, str]:
        """Check if rate is competitive vs market."""
        # Would use market data service
        # Placeholder logic
        market_avg = Decimal("2.00")  # Example market average
        
        if rate_per_mille < market_avg * Decimal("0.9"):
            return True, "BELOW_MARKET"
        elif rate_per_mille <= market_avg * Decimal("1.1"):
            return True, "AT_MARKET"
        else:
            return False, "ABOVE_MARKET"
    
    def _generate_recommendations(
        self,
        input: PricingInput,
        risk_score: float
    ) -> List[str]:
        """Generate recommendations for the customer."""
        recommendations = []
        
        if risk_score > 0.6:
            recommendations.append(
                "Consider premium packaging to reduce cargo damage risk"
            )
        
        if input.pricing_tier == PricingTier.STANDARD:
            recommendations.append(
                "Upgrade to Preferred tier with 3+ shipments for 10% discount"
            )
        
        if input.deductible_type == DeductibleType.PERCENTAGE and input.deductible_value < Decimal("0.02"):
            recommendations.append(
                "Increasing deductible to 2% could reduce premium by ~15%"
            )
        
        if input.coverage_type == CoverageType.ALL_RISKS:
            recommendations.append(
                "Named Perils coverage may provide 25% savings if specific risks are known"
            )
        
        return recommendations
