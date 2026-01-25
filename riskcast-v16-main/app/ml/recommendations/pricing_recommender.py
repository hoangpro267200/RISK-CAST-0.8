"""
Pricing Recommendation Engine

Features:
1. Competitive pricing analysis
2. Dynamic pricing suggestions
3. Discount optimization
4. Bundle recommendations
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class PricingRecommendation:
    """Pricing recommendation result."""
    recommended_rate: float
    recommended_premium: float
    min_rate: float  # Floor rate
    max_rate: float  # Ceiling rate
    market_position: str  # "competitive", "premium", "economy"
    confidence: float
    factors: Dict[str, float]
    suggested_discounts: List[Dict]
    reasoning: List[str]


@dataclass
class DiscountRecommendation:
    """Discount recommendation."""
    discount_type: str
    discount_pct: float
    conditions: Dict
    expected_conversion_lift: float
    margin_impact: float


class PricingRecommender:
    """
    Recommends optimal pricing based on market, competition, and customer.
    """
    
    # Market benchmark rates (per mille) by cargo type
    MARKET_RATES = {
        "ELECTRONICS": {"min": 0.8, "avg": 1.2, "max": 2.0},
        "MACHINERY": {"min": 0.5, "avg": 0.8, "max": 1.5},
        "FOOD_PERISHABLE": {"min": 1.0, "avg": 1.8, "max": 3.0},
        "TEXTILES": {"min": 0.4, "avg": 0.6, "max": 1.0},
        "CHEMICALS": {"min": 0.8, "avg": 1.5, "max": 2.5},
        "PHARMACEUTICALS": {"min": 1.2, "avg": 2.0, "max": 3.5},
        "AUTOMOTIVE": {"min": 0.6, "avg": 1.0, "max": 1.8},
        "RAW_MATERIALS": {"min": 0.3, "avg": 0.5, "max": 0.8},
        "GENERAL": {"min": 0.5, "avg": 1.0, "max": 2.0},
    }
    
    # Route risk multipliers
    ROUTE_MULTIPLIERS = {
        ("ASIA", "NORTH_AMERICA"): 1.0,
        ("ASIA", "EUROPE"): 0.95,
        ("EUROPE", "NORTH_AMERICA"): 0.85,
        ("MIDDLE_EAST", "EUROPE"): 1.2,
        ("AFRICA", "EUROPE"): 1.3,
        ("SOUTH_AMERICA", "NORTH_AMERICA"): 0.9,
    }
    
    def __init__(self):
        self.competitor_rates: Dict[str, float] = {}
        self.conversion_model = None
    
    def set_competitor_rates(self, rates: Dict[str, float]):
        """Set competitor rate benchmarks."""
        self.competitor_rates = rates
    
    def recommend_pricing(
        self,
        cargo_type: str,
        cargo_value_usd: float,
        risk_score: float,
        origin_region: str,
        destination_region: str,
        customer_tier: str = "STANDARD",
        customer_history: Optional[Dict] = None,
        target_margin: float = 0.20
    ) -> PricingRecommendation:
        """
        Generate pricing recommendation.
        """
        # Get market benchmark
        market_rates = self.MARKET_RATES.get(
            cargo_type.upper(),
            self.MARKET_RATES["GENERAL"]
        )
        
        # Calculate base rate from risk
        risk_adjusted_rate = self._calculate_risk_adjusted_rate(
            risk_score, market_rates
        )
        
        # Apply route multiplier
        route_key = (origin_region.upper(), destination_region.upper())
        route_multiplier = self.ROUTE_MULTIPLIERS.get(route_key, 1.0)
        route_adjusted_rate = risk_adjusted_rate * route_multiplier
        
        # Apply customer tier adjustment
        tier_adjustment = self._get_tier_adjustment(customer_tier)
        tier_adjusted_rate = route_adjusted_rate * tier_adjustment
        
        # Consider competition
        competitive_rate = self._adjust_for_competition(
            tier_adjusted_rate, cargo_type
        )
        
        # Apply volume discount if applicable
        volume_rate, volume_discount = self._calculate_volume_discount(
            competitive_rate, cargo_value_usd, customer_history
        )
        
        # Calculate final rate and premium
        final_rate = volume_rate
        final_premium = final_rate * cargo_value_usd / 1000
        
        # Ensure minimum margin
        min_rate = self._calculate_floor_rate(risk_score, market_rates, target_margin)
        final_rate = max(final_rate, min_rate)
        
        # Determine market position
        market_position = self._determine_market_position(
            final_rate, market_rates
        )
        
        # Generate discount suggestions
        discounts = self._suggest_discounts(
            customer_history, cargo_value_usd, customer_tier
        )
        
        # Generate reasoning
        reasoning = self._generate_pricing_reasoning(
            risk_score, route_multiplier, tier_adjustment,
            volume_discount, market_position
        )
        
        return PricingRecommendation(
            recommended_rate=final_rate,
            recommended_premium=final_premium,
            min_rate=min_rate,
            max_rate=market_rates["max"] * route_multiplier,
            market_position=market_position,
            confidence=0.85 if customer_history else 0.70,
            factors={
                "base_rate": risk_adjusted_rate,
                "route_multiplier": route_multiplier,
                "tier_adjustment": tier_adjustment,
                "volume_discount": volume_discount,
                "competitive_adjustment": competitive_rate / tier_adjusted_rate if tier_adjusted_rate > 0 else 1.0
            },
            suggested_discounts=discounts,
            reasoning=reasoning
        )
    
    def _calculate_risk_adjusted_rate(
        self,
        risk_score: float,
        market_rates: Dict[str, float]
    ) -> float:
        """Calculate rate based on risk score."""
        min_rate = market_rates["min"]
        max_rate = market_rates["max"]
        avg_rate = market_rates["avg"]
        
        if risk_score < 0.3:
            # Low risk - below average
            return min_rate + (avg_rate - min_rate) * (risk_score / 0.3)
        elif risk_score < 0.7:
            # Medium risk - around average
            normalized = (risk_score - 0.3) / 0.4
            return avg_rate + (max_rate - avg_rate) * 0.3 * normalized
        else:
            # High risk - above average
            normalized = (risk_score - 0.7) / 0.3
            return avg_rate + (max_rate - avg_rate) * (0.3 + 0.7 * normalized)
    
    def _get_tier_adjustment(self, tier: str) -> float:
        """Get pricing adjustment based on customer tier."""
        adjustments = {
            "PREMIER": 0.85,    # 15% discount
            "PREFERRED": 0.92,  # 8% discount
            "STANDARD": 1.00,   # No adjustment
            "HIGH_RISK": 1.15,  # 15% surcharge
            "NEW": 0.98,        # 2% discount (acquisition)
        }
        return adjustments.get(tier.upper(), 1.0)
    
    def _adjust_for_competition(
        self,
        rate: float,
        cargo_type: str
    ) -> float:
        """Adjust rate based on competitive landscape."""
        if not self.competitor_rates:
            return rate
        
        competitor_avg = self.competitor_rates.get(cargo_type.upper())
        if competitor_avg is None:
            return rate
        
        # If we're significantly above competition, adjust down
        if rate > competitor_avg * 1.2:
            # Cap at 10% above competition
            return min(rate, competitor_avg * 1.10)
        
        # If we're below competition, we have room to increase
        if rate < competitor_avg * 0.9:
            # Move closer to market (but stay competitive)
            return rate * 1.05
        
        return rate
    
    def _calculate_volume_discount(
        self,
        rate: float,
        cargo_value_usd: float,
        customer_history: Optional[Dict]
    ) -> Tuple[float, float]:
        """Calculate volume-based discount."""
        discount = 0.0
        
        # Shipment value discount
        if cargo_value_usd >= 5000000:
            discount = 0.15
        elif cargo_value_usd >= 1000000:
            discount = 0.10
        elif cargo_value_usd >= 500000:
            discount = 0.05
        
        # Annual volume discount
        if customer_history:
            annual_premium = customer_history.get('annual_premium', 0)
            if annual_premium >= 500000:
                discount = max(discount, 0.20)
            elif annual_premium >= 100000:
                discount = max(discount, 0.12)
            elif annual_premium >= 50000:
                discount = max(discount, 0.08)
        
        discounted_rate = rate * (1 - discount)
        return discounted_rate, discount
    
    def _calculate_floor_rate(
        self,
        risk_score: float,
        market_rates: Dict[str, float],
        target_margin: float
    ) -> float:
        """Calculate minimum acceptable rate."""
        # Floor should cover expected loss + expenses + minimum margin
        expected_loss_rate = risk_score * 0.05  # Simplified loss assumption
        expense_ratio = 0.25
        
        floor_rate = expected_loss_rate / (1 - expense_ratio - target_margin)
        
        # Also ensure we're not below market minimum
        return max(floor_rate, market_rates["min"] * 0.8)
    
    def _determine_market_position(
        self,
        rate: float,
        market_rates: Dict[str, float]
    ) -> str:
        """Determine market positioning."""
        avg_rate = market_rates["avg"]
        
        if rate < avg_rate * 0.85:
            return "economy"
        elif rate > avg_rate * 1.15:
            return "premium"
        else:
            return "competitive"
    
    def _suggest_discounts(
        self,
        customer_history: Optional[Dict],
        cargo_value_usd: float,
        customer_tier: str
    ) -> List[Dict]:
        """Suggest potential discounts."""
        discounts = []
        
        # Multi-policy discount
        if customer_history and customer_history.get('policy_count', 0) < 3:
            discounts.append({
                "type": "MULTI_POLICY",
                "discount_pct": 0.05,
                "condition": "Bundle with additional shipments",
                "conversion_lift": 0.15
            })
        
        # Annual policy discount
        if cargo_value_usd > 100000:
            discounts.append({
                "type": "ANNUAL_POLICY",
                "discount_pct": 0.10,
                "condition": "Convert to annual policy",
                "conversion_lift": 0.20
            })
        
        # Early payment discount
        discounts.append({
            "type": "EARLY_PAYMENT",
            "discount_pct": 0.02,
            "condition": "Pay within 10 days",
            "conversion_lift": 0.05
        })
        
        # Loyalty discount for existing customers
        if customer_history and customer_history.get('years_as_customer', 0) >= 2:
            discounts.append({
                "type": "LOYALTY",
                "discount_pct": 0.03,
                "condition": "Loyalty reward",
                "conversion_lift": 0.10
            })
        
        return discounts
    
    def _generate_pricing_reasoning(
        self,
        risk_score: float,
        route_multiplier: float,
        tier_adjustment: float,
        volume_discount: float,
        market_position: str
    ) -> List[str]:
        """Generate pricing reasoning."""
        reasons = []
        
        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high"
        reasons.append(f"Base rate reflects {risk_level} risk profile ({risk_score:.0%})")
        
        if route_multiplier != 1.0:
            direction = "premium" if route_multiplier > 1 else "discount"
            reasons.append(f"Route {direction} of {abs(1-route_multiplier):.0%} applied")
        
        if tier_adjustment != 1.0:
            if tier_adjustment < 1:
                reasons.append(f"Customer tier discount of {(1-tier_adjustment):.0%}")
            else:
                reasons.append(f"Risk surcharge of {(tier_adjustment-1):.0%}")
        
        if volume_discount > 0:
            reasons.append(f"Volume discount of {volume_discount:.0%} applied")
        
        reasons.append(f"Final rate positioned as {market_position} in market")
        
        return reasons
