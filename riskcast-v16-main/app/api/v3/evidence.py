"""
Evidence API Endpoints
API v3 endpoints for evidence management
RISKCAST V3 - Modular Monolith
"""
from fastapi import APIRouter, Depends, Request, status
from typing import List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field
import logging

# Import dependencies
from app.shared.dependencies import TenantContext
from app.shared.utils import build_audit_context
from app.modules.rbac_policy.service import require_permission
from app.modules.rbac_policy.constants import Permissions
from app.modules.evidence.service import EvidenceService, StorageClient
from app.modules.evidence.models import EvidenceBundle

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession, get_tenant_scoped_db

logger = logging.getLogger(__name__)

# Evidence router
router = APIRouter(prefix="/evidence-bundles", tags=["evidence"])


# Schemas
class BundleCreate(BaseModel):
    """Schema for creating evidence bundle"""
    evidence_object_ids: List[str] = Field(..., description="List of evidence object IDs")
    links: List[Dict[str, Any]] = Field(..., description="List of link dictionaries")


class BundleResponse(BaseModel):
    """Schema for evidence bundle response"""
    id: str
    tenant_id: str
    schema_version: str
    bundle_hash: str
    created_by_user_id: str
    created_at: str
    
    class Config:
        from_attributes = True


# Storage client factory (mock implementation)
def get_storage_client() -> StorageClient:
    """Get storage client instance"""
    # In production, this would return actual S3 client
    # For now, return mock implementation
    try:
        from app.modules.evidence.service_example import MockStorageClient
        return MockStorageClient()
    except ImportError:
        # Fallback: create minimal mock
        class MockStorageClient(StorageClient):
            def __init__(self):
                self.storage = {}
            async def upload(self, uri: str, content: bytes) -> None:
                self.storage[uri] = content
            async def download(self, uri: str) -> bytes:
                return self.storage.get(uri, b"")
            async def delete(self, uri: str) -> None:
                if uri in self.storage:
                    del self.storage[uri]
        return MockStorageClient()


@router.post(
    "",
    response_model=BundleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evidence bundle",
    description="Create a new evidence bundle with canonical manifest"
)
async def create_evidence_bundle(
    data: BundleCreate,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.EVIDENCE_WRITE))
):
    """Create a new evidence bundle"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = EvidenceService(db, get_storage_client())
        bundle = await service.create_bundle(
            evidence_ids=data.evidence_object_ids,
            links=data.links,
            user_id=context.user_id,
            context=audit_context
        )
        
        return BundleResponse(
            id=bundle.id,
            tenant_id=bundle.tenant_id,
            schema_version=bundle.schema_version,
            bundle_hash=bundle.bundle_hash,
            created_by_user_id=bundle.created_by_user_id or "",
            created_at=bundle.created_at.isoformat() + 'Z'
        )
    finally:
        db_session.close()


@router.get(
    "/{id}/export",
    summary="Export evidence bundle",
    description="Export bundle manifest for verification"
)
async def export_evidence_bundle(
    id: str,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.EVIDENCE_EXPORT))
):
    """Export evidence bundle manifest"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        service = EvidenceService(db, get_storage_client())
        export_data = await service.export_bundle(id)
        
        return export_data
    finally:
        db_session.close()
