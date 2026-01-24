"""
Hash-Chained Audit Ledger Models

Append-only audit trail with hash chaining for immutable event logging.
Each event links to the previous event via hash for chain integrity verification.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, BigInteger, DateTime, ForeignKey, JSON,
    Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class ActorType(str, enum.Enum):
    """Actor type for audit events"""
    USER = "USER"
    SYSTEM = "SYSTEM"
    API_KEY = "API_KEY"


class AuditEvent(Base):
    """
    Audit Event Model
    
    Append-only, hash-chained audit log entry.
    No UPDATE or DELETE operations allowed at application level.
    
    Fields:
    - id: UUID primary key
    - tenant_id: FK to tenants (ULID String(26))
    - sequence_num: Sequential number per tenant for ordering
    - prev_hash: SHA256 hash of previous event (NULL for first event)
    - event_hash: SHA256 hash of this event
    - event_type: Type of event (e.g., 'risk_assessment.created')
    - entity_type: Type of entity affected (e.g., 'risk_assessment')
    - entity_id: ID of entity affected
    - action: Action performed (e.g., 'created', 'updated', 'deleted')
    - actor_type: Type of actor (USER, SYSTEM, API_KEY)
    - actor_id: ID of actor
    - payload_json: Event payload (JSON)
    - created_at: Timestamp when event was created
    """
    
    __tablename__ = "legacy_audit_events"
    
    # Primary key (UUID)
    id = Column(String(36), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tenant association
    tenant_id = Column(
        String(26),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Chain fields
    sequence_num = Column(BigInteger, nullable=False, index=True)
    prev_hash = Column(String(64), nullable=True, index=True)  # NULL for first event
    event_hash = Column(String(64), nullable=False, index=True)  # SHA256 hex
    
    # Event data
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(String(100), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    
    # Actor
    actor_type = Column(String(50), nullable=False, index=True)  # USER, SYSTEM, API_KEY
    actor_id = Column(String(255), nullable=True, index=True)
    
    # Payload
    payload_json = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "sequence_num",
            name="uq_audit_events_tenant_sequence",
        ),
        Index("idx_audit_events_tenant_seq", "tenant_id", "sequence_num"),
        Index("idx_audit_events_entity", "entity_type", "entity_id"),
        Index("idx_audit_events_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<AuditEvent(id={self.id!r}, tenant_id={self.tenant_id!r}, "
            f"sequence_num={self.sequence_num}, event_type={self.event_type!r})>"
        )


class AuditChainHead(Base):
    """
    Audit Chain Head Model
    
    Tracks the latest event in the hash chain for each tenant.
    Used to maintain chain integrity and get the previous hash for new events.
    
    Fields:
    - tenant_id: FK to tenants (PK, ULID String(26))
    - latest_sequence_num: Latest sequence number for this tenant
    - latest_hash: SHA256 hash of the latest event
    - updated_at: Timestamp when chain head was last updated
    """
    
    __tablename__ = "legacy_audit_chain_heads"
    
    # Primary key (tenant_id)
    tenant_id = Column(
        String(26),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    
    # Chain state
    latest_sequence_num = Column(BigInteger, nullable=False, server_default="0")
    latest_hash = Column(String(64), nullable=True)  # SHA256 hex
    
    # Metadata
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return (
            f"<AuditChainHead(tenant_id={self.tenant_id!r}, "
            f"latest_sequence_num={self.latest_sequence_num}, "
            f"latest_hash={self.latest_hash!r})>"
        )
