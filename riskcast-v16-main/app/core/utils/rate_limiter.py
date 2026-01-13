"""
RISKCAST Security - Rate Limiting
Prevents abuse, brute-force attacks, and spam
"""

import time
from collections import defaultdict
from typing import Optional
from fastapi import Request, HTTPException, status
from functools import wraps
import os


class RateLimiter:
    """In-memory rate limiter (for production, use Redis)"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.max_requests_per_minute_ai = int(os.getenv("RATE_LIMIT_AI_PER_MINUTE", "10"))
        self.cleanup_interval = 300  # Cleanup old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def cleanup_old_entries(self):
        """Remove old rate limit entries"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 60  # Remove entries older than 1 minute
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                req_time for req_time in self.requests[ip]
                if req_time > cutoff_time
            ]
            if not self.requests[ip]:
                del self.requests[ip]
        
        self.last_cleanup = current_time
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check X-Forwarded-For header (for proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
            return ip
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def is_allowed(self, ip: str, limit: int = None) -> tuple[bool, int, int]:
        """
        Check if request is allowed
        
        Args:
            ip: Client IP address
            limit: Custom limit (None = use default)
            
        Returns:
            Tuple of (is_allowed, remaining, reset_in_seconds)
        """
        self.cleanup_old_entries()
        
        if limit is None:
            limit = self.max_requests_per_minute
        
        current_time = time.time()
        cutoff_time = current_time - 60
        self.requests[ip] = [
            req_time for req_time in self.requests[ip]
            if req_time > cutoff_time
        ]
        
        # Check if limit exceeded
        request_count = len(self.requests[ip])
        is_allowed = request_count < limit
        remaining = max(0, limit - request_count)
        reset_in = int(60 - (current_time - (self.requests[ip][0] if self.requests[ip] else current_time)))
        
        if is_allowed:
            # Record this request
            self.requests[ip].append(current_time)
        
        return is_allowed, remaining, reset_in
    
    def check_rate_limit(self, request: Request, limit: Optional[int] = None) -> None:
        """
        Check rate limit and raise exception if exceeded
        
        Args:
            request: FastAPI request object
            limit: Custom limit (None = use default)
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        ip = self.get_client_ip(request)
        is_allowed, remaining, reset_in = self.is_allowed(ip, limit)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per minute. Try again in {reset_in} seconds.",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_in),
                    "Retry-After": str(reset_in),
                },
            )


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 60, per_minutes: int = 1):
    """
    Decorator to apply rate limiting to routes
    
    Usage:
        @rate_limit(max_requests=60, per_minutes=1)
        async def my_endpoint(request: Request):
            ...
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if request:
                rate_limiter.check_rate_limit(request, limit=max_requests)
            
            return await f(*args, **kwargs)
        
        return wrapper
    return decorator


def ai_rate_limit(f):
    """
    Decorator for AI endpoints (stricter rate limit)
    """
    @wraps(f)
    async def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break
        
        if request:
            rate_limiter.check_rate_limit(request, limit=rate_limiter.max_requests_per_minute_ai)
        
        return await f(*args, **kwargs)
    
    return wrapper





















