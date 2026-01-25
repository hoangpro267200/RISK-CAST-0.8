"""
Cache Warming Strategies

Features:
1. Startup warming
2. Predictive warming
3. Background refresh
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Callable, Dict, Any, Optional
from dataclasses import dataclass

from app.cache.multi_level import MultiLevelCache
from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class WarmingTask:
    """Definition of a cache warming task."""
    name: str
    loader: Callable
    keys: Optional[List[str]] = None  # Specific keys to warm
    key_generator: Optional[Callable] = None  # Generate keys dynamically
    priority: int = 0  # Higher = more important
    ttl: int = 3600


class CacheWarmer:
    """
    Warms cache with frequently accessed data.
    """
    
    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
        self.tasks: List[WarmingTask] = []
        self._warming = False
    
    def register_task(self, task: WarmingTask):
        """Register a warming task."""
        self.tasks.append(task)
        # Sort by priority
        self.tasks.sort(key=lambda t: t.priority, reverse=True)
    
    async def warm_all(self, concurrency: int = 5):
        """
        Warm all registered tasks.
        """
        if self._warming:
            logger.warning("Warming already in progress")
            return
        
        self._warming = True
        start_time = datetime.utcnow()
        total_warmed = 0
        
        logger.info(f"Starting cache warming with {len(self.tasks)} tasks")
        
        try:
            for task in self.tasks:
                warmed = await self._warm_task(task, concurrency)
                total_warmed += warmed
        finally:
            self._warming = False
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Cache warming completed: {total_warmed} entries in {duration:.2f}s"
        )
    
    async def _warm_task(self, task: WarmingTask, concurrency: int) -> int:
        """Execute a single warming task."""
        # Get keys to warm
        if task.keys:
            keys = task.keys
        elif task.key_generator:
            if asyncio.iscoroutinefunction(task.key_generator):
                keys = await task.key_generator()
            else:
                keys = await asyncio.to_thread(task.key_generator)
        else:
            logger.warning(f"Task {task.name} has no keys to warm")
            return 0
        
        logger.info(f"Warming task {task.name}: {len(keys)} keys")
        
        # Warm in batches
        semaphore = asyncio.Semaphore(concurrency)
        warmed = 0
        
        async def warm_key(key: str):
            nonlocal warmed
            async with semaphore:
                try:
                    # Load value
                    if asyncio.iscoroutinefunction(task.loader):
                        value = await task.loader(key)
                    else:
                        value = await asyncio.to_thread(task.loader, key)
                    
                    if value is not None:
                        await self.cache.set(key, value, l2_ttl=task.ttl)
                        warmed += 1
                except Exception as e:
                    logger.error(f"Failed to warm {key}: {e}")
        
        await asyncio.gather(*[warm_key(k) for k in keys])
        
        return warmed
    
    async def warm_specific(self, task_name: str):
        """Warm a specific task."""
        task = next((t for t in self.tasks if t.name == task_name), None)
        if task:
            await self._warm_task(task, concurrency=5)
        else:
            logger.warning(f"Task {task_name} not found")


class BackgroundRefresher:
    """
    Refreshes cache entries in the background before they expire.
    """
    
    def __init__(
        self,
        cache: MultiLevelCache,
        refresh_threshold: float = 0.2  # Refresh when 20% TTL remaining
    ):
        self.cache = cache
        self.refresh_threshold = refresh_threshold
        self.refresh_tasks: Dict[str, Callable] = {}
        self._running = False
    
    def register_refresher(self, key_pattern: str, loader: Callable):
        """Register a refresher for a key pattern."""
        self.refresh_tasks[key_pattern] = loader
    
    async def start(self, check_interval: int = 60):
        """Start background refresh loop."""
        self._running = True
        
        while self._running:
            try:
                await self._check_and_refresh()
            except Exception as e:
                logger.error(f"Background refresh error: {e}")
            
            await asyncio.sleep(check_interval)
    
    def stop(self):
        """Stop background refresh."""
        self._running = False
    
    async def _check_and_refresh(self):
        """Check entries and refresh those near expiration."""
        # This would need access to L1 cache entries
        # In a real implementation, track refresh candidates
        # For now, this is a placeholder
        pass


class PredictiveWarmer:
    """
    Predicts what data will be needed and warms proactively.
    """
    
    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
        self.access_history: Dict[str, List[datetime]] = {}
    
    def record_access(self, key: str):
        """Record an access for prediction."""
        if key not in self.access_history:
            self.access_history[key] = []
        
        self.access_history[key].append(datetime.utcnow())
        
        # Keep only recent history (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.access_history[key] = [
            t for t in self.access_history[key] if t > cutoff
        ]
    
    def get_hot_keys(self, top_n: int = 100) -> List[str]:
        """Get most frequently accessed keys."""
        key_counts = [
            (key, len(accesses))
            for key, accesses in self.access_history.items()
        ]
        
        key_counts.sort(key=lambda x: x[1], reverse=True)
        
        return [key for key, _ in key_counts[:top_n]]
    
    async def warm_hot_keys(self, loader: Callable):
        """Warm hot keys proactively."""
        hot_keys = self.get_hot_keys()
        
        for key in hot_keys:
            # Check if not in cache
            cached = await self.cache.get(key)
            if cached is None:
                try:
                    if asyncio.iscoroutinefunction(loader):
                        value = await loader(key)
                    else:
                        value = await asyncio.to_thread(loader, key)
                    
                    if value is not None:
                        await self.cache.set(key, value)
                except Exception as e:
                    logger.error(f"Failed to warm hot key {key}: {e}")
