"""
Rate Limiting Middleware (Phase 6 - Day 16)

CRITICAL: Prevents abuse and ensures fair resource usage.
Applies rate limits to all API endpoints.
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


# Rate limit storage (in-memory, use Redis in production)
_rate_limit_storage: Dict[str, Dict[str, Tuple[float, int]]] = defaultdict(dict)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    
    Limits:
    - Default: 100 requests per minute per IP
    - Risk analysis: 10 requests per minute per IP
    - AI advisor: 20 requests per minute per IP
    """
    
    # Rate limits (requests per window_seconds)
    RATE_LIMITS = {
        "/api/v1/risk/v2/analyze": (10, 60),  # 10 req/min
        "/api/v1/risk/v2/simulate": (10, 60),  # 10 req/min
        "/api/v1/risk/v2/report/pdf": (5, 60),  # 5 req/min
        "/api/ai": (20, 60),  # 20 req/min
        "/api/ai/stream": (10, 60),  # 10 req/min
        "default": (100, 60),  # 100 req/min for other endpoints
    }
    
    def __init__(self, app, storage=None):
        super().__init__(app)
        # Use provided storage or in-memory default
        self.storage = storage or _rate_limit_storage
    
    async def dispatch(self, request: Request, call_next):
        """
        Apply rate limiting to request.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response (or 429 if rate limit exceeded)
        """
        # Skip rate limiting for static files
        path = request.url.path
        if path.startswith(("/assets/", "/static/", "/dist/", "/metrics", "/health")):
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        
        # Determine rate limit for this endpoint
        limit, window_seconds = self._get_rate_limit(path)
        
        # Check rate limit
        if not self._check_rate_limit(client_ip, path, limit, window_seconds):
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded: {client_ip} -> {path}",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "client_ip": client_ip,
                    "path": path,
                    "limit": limit,
                    "window": window_seconds,
                }
            )
            
            # Return 429 Too Many Requests
            from app.utils.standard_responses import StandardResponse
            return StandardResponse.error(
                message=f"Rate limit exceeded: {limit} requests per {window_seconds} seconds",
                error_code="RATE_LIMIT_EXCEEDED",
                status_code=429,
                error_type="client",
                request=request
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining, reset_time = self._get_rate_limit_info(client_ip, path, limit, window_seconds)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check X-Forwarded-For header (for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP (client IP)
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_rate_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for endpoint"""
        # Check exact path match
        if path in self.RATE_LIMITS:
            return self.RATE_LIMITS[path]
        
        # Check prefix match (for /api/ai/*)
        for endpoint, limits in self.RATE_LIMITS.items():
            if endpoint != "default" and path.startswith(endpoint):
                return limits
        
        # Default limit
        return self.RATE_LIMITS["default"]
    
    def _check_rate_limit(self, client_ip: str, path: str, limit: int, window_seconds: int) -> bool:
        """
        Check if request is within rate limit.
        
        Returns:
            True if within limit, False if exceeded
        """
        key = f"{client_ip}:{path}"
        now = time.time()
        
        # Get current count and window start
        if key in self.storage:
            window_start, count = self.storage[key]
            
            # Check if window has expired
            if now - window_start < window_seconds:
                # Still in window
                if count >= limit:
                    return False  # Rate limit exceeded
                # Increment count
                self.storage[key] = (window_start, count + 1)
            else:
                # New window
                self.storage[key] = (now, 1)
        else:
            # First request
            self.storage[key] = (now, 1)
        
        return True
    
    def _get_rate_limit_info(self, client_ip: str, path: str, limit: int, window_seconds: int) -> Tuple[int, float]:
        """Get remaining requests and reset time"""
        key = f"{client_ip}:{path}"
        now = time.time()
        
        if key in self.storage:
            window_start, count = self.storage[key]
            
            if now - window_start < window_seconds:
                remaining = max(0, limit - count)
                reset_time = window_start + window_seconds
            else:
                remaining = limit
                reset_time = now + window_seconds
        else:
            remaining = limit
            reset_time = now + window_seconds
        
        return remaining, reset_time


# Production: Use Redis for distributed rate limiting
# Example:
# from redis import Redis
# redis_client = Redis(host='localhost', port=6379, db=0)
# rate_limiter = RateLimiterMiddleware(app, storage=redis_client)
