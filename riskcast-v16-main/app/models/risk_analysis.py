"""
Risk Analysis Model - MySQL
Stores engine v2 analysis results
"""
from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey, Index
from sqlalchemy.dialects.mysql import VARCHAR, DATETIME, TEXT, JSON as MySQLJSON, DOUBLE
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models import Base


class RiskAnalysis(Base):
    """
    Risk Analysis table - stores engine v2 analysis results
    This is the authoritative source for Results page
    """
    __tablename__ = "risk_analyses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(String(100), nullable=False, index=True)
    
    # Link to shipment (optional foreign key)
    # shipment_fk = Column(String(36), ForeignKey("shipments.id"), nullable=True)
    
    # Risk scores
    risk_score = Column(DOUBLE, nullable=True)
    overall_risk = Column(DOUBLE, nullable=True)
    risk_level = Column(VARCHAR(20), nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(DOUBLE, nullable=True)
    
    # Complete engine result (JSON) - stores full engine v2 output
    engine_result = Column(MySQLJSON, nullable=True)
    
    # Decision summary
    decision_summary = Column(MySQLJSON, nullable=True)
    
    # Recommendations
    recommendations = Column(MySQLJSON, nullable=True)
    
    # Layers, drivers, scenarios (stored as JSON)
    layers = Column(MySQLJSON, nullable=True)
    drivers = Column(MySQLJSON, nullable=True)
    scenarios = Column(MySQLJSON, nullable=True)
    
    # Financial metrics
    financial = Column(MySQLJSON, nullable=True)
    
    # AI narrative
    ai_narrative = Column(MySQLJSON, nullable=True)
    
    # Engine metadata
    engine_version = Column(VARCHAR(20), nullable=True, default="v2")
    language = Column(VARCHAR(10), nullable=True, default="en")
    
    # Timestamps
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Index for faster queries
    __table_args__ = (
        Index('idx_shipment_created', 'shipment_id', 'created_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "risk_score": self.risk_score,
            "overall_risk": self.overall_risk,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "engine_result": self.engine_result,
            "decision_summary": self.decision_summary,
            "recommendations": self.recommendations,
            "layers": self.layers,
            "drivers": self.drivers,
            "scenarios": self.scenarios,
            "financial": self.financial,
            "ai_narrative": self.ai_narrative,
            "engine_version": self.engine_version,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


