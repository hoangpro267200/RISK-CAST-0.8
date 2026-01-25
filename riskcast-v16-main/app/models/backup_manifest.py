"""
Backup Manifest Model

Stores metadata about backup operations for disaster recovery.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, JSON

from app.database import Base
from app.shared.models import BaseMixin


class BackupManifestModel(Base, BaseMixin):
    """Backup manifest database model."""
    __tablename__ = "backup_manifests"
    
    # ID, created_at, updated_at are inherited from BaseMixin
    
    backup_id = Column(String(100), unique=True, nullable=False, index=True)
    backup_type = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    
    tables_included = Column(JSON, nullable=True)
    record_counts = Column(JSON, nullable=True)
    
    storage_location = Column(String(500), nullable=False)
    compressed_size_bytes = Column(Integer, nullable=True)
    uncompressed_size_bytes = Column(Integer, nullable=True)
    
    checksum = Column(String(64), nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    retention_days = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    def __repr__(self):
        return f"<BackupManifestModel(backup_id={self.backup_id}, type={self.backup_type}, status={self.status})>"
