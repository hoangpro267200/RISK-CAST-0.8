"""
Immutable Audit Ledger with Hash Chain

This is the FOUNDATION of insurance-grade auditability.
Every event is cryptographically linked to the previous event,
making the audit trail tamper-evident.

Key properties:
1. Append-only (events cannot be modified or deleted)
2. Hash-chained (each event includes hash of previous)
3. Timestamped with server time
4. Signed with system key (HMAC)
5. Verifiable integrity
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Column, DateTime, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Session

from app.database import Base

logger = logging.getLogger(__name__)


def _get_signing_key() -> str:
    try:
        from app.config import settings
        return getattr(settings, "AUDIT_SIGNING_KEY", None) or getattr(
            settings, "SECRET_KEY", "your-secret-signing-key-change-in-production"
        )
    except Exception:
        return "your-secret-signing-key-change-in-production"


class EventType(str, Enum):
    """Categories of audit events."""

    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    UNDERWRITING = "UNDERWRITING"
    QUOTE = "QUOTE"
    POLICY = "POLICY"
    CLAIM = "CLAIM"
    CLAIM_ADJUDICATION = "CLAIM_ADJUDICATION"
    PAYOUT = "PAYOUT"
    DATA_FETCH = "DATA_FETCH"
    DATA_IMPORT = "DATA_IMPORT"
    DATA_COLLECTION = "DATA_COLLECTION"
    DATA_REFRESH = "DATA_REFRESH"
    DATA_VALIDATION = "DATA_VALIDATION"
    MODEL_CALIBRATION = "MODEL_CALIBRATION"
    MODEL_VERSION = "MODEL_VERSION"
    MODEL_PUBLISH = "MODEL_PUBLISH"
    EVIDENCE = "EVIDENCE"
    EVIDENCE_SEAL = "EVIDENCE_SEAL"
    COMPLIANCE = "COMPLIANCE"
    GDPR = "GDPR"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    SYSTEM = "SYSTEM"
    ALERT = "ALERT"


class ActorType(str, Enum):
    """Types of actors that can generate events."""

    USER = "USER"
    SYSTEM = "SYSTEM"
    SCHEDULER = "SCHEDULER"
    API = "API"
    ORACLE = "ORACLE"


class AuditEventImmutable(Base):
    """
    Immutable audit event with hash chain.

    Each event contains:
    - Unique ID
    - Sequence number (monotonically increasing, global)
    - Event details
    - Hash of this event
    - Hash of previous event (chain link)
    - HMAC signature
    """

    __tablename__ = "audit_events_immutable"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_number = Column(Integer, nullable=False, unique=True)

    event_type = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(200), nullable=False)
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(String(200), nullable=True)
    tenant_id = Column(String(26), nullable=True)

    payload_json = Column(JSON, nullable=True)
    event_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    server_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    prev_event_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False)
    hmac_signature = Column(String(64), nullable=False)

    source_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("sequence_number", name="uq_immutable_audit_sequence"),
        Index("idx_immutable_audit_type", "event_type"),
        Index("idx_immutable_audit_entity", "entity_type", "entity_id"),
        Index("idx_immutable_audit_actor", "actor_type", "actor_id"),
        Index("idx_immutable_audit_timestamp", "event_timestamp"),
        Index("idx_immutable_audit_tenant", "tenant_id"),
        Index("idx_immutable_audit_sequence", "sequence_number"),
        Index("idx_immutable_audit_hash", "event_hash"),
    )


class ImmutableAuditChainTip(Base):
    """Single-row table storing global chain tip for atomic appends."""

    __tablename__ = "immutable_audit_chain_tip"

    id = Column(Integer, primary_key=True)  # always 1
    next_sequence = Column(Integer, nullable=False, server_default="1")
    latest_hash = Column(String(64), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


@dataclass
class ChainVerificationResult:
    """Result of hash chain verification."""

    is_valid: bool
    events_checked: int
    first_event_sequence: int
    last_event_sequence: int
    broken_at_sequence: Optional[int]
    error_message: Optional[str]
    verification_hash: str
    verified_at: datetime


class ImmutableAuditLedger:
    """
    Immutable audit ledger with cryptographic hash chain.

    CRITICAL for insurance:
    - Every action is recorded
    - Records cannot be modified
    - Tampering is detectable
    - Full audit trail for regulators
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, db: Session, signing_key: Optional[str] = None):
        self.db = db
        self.signing_key = (signing_key or _get_signing_key()).encode("utf-8")
        self._last_event_cache: Optional[Tuple[int, str]] = None

    def append_event(
        self,
        event_type: str,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_type: str = "SYSTEM",
        actor_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditEventImmutable:
        """
        Append a new event to the audit ledger.

        This is the ONLY way to add events. Events cannot be modified or deleted.
        Uses chain-tip locking for safe concurrent appends.
        """
        now = datetime.utcnow()

        tip = (
            self.db.query(ImmutableAuditChainTip)
            .filter(ImmutableAuditChainTip.id == 1)
            .with_for_update()
            .first()
        )
        if not tip:
            tip = ImmutableAuditChainTip(
                id=1,
                next_sequence=1,
                latest_hash=self.GENESIS_HASH,
                updated_at=now,
            )
            self.db.add(tip)
            self.db.flush()
            prev_hash = self.GENESIS_HASH
            next_seq = 1
        else:
            next_seq = tip.next_sequence
            prev_hash = tip.latest_hash

        event = AuditEventImmutable(
            sequence_number=next_seq,
            event_type=event_type,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            actor_type=actor_type,
            actor_id=str(actor_id) if actor_id else None,
            tenant_id=tenant_id,
            payload_json=payload,
            event_timestamp=now,
            server_timestamp=now,
            prev_event_hash=prev_hash,
            event_hash="",  # set below
            hmac_signature="",  # set below
            source_ip=source_ip,
            user_agent=user_agent,
            request_id=request_id,
        )
        self.db.add(event)
        self.db.flush()

        event.event_hash = self._compute_event_hash(event)
        event.hmac_signature = self._compute_hmac(event)

        tip.next_sequence = next_seq + 1
        tip.latest_hash = event.event_hash
        tip.updated_at = now

        self.db.commit()
        self.db.refresh(event)
        self._last_event_cache = (next_seq, event.event_hash)

        logger.debug(
            "Audit event appended: seq=%s, type=%s, action=%s, hash=%s...",
            next_seq,
            event_type,
            action,
            event.event_hash[:16],
        )
        return event

    def verify_chain(
        self,
        start_sequence: Optional[int] = None,
        end_sequence: Optional[int] = None,
    ) -> ChainVerificationResult:
        """
        Verify the integrity of the hash chain.

        Returns verification result including whether the chain is valid,
        where it breaks (if broken), and how many events were verified.
        """
        query = self.db.query(AuditEventImmutable).order_by(
            AuditEventImmutable.sequence_number.asc()
        )
        if start_sequence is not None:
            query = query.filter(AuditEventImmutable.sequence_number >= start_sequence)
        if end_sequence is not None:
            query = query.filter(AuditEventImmutable.sequence_number <= end_sequence)
        events = query.all()

        if not events:
            return ChainVerificationResult(
                is_valid=True,
                events_checked=0,
                first_event_sequence=0,
                last_event_sequence=0,
                broken_at_sequence=None,
                error_message="No events to verify",
                verification_hash="",
                verified_at=datetime.utcnow(),
            )

        first_seq = events[0].sequence_number
        last_seq = events[-1].sequence_number
        prev_hash: Optional[str] = None

        if first_seq == 1:
            if events[0].prev_event_hash != self.GENESIS_HASH:
                return ChainVerificationResult(
                    is_valid=False,
                    events_checked=0,
                    first_event_sequence=first_seq,
                    last_event_sequence=last_seq,
                    broken_at_sequence=1,
                    error_message="First event does not link to genesis hash",
                    verification_hash="",
                    verified_at=datetime.utcnow(),
                )
        else:
            prior = (
                self.db.query(AuditEventImmutable)
                .filter(AuditEventImmutable.sequence_number == first_seq - 1)
                .first()
            )
            if prior and events[0].prev_event_hash != prior.event_hash:
                return ChainVerificationResult(
                    is_valid=False,
                    events_checked=0,
                    first_event_sequence=first_seq,
                    last_event_sequence=last_seq,
                    broken_at_sequence=first_seq,
                    error_message=f"Chain broken at sequence {first_seq}: prev_hash mismatch",
                    verification_hash="",
                    verified_at=datetime.utcnow(),
                )

        for i, event in enumerate(events):
            computed = self._compute_event_hash(event)
            if computed != event.event_hash:
                return ChainVerificationResult(
                    is_valid=False,
                    events_checked=i,
                    first_event_sequence=first_seq,
                    last_event_sequence=last_seq,
                    broken_at_sequence=event.sequence_number,
                    error_message=f"Event hash mismatch at sequence {event.sequence_number}",
                    verification_hash="",
                    verified_at=datetime.utcnow(),
                )
            sig = self._compute_hmac(event)
            if sig != event.hmac_signature:
                return ChainVerificationResult(
                    is_valid=False,
                    events_checked=i,
                    first_event_sequence=first_seq,
                    last_event_sequence=last_seq,
                    broken_at_sequence=event.sequence_number,
                    error_message=f"HMAC signature mismatch at sequence {event.sequence_number}",
                    verification_hash="",
                    verified_at=datetime.utcnow(),
                )
            if prev_hash is not None and event.prev_event_hash != prev_hash:
                return ChainVerificationResult(
                    is_valid=False,
                    events_checked=i,
                    first_event_sequence=first_seq,
                    last_event_sequence=last_seq,
                    broken_at_sequence=event.sequence_number,
                    error_message=f"Chain broken at sequence {event.sequence_number}",
                    verification_hash="",
                    verified_at=datetime.utcnow(),
                )
            prev_hash = event.event_hash

        verification_hash = hashlib.sha256(
            f"{first_seq}:{last_seq}:{events[-1].event_hash}".encode()
        ).hexdigest()

        return ChainVerificationResult(
            is_valid=True,
            events_checked=len(events),
            first_event_sequence=first_seq,
            last_event_sequence=last_seq,
            broken_at_sequence=None,
            error_message=None,
            verification_hash=verification_hash,
            verified_at=datetime.utcnow(),
        )

    def get_events_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[AuditEventImmutable]:
        """Get all events for a specific entity."""
        query = self.db.query(AuditEventImmutable).filter(
            AuditEventImmutable.entity_type == entity_type,
            AuditEventImmutable.entity_id == str(entity_id),
        )
        if tenant_id:
            query = query.filter(AuditEventImmutable.tenant_id == tenant_id)
        return query.order_by(AuditEventImmutable.sequence_number.asc()).all()

    def get_events_by_actor(
        self,
        actor_type: str,
        actor_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AuditEventImmutable]:
        """Get all events by a specific actor."""
        query = self.db.query(AuditEventImmutable).filter(
            AuditEventImmutable.actor_type == actor_type,
            AuditEventImmutable.actor_id == str(actor_id),
        )
        if start_time:
            query = query.filter(AuditEventImmutable.event_timestamp >= start_time)
        if end_time:
            query = query.filter(AuditEventImmutable.event_timestamp <= end_time)
        return query.order_by(AuditEventImmutable.sequence_number.asc()).all()

    def get_events_by_type(
        self,
        event_type: str,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[AuditEventImmutable]:
        """Get events by type and optionally action."""
        query = self.db.query(AuditEventImmutable).filter(
            AuditEventImmutable.event_type == event_type
        )
        if action:
            query = query.filter(AuditEventImmutable.action == action)
        if start_time:
            query = query.filter(AuditEventImmutable.event_timestamp >= start_time)
        if end_time:
            query = query.filter(AuditEventImmutable.event_timestamp <= end_time)
        return (
            query.order_by(AuditEventImmutable.sequence_number.desc())
            .limit(limit)
            .all()
        )

    def export_for_compliance(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Export audit events for compliance/regulatory review.

        Includes verification proof that events have not been tampered with.
        """
        query = self.db.query(AuditEventImmutable).filter(
            AuditEventImmutable.event_timestamp >= start_date,
            AuditEventImmutable.event_timestamp <= end_date,
        )
        if tenant_id:
            query = query.filter(AuditEventImmutable.tenant_id == tenant_id)
        if event_types:
            query = query.filter(AuditEventImmutable.event_type.in_(event_types))
        events = query.order_by(AuditEventImmutable.sequence_number.asc()).all()

        if not events:
            return {
                "export_id": str(uuid.uuid4()),
                "generated_at": datetime.utcnow().isoformat(),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "event_count": 0,
                "events": [],
                "verification": None,
            }

        verification = self.verify_chain(
            start_sequence=events[0].sequence_number,
            end_sequence=events[-1].sequence_number,
        )
        serialized = []
        for e in events:
            serialized.append({
                "id": str(e.id),
                "sequence_number": e.sequence_number,
                "event_type": e.event_type,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "payload": e.payload_json,
                "event_timestamp": e.event_timestamp.isoformat(),
                "event_hash": e.event_hash,
                "prev_event_hash": e.prev_event_hash,
            })

        return {
            "export_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "event_count": len(events),
            "events": serialized,
            "verification": {
                "is_valid": verification.is_valid,
                "events_verified": verification.events_checked,
                "first_sequence": verification.first_event_sequence,
                "last_sequence": verification.last_event_sequence,
                "verification_hash": verification.verification_hash,
                "verified_at": verification.verified_at.isoformat(),
            },
        }

    def _compute_event_hash(self, event: AuditEventImmutable) -> str:
        """Compute SHA-256 hash of event. Includes all critical fields."""
        data = {
            "sequence_number": event.sequence_number,
            "event_type": event.event_type,
            "action": event.action,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "actor_type": event.actor_type,
            "actor_id": event.actor_id,
            "tenant_id": event.tenant_id,
            "payload": event.payload_json,
            "event_timestamp": event.event_timestamp.isoformat(),
            "prev_event_hash": event.prev_event_hash,
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _compute_hmac(self, event: AuditEventImmutable) -> str:
        """Compute HMAC signature for event."""
        data = f"{event.sequence_number}:{event.event_hash}:{event.event_timestamp.isoformat()}"
        return hmac.new(self.signing_key, data.encode(), hashlib.sha256).hexdigest()


def create_immutable_audit_ledger(db: Session) -> ImmutableAuditLedger:
    """Create immutable audit ledger instance."""
    return ImmutableAuditLedger(db)
