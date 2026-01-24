"""
Claims Repository
Data access layer for claims
"""
from sqlalchemy.orm import Session
from typing import Optional, List

from app.modules.claims.models import Claim, ClaimStatus
from app.shared.exceptions import NotFoundError


class ClaimsRepository:
    """Repository for claims data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, claim_data: dict) -> Claim:
        """Create a new claim"""
        claim = Claim(**claim_data)
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim
    
    def get_by_id(self, claim_id: str, tenant_id: Optional[str] = None) -> Optional[Claim]:
        """Get claim by ID"""
        query = self.db.query(Claim).filter(Claim.id == claim_id)
        if tenant_id:
            query = query.filter(Claim.tenant_id == tenant_id)
        return query.first()
    
    def get_by_claim_number(self, claim_number: str, tenant_id: Optional[str] = None) -> Optional[Claim]:
        """Get claim by claim number"""
        query = self.db.query(Claim).filter(Claim.claim_number == claim_number)
        if tenant_id:
            query = query.filter(Claim.tenant_id == tenant_id)
        return query.first()
    
    def list_by_tenant(self, tenant_id: str, status: Optional[ClaimStatus] = None,
                      skip: int = 0, limit: int = 100) -> List[Claim]:
        """List claims for a tenant"""
        query = self.db.query(Claim).filter(Claim.tenant_id == tenant_id)
        if status:
            query = query.filter(Claim.status == status)
        return query.order_by(Claim.created_at.desc()).offset(skip).limit(limit).all()
