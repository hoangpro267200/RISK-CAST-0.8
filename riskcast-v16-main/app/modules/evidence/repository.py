"""
Evidence Repository
Data access layer for evidence
"""
from sqlalchemy.orm import Session
from typing import Optional, List

from app.modules.evidence.models import Evidence
from app.shared.exceptions import NotFoundError


class EvidenceRepository:
    """Repository for evidence data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, evidence_data: dict) -> Evidence:
        """Create a new evidence entry"""
        evidence = Evidence(**evidence_data)
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence
    
    def get_by_id(self, evidence_id: str, tenant_id: Optional[str] = None) -> Optional[Evidence]:
        """Get evidence by ID"""
        query = self.db.query(Evidence).filter(Evidence.id == evidence_id)
        if tenant_id:
            query = query.filter(Evidence.tenant_id == tenant_id)
        return query.first()
    
    def list_by_assessment(self, assessment_id: str, tenant_id: Optional[str] = None) -> List[Evidence]:
        """List evidence for an assessment"""
        query = self.db.query(Evidence).filter(Evidence.assessment_id == assessment_id)
        if tenant_id:
            query = query.filter(Evidence.tenant_id == tenant_id)
        return query.all()
