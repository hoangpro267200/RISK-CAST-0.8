"""
RISKCAST Insurance Quote Generation Service
===========================================
Generates insurance quotes (classical and parametric) based on risk assessments.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from app.models.insurance import (
    InsuranceProduct, InsuranceQuote, PremiumBreakdown, CoverageDetails,
    PricingBreakdown, ParametricTrigger, PayoutStructure, Carrier
)
from app.services.parametric_engine import (
    ParametricPricingEngine, ParametricQuote
)
from app.services.insurance_premium_calculator import InsurancePremiumCalculator

logger = logging.getLogger(__name__)


class InsuranceQuoteService:
    """
    Service for generating insurance quotes.
    """
    
    # Product catalog (simplified - should be in database)
    PRODUCT_CATALOG = {
        "marine_cargo_icc_a": {
            "product_id": "marine_cargo_icc_a",
            "name": "Marine Cargo Insurance (ICC A)",
            "category": "classical",
            "tier": "A",
            "status": "transactional",
            "description": "Comprehensive marine cargo insurance covering all risks",
            "coverage_type": "ICC_A",
            "carrier": "allianz",
            "base_rate": 0.008,  # 0.8% of cargo value
            "pricing_model": "classical",
            "requires_kyc": True,
        },
        "port_delay_parametric": {
            "product_id": "port_delay_parametric",
            "name": "Port Delay Parametric Insurance",
            "category": "parametric",
            "tier": "B",
            "status": "api_parametric",
            "description": "Parametric insurance for port congestion delays",
            "pricing_model": "parametric",
            "carrier": "riskcast",
            "requires_kyc": True,
        },
        "weather_delay_parametric": {
            "product_id": "weather_delay_parametric",
            "name": "Weather Delay Parametric Insurance",
            "category": "parametric",
            "tier": "B",
            "status": "api_parametric",
            "description": "Parametric insurance for weather-related delays",
            "pricing_model": "parametric",
            "carrier": "riskcast",
            "requires_kyc": True,
        },
    }
    
    @staticmethod
    def generate_quotes(
        risk_assessment: Dict[str, Any],
        shipment_data: Dict[str, Any]
    ) -> List[InsuranceQuote]:
        """
        Generate insurance quotes based on risk assessment.
        
        Args:
            risk_assessment: RISKCAST risk assessment result
            shipment_data: Shipment data
            
        Returns:
            List of insurance quotes
        """
        quotes = []
        
        # Extract key data
        risk_score = risk_assessment.get("risk_score", {}).get("overallScore", 50)
        cargo_value = shipment_data.get("cargo", {}).get("value_usd", 100000)
        transport_mode = shipment_data.get("transport", {}).get("mode", "ocean")
        route = shipment_data.get("route", {})
        
        # Risk factors
        risk_factors = risk_assessment.get("layers", [])
        port_congestion_score = next(
            (layer.get("score", 0) for layer in risk_factors 
             if "port" in layer.get("name", "").lower() or "congestion" in layer.get("name", "").lower()),
            0
        )
        weather_score = next(
            (layer.get("score", 0) for layer in risk_factors 
             if "weather" in layer.get("name", "").lower() or "climate" in layer.get("name", "").lower()),
            0
        )
        
        # 1. Classical Marine Cargo Insurance
        if cargo_value >= 50000:  # Minimum threshold
            classical_quote = InsuranceQuoteService._generate_classical_quote(
                risk_score=risk_score,
                cargo_value=cargo_value,
                transport_mode=transport_mode,
                shipment_data=shipment_data
            )
            if classical_quote:
                quotes.append(classical_quote)
        
        # 2. Port Congestion Parametric (if high port congestion risk)
        if port_congestion_score > 60:
            parametric_quote = InsuranceQuoteService._generate_port_congestion_parametric(
                risk_score=risk_score,
                cargo_value=cargo_value,
                route=route,
                port_congestion_score=port_congestion_score
            )
            if parametric_quote:
                quotes.append(parametric_quote)
        
        # 3. Weather Delay Parametric (if high weather risk)
        if weather_score > 50:
            weather_quote = InsuranceQuoteService._generate_weather_parametric(
                risk_score=risk_score,
                cargo_value=cargo_value,
                route=route,
                weather_score=weather_score
            )
            if weather_quote:
                quotes.append(weather_quote)
        
        return quotes
    
    @staticmethod
    def _generate_classical_quote(
        risk_score: float,
        cargo_value: float,
        transport_mode: str,
        shipment_data: Dict[str, Any]
    ) -> Optional[InsuranceQuote]:
        """Generate classical marine cargo insurance quote."""
        try:
            # Use existing premium calculator
            cargo_type = shipment_data.get("cargo", {}).get("type", "general")
            
            premium_result = InsurancePremiumCalculator.calculate_premium(
                cargo_value=cargo_value,
                transport_mode=transport_mode,
                risk_score=risk_score,
                cargo_type=cargo_type
            )
            
            # Build quote
            quote_id = f"QUOTE_{uuid4().hex[:12].upper()}"
            
            # Calculate coverage dates (default 90 days from now)
            effective_date = datetime.now()
            expiry_date = effective_date + timedelta(days=90)
            
            premium_breakdown = PremiumBreakdown(
                base_premium=premium_result.base_rate * cargo_value,
                risk_adjustment=premium_result.risk_multiplier * premium_result.base_rate * cargo_value - 
                               premium_result.base_rate * cargo_value,
                total_premium=premium_result.premium_usd,
                currency="USD"
            )
            
            coverage = CoverageDetails(
                sum_insured=cargo_value,
                deductible=premium_result.recommended_deductible_usd,
                coverage_type="ICC_A",
                territorial_scope="worldwide_excluding_excluded_countries",
                effective_date=effective_date,
                expiry_date=expiry_date
            )
            
            # Pricing breakdown
            expected_loss = cargo_value * (risk_score / 100) * 0.1  # Simplified
            pricing_breakdown = PricingBreakdown(
                expected_loss=expected_loss,
                load_factor=1.3,
                administrative_costs=premium_result.premium_usd * 0.15,
                risk_adjustments=[
                    {
                        "factor": "risk_score",
                        "score": risk_score,
                        "adjustment": f"{premium_result.risk_multiplier:.2%}",
                        "reasoning": f"Risk score {risk_score:.1f}/100"
                    }
                ]
            )
            
            quote = InsuranceQuote(
                quote_id=quote_id,
                product_id="marine_cargo_icc_a",
                premium=premium_breakdown,
                coverage=coverage,
                pricing_breakdown=pricing_breakdown,
                valid_until=datetime.now() + timedelta(days=7),
                carrier=Carrier.ALLIANZ
            )
            
            return quote
            
        except Exception as e:
            logger.error(f"Error generating classical quote: {e}")
            return None
    
    @staticmethod
    def _generate_port_congestion_parametric(
        risk_score: float,
        cargo_value: float,
        route: Dict[str, Any],
        port_congestion_score: float
    ) -> Optional[InsuranceQuote]:
        """Generate port congestion parametric quote."""
        try:
            # Build trigger
            destination_port = route.get("pod", "USLAX")
            
            trigger = ParametricTrigger(
                product_id="port_delay_parametric",
                trigger_type="port_congestion",
                location={"port_code": destination_port},
                metric="container_dwell_time",
                threshold=14.0,  # 14 days
                data_source="port_authority_api"
            )
            
            payout_structure = PayoutStructure(
                type="per_day_excess",
                payout_per_unit=1000.0,  # $1000/day
                maximum_days=30,
                franchise_deductible=3.0  # 3 days
            )
            trigger.payout_structure = payout_structure
            
            # Mock historical data (in production, fetch from database/API)
            historical_data = [
                {"dwell_days": d} for d in [8, 10, 12, 15, 18, 20, 22, 25, 8, 10]
            ]
            
            # Price parametric product
            parametric_quote = ParametricPricingEngine.price_port_congestion_parametric(
                trigger=trigger,
                historical_data=historical_data,
                cargo_value=cargo_value
            )
            
            # Build InsuranceQuote
            quote_id = f"QUOTE_{uuid4().hex[:12].upper()}"
            
            effective_date = datetime.now()
            expiry_date = effective_date + timedelta(days=90)
            
            premium_breakdown = PremiumBreakdown(
                base_premium=parametric_quote.premium,
                risk_adjustment=0.0,  # Parametric doesn't have risk adjustment
                total_premium=parametric_quote.premium,
                currency="USD"
            )
            
            coverage = CoverageDetails(
                sum_insured=cargo_value,
                deductible=0.0,  # Parametric doesn't have traditional deductible
                coverage_type="parametric_port_delay",
                territorial_scope=f"Port {destination_port}",
                effective_date=effective_date,
                expiry_date=expiry_date
            )
            
            pricing_breakdown = PricingBreakdown(
                expected_loss=parametric_quote.expected_payout,
                load_factor=1.2,
                administrative_costs=parametric_quote.premium * 0.18,
                risk_adjustments=[]
            )
            
            quote = InsuranceQuote(
                quote_id=quote_id,
                product_id="port_delay_parametric",
                premium=premium_breakdown,
                coverage=coverage,
                trigger=trigger,
                payout_structure=payout_structure,
                expected_payout=parametric_quote.expected_payout,
                trigger_probability=parametric_quote.trigger_probability,
                basis_risk_score=parametric_quote.basis_risk_score,
                pricing_breakdown=pricing_breakdown,
                valid_until=datetime.now() + timedelta(days=7),
                carrier=Carrier.RISKCAST
            )
            
            return quote
            
        except Exception as e:
            logger.error(f"Error generating port congestion parametric quote: {e}")
            return None
    
    @staticmethod
    def _generate_weather_parametric(
        risk_score: float,
        cargo_value: float,
        route: Dict[str, Any],
        weather_score: float
    ) -> Optional[InsuranceQuote]:
        """Generate weather delay parametric quote."""
        try:
            # Build trigger
            origin_port = route.get("pol", "CNSHA")
            
            trigger = ParametricTrigger(
                product_id="weather_delay_parametric",
                trigger_type="weather",
                location={"port_code": origin_port},
                metric="cumulative_rainfall_mm",
                threshold=150.0,  # 150mm (95th percentile)
                data_source="tomorrow_io"
            )
            
            payout_structure = PayoutStructure(
                type="per_mm_excess",
                payout_per_unit=50.0,  # $50/mm
                minimum_payout=500.0,
                maximum_payout=10000.0
            )
            trigger.payout_structure = payout_structure
            
            # Mock historical data
            historical_data = [
                {"rainfall_mm": r} for r in [50, 80, 120, 140, 160, 180, 200, 100, 90, 110]
            ]
            
            # Price parametric product
            parametric_quote = ParametricPricingEngine.price_rainfall_parametric(
                trigger=trigger,
                historical_data=historical_data,
                cargo_value=cargo_value
            )
            
            # Build InsuranceQuote
            quote_id = f"QUOTE_{uuid4().hex[:12].upper()}"
            
            effective_date = datetime.now()
            expiry_date = effective_date + timedelta(days=30)  # Shorter for weather
            
            premium_breakdown = PremiumBreakdown(
                base_premium=parametric_quote.premium,
                risk_adjustment=0.0,
                total_premium=parametric_quote.premium,
                currency="USD"
            )
            
            coverage = CoverageDetails(
                sum_insured=cargo_value,
                deductible=0.0,
                coverage_type="parametric_weather_delay",
                territorial_scope=f"Port {origin_port}",
                effective_date=effective_date,
                expiry_date=expiry_date
            )
            
            pricing_breakdown = PricingBreakdown(
                expected_loss=parametric_quote.expected_payout,
                load_factor=1.3,
                administrative_costs=parametric_quote.premium * 0.20,
                risk_adjustments=[]
            )
            
            quote = InsuranceQuote(
                quote_id=quote_id,
                product_id="weather_delay_parametric",
                premium=premium_breakdown,
                coverage=coverage,
                trigger=trigger,
                payout_structure=payout_structure,
                expected_payout=parametric_quote.expected_payout,
                trigger_probability=parametric_quote.trigger_probability,
                basis_risk_score=parametric_quote.basis_risk_score,
                pricing_breakdown=pricing_breakdown,
                valid_until=datetime.now() + timedelta(days=7),
                carrier=Carrier.RISKCAST
            )
            
            return quote
            
        except Exception as e:
            logger.error(f"Error generating weather parametric quote: {e}")
            return None
    
    @staticmethod
    def compare_quotes(quotes: List[InsuranceQuote]) -> Dict[str, Any]:
        """
        Compare multiple quotes and provide recommendations.
        
        Args:
            quotes: List of insurance quotes
            
        Returns:
            Comparison analysis
        """
        if not quotes:
            return {"error": "No quotes to compare"}
        
        # Find best by different metrics
        best_price = min(quotes, key=lambda q: q.premium.total_premium)
        best_coverage = max(quotes, key=lambda q: q.coverage.sum_insured if q.coverage else 0)
        
        # Calculate average
        avg_premium = sum(q.premium.total_premium for q in quotes) / len(quotes)
        
        return {
            "quotes": [q.to_dict() for q in quotes],
            "comparison": {
                "best_price": {
                    "quote_id": best_price.quote_id,
                    "premium": best_price.premium.total_premium
                },
                "best_coverage": {
                    "quote_id": best_coverage.quote_id,
                    "sum_insured": best_coverage.coverage.sum_insured if best_coverage.coverage else 0
                },
                "average_premium": avg_premium
            },
            "recommendation": InsuranceQuoteService._generate_recommendation(quotes)
        }
    
    @staticmethod
    def _generate_recommendation(quotes: List[InsuranceQuote]) -> str:
        """Generate AI recommendation for quote selection."""
        # Simple logic - in production, use AI advisor
        parametric_quotes = [q for q in quotes if q.product_id.endswith("_parametric")]
        classical_quotes = [q for q in quotes if not q.product_id.endswith("_parametric")]
        
        if parametric_quotes and classical_quotes:
            return "Consider parametric products for faster payout (48hr vs 30-90 days) if delay risk is your primary concern."
        elif parametric_quotes:
            return "Parametric insurance offers fast, automatic payouts. Best for delay-related risks."
        elif classical_quotes:
            return "Classical cargo insurance provides comprehensive coverage for physical damage and theft."
        else:
            return "No specific recommendation available."
