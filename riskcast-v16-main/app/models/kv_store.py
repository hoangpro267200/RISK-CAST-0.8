"""
Key-Value Store Model - MySQL
Replaces JSON file-based kv_store
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.mysql import VARCHAR, DATETIME, TEXT, JSON as MySQLJSON
from datetime import datetime

from app.models import Base


class KVStore(Base):
    """
    Key-Value Store table - replaces data/kv_store.json
    """
    __tablename__ = "kv_store"
    
    key = Column(VARCHAR(200), primary_key=True, index=True)
    value = Column(MySQLJSON, nullable=True)
    
    # Timestamps
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


