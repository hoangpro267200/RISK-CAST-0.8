"""
News & Events Data Models
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class EventCategory(str, Enum):
    """Risk event categories."""
    NATURAL_DISASTER = "NATURAL_DISASTER"
    PIRACY = "PIRACY"
    POLITICAL_INSTABILITY = "POLITICAL_INSTABILITY"
    PORT_DISRUPTION = "PORT_DISRUPTION"
    SANCTIONS = "SANCTIONS"
    ACCIDENT = "ACCIDENT"
    STRIKE = "STRIKE"
    PANDEMIC = "PANDEMIC"
    WAR_CONFLICT = "WAR_CONFLICT"
    CYBER_ATTACK = "CYBER_ATTACK"
    REGULATORY_CHANGE = "REGULATORY_CHANGE"
    OTHER = "OTHER"


class EventSeverity(str, Enum):
    """Event severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class NewsArticle:
    """News article data."""
    article_id: str
    title: str
    description: Optional[str]
    content: Optional[str]
    source: str
    source_name: str
    url: str
    published_at: datetime
    
    # Optional fields
    author: Optional[str] = None
    image_url: Optional[str] = None


@dataclass
class RiskEvent:
    """Detected risk event."""
    event_id: str
    category: EventCategory
    severity: EventSeverity
    
    title: str
    summary: str
    
    # Entities
    affected_regions: List[str] = field(default_factory=list)
    affected_ports: List[str] = field(default_factory=list)
    affected_routes: List[str] = field(default_factory=list)
    mentioned_vessels: List[str] = field(default_factory=list)
    mentioned_companies: List[str] = field(default_factory=list)
    
    # Risk impact
    risk_score_impact: float = 0.0
    estimated_duration_days: Optional[int] = None
    
    # Sources
    source_articles: List[str] = field(default_factory=list)
    first_reported: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Status
    is_active: bool = True
    confidence: float = 0.8
    
    # Metadata
    keywords: List[str] = field(default_factory=list)
    raw_data: Dict = field(default_factory=dict)


@dataclass
class NewsAlert:
    """Alert generated from news event."""
    alert_id: str
    event: RiskEvent
    
    alert_type: str  # "NEW_EVENT", "ESCALATION", "UPDATE", "RESOLVED"
    message: str
    
    # Optional fields
    recommended_actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    notified: bool = False
