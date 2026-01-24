"""
System Configuration Model

Key-value store for system-wide settings (e.g. active_model_version_id).
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String, Text

from app.database import Base


class SystemConfig(Base):
    """System-wide configuration settings."""

    __tablename__ = "system_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SystemConfig(key={self.key!r})>"
