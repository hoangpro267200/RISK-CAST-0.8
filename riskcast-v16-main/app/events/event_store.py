"""
Event Store Implementation

Features:
1. Append-only event storage
2. Event versioning
3. Snapshots for aggregates
4. Event replay
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from abc import ABC, abstractmethod

from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base

from app.core.logging import get_logger
from app.database import Base


logger = get_logger(__name__)


# =============================================================================
# Event Base Classes
# =============================================================================

class EventType(str, Enum):
    """Domain event types."""
    # Quote events
    QUOTE_REQUESTED = "quote.requested"
    QUOTE_CALCULATED = "quote.calculated"
    QUOTE_ACCEPTED = "quote.accepted"
    QUOTE_DECLINED = "quote.declined"
    QUOTE_EXPIRED = "quote.expired"
    QUOTE_MODIFIED = "quote.modified"
    
    # Policy events
    POLICY_CREATED = "policy.created"
    POLICY_ACTIVATED = "policy.activated"
    POLICY_CANCELLED = "policy.cancelled"
    POLICY_RENEWED = "policy.renewed"
    POLICY_ENDORSED = "policy.endorsed"
    
    # Claim events
    CLAIM_FILED = "claim.filed"
    CLAIM_DOCUMENTED = "claim.documented"
    CLAIM_ASSESSED = "claim.assessed"
    CLAIM_APPROVED = "claim.approved"
    CLAIM_DENIED = "claim.denied"
    CLAIM_PAID = "claim.paid"
    
    # Risk events
    RISK_ASSESSED = "risk.assessed"
    RISK_UPDATED = "risk.updated"
    MODEL_CALIBRATED = "model.calibrated"
    
    # Customer events
    CUSTOMER_REGISTERED = "customer.registered"
    CUSTOMER_VERIFIED = "customer.verified"
    CUSTOMER_TIER_CHANGED = "customer.tier_changed"


@dataclass
class DomainEvent:
    """Base class for domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    aggregate_type: str = ""
    aggregate_id: str = ""
    version: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata
        }
    
    def compute_hash(self) -> str:
        """Compute hash of event for integrity."""
        content = json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


# =============================================================================
# Event Store Model
# =============================================================================

class StoredEvent(Base):
    """Stored event in database."""
    __tablename__ = "event_store"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(String(36), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    metadata = Column(JSONB, default={})
    event_hash = Column(String(64), nullable=False)
    
    __table_args__ = (
        Index('ix_event_store_aggregate', 'aggregate_type', 'aggregate_id', 'version'),
        Index('ix_event_store_timestamp', 'timestamp'),
    )


class AggregateSnapshot(Base):
    """Snapshot of aggregate state."""
    __tablename__ = "aggregate_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(String(36), nullable=False)
    version = Column(Integer, nullable=False)
    state = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_snapshot_aggregate', 'aggregate_type', 'aggregate_id', 'version'),
    )


# =============================================================================
# Event Store
# =============================================================================

class EventStore:
    """
    Append-only event store for event sourcing.
    """
    
    def __init__(self, session: AsyncSession, snapshot_threshold: int = 100):
        self.session = session
        self.snapshot_threshold = snapshot_threshold
    
    async def append(
        self,
        event: DomainEvent,
        expected_version: Optional[int] = None
    ) -> StoredEvent:
        """
        Append an event to the store.
        
        Args:
            event: Event to append
            expected_version: Expected current version (for optimistic locking)
        
        Raises:
            ConcurrencyError: If version doesn't match
        """
        # Check version for optimistic concurrency
        if expected_version is not None:
            current_version = await self._get_current_version(
                event.aggregate_type, event.aggregate_id
            )
            if current_version != expected_version:
                raise ConcurrencyError(
                    f"Expected version {expected_version}, but current is {current_version}"
                )
        
        # Create stored event
        stored = StoredEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            version=event.version,
            timestamp=event.timestamp,
            data=event.data,
            metadata=event.metadata,
            event_hash=event.compute_hash()
        )
        
        self.session.add(stored)
        await self.session.flush()
        
        logger.info(
            f"Event appended: {event.event_type}",
            event_id=event.event_id,
            aggregate_id=event.aggregate_id,
            version=event.version
        )
        
        return stored
    
    async def append_batch(self, events: List[DomainEvent]) -> List[StoredEvent]:
        """Append multiple events atomically."""
        stored_events = []
        
        for event in events:
            stored = StoredEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                version=event.version,
                timestamp=event.timestamp,
                data=event.data,
                metadata=event.metadata,
                event_hash=event.compute_hash()
            )
            self.session.add(stored)
            stored_events.append(stored)
        
        await self.session.flush()
        return stored_events
    
    async def get_events(
        self,
        aggregate_type: str,
        aggregate_id: str,
        from_version: int = 0
    ) -> List[DomainEvent]:
        """Get all events for an aggregate from a specific version."""
        result = await self.session.execute(
            select(StoredEvent)
            .where(StoredEvent.aggregate_type == aggregate_type)
            .where(StoredEvent.aggregate_id == aggregate_id)
            .where(StoredEvent.version >= from_version)
            .order_by(StoredEvent.version)
        )
        
        stored_events = result.scalars().all()
        
        return [
            DomainEvent(
                event_id=e.event_id,
                event_type=e.event_type,
                aggregate_type=e.aggregate_type,
                aggregate_id=e.aggregate_id,
                version=e.version,
                timestamp=e.timestamp,
                data=e.data,
                metadata=e.metadata
            )
            for e in stored_events
        ]
    
    async def get_events_by_type(
        self,
        event_type: str,
        from_timestamp: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[DomainEvent]:
        """Get events by type, optionally from a timestamp."""
        query = select(StoredEvent).where(StoredEvent.event_type == event_type)
        
        if from_timestamp:
            query = query.where(StoredEvent.timestamp >= from_timestamp)
        
        query = query.order_by(StoredEvent.timestamp).limit(limit)
        
        result = await self.session.execute(query)
        stored_events = result.scalars().all()
        
        return [self._to_domain_event(e) for e in stored_events]
    
    async def get_all_events(
        self,
        from_position: int = 0,
        limit: int = 1000
    ) -> List[DomainEvent]:
        """Get all events from a position (for projections)."""
        result = await self.session.execute(
            select(StoredEvent)
            .where(StoredEvent.id > from_position)
            .order_by(StoredEvent.id)
            .limit(limit)
        )
        
        return [self._to_domain_event(e) for e in result.scalars().all()]
    
    async def save_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: str,
        version: int,
        state: Dict
    ):
        """Save an aggregate snapshot."""
        snapshot = AggregateSnapshot(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            version=version,
            state=state
        )
        self.session.add(snapshot)
        await self.session.flush()
        
        logger.debug(f"Snapshot saved for {aggregate_type}:{aggregate_id} at version {version}")
    
    async def get_latest_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: str
    ) -> Optional[Tuple[int, Dict]]:
        """Get the latest snapshot for an aggregate."""
        result = await self.session.execute(
            select(AggregateSnapshot)
            .where(AggregateSnapshot.aggregate_type == aggregate_type)
            .where(AggregateSnapshot.aggregate_id == aggregate_id)
            .order_by(AggregateSnapshot.version.desc())
            .limit(1)
        )
        
        snapshot = result.scalar_one_or_none()
        if snapshot:
            return snapshot.version, snapshot.state
        return None
    
    async def _get_current_version(
        self,
        aggregate_type: str,
        aggregate_id: str
    ) -> int:
        """Get current version of an aggregate."""
        result = await self.session.execute(
            select(StoredEvent.version)
            .where(StoredEvent.aggregate_type == aggregate_type)
            .where(StoredEvent.aggregate_id == aggregate_id)
            .order_by(StoredEvent.version.desc())
            .limit(1)
        )
        
        version = result.scalar_one_or_none()
        return version if version is not None else -1
    
    def _to_domain_event(self, stored: StoredEvent) -> DomainEvent:
        """Convert stored event to domain event."""
        return DomainEvent(
            event_id=stored.event_id,
            event_type=stored.event_type,
            aggregate_type=stored.aggregate_type,
            aggregate_id=stored.aggregate_id,
            version=stored.version,
            timestamp=stored.timestamp,
            data=stored.data,
            metadata=stored.metadata
        )


class ConcurrencyError(Exception):
    """Raised when there's a version conflict."""
    pass
