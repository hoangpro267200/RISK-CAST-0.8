# Advanced Caching Strategies

Multi-level caching system with L1 (local) and L2 (Redis) support, cache-aside pattern, invalidation strategies, and cache warming.

## Features

1. **Multi-Level Cache**: L1 (in-memory LRU) + L2 (Redis)
2. **Cache-Aside Pattern**: Read-through and write-around caching
3. **Tag-Based Invalidation**: Group and invalidate by tags
4. **Dependency Tracking**: Cascading invalidation
5. **Event-Based Invalidation**: Automatic invalidation on domain events
6. **Cache Warming**: Startup and predictive warming
7. **Background Refresh**: Refresh entries before expiration

## Architecture

### Multi-Level Cache

- **L1 (Local)**: Fast, thread-safe LRU cache, limited size (default: 1000)
- **L2 (Redis)**: Distributed cache, larger capacity, shared across processes
- **Automatic Promotion**: L2 hits are promoted to L1
- **TTL Management**: Separate TTLs for L1 and L2

### Cache-Aside Pattern

- **Read**: Check cache → If miss, load from DB → Cache result
- **Write**: Update DB → Invalidate cache
- **Query Cache**: Cache database query results with parameter hashing

### Invalidation Strategies

1. **Tag-Based**: Group entries by tags, invalidate by tag
2. **Dependency-Based**: Track dependencies, cascade invalidation
3. **Event-Based**: Listen to domain events, invalidate automatically

### Cache Warming

1. **Startup Warming**: Pre-load frequently accessed data on startup
2. **Predictive Warming**: Warm based on access patterns
3. **Background Refresh**: Refresh entries before expiration

## Usage

### Basic Multi-Level Cache

```python
import redis.asyncio as redis
from app.cache import MultiLevelCache

# Initialize Redis client
redis_client = redis.from_url("redis://localhost:6379/0")

# Create cache
cache = MultiLevelCache(
    redis_client=redis_client,
    l1_max_size=1000,
    l1_default_ttl=60,  # 1 minute
    l2_default_ttl=3600,  # 1 hour
    key_prefix="cache:",
    serializer="json"  # or "pickle"
)

# Get value
value = await cache.get("user:123")

# Set value
await cache.set("user:123", user_data, l1_ttl=30, l2_ttl=300)

# Get or set (with factory)
value = await cache.get_or_set(
    "user:123",
    lambda: load_user_from_db("123"),
    l1_ttl=30,
    l2_ttl=300
)
```

### Cache-Aside Pattern

```python
from app.cache import CacheAside, MultiLevelCache

# Create cache-aside for entities
user_cache = CacheAside(
    cache=cache,
    key_prefix="user",
    loader=lambda user_id: db.query(User).filter(User.id == user_id).first(),
    l1_ttl=60,
    l2_ttl=3600
)

# Get user (loads from DB if not cached)
user = await user_cache.get("user-123")

# Invalidate on update
await user_cache.invalidate("user-123")

# Refresh
user = await user_cache.refresh("user-123")
```

### Query Cache

```python
from app.cache import QueryCache

query_cache = QueryCache(cache, key_prefix="query", default_ttl=300)

# Cache query results
result = await query_cache.get(
    query_name="user_by_email",
    params={"email": "user@example.com"},
    executor=lambda p: db.query(User).filter(User.email == p["email"]).first(),
    ttl=600
)

# Invalidate all results for a query
await query_cache.invalidate("user_by_email")
```

### Tag-Based Invalidation

```python
from app.cache import TagBasedInvalidation

tag_invalidation = TagBasedInvalidation(cache, redis_client)

# Tag a key
await tag_invalidation.tag_key("user:123", ["customer:456", "tenant:789"])

# Invalidate by tag
await tag_invalidation.invalidate_by_tag("customer:456")

# Invalidate by multiple tags
await tag_invalidation.invalidate_by_tags(["customer:456", "tenant:789"])
```

### Dependency Tracking

```python
from app.cache import DependencyTracker

dep_tracker = DependencyTracker(cache, redis_client)

# Add dependency
await dep_tracker.add_dependency("quote:123", "customer:456")

# Invalidate with cascading
await dep_tracker.invalidate_with_dependents("customer:456")
# This will also invalidate "quote:123"
```

### Event-Based Invalidation

```python
from app.cache import EventBasedInvalidation, TagBasedInvalidation

event_invalidation = EventBasedInvalidation(cache, tag_invalidation)

# Set up default handlers
event_invalidation.setup_default_handlers()

# Handle domain event
await event_invalidation.handle_event(
    "quote.created",
    {"quote_id": "quote-123", "customer_id": "customer-456"}
)

# Register custom handler
async def custom_handler(event_data: dict):
    await cache.delete(f"custom:{event_data['id']}")

event_invalidation.register_handler("custom.event", custom_handler)
```

### Cache Warming

```python
from app.cache import CacheWarmer, WarmingTask

warmer = CacheWarmer(cache)

# Register warming task
warmer.register_task(WarmingTask(
    name="warm_users",
    loader=lambda user_id: db.query(User).filter(User.id == user_id).first(),
    keys=["user-1", "user-2", "user-3"],
    priority=10,
    ttl=3600
))

# Or with dynamic key generation
async def get_active_user_ids():
    return [u.id for u in db.query(User).filter(User.active == True).all()]

warmer.register_task(WarmingTask(
    name="warm_active_users",
    loader=lambda user_id: db.query(User).filter(User.id == user_id).first(),
    key_generator=get_active_user_ids,
    priority=5,
    ttl=3600
))

# Warm all tasks
await warmer.warm_all(concurrency=5)

# Warm specific task
await warmer.warm_specific("warm_users")
```

### Predictive Warming

```python
from app.cache import PredictiveWarmer

predictive = PredictiveWarmer(cache)

# Record accesses
predictive.record_access("user:123")
predictive.record_access("user:456")

# Get hot keys
hot_keys = predictive.get_hot_keys(top_n=100)

# Warm hot keys
async def load_user(user_id: str):
    return db.query(User).filter(User.id == user_id).first()

await predictive.warm_hot_keys(load_user)
```

### Cache Decorator

```python
from app.cache import cached

@cached("user:{user_id}", l1_ttl=30, l2_ttl=300)
async def get_user(user_id: str, _cache=None):
    return db.query(User).filter(User.id == user_id).first()
```

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Cache settings
CACHE_L1_MAX_SIZE=1000
CACHE_L1_DEFAULT_TTL=60
CACHE_L2_DEFAULT_TTL=3600
CACHE_KEY_PREFIX=cache:
CACHE_SERIALIZER=json  # or pickle
```

## Statistics

```python
stats = cache.get_stats()
print(stats)
# {
#     "l1": {
#         "size": 500,
#         "max_size": 1000,
#         "hits": 1000,
#         "misses": 200,
#         "hit_rate": "83.33%"
#     },
#     "l2": {
#         "hits": 150,
#         "misses": 50,
#         "hit_rate": "75.00%"
#     },
#     "overall": {
#         "writes": 400,
#         "hit_rate": "88.33%"
#     }
# }
```

## Best Practices

1. **Key Naming**: Use consistent prefixes and separators (e.g., `user:123`, `quote:456`)
2. **TTL Strategy**: Shorter TTL for frequently changing data, longer for stable data
3. **Invalidation**: Invalidate on writes, use tags for bulk invalidation
4. **Warming**: Warm frequently accessed data on startup
5. **Monitoring**: Track hit rates and adjust TTLs accordingly
6. **Serialization**: Use JSON for simple data, pickle for complex objects

## Dependencies

- `redis` (optional): For L2 cache backend
- Standard library: `asyncio`, `json`, `pickle`, `threading`

## Notes

- L1 cache is thread-safe using `threading.RLock`
- L2 cache supports both sync and async Redis clients
- Cache automatically falls back to L1-only if Redis is unavailable
- Serialization falls back to pickle if JSON fails
