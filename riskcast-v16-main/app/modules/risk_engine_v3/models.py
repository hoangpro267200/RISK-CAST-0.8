"""
Risk Engine V3 Models
SQLAlchemy models for risk engine configuration
"""
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean
from datetime import datetime
import uuid

from app.database import Base


class RiskModelVersion(Base):
    """Risk model version configuration"""
    __tablename__ = "risk_model_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "v3.1.0"
    
    # Configuration
    layer_weights = Column(JSON, nullable=False)  # Risk layer weights
    calibration_data = Column(JSON, nullable=True)  # Calibration parameters
    calibration_date = Column(DateTime, nullable=True)
    
    # Performance metrics
    performance_metrics = Column(JSON, nullable=True)  # Accuracy, loss ratio, etc.
    
    # Status
    is_production = Column(Boolean, default=False, nullable=False, index=True)
    is_deprecated = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    changelog = Column(JSON, default=list)
    regulatory_approvals = Column(JSON, default=list)
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deprecated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<RiskModelVersion(id={self.id}, version={self.version}, is_production={self.is_production})>"
