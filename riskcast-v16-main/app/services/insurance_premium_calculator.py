"""
RISKCAST Insurance Premium Calculator
=======================================
Calculate insurance premium adjustments based on RISKCAST risk scores.

Aligns with actuarial principles and industry standards:
- Risk class determination
- Premium rate calculation
- Deductible recommendations
- Portfolio-level analysis

Author: RISKCAST Team
Version: 2.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskClass(Enum):
    """Insurance risk classification."""
    CLASS_A = "class_a"  # Excellent: 40% discount
    CLASS_B = "class_b"  # Good: 20% discount
    CLASS_C = "class_c"  # Standard: base rate
    CLASS_D = "class_d"  # Elevated: 50% surcharge
    CLASS_E = "class_e"  # High: 150% surcharge
    
    @property
    def description(self) -> str:
        descriptions = {
            "class_a": "Excellent Risk - Low probability of claim",
            "class_b": "Good Risk - Below average probability",
            "class_c": "Standard Risk - Average probability",
            "class_d": "Elevated Risk - Above average probability",
            "class_e": "High Risk - Significant claim probability"
        }
        return descriptions.get(self.value, "Unknown")
    
    @property
    def multiplier(self) -> float:
        multipliers = {
            "class_a": 0.6,   # 40% discount
            "class_b": 0.8,   # 20% discount
            "class_c": 1.0,   # Base rate
            "class_d": 1.5,   # 50% surcharge
            "class_e": 2.5    # 150% surcharge
        }
        return multipliers.get(self.value, 1.0)


@dataclass
class PremiumResult:
    """Insurance premium calculation result."""
    premium_usd: float
    premium_rate: float
    base_rate: float
    risk_class: str
    risk_class_description: str
    risk_multiplier: float
    additional_multiplier: float
    recommended_deductible_usd: float
    coverage_details: Dict
    comparison_to_baseline: Dict
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass 
class PortfolioPremiumResult:
    """Portfolio premium calculation result."""
    total_premium_before_discount: float
    portfolio_discount_pct: float
    total_premium_after_discount: float
    savings_from_discount: float
    shipment_count: int
    average_premium_per_shipment: float
    risk_distribution: Dict
    recommendations: List[str]
    individual_shipments: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            'total_premium_before_discount': self.total_premium_before_discount,
            'portfolio_discount_pct': self.portfolio_discount_pct,
            'total_premium_after_discount': self.total_premium_after_discount,
            'savings_from_discount': self.savings_from_discount,
            'shipment_count': self.shipment_count,
            'average_premium_per_shipment': self.average_premium_per_shipment,
            'risk_distribution': self.risk_distribution,
            'recommendations': self.recommendations,
            'individual_shipments': self.individual_shipments
        }


class InsurancePremiumCalculator:
    """
    Calculate insurance premium adjustments based on RISKCAST scores.
    Aligns with actuarial principles.
    """
    
    # Industry baseline rates (% of cargo value)
    BASELINE_RATES = {
        'ocean': 0.008,    # 0.8% - Higher risk (longer transit, more variables)
        'air': 0.003,      # 0.3% - Lower risk (faster, controlled)
        'rail': 0.005,     # 0.5% - Medium risk
        'road': 0.006,     # 0.6% - Medium-high risk (accidents, theft)
        'multimodal': 0.007,  # 0.7% - Combined risks
        'default': 0.006   # Default rate if mode unknown
    }
    
    # Risk class boundaries (based on risk score)
    RISK_CLASS_BOUNDARIES = {
        RiskClass.CLASS_A: (0, 30),
        RiskClass.CLASS_B: (30, 50),
        RiskClass.CLASS_C: (50, 70),
        RiskClass.CLASS_D: (70, 85),
        RiskClass.CLASS_E: (85, 100)
    }
    
    # Cargo type risk adjustments
    CARGO_ADJUSTMENTS = {
        'general': 1.0,
        'electronics': 1.15,      # Higher theft risk
        'pharmaceuticals': 1.20,  # Temperature sensitive
        'perishables': 1.25,      # Time and temperature sensitive
        'hazmat': 1.40,           # Special handling requirements
        'machinery': 1.10,        # Damage risk
        'textiles': 0.90,         # Lower risk
        'raw_materials': 0.85     # Bulk, lower value density
    }
    
    @staticmethod
    def calculate_premium(
        cargo_value: float,
        transport_mode: str,
        risk_score: float,
        cargo_type: str = 'general',
        additional_factors: Dict = None
    ) -> PremiumResult:
        """
        Calculate insurance premium based on RISKCAST risk score.
        
        Args:
            cargo_value: Value of cargo in USD
            transport_mode: Mode of transport (ocean, air, rail, road, multimodal)
            risk_score: RISKCAST risk score (0-100)
            cargo_type: Type of cargo for adjustment
            additional_factors: Additional risk factors (hazmat, high_value, peak_season, etc.)
            
        Returns:
            PremiumResult with detailed breakdown
        """
        additional_factors = additional_factors or {}
        
        # Get base rate for transport mode
        base_rate = InsurancePremiumCalculator.BASELINE_RATES.get(
            transport_mode.lower(),
            InsurancePremiumCalculator.BASELINE_RATES['default']
        )
        
        # Determine risk class from score
        risk_class = InsurancePremiumCalculator._determine_risk_class(risk_score)
        risk_multiplier = risk_class.multiplier
        
        # Calculate additional multipliers
        additional_multiplier = InsurancePremiumCalculator._calculate_additional_multiplier(
            cargo_value=cargo_value,
            cargo_type=cargo_type,
            additional_factors=additional_factors
        )
        
        # Calculate final rate and premium
        final_rate = base_rate * risk_multiplier * additional_multiplier
        premium = cargo_value * final_rate
        
        # Calculate baseline premium (without risk adjustment)
        baseline_premium = cargo_value * base_rate
        
        # Recommend deductible
        deductible = InsurancePremiumCalculator._recommend_deductible(cargo_value, risk_score)
        
        # Generate recommendations
        recommendations = InsurancePremiumCalculator._generate_recommendations(
            risk_score=risk_score,
            risk_class=risk_class,
            cargo_value=cargo_value,
            additional_factors=additional_factors
        )
        
        return PremiumResult(
            premium_usd=round(premium, 2),
            premium_rate=round(final_rate, 6),
            base_rate=base_rate,
            risk_class=risk_class.value,
            risk_class_description=risk_class.description,
            risk_multiplier=risk_multiplier,
            additional_multiplier=round(additional_multiplier, 4),
            recommended_deductible_usd=deductible,
            coverage_details={
                'cargo_value': cargo_value,
                'transport_mode': transport_mode,
                'cargo_type': cargo_type,
                'risk_score': risk_score
            },
            comparison_to_baseline={
                'baseline_premium': round(baseline_premium, 2),
                'adjustment_amount': round(premium - baseline_premium, 2),
                'adjustment_pct': round((final_rate - base_rate) / base_rate * 100, 1)
            },
            recommendations=recommendations
        )
    
    @staticmethod
    def _determine_risk_class(risk_score: float) -> RiskClass:
        """Map risk score to insurance risk class."""
        for risk_class, (min_score, max_score) in InsurancePremiumCalculator.RISK_CLASS_BOUNDARIES.items():
            if min_score <= risk_score < max_score:
                return risk_class
        return RiskClass.CLASS_E  # Default to highest risk if score >= 100
    
    @staticmethod
    def _calculate_additional_multiplier(
        cargo_value: float,
        cargo_type: str,
        additional_factors: Dict
    ) -> float:
        """Calculate additional premium adjustments."""
        multiplier = 1.0
        
        # Cargo type adjustment
        cargo_adj = InsurancePremiumCalculator.CARGO_ADJUSTMENTS.get(
            cargo_type.lower(),
            1.0
        )
        multiplier *= cargo_adj
        
        # High-value cargo surcharge (over $500k)
        if cargo_value > 500000:
            multiplier *= 1.10
        elif cargo_value > 1000000:
            multiplier *= 1.15
        
        # Hazmat surcharge
        if additional_factors.get('hazmat'):
            multiplier *= 1.30
        
        # Refrigerated/temperature controlled
        if additional_factors.get('temperature_controlled'):
            multiplier *= 1.15
        
        # Multi-modal complexity discount (already priced into multimodal base rate)
        # But if explicitly flagged as simple single-mode, small discount
        if additional_factors.get('single_mode_direct'):
            multiplier *= 0.95
        
        # Peak season adjustment
        if additional_factors.get('peak_season'):
            multiplier *= 1.05
        
        # Known good shipper discount
        if additional_factors.get('preferred_shipper'):
            multiplier *= 0.90
        
        # New route surcharge (no historical data)
        if additional_factors.get('new_route'):
            multiplier *= 1.10
        
        # Claims history adjustment
        claims_history = additional_factors.get('claims_history_factor', 1.0)
        multiplier *= claims_history
        
        return multiplier
    
    @staticmethod
    def _recommend_deductible(cargo_value: float, risk_score: float) -> float:
        """
        Recommend appropriate deductible based on cargo value and risk.
        
        Lower risk = can accept higher deductible for lower premium
        Higher risk = recommend lower deductible for protection
        """
        # Base deductible percentage
        if risk_score < 30:
            # Low risk: recommend higher deductible for premium savings
            deductible_pct = 0.05  # 5%
        elif risk_score < 50:
            deductible_pct = 0.04  # 4%
        elif risk_score < 70:
            deductible_pct = 0.03  # 3%
        else:
            # High risk: recommend lower deductible
            deductible_pct = 0.02  # 2%
        
        # Calculate deductible
        deductible = cargo_value * deductible_pct
        
        # Apply min/max bounds
        min_deductible = 500
        max_deductible = 50000
        
        deductible = max(min_deductible, min(deductible, max_deductible))
        
        return round(deductible, 2)
    
    @staticmethod
    def _generate_recommendations(
        risk_score: float,
        risk_class: RiskClass,
        cargo_value: float,
        additional_factors: Dict
    ) -> List[str]:
        """Generate actionable recommendations based on risk assessment."""
        recommendations = []
        
        # Risk class specific recommendations
        if risk_class == RiskClass.CLASS_A:
            recommendations.append(
                "Consider higher deductible options for additional premium savings"
            )
            recommendations.append(
                "Eligible for preferred shipper discount programs"
            )
        elif risk_class == RiskClass.CLASS_B:
            recommendations.append(
                "Good risk profile - maintain current risk management practices"
            )
        elif risk_class == RiskClass.CLASS_C:
            recommendations.append(
                "Review route alternatives for potential premium reduction"
            )
            recommendations.append(
                "Consider enhanced packaging to reduce damage risk"
            )
        elif risk_class == RiskClass.CLASS_D:
            recommendations.append(
                "HIGH PRIORITY: Implement risk mitigation measures before shipping"
            )
            recommendations.append(
                "Consider alternative carriers with better track records"
            )
            recommendations.append(
                "Split shipments to reduce concentration risk"
            )
        elif risk_class == RiskClass.CLASS_E:
            recommendations.append(
                "CRITICAL: Risk score requires manual underwriter review"
            )
            recommendations.append(
                "Strongly recommend postponing shipment until risk factors are addressed"
            )
            recommendations.append(
                "Contact insurance advisor for specialized high-risk coverage options"
            )
        
        # Value-based recommendations
        if cargo_value > 1000000:
            recommendations.append(
                "High-value cargo: Consider multi-carrier coverage for excess exposure"
            )
        
        # Additional factor recommendations
        if additional_factors.get('peak_season'):
            recommendations.append(
                "Peak season: Build in additional transit time buffers"
            )
        
        if additional_factors.get('new_route'):
            recommendations.append(
                "New route: Request pilot shipment monitoring for first 3 shipments"
            )
        
        return recommendations
    
    @staticmethod
    def calculate_portfolio_premium(
        shipments: List[Dict]
    ) -> PortfolioPremiumResult:
        """
        Calculate total premium for a portfolio of shipments.
        Includes portfolio diversification discount.
        
        Args:
            shipments: List of shipment dictionaries with:
                - cargo_value: float
                - transport_mode: str
                - risk_score: float
                - cargo_type: str (optional)
                - additional_factors: Dict (optional)
                
        Returns:
            PortfolioPremiumResult with portfolio analysis
        """
        if not shipments:
            raise ValueError("Shipments list cannot be empty")
        
        total_premium = 0
        shipment_premiums = []
        risk_distribution = {rc.value: 0 for rc in RiskClass}
        
        for idx, shipment in enumerate(shipments):
            result = InsurancePremiumCalculator.calculate_premium(
                cargo_value=shipment['cargo_value'],
                transport_mode=shipment['transport_mode'],
                risk_score=shipment['risk_score'],
                cargo_type=shipment.get('cargo_type', 'general'),
                additional_factors=shipment.get('additional_factors')
            )
            
            total_premium += result.premium_usd
            risk_distribution[result.risk_class] += 1
            
            shipment_premiums.append({
                'shipment_id': shipment.get('shipment_id', f'shipment_{idx + 1}'),
                **result.to_dict()
            })
        
        # Calculate portfolio discount based on size and diversification
        portfolio_size = len(shipments)
        diversification_score = InsurancePremiumCalculator._calculate_diversification(
            risk_distribution,
            portfolio_size
        )
        
        # Portfolio discount: volume + diversification
        if portfolio_size >= 100:
            volume_discount = 0.15
        elif portfolio_size >= 50:
            volume_discount = 0.10
        elif portfolio_size >= 20:
            volume_discount = 0.05
        elif portfolio_size >= 10:
            volume_discount = 0.03
        else:
            volume_discount = 0.0
        
        # Additional discount for well-diversified portfolios
        diversification_discount = min(0.05, diversification_score * 0.10)
        
        total_discount = volume_discount + diversification_discount
        discounted_premium = total_premium * (1 - total_discount)
        
        # Portfolio recommendations
        recommendations = InsurancePremiumCalculator._generate_portfolio_recommendations(
            risk_distribution=risk_distribution,
            portfolio_size=portfolio_size,
            total_premium=total_premium
        )
        
        return PortfolioPremiumResult(
            total_premium_before_discount=round(total_premium, 2),
            portfolio_discount_pct=round(total_discount * 100, 1),
            total_premium_after_discount=round(discounted_premium, 2),
            savings_from_discount=round(total_premium - discounted_premium, 2),
            shipment_count=portfolio_size,
            average_premium_per_shipment=round(discounted_premium / portfolio_size, 2),
            risk_distribution={
                k: {
                    'count': v,
                    'percentage': round(v / portfolio_size * 100, 1)
                }
                for k, v in risk_distribution.items() if v > 0
            },
            recommendations=recommendations,
            individual_shipments=shipment_premiums
        )
    
    @staticmethod
    def _calculate_diversification(risk_distribution: Dict, portfolio_size: int) -> float:
        """
        Calculate portfolio diversification score.
        Higher score = better diversified (more classes represented).
        """
        if portfolio_size == 0:
            return 0.0
        
        # Count non-empty classes
        classes_with_shipments = sum(1 for count in risk_distribution.values() if count > 0)
        
        # Calculate concentration (Herfindahl index)
        concentration = sum(
            (count / portfolio_size) ** 2 
            for count in risk_distribution.values() if count > 0
        )
        
        # Diversification is inverse of concentration
        diversification = 1 - concentration
        
        return diversification
    
    @staticmethod
    def _generate_portfolio_recommendations(
        risk_distribution: Dict,
        portfolio_size: int,
        total_premium: float
    ) -> List[str]:
        """Generate portfolio-level recommendations."""
        recommendations = []
        
        # Check for concentration in high-risk classes
        high_risk_count = risk_distribution.get('class_d', 0) + risk_distribution.get('class_e', 0)
        high_risk_pct = high_risk_count / portfolio_size * 100 if portfolio_size > 0 else 0
        
        if high_risk_pct > 30:
            recommendations.append(
                f"ALERT: {high_risk_pct:.0f}% of portfolio in elevated/high risk classes. Review risk mitigation strategies."
            )
        
        if high_risk_pct > 50:
            recommendations.append(
                "CRITICAL: Portfolio concentration in high-risk shipments may trigger reinsurance requirements"
            )
        
        # Volume recommendations
        if portfolio_size < 20:
            recommendations.append(
                "Consider consolidating more shipments to qualify for volume discounts"
            )
        elif portfolio_size >= 50:
            recommendations.append(
                "Eligible for enterprise pricing. Contact account manager for custom rates."
            )
        
        # Premium optimization
        if total_premium > 100000:
            recommendations.append(
                "High premium volume: Consider annual policy vs. per-shipment coverage"
            )
        
        return recommendations
    
    @staticmethod
    def estimate_savings_with_riskcast(
        current_premium: float,
        current_risk_score: float,
        projected_risk_score: float,
        cargo_value: float,
        transport_mode: str
    ) -> Dict:
        """
        Estimate premium savings if RISKCAST helps reduce risk score.
        
        Useful for ROI discussions with prospects.
        """
        # Calculate current premium (using current risk score)
        current_result = InsurancePremiumCalculator.calculate_premium(
            cargo_value=cargo_value,
            transport_mode=transport_mode,
            risk_score=current_risk_score
        )
        
        # Calculate projected premium (with improved risk score)
        projected_result = InsurancePremiumCalculator.calculate_premium(
            cargo_value=cargo_value,
            transport_mode=transport_mode,
            risk_score=projected_risk_score
        )
        
        savings = current_result.premium_usd - projected_result.premium_usd
        savings_pct = (savings / current_result.premium_usd * 100) if current_result.premium_usd > 0 else 0
        
        return {
            'current_premium': current_result.premium_usd,
            'current_risk_class': current_result.risk_class,
            'projected_premium': projected_result.premium_usd,
            'projected_risk_class': projected_result.risk_class,
            'estimated_savings': round(savings, 2),
            'savings_percentage': round(savings_pct, 1),
            'risk_score_improvement': current_risk_score - projected_risk_score,
            'recommendation': (
                f"Reducing risk score from {current_risk_score} to {projected_risk_score} "
                f"could save ${savings:,.2f} ({savings_pct:.1f}%) per shipment"
            )
        }


# Convenience functions
def calculate_premium(
    cargo_value: float,
    transport_mode: str,
    risk_score: float,
    **kwargs
) -> Dict:
    """Calculate insurance premium."""
    result = InsurancePremiumCalculator.calculate_premium(
        cargo_value=cargo_value,
        transport_mode=transport_mode,
        risk_score=risk_score,
        **kwargs
    )
    return result.to_dict()


def calculate_portfolio_premium(shipments: List[Dict]) -> Dict:
    """Calculate portfolio premium."""
    result = InsurancePremiumCalculator.calculate_portfolio_premium(shipments)
    return result.to_dict()


def estimate_savings(
    current_risk_score: float,
    projected_risk_score: float,
    cargo_value: float,
    transport_mode: str
) -> Dict:
    """Estimate savings from risk score improvement."""
    return InsurancePremiumCalculator.estimate_savings_with_riskcast(
        current_premium=0,  # Not used directly
        current_risk_score=current_risk_score,
        projected_risk_score=projected_risk_score,
        cargo_value=cargo_value,
        transport_mode=transport_mode
    )
