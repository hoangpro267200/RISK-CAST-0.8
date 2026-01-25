"""
Multi-Level Cache Implementation

Features:
1. L1 (Local) + L2 (Redis) caching
2. Automatic promotion/demotion
3. TTL management
4. Cache statistics
"""

import asyncio
import time
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from collections import OrderedDict
from functools import wraps
import threading

from app.core.logging import get_logger


logger = get_logger(__name__)
T = TypeVar("T")

# Optional Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import redis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        redis = None


@dataclass
class CacheEntry:
    """Entry in the cache."""
    value: Any
    expires_at: float  # Unix timestamp
    created_at: float
    access_count: int = 0
    last_accessed: float = 0
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    @property
    def ttl_remaining(self) -> float:
        return max(0, self.expires_at - time.time())


@dataclass
class CacheStats:
    """Cache statistics."""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    writes: int = 0
    evictions: int = 0
    
    @property
    def l1_hit_rate(self) -> float:
        total = self.l1_hits + self.l1_misses
        return self.l1_hits / total if total > 0 else 0
    
    @property
    def l2_hit_rate(self) -> float:
        total = self.l2_hits + self.l2_misses
        return self.l2_hits / total if total > 0 else 0
    
    @property
    def overall_hit_rate(self) -> float:
        total = self.l1_hits + self.l1_misses
        hits = self.l1_hits + self.l2_hits
        return hits / total if total > 0 else 0


class LRUCache:
    """
    Thread-safe LRU cache for L1 (local) caching.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            # Update access stats
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            return entry
    
    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set entry in cache."""
        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug(f"L1 evicted: {evicted_key}")
            
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)


class MultiLevelCache:
    """
    Multi-level cache with L1 (local) and L2 (Redis).
    
    L1: Fast, limited size, process-local
    L2: Slower, larger, distributed
    """
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        l1_max_size: int = 1000,
        l1_default_ttl: int = 60,  # seconds
        l2_default_ttl: int = 3600,  # seconds
        key_prefix: str = "cache:",
        serializer: str = "json"  # "json" or "pickle"
    ):
        self.redis = redis_client
        self.l1 = LRUCache(max_size=l1_max_size)
        self.l1_default_ttl = l1_default_ttl
        self.l2_default_ttl = l2_default_ttl
        self.key_prefix = key_prefix
        self.serializer = serializer
        self.stats = CacheStats()
        self._is_async_redis = False
        
        # Check if Redis client is async
        if self.redis is not None:
            try:
                # Try to detect async Redis client
                if hasattr(self.redis, 'get') and asyncio.iscoroutinefunction(self.redis.get):
                    self._is_async_redis = True
                elif hasattr(self.redis, 'execute_command'):
                    # Sync Redis client
                    self._is_async_redis = False
            except Exception:
                pass
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if self.serializer == "json":
            try:
                return json.dumps(value).encode()
            except (TypeError, ValueError):
                # Fallback to pickle for non-JSON-serializable objects
                return pickle.dumps(value)
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        if self.serializer == "json":
            try:
                return json.loads(data.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fallback to pickle
                return pickle.loads(data)
        else:
            return pickle.loads(data)
    
    def _make_key(self, key: str) -> str:
        """Create full cache key."""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Checks L1 first, then L2. Promotes L2 hits to L1.
        """
        # Try L1
        l1_entry = self.l1.get(key)
        if l1_entry is not None:
            self.stats.l1_hits += 1
            return l1_entry.value
        
        self.stats.l1_misses += 1
        
        # Try L2 if Redis is available
        if self.redis is None:
            self.stats.l2_misses += 1
            return None
        
        full_key = self._make_key(key)
        try:
            if self._is_async_redis:
                data = await self.redis.get(full_key)
            else:
                # Sync Redis - run in thread
                data = await asyncio.to_thread(self.redis.get, full_key)
            
            if data is not None:
                self.stats.l2_hits += 1
                value = self._deserialize(data)
                
                # Promote to L1
                if self._is_async_redis:
                    ttl = await self.redis.ttl(full_key)
                else:
                    ttl = await asyncio.to_thread(self.redis.ttl, full_key)
                
                if ttl > 0:
                    l1_ttl = min(ttl, self.l1_default_ttl)
                    self.l1.set(key, CacheEntry(
                        value=value,
                        expires_at=time.time() + l1_ttl,
                        created_at=time.time()
                    ))
                
                return value
            
            self.stats.l2_misses += 1
            return None
            
        except Exception as e:
            logger.error(f"L2 cache error: {e}")
            self.stats.l2_misses += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None
    ):
        """
        Set value in both cache levels.
        """
        l1_ttl = l1_ttl or self.l1_default_ttl
        l2_ttl = l2_ttl or self.l2_default_ttl
        
        # Set in L1
        self.l1.set(key, CacheEntry(
            value=value,
            expires_at=time.time() + l1_ttl,
            created_at=time.time()
        ))
        
        # Set in L2 if Redis is available
        if self.redis is not None:
            full_key = self._make_key(key)
            try:
                serialized = self._serialize(value)
                if self._is_async_redis:
                    await self.redis.setex(full_key, l2_ttl, serialized)
                else:
                    await asyncio.to_thread(
                        self.redis.setex, full_key, l2_ttl, serialized
                    )
                self.stats.writes += 1
            except Exception as e:
                logger.error(f"L2 cache write error: {e}")
    
    async def delete(self, key: str):
        """Delete from both cache levels."""
        self.l1.delete(key)
        
        if self.redis is not None:
            full_key = self._make_key(key)
            try:
                if self._is_async_redis:
                    await self.redis.delete(full_key)
                else:
                    await asyncio.to_thread(self.redis.delete, full_key)
            except Exception as e:
                logger.error(f"L2 cache delete error: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        if self.redis is None:
            return
        
        # Clear matching L2 entries
        full_pattern = self._make_key(pattern)
        try:
            if self._is_async_redis:
                cursor = 0
                while True:
                    cursor, keys = await self.redis.scan(
                        cursor=cursor,
                        match=full_pattern,
                        count=100
                    )
                    if keys:
                        await self.redis.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # Sync Redis - use scan_iter
                def _delete_pattern():
                    keys = list(self.redis.scan_iter(match=full_pattern))
                    if keys:
                        self.redis.delete(*keys)
                
                await asyncio.to_thread(_delete_pattern)
        except Exception as e:
            logger.error(f"L2 pattern delete error: {e}")
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None
    ) -> Any:
        """
        Get value or compute and cache if missing.
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            # Run sync function in thread
            value = await asyncio.to_thread(factory)
        
        # Cache it
        await self.set(key, value, l1_ttl, l2_ttl)
        
        return value
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "l1": {
                "size": self.l1.size(),
                "max_size": self.l1.max_size,
                "hits": self.stats.l1_hits,
                "misses": self.stats.l1_misses,
                "hit_rate": f"{self.stats.l1_hit_rate:.2%}"
            },
            "l2": {
                "hits": self.stats.l2_hits,
                "misses": self.stats.l2_misses,
                "hit_rate": f"{self.stats.l2_hit_rate:.2%}"
            },
            "overall": {
                "writes": self.stats.writes,
                "hit_rate": f"{self.stats.overall_hit_rate:.2%}"
            }
        }
    
    async def cleanup(self):
        """Run cleanup tasks."""
        # Cleanup expired L1 entries
        expired = self.l1.cleanup_expired()
        if expired > 0:
            logger.debug(f"Cleaned up {expired} expired L1 entries")


def cached(
    key_template: str,
    l1_ttl: int = 60,
    l2_ttl: int = 3600
):
    """
    Decorator for caching function results.
    
    Usage:
        @cached("user:{user_id}", l1_ttl=30, l2_ttl=300)
        async def get_user(user_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from template
            # Extract named parameters
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            key = key_template.format(**bound.arguments)
            
            # Get cache from context or global
            cache = kwargs.pop('_cache', None)
            if cache is None:
                # Would get from application context
                return await func(*args, **kwargs)
            
            return await cache.get_or_set(
                key,
                lambda: func(*args, **kwargs),
                l1_ttl=l1_ttl,
                l2_ttl=l2_ttl
            )
        
        return wrapper
    return decorator
