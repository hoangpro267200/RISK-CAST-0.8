"""
RISKCAST Parametric Insurance Engine
====================================
Core engine for parametric insurance products:
- Trigger evaluation
- Payout calculation
- Pricing
- Basis risk assessment
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import math
import logging

from app.models.insurance import (
    ParametricTrigger, PayoutStructure, InsuranceQuote, 
    PremiumBreakdown, PricingBreakdown
)

logger = logging.getLogger(__name__)


class TriggerType(str, Enum):
    WEATHER_RAINFALL = "weather_rainfall"
    PORT_CONGESTION = "port_congestion"
    NATCAT_CYCLONE = "natcat_cyclone"
    STRIKE = "strike"
    ROUTING = "routing"


@dataclass
class TriggerEvaluation:
    """Result of trigger evaluation."""
    triggered: bool
    payout_amount: float = 0.0
    trigger_evidence: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    escalate_to_manual: bool = False


@dataclass
class ParametricQuote:
    """Parametric insurance quote."""
    premium: float
    expected_payout: float
    trigger_probability: float  # 0-1
    burn_rate: float  # Historical trigger frequency
    loss_ratio: float  # expected_payout / premium
    confidence_interval: Dict[str, float]  # p10, p50, p90
    basis_risk_score: float  # 0-1 (lower = better)


class ParametricPricingEngine:
    """
    Pricing engine for parametric insurance products.
    """
    
    @staticmethod
    def price_rainfall_parametric(
        trigger: ParametricTrigger,
        historical_data: List[Dict[str, Any]],
        cargo_value: float
    ) -> ParametricQuote:
        """
        Price rainfall-based parametric insurance.
        
        Args:
            trigger: Rainfall trigger definition
            historical_data: Historical weather data
            cargo_value: Cargo value for context
            
        Returns:
            ParametricQuote with pricing details
        """
        # Calculate historical trigger frequency (burn rate)
        trigger_events = [
            d for d in historical_data 
            if d.get("rainfall_mm", 0) > trigger.threshold
        ]
        burn_rate = len(trigger_events) / len(historical_data) if historical_data else 0.0
        
        # Calculate average excess rainfall
        if trigger_events:
            avg_excess = sum(
                d["rainfall_mm"] - trigger.threshold 
                for d in trigger_events
            ) / len(trigger_events)
        else:
            avg_excess = 0.0
        
        # Calculate expected payout
        payout_per_mm = trigger.payout_structure.payout_per_unit if trigger.payout_structure else 50.0
        expected_payout = burn_rate * (avg_excess * payout_per_mm)
        
        # Apply load factor (covers overhead, profit, capital cost)
        load_factor = 1.3
        premium = expected_payout * load_factor
        
        # Risk margins for volatility
        volatility_adjustment = ParametricPricingEngine._calculate_volatility_margin(trigger_events)
        final_premium = premium * (1 + volatility_adjustment)
        
        # Calculate loss ratio
        loss_ratio = expected_payout / final_premium if final_premium > 0 else 0.0
        
        # Confidence intervals (simplified)
        confidence_interval = {
            "p10": burn_rate * 0.5,
            "p50": burn_rate,
            "p90": burn_rate * 2.0
        }
        
        return ParametricQuote(
            premium=final_premium,
            expected_payout=expected_payout,
            trigger_probability=burn_rate,
            burn_rate=burn_rate,
            loss_ratio=loss_ratio,
            confidence_interval=confidence_interval,
            basis_risk_score=0.15  # Default, should be calculated based on correlation
        )
    
    @staticmethod
    def price_port_congestion_parametric(
        trigger: ParametricTrigger,
        historical_data: List[Dict[str, Any]],
        cargo_value: float
    ) -> ParametricQuote:
        """
        Price port congestion parametric insurance.
        
        Args:
            trigger: Port congestion trigger definition
            historical_data: Historical port congestion data
            cargo_value: Cargo value for context
            
        Returns:
            ParametricQuote with pricing details
        """
        # Analyze historical dwell times
        dwell_times = [d.get("dwell_days", 0) for d in historical_data]
        threshold_days = trigger.threshold
        
        # Calculate exceedance probability
        exceedances = [d for d in dwell_times if d > threshold_days]
        exceedance_probability = len(exceedances) / len(dwell_times) if dwell_times else 0.0
        
        # Calculate average excess days
        if exceedances:
            max_days = trigger.payout_structure.maximum_days if trigger.payout_structure else 30
            avg_excess_days = sum(
                min(d - threshold_days, max_days) 
                for d in exceedances
            ) / len(exceedances)
        else:
            avg_excess_days = 0.0
        
        # Expected payout
        payout_per_day = trigger.payout_structure.payout_per_unit if trigger.payout_structure else 1000.0
        expected_payout = exceedance_probability * avg_excess_days * payout_per_day
        
        # Load factor (lower than weather due to better data quality)
        load_factor = 1.2
        premium = expected_payout * load_factor
        
        # Loss ratio
        loss_ratio = expected_payout / premium if premium > 0 else 0.0
        
        # Confidence intervals
        confidence_interval = {
            "p10": exceedance_probability * 0.7,
            "p50": exceedance_probability,
            "p90": exceedance_probability * 1.5
        }
        
        return ParametricQuote(
            premium=premium,
            expected_payout=expected_payout,
            trigger_probability=exceedance_probability,
            burn_rate=exceedance_probability,
            loss_ratio=loss_ratio,
            confidence_interval=confidence_interval,
            basis_risk_score=0.10  # Lower basis risk for port congestion (better data)
        )
    
    @staticmethod
    def price_cyclone_parametric(
        trigger: ParametricTrigger,
        cat_model_output: Dict[str, Any],
        cargo_value: float
    ) -> ParametricQuote:
        """
        Price tropical cyclone parametric insurance using catastrophe model.
        
        Args:
            trigger: Cyclone trigger definition
            cat_model_output: Catastrophe model output
            cargo_value: Cargo value for context
            
        Returns:
            ParametricQuote with pricing details
        """
        # Get annual exceedance probability from cat model
        annual_probability = cat_model_output.get("annual_exceedance_probability", 0.0)
        
        # Adjust for exposure period
        if trigger.observation_period:
            days_in_period = trigger.observation_period.get("duration_days", 30)
            period_probability = 1 - math.pow(1 - annual_probability, days_in_period / 365)
        else:
            period_probability = annual_probability
        
        # Expected loss
        payout_amount = trigger.payout_structure.maximum_payout if trigger.payout_structure else 25000.0
        expected_loss = period_probability * payout_amount
        
        # Load factor (higher for cat risk due to tail risk)
        load_factor = 1.5
        premium = expected_loss * load_factor
        
        # Model uncertainty margin
        model_uncertainty = 0.3
        final_premium = premium * (1 + model_uncertainty * 0.5)
        
        # Loss ratio
        loss_ratio = expected_loss / final_premium if final_premium > 0 else 0.0
        
        # Confidence intervals from cat model
        confidence_interval = cat_model_output.get("confidence_interval", {
            "p10": period_probability * 0.4,
            "p50": period_probability,
            "p90": period_probability * 1.8
        })
        
        return ParametricQuote(
            premium=final_premium,
            expected_payout=expected_loss,
            trigger_probability=period_probability,
            burn_rate=period_probability,
            loss_ratio=loss_ratio,
            confidence_interval=confidence_interval,
            basis_risk_score=0.20  # Higher basis risk for cat events
        )
    
    @staticmethod
    def _calculate_volatility_margin(trigger_events: List[Dict[str, Any]]) -> float:
        """Calculate volatility adjustment based on historical variance."""
        if len(trigger_events) < 2:
            return 0.15  # Default 15% margin
        
        # Calculate coefficient of variation
        values = [d.get("rainfall_mm", 0) for d in trigger_events]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        if mean > 0:
            cv = std_dev / mean
            # Higher volatility = higher margin (capped at 30%)
            return min(cv * 0.1, 0.30)
        
        return 0.15


class ParametricTriggerEvaluator:
    """
    Evaluates parametric triggers based on real-time data.
    """
    
    @staticmethod
    def evaluate_rainfall_trigger(
        trigger: ParametricTrigger,
        current_data: Dict[str, Any]
    ) -> TriggerEvaluation:
        """
        Evaluate rainfall trigger.
        
        Args:
            trigger: Rainfall trigger definition
            current_data: Current weather data
            
        Returns:
            TriggerEvaluation result
        """
        current_rainfall = current_data.get("cumulative_rainfall_mm", 0)
        threshold = trigger.threshold
        
        if current_rainfall <= threshold:
            return TriggerEvaluation(
                triggered=False,
                reason=f"Rainfall {current_rainfall}mm below threshold {threshold}mm"
            )
        
        # Calculate payout
        excess = current_rainfall - threshold
        payout_per_mm = trigger.payout_structure.payout_per_unit if trigger.payout_structure else 50.0
        payout = excess * payout_per_mm
        
        # Apply limits
        if trigger.payout_structure:
            if trigger.payout_structure.minimum_payout:
                payout = max(payout, trigger.payout_structure.minimum_payout)
            if trigger.payout_structure.maximum_payout:
                payout = min(payout, trigger.payout_structure.maximum_payout)
        
        return TriggerEvaluation(
            triggered=True,
            payout_amount=payout,
            trigger_evidence={
                "cumulative_rainfall_mm": current_rainfall,
                "threshold_mm": threshold,
                "excess_mm": excess,
                "data_source": trigger.data_source,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def evaluate_port_congestion_trigger(
        trigger: ParametricTrigger,
        current_data: Dict[str, Any]
    ) -> TriggerEvaluation:
        """
        Evaluate port congestion trigger.
        
        Args:
            trigger: Port congestion trigger definition
            current_data: Current port congestion data
            
        Returns:
            TriggerEvaluation result
        """
        dwell_days = current_data.get("dwell_days", 0)
        threshold_days = trigger.threshold
        
        if dwell_days <= threshold_days:
            return TriggerEvaluation(
                triggered=False,
                reason=f"Dwell time {dwell_days} days below threshold {threshold_days} days"
            )
        
        # Check franchise deductible
        franchise = trigger.payout_structure.franchise_deductible if trigger.payout_structure else 0
        excess_days = dwell_days - threshold_days
        
        if excess_days < franchise:
            return TriggerEvaluation(
                triggered=False,
                reason=f"Excess {excess_days} days below franchise {franchise} days"
            )
        
        # Calculate payout
        payout_per_day = trigger.payout_structure.payout_per_unit if trigger.payout_structure else 1000.0
        payable_days = excess_days - franchise
        
        # Apply maximum days limit
        if trigger.payout_structure and trigger.payout_structure.maximum_days:
            payable_days = min(payable_days, trigger.payout_structure.maximum_days)
        
        payout = payable_days * payout_per_day
        
        # Apply maximum payout limit
        if trigger.payout_structure and trigger.payout_structure.maximum_payout:
            payout = min(payout, trigger.payout_structure.maximum_payout)
        
        return TriggerEvaluation(
            triggered=True,
            payout_amount=payout,
            trigger_evidence={
                "dwell_days": dwell_days,
                "threshold_days": threshold_days,
                "excess_days": excess_days,
                "payable_days": payable_days,
                "data_source": trigger.data_source,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def evaluate_cyclone_trigger(
        trigger: ParametricTrigger,
        cyclone_data: Dict[str, Any]
    ) -> TriggerEvaluation:
        """
        Evaluate tropical cyclone trigger.
        
        Args:
            trigger: Cyclone trigger definition
            cyclone_data: Current cyclone tracking data
            
        Returns:
            TriggerEvaluation result
        """
        # Check if cyclone entered coverage area
        coverage_center = trigger.location.get("coordinates", {})
        coverage_radius = trigger.location.get("radius_km", 100)
        
        track_points = cyclone_data.get("forecast_track", [])
        entered_area = False
        max_wind_in_area = 0
        
        for point in track_points:
            distance = ParametricTriggerEvaluator._calculate_distance(
                coverage_center,
                {"lat": point.get("lat"), "lon": point.get("lon")}
            )
            
            if distance <= coverage_radius:
                entered_area = True
                max_wind_in_area = max(max_wind_in_area, point.get("wind_kph", 0))
        
        if not entered_area:
            return TriggerEvaluation(
                triggered=False,
                reason="Cyclone did not enter coverage area"
            )
        
        # Check windspeed threshold
        threshold_kph = trigger.threshold
        if max_wind_in_area < threshold_kph:
            return TriggerEvaluation(
                triggered=False,
                reason=f"Max wind {max_wind_in_area} kph below threshold {threshold_kph} kph"
            )
        
        # Binary payout
        payout_amount = trigger.payout_structure.maximum_payout if trigger.payout_structure else 25000.0
        
        return TriggerEvaluation(
            triggered=True,
            payout_amount=payout_amount,
            trigger_evidence={
                "storm_id": cyclone_data.get("storm_id"),
                "max_wind_kph": max_wind_in_area,
                "threshold_kph": threshold_kph,
                "entered_coverage_area": True,
                "data_source": trigger.data_source,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def _calculate_distance(point1: Dict[str, float], point2: Dict[str, float]) -> float:
        """Calculate distance between two lat/lon points in km (Haversine formula)."""
        from math import radians, sin, cos, sqrt, atan2
        
        lat1, lon1 = radians(point1.get("lat", 0)), radians(point1.get("lon", 0))
        lat2, lon2 = radians(point2.get("lat", 0)), radians(point2.get("lon", 0))
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        R = 6371  # Earth radius in km
        return R * c


class BasisRiskCalculator:
    """
    Calculates basis risk (mismatch between trigger and actual loss).
    """
    
    @staticmethod
    def assess_basis_risk(
        trigger: ParametricTrigger,
        actual_loss_driver: str,
        historical_correlation: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Assess basis risk for a parametric trigger.
        
        Args:
            trigger: Parametric trigger definition
            actual_loss_driver: Primary actual loss driver
            historical_correlation: Historical correlation (0-1) if available
            
        Returns:
            Basis risk assessment
        """
        # Map loss drivers to correlation estimates
        correlation_map = {
            "port_operations_suspended_due_to_rain": 0.85,
            "road_flooding_prevents_truck_access": 0.65,
            "customs_delays": 0.1,
            "port_congestion_delay": 0.85,
            "carrier_delay": 0.4,
            "weather_damage": 0.7,
            "theft": 0.0,
        }
        
        correlation = historical_correlation or correlation_map.get(actual_loss_driver, 0.5)
        basis_risk = 1.0 - correlation
        
        # Risk level classification
        if basis_risk < 0.2:
            risk_level = "low"
        elif basis_risk < 0.4:
            risk_level = "moderate"
        else:
            risk_level = "high"
        
        return {
            "correlation": correlation,
            "basis_risk_score": basis_risk,
            "risk_level": risk_level,
            "explanation": f"Correlation between trigger and loss: {correlation:.2f}. "
                          f"Basis risk: {basis_risk:.2f} ({risk_level})"
        }
