"""
Event Projections (Read Models)

Features:
1. Real-time projections
2. Catchup projections
3. Multiple read models
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Type
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.events.event_store import DomainEvent, EventStore, EventType
from app.core.logging import get_logger


logger = get_logger(__name__)


class Projection(ABC):
    """Base class for projections."""
    
    @property
    @abstractmethod
    def projection_name(self) -> str:
        """Unique name for this projection."""
        pass
    
    @property
    @abstractmethod
    def handles_events(self) -> List[str]:
        """List of event types this projection handles."""
        pass
    
    @abstractmethod
    async def apply(self, event: DomainEvent, session: AsyncSession):
        """Apply an event to update the read model."""
        pass
    
    async def rebuild(self, event_store: EventStore, session: AsyncSession):
        """Rebuild projection from all events."""
        position = 0
        batch_size = 1000
        
        while True:
            events = await event_store.get_all_events(position, batch_size)
            if not events:
                break
            
            for event in events:
                if event.event_type in self.handles_events:
                    await self.apply(event, session)
            
            position += len(events)
            await session.commit()
        
        logger.info(f"Rebuilt projection {self.projection_name} with {position} events")


class QuoteSummaryProjection(Projection):
    """
    Projects quote summaries for fast querying.
    """
    
    @property
    def projection_name(self) -> str:
        return "quote_summary"
    
    @property
    def handles_events(self) -> List[str]:
        return [
            EventType.QUOTE_REQUESTED,
            EventType.QUOTE_CALCULATED,
            EventType.QUOTE_ACCEPTED,
            EventType.QUOTE_DECLINED,
            EventType.QUOTE_EXPIRED
        ]
    
    async def apply(self, event: DomainEvent, session: AsyncSession):
        """Update quote summary read model."""
        from app.models.read_models import QuoteSummary
        
        # Get or create summary
        result = await session.execute(
            select(QuoteSummary).where(QuoteSummary.quote_id == event.aggregate_id)
        )
        summary = result.scalar_one_or_none()
        
        if event.event_type == EventType.QUOTE_REQUESTED:
            if not summary:
                summary = QuoteSummary(
                    quote_id=event.aggregate_id,
                    customer_id=event.data["customer_id"],
                    cargo_type=event.data["cargo_type"],
                    cargo_value_usd=event.data["cargo_value_usd"],
                    origin_port=event.data["origin_port"],
                    destination_port=event.data["destination_port"],
                    status="DRAFT",
                    created_at=event.timestamp
                )
                session.add(summary)
        
        elif event.event_type == EventType.QUOTE_CALCULATED:
            if summary:
                summary.status = "PENDING"
                summary.risk_score = event.data["risk_score"]
                summary.total_premium_usd = event.data["total_premium_usd"]
                summary.valid_until = datetime.fromisoformat(event.data["valid_until"])
        
        elif event.event_type == EventType.QUOTE_ACCEPTED:
            if summary:
                summary.status = "ACCEPTED"
                summary.accepted_at = event.timestamp
        
        elif event.event_type == EventType.QUOTE_DECLINED:
            if summary:
                summary.status = "DECLINED"
                summary.decline_reason = event.data.get("reason")


class DailyMetricsProjection(Projection):
    """
    Projects daily business metrics.
    """
    
    @property
    def projection_name(self) -> str:
        return "daily_metrics"
    
    @property
    def handles_events(self) -> List[str]:
        return [
            EventType.QUOTE_REQUESTED,
            EventType.QUOTE_ACCEPTED,
            EventType.POLICY_CREATED,
            EventType.CLAIM_FILED,
            EventType.CLAIM_PAID
        ]
    
    async def apply(self, event: DomainEvent, session: AsyncSession):
        """Update daily metrics."""
        from app.models.read_models import DailyMetrics
        
        event_date = event.timestamp.date()
        
        result = await session.execute(
            select(DailyMetrics).where(DailyMetrics.date == event_date)
        )
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            metrics = DailyMetrics(date=event_date)
            session.add(metrics)
        
        if event.event_type == EventType.QUOTE_REQUESTED:
            metrics.quotes_requested += 1
            metrics.total_quote_value += event.data.get("cargo_value_usd", 0)
        
        elif event.event_type == EventType.QUOTE_ACCEPTED:
            metrics.quotes_accepted += 1
        
        elif event.event_type == EventType.POLICY_CREATED:
            metrics.policies_created += 1
            metrics.total_premium += event.data.get("total_premium_usd", 0)
        
        elif event.event_type == EventType.CLAIM_FILED:
            metrics.claims_filed += 1
            metrics.total_claimed += event.data.get("claimed_amount_usd", 0)
        
        elif event.event_type == EventType.CLAIM_PAID:
            metrics.claims_paid += 1
            metrics.total_paid += event.data.get("paid_amount_usd", 0)


class ProjectionManager:
    """Manages all projections."""
    
    def __init__(self, event_store: EventStore, session: AsyncSession):
        self.event_store = event_store
        self.session = session
        self.projections: Dict[str, Projection] = {}
    
    def register(self, projection: Projection):
        """Register a projection."""
        self.projections[projection.projection_name] = projection
    
    async def apply_event(self, event: DomainEvent):
        """Apply event to all relevant projections."""
        for projection in self.projections.values():
            if event.event_type in projection.handles_events:
                await projection.apply(event, self.session)
    
    async def rebuild_all(self):
        """Rebuild all projections."""
        for projection in self.projections.values():
            await projection.rebuild(self.event_store, self.session)
    
    async def rebuild_projection(self, name: str):
        """Rebuild a specific projection."""
        projection = self.projections.get(name)
        if projection:
            await projection.rebuild(self.event_store, self.session)
