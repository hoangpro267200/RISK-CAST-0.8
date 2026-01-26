"""
News & Events Monitoring Service

Provides:
1. News aggregation from multiple sources
2. NLP-based risk event detection
3. Entity extraction (ports, vessels, companies)
4. Severity classification
5. Real-time alerts
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from app.core.logging import get_logger
from app.integrations.news.models import (
    NewsArticle, RiskEvent, NewsAlert, EventCategory, EventSeverity
)
from app.integrations.news.news_api_client import NewsAPIClient
from app.integrations.news.event_detector import RiskEventDetector


logger = get_logger(__name__)


class NewsService:
    """
    Unified news monitoring service.
    """
    
    # Keywords for category detection
    CATEGORY_KEYWORDS = {
        EventCategory.NATURAL_DISASTER: [
            "typhoon", "hurricane", "cyclone", "earthquake", "tsunami",
            "flood", "storm", "volcano", "tornado", "wildfire"
        ],
        EventCategory.PIRACY: [
            "piracy", "pirate", "hijack", "armed robbery", "maritime security",
            "kidnap", "ransom", "somali", "gulf of guinea"
        ],
        EventCategory.POLITICAL_INSTABILITY: [
            "coup", "protest", "unrest", "revolution", "political crisis",
            "government collapse", "civil unrest", "riot"
        ],
        EventCategory.PORT_DISRUPTION: [
            "port closure", "port congestion", "terminal shutdown",
            "dock strike", "port blockade", "berth", "quay"
        ],
        EventCategory.SANCTIONS: [
            "sanction", "embargo", "blacklist", "ofac", "trade restriction",
            "export ban", "import ban", "trade war"
        ],
        EventCategory.ACCIDENT: [
            "collision", "grounding", "capsiz", "sinking", "fire",
            "explosion", "container lost", "oil spill", "shipwreck"
        ],
        EventCategory.STRIKE: [
            "strike", "labor dispute", "walkout", "industrial action",
            "union", "workers protest"
        ],
        EventCategory.WAR_CONFLICT: [
            "war", "conflict", "military", "attack", "missile",
            "bombing", "invasion", "armed forces"
        ],
        EventCategory.CYBER_ATTACK: [
            "cyber attack", "ransomware", "hacking", "data breach",
            "system outage", "IT disruption"
        ]
    }
    
    # High-risk regions
    HIGH_RISK_REGIONS = {
        "Gulf of Aden", "Somali", "Yemen", "Horn of Africa",
        "Gulf of Guinea", "Nigeria", "West Africa",
        "Strait of Malacca", "Indonesia", "Malaysia", "Singapore Strait",
        "Red Sea", "Suez Canal", "Mediterranean",
        "South China Sea", "Taiwan", "Philippines",
        "Black Sea", "Ukraine", "Russia", "Crimea",
        "Persian Gulf", "Iran", "Iraq", "Kuwait",
        "Venezuela", "Caribbean"
    }
    
    # Major ports for detection
    MAJOR_PORTS = {
        "Shanghai", "Singapore", "Ningbo", "Shenzhen", "Guangzhou",
        "Busan", "Hong Kong", "Qingdao", "Tianjin", "Rotterdam",
        "Antwerp", "Hamburg", "Los Angeles", "Long Beach", "New York",
        "Savannah", "Felixstowe", "Southampton", "Le Havre", "Piraeus",
        "Dubai", "Jeddah", "Port Said", "Colombo", "Tanjung Pelepas"
    }
    
    def __init__(
        self,
        news_client: NewsAPIClient,
        event_detector: Optional[RiskEventDetector] = None,
        check_interval_minutes: int = 15
    ):
        self.news_client = news_client
        self.event_detector = event_detector or RiskEventDetector()
        self.check_interval = check_interval_minutes
        
        # Active events cache
        self._active_events: Dict[str, RiskEvent] = {}
        
        # Processed articles (to avoid duplicates)
        self._processed_articles: Set[str] = set()
        
        # Running flag
        self._running = False
    
    async def search_news(
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
        from_date = from_date or (datetime.utcnow() - timedelta(days=7))
        to_date = to_date or datetime.utcnow()
        
        return await self.news_client.search(
            query=query,
            from_date=from_date,
            to_date=to_date,
            sources=sources,
            language=language,
            limit=limit
        )
    
    async def get_maritime_news(
        self,
        hours: int = 24
    ) -> List[NewsArticle]:
        """
        Get recent maritime/shipping news.
        """
        queries = [
            "shipping maritime",
            "container vessel",
            "port cargo",
            "marine insurance",
            "Lloyd's shipping"
        ]
        
        all_articles = []
        
        for query in queries:
            articles = await self.search_news(
                query=query,
                from_date=datetime.utcnow() - timedelta(hours=hours),
                limit=50
            )
            all_articles.extend(articles)
        
        # Deduplicate
        seen = set()
        unique_articles = []
        for article in all_articles:
            if article.article_id not in seen:
                seen.add(article.article_id)
                unique_articles.append(article)
        
        return unique_articles
    
    async def detect_risk_events(
        self,
        articles: List[NewsArticle]
    ) -> List[RiskEvent]:
        """
        Analyze articles and detect risk events.
        """
        events = []
        
        for article in articles:
            if article.article_id in self._processed_articles:
                continue
            
            self._processed_articles.add(article.article_id)
            
            # Combine text for analysis
            text = f"{article.title} {article.description or ''} {article.content or ''}"
            text_lower = text.lower()
            
            # Detect category
            category = self._detect_category(text_lower)
            if category == EventCategory.OTHER:
                continue  # Skip non-risk articles
            
            # Detect severity
            severity = self._detect_severity(text_lower, category)
            
            # Extract entities
            regions = self._extract_regions(text)
            ports = self._extract_ports(text)
            
            # Skip if no geographic relevance
            if not regions and not ports:
                continue
            
            # Calculate risk impact
            risk_impact = self._calculate_risk_impact(category, severity, regions)
            
            # Create event
            event = RiskEvent(
                event_id=f"EVT-{article.article_id[:8]}",
                category=category,
                severity=severity,
                title=article.title,
                summary=article.description or article.title,
                affected_regions=regions,
                affected_ports=ports,
                risk_score_impact=risk_impact,
                source_articles=[article.article_id],
                first_reported=article.published_at,
                last_updated=datetime.utcnow(),
                confidence=0.75,
                keywords=self._extract_keywords(text_lower, category)
            )
            
            events.append(event)
            
            logger.info(
                f"Risk event detected: {category.value} - {severity.value}",
                extra={"event_id": event.event_id, "regions": regions}
            )
        
        # Merge similar events
        merged_events = self._merge_similar_events(events)
        
        return merged_events
    
    async def start_monitoring(self):
        """
        Start continuous news monitoring.
        """
        self._running = True
        logger.info("News monitoring started")
        
        while self._running:
            try:
                # Get recent news
                articles = await self.get_maritime_news(hours=1)
                
                # Detect events
                events = await self.detect_risk_events(articles)
                
                # Update active events
                for event in events:
                    self._active_events[event.event_id] = event
                
                # Generate alerts for new/escalated events
                alerts = self._generate_alerts(events)
                
                # TODO: Send alerts via webhook/websocket
                for alert in alerts:
                    logger.warning(
                        f"Risk Alert: {alert.event.category.value}",
                        extra={"message": alert.message}
                    )
                
            except Exception as e:
                logger.error(f"News monitoring error: {e}")
            
            await asyncio.sleep(self.check_interval * 60)
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self._running = False
        logger.info("News monitoring stopped")
    
    def get_active_events(
        self,
        category: Optional[EventCategory] = None,
        severity: Optional[EventSeverity] = None,
        region: Optional[str] = None
    ) -> List[RiskEvent]:
        """
        Get currently active risk events.
        """
        events = list(self._active_events.values())
        
        if category:
            events = [e for e in events if e.category == category]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        if region:
            region_lower = region.lower()
            events = [
                e for e in events
                if any(region_lower in r.lower() for r in e.affected_regions)
            ]
        
        return sorted(events, key=lambda e: e.last_updated, reverse=True)
    
    def get_risk_adjustment_for_route(
        self,
        origin_region: str,
        destination_region: str
    ) -> Dict:
        """
        Get risk score adjustment based on active events affecting a route.
        """
        relevant_events = []
        total_adjustment = 0.0
        
        for event in self._active_events.values():
            if not event.is_active:
                continue
            
            # Check if event affects route
            route_regions = {origin_region.lower(), destination_region.lower()}
            event_regions = {r.lower() for r in event.affected_regions}
            
            if route_regions & event_regions:
                relevant_events.append(event)
                total_adjustment += event.risk_score_impact
        
        return {
            "adjustment": min(total_adjustment, 0.3),  # Cap at 30%
            "events": [
                {
                    "event_id": e.event_id,
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "summary": e.summary,
                    "impact": e.risk_score_impact
                }
                for e in relevant_events
            ]
        }
    
    def _detect_category(self, text: str) -> EventCategory:
        """Detect event category from text."""
        category_scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return EventCategory.OTHER
        
        return max(category_scores, key=category_scores.get)
    
    def _detect_severity(self, text: str, category: EventCategory) -> EventSeverity:
        """Detect event severity."""
        critical_words = [
            "major", "severe", "critical", "emergency", "catastrophic",
            "deadly", "fatal", "massive", "widespread", "unprecedented"
        ]
        
        high_words = [
            "significant", "serious", "substantial", "considerable",
            "extensive", "heavy", "intense"
        ]
        
        critical_count = sum(1 for w in critical_words if w in text)
        high_count = sum(1 for w in high_words if w in text)
        
        # Category-based adjustment
        if category in [EventCategory.WAR_CONFLICT, EventCategory.PIRACY]:
            return EventSeverity.CRITICAL if critical_count > 0 else EventSeverity.HIGH
        
        if critical_count >= 2:
            return EventSeverity.CRITICAL
        elif critical_count >= 1 or high_count >= 2:
            return EventSeverity.HIGH
        elif high_count >= 1:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW
    
    def _extract_regions(self, text: str) -> List[str]:
        """Extract affected regions from text."""
        found_regions = []
        text_lower = text.lower()
        
        for region in self.HIGH_RISK_REGIONS:
            if region.lower() in text_lower:
                found_regions.append(region)
        
        return list(set(found_regions))
    
    def _extract_ports(self, text: str) -> List[str]:
        """Extract mentioned ports from text."""
        found_ports = []
        text_lower = text.lower()
        
        for port in self.MAJOR_PORTS:
            if port.lower() in text_lower:
                found_ports.append(port)
        
        return list(set(found_ports))
    
    def _extract_keywords(self, text: str, category: EventCategory) -> List[str]:
        """Extract relevant keywords."""
        keywords = []
        
        if category in self.CATEGORY_KEYWORDS:
            for kw in self.CATEGORY_KEYWORDS[category]:
                if kw in text:
                    keywords.append(kw)
        
        return keywords[:10]  # Limit to top 10
    
    def _calculate_risk_impact(
        self,
        category: EventCategory,
        severity: EventSeverity,
        regions: List[str]
    ) -> float:
        """Calculate risk score impact."""
        # Base impact by severity
        severity_impact = {
            EventSeverity.LOW: 0.02,
            EventSeverity.MEDIUM: 0.05,
            EventSeverity.HIGH: 0.10,
            EventSeverity.CRITICAL: 0.20
        }
        
        # Category multiplier
        category_multiplier = {
            EventCategory.WAR_CONFLICT: 1.5,
            EventCategory.PIRACY: 1.3,
            EventCategory.NATURAL_DISASTER: 1.2,
            EventCategory.PORT_DISRUPTION: 1.1,
            EventCategory.SANCTIONS: 1.2,
            EventCategory.ACCIDENT: 0.8,
            EventCategory.STRIKE: 0.9,
            EventCategory.CYBER_ATTACK: 1.0,
            EventCategory.OTHER: 0.5
        }
        
        base = severity_impact.get(severity, 0.05)
        multiplier = category_multiplier.get(category, 1.0)
        
        # Increase for multiple regions
        region_factor = 1 + (len(regions) - 1) * 0.1
        
        return min(base * multiplier * region_factor, 0.30)
    
    def _merge_similar_events(self, events: List[RiskEvent]) -> List[RiskEvent]:
        """Merge events that appear to be about the same incident."""
        if len(events) <= 1:
            return events
        
        merged = []
        used = set()
        
        for i, event1 in enumerate(events):
            if i in used:
                continue
            
            # Find similar events
            similar = [event1]
            
            for j, event2 in enumerate(events[i+1:], start=i+1):
                if j in used:
                    continue
                
                if self._events_similar(event1, event2):
                    similar.append(event2)
                    used.add(j)
            
            # Merge if multiple similar
            if len(similar) > 1:
                merged.append(self._merge_events(similar))
            else:
                merged.append(event1)
            
            used.add(i)
        
        return merged
    
    def _events_similar(self, e1: RiskEvent, e2: RiskEvent) -> bool:
        """Check if two events are about the same incident."""
        # Same category
        if e1.category != e2.category:
            return False
        
        # Overlapping regions
        regions1 = set(r.lower() for r in e1.affected_regions)
        regions2 = set(r.lower() for r in e2.affected_regions)
        
        if not regions1 & regions2:
            return False
        
        # Similar timeframe (within 24 hours)
        time_diff = abs((e1.first_reported - e2.first_reported).total_seconds())
        if time_diff > 86400:  # 24 hours
            return False
        
        return True
    
    def _merge_events(self, events: List[RiskEvent]) -> RiskEvent:
        """Merge multiple similar events into one."""
        primary = events[0]
        
        # Combine sources
        all_sources = []
        for e in events:
            all_sources.extend(e.source_articles)
        
        # Use highest severity
        severity = max(e.severity for e in events)
        
        # Combine regions
        all_regions = set()
        for e in events:
            all_regions.update(e.affected_regions)
        
        # Use earliest report time
        first_reported = min(e.first_reported for e in events)
        
        # Increase confidence with more sources
        confidence = min(0.95, 0.6 + len(events) * 0.1)
        
        return RiskEvent(
            event_id=primary.event_id,
            category=primary.category,
            severity=severity,
            title=primary.title,
            summary=primary.summary,
            affected_regions=list(all_regions),
            affected_ports=primary.affected_ports,
            risk_score_impact=max(e.risk_score_impact for e in events),
            source_articles=all_sources,
            first_reported=first_reported,
            last_updated=datetime.utcnow(),
            confidence=confidence,
            keywords=primary.keywords
        )
    
    def _generate_alerts(self, events: List[RiskEvent]) -> List[NewsAlert]:
        """Generate alerts for new/escalated events."""
        alerts = []
        
        for event in events:
            existing = self._active_events.get(event.event_id)
            
            if not existing:
                # New event
                alerts.append(NewsAlert(
                    alert_id=f"ALERT-{event.event_id}",
                    event=event,
                    alert_type="NEW_EVENT",
                    message=f"New {event.severity.value} risk event: {event.title}",
                    recommended_actions=self._get_recommended_actions(event)
                ))
            elif self._severity_value(event.severity) > self._severity_value(existing.severity):
                # Escalation
                alerts.append(NewsAlert(
                    alert_id=f"ALERT-{event.event_id}-ESC",
                    event=event,
                    alert_type="ESCALATION",
                    message=f"Risk event escalated to {event.severity.value}: {event.title}",
                    recommended_actions=self._get_recommended_actions(event)
                ))
        
        return alerts
    
    def _severity_value(self, severity: EventSeverity) -> int:
        """Get numeric value for severity comparison."""
        values = {
            EventSeverity.LOW: 1,
            EventSeverity.MEDIUM: 2,
            EventSeverity.HIGH: 3,
            EventSeverity.CRITICAL: 4
        }
        return values.get(severity, 0)
    
    def _get_recommended_actions(self, event: RiskEvent) -> List[str]:
        """Get recommended actions for an event."""
        actions = []
        
        if event.severity in [EventSeverity.HIGH, EventSeverity.CRITICAL]:
            actions.append("Review all active policies in affected regions")
            actions.append("Consider issuing risk advisories to clients")
        
        if event.category == EventCategory.PIRACY:
            actions.append("Verify security arrangements for vessels in area")
            actions.append("Check armed guard requirements")
        
        if event.category == EventCategory.PORT_DISRUPTION:
            actions.append("Contact affected port agents for status updates")
            actions.append("Assess delays impact on coverage periods")
        
        if event.category == EventCategory.NATURAL_DISASTER:
            actions.append("Monitor weather forecast updates")
            actions.append("Review cargo handling recommendations")
        
        return actions
