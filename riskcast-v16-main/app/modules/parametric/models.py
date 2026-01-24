"""
Parametric Models
SQLAlchemy models for parametric insurance triggers and oracle events
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    Integer, UniqueConstraint, Index, Float, Boolean, Text, BigInteger
)
import sqlalchemy as sa
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin
from app.shared.utils import generate_ulid


class TriggerDefinitionStatus(str, enum.Enum):
    """Trigger definition status"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"


class TriggerEventStatus(str, enum.Enum):
    """Trigger event status"""
    DETECTED = "DETECTED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    CORROBORATION_FAILED = "CORROBORATION_FAILED"
    PROPOSED_PAYOUT = "PROPOSED_PAYOUT"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REJECTED = "REJECTED"


class TriggerDefinition(Base, BaseMixin, TenantScopedMixin):
    """
    Trigger Definition model.
    
    Represents a parametric trigger definition with immutability enforcement.
    """
    __tablename__ = 'trigger_definitions'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping (can be NULL for system triggers)
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin (nullable for system triggers)
    # created_at, updated_at are inherited from BaseMixin
    
    # Identification
    name = Column(String(100), nullable=True, index=True)
    description = Column(sa.Text, nullable=True)
    
    # Status
    status = Column(
        SQLEnum(TriggerDefinitionStatus, native_enum=False),
        default=TriggerDefinitionStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Trigger type and version
    type = Column(String(50), nullable=True, index=True)  # TEMP_EXCURSION, DELAY_THRESHOLD, etc. (legacy)
    trigger_type = Column(String(50), nullable=True, index=True)  # RAINFALL, WIND_SPEED, FLOOD, DELAY, TEMPERATURE, CYCLONE
    version = Column(Integer, nullable=False, default=1)
    replaces_definition_id = Column(
        String(26),
        ForeignKey('trigger_definitions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Parameters
    params_json = Column(JSON, nullable=False)  # threshold, window, corridor, corroboration rules
    scope_constraints_json = Column(JSON, nullable=True)  # Scope constraints
    corroboration_json = Column(JSON, nullable=True)  # Corroboration requirements
    payout_structure_json = Column(JSON, nullable=True)  # Payout structure
    
    # Creator
    created_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Publishing
    published_at = Column(DateTime, nullable=True, index=True)
    published_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Immutability
    immutable_hash = Column(String(64), nullable=True, index=True)  # Set on publish
    
    # Relationships
    created_by_user = relationship(
        'User',
        foreign_keys=[created_by_user_id],
        lazy='select'
    )
    published_by_user = relationship(
        'User',
        foreign_keys=[published_by_user_id],
        lazy='select'
    )
    replaces_definition = relationship(
        'TriggerDefinition',
        foreign_keys=[replaces_definition_id],
        remote_side='TriggerDefinition.id',
        lazy='select'
    )
    trigger_events = relationship(
        'TriggerEvent',
        back_populates='trigger_definition',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'type', 'version', name='uq_trigger_def_tenant_type_version'),
        UniqueConstraint('tenant_id', 'name', 'version', name='uq_trigger_def_version'),
        Index('ix_trigger_def_tenant_type', 'tenant_id', 'type', 'status'),
        Index('ix_trigger_def_tenant_trigger_type', 'tenant_id', 'trigger_type', 'status'),
    )
    
    def __repr__(self):
        return f"<TriggerDefinition(id={self.id}, name={self.name}, trigger_type={self.trigger_type}, version={self.version}, status={self.status.value})>"


class OracleEvent(Base, BaseMixin):
    """
    Oracle Event model.
    
    Represents external data events (weather, carrier, IoT) that can trigger parametric payouts.
    Tenant_id can be NULL for global events.
    """
    __tablename__ = 'oracle_events'
    
    # ID is inherited from BaseMixin (ULID String(26))
    # created_at, updated_at are inherited from BaseMixin
    
    # Tenant (nullable for global events)
    tenant_id = Column(
        String(26),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Source identification
    source = Column(String(100), nullable=False, index=True)  # NOAA, CARRIER_API, IOT_PROVIDER, TOMORROW_IO, etc.
    source_event_id = Column(String(255), nullable=True)  # External ID if any
    
    # Scope
    scope_type = Column(String(50), nullable=True)  # LOCATION, ROUTE, PORT, GLOBAL
    scope_id = Column(String(255), nullable=True)  # lat,lng or port_code or route_id
    
    # Event data (immutable)
    event_type = Column(String(100), nullable=True, index=True)  # WEATHER, FLOOD, PORT_CONGESTION, etc.
    captured_at = Column(DateTime, nullable=False, index=True)  # When event was captured
    event_time = Column(DateTime, nullable=True)  # When event occurred (if different)
    
    # Payload
    payload_json = Column(JSON, nullable=False)  # Event data
    payload_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash for deduplication
    raw_response_hash = Column(String(64), nullable=True)  # Hash of raw API response
    
    # Quality metadata
    confidence_score = Column(Float, nullable=True)  # 0-1
    data_quality_json = Column(JSON, nullable=True)
    
    # Ingestion metadata
    ingested_at = Column(DateTime, nullable=True, server_default='CURRENT_TIMESTAMP')
    ingestion_batch_id = Column(String(100), nullable=True, index=True)
    
    # Processing
    processed = Column(Boolean, nullable=True, server_default='0', index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    primary_correlations = relationship(
        'OracleEventCorrelation',
        foreign_keys='OracleEventCorrelation.primary_event_id',
        back_populates='primary_event',
        lazy='dynamic'
    )
    corroborating_correlations = relationship(
        'OracleEventCorrelation',
        foreign_keys='OracleEventCorrelation.corroborating_event_id',
        back_populates='corroborating_event',
        lazy='dynamic'
    )
    
    __table_args__ = (
        Index('ix_oracle_events_source', 'tenant_id', 'source', 'captured_at'),
        Index('ix_oracle_events_hash', 'payload_hash'),
        Index('ix_oracle_events_tenant_captured', 'tenant_id', 'captured_at'),
        Index('ix_oracle_events_scope', 'scope_type', 'scope_id'),
        Index('ix_oracle_events_source_type', 'source', 'event_type'),
    )
    
    def __repr__(self):
        return f"<OracleEvent(id={self.id}, source={self.source}, event_type={self.event_type}, captured_at={self.captured_at})>"


class TriggerEvent(Base, BaseMixin, TenantScopedMixin):
    """
    Trigger Event model.
    
    Represents a detected trigger event that matches a trigger definition for a policy.
    """
    __tablename__ = 'trigger_events'
    __tenant_scoped__ = True  # Explicit marker for tenant scoping
    
    # ID is inherited from BaseMixin (ULID String(26))
    # tenant_id is inherited from TenantScopedMixin
    # created_at, updated_at are inherited from BaseMixin
    
    # References
    trigger_definition_id = Column(
        String(26),
        ForeignKey('trigger_definitions.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    policy_id = Column(
        String(26),
        ForeignKey('policies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    # Status
    status = Column(
        SQLEnum(TriggerEventStatus, native_enum=False),
        default=TriggerEventStatus.DETECTED,
        nullable=False,
        index=True
    )
    
    # Detection
    detected_at = Column(DateTime, nullable=True, index=True)  # When trigger was detected
    matched_at = Column(DateTime, nullable=True, index=True)  # When trigger matched (legacy)
    detection_json = Column(JSON, nullable=True)  # Detection details
    
    # Validation/Corroboration
    validation_json = Column(JSON, nullable=True)  # Corroboration evidence summary
    validated_at = Column(DateTime, nullable=True)  # When validation completed
    
    # Payout calculation
    payout_calculation_json = Column(JSON, nullable=True)  # Payout calculation details
    proposed_payout_cents = Column(BigInteger, nullable=True)  # Proposed payout amount
    
    # Evaluation hash (for reproducibility)
    evaluation_hash = Column(String(64), nullable=True, index=True)
    
    # Evidence and payout
    evidence_bundle_id = Column(
        String(36),
        ForeignKey('evidence_bundles.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    payout_id = Column(
        String(36),
        ForeignKey('payouts.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Approval
    approved_at = Column(DateTime, nullable=True)
    approved_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Relationships
    trigger_definition = relationship(
        'TriggerDefinition',
        foreign_keys=[trigger_definition_id],
        back_populates='trigger_events',
        lazy='select'
    )
    policy = relationship(
        'Policy',
        foreign_keys=[policy_id],
        lazy='select'
    )
    evidence_bundle = relationship(
        'EvidenceBundle',
        foreign_keys=[evidence_bundle_id],
        lazy='select'
    )
    payout = relationship(
        'Payout',
        foreign_keys=[payout_id],
        lazy='select'
    )
    approved_by_user = relationship(
        'User',
        foreign_keys=[approved_by_user_id],
        lazy='select'
    )
    
    __table_args__ = (
        Index('ix_trigger_events_tenant_status', 'tenant_id', 'status'),
        Index('ix_trigger_events_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_trigger_events_policy_status', 'policy_id', 'status'),
    )
    
    def __repr__(self):
        return f"<TriggerEvent(id={self.id}, trigger_def_id={self.trigger_definition_id}, policy_id={self.policy_id}, status={self.status.value})>"
