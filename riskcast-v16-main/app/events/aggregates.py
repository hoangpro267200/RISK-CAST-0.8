"""
Aggregate Root Implementations

Features:
1. Event-sourced aggregates
2. State reconstruction
3. Command handling
4. Invariant validation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
import uuid

from app.events.event_store import DomainEvent, EventType, EventStore


T = TypeVar('T', bound='Aggregate')


class Aggregate(ABC):
    """
    Base class for event-sourced aggregates.
    """
    
    def __init__(self, aggregate_id: Optional[str] = None):
        self.id = aggregate_id or str(uuid.uuid4())
        self.version = -1
        self._pending_events: List[DomainEvent] = []
    
    @property
    @abstractmethod
    def aggregate_type(self) -> str:
        """Return aggregate type name."""
        pass
    
    def apply_event(self, event: DomainEvent):
        """Apply an event to update state."""
        handler_name = f"_apply_{event.event_type.replace('.', '_')}"
        handler = getattr(self, handler_name, None)
        
        if handler:
            handler(event)
        
        self.version = event.version
    
    def _raise_event(self, event_type: str, data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Raise a new domain event."""
        event = DomainEvent(
            event_type=event_type,
            aggregate_type=self.aggregate_type,
            aggregate_id=self.id,
            version=self.version + 1,
            data=data,
            metadata=metadata or {}
        )
        
        self._pending_events.append(event)
        self.apply_event(event)
    
    def get_pending_events(self) -> List[DomainEvent]:
        """Get pending events and clear them."""
        events = self._pending_events
        self._pending_events = []
        return events
    
    @classmethod
    async def load(
        cls: Type[T],
        aggregate_id: str,
        event_store: EventStore
    ) -> Optional[T]:
        """Load aggregate from event store."""
        # Try to load from snapshot first
        snapshot = await event_store.get_latest_snapshot(
            cls.__name__, aggregate_id
        )
        
        if snapshot:
            version, state = snapshot
            instance = cls._from_snapshot(aggregate_id, state)
            from_version = version + 1
        else:
            instance = cls(aggregate_id)
            from_version = 0
        
        # Load remaining events
        events = await event_store.get_events(
            instance.aggregate_type,
            aggregate_id,
            from_version
        )
        
        if not events and not snapshot:
            return None
        
        for event in events:
            instance.apply_event(event)
        
        return instance
    
    @classmethod
    def _from_snapshot(cls: Type[T], aggregate_id: str, state: Dict) -> T:
        """Reconstruct from snapshot state."""
        instance = cls(aggregate_id)
        instance.__dict__.update(state)
        return instance
    
    def to_snapshot(self) -> Dict:
        """Convert to snapshot state."""
        state = self.__dict__.copy()
        state.pop('_pending_events', None)
        return state


class QuoteAggregate(Aggregate):
    """Quote aggregate root."""
    
    @property
    def aggregate_type(self) -> str:
        return "Quote"
    
    def __init__(self, aggregate_id: Optional[str] = None):
        super().__init__(aggregate_id)
        self.status = "DRAFT"
        self.cargo_type: Optional[str] = None
        self.cargo_value_usd: float = 0
        self.origin_port: Optional[str] = None
        self.destination_port: Optional[str] = None
        self.risk_score: float = 0
        self.total_premium_usd: float = 0
        self.coverage_type: Optional[str] = None
        self.valid_until: Optional[datetime] = None
        self.customer_id: Optional[str] = None
        self.decline_reason: Optional[str] = None
    
    # Commands
    def request_quote(
        self,
        customer_id: str,
        cargo_type: str,
        cargo_value_usd: float,
        origin_port: str,
        destination_port: str,
        coverage_type: str,
        metadata: Dict = None
    ):
        """Request a new quote."""
        if self.version >= 0:
            raise InvalidOperationError("Quote already exists")
        
        self._raise_event(
            EventType.QUOTE_REQUESTED,
            {
                "customer_id": customer_id,
                "cargo_type": cargo_type,
                "cargo_value_usd": cargo_value_usd,
                "origin_port": origin_port,
                "destination_port": destination_port,
                "coverage_type": coverage_type
            },
            metadata
        )
    
    def set_calculated_premium(
        self,
        risk_score: float,
        total_premium_usd: float,
        valid_until: datetime,
        pricing_breakdown: Dict
    ):
        """Set calculated premium."""
        if self.status != "DRAFT":
            raise InvalidOperationError(f"Cannot calculate for quote in status {self.status}")
        
        self._raise_event(
            EventType.QUOTE_CALCULATED,
            {
                "risk_score": risk_score,
                "total_premium_usd": total_premium_usd,
                "valid_until": valid_until.isoformat(),
                "pricing_breakdown": pricing_breakdown
            }
        )
    
    def accept(self, accepted_by: str):
        """Accept the quote."""
        if self.status != "PENDING":
            raise InvalidOperationError(f"Cannot accept quote in status {self.status}")
        
        if self.valid_until and datetime.utcnow() > self.valid_until:
            raise InvalidOperationError("Quote has expired")
        
        self._raise_event(
            EventType.QUOTE_ACCEPTED,
            {"accepted_by": accepted_by, "accepted_at": datetime.utcnow().isoformat()}
        )
    
    def decline(self, reason: str, declined_by: str):
        """Decline the quote."""
        if self.status not in ["PENDING", "DRAFT"]:
            raise InvalidOperationError(f"Cannot decline quote in status {self.status}")
        
        self._raise_event(
            EventType.QUOTE_DECLINED,
            {"reason": reason, "declined_by": declined_by}
        )
    
    # Event handlers
    def _apply_quote_requested(self, event: DomainEvent):
        self.status = "DRAFT"
        self.customer_id = event.data["customer_id"]
        self.cargo_type = event.data["cargo_type"]
        self.cargo_value_usd = event.data["cargo_value_usd"]
        self.origin_port = event.data["origin_port"]
        self.destination_port = event.data["destination_port"]
        self.coverage_type = event.data["coverage_type"]
    
    def _apply_quote_calculated(self, event: DomainEvent):
        self.status = "PENDING"
        self.risk_score = event.data["risk_score"]
        self.total_premium_usd = event.data["total_premium_usd"]
        self.valid_until = datetime.fromisoformat(event.data["valid_until"])
    
    def _apply_quote_accepted(self, event: DomainEvent):
        self.status = "ACCEPTED"
    
    def _apply_quote_declined(self, event: DomainEvent):
        self.status = "DECLINED"
        self.decline_reason = event.data["reason"]


class PolicyAggregate(Aggregate):
    """Policy aggregate root."""
    
    @property
    def aggregate_type(self) -> str:
        return "Policy"
    
    def __init__(self, aggregate_id: Optional[str] = None):
        super().__init__(aggregate_id)
        self.status = "DRAFT"
        self.quote_id: Optional[str] = None
        self.customer_id: Optional[str] = None
        self.policy_number: Optional[str] = None
        self.effective_from: Optional[datetime] = None
        self.effective_to: Optional[datetime] = None
        self.total_premium_usd: float = 0
        self.coverage_limit_usd: float = 0
        self.claims: List[str] = []
    
    def create_from_quote(
        self,
        quote_id: str,
        customer_id: str,
        policy_number: str,
        effective_from: datetime,
        effective_to: datetime,
        total_premium_usd: float,
        coverage_limit_usd: float,
        metadata: Dict = None
    ):
        """Create policy from accepted quote."""
        self._raise_event(
            EventType.POLICY_CREATED,
            {
                "quote_id": quote_id,
                "customer_id": customer_id,
                "policy_number": policy_number,
                "effective_from": effective_from.isoformat(),
                "effective_to": effective_to.isoformat(),
                "total_premium_usd": total_premium_usd,
                "coverage_limit_usd": coverage_limit_usd
            },
            metadata
        )
    
    def activate(self):
        """Activate the policy."""
        if self.status != "DRAFT":
            raise InvalidOperationError("Can only activate draft policies")
        
        self._raise_event(EventType.POLICY_ACTIVATED, {})
    
    def cancel(self, reason: str, cancelled_by: str):
        """Cancel the policy."""
        if self.status != "ACTIVE":
            raise InvalidOperationError("Can only cancel active policies")
        
        self._raise_event(
            EventType.POLICY_CANCELLED,
            {"reason": reason, "cancelled_by": cancelled_by}
        )
    
    def _apply_policy_created(self, event: DomainEvent):
        self.status = "DRAFT"
        self.quote_id = event.data["quote_id"]
        self.customer_id = event.data["customer_id"]
        self.policy_number = event.data["policy_number"]
        self.effective_from = datetime.fromisoformat(event.data["effective_from"])
        self.effective_to = datetime.fromisoformat(event.data["effective_to"])
        self.total_premium_usd = event.data["total_premium_usd"]
        self.coverage_limit_usd = event.data["coverage_limit_usd"]
    
    def _apply_policy_activated(self, event: DomainEvent):
        self.status = "ACTIVE"
    
    def _apply_policy_cancelled(self, event: DomainEvent):
        self.status = "CANCELLED"


class ClaimAggregate(Aggregate):
    """Claim aggregate root."""
    
    @property
    def aggregate_type(self) -> str:
        return "Claim"
    
    def __init__(self, aggregate_id: Optional[str] = None):
        super().__init__(aggregate_id)
        self.status = "DRAFT"
        self.policy_id: Optional[str] = None
        self.claim_number: Optional[str] = None
        self.loss_date: Optional[datetime] = None
        self.loss_type: Optional[str] = None
        self.claimed_amount_usd: float = 0
        self.approved_amount_usd: float = 0
        self.denial_reason: Optional[str] = None
        self.documents: List[Dict] = []
    
    def file_claim(
        self,
        policy_id: str,
        claim_number: str,
        loss_date: datetime,
        loss_type: str,
        loss_description: str,
        claimed_amount_usd: float,
        filed_by: str
    ):
        """File a new claim."""
        self._raise_event(
            EventType.CLAIM_FILED,
            {
                "policy_id": policy_id,
                "claim_number": claim_number,
                "loss_date": loss_date.isoformat(),
                "loss_type": loss_type,
                "loss_description": loss_description,
                "claimed_amount_usd": claimed_amount_usd,
                "filed_by": filed_by
            }
        )
    
    def add_document(self, document_id: str, document_type: str, filename: str):
        """Add supporting document."""
        self._raise_event(
            EventType.CLAIM_DOCUMENTED,
            {
                "document_id": document_id,
                "document_type": document_type,
                "filename": filename
            }
        )
    
    def approve(self, approved_amount_usd: float, approved_by: str, notes: str = ""):
        """Approve the claim."""
        if self.status not in ["FILED", "IN_REVIEW"]:
            raise InvalidOperationError(f"Cannot approve claim in status {self.status}")
        
        self._raise_event(
            EventType.CLAIM_APPROVED,
            {
                "approved_amount_usd": approved_amount_usd,
                "approved_by": approved_by,
                "notes": notes
            }
        )
    
    def deny(self, reason: str, denied_by: str):
        """Deny the claim."""
        if self.status not in ["FILED", "IN_REVIEW"]:
            raise InvalidOperationError(f"Cannot deny claim in status {self.status}")
        
        self._raise_event(
            EventType.CLAIM_DENIED,
            {"reason": reason, "denied_by": denied_by}
        )
    
    def pay(self, paid_amount_usd: float, payment_reference: str):
        """Record claim payment."""
        if self.status != "APPROVED":
            raise InvalidOperationError("Can only pay approved claims")
        
        self._raise_event(
            EventType.CLAIM_PAID,
            {
                "paid_amount_usd": paid_amount_usd,
                "payment_reference": payment_reference
            }
        )
    
    def _apply_claim_filed(self, event: DomainEvent):
        self.status = "FILED"
        self.policy_id = event.data["policy_id"]
        self.claim_number = event.data["claim_number"]
        self.loss_date = datetime.fromisoformat(event.data["loss_date"])
        self.loss_type = event.data["loss_type"]
        self.claimed_amount_usd = event.data["claimed_amount_usd"]
    
    def _apply_claim_documented(self, event: DomainEvent):
        self.documents.append({
            "document_id": event.data["document_id"],
            "document_type": event.data["document_type"],
            "filename": event.data["filename"]
        })
    
    def _apply_claim_approved(self, event: DomainEvent):
        self.status = "APPROVED"
        self.approved_amount_usd = event.data["approved_amount_usd"]
    
    def _apply_claim_denied(self, event: DomainEvent):
        self.status = "DENIED"
        self.denial_reason = event.data["reason"]
    
    def _apply_claim_paid(self, event: DomainEvent):
        self.status = "PAID"


class InvalidOperationError(Exception):
    """Raised when an invalid operation is attempted on an aggregate."""
    pass
