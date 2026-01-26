"""
NewsAPI Client

Uses NewsAPI.org for news aggregation
"""

import aiohttp
import os
import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.logging import get_logger
from app.integrations.news.models import NewsArticle


logger = get_logger(__name__)


class NewsAPIClient:
    """
    NewsAPI.org client for news search.
    """
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("NewsAPI key not configured, using mock data")
    
    async def search(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sources: Optional[List[str]] = None,
        language: str = "en",
        limit: int = 100
    ) -> List[NewsArticle]:
        """
        Search news articles.
        """
        if not self.api_key:
            return self._mock_search(query, limit)
        
        params = {
            "q": query,
            "language": language,
            "pageSize": min(limit, 100),
            "sortBy": "publishedAt",
            "apiKey": self.api_key
        }
        
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%S")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%dT%H:%M:%S")
        if sources:
            params["sources"] = ",".join(sources)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/everything",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        logger.error(f"NewsAPI error: {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    if data.get("status") != "ok":
                        logger.error(f"NewsAPI error: {data.get('message')}")
                        return []
                    
                    return self._parse_articles(data.get("articles", []))
                    
        except Exception as e:
            logger.error(f"NewsAPI request failed: {e}")
            return []
    
    def _parse_articles(self, articles: List[dict]) -> List[NewsArticle]:
        """Parse API response to NewsArticle objects."""
        parsed = []
        
        for article in articles:
            try:
                # Generate ID from URL
                article_id = hashlib.md5(
                    article.get("url", "").encode()
                ).hexdigest()[:12]
                
                published_str = article.get("publishedAt", "")
                if published_str:
                    # Parse ISO format with timezone
                    published_str = published_str.replace("Z", "+00:00")
                    published_at = datetime.fromisoformat(published_str)
                else:
                    published_at = datetime.utcnow()
                
                parsed.append(NewsArticle(
                    article_id=article_id,
                    title=article.get("title", ""),
                    description=article.get("description"),
                    content=article.get("content"),
                    source=article.get("source", {}).get("id", "unknown"),
                    source_name=article.get("source", {}).get("name", "Unknown"),
                    url=article.get("url", ""),
                    published_at=published_at,
                    author=article.get("author"),
                    image_url=article.get("urlToImage")
                ))
            except Exception as e:
                logger.warning(f"Failed to parse article: {e}")
        
        return parsed
    
    def _mock_search(self, query: str, limit: int) -> List[NewsArticle]:
        """Generate mock news articles for testing."""
        mock_articles = [
            {
                "title": "Port of Singapore Reports Record Container Throughput",
                "description": "Singapore's port handled record volumes as shipping demand surges",
                "source": "reuters",
                "regions": ["Singapore"],
                "category": "PORT"
            },
            {
                "title": "Typhoon Warning Issued for South China Sea",
                "description": "Typhoon Hainan expected to impact shipping routes this week",
                "source": "bbc",
                "regions": ["South China Sea", "Hong Kong"],
                "category": "NATURAL_DISASTER"
            },
            {
                "title": "Piracy Incident Reported in Gulf of Guinea",
                "description": "Armed men boarded tanker off Nigerian coast, crew safe",
                "source": "lloyds",
                "regions": ["Gulf of Guinea", "Nigeria", "West Africa"],
                "category": "PIRACY"
            },
            {
                "title": "Suez Canal Congestion Eases as Backlog Clears",
                "description": "Traffic returning to normal after week of delays",
                "source": "splash247",
                "regions": ["Suez Canal", "Red Sea", "Mediterranean"],
                "category": "PORT_DISRUPTION"
            },
            {
                "title": "New Sanctions Announced on Russian Oil Tankers",
                "description": "EU expands sanctions list to include shadow fleet vessels",
                "source": "ft",
                "regions": ["Russia", "Black Sea"],
                "category": "SANCTIONS"
            },
            {
                "title": "Container Ship Runs Aground in Strait of Malacca",
                "description": "13,000 TEU vessel refloated after 12-hour grounding",
                "source": "tradewinds",
                "regions": ["Strait of Malacca", "Singapore", "Malaysia"],
                "category": "ACCIDENT"
            },
            {
                "title": "Port Workers Strike at Rotterdam",
                "description": "Dockworkers begin 48-hour strike over pay dispute",
                "source": "reuters",
                "regions": ["Rotterdam"],
                "category": "STRIKE"
            },
            {
                "title": "Houthi Missile Attack on Commercial Vessel in Red Sea",
                "description": "Bulk carrier reports near miss from missile attack",
                "source": "bbc",
                "regions": ["Red Sea", "Yemen", "Gulf of Aden"],
                "category": "WAR_CONFLICT"
            }
        ]
        
        # Filter by query
        results = []
        query_lower = query.lower()
        
        for article_data in mock_articles:
            if any(word in article_data["title"].lower() or 
                   word in article_data["description"].lower() 
                   for word in query_lower.split()):
                results.append(article_data)
        
        # If no matches, return random selection
        if not results:
            results = random.sample(mock_articles, min(limit, len(mock_articles)))
        
        # Convert to NewsArticle
        articles = []
        for i, data in enumerate(results[:limit]):
            article_id = hashlib.md5(
                f"{data['title']}{i}".encode()
            ).hexdigest()[:12]
            
            articles.append(NewsArticle(
                article_id=article_id,
                title=data["title"],
                description=data["description"],
                content=data["description"],
                source=data["source"],
                source_name=data["source"].title(),
                url=f"https://example.com/news/{article_id}",
                published_at=datetime.utcnow() - timedelta(
                    hours=random.randint(1, 48)
                )
            ))
        
        return articles
