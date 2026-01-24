"""
Model Versioning Repository
Data access layer for model versioning (reuses risk_engine_v3 repository)
"""
from app.modules.risk_engine_v3.repository import RiskEngineRepository

__all__ = ["RiskEngineRepository"]
