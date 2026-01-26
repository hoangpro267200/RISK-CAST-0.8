"""
News & Events Monitoring API Endpoints
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.integrations.news import NewsService, NewsAPIClient
from app.integrations.news.models import EventCategory, EventSeverity
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/news", tags=["News & Events"])


# Singleton service
_news_service: Optional[NewsService] = None


def get_news_service() -> NewsService:
    global _news_service
    if _news_service is None:
        client = NewsAPIClient()
        _news_service = NewsService(news_client=client)
    return _news_service


# Response Models
class NewsArticleResponse(BaseModel):
    article_id: str
    title: str
    description: Optional[str]
    source_name: str
    url: str
    published_at: datetime


class RiskEventResponse(BaseModel):
    event_id: str
    category: str
    severity: str
    title: str
    summary: str
    affected_regions: List[str]
    affected_ports: List[str]
    risk_score_impact: float
    confidence: float
    first_reported: datetime
    is_active: bool


class RouteRiskAdjustmentResponse(BaseModel):
    adjustment: float
    events: List[dict]


# Endpoints
@router.get("/search")
async def search_news(
    query: str,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Search news articles."""
    articles = await news_service.search_news(
        query=query,
        from_date=datetime.utcnow() - timedelta(hours=hours),
        limit=limit
    )
    
    return {
        "count": len(articles),
        "articles": [
            NewsArticleResponse(
                article_id=a.article_id,
                title=a.title,
                description=a.description,
                source_name=a.source_name,
                url=a.url,
                published_at=a.published_at
            )
            for a in articles
        ]
    }


@router.get("/maritime")
async def get_maritime_news(
    hours: int = Query(24, ge=1, le=168),
    current_user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Get recent maritime/shipping news."""
    articles = await news_service.get_maritime_news(hours=hours)
    
    return {
        "count": len(articles),
        "articles": [
            NewsArticleResponse(
                article_id=a.article_id,
                title=a.title,
                description=a.description,
                source_name=a.source_name,
                url=a.url,
                published_at=a.published_at
            )
            for a in articles
        ]
    }


@router.get("/events/active", response_model=List[RiskEventResponse])
async def get_active_events(
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    region: Optional[str] = Query(None, description="Filter by region"),
    current_user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Get currently active risk events."""
    category_enum = None
    if category:
        try:
            category_enum = EventCategory(category)
        except ValueError:
            raise HTTPException(400, f"Invalid category: {category}")
    
    severity_enum = None
    if severity:
        try:
            severity_enum = EventSeverity(severity)
        except ValueError:
            raise HTTPException(400, f"Invalid severity: {severity}")
    
    events = news_service.get_active_events(
        category=category_enum,
        severity=severity_enum,
        region=region
    )
    
    return [
        RiskEventResponse(
            event_id=e.event_id,
            category=e.category.value,
            severity=e.severity.value,
            title=e.title,
            summary=e.summary,
            affected_regions=e.affected_regions,
            affected_ports=e.affected_ports,
            risk_score_impact=e.risk_score_impact,
            confidence=e.confidence,
            first_reported=e.first_reported,
            is_active=e.is_active
        )
        for e in events
    ]


@router.get("/events/detect")
async def detect_events(
    hours: int = Query(24, ge=1, le=72),
    current_user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Detect risk events from recent news."""
    articles = await news_service.get_maritime_news(hours=hours)
    events = await news_service.detect_risk_events(articles)
    
    return {
        "articles_analyzed": len(articles),
        "events_detected": len(events),
        "events": [
            RiskEventResponse(
                event_id=e.event_id,
                category=e.category.value,
                severity=e.severity.value,
                title=e.title,
                summary=e.summary,
                affected_regions=e.affected_regions,
                affected_ports=e.affected_ports,
                risk_score_impact=e.risk_score_impact,
                confidence=e.confidence,
                first_reported=e.first_reported,
                is_active=e.is_active
            )
            for e in events
        ]
    }


@router.get("/route-risk", response_model=RouteRiskAdjustmentResponse)
async def get_route_risk_adjustment(
    origin_region: str,
    destination_region: str,
    current_user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Get risk adjustment for a route based on active events."""
    result = news_service.get_risk_adjustment_for_route(
        origin_region=origin_region,
        destination_region=destination_region
    )
    
    return RouteRiskAdjustmentResponse(**result)


@router.post("/monitoring/start")
async def start_monitoring(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Start background news monitoring."""
    background_tasks.add_task(news_service.start_monitoring)
    return {"status": "monitoring_started"}


@router.post("/monitoring/stop")
async def stop_monitoring(
    current_user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Stop background news monitoring."""
    news_service.stop_monitoring()
    return {"status": "monitoring_stopped"}


@router.get("/categories")
async def get_event_categories():
    """Get list of event categories."""
    return {
        "categories": [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in EventCategory
        ]
    }


@router.get("/severity-levels")
async def get_severity_levels():
    """Get list of severity levels."""
    return {
        "severity_levels": [
            {"value": s.value, "label": s.value}
            for s in EventSeverity
        ]
    }
