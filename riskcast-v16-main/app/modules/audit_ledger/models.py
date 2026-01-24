"""
Audit Ledger Models
Append-only, hash-chained audit trail for immutable event logging
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    Index, CHAR
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base
from app.shared.models import BaseMixin


class ActorType(str, enum.Enum):
    """Actor type for audit events"""
    USER = "USER"
    API_KEY = "API_KEY"
    SYSTEM = "SYSTEM"


class AuditEvent(Base):
    """
    Audit Event Model
    
    Append-only, hash-chained audit log entry.
    No UPDATE or DELETE operations allowed at application level.
    """
    __tablename__ = "audit_events"
    
    # Primary key
    id = Column(String(26), primary_key=True, nullable=False)  # ULID
    
    # Tenant association (nullable for platform-level events)
    tenant_id = Column(String(26), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Event timestamp
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Actor information
    actor_type = Column(
        SQLEnum(ActorType, native_enum=False),
        nullable=False,
        index=True
    )
    actor_id = Column(String(100), nullable=False, index=True)
    
    # Action and resource
    action = Column(String(100), nullable=False, index=True)  # e.g., 'risk_assessment.created', 'risk_run.completed'
    resource_type = Column(String(100), nullable=False, index=True)  # e.g., 'risk_assessment', 'risk_run'
    resource_id = Column(String(100), nullable=False, index=True)
    
    # Context information
    context_json = Column(JSON, nullable=True)  # request_id, trace_id, ip, user_agent, route, method
    
    # State changes (optional)
    diff_json = Column(JSON, nullable=True)  # For state changes
    
    # Hash chain
    prev_hash = Column(CHAR(64), nullable=True, index=True)  # NULL for first event in chain
    event_hash = Column(CHAR(64), nullable=False, index=True)  # SHA-256 hash of this event
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_audit_tenant_occurred", "tenant_id", "occurred_at"),
        Index("idx_audit_tenant_resource", "tenant_id", "resource_type", "resource_id"),
        Index("idx_audit_tenant_action", "tenant_id", "action", "occurred_at"),
        Index("idx_audit_actor", "actor_type", "actor_id", "occurred_at"),
    )
    
    def __repr__(self):
        return f"<AuditEvent(id={self.id}, action={self.action}, occurred_at={self.occurred_at})>"


class AuditChainHead(Base):
    """
    Audit Chain Head Model
    
    Tracks the last event hash for each tenant to maintain chain integrity.
    Used to quickly find the head of the chain and verify chain continuity.
    """
    __tablename__ = "audit_chain_heads"
    
    # Primary key (one record per tenant, NULL for platform-level)
    tenant_id = Column(String(26), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True, nullable=True)
    
    # Last event hash in the chain
    last_event_hash = Column(CHAR(64), nullable=False)
    
    # Last update timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    def __repr__(self):
        return f"<AuditChainHead(tenant_id={self.tenant_id}, last_event_hash={self.last_event_hash[:16]}...)>"
