"""
RISKCAST Cache Module
Caching utilities for risk analysis results
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json


class SimpleCache:
    """Simple in-memory cache for risk analysis results"""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time to live in seconds (default 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if expired/missing
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if datetime.now() > entry['expires_at']:
            del self.cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = {
            'value': value,
            'expires_at': datetime.now() + self.ttl
        }
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate specific cache entry
        
        Args:
            key: Cache key to invalidate
        """
        if key in self.cache:
            del self.cache[key]


# Global cache instance
risk_cache = SimpleCache(ttl_seconds=3600)





















