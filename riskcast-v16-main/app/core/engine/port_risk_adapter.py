"""
Port Risk Adapter

Adapts real-time port data from PortService to work with synchronous risk engine.
Provides fallback to hardcoded data when real data unavailable.
"""
from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# Global cache for port risk data (to avoid repeated API calls in same request)
_port_risk_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamp: Dict[str, datetime] = {}


async def get_port_risk_from_api(
    port_code: str,
    port_type: str = "departure"
) -> Optional[Dict[str, Any]]:
    """
    Get port risk from real API if available.
    
    This is called asynchronously before risk calculation.
    Results are cached for the duration of the request.
    """
    try:
        from app.integrations.ports import get_port_service
        
        port_service = get_port_service()
        assessment = await port_service.get_port_risk_assessment(port_code)
        
        # Convert to format expected by risk engine
        risk_data = {
            "port_code": port_code,
            "port_risk_score": assessment["risk_assessment"]["port_risk_score"],
            "congestion": assessment["current_conditions"]["congestion_score"] * 10,  # Convert 0-1 to 0-10
            "efficiency": 10 - (assessment["current_conditions"]["berth_utilization_pct"] / 10),  # Invert
            "customs": 5.0,  # Would need separate API
            "data_quality": assessment["data_quality"]["quality"],
            "risk_factors": assessment["risk_assessment"]["risk_factors"],
            "from_api": True
        }
        
        # Cache for this request
        cache_key = f"{port_code}:{port_type}"
        _port_risk_cache[cache_key] = risk_data
        _cache_timestamp[cache_key] = datetime.utcnow()
        
        return risk_data
        
    except Exception as e:
        logger.warning(f"Failed to fetch real port data for {port_code}: {e}")
        return None


def get_cached_port_risk(
    port_code: str,
    port_type: str = "departure"
) -> Optional[Dict[str, Any]]:
    """
    Get cached port risk data from API call.
    
    Used by synchronous risk engine.
    """
    cache_key = f"{port_code}:{port_type}"
    if cache_key in _port_risk_cache:
        # Check if cache is still fresh (within last 5 minutes)
        age = datetime.utcnow() - _cache_timestamp.get(cache_key, datetime.utcnow())
        if age.total_seconds() < 300:  # 5 minutes
            return _port_risk_cache[cache_key]
    
    return None


def clear_port_risk_cache():
    """Clear port risk cache (call at start of new request)."""
    global _port_risk_cache, _cache_timestamp
    _port_risk_cache.clear()
    _cache_timestamp.clear()
