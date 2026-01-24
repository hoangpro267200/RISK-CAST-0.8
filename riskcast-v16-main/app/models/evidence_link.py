"""
Evidence Link Model
SQLAlchemy model for linking evidence objects to entities with polymorphic relationships.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
import sqlalchemy as sa

from app.database import Base


class EvidenceLink(Base):
    """
    Evidence Link Model
    
    Represents a link between an evidence object and an entity (risk_assessment,
    risk_run, policy, claim, trigger_event) with polymorphic relationships.
    
    Fields:
    - id: UUID primary key
    - tenant_id: Tenant ID (UUID String(36))
    - evidence_id: FK to evidence_objects (UUID String(36))
    - entity_type: Type of entity (String(100)) - risk_assessment, risk_run, policy, claim, trigger_event
    - entity_id: ID of the entity (UUID String(36))
    - link_type: Type of link (String(50), default 'ATTACHMENT') - ATTACHMENT, SOURCE_DATA, DECISION_BASIS, OUTPUT
    - description: Description of the link (Text, nullable)
    - created_at: Creation timestamp
    """
    __tablename__ = 'evidence_links'
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    
    # Evidence reference
    evidence_id = Column(
        String(36),
        ForeignKey('evidence_objects.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Polymorphic link
    entity_type = Column(String(100), nullable=False, index=True)  # risk_assessment, risk_run, policy, claim, trigger_event
    entity_id = Column(String(36), nullable=False, index=True)  # UUID
    
    # Link metadata
    link_type = Column(String(50), nullable=False, server_default='ATTACHMENT', index=True)  # ATTACHMENT, SOURCE_DATA, DECISION_BASIS, OUTPUT
    description = Column(Text(), nullable=True)
    
    # Timing
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    evidence = relationship('EvidenceObject', back_populates='links')
    
    # Unique constraint: prevent duplicate links
    __table_args__ = (
        UniqueConstraint('evidence_id', 'entity_type', 'entity_id', name='uq_evidence_links_unique'),
        Index('ix_evidence_links_entity', 'entity_type', 'entity_id'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<EvidenceLink(id={self.id}, evidence_id={self.evidence_id}, "
            f"entity_type={self.entity_type}, entity_id={self.entity_id}, link_type={self.link_type})>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'evidence_id': self.evidence_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'link_type': self.link_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
