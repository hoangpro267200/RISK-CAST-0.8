"""
SQLAlchemy Models for RISKCAST
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here to ensure they're registered
from app.models.shipment import ShipmentDB
from app.models.risk_analysis import RiskAnalysis
from app.models.scenario import Scenario
from app.models.kv_store import KVStore

__all__ = ["Base", "ShipmentDB", "RiskAnalysis", "Scenario", "KVStore"]

