"""
Underwriting Repository
Data access layer for underwriting
"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.modules.underwriting.models import UnderwritingDecision, UnderwritingStatus
from app.shared.exceptions import NotFoundError


class UnderwritingRepository:
    """Repository for underwriting data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, decision_data: dict) -> UnderwritingDecision:
        """Create a new underwriting decision"""
        decision = UnderwritingDecision(**decision_data)
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision
    
    def get_by_id(self, decision_id: str, tenant_id: Optional[str] = None) -> Optional[UnderwritingDecision]:
        """Get decision by ID"""
        query = self.db.query(UnderwritingDecision).filter(UnderwritingDecision.id == decision_id)
        if tenant_id:
            query = query.filter(UnderwritingDecision.tenant_id == tenant_id)
        return query.first()
    
    def get_by_assessment(self, assessment_id: str) -> Optional[UnderwritingDecision]:
        """Get decision by assessment ID"""
        return self.db.query(UnderwritingDecision).filter(
            UnderwritingDecision.assessment_id == assessment_id
        ).first()
    
    def update_status(self, decision_id: str, status: UnderwritingStatus,
                     decision: Optional[str] = None, underwriter_id: Optional[str] = None) -> UnderwritingDecision:
        """Update decision status"""
        decision_obj = self.get_by_id(decision_id)
        if not decision_obj:
            raise NotFoundError("UnderwritingDecision", decision_id)
        
        decision_obj.status = status
        if decision:
            decision_obj.decision = decision
        if underwriter_id:
            decision_obj.underwriter_id = underwriter_id
            decision_obj.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(decision_obj)
        return decision_obj
