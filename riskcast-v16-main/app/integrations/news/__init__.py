"""
News & Events Monitoring Integration

Provides real-time news monitoring and risk event detection.
"""

from app.integrations.news.news_service import NewsService
from app.integrations.news.news_api_client import NewsAPIClient
from app.integrations.news.event_detector import RiskEventDetector

__all__ = ["NewsService", "NewsAPIClient", "RiskEventDetector"]
