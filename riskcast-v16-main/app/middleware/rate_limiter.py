"""
API Rate Limiting & Throttling

Features:
1. Per-customer rate limits
2. Tiered limits by plan
3. Burst handling
4. Rate limit headers
5. Quota tracking
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
import time
import os

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Try to import Redis, with graceful fallback
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

# Type alias for Redis client (for type hints)
if REDIS_AVAILABLE:
    RedisClient = aioredis.Redis
else:
    RedisClient = type(None)  # Placeholder type when redis not available


class RateLimitTier(Enum):
    """Rate limit tiers."""
    FREE = "FREE"
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit tier."""
    requests_per_second: int
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_size: int  # Maximum burst above normal rate


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    limit: int
    reset_at: datetime
    retry_after: Optional[int] = None  # Seconds to wait if limited


class RateLimiter:
    """
    Token bucket rate limiter with Redis backend.
    
    Uses sliding window algorithm for accurate rate limiting.
    Falls back to in-memory if Redis unavailable.
    """
    
    # Default configurations by tier
    TIER_CONFIGS = {
        RateLimitTier.FREE: RateLimitConfig(
            requests_per_second=1,
            requests_per_minute=30,
            requests_per_hour=500,
            requests_per_day=1000,
            burst_size=5
        ),
        RateLimitTier.STARTER: RateLimitConfig(
            requests_per_second=5,
            requests_per_minute=100,
            requests_per_hour=2000,
            requests_per_day=10000,
            burst_size=20
        ),
        RateLimitTier.PROFESSIONAL: RateLimitConfig(
            requests_per_second=20,
            requests_per_minute=500,
            requests_per_hour=10000,
            requests_per_day=100000,
            burst_size=50
        ),
        RateLimitTier.ENTERPRISE: RateLimitConfig(
            requests_per_second=100,
            requests_per_minute=2000,
            requests_per_hour=50000,
            requests_per_day=1000000,
            burst_size=200
        )
    }
    
    # Endpoint-specific limits (multiplier relative to base)
    ENDPOINT_MULTIPLIERS = {
        "/api/v3/risk/assess": 0.5,  # More expensive operation
        "/api/v3/quotes/request": 0.5,
        "/api/v3/compliance/export": 0.1,
        "/api/v3/analytics": 0.2,
    }
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        prefix: str = "ratelimit",
        use_redis: bool = True
    ):
        self.redis = redis_client
        self.prefix = prefix
        self.use_redis = use_redis and REDIS_AVAILABLE and redis_client is not None
        self.logger = logging.getLogger(__name__)
        
        # In-memory fallback storage
        self._memory_store: Dict[str, Dict[str, Any]] = {}
    
    async def check_rate_limit(
        self,
        identifier: str,
        tier: RateLimitTier,
        endpoint: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limits.
        
        Uses sliding window counter algorithm.
        """
        config = self.TIER_CONFIGS[tier]
        
        # Apply endpoint-specific multiplier
        multiplier = 1.0
        if endpoint:
            for pattern, mult in self.ENDPOINT_MULTIPLIERS.items():
                if endpoint.startswith(pattern):
                    multiplier = mult
                    break
        
        # Adjust limits
        limit_per_minute = int(config.requests_per_minute * multiplier)
        
        if self.use_redis and self.redis:
            return await self._check_redis_rate_limit(identifier, limit_per_minute, config.requests_per_day)
        else:
            return await self._check_memory_rate_limit(identifier, limit_per_minute, config.requests_per_day)
    
    async def _check_redis_rate_limit(
        self,
        identifier: str,
        limit_per_minute: int,
        limit_per_day: int
    ) -> RateLimitResult:
        """Check rate limit using Redis."""
        try:
            # Check minute window (primary limit)
            key = f"{self.prefix}:{identifier}:minute"
            now = time.time()
            window_start = now - 60
            
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current entries
            pipe.zcard(key)
            
            # Add current request (we'll remove if over limit)
            import uuid
            request_id = f"{now}:{uuid.uuid4().hex[:8]}"
            pipe.zadd(key, {request_id: now})
            
            # Set expiry
            pipe.expire(key, 120)
            
            results = await pipe.execute()
            current_count = results[1]
            
            if current_count >= limit_per_minute:
                # Remove the request we just added
                await self.redis.zrem(key, request_id)
                
                # Calculate retry after
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(60 - (now - oldest_time)) + 1
                else:
                    retry_after = 60
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=limit_per_minute,
                    reset_at=datetime.utcnow() + timedelta(seconds=retry_after),
                    retry_after=retry_after
                )
            
            # Also check daily limit
            daily_allowed = await self._check_daily_limit_redis(identifier, limit_per_day)
            if not daily_allowed:
                await self.redis.zrem(key, request_id)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=limit_per_day,
                    reset_at=self._get_day_reset(),
                    retry_after=self._seconds_until_day_reset()
                )
            
            return RateLimitResult(
                allowed=True,
                remaining=limit_per_minute - current_count - 1,
                limit=limit_per_minute,
                reset_at=datetime.utcnow() + timedelta(seconds=60)
            )
        except Exception as e:
            self.logger.warning(f"Redis rate limit check failed: {e}, allowing request")
            # Fail open - allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                remaining=limit_per_minute,
                limit=limit_per_minute,
                reset_at=datetime.utcnow() + timedelta(seconds=60)
            )
    
    async def _check_memory_rate_limit(
        self,
        identifier: str,
        limit_per_minute: int,
        limit_per_day: int
    ) -> RateLimitResult:
        """Check rate limit using in-memory storage."""
        now = time.time()
        
        # Initialize storage for identifier
        if identifier not in self._memory_store:
            self._memory_store[identifier] = {
                "minute_requests": [],
                "daily_count": 0,
                "daily_reset": self._get_day_reset()
            }
        
        store = self._memory_store[identifier]
        
        # Check daily reset
        if datetime.utcnow() >= store["daily_reset"]:
            store["daily_count"] = 0
            store["daily_reset"] = self._get_day_reset()
        
        # Check daily limit
        if store["daily_count"] >= limit_per_day:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=limit_per_day,
                reset_at=store["daily_reset"],
                retry_after=self._seconds_until_day_reset()
            )
        
        # Clean old minute requests
        store["minute_requests"] = [
            ts for ts in store["minute_requests"]
            if now - ts < 60
        ]
        
        # Check minute limit
        if len(store["minute_requests"]) >= limit_per_minute:
            oldest = min(store["minute_requests"])
            retry_after = int(60 - (now - oldest)) + 1
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=limit_per_minute,
                reset_at=datetime.utcnow() + timedelta(seconds=retry_after),
                retry_after=retry_after
            )
        
        # Allow request
        store["minute_requests"].append(now)
        store["daily_count"] += 1
        
        return RateLimitResult(
            allowed=True,
            remaining=limit_per_minute - len(store["minute_requests"]),
            limit=limit_per_minute,
            reset_at=datetime.utcnow() + timedelta(seconds=60)
        )
    
    async def _check_daily_limit_redis(self, identifier: str, limit: int) -> bool:
        """Check daily rate limit using Redis."""
        try:
            key = f"{self.prefix}:{identifier}:daily:{datetime.utcnow().strftime('%Y%m%d')}"
            
            current = await self.redis.incr(key)
            
            if current == 1:
                # First request of the day, set expiry
                await self.redis.expire(key, 86400 + 3600)  # 25 hours for safety
            
            return current <= limit
        except Exception as e:
            self.logger.warning(f"Redis daily limit check failed: {e}")
            return True  # Fail open
    
    async def get_usage_stats(self, identifier: str) -> Dict[str, Any]:
        """Get current usage statistics."""
        if self.use_redis and self.redis:
            return await self._get_usage_stats_redis(identifier)
        else:
            return await self._get_usage_stats_memory(identifier)
    
    async def _get_usage_stats_redis(self, identifier: str) -> Dict[str, Any]:
        """Get usage stats from Redis."""
        try:
            now = time.time()
            day_key = datetime.utcnow().strftime('%Y%m%d')
            
            pipe = self.redis.pipeline()
            
            # Minute count
            minute_key = f"{self.prefix}:{identifier}:minute"
            pipe.zcount(minute_key, now - 60, now)
            
            # Daily count
            daily_key = f"{self.prefix}:{identifier}:daily:{day_key}"
            pipe.get(daily_key)
            
            results = await pipe.execute()
            
            return {
                "requests_last_minute": results[0] or 0,
                "requests_today": int(results[1] or 0),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Failed to get usage stats: {e}")
            return {
                "requests_last_minute": 0,
                "requests_today": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_usage_stats_memory(self, identifier: str) -> Dict[str, Any]:
        """Get usage stats from memory."""
        if identifier not in self._memory_store:
            return {
                "requests_last_minute": 0,
                "requests_today": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        store = self._memory_store[identifier]
        now = time.time()
        
        # Count requests in last minute
        minute_requests = [
            ts for ts in store["minute_requests"]
            if now - ts < 60
        ]
        
        return {
            "requests_last_minute": len(minute_requests),
            "requests_today": store["daily_count"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_day_reset(self) -> datetime:
        """Get next day reset time (midnight UTC)."""
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        return datetime.combine(tomorrow, datetime.min.time())
    
    def _seconds_until_day_reset(self) -> int:
        """Get seconds until day reset."""
        return int((self._get_day_reset() - datetime.utcnow()).total_seconds())


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    """
    
    def __init__(
        self,
        app,
        redis_client: Optional[Any] = None,
        get_identifier_func=None,
        get_tier_func=None
    ):
        super().__init__(app)
        self.limiter = RateLimiter(redis_client=redis_client)
        self.get_identifier = get_identifier_func or self._default_get_identifier
        self.get_tier = get_tier_func or self._default_get_tier
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for certain paths
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(p) for p in skip_paths):
            return await call_next(request)
        
        # Get identifier (customer ID, API key, or IP)
        identifier = await self.get_identifier(request)
        
        # Get tier
        tier = await self.get_tier(request)
        
        # Check rate limit
        result = await self.limiter.check_rate_limit(
            identifier=identifier,
            tier=tier,
            endpoint=request.url.path
        )
        
        if not result.allowed:
            response = Response(
                content=f'{{"error": "Rate limit exceeded", "retry_after": {result.retry_after}}}',
                status_code=429,
                media_type="application/json"
            )
            self._add_rate_limit_headers(response, result)
            return response
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Track usage (async, don't wait)
        asyncio.create_task(
            self._track_usage(identifier, request.url.path, request.method, response_time_ms, response.status_code)
        )
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, result)
        
        return response
    
    def _add_rate_limit_headers(self, response: Response, result: RateLimitResult):
        """Add standard rate limit headers."""
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_at.timestamp()))
        
        if result.retry_after:
            response.headers["Retry-After"] = str(result.retry_after)
    
    async def _track_usage(
        self,
        identifier: str,
        endpoint: str,
        method: str,
        response_time_ms: int,
        status_code: int
    ):
        """Track API usage for analytics."""
        try:
            if hasattr(self.limiter, 'redis') and self.limiter.redis:
                tracker = UsageTracker(self.limiter.redis)
                # Extract tenant_id from identifier if it's tenant-based
                tenant_id = identifier.split(":")[-1] if ":" in identifier else identifier
                await tracker.track_request(tenant_id, endpoint, method, response_time_ms, status_code)
        except Exception as e:
            self.limiter.logger.warning(f"Failed to track usage: {e}")
    
    async def _default_get_identifier(self, request: Request) -> str:
        """Default identifier extraction."""
        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:16]}"
        
        # Try tenant
        tenant = getattr(request.state, "tenant", None)
        if tenant:
            return f"tenant:{tenant.id}"
        
        # Try tenant_id from state
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            return f"tenant:{tenant_id}"
        
        # Try user
        user = getattr(request.state, "user", None)
        if user:
            return f"user:{user.id}"
        
        # Fallback to IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def _default_get_tier(self, request: Request) -> RateLimitTier:
        """Default tier determination."""
        # Check tenant plan
        tenant = getattr(request.state, "tenant", None)
        if tenant and hasattr(tenant, "plan"):
            plan_mapping = {
                "STARTER": RateLimitTier.STARTER,
                "PROFESSIONAL": RateLimitTier.PROFESSIONAL,
                "ENTERPRISE": RateLimitTier.ENTERPRISE
            }
            return plan_mapping.get(tenant.plan, RateLimitTier.STARTER)
        
        # Check API key tier (would look up in database)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Would look up tier from API key
            return RateLimitTier.STARTER
        
        # Default for unauthenticated
        return RateLimitTier.FREE


# ============================================================================
# Usage Tracking
# ============================================================================

class UsageTracker:
    """
    Tracks API usage for billing and analytics.
    """
    
    def __init__(self, redis_client: Any):
        self.redis = redis_client
        self.prefix = "usage"
    
    async def track_request(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        response_time_ms: int,
        status_code: int
    ):
        """Track a single request."""
        try:
            now = datetime.utcnow()
            day_key = now.strftime('%Y%m%d')
            hour_key = now.strftime('%Y%m%d%H')
            
            pipe = self.redis.pipeline()
            
            # Increment counters
            pipe.hincrby(f"{self.prefix}:daily:{tenant_id}:{day_key}", "total", 1)
            pipe.hincrby(f"{self.prefix}:daily:{tenant_id}:{day_key}", f"status:{status_code // 100}xx", 1)
            pipe.hincrby(f"{self.prefix}:hourly:{tenant_id}:{hour_key}", "total", 1)
            
            # Track response time (for percentiles)
            pipe.lpush(f"{self.prefix}:latency:{tenant_id}:{hour_key}", response_time_ms)
            pipe.ltrim(f"{self.prefix}:latency:{tenant_id}:{hour_key}", 0, 999)
            
            # Endpoint-specific tracking
            pipe.hincrby(f"{self.prefix}:endpoints:{tenant_id}:{day_key}", endpoint, 1)
            
            # Set expiries
            pipe.expire(f"{self.prefix}:daily:{tenant_id}:{day_key}", 86400 * 35)  # 35 days
            pipe.expire(f"{self.prefix}:hourly:{tenant_id}:{hour_key}", 86400 * 3)  # 3 days
            pipe.expire(f"{self.prefix}:latency:{tenant_id}:{hour_key}", 86400 * 3)
            pipe.expire(f"{self.prefix}:endpoints:{tenant_id}:{day_key}", 86400 * 35)
            
            await pipe.execute()
        except Exception as e:
            # Fail silently - don't break requests if tracking fails
            logging.getLogger(__name__).warning(f"Usage tracking failed: {e}")
    
    async def get_daily_usage(self, tenant_id: str, date_str: str) -> Dict[str, Any]:
        """Get usage for a specific day."""
        try:
            key = f"{self.prefix}:daily:{tenant_id}:{date_str}"
            data = await self.redis.hgetall(key)
            
            return {
                "date": date_str,
                "total_requests": int(data.get(b"total", 0) or data.get("total", 0)),
                "status_2xx": int(data.get(b"status:2xx", 0) or data.get("status:2xx", 0)),
                "status_4xx": int(data.get(b"status:4xx", 0) or data.get("status:4xx", 0)),
                "status_5xx": int(data.get(b"status:5xx", 0) or data.get("status:5xx", 0))
            }
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to get daily usage: {e}")
            return {
                "date": date_str,
                "total_requests": 0,
                "status_2xx": 0,
                "status_4xx": 0,
                "status_5xx": 0
            }
    
    async def get_monthly_usage(self, tenant_id: str, year: int, month: int) -> Dict[str, Any]:
        """Get usage for a month."""
        from calendar import monthrange
        
        try:
            _, days_in_month = monthrange(year, month)
            
            total = 0
            daily_data = []
            
            for day in range(1, days_in_month + 1):
                date_str = f"{year}{month:02d}{day:02d}"
                usage = await self.get_daily_usage(tenant_id, date_str)
                total += usage["total_requests"]
                daily_data.append(usage)
            
            return {
                "year": year,
                "month": month,
                "total_requests": total,
                "daily_breakdown": daily_data
            }
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to get monthly usage: {e}")
            return {
                "year": year,
                "month": month,
                "total_requests": 0,
                "daily_breakdown": []
            }
