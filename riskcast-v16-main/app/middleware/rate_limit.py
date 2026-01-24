"""
Redis-ready rate limiting and lockout middleware.
Falls back to in-memory store if REDIS_URL not provided.
"""

import time
import os
import logging
from typing import Callable, Optional, Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

try:
    import redis  # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimiter:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url else os.getenv("REDIS_URL", "")
        self.use_redis = bool(self.redis_url and REDIS_AVAILABLE)
        self.local_store: Dict[str, Tuple[float, int]] = {}
        if self.use_redis:
            self.client = redis.Redis.from_url(self.redis_url)
        else:
            self.client = None

    def _key(self, prefix: str, token: str) -> str:
        return f"rl:{prefix}:{token}"

    def incr(self, prefix: str, token: str, limit: int, window_seconds: int) -> Tuple[int, float]:
        now = time.time()
        if self.use_redis and self.client:
            key = self._key(prefix, token)
            pipe = self.client.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, window_seconds)
            count, _ = pipe.execute()
            ttl = self.client.ttl(key)
            reset_at = now + (ttl if ttl > 0 else window_seconds)
            return int(count), reset_at
        # fallback in-memory
        entry = self.local_store.get((prefix + token), (now, 0))
        window_start, count = entry
        if now - window_start > window_seconds:
            window_start, count = now, 0
        count += 1
        self.local_store[prefix + token] = (window_start, count)
        reset_at = window_start + window_seconds
        return count, reset_at


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limit auth endpoints with backoff.
    Configurable via env:
      RL_WINDOW=60, RL_LIMIT=100, RL_LOGIN_LIMIT=10, RL_LOGIN_WINDOW=300
    """

    def __init__(self, app, limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.limiter = limiter or RateLimiter()
        self.default_limit = int(os.getenv("RL_LIMIT", "100"))
        self.default_window = int(os.getenv("RL_WINDOW", "60"))
        self.login_limit = int(os.getenv("RL_LOGIN_LIMIT", "10"))
        self.login_window = int(os.getenv("RL_LOGIN_WINDOW", "300"))

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        method = request.method.upper()
        client_ip = self._get_ip(request)
        email = ""

        is_login = path.endswith("/login") and method == "POST"
        limit = self.login_limit if is_login else self.default_limit
        window = self.login_window if is_login else self.default_window

        # use email if provided (auth)
        if is_login:
            try:
                data = await request.json()
                email = (data.get("email") or "").lower()
            except Exception:
                email = ""

        # per-IP
        count_ip, reset_ip = self.limiter.incr("ip", client_ip, limit, window)
        if count_ip > limit:
            return self._too_many(request, limit, reset_ip)

        # per-email
        if email:
            count_email, reset_email = self.limiter.incr("email", email, limit, window)
            if count_email > limit:
                return self._too_many(request, limit, reset_email)

        response = await call_next(request)
        return response

    def _too_many(self, request: Request, limit: int, reset_at: float) -> Response:
        from app.utils.standard_responses import fail
        ttl = max(0, int(reset_at - time.time()))
        return fail(
            code="RATE_LIMITED",
            message="Too many requests. Please wait before retrying.",
            status_code=429,
            details={"retry_after": ttl, "limit": limit},
            request=request,
        )

    def _get_ip(self, request: Request) -> str:
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
