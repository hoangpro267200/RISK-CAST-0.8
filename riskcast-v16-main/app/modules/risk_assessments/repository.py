"""
Risk Assessments Repository
Data access layer for risk assessments
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from datetime import datetime
import hashlib
import json

from app.modules.risk_assessments.models import RiskAssessment
from app.shared.exceptions import NotFoundError


class RiskAssessmentRepository:
    """Repository for risk assessment data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, assessment_data: dict) -> RiskAssessment:
        """Create a new risk assessment"""
        # Generate input hash
        input_str = json.dumps(assessment_data["input_data"], sort_keys=True)
        input_hash = hashlib.sha256(input_str.encode()).hexdigest()
        assessment_data["input_hash"] = input_hash
        
        # Generate result hash if result_data provided
        if "result_data" in assessment_data:
            result_str = json.dumps(assessment_data["result_data"], sort_keys=True)
            result_hash = hashlib.sha256(result_str.encode()).hexdigest()
            assessment_data["result_hash"] = result_hash
        
        assessment = RiskAssessment(**assessment_data)
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def get_by_id(self, assessment_id: str, tenant_id: Optional[str] = None) -> Optional[RiskAssessment]:
        """Get assessment by ID"""
        query = self.db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id)
        if tenant_id:
            query = query.filter(RiskAssessment.tenant_id == tenant_id)
        return query.first()
    
    def get_by_assessment_id(self, assessment_id: str, tenant_id: Optional[str] = None) -> Optional[RiskAssessment]:
        """Get assessment by assessment_id"""
        query = self.db.query(RiskAssessment).filter(RiskAssessment.assessment_id == assessment_id)
        if tenant_id:
            query = query.filter(RiskAssessment.tenant_id == tenant_id)
        return query.first()
    
    def find_duplicate(self, input_hash: str, tenant_id: Optional[str] = None) -> Optional[RiskAssessment]:
        """Find duplicate assessment by input hash"""
        query = self.db.query(RiskAssessment).filter(RiskAssessment.input_hash == input_hash)
        if tenant_id:
            query = query.filter(RiskAssessment.tenant_id == tenant_id)
        return query.order_by(desc(RiskAssessment.created_at)).first()
    
    def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[RiskAssessment]:
        """List assessments for a tenant"""
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.tenant_id == tenant_id
        ).order_by(desc(RiskAssessment.created_at)).offset(skip).limit(limit).all()
    
    def count_by_tenant(self, tenant_id: str) -> int:
        """Count assessments for a tenant"""
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.tenant_id == tenant_id
        ).count()
