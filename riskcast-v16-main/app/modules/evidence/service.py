"""
Evidence Service
Business logic for evidence management with storage and bundle hashing
RISKCAST V3 - Modular Monolith
"""
import hashlib
import json
import mimetypes
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
import logging

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession

from app.modules.evidence.models import (
    EvidenceObject,
    EvidenceLink,
    EvidenceBundle,
    EvidenceType,
    RetentionClass
)
from app.modules.evidence.exceptions import (
    EvidenceNotFoundError,
    BundleNotFoundError,
    StorageError,
    InvalidBundleManifestError
)
from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.models import ActorType
from app.modules.audit_ledger.schemas import AuditContext
from app.shared.utils import generate_ulid

# Import settings (with fallback if not available)
try:
    from app.config import settings
except ImportError:
    # Fallback for environments without config
    class Settings:
        EVIDENCE_BUCKET = "riskcast-evidence"
    settings = Settings()

logger = logging.getLogger(__name__)


# Storage client interface (abstract)
class StorageClient:
    """Abstract storage client interface"""
    
    async def upload(self, uri: str, content: bytes) -> None:
        """Upload content to storage URI"""
        raise NotImplementedError
    
    async def download(self, uri: str) -> bytes:
        """Download content from storage URI"""
        raise NotImplementedError
    
    async def delete(self, uri: str) -> None:
        """Delete content from storage URI"""
        raise NotImplementedError


class EvidenceService:
    """Service for evidence management with storage and bundle hashing"""
    
    BUNDLE_SCHEMA_VERSION = "evidence_bundle_v1.0"
    
    def __init__(self, db: 'TenantScopedSession', storage_client: StorageClient):
        """
        Initialize evidence service.
        
        Args:
            db: Tenant-scoped database session
            storage_client: Storage client for file operations
        """
        self.db = db
        self.storage = storage_client
        self.audit = AuditLedgerService(db._raw_session)
    
    def _generate_storage_uri(self, evidence_id: str, filename: str) -> str:
        """
        Generate S3 URI with tenant isolation.
        
        Args:
            evidence_id: Evidence object ID (ULID)
            filename: Original filename
            
        Returns:
            Storage URI (e.g., s3://bucket/tenants/{tenant_id}/evidence/{year}/{month}/{evidence_id}/{filename})
        """
        now = datetime.utcnow()
        return (
            f"s3://{settings.EVIDENCE_BUCKET}/tenants/{self.db.tenant_id}/"
            f"evidence/{now.year}/{now.month:02d}/{evidence_id}/{filename}"
        )
    
    def _compute_content_hash(self, content: bytes) -> str:
        """
        Compute SHA256 hash of content.
        
        Args:
            content: File content bytes
            
        Returns:
            SHA256 hash as hex string (64 characters)
        """
        return hashlib.sha256(content).hexdigest()
    
    async def upload_evidence(
        self,
        file_content: bytes,
        filename: str,
        evidence_type: EvidenceType,
        source: str,
        captured_at: Optional[datetime],
        user_id: str,
        context: AuditContext,
        metadata: Optional[Dict[str, Any]] = None,
        pii_flags: Optional[Dict[str, Any]] = None
    ) -> EvidenceObject:
        """
        Upload and register evidence object.
        
        Features:
        - Content hashing for deduplication
        - Storage upload
        - Metadata and PII flags
        - Audit logging
        
        Args:
            file_content: File content bytes
            filename: Original filename
            evidence_type: Type of evidence
            source: Source identifier (UPLOAD, NOAA, etc.)
            captured_at: When evidence was captured (optional)
            user_id: User ID who uploaded
            context: Audit context
            metadata: Safe metadata (no PII)
            pii_flags: PII flags (contains_name, etc.)
            
        Returns:
            EvidenceObject instance
        """
        # Compute content hash
        content_hash = self._compute_content_hash(file_content)
        
        # Check for duplicate by hash (deduplication)
        existing = self.db.query(EvidenceObject).filter(
            EvidenceObject.content_hash == content_hash,
            EvidenceObject.tenant_id == self.db.tenant_id
        ).first()
        
        if existing:
            logger.info(f"Evidence deduplication: Found existing evidence {existing.id} with hash {content_hash[:16]}...")
            return existing  # Return existing evidence (dedupe by hash)
        
        # Generate evidence ID and storage path
        evidence_id = generate_ulid()
        storage_uri = self._generate_storage_uri(evidence_id, filename)
        
        # Upload to storage
        try:
            await self.storage.upload(storage_uri, file_content)
        except Exception as e:
            logger.error(f"Storage upload failed for {storage_uri}: {e}")
            raise StorageError(f"Failed to upload evidence: {str(e)}")
        
        # Create evidence record
        evidence = EvidenceObject(
            id=evidence_id,
            tenant_id=self.db.tenant_id,
            type=evidence_type,
            source=source,
            storage_uri=storage_uri,
            content_hash=content_hash,
            mime_type=mimetypes.guess_type(filename)[0],
            size_bytes=len(file_content),
            captured_at=captured_at,
            ingested_at=datetime.utcnow(),
            retention_class=RetentionClass.STANDARD,
            metadata_json=metadata,
            pii_flags_json=pii_flags
        )
        
        self.db.add(evidence)
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action='evidence.uploaded',
            resource_type='evidence_object',
            resource_id=str(evidence_id),
            context=context,
            diff={
                'type': evidence_type.value,
                'source': source,
                'size_bytes': len(file_content),
                'content_hash': content_hash[:16] + '...'  # Truncate for audit
            }
        )
        
        logger.info(f"Evidence uploaded: {evidence_id} ({filename}, {len(file_content)} bytes)")
        return evidence
    
    async def link_evidence(
        self,
        evidence_id: str,
        resource_type: str,
        resource_id: str,
        relationship_type: str
    ) -> EvidenceLink:
        """
        Link evidence to a resource.
        
        Args:
            evidence_id: Evidence object ID
            resource_type: Resource type (risk_run, claim, assessment, etc.)
            resource_id: Resource ID
            relationship_type: Relationship type (SUPPORTS, DERIVED_FROM, ATTACHED, etc.)
            
        Returns:
            EvidenceLink instance
        """
        # Verify evidence exists and belongs to tenant
        evidence = self.db.query(EvidenceObject).filter(
            EvidenceObject.id == evidence_id,
            EvidenceObject.tenant_id == self.db.tenant_id
        ).first()
        
        if not evidence:
            raise EvidenceNotFoundError(evidence_id)
        
        # Create link
        link = EvidenceLink(
            tenant_id=self.db.tenant_id,
            evidence_id=evidence_id,
            resource_type=resource_type,
            resource_id=resource_id,
            relationship_type=relationship_type
        )
        
        self.db.add(link)
        self.db.commit()
        
        logger.info(f"Evidence linked: {evidence_id} -> {resource_type}:{resource_id} ({relationship_type})")
        return link
    
    async def create_bundle(
        self,
        evidence_ids: List[str],
        links: List[Dict[str, Any]],
        user_id: str,
        context: AuditContext
    ) -> EvidenceBundle:
        """
        Create evidence bundle with canonical manifest and hash.
        
        Features:
        - Canonical JSON manifest
        - SHA256 bundle hash for integrity
        - Automatic evidence linking
        
        Args:
            evidence_ids: List of evidence object IDs
            links: List of link dictionaries with keys: evidence_id, resource_type, resource_id, relationship
            user_id: User ID who created bundle
            context: Audit context
            
        Returns:
            EvidenceBundle instance
        """
        # Load evidence objects
        evidence_objects = self.db.query(EvidenceObject).filter(
            EvidenceObject.id.in_(evidence_ids),
            EvidenceObject.tenant_id == self.db.tenant_id
        ).all()
        
        if len(evidence_objects) != len(evidence_ids):
            found_ids = {e.id for e in evidence_objects}
            missing_ids = set(evidence_ids) - found_ids
            raise EvidenceNotFoundError(f"Some evidence objects not found: {missing_ids}")
        
        # Build manifest
        manifest = {
            'evidence_objects': [
                {
                    'id': str(e.id),
                    'type': e.type.value,
                    'content_hash': e.content_hash,
                    'captured_at': e.captured_at.isoformat() + 'Z' if e.captured_at else None,
                    'source': e.source
                }
                for e in evidence_objects
            ],
            'links': links,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Compute bundle hash (canonical JSON)
        canonical_manifest = json.dumps(manifest, sort_keys=True, separators=(',', ':'))
        bundle_hash = hashlib.sha256(canonical_manifest.encode()).hexdigest()
        
        # Create bundle
        bundle = EvidenceBundle(
            tenant_id=self.db.tenant_id,
            schema_version=self.BUNDLE_SCHEMA_VERSION,
            manifest_json=manifest,
            bundle_hash=bundle_hash,
            created_by_user_id=user_id
        )
        
        self.db.add(bundle)
        self.db.commit()
        
        # Create links
        for link_data in links:
            await self.link_evidence(
                link_data['evidence_id'],
                link_data['resource_type'],
                link_data['resource_id'],
                link_data['relationship']
            )
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action='evidence.bundle.created',
            resource_type='evidence_bundle',
            resource_id=str(bundle.id),
            context=context,
            diff={
                'evidence_count': len(evidence_ids),
                'link_count': len(links),
                'bundle_hash': bundle_hash[:16] + '...'  # Truncate for audit
            }
        )
        
        logger.info(f"Evidence bundle created: {bundle.id} ({len(evidence_ids)} evidence objects)")
        return bundle
    
    async def export_bundle(self, bundle_id: str) -> Dict[str, Any]:
        """
        Export bundle manifest for verification.
        
        Args:
            bundle_id: Bundle ID
            
        Returns:
            Dictionary with bundle export data including verification info
        """
        bundle = self.db.query(EvidenceBundle).filter(
            EvidenceBundle.id == bundle_id,
            EvidenceBundle.tenant_id == self.db.tenant_id
        ).first()
        
        if not bundle:
            raise BundleNotFoundError(bundle_id)
        
        return {
            'bundle_id': str(bundle.id),
            'schema_version': bundle.schema_version,
            'manifest': bundle.manifest_json,
            'bundle_hash': bundle.bundle_hash,
            'verification': {
                'algorithm': 'SHA256',
                'canonicalization': 'JSON with sorted keys, no whitespace',
                'computed_hash': self._verify_bundle_hash(bundle)
            }
        }
    
    def _verify_bundle_hash(self, bundle: EvidenceBundle) -> str:
        """
        Verify bundle hash by recomputing from manifest.
        
        Args:
            bundle: EvidenceBundle instance
            
        Returns:
            Computed hash
        """
        canonical_manifest = json.dumps(bundle.manifest_json, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_manifest.encode()).hexdigest()
    
    async def verify_bundle_integrity(self, bundle_id: str) -> bool:
        """
        Verify bundle integrity by comparing stored hash with computed hash.
        
        Args:
            bundle_id: Bundle ID
            
        Returns:
            True if integrity is valid, False otherwise
        """
        bundle = self.db.query(EvidenceBundle).filter(
            EvidenceBundle.id == bundle_id,
            EvidenceBundle.tenant_id == self.db.tenant_id
        ).first()
        
        if not bundle:
            raise BundleNotFoundError(bundle_id)
        
        computed_hash = self._verify_bundle_hash(bundle)
        return computed_hash == bundle.bundle_hash
