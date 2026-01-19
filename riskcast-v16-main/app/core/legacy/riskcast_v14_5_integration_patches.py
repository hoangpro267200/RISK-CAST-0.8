"""
===============================================================
RISKCAST v14.5 — Integration Patches
Helper functions for integrating climate modules into v14.0

Author: Kai × Hoàng | v14.5 Integration
===============================================================
"""

from typing import Dict, Any, Optional
from app.core.legacy.riskcast_v14_5_climate_upgrade import ClimateVariables


def extract_climate_variables(shipment_data: Dict[str, Any]) -> ClimateVariables:
    """
    Extract climate variables from shipment data dictionary
    
    Args:
        shipment_data: Dictionary containing shipment parameters
        
    Returns:
        ClimateVariables object
    """
    return ClimateVariables(
        ENSO_index=shipment_data.get('ENSO_index', 0.0),
        seasonal_typhoon_frequency=shipment_data.get('typhoon_frequency', 0.5),
        sea_surface_temperature_anomaly=shipment_data.get('sst_anomaly', 0.0),
        port_climate_stress_score=shipment_data.get('port_climate_stress', 5.0),
        long_term_climate_volatility_index=shipment_data.get('climate_volatility_index', 5.0),
        climate_tail_event_probability=shipment_data.get('climate_tail_event_probability', 0.05),
        ESG_score=shipment_data.get('ESG_score', 50.0),
        climate_resilience_score=shipment_data.get('climate_resilience', 5.0),
        green_packaging_score=shipment_data.get('green_packaging', 5.0),
    )


def apply_climate_defaults(shipment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply default climate values if missing from shipment data
    
    Args:
        shipment_data: Dictionary containing shipment parameters
        
    Returns:
        Dictionary with climate defaults applied
    """
    defaults = {
        'ENSO_index': 0.0,
        'typhoon_frequency': 0.5,
        'sst_anomaly': 0.0,
        'port_climate_stress': 5.0,
        'climate_volatility_index': 5.0,
        'climate_tail_event_probability': 0.05,
        'ESG_score': 50.0,
        'climate_resilience': 5.0,
        'green_packaging': 5.0
    }
    
    result = shipment_data.copy()
    for key, default_value in defaults.items():
        if key not in result:
            result[key] = default_value
    
    return result




