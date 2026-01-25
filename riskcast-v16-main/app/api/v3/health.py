"""
Health Check API Endpoints
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database import get_db
from app.monitoring.health_monitor import HealthMonitor, SystemHealth, ComponentHealth, HealthStatus
from sqlalchemy.orm import Session


router = APIRouter(prefix="/health", tags=["Health"])


class ComponentHealthResponse(BaseModel):
    component: str
    status: str
    latency_ms: float = None
    message: str
    last_checked: datetime
    details: dict = None


class SystemHealthResponse(BaseModel):
    overall_status: str
    components: List[ComponentHealthResponse]
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    checked_at: datetime
    uptime_seconds: float


@router.get("/", response_model=SystemHealthResponse)
async def get_system_health(db: Session = Depends(get_db)):
    """
    Get comprehensive system health status.
    
    Checks all components and returns overall health.
    """
    monitor = HealthMonitor(db)
    health = await monitor.check_health()
    
    return SystemHealthResponse(
        overall_status=health.overall_status.value,
        components=[
            ComponentHealthResponse(
                component=c.component,
                status=c.status.value,
                latency_ms=c.latency_ms,
                message=c.message,
                last_checked=c.last_checked,
                details=c.details
            )
            for c in health.components
        ],
        healthy_count=health.healthy_count,
        degraded_count=health.degraded_count,
        unhealthy_count=health.unhealthy_count,
        checked_at=health.checked_at,
        uptime_seconds=health.uptime_seconds
    )


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe.
    
    Returns 200 if system is ready to handle requests.
    """
    monitor = HealthMonitor(db)
    health = await monitor.check_health()
    
    if health.overall_status == HealthStatus.UNHEALTHY:
        return {"ready": False, "status": "UNHEALTHY"}
    
    return {"ready": True, "status": health.overall_status.value}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe.
    
    Returns 200 if application is alive.
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/startup")
async def startup_check(db: Session = Depends(get_db)):
    """
    Kubernetes startup probe.
    
    Returns 200 when application has fully started.
    """
    try:
        # Just check database connectivity
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"started": True}
    except:
        return {"started": False}
