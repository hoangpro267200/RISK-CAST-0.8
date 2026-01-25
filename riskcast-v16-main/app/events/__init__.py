"""
Event Sourcing and CQRS Module

Provides:
- Event Store for append-only event storage
- Aggregates for domain logic
- Projections for read models
- Complete audit trail
"""

from app.events.event_store import (
    EventStore,
    DomainEvent,
    EventType,
    StoredEvent,
    AggregateSnapshot,
    ConcurrencyError,
)

from app.events.aggregates import (
    Aggregate,
    QuoteAggregate,
    PolicyAggregate,
    ClaimAggregate,
    InvalidOperationError,
)

from app.events.projections import (
    Projection,
    QuoteSummaryProjection,
    DailyMetricsProjection,
    ProjectionManager,
)

__all__ = [
    # Event Store
    "EventStore",
    "DomainEvent",
    "EventType",
    "StoredEvent",
    "AggregateSnapshot",
    "ConcurrencyError",
    # Aggregates
    "Aggregate",
    "QuoteAggregate",
    "PolicyAggregate",
    "ClaimAggregate",
    "InvalidOperationError",
    # Projections
    "Projection",
    "QuoteSummaryProjection",
    "DailyMetricsProjection",
    "ProjectionManager",
]
