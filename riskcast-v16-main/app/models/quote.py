"""
Quote Model
SQLAlchemy model for versioned quotes with immutability
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Integer, Boolean, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
import sqlalchemy as sa
import uuid

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin


class Quote(Base, TenantScopedMixin):
    """
    Quote model.
    
    Represents a versioned, immutable quote snapshot.
    Quotes are immutable after issuance - changes create new versions.
    """
    __tablename__ = 'quotes'
    __tenant_scoped__ = True
    
    # ID is UUID (String(36))
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # tenant_id is inherited from TenantScopedMixin
    
    # Reference
    quote_number = Column(String(50), nullable=False, index=True)
    submission_id = Column(
        String(26),
        ForeignKey('underwriting_submissions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Versioning
    version = Column(Integer, nullable=False, server_default='1')
    is_latest = Column(Boolean, nullable=False, server_default='0')  # MySQL boolean
    replaces_quote_id = Column(
        String(36),
        ForeignKey('quotes.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Status
    status = Column(String(20), nullable=False, server_default='DRAFT', index=True)
    # DRAFT, ISSUED, ACCEPTED, DECLINED, EXPIRED, REPLACED
    
    # Pinned references (immutable after ISSUED)
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
    evidence_bundle_id = Column(
        String(36),
        ForeignKey('evidence_bundles.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Pricing snapshot (immutable)
    pricing_snapshot_json = Column(JSON, nullable=False)
    
    # Coverage terms (immutable)
    coverage_terms_json = Column(JSON, nullable=False)
    
    # Risk summary (immutable)
    risk_summary_json = Column(JSON, nullable=True)
    
    # Quote hash (for integrity verification)
    quote_hash = Column(String(64), nullable=False, server_default='', index=True)
    
    # Validity
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False, index=True)
    
    # Timestamps
    issued_at = Column(DateTime, nullable=True)
    issued_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    submission = relationship(
        'UnderwritingSubmission',
        foreign_keys=[submission_id],
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
    issued_by_user = relationship(
        'User',
        foreign_keys=[issued_by_user_id],
        lazy='select'
    )
    replaced_quote = relationship(
        'Quote',
        foreign_keys=[replaces_quote_id],
        remote_side=[id],
        lazy='select'
    )
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'quote_number', 'version', name='uq_quote_version'),
        Index('idx_quotes_tenant', 'tenant_id'),
        Index('idx_quotes_submission', 'submission_id'),
        Index('idx_quotes_status', 'status'),
        Index('idx_quotes_latest', 'submission_id', 'is_latest'),
        Index('idx_quotes_hash', 'quote_hash'),
        Index('idx_quotes_valid_until', 'valid_until'),
    )
    
    def __repr__(self):
        return f"<Quote(id={self.id}, quote_number={self.quote_number}, version={self.version}, status={self.status})>"
