"""
Parametric Repository
Data access layer for parametric triggers
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.modules.parametric.models import ParametricTrigger, TriggerStatus
from app.shared.exceptions import NotFoundError


class ParametricRepository:
    """Repository for parametric trigger data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, trigger_data: dict) -> ParametricTrigger:
        """Create a new parametric trigger"""
        trigger = ParametricTrigger(**trigger_data)
        self.db.add(trigger)
        self.db.commit()
        self.db.refresh(trigger)
        return trigger
    
    def get_by_id(self, trigger_id: str, tenant_id: Optional[str] = None) -> Optional[ParametricTrigger]:
        """Get trigger by ID"""
        query = self.db.query(ParametricTrigger).filter(ParametricTrigger.id == trigger_id)
        if tenant_id:
            query = query.filter(ParametricTrigger.tenant_id == tenant_id)
        return query.first()
    
    def list_active(self, tenant_id: Optional[str] = None) -> List[ParametricTrigger]:
        """List active triggers"""
        query = self.db.query(ParametricTrigger).filter(
            ParametricTrigger.status == TriggerStatus.ACTIVE,
            ParametricTrigger.monitoring_enabled == True,
            (ParametricTrigger.expires_at.is_(None) | (ParametricTrigger.expires_at > datetime.utcnow()))
        )
        if tenant_id:
            query = query.filter(ParametricTrigger.tenant_id == tenant_id)
        return query.all()
    
    def mark_triggered(self, trigger_id: str, trigger_value: float, payout_amount: float) -> ParametricTrigger:
        """Mark trigger as triggered"""
        trigger = self.get_by_id(trigger_id)
        if not trigger:
            raise NotFoundError("ParametricTrigger", trigger_id)
        
        trigger.status = TriggerStatus.TRIGGERED
        trigger.triggered_at = datetime.utcnow()
        trigger.trigger_value = trigger_value
        trigger.payout_amount_usd = payout_amount
        trigger.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(trigger)
        return trigger
