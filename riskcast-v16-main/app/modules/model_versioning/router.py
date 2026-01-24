"""
Model Versioning Router
FastAPI routes for model versioning
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse
from app.shared.dependencies import require_user
from app.modules.model_versioning.service import ModelVersioningService
from app.modules.model_versioning.schemas import RiskModelVersionCreate, RiskModelVersionResponse

router = APIRouter(prefix="/model-versions", tags=["Model Versioning"])


@router.get("", response_model=StandardResponse)
async def list_versions(
    db: Session = Depends(get_db),
    current_user = Depends(require_user)
):
    """List all model versions"""
    service = ModelVersioningService(db)
    versions = service.list_versions()
    return StandardResponse(
        success=True,
        data={"versions": [v.dict() for v in versions]},
        message="Model versions retrieved"
    )
