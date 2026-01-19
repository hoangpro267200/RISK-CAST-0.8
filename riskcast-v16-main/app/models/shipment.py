"""
Shipment Model - MySQL
"""
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.mysql import VARCHAR, DATETIME, TEXT, JSON as MySQLJSON
from datetime import datetime
import uuid

from app.models import Base


class ShipmentDB(Base):
    """
    Shipment table - stores shipment data and analysis results
    """
    __tablename__ = "shipments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Route information
    pol = Column(VARCHAR(50), nullable=True)
    pod = Column(VARCHAR(50), nullable=True)
    route = Column(VARCHAR(200), nullable=True)
    carrier = Column(VARCHAR(100), nullable=True)
    
    # Dates
    etd = Column(DATETIME, nullable=True)
    eta = Column(DATETIME, nullable=True)
    transit_time = Column(String(50), nullable=True)
    
    # Cargo information
    cargo_type = Column(VARCHAR(100), nullable=True)
    cargo_value = Column(String(50), nullable=True)
    container = Column(VARCHAR(50), nullable=True)
    packaging = Column(VARCHAR(50), nullable=True)
    incoterm = Column(VARCHAR(20), nullable=True)
    
    # Shipment data (JSON) - stores full shipment payload
    shipment_data = Column(MySQLJSON, nullable=True)
    
    # Timestamps
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "pol": self.pol,
            "pod": self.pod,
            "route": self.route,
            "carrier": self.carrier,
            "etd": self.etd.isoformat() if self.etd else None,
            "eta": self.eta.isoformat() if self.eta else None,
            "transit_time": self.transit_time,
            "cargo_type": self.cargo_type,
            "cargo_value": self.cargo_value,
            "container": self.container,
            "packaging": self.packaging,
            "incoterm": self.incoterm,
            "shipment_data": self.shipment_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
