"""
Compliance API endpoints.

GDPR and regulatory compliance endpoints.
"""

from typing import Optional
from datetime import datetime
import io
from fastapi import APIRouter, Depends, HTTPException, Response, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker
from app.services.compliance.gdpr_service import (
    GDPRService,
    InvalidDeletionTokenError
)
from app.services.compliance.decision_pack_service import (
    DecisionPackService,
    PolicyNotFoundError,
    ClaimNotFoundError
)
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

router = APIRouter(prefix="/compliance", tags=["Compliance"])


def get_gdpr_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> GDPRService:
    """Dependency to get GDPRService."""
    audit = AuditLedger(db)
    return GDPRService(db, audit)


def get_decision_pack_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> DecisionPackService:
    """Dependency to get DecisionPackService."""
    audit = AuditLedger(db)
    return DecisionPackService(db, audit)


@router.post("/gdpr/export", response_class=Response)
async def export_user_data(
    user_id: Optional[str] = None,
    service: GDPRService = Depends(get_gdpr_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("compliance:export"))
):
    """
    Export user data (GDPR Data Subject Access Request).
    
    Returns a ZIP file containing all personal data for the specified user.
    """
    # Use provided user_id or current user
    target_user_id = user_id or context.user_id
    
    if not target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )
    
    # Generate request reference
    request_reference = f"GDPR-{datetime.utcnow().strftime('%Y%m%d')}-{generate_ulid()[:8]}"
    
    # Export data
    zip_bytes = service.export_user_data(
        user_id=target_user_id,
        requested_by=context.user_id or context.actor_id,
        request_reference=request_reference
    )
    
    # Return as downloadable file
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=gdpr_export_{target_user_id}_{request_reference}.zip"
        }
    )


@router.post("/gdpr/delete")
async def delete_user_data(
    user_id: str,
    verification_token: str,
    service: GDPRService = Depends(get_gdpr_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("compliance:delete"))
):
    """
    Delete user data (GDPR Right to Erasure).
    
    Requires verification token to prevent accidental deletion.
    Returns deletion report with actions taken.
    """
    # Generate request reference
    request_reference = f"GDPR-DEL-{datetime.utcnow().strftime('%Y%m%d')}-{generate_ulid()[:8]}"
    
    try:
        deletion_report = service.process_deletion_request(
            user_id=user_id,
            requested_by=context.user_id or context.actor_id,
            request_reference=request_reference,
            verification_token=verification_token
        )
        
        return deletion_report
    except InvalidDeletionTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/policies/{policy_id}/decision-pack", response_class=StreamingResponse)
async def get_policy_decision_pack(
    policy_id: str,
    purpose: str = Query("AUDIT", description="Purpose of pack (AUDIT, REGULATORY, etc.)"),
    service: DecisionPackService = Depends(get_decision_pack_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("compliance:export"))
):
    """
    Generate and download policy decision pack.
    
    Contains all information needed to verify the underwriting decision.
    """
    try:
        zip_bytes = service.generate_policy_decision_pack(
            policy_id=policy_id,
            generated_by=context.user_id or context.actor_id,
            purpose=purpose
        )
        
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=decision_pack_policy_{policy_id}.zip"
            }
        )
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/claims/{claim_id}/decision-pack", response_class=StreamingResponse)
async def get_claim_decision_pack(
    claim_id: str,
    purpose: str = Query("AUDIT", description="Purpose of pack (AUDIT, REGULATORY, etc.)"),
    service: DecisionPackService = Depends(get_decision_pack_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("compliance:export"))
):
    """
    Generate and download claim decision pack.
    
    Contains all information needed to verify the claim decision.
    """
    try:
        zip_bytes = service.generate_claim_decision_pack(
            claim_id=claim_id,
            generated_by=context.user_id or context.actor_id,
            purpose=purpose
        )
        
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=decision_pack_claim_{claim_id}.zip"
            }
        )
    except ClaimNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
