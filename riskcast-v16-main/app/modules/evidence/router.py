"""
Evidence Router
FastAPI routes for evidence management
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse
from app.shared.dependencies import require_user, require_tenant
from app.modules.evidence.service import EvidenceService
from app.modules.evidence.schemas import EvidenceCreate, EvidenceResponse

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.post("", response_model=StandardResponse)
async def upload_evidence(
    assessment_id: str,
    evidence_type: str,
    title: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Upload evidence file"""
    service = EvidenceService(db)
    
    # Read file content
    file_content = await file.read()
    
    # Save file
    file_path = service.save_file(file_content, file.filename, tenant_id)
    
    # Create evidence entry
    evidence_data = EvidenceCreate(
        assessment_id=assessment_id,
        evidence_type=evidence_type,
        title=title,
        source="file_upload"
    )
    evidence = service.create_evidence(evidence_data, tenant_id, file_path, current_user.id)
    
    return StandardResponse(
        success=True,
        data=evidence.dict(),
        message="Evidence uploaded"
    )


@router.get("/assessment/{assessment_id}", response_model=StandardResponse)
async def list_evidence(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """List evidence for an assessment"""
    service = EvidenceService(db)
    evidence_list = service.list_evidence(assessment_id, tenant_id)
    return StandardResponse(
        success=True,
        data={"evidence": [e.dict() for e in evidence_list]},
        message="Evidence retrieved"
    )
