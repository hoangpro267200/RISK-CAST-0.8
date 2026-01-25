"""
Cache Invalidation Strategies

Features:
1. Event-based invalidation
2. Tag-based invalidation
3. Time-based invalidation
4. Dependency tracking
"""

from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from app.cache.multi_level import MultiLevelCache
from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class CacheTag:
    """Tag for grouping cache entries."""
    name: str
    keys: Set[str] = field(default_factory=set)


class TagBasedInvalidation:
    """
    Tag-based cache invalidation.
    
    Allows grouping cache entries by tags and invalidating by tag.
    """
    
    def __init__(self, cache: MultiLevelCache, redis_client):
        self.cache = cache
        self.redis = redis_client
        self.tag_prefix = "cache:tag:"
        self._is_async_redis = False
        
        # Check if Redis client is async
        if self.redis is not None:
            try:
                if hasattr(self.redis, 'sadd') and asyncio.iscoroutinefunction(self.redis.sadd):
                    self._is_async_redis = True
            except Exception:
                pass
    
    async def tag_key(self, key: str, tags: List[str]):
        """Associate a key with tags."""
        if self.redis is None:
            return
        
        for tag in tags:
            tag_key = f"{self.tag_prefix}{tag}"
            try:
                if self._is_async_redis:
                    await self.redis.sadd(tag_key, key)
                else:
                    await asyncio.to_thread(self.redis.sadd, tag_key, key)
            except Exception as e:
                logger.error(f"Failed to tag key {key}: {e}")
    
    async def untag_key(self, key: str, tags: List[str]):
        """Remove key from tags."""
        if self.redis is None:
            return
        
        for tag in tags:
            tag_key = f"{self.tag_prefix}{tag}"
            try:
                if self._is_async_redis:
                    await self.redis.srem(tag_key, key)
                else:
                    await asyncio.to_thread(self.redis.srem, tag_key, key)
            except Exception as e:
                logger.error(f"Failed to untag key {key}: {e}")
    
    async def invalidate_by_tag(self, tag: str):
        """Invalidate all entries with a given tag."""
        if self.redis is None:
            return
        
        tag_key = f"{self.tag_prefix}{tag}"
        
        try:
            # Get all keys with this tag
            if self._is_async_redis:
                keys = await self.redis.smembers(tag_key)
            else:
                keys = await asyncio.to_thread(self.redis.smembers, tag_key)
            
            if keys:
                # Delete all cached values
                for key in keys:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    await self.cache.delete(key_str)
                
                # Clear the tag
                if self._is_async_redis:
                    await self.redis.delete(tag_key)
                else:
                    await asyncio.to_thread(self.redis.delete, tag_key)
                
                logger.info(f"Invalidated {len(keys)} entries for tag: {tag}")
        except Exception as e:
            logger.error(f"Failed to invalidate by tag {tag}: {e}")
    
    async def invalidate_by_tags(self, tags: List[str]):
        """Invalidate entries matching any of the tags."""
        for tag in tags:
            await self.invalidate_by_tag(tag)


class DependencyTracker:
    """
    Track dependencies between cached items for cascading invalidation.
    """
    
    def __init__(self, cache: MultiLevelCache, redis_client):
        self.cache = cache
        self.redis = redis_client
        self.dep_prefix = "cache:dep:"
        self._is_async_redis = False
        
        # Check if Redis client is async
        if self.redis is not None:
            try:
                if hasattr(self.redis, 'sadd') and asyncio.iscoroutinefunction(self.redis.sadd):
                    self._is_async_redis = True
            except Exception:
                pass
    
    async def add_dependency(self, key: str, depends_on: str):
        """Mark that key depends on another key."""
        if self.redis is None:
            return
        
        # Forward dependency: key depends on depends_on
        forward_key = f"{self.dep_prefix}forward:{key}"
        # Reverse dependency: depends_on has dependent key
        reverse_key = f"{self.dep_prefix}reverse:{depends_on}"
        
        try:
            if self._is_async_redis:
                await self.redis.sadd(forward_key, depends_on)
                await self.redis.sadd(reverse_key, key)
            else:
                await asyncio.to_thread(self.redis.sadd, forward_key, depends_on)
                await asyncio.to_thread(self.redis.sadd, reverse_key, key)
        except Exception as e:
            logger.error(f"Failed to add dependency: {e}")
    
    async def get_dependents(self, key: str) -> List[str]:
        """Get all keys that depend on this key."""
        if self.redis is None:
            return []
        
        reverse_key = f"{self.dep_prefix}reverse:{key}"
        
        try:
            if self._is_async_redis:
                dependents = await self.redis.smembers(reverse_key)
            else:
                dependents = await asyncio.to_thread(self.redis.smembers, reverse_key)
            
            return [
                d.decode() if isinstance(d, bytes) else d
                for d in dependents
            ]
        except Exception as e:
            logger.error(f"Failed to get dependents: {e}")
            return []
    
    async def invalidate_with_dependents(self, key: str):
        """Invalidate key and all its dependents (cascading)."""
        # Get dependents
        dependents = await self.get_dependents(key)
        
        # Invalidate the key
        await self.cache.delete(key)
        
        # Recursively invalidate dependents
        for dep in dependents:
            await self.invalidate_with_dependents(dep)
        
        # Clean up dependency tracking
        if self.redis is not None:
            try:
                forward_key = f"{self.dep_prefix}forward:{key}"
                reverse_key = f"{self.dep_prefix}reverse:{key}"
                
                if self._is_async_redis:
                    await self.redis.delete(forward_key, reverse_key)
                else:
                    await asyncio.to_thread(self.redis.delete, forward_key, reverse_key)
            except Exception as e:
                logger.error(f"Failed to clean up dependencies: {e}")


class EventBasedInvalidation:
    """
    Event-based cache invalidation.
    
    Listens to domain events and invalidates relevant cache entries.
    """
    
    def __init__(
        self,
        cache: MultiLevelCache,
        tag_invalidation: TagBasedInvalidation
    ):
        self.cache = cache
        self.tag_invalidation = tag_invalidation
        self.handlers: Dict[str, List[Callable]] = {}
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register invalidation handler for event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def handle_event(self, event_type: str, event_data: dict):
        """Handle a domain event and perform invalidation."""
        handlers = self.handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    # Run sync handler in thread
                    await asyncio.to_thread(handler, event_data)
            except Exception as e:
                logger.error(f"Invalidation handler error: {e}")
    
    def setup_default_handlers(self):
        """Set up default invalidation handlers."""
        # Quote events
        self.register_handler("quote.created", self._invalidate_quote)
        self.register_handler("quote.updated", self._invalidate_quote)
        self.register_handler("quote.accepted", self._invalidate_quote)
        
        # Policy events
        self.register_handler("policy.created", self._invalidate_policy)
        self.register_handler("policy.updated", self._invalidate_policy)
        self.register_handler("policy.cancelled", self._invalidate_policy)
        
        # Claim events
        self.register_handler("claim.filed", self._invalidate_claim)
        self.register_handler("claim.updated", self._invalidate_claim)
        self.register_handler("claim.approved", self._invalidate_claim)
    
    async def _invalidate_quote(self, event_data: dict):
        """Invalidate quote-related cache."""
        quote_id = event_data.get("quote_id")
        customer_id = event_data.get("customer_id")
        
        if quote_id:
            await self.cache.delete(f"quote:{quote_id}")
        
        if customer_id:
            await self.tag_invalidation.invalidate_by_tag(f"customer:{customer_id}:quotes")
    
    async def _invalidate_policy(self, event_data: dict):
        """Invalidate policy-related cache."""
        policy_id = event_data.get("policy_id")
        customer_id = event_data.get("customer_id")
        
        if policy_id:
            await self.cache.delete(f"policy:{policy_id}")
        
        if customer_id:
            await self.tag_invalidation.invalidate_by_tag(f"customer:{customer_id}:policies")
    
    async def _invalidate_claim(self, event_data: dict):
        """Invalidate claim-related cache."""
        claim_id = event_data.get("claim_id")
        policy_id = event_data.get("policy_id")
        
        if claim_id:
            await self.cache.delete(f"claim:{claim_id}")
        
        if policy_id:
            await self.tag_invalidation.invalidate_by_tag(f"policy:{policy_id}:claims")
