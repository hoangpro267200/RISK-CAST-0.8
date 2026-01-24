"""
Evidence Object Model
SQLAlchemy model for evidence objects with content hashing and storage references.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column, String, BigInteger, Boolean, DateTime, Text, JSON
)
from sqlalchemy.orm import relationship
import sqlalchemy as sa

from app.database import Base


class EvidenceObject(Base):
    """
    Evidence Object Model
    
    Represents an evidence object (document, image, data export, etc.) with
    content hashing for deduplication and storage references.
    
    Fields:
    - id: UUID primary key
    - tenant_id: Tenant ID (UUID String(36))
    - content_hash: SHA256 hash of content (String(64))
    - content_type: MIME type (String(100))
    - content_size_bytes: Size in bytes (BigInteger, nullable)
    - storage_uri: Storage URI (Text) - s3://bucket/path or file://path
    - storage_provider: Storage provider (String(50)) - 'local', 's3', etc.
    - filename: Original filename (String(255), nullable)
    - description: Description (Text, nullable)
    - metadata_json: Additional metadata (JSON, nullable)
    - evidence_type: Type of evidence (String(50), nullable) - DOCUMENT, IMAGE, DATA_EXPORT, etc.
    - is_pii: Whether content contains PII (Boolean, default False)
    - retention_class: Retention classification (String(50), default 'STANDARD')
    - created_by_user_id: User who created this (UUID String(36), nullable)
    - created_at: Creation timestamp
    - expires_at: Expiration timestamp (nullable)
    - deleted_at: Soft delete timestamp (nullable)
    """
    __tablename__ = 'evidence_objects'
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    
    # Content identification
    content_hash = Column(String(64), nullable=False, index=True)
    content_type = Column(String(100), nullable=False)
    content_size_bytes = Column(BigInteger(), nullable=True)
    
    # Storage
    storage_uri = Column(Text(), nullable=False)
    storage_provider = Column(String(50), nullable=False, server_default='local')
    
    # Metadata
    filename = Column(String(255), nullable=True)
    description = Column(Text(), nullable=True)
    metadata_json = Column(JSON(), nullable=True, default=dict)
    
    # Classification
    evidence_type = Column(String(50), nullable=True, index=True)  # DOCUMENT, IMAGE, DATA_EXPORT, etc.
    is_pii = Column(Boolean(), nullable=False, server_default='0')
    retention_class = Column(String(50), nullable=False, server_default='STANDARD')
    
    # Lifecycle
    created_by_user_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    expires_at = Column(DateTime(), nullable=True)
    deleted_at = Column(DateTime(), nullable=True, index=True)  # Soft delete
    
    # Relationships
    links = relationship('EvidenceLink', back_populates='evidence', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f"<EvidenceObject(id={self.id}, tenant_id={self.tenant_id}, content_hash={self.content_hash[:8]}..., evidence_type={self.evidence_type})>"
    
    def is_deleted(self) -> bool:
        """Check if this evidence object is soft-deleted"""
        return self.deleted_at is not None
    
    def is_expired(self) -> bool:
        """Check if this evidence object has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'content_hash': self.content_hash,
            'content_type': self.content_type,
            'content_size_bytes': self.content_size_bytes,
            'storage_uri': self.storage_uri,
            'storage_provider': self.storage_provider,
            'filename': self.filename,
            'description': self.description,
            'metadata_json': self.metadata_json or {},
            'evidence_type': self.evidence_type,
            'is_pii': self.is_pii,
            'retention_class': self.retention_class,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
        }
