"""
API endpoints for evidence bundles.
"""

from typing import List, Optional
from datetime import datetime
import io
import zipfile
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context, require_user
from app.api.deps.rbac import PermissionChecker
from app.services.evidence_bundle_service import (
    EvidenceBundleService,
    BundleNotFoundError,
    BundleSealedError,
    BundleNotSealedError,
    EmptyBundleError
)
from app.schemas.evidence_bundle import (
    BundleCreateRequest,
    BundleResponse,
    BundleDetailResponse,
    BundleItemAddRequest,
    BundleItemResponse,
    BundleLinkRequest,
    BundleLinkResponse,
    BundleExportResponse,
    BundleManifest
)
from app.models.evidence import EvidenceObject
from app.models.evidence_bundle import EvidenceBundleItem
from app.core.audit_ledger.ledger import AuditLedger

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/evidence/bundles", tags=["Evidence Bundles"])


async def get_bundle_service(
    request: Request,
    db_session: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> EvidenceBundleService:
    """Get evidence bundle service with database session."""
    audit = AuditLedger(db_session)
    return EvidenceBundleService(db_session, audit)


@router.post(
    "",
    response_model=BundleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evidence bundle",
    description="Create a new evidence bundle in OPEN status"
)
async def create_bundle(
    request_data: BundleCreateRequest,
    http_request: Request,
    service: EvidenceBundleService = Depends(get_bundle_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user = Depends(require_user),
    _: None = Depends(PermissionChecker("evidence:write"))
) -> BundleResponse:
    """
    Create a new evidence bundle.
    
    Bundles are created in OPEN status and can have items added.
    Seal the bundle when ready to link to insurance decisions.
    """
    try:
        bundle = service.create_bundle(context.tenant_id, request_data, user.id)
        return BundleResponse.model_validate(bundle)
    except Exception as e:
        logger.error(f"Error creating bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    response_model=List[BundleResponse],
    summary="List evidence bundles",
    description="List evidence bundles with optional filters"
)
async def list_bundles(
    http_request: Request,
    bundle_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: EvidenceBundleService = Depends(get_bundle_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("evidence:read"))
) -> List[BundleResponse]:
    """List evidence bundles with optional filters."""
    try:
        if entity_type and entity_id:
            bundles = service.get_bundles_for_entity(entity_type, entity_id)
        else:
            # Simple list - in production, add filtering
            from app.models.evidence_bundle import EvidenceBundle
            query = service.db.query(EvidenceBundle).filter(
                EvidenceBundle.tenant_id == context.tenant_id
            )
            
            if bundle_type:
                query = query.filter(EvidenceBundle.bundle_type == bundle_type)
            if status_filter:
                query = query.filter(EvidenceBundle.status == status_filter)
            
            bundles = query.offset(offset).limit(limit).all()
        
        return [BundleResponse.model_validate(b) for b in bundles]
    except Exception as e:
        logger.error(f"Error listing bundles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{bundle_id}",
    response_model=BundleDetailResponse,
    summary="Get bundle details",
    description="Get bundle details including items and links"
)
async def get_bundle(
    bundle_id: str,
    http_request: Request,
    service: EvidenceBundleService = Depends(get_bundle_service),
    _: None = Depends(PermissionChecker("evidence:read"))
) -> BundleDetailResponse:
    """Get bundle details including items and links."""
    try:
        bundle = service._get_bundle(bundle_id)
        
        # Get items
        items = service.db.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == bundle_id
        ).order_by(EvidenceBundleItem.sequence).all()
        
        # Get links
        from app.models.evidence_bundle import EvidenceBundleLink
        links = service.db.query(EvidenceBundleLink).filter(
            EvidenceBundleLink.bundle_id == bundle_id
        ).all()
        
        # Build detail response
        return BundleDetailResponse(
            id=bundle.id,
            tenant_id=bundle.tenant_id,
            name=bundle.name,
            description=bundle.description,
            bundle_type=bundle.bundle_type,
            status=bundle.status,
            manifest_hash=bundle.manifest_hash,
            retention_class=bundle.retention_class,
            legal_hold=bundle.legal_hold,
            contains_pii=bundle.contains_pii,
            item_count=len(items),
            created_at=bundle.created_at,
            sealed_at=bundle.sealed_at,
            manifest=BundleManifest(**bundle.manifest_json) if bundle.manifest_json else None,
            items=[BundleItemResponse.model_validate(item) for item in items],
            links=[BundleLinkResponse.model_validate(link) for link in links],
            pii_categories=bundle.pii_categories
        )
    except BundleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{bundle_id}/items",
    response_model=BundleItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to bundle",
    description="Add an evidence object to a bundle"
)
async def add_bundle_item(
    bundle_id: str,
    request_data: BundleItemAddRequest,
    http_request: Request,
    service: EvidenceBundleService = Depends(get_bundle_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user = Depends(require_user),
    _: None = Depends(PermissionChecker("evidence:write"))
) -> BundleItemResponse:
    """Add an evidence object to a bundle."""
    try:
        item = service.add_item(bundle_id, request_data, user.id)
        return BundleItemResponse.model_validate(item)
    except BundleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BundleSealedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{bundle_id}/items/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from bundle",
    description="Remove an item from an OPEN bundle"
)
async def remove_bundle_item(
    bundle_id: str,
    evidence_id: str,
    http_request: Request,
    service: EvidenceBundleService = Depends(get_bundle_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user = Depends(require_user),
    _: None = Depends(PermissionChecker("evidence:write"))
):
    """Remove an item from an OPEN bundle."""
    try:
        service.remove_item(bundle_id, evidence_id, user.id)
    except BundleSealedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{bundle_id}/seal",
    response_model=BundleResponse,
    summary="Seal bundle",
    description="Seal a bundle, making it immutable and computing manifest hash"
)
async def seal_bundle(
    bundle_id: str,
    http_request: Request,
    service: EvidenceBundleService = Depends(get_bundle_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user = Depends(require_user),
    _: None = Depends(PermissionChecker("evidence:write"))
) -> BundleResponse:
    """
    Seal a bundle, making it immutable.
    
    Computes the manifest hash. After sealing, no items can be added or removed.
    """
    try:
        bundle = service.seal_bundle(bundle_id, user.id)
        return BundleResponse.model_validate(bundle)
    except EmptyBundleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BundleSealedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error sealing bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{bundle_id}/links",
    response_model=BundleLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link bundle to entity",
    description="Link a bundle to a domain entity"
)
async def link_bundle(
    bundle_id: str,
    request_data: BundleLinkRequest,
    http_request: Request,
    service: EvidenceBundleService = Depends(get_bundle_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user = Depends(require_user),
    _: None = Depends(PermissionChecker("evidence:write"))
) -> BundleLinkResponse:
    """Link a bundle to a domain entity."""
    try:
        link = service.link_to_entity(bundle_id, request_data, user.id)
        return BundleLinkResponse.model_validate(link)
    except BundleNotSealedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error linking bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{bundle_id}/verify",
    summary="Verify bundle integrity",
    description="Verify integrity of a sealed bundle"
)
async def verify_bundle(
    bundle_id: str,
    http_request: Request,
    service: EvidenceBundleService = Depends(get_bundle_service),
    _: None = Depends(PermissionChecker("evidence:read"))
) -> dict:
    """
    Verify integrity of a sealed bundle.
    
    Checks manifest hash and content hashes of all items.
    """
    try:
        return service.verify_bundle_integrity(bundle_id)
    except BundleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{bundle_id}/export",
    response_model=BundleExportResponse,
    summary="Export bundle",
    description="Export a bundle with verification manifest"
)
async def export_bundle(
    bundle_id: str,
    include_content: bool = Query(False, description="Include actual file content"),
    http_request: Request = None,
    service: EvidenceBundleService = Depends(get_bundle_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user = Depends(require_user),
    _: None = Depends(PermissionChecker("evidence:export"))
) -> BundleExportResponse:
    """
    Export a bundle with verification manifest.
    
    Returns manifest and download URLs for each evidence object.
    Can optionally include actual file content (for archival).
    """
    try:
        bundle = service._get_bundle(bundle_id)
        
        if bundle.status != 'SEALED':
            raise HTTPException(status_code=400, detail="Can only export SEALED bundles")
        
        # Get items
        items = service.db.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == bundle_id
        ).order_by(EvidenceBundleItem.sequence).all()
        
        # Generate download URLs (in production, use signed URLs)
        download_urls = []
        for item in items:
            # In production, generate signed URL with expiration
            # For now, return a placeholder URL
            url = f"/api/v3/evidence/objects/{item.evidence_id}/download"
            download_urls.append({
                "evidence_id": item.evidence_id,
                "content_hash": item.content_hash_at_addition,
                "url": url
            })
        
        # Build export response
        manifest = BundleManifest(**bundle.manifest_json) if bundle.manifest_json else None
        
        return BundleExportResponse(
            bundle_id=bundle.id,
            manifest=manifest,
            manifest_hash=bundle.manifest_hash or "",
            export_timestamp=datetime.utcnow(),
            verification_instructions="""
To verify this bundle:
1. Download all files using the provided URLs
2. Compute SHA256 hash of each file
3. Compare with content_hash in manifest
4. Compute SHA256 of the manifest JSON (sorted keys, no whitespace)
5. Compare with manifest_hash
            """.strip(),
            download_urls=download_urls
        )
        
    except BundleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{bundle_id}/export/zip",
    summary="Export bundle as ZIP",
    description="Export bundle as a ZIP file containing all evidence and manifest"
)
async def export_bundle_as_zip(
    bundle_id: str,
    background_tasks: BackgroundTasks,
    http_request: Request,
    service: EvidenceBundleService = Depends(get_bundle_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user = Depends(require_user),
    _: None = Depends(PermissionChecker("evidence:export"))
) -> StreamingResponse:
    """
    Export bundle as a ZIP file containing all evidence and manifest.
    
    For large bundles, this may take time and return a streaming response.
    """
    try:
        bundle = service._get_bundle(bundle_id)
        
        if bundle.status != 'SEALED':
            raise HTTPException(status_code=400, detail="Can only export SEALED bundles")
        
        # Create ZIP in memory
        zip_buffer = create_bundle_zip(bundle, service)
        
        # Audit the export
        background_tasks.add_task(
            service.audit.append_event,
            tenant_id=bundle.tenant_id,
            event_type="EVIDENCE_BUNDLE",
            action="EXPORTED",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="USER",
            actor_id=user.id,
            payload={"format": "zip"}
        )
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=bundle_{bundle_id}.zip"
            }
        )
        
    except BundleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting bundle as ZIP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_bundle_zip(bundle, service) -> io.BytesIO:
    """
    Create a ZIP file containing bundle contents and manifest.
    
    Args:
        bundle: EvidenceBundle instance
        service: EvidenceBundleService instance
        
    Returns:
        BytesIO buffer containing ZIP file
    """
    buffer = io.BytesIO()
    
    try:
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add manifest
            if bundle.manifest_json:
                manifest_json = json.dumps(bundle.manifest_json, indent=2, sort_keys=True)
                zf.writestr('manifest.json', manifest_json)
            
            # Add verification file
            verification = {
                "bundle_id": bundle.id,
                "manifest_hash": bundle.manifest_hash,
                "sealed_at": bundle.sealed_at.isoformat() if bundle.sealed_at else None,
                "verification_instructions": "Compute SHA256 of manifest.json and compare with manifest_hash"
            }
            zf.writestr('verification.json', json.dumps(verification, indent=2))
            
            # Add each evidence file
            items = service.db.query(EvidenceBundleItem).filter(
                EvidenceBundleItem.bundle_id == bundle.id
            ).order_by(EvidenceBundleItem.sequence).all()
            
            for item in items:
                evidence = service.db.query(EvidenceObject).filter(
                    EvidenceObject.id == item.evidence_id,
                    EvidenceObject.deleted_at.is_(None)
                ).first()
                
                if evidence:
                    # In production, download from storage
                    # For now, create a placeholder file with metadata
                    filename = evidence.filename or f"{evidence.id}.bin"
                    metadata = {
                        "evidence_id": evidence.id,
                        "content_hash": item.content_hash_at_addition,
                        "content_type": evidence.content_type,
                        "storage_uri": evidence.storage_uri,
                        "note": "Actual content not included. Download from storage_uri."
                    }
                    zf.writestr(
                        f"evidence/{filename}.metadata.json",
                        json.dumps(metadata, indent=2)
                    )
    except Exception as e:
        logger.error(f"Error creating bundle ZIP: {e}")
        raise
    
    buffer.seek(0)
    return buffer
