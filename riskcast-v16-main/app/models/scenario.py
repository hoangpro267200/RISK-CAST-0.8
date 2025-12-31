"""
Scenario Model - MySQL
Stores scenario configurations
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.mysql import VARCHAR, DATETIME, TEXT, JSON as MySQLJSON
from datetime import datetime
import uuid

from app.models import Base


class Scenario(Base):
    """
    Scenario table - stores scenario configurations
    """
    __tablename__ = "scenarios"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(VARCHAR(200), unique=True, nullable=False, index=True)
    
    # Scenario configuration
    adjustments = Column(MySQLJSON, nullable=True)
    result = Column(MySQLJSON, nullable=True)
    baseline_score = Column(String(50), nullable=True)
    description = Column(TEXT, nullable=True)
    
    # Category
    category = Column(VARCHAR(50), nullable=True)
    
    # Timestamps
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "adjustments": self.adjustments,
            "result": self.result,
            "baseline_score": self.baseline_score,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


