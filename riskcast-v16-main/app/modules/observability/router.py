"""
Observability Router
FastAPI routes for observability (metrics endpoint)
"""
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import settings

router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.ENABLE_PROMETHEUS:
        return Response(content="Prometheus not enabled", status_code=503)
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
