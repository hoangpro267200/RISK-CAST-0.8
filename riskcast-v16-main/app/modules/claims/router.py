"""
Claims Router
FastAPI routes for claims
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse, PaginationParams
from app.shared.dependencies import require_user, require_tenant
from app.modules.claims.service import ClaimsService
from app.modules.claims.schemas import ClaimCreate, ClaimResponse, ClaimStatus

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.post("", response_model=StandardResponse)
async def create_claim(
    claim_data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Create a new claim"""
    service = ClaimsService(db)
    claim = service.create_claim(claim_data, tenant_id, current_user.id)
    return StandardResponse(
        success=True,
        data=claim.dict(),
        message="Claim created"
    )


@router.get("/{claim_id}", response_model=StandardResponse)
async def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Get claim by ID"""
    service = ClaimsService(db)
    claim = service.get_claim(claim_id, tenant_id)
    return StandardResponse(
        success=True,
        data=claim.dict(),
        message="Claim retrieved"
    )


@router.get("", response_model=StandardResponse)
async def list_claims(
    status: ClaimStatus = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """List claims"""
    service = ClaimsService(db)
    claims = service.list_claims(tenant_id, status, pagination.offset, pagination.limit)
    return StandardResponse(
        success=True,
        data={"claims": [c.dict() for c in claims]},
        message="Claims retrieved"
    )
