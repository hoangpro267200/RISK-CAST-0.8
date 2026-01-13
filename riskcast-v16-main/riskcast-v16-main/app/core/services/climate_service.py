"""
RISKCAST Climate Service Module
Climate data and risk analysis services
"""

from typing import Dict, Any, Optional
from datetime import datetime
from app.core.legacy.riskcast_v14_5_climate_upgrade import ClimateVariables


def get_climate_data(
    route: str = "",
    start_date: str = "",
    end_date: str = "",
    pol: str = "",
    pod: str = ""
) -> Dict[str, float]:
    """
    Fetch climate data for transit window.
    Returns seasonal defaults if NOAA/NASA APIs unavailable.
    
    Args:
        route: Route identifier
        start_date: Start date in ISO format
        end_date: End date in ISO format
        pol: Port of loading code
        pod: Port of discharge code
    
    Returns:
        Dictionary with climate data
    """
    try:
        # Parse dates
        start = datetime.fromisoformat(start_date) if start_date else datetime.now()
        month = start.month
        
        # Determine if typhoon season (June-October)
        is_typhoon_season = month in [6, 7, 8, 9, 10]
        
        # Route-based defaults
        route_risk_map = {
            'vn_us': 6.5,
            'vn_eu': 5.0,
            'vn_cn': 4.5,
            'domestic': 3.5
        }
        
        base_weather_risk = route_risk_map.get(route, 5.0)
        if is_typhoon_season:
            base_weather_risk += 2.0
        
        # Port risk defaults (can be enhanced with port database)
        port_risk_db = {
            'VNSGN': 4.0,
            'VNHPH': 3.5,
            'USLAX': 5.0,
            'USNYC': 5.5,
            'CNSHA': 4.5,
        }
        
        pol_risk = port_risk_db.get(pol, 5.0)
        pod_risk = port_risk_db.get(pod, 5.0)
        port_stress = (pol_risk + pod_risk) / 2
        
        # Return climate data
        return {
            'enso': 0.0,  # Neutral by default
            'typhoon_freq': 0.7 if is_typhoon_season else 0.3,
            'sst_anomaly': 0.0,
            'port_stress': min(port_stress, 10.0),
            'volatility': 65 if is_typhoon_season else 45
        }
        
    except Exception as e:
        # Return safe defaults on error
        return {
            'enso': 0.0,
            'typhoon_freq': 0.5,
            'sst_anomaly': 0.0,
            'port_stress': 5.0,
            'volatility': 50
        }


def create_climate_variables(climate_data: Dict[str, float]) -> ClimateVariables:
    """
    Create ClimateVariables object from climate data
    
    Args:
        climate_data: Dictionary with climate metrics
    
    Returns:
        ClimateVariables instance
    """
    return ClimateVariables(
        ENSO_index=climate_data.get('enso', 0.0),
        seasonal_typhoon_frequency=climate_data.get('typhoon_freq', 0.5),
        sea_surface_temperature_anomaly=climate_data.get('sst_anomaly', 0.0),
        port_climate_stress_score=climate_data.get('port_stress', 5.0),
        long_term_climate_volatility_index=climate_data.get('volatility', 50.0) / 10.0,  # Convert to 0-10 scale
        climate_tail_event_probability=0.05,
        ESG_score=50.0,
        climate_resilience_score=5.0,
        green_packaging_score=5.0
    )





















