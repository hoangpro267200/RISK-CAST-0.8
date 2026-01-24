"""
SQLAlchemy models for evidence bundles.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import sqlalchemy as sa
import uuid

from app.database import Base


class EvidenceBundle(Base):
    """
    Evidence Bundle Model
    
    Groups multiple evidence objects together for:
    - Underwriting decisions (all documents supporting a quote)
    - Claims (all claim evidence)
    - Trigger events (all oracle data supporting a trigger)
    
    Bundle has manifest hash to verify integrity of entire bundle.
    """
    __tablename__ = 'evidence_bundles'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    
    # Identification
    name = Column(String(255), nullable=True)
    description = Column(Text(), nullable=True)
    bundle_type = Column(String(50), nullable=False, index=True)
    # UNDERWRITING, CLAIM, TRIGGER, ASSESSMENT, POLICY, EXPORT
    
    # Status
    status = Column(String(20), nullable=False, server_default='OPEN', index=True)
    # OPEN (can add items), SEALED (immutable), ARCHIVED
    
    # Manifest
    manifest_json = Column(sa.JSON(), nullable=True, server_default='{}')
    # {
    #   "items": [
    #     {"evidence_id": "...", "content_hash": "...", "added_at": "..."},
    #     ...
    #   ],
    #   "item_count": 5,
    #   "total_size_bytes": 12345
    # }
    manifest_hash = Column(String(64), nullable=True, index=True)  # SHA256 of manifest
    
    # Compliance
    retention_class = Column(String(50), nullable=False, server_default='STANDARD')
    # STANDARD (7 years), REGULATORY (10 years), LEGAL_HOLD (indefinite)
    legal_hold = Column(Boolean(), nullable=False, server_default='0')
    legal_hold_reason = Column(Text(), nullable=True)
    expires_at = Column(DateTime(), nullable=True)
    
    # PII tracking
    contains_pii = Column(Boolean(), nullable=False, server_default='0')
    pii_categories = Column(sa.JSON(), nullable=True, server_default='[]')
    # ["name", "address", "financial"]
    
    # Audit
    created_by_user_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    sealed_at = Column(DateTime(), nullable=True)
    sealed_by_user_id = Column(String(36), nullable=True)
    
    # Relationships
    items = relationship('EvidenceBundleItem', back_populates='bundle', cascade='all, delete-orphan')
    links = relationship('EvidenceBundleLink', back_populates='bundle', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_evidence_bundles_tenant', 'tenant_id'),
        Index('idx_evidence_bundles_type', 'bundle_type'),
        Index('idx_evidence_bundles_status', 'status'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<EvidenceBundle(id={self.id}, tenant_id={self.tenant_id}, bundle_type={self.bundle_type}, status={self.status})>"
    
    def is_sealed(self) -> bool:
        """Check if bundle is sealed (immutable)"""
        return self.status == 'SEALED'
    
    def is_archived(self) -> bool:
        """Check if bundle is archived"""
        return self.status == 'ARCHIVED'
    
    def can_add_items(self) -> bool:
        """Check if items can be added to bundle"""
        return self.status == 'OPEN'


class EvidenceBundleItem(Base):
    """
    Evidence Bundle Item Model
    
    Links evidence objects to bundles with metadata about the item's role
    within the bundle.
    """
    __tablename__ = 'evidence_bundle_items'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bundle_id = Column(String(36), ForeignKey('evidence_bundles.id', ondelete='CASCADE'), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey('evidence_objects.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Item metadata within bundle
    sequence = Column(Integer(), nullable=True)  # Order within bundle
    role = Column(String(50), nullable=True)  # PRIMARY, SUPPORTING, REFERENCE
    description = Column(Text(), nullable=True)
    
    # Hash at time of addition (for integrity)
    content_hash_at_addition = Column(String(64), nullable=False)
    
    added_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    added_by_user_id = Column(String(36), nullable=True)
    
    # Relationships
    bundle = relationship('EvidenceBundle', back_populates='items')
    evidence = relationship('EvidenceObject')
    
    __table_args__ = (
        UniqueConstraint('bundle_id', 'evidence_id', name='uq_bundle_evidence'),
        Index('idx_bundle_items_bundle', 'bundle_id'),
        Index('idx_bundle_items_evidence', 'evidence_id'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<EvidenceBundleItem(id={self.id}, bundle_id={self.bundle_id}, evidence_id={self.evidence_id}, role={self.role})>"


class EvidenceBundleLink(Base):
    """
    Evidence Bundle Link Model
    
    Polymorphic links from bundles to domain entities (policy, claim, trigger_event, etc.)
    """
    __tablename__ = 'evidence_bundle_links'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bundle_id = Column(String(36), ForeignKey('evidence_bundles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Polymorphic link
    entity_type = Column(String(100), nullable=False, index=True)
    # policy, claim, trigger_event, risk_run, underwriting_submission, quote
    entity_id = Column(String(36), nullable=False, index=True)  # UUID
    
    # Link type
    link_type = Column(String(50), nullable=False, server_default='PRIMARY')
    # PRIMARY, SUPPLEMENTARY, REFERENCE
    
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    bundle = relationship('EvidenceBundle', back_populates='links')
    
    __table_args__ = (
        UniqueConstraint('bundle_id', 'entity_type', 'entity_id', name='uq_bundle_entity'),
        Index('idx_bundle_links_bundle', 'bundle_id'),
        Index('idx_bundle_links_entity', 'entity_type', 'entity_id'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<EvidenceBundleLink(id={self.id}, bundle_id={self.bundle_id}, entity_type={self.entity_type}, entity_id={self.entity_id})>"
