"""
Advanced Caching Strategies

Features:
1. Multi-level caching (L1 local + L2 Redis)
2. Cache-aside pattern
3. Tag-based invalidation
4. Event-based invalidation
5. Cache warming
"""

from app.cache.multi_level import (
    MultiLevelCache,
    LRUCache,
    CacheEntry,
    CacheStats,
    cached,
)

from app.cache.cache_aside import (
    CacheAside,
    QueryCache,
)

from app.cache.invalidation import (
    TagBasedInvalidation,
    DependencyTracker,
    EventBasedInvalidation,
)

from app.cache.warming import (
    CacheWarmer,
    WarmingTask,
    BackgroundRefresher,
    PredictiveWarmer,
)

__all__ = [
    "MultiLevelCache",
    "LRUCache",
    "CacheEntry",
    "CacheStats",
    "cached",
    "CacheAside",
    "QueryCache",
    "TagBasedInvalidation",
    "DependencyTracker",
    "EventBasedInvalidation",
    "CacheWarmer",
    "WarmingTask",
    "BackgroundRefresher",
    "PredictiveWarmer",
]
