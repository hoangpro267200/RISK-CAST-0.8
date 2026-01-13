"""
RISKCAST Caching System

Provides caching for risk calculation results to improve performance.
Supports both in-memory (default) and Redis (optional) backends.

ARCHITECTURE:
- Cache key generated from normalized RiskRequest (hash)
- TTL configurable via environment
- Same inputs return cached results (within tolerance)
"""
import os
import hashlib
import json
import time
from typing import Dict, Any, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Check if Redis is available
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cache configuration
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Default 1 hour
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"

# Initialize Redis client if enabled
redis_client = None
if USE_REDIS:
    try:
        import redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        redis_client.ping()
        logger.info(f"[Cache] Using Redis backend: {REDIS_URL}")
    except ImportError:
        logger.warning("[Cache] Redis not installed, falling back to in-memory cache")
        USE_REDIS = False
    except Exception as e:
        logger.warning(f"[Cache] Redis connection failed: {e}, falling back to in-memory cache")
        USE_REDIS = False

# In-memory cache (fallback or default)
_memory_cache: Dict[str, tuple] = {}  # {cache_key: (data, timestamp)}


def normalize_request_for_cache(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize request data for cache key generation
    
    Removes non-deterministic fields (timestamps, IDs) and sorts keys
    for consistent hashing.
    
    Args:
        request: Risk calculation request dictionary
        
    Returns:
        Normalized dictionary
    """
    normalized = {}
    
    # Fields that affect calculation (include in cache key)
    cache_relevant_fields = [
        'transport_mode', 'cargo_type', 'route', 'incoterm',
        'container', 'container_match', 'packaging', 'packaging_quality',
        'priority', 'priority_profile', 'priority_weights',
        'transit_time', 'cargo_value', 'shipment_value',
        'route_type', 'distance',
        'weather_risk', 'port_risk', 'carrier_rating',
        'ENSO_index', 'typhoon_frequency', 'sst_anomaly',
        'port_climate_stress', 'climate_volatility_index',
        'climate_tail_event_probability', 'ESG_score',
        'climate_resilience', 'green_packaging',
        'buyer', 'seller',
        'use_fuzzy', 'use_forecast', 'use_mc', 'use_var',
        'mc_iterations', 'language'
    ]
    
    for field in cache_relevant_fields:
        if field in request:
            value = request[field]
            # Normalize nested structures
            if isinstance(value, dict):
                # Sort dict keys for consistent hashing
                value = json.dumps(value, sort_keys=True)
            elif isinstance(value, list):
                # Sort list items if possible
                try:
                    value = json.dumps(sorted(value), sort_keys=True)
                except TypeError:
                    value = json.dumps(value, sort_keys=True)
            normalized[field] = value
    
    return normalized


def generate_cache_key(request: Dict[str, Any]) -> str:
    """
    Generate cache key from normalized request
    
    Args:
        request: Risk calculation request
        
    Returns:
        Cache key (MD5 hash)
    """
    normalized = normalize_request_for_cache(request)
    
    # Convert to JSON string with sorted keys
    json_str = json.dumps(normalized, sort_keys=True, default=str)
    
    # Generate MD5 hash
    cache_key = hashlib.md5(json_str.encode('utf-8')).hexdigest()
    
    return f"riskcast:risk:{cache_key}"


def get_cache(key: str) -> Optional[Dict[str, Any]]:
    """
    Get value from cache
    
    Args:
        key: Cache key
        
    Returns:
        Cached data or None if not found/expired
    """
    if not CACHE_ENABLED:
        return None
    
    try:
        if USE_REDIS and redis_client:
            # Redis backend
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
        else:
            # In-memory backend
            if key in _memory_cache:
                data, timestamp = _memory_cache[key]
                # Check TTL
                if time.time() - timestamp < CACHE_TTL:
                    return data
                else:
                    # Expired, remove from cache
                    del _memory_cache[key]
    except Exception as e:
        logger.warning(f"[Cache] Error getting cache key {key}: {e}")
    
    return None


def set_cache(key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
    """
    Set value in cache
    
    Args:
        key: Cache key
        value: Data to cache
        ttl: Time to live in seconds (defaults to CACHE_TTL)
    """
    if not CACHE_ENABLED:
        return
    
    ttl = ttl or CACHE_TTL
    
    try:
        if USE_REDIS and redis_client:
            # Redis backend
            redis_client.setex(key, ttl, json.dumps(value))
        else:
            # In-memory backend
            _memory_cache[key] = (value, time.time())
            # Simple cleanup: remove expired entries if cache gets too large
            if len(_memory_cache) > 1000:
                current_time = time.time()
                expired_keys = [
                    k for k, (_, ts) in _memory_cache.items()
                    if current_time - ts >= ttl
                ]
                for k in expired_keys:
                    del _memory_cache[k]
    except Exception as e:
        logger.warning(f"[Cache] Error setting cache key {key}: {e}")


def clear_cache(pattern: Optional[str] = None) -> int:
    """
    Clear cache entries
    
    Args:
        pattern: Optional pattern to match (e.g., "riskcast:risk:*")
                 If None, clears all cache
                 
    Returns:
        Number of keys cleared
    """
    cleared = 0
    
    try:
        if USE_REDIS and redis_client:
            # Redis backend
            if pattern:
                keys = redis_client.keys(pattern)
                if keys:
                    cleared = redis_client.delete(*keys)
            else:
                # Clear all riskcast keys
                keys = redis_client.keys("riskcast:*")
                if keys:
                    cleared = redis_client.delete(*keys)
        else:
            # In-memory backend
            if pattern:
                # Simple pattern matching (starts with)
                prefix = pattern.replace("*", "")
                keys_to_delete = [k for k in _memory_cache.keys() if k.startswith(prefix)]
                for k in keys_to_delete:
                    del _memory_cache[k]
                    cleared += 1
            else:
                # Clear all
                cleared = len(_memory_cache)
                _memory_cache.clear()
    except Exception as e:
        logger.warning(f"[Cache] Error clearing cache: {e}")
    
    return cleared


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics
    
    Returns:
        Dictionary with cache stats
    """
    stats = {
        "enabled": CACHE_ENABLED,
        "backend": "redis" if (USE_REDIS and redis_client) else "memory",
        "ttl": CACHE_TTL
    }
    
    try:
        if USE_REDIS and redis_client:
            # Redis stats
            info = redis_client.info("memory")
            stats["memory_used"] = info.get("used_memory_human", "unknown")
            stats["keys"] = redis_client.dbsize()
        else:
            # Memory stats
            stats["keys"] = len(_memory_cache)
            stats["memory_used"] = "N/A (in-memory)"
    except Exception as e:
        logger.warning(f"[Cache] Error getting cache stats: {e}")
    
    return stats
