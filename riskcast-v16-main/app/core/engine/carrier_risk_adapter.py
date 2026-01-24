"""
Carrier Risk Adapter

Adapts real-time carrier data from CarrierService to work with synchronous risk engine.
Provides fallback to hardcoded data when real data unavailable.
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global cache for carrier risk data (to avoid repeated API calls in same request)
_carrier_risk_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamp: Dict[str, datetime] = {}


async def get_carrier_risk_from_api(
    carrier_code: str,
    origin_port: Optional[str] = None,
    destination_port: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get carrier risk from real API if available.
    
    This is called asynchronously before risk calculation.
    Results are cached for the duration of the request.
    """
    try:
        from app.integrations.carriers import get_carrier_service
        
        carrier_service = get_carrier_service()
        assessment = await carrier_service.get_carrier_risk_assessment(
            carrier_code=carrier_code,
            origin_port=origin_port,
            destination_port=destination_port
        )
        
        # Convert to format expected by risk engine
        risk_data = {
            "carrier_code": carrier_code,
            "carrier_rating": assessment["rating"]["carrier_rating"],
            "carrier_risk_score": assessment["rating"]["carrier_risk_score"],
            "on_time_delivery_pct": assessment["performance"]["on_time_delivery_pct"],
            "schedule_reliability_pct": assessment["performance"]["schedule_reliability_pct"],
            "claim_frequency_pct": assessment["performance"]["claim_frequency_pct"],
            "damage_rate_pct": assessment["performance"]["damage_rate_pct"],
            "data_quality": assessment["data_quality"]["quality"],
            "risk_factors": assessment["rating"]["risk_factors"],
            "from_api": True
        }
        
        # Add route-specific data if available
        if assessment.get("route_specific"):
            route = assessment["route_specific"]
            risk_data["route_on_time_pct"] = route.get("route_on_time_pct")
            risk_data["route_transit_variance_days"] = route.get("route_transit_variance_days")
        
        # Cache for this request
        cache_key = f"{carrier_code}:{origin_port}:{destination_port}"
        _carrier_risk_cache[cache_key] = risk_data
        _cache_timestamp[cache_key] = datetime.utcnow()
        
        return risk_data
        
    except Exception as e:
        logger.warning(f"Failed to fetch real carrier data for {carrier_code}: {e}")
        return None


def get_cached_carrier_risk(
    carrier_code: str,
    origin_port: Optional[str] = None,
    destination_port: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get cached carrier risk data from API call.
    
    Used by synchronous risk engine.
    """
    cache_key = f"{carrier_code}:{origin_port}:{destination_port}"
    if cache_key in _carrier_risk_cache:
        # Check if cache is still fresh (within last 5 minutes)
        age = datetime.utcnow() - _cache_timestamp.get(cache_key, datetime.utcnow())
        if age.total_seconds() < 300:  # 5 minutes
            return _carrier_risk_cache[cache_key]
    
    return None


def clear_carrier_risk_cache():
    """Clear carrier risk cache (call at start of new request)."""
    global _carrier_risk_cache, _cache_timestamp
    _carrier_risk_cache.clear()
    _cache_timestamp.clear()
