"""
Underwriting Models
SQLAlchemy models for underwriting workflow
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    Text, UniqueConstraint, Index, Boolean, Integer
)
import sqlalchemy as sa
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin
from app.shared.utils import generate_ulid


class SubmissionStatus(str, enum.Enum):
    """Underwriting submission status"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    REQUESTED_INFO = "REQUESTED_INFO"
    QUOTED = "QUOTED"
    BOUND = "BOUND"
    DECLINED = "DECLINED"
    CANCELED = "CANCELED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class DecisionType(str, enum.Enum):
    """Underwriting decision type"""
    QUOTE = "QUOTE"
    DECLINE = "DECLINE"
    REQUEST_INFO = "REQUEST_INFO"


class PolicyStatus(str, enum.Enum):
    """Policy status"""
    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    CLAIMED = "CLAIMED"


class UnderwritingSubmission(Base, BaseMixin, TenantScopedMixin):
    """
    Underwriting Submission model.
    
    Represents a submission for underwriting review with state machine workflow.
    """
    __tablename__ = 'underwriting_submissions'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Status
    status = Column(
        SQLEnum(SubmissionStatus, native_enum=False),
        default=SubmissionStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Creator
    created_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Risk assessment and run references
    risk_assessment_id = Column(
        String(26),
        ForeignKey('risk_assessments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    risk_run_id = Column(
        String(26),
        ForeignKey('risk_runs.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Evidence bundle reference
    evidence_bundle_id = Column(
        String(26),
        ForeignKey('evidence_bundles.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Submission number
    submission_number = Column(String(50), nullable=True, index=True)
    
    # Coverage request
    requested_coverage_json = Column(JSON, nullable=True)  # limits, deductible, duration
    corridor_id = Column(String(100), nullable=True, index=True)
    product_type = Column(String(100), nullable=True, index=True)
    
    # Applicant info (minimal, PII-flagged)
    applicant_json = Column(JSON, nullable=True)
    applicant_pii = Column(sa.Boolean(), nullable=True, server_default='1')
    
    # Shipment reference
    shipment_id = Column(String(36), nullable=True, index=True)
    
    # Underwriter assignment
    assigned_to_user_id = Column(String(26), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    
    # Decision tracking
    decision = Column(String(20), nullable=True)  # APPROVED, DECLINED
    decision_reason = Column(Text, nullable=True)
    decision_by_user_id = Column(String(26), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    decision_at = Column(DateTime, nullable=True)
    
    # Timestamps
    submitted_at = Column(DateTime, nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    risk_assessment = relationship(
        'RiskAssessment',
        foreign_keys=[risk_assessment_id],
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
    decisions = relationship(
        'UnderwritingDecision',
        back_populates='submission',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    policies = relationship(
        'Policy',
        back_populates='submission',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    events = relationship(
        'UnderwritingSubmissionEvent',
        back_populates='submission',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='UnderwritingSubmissionEvent.created_at'
    )
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'submission_number', name='uq_submission_number'),
        Index('ix_submissions_tenant_status', 'tenant_id', 'status'),
        Index('ix_submissions_tenant_created', 'tenant_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<UnderwritingSubmission(id={self.id}, status={self.status.value}, risk_assessment_id={self.risk_assessment_id})>"


class UnderwritingDecision(Base, BaseMixin, TenantScopedMixin):
    """
    Underwriting Decision model.
    
    Represents a decision made during underwriting review.
    Includes pinned references for audit trail.
    """
    __tablename__ = 'underwriting_decisions'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Submission reference
    submission_id = Column(
        String(26),
        ForeignKey('underwriting_submissions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Decision maker
    decided_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Decision
    decision = Column(
        SQLEnum(DecisionType, native_enum=False),
        nullable=False,
        index=True
    )
    
    # Decision details
    terms_json = Column(JSON, nullable=True)  # premium, limits, exclusions
    notes = Column(Text, nullable=True)
    
    # Pinned references (immutable at decision time)
    model_version_id = Column(
        String(26),
        ForeignKey('risk_model_versions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    risk_run_id = Column(
        String(26),
        ForeignKey('risk_runs.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    evidence_bundle_id = Column(
        String(26),
        ForeignKey('evidence_bundles.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Relationships
    submission = relationship(
        'UnderwritingSubmission',
        foreign_keys=[submission_id],
        back_populates='decisions',
        lazy='select'
    )
    decided_by_user = relationship(
        'User',
        foreign_keys=[decided_by_user_id],
        lazy='select'
    )
    model_version = relationship(
        'RiskModelVersion',
        foreign_keys=[model_version_id],
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
    
    __table_args__ = (
        Index('ix_decisions_tenant_submission', 'tenant_id', 'submission_id'),
        Index('ix_decisions_tenant_created', 'tenant_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<UnderwritingDecision(id={self.id}, submission_id={self.submission_id}, decision={self.decision.value})>"


class Policy(Base, BaseMixin, TenantScopedMixin):
    """
    Policy model.
    
    Represents a bound insurance policy with pinned references for audit.
    """
    __tablename__ = 'policies'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Policy identifier
    policy_number = Column(String(100), nullable=False, index=True)
    
    # Status
    status = Column(
        SQLEnum(PolicyStatus, native_enum=False),
        default=PolicyStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Submission reference
    submission_id = Column(
        String(26),
        ForeignKey('underwriting_submissions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Binding information
    bound_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    bound_at = Column(DateTime, nullable=True, index=True)
    
    # Effective period
    effective_from = Column(DateTime, nullable=False, index=True)
    effective_to = Column(DateTime, nullable=False, index=True)
    
    # Pinned references (critical for audit)
    model_version_id = Column(
        String(26),
        ForeignKey('risk_model_versions.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    risk_run_id = Column(
        String(26),
        ForeignKey('risk_runs.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    # Quote reference
    quote_id = Column(
        String(36),
        ForeignKey('quotes.id', ondelete='RESTRICT', use_alter=True),
        nullable=True,
        index=True
    )
    
    # Evidence bundle reference
    evidence_bundle_id = Column(
        String(36),
        ForeignKey('evidence_bundles.id', ondelete='SET NULL', use_alter=True),
        nullable=True,
        index=True
    )
    
    # Policy terms (copied from quote, immutable)
    terms_json = Column(JSON, nullable=True)
    
    # Premium details
    premium_json = Column(JSON, nullable=True)
    
    # Risk snapshot at binding
    risk_snapshot_json = Column(JSON, nullable=True)
    
    # Policyholder (from submission applicant)
    policyholder_json = Column(JSON, nullable=True)
    policyholder_pii = Column(Boolean(), nullable=True, server_default='1')
    
    # Shipment reference
    shipment_id = Column(String(36), nullable=True, index=True)
    corridor_id = Column(String(100), nullable=True, index=True)
    
    # Policy document
    policy_document_evidence_id = Column(
        String(36),
        ForeignKey('evidence_objects.id', ondelete='SET NULL', use_alter=True),
        nullable=True
    )
    policy_document_hash = Column(String(64), nullable=True)
    
    # Policy hash (for integrity)
    policy_hash = Column(String(64), nullable=False, server_default='', index=True)
    
    # Cancellation (if applicable)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    cancellation_reason = Column(Text, nullable=True)
    refund_amount_cents = Column(Integer, nullable=True)
    
    # Relationships
    submission = relationship(
        'UnderwritingSubmission',
        foreign_keys=[submission_id],
        back_populates='policies',
        lazy='select'
    )
    quote = relationship(
        'Quote',
        foreign_keys=[quote_id],
        lazy='select'
    )
    evidence_bundle = relationship(
        'EvidenceBundle',
        foreign_keys=[evidence_bundle_id],
        lazy='select'
    )
    policy_document_evidence = relationship(
        'EvidenceObject',
        foreign_keys=[policy_document_evidence_id],
        lazy='select'
    )
    bound_by_user = relationship(
        'User',
        foreign_keys=[bound_by_user_id],
        lazy='select'
    )
    model_version = relationship(
        'RiskModelVersion',
        foreign_keys=[model_version_id],
        lazy='select'
    )
    risk_run = relationship(
        'RiskRun',
        foreign_keys=[risk_run_id],
        lazy='select'
    )
    
    events = relationship(
        'PolicyEvent',
        back_populates='policy',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='PolicyEvent.created_at'
    )
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'policy_number', name='uq_policies_tenant_policy_number'),
        Index('ix_policies_tenant_status', 'tenant_id', 'status'),
        Index('ix_policies_tenant_policy_number', 'tenant_id', 'policy_number'),
        Index('ix_policies_effective_period', 'effective_from', 'effective_to'),
    )
    
    def __repr__(self):
        return f"<Policy(id={self.id}, policy_number={self.policy_number}, status={self.status.value})>"


class PolicyEvent(Base, BaseMixin):
    """
    Policy Event model.
    
    Tracks all events for a policy (binding, payment, cancellation, etc.).
    """
    __tablename__ = 'policy_events'
    
    # ID is inherited from BaseMixin (ULID String(26))
    # created_at is inherited from BaseMixin
    
    # Policy reference
    policy_id = Column(
        String(26),
        ForeignKey('policies.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Event type
    event_type = Column(String(50), nullable=False, index=True)
    # BOUND, DOCUMENT_GENERATED, PREMIUM_PAID, CANCELLED, EXPIRED, CLAIM_FILED
    
    # Actor info
    actor_type = Column(String(20), nullable=False)  # USER, SYSTEM
    actor_id = Column(String(26), nullable=True)  # ULID
    
    # Event payload
    payload_json = Column(JSON, nullable=True)
    
    # Relationships
    policy = relationship(
        'Policy',
        foreign_keys=[policy_id],
        back_populates='events',
        lazy='select'
    )
    
    __table_args__ = (
        Index('idx_policy_events_policy', 'policy_id'),
        Index('idx_policy_events_type', 'event_type'),
        Index('idx_policy_events_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<PolicyEvent(id={self.id}, policy_id={self.policy_id}, event_type={self.event_type})>"


class UnderwritingSubmissionEvent(Base, BaseMixin):
    """
    Underwriting Submission Event model.
    
    Tracks all events and state transitions for a submission.
    """
    __tablename__ = 'underwriting_submission_events'
    
    # ID is inherited from BaseMixin (ULID String(26))
    # created_at is inherited from BaseMixin
    
    # Submission reference
    submission_id = Column(
        String(26),
        ForeignKey('underwriting_submissions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Event type
    event_type = Column(String(50), nullable=False, index=True)
    # STATE_TRANSITION, NOTE_ADDED, EVIDENCE_ADDED, ASSIGNMENT_CHANGED, INFO_REQUESTED
    
    # State transition info
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=True)
    
    # Actor info
    actor_type = Column(String(20), nullable=False)  # USER, SYSTEM
    actor_id = Column(String(26), nullable=True)  # ULID
    
    # Event payload
    payload_json = Column(JSON, nullable=True)
    
    # Relationships
    submission = relationship(
        'UnderwritingSubmission',
        foreign_keys=[submission_id],
        back_populates='events',
        lazy='select'
    )
    
    __table_args__ = (
        Index('idx_submission_events_submission', 'submission_id'),
        Index('idx_submission_events_created', 'created_at'),
        Index('idx_submission_events_type', 'event_type'),
    )
    
    def __repr__(self):
        return f"<UnderwritingSubmissionEvent(id={self.id}, submission_id={self.submission_id}, event_type={self.event_type})>"
