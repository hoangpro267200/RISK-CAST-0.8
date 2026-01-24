"""
Hash-Chained Audit Ledger Core Implementation

Provides append-only audit logging with hash chaining for integrity verification.
Each event links to the previous event via hash, forming an immutable chain.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent, AuditChainHead, ActorType


def compute_event_hash(event_data: dict, prev_hash: str | None) -> str:
    """
    Compute SHA256 hash of event data including previous hash.
    
    Uses canonical JSON serialization for deterministic hashing.
    Includes prev_hash in computation to form hash chain.
    
    Args:
        event_data: Dictionary with event data (excluding id, event_hash, sequence_num)
        prev_hash: Previous event hash (None for first event)
        
    Returns:
        SHA256 hash as hex string (64 characters)
    """
    # Build hash payload (exclude id, event_hash, sequence_num from hash computation)
    hash_payload = {
        "tenant_id": event_data.get("tenant_id"),
        "event_type": event_data.get("event_type"),
        "entity_type": event_data.get("entity_type"),
        "entity_id": event_data.get("entity_id"),
        "action": event_data.get("action"),
        "actor_type": event_data.get("actor_type"),
        "actor_id": event_data.get("actor_id"),
        "payload_json": event_data.get("payload_json") or {},
        "created_at": (
            event_data["created_at"].isoformat()
            if isinstance(event_data.get("created_at"), datetime)
            else str(event_data.get("created_at", ""))
        ),
        "prev_hash": prev_hash,
    }
    
    # Canonical JSON serialization (sorted keys, no whitespace)
    canonical_json = json.dumps(
        hash_payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    
    # Compute SHA256 hash
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass
class ChainVerificationResult:
    """Result of chain verification"""
    is_valid: bool
    total_events: int
    verified_events: int
    errors: List[str]
    
    def __repr__(self) -> str:
        return (
            f"ChainVerificationResult(is_valid={self.is_valid}, "
            f"total_events={self.total_events}, "
            f"verified_events={self.verified_events}, "
            f"errors={len(self.errors)})"
        )


class AuditLedger:
    """
    Hash-chained audit ledger for append-only event logging.
    
    Provides:
    - Thread-safe event appending with SELECT FOR UPDATE
    - Hash chain integrity verification
    - Querying events with filters
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize audit ledger.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.session = db_session
    
    def append_event(
        self,
        tenant_id: str,
        event_type: str,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor_type: str = "SYSTEM",
        actor_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Append a new event to the audit ledger.
        
        Uses SELECT FOR UPDATE to lock chain head row, ensuring:
        - Sequential sequence numbers per tenant
        - Correct prev_hash linking
        - Atomic chain head update
        
        All operations are performed in a single transaction.
        
        Args:
            tenant_id: Tenant ID (ULID String(26))
            event_type: Type of event (e.g., 'risk_assessment.created')
            action: Action performed (e.g., 'created', 'updated', 'deleted')
            entity_type: Type of entity affected (optional)
            entity_id: ID of entity affected (optional)
            actor_type: Type of actor (USER, SYSTEM, API_KEY) - defaults to SYSTEM
            actor_id: ID of actor (optional)
            payload: Event payload dictionary (optional)
            
        Returns:
            Created AuditEvent instance
            
        Raises:
            IntegrityError: If unique constraint violation (should not happen with proper locking)
        """
        # 1. Lock chain head row (SELECT FOR UPDATE)
        chain_head = (
            self.session.query(AuditChainHead)
            .filter(AuditChainHead.tenant_id == tenant_id)
            .with_for_update()
            .first()
        )
        
        # 2. Get current sequence_num and latest_hash
        if chain_head:
            next_sequence_num = chain_head.latest_sequence_num + 1
            prev_hash = chain_head.latest_hash
        else:
            # First event for this tenant
            next_sequence_num = 1
            prev_hash = None
            # Create chain head record
            chain_head = AuditChainHead(
                tenant_id=tenant_id,
                latest_sequence_num=0,
                latest_hash=None,
            )
            self.session.add(chain_head)
        
        # 3. Prepare event data
        event_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        event_data = {
            "id": event_id,
            "tenant_id": tenant_id,
            "sequence_num": next_sequence_num,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "payload_json": payload,
            "created_at": created_at,
        }
        
        # 4. Compute new event hash
        event_hash = compute_event_hash(event_data, prev_hash)
        event_data["prev_hash"] = prev_hash
        event_data["event_hash"] = event_hash
        
        # 5. Insert event
        event = AuditEvent(**event_data)
        self.session.add(event)
        
        # 6. Update chain head
        chain_head.latest_sequence_num = next_sequence_num
        chain_head.latest_hash = event_hash
        chain_head.updated_at = datetime.utcnow()
        
        # Commit transaction (all operations in same transaction)
        self.session.commit()
        self.session.refresh(event)
        
        return event
    
    def verify_chain(
        self, tenant_id: str, from_seq: int = 0
    ) -> ChainVerificationResult:
        """
        Verify hash chain integrity for a tenant.
        
        Checks:
        - Each event's prev_hash matches previous event's event_hash
        - Event hashes are correctly computed
        - Sequence numbers are sequential
        
        Args:
            tenant_id: Tenant ID
            from_seq: Starting sequence number (default: 0, verify all)
            
        Returns:
            ChainVerificationResult with verification status and errors
        """
        # Load events in sequence order
        query = (
            self.session.query(AuditEvent)
            .filter(AuditEvent.tenant_id == tenant_id)
            .filter(AuditEvent.sequence_num >= from_seq)
            .order_by(AuditEvent.sequence_num.asc())
        )
        events = query.all()
        
        if not events:
            return ChainVerificationResult(
                is_valid=True,
                total_events=0,
                verified_events=0,
                errors=[],
            )
        
        errors: List[str] = []
        verified_count = 0
        
        # Verify first event
        first_event = events[0]
        if first_event.sequence_num != from_seq and from_seq == 0:
            # First event should have sequence_num = 1 (or from_seq if specified)
            expected_seq = 1 if from_seq == 0 else from_seq
            if first_event.sequence_num != expected_seq:
                errors.append(
                    f"First event has wrong sequence_num: "
                    f"expected {expected_seq}, got {first_event.sequence_num}"
                )
        
        # Verify prev_hash is None for first event (or matches chain head if from_seq > 0)
        if first_event.sequence_num == 1 and first_event.prev_hash is not None:
            errors.append(
                f"First event (seq={first_event.sequence_num}) should have "
                f"prev_hash=None, got {first_event.prev_hash}"
            )
        
        # Recompute and verify first event hash
        first_event_data = {
            "tenant_id": first_event.tenant_id,
            "event_type": first_event.event_type,
            "entity_type": first_event.entity_type,
            "entity_id": first_event.entity_id,
            "action": first_event.action,
            "actor_type": first_event.actor_type,
            "actor_id": first_event.actor_id,
            "payload_json": first_event.payload_json,
            "created_at": first_event.created_at,
        }
        computed_hash = compute_event_hash(first_event_data, first_event.prev_hash)
        if computed_hash != first_event.event_hash:
            errors.append(
                f"Event seq={first_event.sequence_num} hash mismatch: "
                f"computed {computed_hash}, stored {first_event.event_hash}"
            )
        else:
            verified_count += 1
        
        # Verify chain links
        for i in range(1, len(events)):
            prev_event = events[i - 1]
            current_event = events[i]
            
            # Check sequence numbers are sequential
            expected_seq = prev_event.sequence_num + 1
            if current_event.sequence_num != expected_seq:
                errors.append(
                    f"Non-sequential sequence_num at seq={current_event.sequence_num}: "
                    f"expected {expected_seq}, got {current_event.sequence_num}"
                )
                continue
            
            # Check prev_hash links
            if current_event.prev_hash != prev_event.event_hash:
                errors.append(
                    f"Chain broken at seq={current_event.sequence_num}: "
                    f"prev_hash={current_event.prev_hash}, "
                    f"previous event_hash={prev_event.event_hash}"
                )
                continue
            
            # Recompute and verify current event hash
            current_event_data = {
                "tenant_id": current_event.tenant_id,
                "event_type": current_event.event_type,
                "entity_type": current_event.entity_type,
                "entity_id": current_event.entity_id,
                "action": current_event.action,
                "actor_type": current_event.actor_type,
                "actor_id": current_event.actor_id,
                "payload_json": current_event.payload_json,
                "created_at": current_event.created_at,
            }
            computed_hash = compute_event_hash(
                current_event_data, current_event.prev_hash
            )
            if computed_hash != current_event.event_hash:
                errors.append(
                    f"Event seq={current_event.sequence_num} hash mismatch: "
                    f"computed {computed_hash}, stored {current_event.event_hash}"
                )
            else:
                verified_count += 1
        
        is_valid = len(errors) == 0
        
        return ChainVerificationResult(
            is_valid=is_valid,
            total_events=len(events),
            verified_events=verified_count,
            errors=errors,
        )
    
    def get_events(
        self,
        tenant_id: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[AuditEvent]:
        """
        Get audit events with optional filters.
        
        Args:
            tenant_id: Tenant ID (required)
            entity_type: Filter by entity type (optional)
            entity_id: Filter by entity ID (optional)
            from_date: Filter events from this date (optional)
            to_date: Filter events to this date (optional)
            limit: Maximum number of events to return (optional)
            
        Returns:
            List of AuditEvent instances, ordered by sequence_num ascending
        """
        query = (
            self.session.query(AuditEvent)
            .filter(AuditEvent.tenant_id == tenant_id)
        )
        
        # Apply filters
        if entity_type is not None:
            query = query.filter(AuditEvent.entity_type == entity_type)
        
        if entity_id is not None:
            query = query.filter(AuditEvent.entity_id == entity_id)
        
        if from_date is not None:
            query = query.filter(AuditEvent.created_at >= from_date)
        
        if to_date is not None:
            query = query.filter(AuditEvent.created_at <= to_date)
        
        # Order by sequence number
        query = query.order_by(AuditEvent.sequence_num.asc())
        
        # Apply limit
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()
