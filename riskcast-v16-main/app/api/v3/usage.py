"""
Usage Statistics API Endpoints

Provides API usage statistics and quota information.
"""

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_audit
from app.shared.dependencies import get_current_user, resolve_tenant_context, TenantContext
from app.middleware.rate_limiter import UsageTracker, RateLimiter, RateLimitTier

# Try to import Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

router = APIRouter(prefix="/usage", tags=["Usage"])


class UsageResponse(BaseModel):
    date: str
    total_requests: int
    status_2xx: int
    status_4xx: int
    status_5xx: int


class QuotaResponse(BaseModel):
    tier: str
    limits: dict
    current_usage: dict
    percentage_used: dict


async def get_redis_client():
    """Get Redis client for usage tracking."""
    if not REDIS_AVAILABLE:
        return None
    
    try:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url)
        await client.ping()
        return client
    except Exception:
        return None


@router.get("/daily", response_model=UsageResponse)
async def get_daily_usage(
    date_str: Optional[str] = Query(None, description="Date in YYYYMMDD format"),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get daily API usage statistics.
    """
    if not date_str:
        date_str = datetime.utcnow().strftime('%Y%m%d')
    
    tenant_id = tenant_context.tenant_id
    
    redis_client = await get_redis_client()
    if redis_client:
        tracker = UsageTracker(redis_client)
        usage = await tracker.get_daily_usage(tenant_id, date_str)
        await redis_client.aclose()
        return UsageResponse(**usage)
    
    # Fallback if Redis unavailable
    return UsageResponse(
        date=date_str,
        total_requests=0,
        status_2xx=0,
        status_4xx=0,
        status_5xx=0
    )


@router.get("/monthly")
async def get_monthly_usage(
    year: int = Query(..., description="Year (YYYY)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get monthly API usage statistics.
    """
    tenant_id = tenant_context.tenant_id
    
    redis_client = await get_redis_client()
    if redis_client:
        tracker = UsageTracker(redis_client)
        usage = await tracker.get_monthly_usage(tenant_id, year, month)
        await redis_client.aclose()
        return usage
    
    # Fallback
    return {
        "year": year,
        "month": month,
        "total_requests": 0,
        "daily_breakdown": []
    }


@router.get("/quota", response_model=QuotaResponse)
async def get_quota_status(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get current quota status and usage.
    """
    tenant_id = tenant_context.tenant_id
    
    # Get tenant plan (would come from tenant model)
    tier = RateLimitTier.STARTER  # Default
    
    # Try to get tenant plan from tenant manager
    try:
        from app.tenants.tenant_manager import TenantManager
        
        audit = get_audit(db)
        manager = TenantManager(db, audit)
        tenant = await manager.get_tenant(tenant_id)
        
        if tenant:
            plan_mapping = {
                "STARTER": RateLimitTier.STARTER,
                "PROFESSIONAL": RateLimitTier.PROFESSIONAL,
                "ENTERPRISE": RateLimitTier.ENTERPRISE
            }
            tier = plan_mapping.get(tenant.plan.value, RateLimitTier.STARTER)
    except Exception:
        pass  # Use default tier
    
    config = RateLimiter.TIER_CONFIGS[tier]
    
    # Get actual usage
    redis_client = await get_redis_client()
    current = {
        "requests_per_minute": 0,
        "requests_per_hour": 0,
        "requests_per_day": 0
    }
    
    if redis_client:
        try:
            limiter = RateLimiter(redis_client=redis_client)
            stats = await limiter.get_usage_stats(f"tenant:{tenant_id}")
            current["requests_per_minute"] = stats.get("requests_last_minute", 0)
            current["requests_per_day"] = stats.get("requests_today", 0)
            
            # Hourly would need separate tracking
            current["requests_per_hour"] = current["requests_per_day"] // 24  # Rough estimate
            
            await redis_client.aclose()
        except Exception:
            pass
    
    return QuotaResponse(
        tier=tier.value,
        limits={
            "requests_per_minute": config.requests_per_minute,
            "requests_per_hour": config.requests_per_hour,
            "requests_per_day": config.requests_per_day
        },
        current_usage=current,
        percentage_used={
            "minute": round(current["requests_per_minute"] / config.requests_per_minute * 100, 1) if config.requests_per_minute > 0 else 0,
            "hour": round(current["requests_per_hour"] / config.requests_per_hour * 100, 1) if config.requests_per_hour > 0 else 0,
            "day": round(current["requests_per_day"] / config.requests_per_day * 100, 1) if config.requests_per_day > 0 else 0
        }
    )


@router.get("/stats")
async def get_usage_stats(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get current usage statistics (last minute, today).
    """
    tenant_id = tenant_context.tenant_id
    
    redis_client = await get_redis_client()
    if redis_client:
        try:
            limiter = RateLimiter(redis_client=redis_client)
            stats = await limiter.get_usage_stats(f"tenant:{tenant_id}")
            await redis_client.aclose()
            return stats
        except Exception:
            pass
    
    return {
        "requests_last_minute": 0,
        "requests_today": 0,
        "timestamp": datetime.utcnow().isoformat()
    }
