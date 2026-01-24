"""
Evidence Models
SQLAlchemy models for evidence objects, links, and bundles
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    BigInteger, Index
)
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin
from app.shared.utils import generate_ulid


class EvidenceType(str, enum.Enum):
    """Evidence object type"""
    DOCUMENT = "DOCUMENT"
    WEATHER_SNAPSHOT = "WEATHER_SNAPSHOT"
    SENSOR_SEGMENT = "SENSOR_SEGMENT"
    PORT_EVENT = "PORT_EVENT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class RetentionClass(str, enum.Enum):
    """Evidence retention class"""
    STANDARD = "STANDARD"  # Standard retention period
    REGULATORY = "REGULATORY"  # Extended retention for regulatory compliance
    LEGAL_HOLD = "LEGAL_HOLD"  # Legal hold - cannot be deleted


class EvidenceObject(Base, BaseMixin, TenantScopedMixin):
    """
    Evidence Object model.
    
    Represents a piece of evidence (document, image, sensor data, etc.)
    with storage location, content hash, and metadata.
    """
    __tablename__ = 'evidence_objects'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Evidence type and source
    type = Column(
        SQLEnum(EvidenceType, native_enum=False),
        nullable=False,
        index=True
    )
    source = Column(String(100), nullable=False, index=True)  # UPLOAD, NOAA, CARRIER_API, etc.
    
    # Storage and content
    storage_uri = Column(String(500), nullable=False)  # URI to storage location
    content_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash of content
    mime_type = Column(String(100), nullable=True)  # MIME type (e.g., 'application/pdf')
    size_bytes = Column(BigInteger, nullable=True)  # File size in bytes
    
    # Timestamps
    captured_at = Column(DateTime, nullable=True, index=True)  # When evidence was generated/captured
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)  # When ingested into system
    
    # Retention and compliance
    retention_class = Column(
        SQLEnum(RetentionClass, native_enum=False),
        default=RetentionClass.STANDARD,
        nullable=False,
        index=True
    )
    pii_flags_json = Column(JSON, nullable=True)  # {contains_name: bool, contains_email: bool, ...}
    metadata_json = Column(JSON, nullable=True)  # Safe metadata (no PII)
    
    # Relationships
    links = relationship(
        'EvidenceLink',
        back_populates='evidence_object',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    __table_args__ = (
        Index('ix_evidence_tenant_type', 'tenant_id', 'type', 'captured_at'),
        Index('ix_evidence_tenant_hash', 'tenant_id', 'content_hash'),
        Index('ix_evidence_tenant_source', 'tenant_id', 'source'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<EvidenceObject(id={self.id}, type={self.type.value}, source={self.source})>"


class EvidenceLink(Base, BaseMixin, TenantScopedMixin):
    """
    Evidence Link model.
    
    Links evidence objects to resources (risk runs, claims, etc.)
    with relationship types.
    """
    __tablename__ = 'evidence_links'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Evidence reference
    evidence_id = Column(
        String(26),
        ForeignKey('evidence_objects.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Resource reference
    resource_type = Column(String(100), nullable=False, index=True)  # risk_run, claim, assessment, etc.
    resource_id = Column(String(100), nullable=False, index=True)  # Resource ID (ULID or other)
    
    # Relationship type
    relationship_type = Column(String(50), nullable=False, index=True)  # SUPPORTS, DERIVED_FROM, ATTACHED, etc.
    
    # Relationships
    evidence_object = relationship(
        'EvidenceObject',
        foreign_keys=[evidence_id],
        back_populates='links',
        lazy='select'
    )
    
    __table_args__ = (
        Index('ix_evidence_links_resource', 'tenant_id', 'resource_type', 'resource_id'),
        Index('ix_evidence_links_evidence', 'evidence_id', 'resource_type'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<EvidenceLink(id={self.id}, evidence_id={self.evidence_id}, resource={self.resource_type}:{self.resource_id})>"


class EvidenceBundle(Base, BaseMixin, TenantScopedMixin):
    """
    Evidence Bundle model.
    
    Represents a collection of evidence objects with a canonical manifest
    and bundle hash for integrity verification.
    """
    __tablename__ = 'evidence_bundles'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # Bundle schema and manifest
    schema_version = Column(String(50), nullable=False)  # e.g., 'evidence_bundle_v1.0'
    manifest_json = Column(JSON, nullable=False)  # List of evidence refs + hashes
    bundle_hash = Column(String(64), nullable=False, index=True)  # SHA256 of canonical manifest
    
    # Audit
    created_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Relationships
    created_by_user = relationship(
        'User',
        foreign_keys=[created_by_user_id],
        lazy='select'
    )
    
    __table_args__ = (
        Index('ix_bundles_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_bundles_tenant_hash', 'tenant_id', 'bundle_hash'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<EvidenceBundle(id={self.id}, schema_version={self.schema_version}, bundle_hash={self.bundle_hash[:16]}...)>"
