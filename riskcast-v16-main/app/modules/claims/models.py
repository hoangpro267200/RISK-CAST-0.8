"""
Claims Models
SQLAlchemy models for claims management with state machine
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    BigInteger, Index, Text, UniqueConstraint
)
import sqlalchemy as sa
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin
from app.shared.utils import generate_ulid


class ClaimStatus(str, enum.Enum):
    """Claim status"""
    FNOL_RECEIVED = "FNOL_RECEIVED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    AWAITING_EVIDENCE = "AWAITING_EVIDENCE"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    AUTHORIZED = "AUTHORIZED"
    PAID = "PAID"
    CLOSED = "CLOSED"
    WITHDRAWN = "WITHDRAWN"


class PayoutStatus(str, enum.Enum):
    """Payout status"""
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    AUTHORIZED = "AUTHORIZED"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Claim(Base, BaseMixin, TenantScopedMixin):
    """
    Claim model.
    
    Represents an insurance claim with state machine workflow.
    """
    __tablename__ = 'claims'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Claim identification
    claim_number = Column(String(50), nullable=True, index=True)
    
    # Policy reference
    policy_id = Column(
        String(26),
        ForeignKey('policies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    # Status
    status = Column(
        SQLEnum(ClaimStatus, native_enum=False),
        default=ClaimStatus.FNOL_RECEIVED,
        nullable=False,
        index=True
    )
    
    # FNOL (First Notice of Loss) - immutable snapshot
    fnol_json = Column(JSON, nullable=False)  # incident summary, time, location, alleged loss
    
    # References
    risk_run_id = Column(
        String(26),
        ForeignKey('risk_runs.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )  # Reference to underwriting run
    evidence_bundle_id = Column(
        String(36),
        ForeignKey('evidence_bundles.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )  # Latest bundle
    
    # Investigation
    assigned_adjuster_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    assigned_at = Column(DateTime, nullable=True)
    investigation_notes = Column(sa.Text, nullable=True)
    
    # Decision
    decision = Column(String(20), nullable=True)  # APPROVED, DECLINED
    decision_reason = Column(sa.Text, nullable=True)
    decision_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    decision_at = Column(DateTime, nullable=True)
    
    # Approved amount (may differ from claimed)
    approved_amount_cents = Column(BigInteger, nullable=True)
    approved_currency = Column(String(3), nullable=True)
    
    # Adjudication details
    adjudication_json = Column(JSON, nullable=True)
    
    # Payout tracking
    payout_id = Column(String(36), nullable=True, index=True)  # Link to payout record
    
    # Creator
    created_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Timestamps
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    policy = relationship(
        'Policy',
        foreign_keys=[policy_id],
        lazy='select'
    )
    risk_run = relationship(
        'RiskRun',
        foreign_keys=[risk_run_id],
        lazy='select'
    )
    evidence_bundle = relationship(
        'EvidenceBundle',
        foreign_keys=[evidence_bundle_id],
        lazy='select'
    )
    created_by_user = relationship(
        'User',
        foreign_keys=[created_by_user_id],
        lazy='select'
    )
    events = relationship(
        'ClaimEvent',
        back_populates='claim',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='ClaimEvent.created_at'
    )
    payouts = relationship(
        'Payout',
        back_populates='claim',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    __table_args__ = (
        Index('ix_claims_tenant_status', 'tenant_id', 'status'),
        Index('ix_claims_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_claims_policy_status', 'policy_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Claim(id={self.id}, policy_id={self.policy_id}, status={self.status.value})>"


class ClaimEvent(Base, BaseMixin, TenantScopedMixin):
    """
    Claim Event model.
    
    Represents events in the claim lifecycle (state transitions, notes, evidence additions).
    """
    __tablename__ = 'claim_events'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Claim reference
    claim_id = Column(
        String(26),
        ForeignKey('claims.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Event type
    event_type = Column(String(50), nullable=False, index=True)  # STATE_TRANSITION, NOTE_ADDED, EVIDENCE_ADDED
    
    # State transition (if applicable)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=True)
    
    # Actor information
    actor_type = Column(String(20), nullable=False, index=True)  # USER, SYSTEM
    actor_id = Column(String(26), nullable=True, index=True)  # ULID
    
    # Event payload
    payload_json = Column(JSON, nullable=True)  # minimal; reference evidence IDs
    
    # Relationships
    claim = relationship(
        'Claim',
        foreign_keys=[claim_id],
        back_populates='events',
        lazy='select'
    )
    
    __table_args__ = (
        Index('ix_claim_events_tenant_claim', 'tenant_id', 'claim_id'),
        Index('ix_claim_events_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_claim_events_claim_type', 'claim_id', 'event_type'),
    )
    
    def __repr__(self):
        return f"<ClaimEvent(id={self.id}, claim_id={self.claim_id}, event_type={self.event_type})>"


class Payout(Base, BaseMixin, TenantScopedMixin):
    """
    Payout model.
    
    Represents a payout/payment for a claim or parametric trigger.
    """
    __tablename__ = 'payouts'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Payout identification
    payout_number = Column(String(50), nullable=True, index=True)
    
    # Source (claim or parametric trigger)
    payout_type = Column(String(20), nullable=False, server_default='CLAIM')  # CLAIM, PARAMETRIC
    
    # Claim reference (optional for parametric payouts)
    claim_id = Column(
        String(26),
        ForeignKey('claims.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Policy reference (required)
    policy_id = Column(
        String(26),
        ForeignKey('policies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    # Trigger event (for parametric payouts)
    trigger_event_id = Column(String(26), nullable=True, index=True)  # For parametric
    
    # Status
    status = Column(
        SQLEnum(PayoutStatus, native_enum=False),
        default=PayoutStatus.PROPOSED,
        nullable=False,
        index=True
    )
    
    # Amount
    amount_cents = Column(BigInteger, nullable=False)  # Amount in cents to avoid float precision issues
    currency = Column(String(3), nullable=False, default='USD', index=True)
    
    # Calculation
    calculation_snapshot_json = Column(JSON, nullable=True)
    calculation_hash = Column(String(64), nullable=True)
    
    # Recipient
    recipient_json = Column(JSON, nullable=True)
    
    # Approval workflow
    proposed_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    proposed_at = Column(DateTime, nullable=True)
    approved_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    approved_at = Column(DateTime, nullable=True)
    authorized_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    authorized_at = Column(DateTime, nullable=True)
    
    # Payment
    payment_reference = Column(String(255), nullable=True)
    payment_method = Column(String(50), nullable=True)
    paid_at = Column(DateTime, nullable=True, index=True)
    payment_confirmation_json = Column(JSON, nullable=True)
    
    # Failure tracking
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(sa.Integer, nullable=True, server_default='0')
    
    # Relationships
    claim = relationship(
        'Claim',
        foreign_keys=[claim_id],
        back_populates='payouts',
        lazy='select'
    )
    policy = relationship(
        'Policy',
        foreign_keys=[policy_id],
        lazy='select'
    )
    approved_by_user = relationship(
        'User',
        foreign_keys=[approved_by_user_id],
        lazy='select'
    )
    
    __table_args__ = (
        sa.UniqueConstraint('tenant_id', 'payout_number', name='uq_payout_number'),
        Index('ix_payouts_tenant_status', 'tenant_id', 'status'),
        Index('ix_payouts_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_payouts_claim_status', 'claim_id', 'status'),
        Index('ix_payouts_policy_status', 'policy_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Payout(id={self.id}, claim_id={self.claim_id}, status={self.status.value}, amount={self.amount_cents} {self.currency})>"
