"""
Climate Risk Adapter

Adapts real-time climate data from ClimateService to work with risk engine.
Provides fallback to synthetic/default climate inputs when real data unavailable.
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global cache for climate data (to avoid repeated API calls in same request)
_climate_data_cache: Optional[Dict[str, Any]] = None
_cache_timestamp: Optional[datetime] = None


async def get_climate_data_from_api() -> Optional[Dict[str, Any]]:
    """
    Get climate data from real API if available.
    
    This is called asynchronously before risk calculation.
    Results are cached for the duration of the request.
    """
    try:
        from app.integrations.climate import get_climate_service
        
        climate_service = get_climate_service()
        assessment = await climate_service.get_climate_risk_assessment()
        
        # Convert to format expected by risk engine
        climate_data = {
            "oni_value": assessment["climate_indices"]["oni"],
            "enso_phase": assessment["climate_indices"]["enso_phase"],
            "enso_forecast": assessment["climate_indices"]["enso_forecast"],
            "pdo_value": assessment["climate_indices"]["pdo"],
            "amo_value": assessment["climate_indices"]["amo"],
            "nao_value": assessment["climate_indices"]["nao"],
            "atlantic_ace": assessment["tropical_cyclones"]["atlantic_ace"],
            "pacific_ace": assessment["tropical_cyclones"]["pacific_ace"],
            "active_tropical_systems": assessment["tropical_cyclones"]["active_systems"],
            "risk_adjustments": assessment["risk_adjustments"],
            "data_quality": assessment["data_quality"]["quality"],
            "data_source": assessment["data_quality"]["source"],
            "from_api": True
        }
        
        # Cache for this request
        global _climate_data_cache, _cache_timestamp
        _climate_data_cache = climate_data
        _cache_timestamp = datetime.utcnow()
        
        return climate_data
        
    except Exception as e:
        logger.warning(f"Failed to fetch real climate data: {e}")
        return None


def get_cached_climate_data() -> Optional[Dict[str, Any]]:
    """
    Get cached climate data from API call.
    
    Used by synchronous risk engine.
    """
    global _climate_data_cache, _cache_timestamp
    
    if _climate_data_cache is not None:
        # Check if cache is still fresh (within last 5 minutes)
        if _cache_timestamp:
            age = datetime.utcnow() - _cache_timestamp
            if age.total_seconds() < 300:  # 5 minutes
                return _climate_data_cache
    
    return None


def clear_climate_data_cache():
    """Clear climate data cache (call at start of new request)."""
    global _climate_data_cache, _cache_timestamp
    _climate_data_cache = None
    _cache_timestamp = None


def convert_to_climate_variables_dict(climate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert climate data to ClimateVariables format.
    
    This bridges the new NOAA data structure to the existing ClimateVariables
    used by the risk engine.
    """
    # ONI value is the ENSO index (typically ranges from -2 to +2)
    oni_value = climate_data.get("oni_value", 0.0)
    
    # Convert ACE to typhoon frequency (normalize to 0-1)
    # Historical average ACE is ~100, very active season is ~200+
    pacific_ace = climate_data.get("pacific_ace", 100.0)
    typhoon_frequency = min(pacific_ace / 200.0, 1.0)  # Cap at 1.0
    
    # Use PDO/AMO as SST anomaly proxy (they're related to ocean temperatures)
    sst_anomaly = (climate_data.get("pdo_value", 0.0) + climate_data.get("amo_value", 0.0)) / 2.0
    
    # Port climate stress based on active tropical systems
    active_systems = climate_data.get("active_tropical_systems", [])
    port_stress = min(len(active_systems) * 1.5, 10.0)  # Each system adds stress
    
    # Climate volatility based on ENSO strength
    enso_strength = abs(oni_value)
    climate_volatility = 5.0 + (enso_strength * 2.0)  # Strong ENSO = higher volatility
    
    # Climate tail event probability based on ACE
    # Very active seasons (ACE > 150) have higher tail risk
    atlantic_ace = climate_data.get("atlantic_ace", 100.0)
    tail_probability = min(0.05 + (max(0, atlantic_ace - 100) / 1000), 0.15)
    
    return {
        "ENSO_index": oni_value,
        "seasonal_typhoon_frequency": typhoon_frequency,
        "sea_surface_temperature_anomaly": sst_anomaly,
        "port_climate_stress_score": port_stress,
        "long_term_climate_volatility_index": climate_volatility,
        "climate_tail_event_probability": tail_probability,
        "ESG_score": 50.0,  # Not provided by NOAA, keep default
        "climate_resilience_score": 5.0,  # Not provided by NOAA, keep default
        "green_packaging_score": 5.0,  # Not provided by NOAA, keep default
        # Additional metadata
        "_data_quality": climate_data.get("data_quality", "FALLBACK"),
        "_data_source": climate_data.get("data_source", "synthetic"),
        "_from_api": climate_data.get("from_api", False),
    }
