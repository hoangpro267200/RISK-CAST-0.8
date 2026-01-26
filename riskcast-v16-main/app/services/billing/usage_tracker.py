"""
Usage Tracking Service

Tracks resource usage for billing and quota enforcement.
"""

from datetime import datetime, date
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None


class UsageTracker:
    """
    Tracks resource usage for billing.
    """
    
    def __init__(self, redis_client = None):
        self.redis = redis_client
        self._memory_cache: Dict[str, int] = {}
    
    async def increment(
        self,
        tenant_id: str,
        resource: str,
        amount: int = 1
    ):
        """Increment usage counter."""
        key = self._make_key(tenant_id, resource)
        
        if self.redis and REDIS_AVAILABLE:
            try:
                await self.redis.incrby(key, amount)
                # Set expiry for monthly reset
                await self.redis.expire(key, 60 * 60 * 24 * 31)  # 31 days
            except Exception as e:
                logger.warning(f"Redis increment failed: {e}")
                self._memory_cache[key] = self._memory_cache.get(key, 0) + amount
        else:
            self._memory_cache[key] = self._memory_cache.get(key, 0) + amount
    
    async def get_usage(
        self,
        tenant_id: str,
        resource: str
    ) -> int:
        """Get current usage."""
        key = self._make_key(tenant_id, resource)
        
        if self.redis and REDIS_AVAILABLE:
            try:
                value = await self.redis.get(key)
                return int(value) if value else 0
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
                return self._memory_cache.get(key, 0)
        else:
            return self._memory_cache.get(key, 0)
    
    async def reset_usage(
        self,
        tenant_id: str,
        resource: Optional[str] = None
    ):
        """Reset usage counters."""
        if resource:
            key = self._make_key(tenant_id, resource)
            if self.redis and REDIS_AVAILABLE:
                try:
                    await self.redis.delete(key)
                except Exception as e:
                    logger.warning(f"Redis delete failed: {e}")
            self._memory_cache.pop(key, None)
        else:
            # Reset all for tenant
            keys_to_delete = [
                k for k in self._memory_cache.keys()
                if k.startswith(f"usage:{tenant_id}:")
            ]
            for key in keys_to_delete:
                self._memory_cache.pop(key, None)
            
            if self.redis and REDIS_AVAILABLE:
                try:
                    pattern = f"usage:{tenant_id}:*"
                    cursor = 0
                    while True:
                        cursor, keys = await self.redis.scan(cursor, match=pattern)
                        if keys:
                            await self.redis.delete(*keys)
                        if cursor == 0:
                            break
                except Exception as e:
                    logger.warning(f"Redis scan/delete failed: {e}")
    
    async def get_all_usage(self, tenant_id: str) -> Dict[str, int]:
        """Get all usage for tenant."""
        usage = {}
        
        for resource in ["quotes", "policies", "api_calls"]:
            usage[resource] = await self.get_usage(tenant_id, resource)
        
        return usage
    
    async def get_usage_history(
        self,
        tenant_id: str,
        resource: str,
        days: int = 30
    ) -> Dict[str, int]:
        """Get usage history for past N days."""
        history = {}
        
        for i in range(days):
            day = (date.today() - timedelta(days=i)).strftime("%Y-%m")
            key = f"usage:{tenant_id}:{resource}:{day}"
            
            if self.redis and REDIS_AVAILABLE:
                try:
                    value = await self.redis.get(key)
                    history[day] = int(value) if value else 0
                except Exception:
                    history[day] = 0
            else:
                history[day] = self._memory_cache.get(key, 0)
        
        return history
    
    def _make_key(self, tenant_id: str, resource: str) -> str:
        """Make cache key for usage counter."""
        # Include month for automatic monthly reset
        month = date.today().strftime("%Y-%m")
        return f"usage:{tenant_id}:{resource}:{month}"


# Import for usage history
from datetime import timedelta
