"""
RISKCAST Engine v2 - Climate Risk Model
Computes climate-related risk scores based on weather patterns, seasonality, and extreme events
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass
class ClimateRiskScore:
    """Climate risk assessment result"""
    overall_risk: float  # 0-1
    storm_probability: float  # 0-1
    rainfall_intensity: float  # 0-1
    wind_index: float  # 0-1
    temperature_deviation: float  # 0-1
    seasonal_volatility: float  # 0-1
    enso_influence: float  # -1 to 1 (El Niño/La Niña)
    explanation: Dict[str, str]


class ClimateRiskModel:
    """Climate risk assessment model"""
    
    # Seasonal risk multipliers (monthly)
    SEASONAL_MULTIPLIERS = {
        1: 1.2,   # January - Winter storms
        2: 1.1,   # February
        3: 0.9,   # March
        4: 0.8,   # April
        5: 0.7,   # May
        6: 1.0,   # June - Hurricane season starts
        7: 1.1,   # July
        8: 1.3,   # August - Peak hurricane
        9: 1.2,   # September - Peak hurricane
        10: 1.1,  # October
        11: 1.0,  # November
        12: 1.2,  # December - Winter storms
    }
    
    # ENSO (El Niño Southern Oscillation) effects
    ENSO_MULTIPLIERS = {
        "el_nino": {
            "pacific": 1.3,  # More storms in Pacific
            "atlantic": 0.7, # Fewer hurricanes in Atlantic
        },
        "la_nina": {
            "pacific": 0.8,  # Fewer storms in Pacific
            "atlantic": 1.4, # More hurricanes in Atlantic
        },
        "neutral": {
            "pacific": 1.0,
            "atlantic": 1.0,
        }
    }
    
    def __init__(self):
        """Initialize climate risk model"""
        pass
    
    def compute_storm_probability(self, route: str, month: int, region: str = "auto") -> float:
        """
        Compute storm probability based on route and season
        
        Args:
            route: Route identifier (e.g., "US-ASIA", "EU-ASIA")
            month: Month number (1-12)
            region: Ocean region ("pacific", "atlantic", "indian", "auto")
            
        Returns:
            Storm probability score (0-1)
        """
        # Auto-detect region from route
        if region == "auto":
            # CRITICAL FIX: Handle None values before calling .upper()
            route = str(route) if route is not None else ""
            route_upper = route.upper()
            if any(x in route_upper for x in ["US", "ASIA", "PACIFIC"]):
                region = "pacific"
            elif any(x in route_upper for x in ["EU", "ATLANTIC"]):
                region = "atlantic"
            elif any(x in route_upper for x in ["INDIA", "MIDDLE", "EAST"]):
                region = "indian"
            else:
                region = "pacific"  # Default
        
        # Base storm probability by region
        base_probability = {
            "pacific": 0.15,
            "atlantic": 0.12,
            "indian": 0.10,
        }.get(region, 0.12)
        
        # Seasonal adjustment
        seasonal_mult = self.SEASONAL_MULTIPLIERS.get(month, 1.0)
        probability = base_probability * seasonal_mult
        
        # Clamp to 0-1
        return min(1.0, max(0.0, probability))
    
    def compute_rainfall_intensity(self, route: str, month: int) -> float:
        """
        Compute rainfall intensity index
        
        Args:
            route: Route identifier
            month: Month number (1-12)
            
        Returns:
            Rainfall intensity score (0-1)
        """
        # Monsoon seasons (approximate)
        monsoon_months = {
            "indian": [6, 7, 8, 9],  # Indian Ocean monsoon
            "southeast_asia": [6, 7, 8, 9, 10],  # Southeast Asia
        }
        
        # CRITICAL FIX: Handle None values before calling .upper()
        route = str(route) if route is not None else ""
        route_upper = route.upper()
        is_monsoon = False
        
        if any(x in route_upper for x in ["INDIA", "BANGLADESH", "MYANMAR"]):
            is_monsoon = month in monsoon_months["indian"]
        elif any(x in route_upper for x in ["VIETNAM", "THAILAND", "SINGAPORE", "MALAYSIA"]):
            is_monsoon = month in monsoon_months["southeast_asia"]
        
        if is_monsoon:
            base_intensity = 0.7
        else:
            base_intensity = 0.3
        
        # Seasonal variation
        seasonal_factor = 0.5 + 0.5 * math.sin((month - 3) * math.pi / 6)
        intensity = base_intensity * seasonal_factor
        
        return min(1.0, max(0.0, intensity))
    
    def compute_wind_index(self, route: str, month: int) -> float:
        """
        Compute wind intensity index
        
        Args:
            route: Route identifier
            month: Month number (1-12)
            
        Returns:
            Wind index (0-1)
        """
        # Peak wind months
        peak_wind_months = [7, 8, 9, 10]  # Hurricane/typhoon season
        
        base_wind = 0.4
        if month in peak_wind_months:
            base_wind = 0.8
        
        # Route-specific adjustments
        # CRITICAL FIX: Handle None values before calling .upper()
        route = str(route) if route is not None else ""
        route_upper = route.upper()
        if any(x in route_upper for x in ["CARIBBEAN", "GULF", "EAST_COAST"]):
            base_wind *= 1.2  # Higher wind risk
        
        return min(1.0, max(0.0, base_wind))
    
    def compute_temperature_deviation(self, route: str, month: int) -> float:
        """
        Compute temperature deviation from normal
        
        Args:
            route: Route identifier
            month: Month number (1-12)
            
        Returns:
            Temperature deviation score (0-1, higher = more extreme)
        """
        # Simplified: assume normal variation is low, extreme is high
        # In production, would use actual climate data
        
        base_deviation = 0.3
        
        # Extreme months (summer/winter)
        if month in [1, 2, 7, 8]:
            base_deviation = 0.6
        
        # Add some randomness (simulating climate variability)
        variation = np.random.normal(0, 0.1)
        deviation = base_deviation + variation
        
        return min(1.0, max(0.0, deviation))
    
    def compute_seasonal_volatility(self, route: str) -> float:
        """
        Compute seasonal volatility index
        
        Args:
            route: Route identifier
            
        Returns:
            Seasonal volatility score (0-1)
        """
        # Routes with high seasonal variation
        volatile_routes = ["ARCTIC", "NORTHERN", "BALTIC"]
        
        # CRITICAL FIX: Handle None values before calling .upper()
        route = str(route) if route is not None else ""
        route_upper = route.upper()
        is_volatile = any(volatile in route_upper for volatile in volatile_routes)
        
        if is_volatile:
            volatility = 0.7
        else:
            volatility = 0.4
        
        return volatility
    
    def compute_enso_influence(self, route: str, enso_state: str = "neutral") -> float:
        """
        Compute El Niño/La Niña influence
        
        Args:
            route: Route identifier
            enso_state: "el_nino", "la_nina", or "neutral"
            
        Returns:
            ENSO influence multiplier (0-2)
        """
        # Determine route region
        # CRITICAL FIX: Handle None values before calling .upper()
        route = str(route) if route is not None else ""
        route_upper = route.upper()
        if any(x in route_upper for x in ["PACIFIC", "ASIA", "US"]):
            region = "pacific"
        elif any(x in route_upper for x in ["ATLANTIC", "EU"]):
            region = "atlantic"
        else:
            region = "pacific"  # Default
        
        # Get ENSO multiplier
        multipliers = self.ENSO_MULTIPLIERS.get(enso_state, self.ENSO_MULTIPLIERS["neutral"])
        multiplier = multipliers.get(region, 1.0)
        
        return multiplier
    
    def compute_climate_risk(self, route: str, departure_date: Optional[str] = None,
                           etd: Optional[str] = None, enso_state: str = "neutral") -> ClimateRiskScore:
        """
        Compute comprehensive climate risk score
        
        Args:
            route: Route identifier
            departure_date: Departure date (YYYY-MM-DD)
            etd: Estimated time of departure (alternative to departure_date)
            enso_state: ENSO state ("el_nino", "la_nina", "neutral")
            
        Returns:
            ClimateRiskScore object
        """
        # Determine month from date
        month = datetime.now().month  # Default to current month
        if departure_date:
            try:
                date_obj = datetime.strptime(departure_date, "%Y-%m-%d")
                month = date_obj.month
            except:
                pass
        elif etd:
            try:
                date_obj = datetime.strptime(etd, "%Y-%m-%d")
                month = date_obj.month
            except:
                pass
        
        # Compute individual components
        storm_prob = self.compute_storm_probability(route, month)
        rainfall = self.compute_rainfall_intensity(route, month)
        wind = self.compute_wind_index(route, month)
        temp_dev = self.compute_temperature_deviation(route, month)
        volatility = self.compute_seasonal_volatility(route)
        enso_mult = self.compute_enso_influence(route, enso_state)
        
        # Weighted combination (storm and wind are most critical)
        weighted_components = (
            storm_prob * 0.30 +
            wind * 0.25 +
            rainfall * 0.20 +
            temp_dev * 0.10 +
            volatility * 0.15
        )
        
        # Apply ENSO multiplier
        overall_risk = weighted_components * enso_mult
        
        # Clamp to 0-1
        overall_risk = min(1.0, max(0.0, overall_risk))
        
        # Generate explanation
        explanation = {
            "storm_probability": f"{storm_prob:.1%} storm probability based on {route} route and season",
            "wind_index": f"Wind index {wind:.2f} (peak season: {month in [7,8,9]})",
            "rainfall": f"Rainfall intensity {rainfall:.2f}",
            "enso": f"ENSO state: {enso_state} (multiplier: {enso_mult:.2f})",
            "overall": f"Combined climate risk: {overall_risk:.1%}"
        }
        
        return ClimateRiskScore(
            overall_risk=overall_risk,
            storm_probability=storm_prob,
            rainfall_intensity=rainfall,
            wind_index=wind,
            temperature_deviation=temp_dev,
            seasonal_volatility=volatility,
            enso_influence=enso_mult - 1.0,  # Center around 0
            explanation=explanation
        )





















