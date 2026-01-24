"""
Risk Runs Repository
Data access layer for risk calculation runs
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import hashlib
import json

from app.modules.risk_runs.models import RiskRun, RunStatus
from app.shared.exceptions import NotFoundError


class RiskRunRepository:
    """Repository for risk run data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, run_data: dict) -> RiskRun:
        """Create a new risk run"""
        # Generate input hash
        input_str = json.dumps(run_data["input_data"], sort_keys=True)
        input_hash = hashlib.sha256(input_str.encode()).hexdigest()
        run_data["input_hash"] = input_hash
        
        run = RiskRun(**run_data)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
    
    def get_by_id(self, run_id: str, tenant_id: Optional[str] = None) -> Optional[RiskRun]:
        """Get run by ID"""
        query = self.db.query(RiskRun).filter(RiskRun.id == run_id)
        if tenant_id:
            query = query.filter(RiskRun.tenant_id == tenant_id)
        return query.first()
    
    def get_by_run_id(self, run_id: str, tenant_id: Optional[str] = None) -> Optional[RiskRun]:
        """Get run by run_id"""
        query = self.db.query(RiskRun).filter(RiskRun.run_id == run_id)
        if tenant_id:
            query = query.filter(RiskRun.tenant_id == tenant_id)
        return query.first()
    
    def update_status(self, run_id: str, status: RunStatus, 
                     output_data: Optional[dict] = None,
                     error_message: Optional[str] = None,
                     duration_ms: Optional[float] = None) -> RiskRun:
        """Update run status"""
        run = self.get_by_id(run_id)
        if not run:
            raise NotFoundError("RiskRun", run_id)
        
        run.status = status
        if output_data:
            run.output_data = output_data
        if error_message:
            run.error_message = error_message
        if duration_ms:
            run.duration_ms = duration_ms
        
        if status == RunStatus.RUNNING:
            run.started_at = datetime.utcnow()
        elif status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
            run.completed_at = datetime.utcnow()
        
        run.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return run
