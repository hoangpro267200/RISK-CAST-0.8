"""
Cache-Aside Pattern Implementation

Features:
1. Read-through caching
2. Write-around caching
3. Cache invalidation
"""

from typing import Any, Callable, Optional, TypeVar, Generic
import asyncio

from app.cache.multi_level import MultiLevelCache
from app.core.logging import get_logger


logger = get_logger(__name__)
T = TypeVar("T")


class CacheAside(Generic[T]):
    """
    Cache-aside pattern for database entities.
    
    Read: Check cache -> If miss, load from DB -> Cache result
    Write: Update DB -> Invalidate cache
    """
    
    def __init__(
        self,
        cache: MultiLevelCache,
        key_prefix: str,
        loader: Callable[[str], T],
        l1_ttl: int = 60,
        l2_ttl: int = 3600
    ):
        self.cache = cache
        self.key_prefix = key_prefix
        self.loader = loader
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
    
    def _make_key(self, entity_id: str) -> str:
        """Create cache key for entity."""
        return f"{self.key_prefix}:{entity_id}"
    
    async def get(self, entity_id: str) -> Optional[T]:
        """
        Get entity from cache or load from source.
        """
        key = self._make_key(entity_id)
        
        # Try cache
        cached = await self.cache.get(key)
        if cached is not None:
            return cached
        
        # Load from source
        entity = await self._load(entity_id)
        
        if entity is not None:
            # Cache it
            await self.cache.set(key, entity, self.l1_ttl, self.l2_ttl)
        
        return entity
    
    async def _load(self, entity_id: str) -> Optional[T]:
        """Load entity from source."""
        if asyncio.iscoroutinefunction(self.loader):
            return await self.loader(entity_id)
        else:
            # Run sync loader in thread
            return await asyncio.to_thread(self.loader, entity_id)
    
    async def invalidate(self, entity_id: str):
        """Invalidate cached entity."""
        key = self._make_key(entity_id)
        await self.cache.delete(key)
        logger.debug(f"Cache invalidated: {key}")
    
    async def invalidate_many(self, entity_ids: list):
        """Invalidate multiple entities."""
        for entity_id in entity_ids:
            await self.invalidate(entity_id)
    
    async def refresh(self, entity_id: str) -> Optional[T]:
        """Force refresh entity in cache."""
        await self.invalidate(entity_id)
        return await self.get(entity_id)
    
    async def set(self, entity_id: str, entity: T):
        """Explicitly set entity in cache."""
        key = self._make_key(entity_id)
        await self.cache.set(key, entity, self.l1_ttl, self.l2_ttl)


class QueryCache:
    """
    Cache for database query results.
    """
    
    def __init__(
        self,
        cache: MultiLevelCache,
        key_prefix: str = "query",
        default_ttl: int = 300
    ):
        self.cache = cache
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
    
    def _make_key(self, query_name: str, params: dict) -> str:
        """Create cache key from query name and parameters."""
        import hashlib
        import json
        
        # Sort params for consistent key
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        
        return f"{self.key_prefix}:{query_name}:{param_hash}"
    
    async def get(
        self,
        query_name: str,
        params: dict,
        executor: Callable,
        ttl: Optional[int] = None
    ):
        """
        Get query result from cache or execute query.
        """
        key = self._make_key(query_name, params)
        ttl = ttl or self.default_ttl
        
        return await self.cache.get_or_set(
            key,
            lambda: executor(params),
            l1_ttl=min(60, ttl),
            l2_ttl=ttl
        )
    
    async def invalidate(self, query_name: str):
        """Invalidate all cached results for a query."""
        pattern = f"{self.key_prefix}:{query_name}:*"
        await self.cache.delete_pattern(pattern)
