"""
Advanced rate limiting with Redis backend.
Supports distributed deployments and per-user quotas.

RISKCAST v17 - Production Excellence
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import hashlib
from typing import Optional, Dict
import os

# Try to import redis, graceful fallback if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class AdvancedRateLimiter(BaseHTTPMiddleware):
    """
    Distributed rate limiter using Redis.
    
    Features:
    - Per-user rate limits (by API key or IP)
    - Per-endpoint rate limits
    - Sliding window algorithm
    - Graceful degradation if Redis unavailable
    
    Usage:
        from app.middleware.advanced_rate_limit import AdvancedRateLimiter
        app.add_middleware(AdvancedRateLimiter)
    """
    
    def __init__(self, app, redis_url: Optional[str] = None):
        super().__init__(app)
        
        self.redis_client = None
        self.redis_available = False
        
        # Initialize Redis if available
        if REDIS_AVAILABLE:
            try:
                url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(url)
                self.redis_client.ping()
                self.redis_available = True
                print("[AdvancedRateLimiter] ✅ Redis connected")
            except Exception as e:
                print(f"[AdvancedRateLimiter] ⚠️ Redis unavailable: {e}")
                self.redis_available = False
        else:
            print("[AdvancedRateLimiter] ⚠️ redis-py not installed, using in-memory fallback")
        
        # In-memory fallback store
        self._memory_store: Dict[str, list] = {}
        
        # Rate limit configurations per endpoint
        self.rate_limits = {
            # Risk analysis - computationally expensive
            '/api/v1/risk/v2/analyze': {'requests': 10, 'window': 60},
            '/api/v2/risk/analyze': {'requests': 10, 'window': 60},
            
            # AI advisor - API cost
            '/api/v1/ai/advisor/chat': {'requests': 20, 'window': 60},
            '/api/v1/ai/advisor/chat/stream': {'requests': 15, 'window': 60},
            
            # Scenarios - moderate load
            '/api/v2/risk/scenarios': {'requests': 5, 'window': 60},
            
            # State management - high frequency
            '/api/v2/state': {'requests': 60, 'window': 60},
            
            # Default for other endpoints
            'default': {'requests': 100, 'window': 60}
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Check rate limit before processing request."""
        
        # Skip rate limiting for certain paths
        skip_paths = ['/health', '/metrics', '/docs', '/openapi.json', '/favicon.ico']
        if any(request.url.path.startswith(p) for p in skip_paths):
            return await call_next(request)
        
        # Skip for static assets
        if request.url.path.startswith('/static') or request.url.path.startswith('/assets'):
            return await call_next(request)
        
        # Get user identifier
        user_id = self._get_user_identifier(request)
        
        # Get rate limit for this endpoint
        endpoint = request.url.path
        rate_config = self._get_rate_config(endpoint)
        
        # Check rate limit
        allowed, remaining = self._check_rate_limit(
            user_id=user_id,
            endpoint=endpoint,
            max_requests=rate_config['requests'],
            window_seconds=rate_config['window']
        )
        
        if not allowed:
            # Rate limit exceeded
            retry_after = self._get_retry_after(user_id, endpoint, rate_config['window'])
            raise HTTPException(
                status_code=429,
                detail={
                    'error': 'Rate limit exceeded',
                    'limit': rate_config['requests'],
                    'window_seconds': rate_config['window'],
                    'retry_after': retry_after
                },
                headers={
                    'Retry-After': str(retry_after),
                    'X-RateLimit-Limit': str(rate_config['requests']),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(time.time()) + retry_after)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers['X-RateLimit-Limit'] = str(rate_config['requests'])
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Reset'] = str(int(time.time()) + rate_config['window'])
        
        return response
    
    def _get_user_identifier(self, request: Request) -> str:
        """Get unique user identifier from request."""
        # Priority 1: API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        
        # Priority 2: Authorization header
        auth = request.headers.get('Authorization')
        if auth:
            return f"auth:{hashlib.sha256(auth.encode()).hexdigest()[:16]}"
        
        # Priority 3: Session ID
        session_id = request.cookies.get('session')
        if session_id:
            return f"session:{session_id[:16]}"
        
        # Priority 4: IP address (fallback)
        client_host = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_host = forwarded_for.split(',')[0].strip()
        
        return f"ip:{client_host}"
    
    def _get_rate_config(self, endpoint: str) -> dict:
        """Get rate limit configuration for endpoint."""
        # Exact match first
        if endpoint in self.rate_limits:
            return self.rate_limits[endpoint]
        
        # Prefix match
        for path, config in self.rate_limits.items():
            if path != 'default' and endpoint.startswith(path):
                return config
        
        return self.rate_limits['default']
    
    def _check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple:
        """
        Check if request is within rate limit using sliding window.
        
        Returns:
            (allowed: bool, remaining: int)
        """
        if self.redis_available and self.redis_client:
            return self._check_redis_rate_limit(
                user_id, endpoint, max_requests, window_seconds
            )
        else:
            return self._check_memory_rate_limit(
                user_id, endpoint, max_requests, window_seconds
            )
    
    def _check_redis_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple:
        """Redis-based sliding window rate limiter."""
        key = f"ratelimit:{user_id}:{endpoint.replace('/', '_')}"
        now = time.time()
        window_start = now - window_seconds
        
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            request_count = results[1]
            
            allowed = request_count < max_requests
            remaining = max(0, max_requests - request_count - 1)
            
            return allowed, remaining
        except Exception as e:
            # Fallback to allow if Redis fails
            print(f"[AdvancedRateLimiter] Redis error: {e}")
            return True, max_requests
    
    def _check_memory_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple:
        """In-memory fallback rate limiter."""
        key = f"{user_id}:{endpoint}"
        now = time.time()
        
        if key not in self._memory_store:
            self._memory_store[key] = []
        
        # Remove old entries
        self._memory_store[key] = [
            timestamp for timestamp in self._memory_store[key]
            if timestamp > now - window_seconds
        ]
        
        request_count = len(self._memory_store[key])
        
        # Check count
        if request_count >= max_requests:
            return False, 0
        
        # Add current request
        self._memory_store[key].append(now)
        remaining = max_requests - request_count - 1
        
        return True, remaining
    
    def _get_retry_after(self, user_id: str, endpoint: str, window_seconds: int) -> int:
        """Get seconds until rate limit resets."""
        if self.redis_available and self.redis_client:
            try:
                key = f"ratelimit:{user_id}:{endpoint.replace('/', '_')}"
                ttl = self.redis_client.ttl(key)
                return max(1, ttl) if ttl > 0 else window_seconds
            except Exception:
                pass
        
        return window_seconds
    
    def update_rate_limit(self, endpoint: str, requests: int, window: int):
        """Dynamically update rate limit for an endpoint."""
        self.rate_limits[endpoint] = {'requests': requests, 'window': window}
    
    def get_usage_stats(self, user_id: str) -> dict:
        """Get rate limit usage statistics for a user."""
        stats = {}
        
        for endpoint, config in self.rate_limits.items():
            if endpoint == 'default':
                continue
            
            key = f"{user_id}:{endpoint}"
            
            if self.redis_available and self.redis_client:
                try:
                    redis_key = f"ratelimit:{user_id}:{endpoint.replace('/', '_')}"
                    count = self.redis_client.zcard(redis_key)
                    stats[endpoint] = {
                        'used': count,
                        'limit': config['requests'],
                        'remaining': max(0, config['requests'] - count)
                    }
                except Exception:
                    pass
            elif key in self._memory_store:
                count = len(self._memory_store[key])
                stats[endpoint] = {
                    'used': count,
                    'limit': config['requests'],
                    'remaining': max(0, config['requests'] - count)
                }
        
        return stats
