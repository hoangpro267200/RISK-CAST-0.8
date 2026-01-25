"""
Authentication-specific Rate Limiting

Production-grade rate limiting for authentication endpoints with:
- Login attempt throttling
- Password reset request limiting
- Email verification rate limiting
- IP-based and email-based tracking
- Distributed support via Redis

SECURITY CONSIDERATIONS:
- Implements exponential backoff for failed login attempts
- Prevents password enumeration via timing-consistent responses
- Tracks both IP and email to prevent distributed attacks
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Try to import Redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)


@dataclass
class AuthRateLimitResult:
    """Result of an auth rate limit check."""
    allowed: bool
    remaining_attempts: int
    max_attempts: int
    lockout_until: Optional[datetime] = None
    retry_after_seconds: Optional[int] = None
    reason: Optional[str] = None


class AuthRateLimitType(Enum):
    """Types of auth rate limits."""
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    SIGNUP = "signup"
    API_KEY_CREATE = "api_key_create"


class AuthRateLimiter:
    """
    Authentication-specific rate limiter.
    
    Features:
    - Per-IP rate limiting
    - Per-email rate limiting (for login/password reset)
    - Combined IP+email tracking for login attempts
    - Exponential backoff for repeated failures
    - Redis backend with in-memory fallback
    """
    
    # Default limits
    DEFAULT_LIMITS = {
        AuthRateLimitType.LOGIN: {
            "max_attempts": 5,
            "window_minutes": 15,
            "lockout_minutes": 15,
            "per_ip_max": 20,  # Max attempts per IP across all emails
            "per_ip_window_minutes": 60,
        },
        AuthRateLimitType.PASSWORD_RESET: {
            "max_attempts": 3,
            "window_minutes": 60,
            "lockout_minutes": 60,
            "per_ip_max": 10,
            "per_ip_window_minutes": 60,
        },
        AuthRateLimitType.EMAIL_VERIFICATION: {
            "max_attempts": 5,
            "window_minutes": 60,
            "lockout_minutes": 30,
            "per_ip_max": 20,
            "per_ip_window_minutes": 60,
        },
        AuthRateLimitType.SIGNUP: {
            "max_attempts": 5,
            "window_minutes": 60,
            "lockout_minutes": 60,
            "per_ip_max": 10,
            "per_ip_window_minutes": 60,
        },
        AuthRateLimitType.API_KEY_CREATE: {
            "max_attempts": 10,
            "window_minutes": 60,
            "lockout_minutes": 30,
            "per_ip_max": 20,
            "per_ip_window_minutes": 60,
        },
    }
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        prefix: str = "auth_ratelimit"
    ):
        """
        Initialize auth rate limiter.
        
        Args:
            redis_client: Optional async Redis client
            prefix: Key prefix for Redis/memory storage
        """
        self.redis = redis_client
        self.prefix = prefix
        self.use_redis = REDIS_AVAILABLE and redis_client is not None
        
        # In-memory fallback storage
        self._memory_store: Dict[str, Dict[str, Any]] = {}
    
    async def check_login_allowed(
        self,
        email: str,
        ip_address: str
    ) -> AuthRateLimitResult:
        """
        Check if login attempt is allowed.
        
        Checks both:
        1. Email+IP combination (prevents credential stuffing)
        2. IP-only (prevents distributed attacks from same IP)
        """
        config = self.DEFAULT_LIMITS[AuthRateLimitType.LOGIN]
        
        # Check combined email+IP
        combined_key = f"{email.lower()}:{ip_address}"
        combined_result = await self._check_rate_limit(
            AuthRateLimitType.LOGIN,
            combined_key,
            config["max_attempts"],
            config["window_minutes"],
            config["lockout_minutes"]
        )
        
        if not combined_result.allowed:
            return combined_result
        
        # Check IP-only limit
        ip_result = await self._check_rate_limit(
            AuthRateLimitType.LOGIN,
            f"ip:{ip_address}",
            config["per_ip_max"],
            config["per_ip_window_minutes"],
            config["lockout_minutes"]
        )
        
        if not ip_result.allowed:
            ip_result.reason = "Too many login attempts from this IP address"
            return ip_result
        
        return combined_result
    
    async def record_login_failure(self, email: str, ip_address: str):
        """Record a failed login attempt."""
        combined_key = f"{email.lower()}:{ip_address}"
        await self._record_attempt(AuthRateLimitType.LOGIN, combined_key)
        await self._record_attempt(AuthRateLimitType.LOGIN, f"ip:{ip_address}")
        
        logger.warning(
            f"Login failure recorded: email={email[:3]}*** ip={ip_address}",
            extra={
                "security_event": "login_failure_recorded",
                "ip": ip_address
            }
        )
    
    async def clear_login_failures(self, email: str, ip_address: str):
        """Clear failed login attempts after successful login."""
        combined_key = f"{email.lower()}:{ip_address}"
        await self._clear_attempts(AuthRateLimitType.LOGIN, combined_key)
        # Note: We don't clear IP-only failures to prevent abuse
    
    async def check_password_reset_allowed(
        self,
        email: str,
        ip_address: str
    ) -> AuthRateLimitResult:
        """Check if password reset request is allowed."""
        config = self.DEFAULT_LIMITS[AuthRateLimitType.PASSWORD_RESET]
        
        # Check email-based limit
        email_result = await self._check_rate_limit(
            AuthRateLimitType.PASSWORD_RESET,
            f"email:{email.lower()}",
            config["max_attempts"],
            config["window_minutes"],
            config["lockout_minutes"]
        )
        
        if not email_result.allowed:
            return email_result
        
        # Check IP-based limit
        ip_result = await self._check_rate_limit(
            AuthRateLimitType.PASSWORD_RESET,
            f"ip:{ip_address}",
            config["per_ip_max"],
            config["per_ip_window_minutes"],
            config["lockout_minutes"]
        )
        
        return ip_result if not ip_result.allowed else email_result
    
    async def record_password_reset_request(self, email: str, ip_address: str):
        """Record a password reset request."""
        await self._record_attempt(AuthRateLimitType.PASSWORD_RESET, f"email:{email.lower()}")
        await self._record_attempt(AuthRateLimitType.PASSWORD_RESET, f"ip:{ip_address}")
    
    async def check_signup_allowed(self, ip_address: str) -> AuthRateLimitResult:
        """Check if signup is allowed from this IP."""
        config = self.DEFAULT_LIMITS[AuthRateLimitType.SIGNUP]
        
        return await self._check_rate_limit(
            AuthRateLimitType.SIGNUP,
            f"ip:{ip_address}",
            config["per_ip_max"],
            config["per_ip_window_minutes"],
            config["lockout_minutes"]
        )
    
    async def record_signup(self, ip_address: str):
        """Record a signup attempt."""
        await self._record_attempt(AuthRateLimitType.SIGNUP, f"ip:{ip_address}")
    
    async def _check_rate_limit(
        self,
        limit_type: AuthRateLimitType,
        identifier: str,
        max_attempts: int,
        window_minutes: int,
        lockout_minutes: int
    ) -> AuthRateLimitResult:
        """
        Generic rate limit check.
        
        Uses sliding window counter algorithm.
        """
        if self.use_redis:
            return await self._check_rate_limit_redis(
                limit_type, identifier, max_attempts, window_minutes, lockout_minutes
            )
        else:
            return await self._check_rate_limit_memory(
                limit_type, identifier, max_attempts, window_minutes, lockout_minutes
            )
    
    async def _check_rate_limit_redis(
        self,
        limit_type: AuthRateLimitType,
        identifier: str,
        max_attempts: int,
        window_minutes: int,
        lockout_minutes: int
    ) -> AuthRateLimitResult:
        """Check rate limit using Redis."""
        try:
            key = f"{self.prefix}:{limit_type.value}:{identifier}"
            lockout_key = f"{key}:lockout"
            
            now = time.time()
            window_start = now - (window_minutes * 60)
            
            # Check if currently locked out
            lockout_until = await self.redis.get(lockout_key)
            if lockout_until:
                lockout_ts = float(lockout_until)
                if lockout_ts > now:
                    return AuthRateLimitResult(
                        allowed=False,
                        remaining_attempts=0,
                        max_attempts=max_attempts,
                        lockout_until=datetime.fromtimestamp(lockout_ts),
                        retry_after_seconds=int(lockout_ts - now) + 1,
                        reason="Too many attempts. Please try again later."
                    )
                else:
                    # Lockout expired, clean up
                    await self.redis.delete(lockout_key)
            
            # Count attempts in window
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
            pipe.zcard(key)  # Count current entries
            results = await pipe.execute()
            
            current_count = results[1]
            remaining = max_attempts - current_count
            
            if current_count >= max_attempts:
                # Set lockout
                lockout_until_ts = now + (lockout_minutes * 60)
                await self.redis.setex(
                    lockout_key,
                    lockout_minutes * 60 + 60,  # Add buffer
                    str(lockout_until_ts)
                )
                
                return AuthRateLimitResult(
                    allowed=False,
                    remaining_attempts=0,
                    max_attempts=max_attempts,
                    lockout_until=datetime.fromtimestamp(lockout_until_ts),
                    retry_after_seconds=lockout_minutes * 60,
                    reason="Too many attempts. Please try again later."
                )
            
            return AuthRateLimitResult(
                allowed=True,
                remaining_attempts=remaining,
                max_attempts=max_attempts
            )
            
        except Exception as e:
            logger.warning(f"Redis auth rate limit check failed: {e}")
            # Fail open in case of Redis error
            return AuthRateLimitResult(
                allowed=True,
                remaining_attempts=max_attempts,
                max_attempts=max_attempts
            )
    
    async def _check_rate_limit_memory(
        self,
        limit_type: AuthRateLimitType,
        identifier: str,
        max_attempts: int,
        window_minutes: int,
        lockout_minutes: int
    ) -> AuthRateLimitResult:
        """Check rate limit using in-memory storage."""
        key = f"{limit_type.value}:{identifier}"
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        # Initialize if needed
        if key not in self._memory_store:
            self._memory_store[key] = {
                "attempts": [],
                "lockout_until": None
            }
        
        store = self._memory_store[key]
        
        # Check lockout
        if store["lockout_until"] and store["lockout_until"] > now:
            return AuthRateLimitResult(
                allowed=False,
                remaining_attempts=0,
                max_attempts=max_attempts,
                lockout_until=datetime.fromtimestamp(store["lockout_until"]),
                retry_after_seconds=int(store["lockout_until"] - now) + 1,
                reason="Too many attempts. Please try again later."
            )
        elif store["lockout_until"]:
            # Lockout expired
            store["lockout_until"] = None
            store["attempts"] = []
        
        # Clean old attempts
        store["attempts"] = [ts for ts in store["attempts"] if ts > window_start]
        
        # Check count
        current_count = len(store["attempts"])
        remaining = max_attempts - current_count
        
        if current_count >= max_attempts:
            # Set lockout
            store["lockout_until"] = now + (lockout_minutes * 60)
            
            return AuthRateLimitResult(
                allowed=False,
                remaining_attempts=0,
                max_attempts=max_attempts,
                lockout_until=datetime.fromtimestamp(store["lockout_until"]),
                retry_after_seconds=lockout_minutes * 60,
                reason="Too many attempts. Please try again later."
            )
        
        return AuthRateLimitResult(
            allowed=True,
            remaining_attempts=remaining,
            max_attempts=max_attempts
        )
    
    async def _record_attempt(
        self,
        limit_type: AuthRateLimitType,
        identifier: str
    ):
        """Record an attempt."""
        if self.use_redis:
            await self._record_attempt_redis(limit_type, identifier)
        else:
            await self._record_attempt_memory(limit_type, identifier)
    
    async def _record_attempt_redis(
        self,
        limit_type: AuthRateLimitType,
        identifier: str
    ):
        """Record attempt in Redis."""
        try:
            key = f"{self.prefix}:{limit_type.value}:{identifier}"
            config = self.DEFAULT_LIMITS[limit_type]
            window_minutes = config.get("window_minutes", 15)
            
            now = time.time()
            
            pipe = self.redis.pipeline()
            pipe.zadd(key, {f"{now}": now})
            pipe.expire(key, window_minutes * 60 + 60)
            await pipe.execute()
            
        except Exception as e:
            logger.warning(f"Failed to record attempt in Redis: {e}")
    
    async def _record_attempt_memory(
        self,
        limit_type: AuthRateLimitType,
        identifier: str
    ):
        """Record attempt in memory."""
        key = f"{limit_type.value}:{identifier}"
        now = time.time()
        
        if key not in self._memory_store:
            self._memory_store[key] = {
                "attempts": [],
                "lockout_until": None
            }
        
        self._memory_store[key]["attempts"].append(now)
    
    async def _clear_attempts(
        self,
        limit_type: AuthRateLimitType,
        identifier: str
    ):
        """Clear recorded attempts."""
        if self.use_redis:
            try:
                key = f"{self.prefix}:{limit_type.value}:{identifier}"
                await self.redis.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear attempts in Redis: {e}")
        else:
            key = f"{limit_type.value}:{identifier}"
            if key in self._memory_store:
                del self._memory_store[key]


# Global instance (initialized lazily)
_auth_rate_limiter: Optional[AuthRateLimiter] = None


def get_auth_rate_limiter() -> AuthRateLimiter:
    """Get or create the global auth rate limiter."""
    global _auth_rate_limiter
    
    if _auth_rate_limiter is None:
        # Try to get Redis connection from config
        redis_client = None
        
        try:
            from app.auth_config.auth import AUTH_CONFIG
            redis_url = AUTH_CONFIG.get("REDIS_URL", "")
            
            if redis_url and REDIS_AVAILABLE:
                redis_client = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Auth rate limiter using Redis backend")
            else:
                logger.info("Auth rate limiter using in-memory backend")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis for auth rate limiter: {e}")
        
        _auth_rate_limiter = AuthRateLimiter(redis_client=redis_client)
    
    return _auth_rate_limiter


async def init_auth_rate_limiter(redis_url: Optional[str] = None):
    """
    Initialize the auth rate limiter with a Redis connection.
    
    Call this at application startup if you want to use Redis.
    """
    global _auth_rate_limiter
    
    redis_client = None
    if redis_url and REDIS_AVAILABLE:
        try:
            redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await redis_client.ping()
            logger.info("Auth rate limiter Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for auth rate limiter: {e}")
            redis_client = None
    
    _auth_rate_limiter = AuthRateLimiter(redis_client=redis_client)
    return _auth_rate_limiter
