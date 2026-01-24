"""
Risk Engine V3 Repository
Data access layer for risk engine configuration
"""
from sqlalchemy.orm import Session
from typing import Optional, List

from app.modules.risk_engine_v3.models import RiskModelVersion
from app.shared.exceptions import NotFoundError


class RiskEngineRepository:
    """Repository for risk engine data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_version(self, version_data: dict) -> RiskModelVersion:
        """Create a new model version"""
        version = RiskModelVersion(**version_data)
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version
    
    def get_version(self, version: str) -> Optional[RiskModelVersion]:
        """Get model version by version string"""
        return self.db.query(RiskModelVersion).filter(
            RiskModelVersion.version == version,
            RiskModelVersion.is_deprecated == False
        ).first()
    
    def get_current_production_version(self) -> Optional[RiskModelVersion]:
        """Get current production model version"""
        return self.db.query(RiskModelVersion).filter(
            RiskModelVersion.is_production == True,
            RiskModelVersion.is_deprecated == False
        ).order_by(RiskModelVersion.created_at.desc()).first()
    
    def list_versions(self) -> List[RiskModelVersion]:
        """List all model versions"""
        return self.db.query(RiskModelVersion).filter(
            RiskModelVersion.is_deprecated == False
        ).order_by(RiskModelVersion.created_at.desc()).all()
