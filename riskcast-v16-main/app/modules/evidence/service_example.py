"""
Evidence Service Usage Examples
Examples demonstrating how to use EvidenceService
RISKCAST V3 - Modular Monolith
"""
import asyncio
from datetime import datetime
from typing import Optional

from app.modules.evidence.service import EvidenceService, StorageClient
from app.modules.evidence.models import EvidenceType
from app.modules.audit_ledger.schemas import AuditContext
from app.database import get_tenant_scoped_db
from app.shared.utils import build_audit_context


# Example: Mock storage client (implement actual S3 client in production)
class MockStorageClient(StorageClient):
    """Mock storage client for testing/development"""
    
    def __init__(self):
        self.storage = {}  # In-memory storage
    
    async def upload(self, uri: str, content: bytes) -> None:
        """Upload to mock storage"""
        self.storage[uri] = content
        print(f"[MockStorage] Uploaded {len(content)} bytes to {uri}")
    
    async def download(self, uri: str) -> bytes:
        """Download from mock storage"""
        if uri not in self.storage:
            raise FileNotFoundError(f"URI not found: {uri}")
        return self.storage[uri]
    
    async def delete(self, uri: str) -> None:
        """Delete from mock storage"""
        if uri in self.storage:
            del self.storage[uri]
            print(f"[MockStorage] Deleted {uri}")


async def example_upload_evidence():
    """Example: Upload evidence"""
    from fastapi import Request
    from app.database import get_db
    
    # Get database session
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        # Get tenant-scoped session (in real usage, this comes from FastAPI dependency)
        # For example, from request context
        request = None  # Would be FastAPI Request object
        db = await get_tenant_scoped_db(request, db_session)
        
        # Initialize service
        storage_client = MockStorageClient()
        service = EvidenceService(db, storage_client)
        
        # Prepare file content
        file_content = b"Sample document content"
        filename = "document.pdf"
        
        # Create audit context
        context = AuditContext(
            request_id="req-123",
            trace_id="trace-456",
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            route="/api/v3/evidence",
            method="POST"
        )
        
        # Upload evidence
        evidence = await service.upload_evidence(
            file_content=file_content,
            filename=filename,
            evidence_type=EvidenceType.DOCUMENT,
            source="UPLOAD",
            captured_at=datetime.utcnow(),
            user_id="user-123",
            context=context,
            metadata={"title": "Shipping Document", "pages": 5},
            pii_flags={"contains_name": False, "contains_email": False}
        )
        
        print(f"✅ Evidence uploaded: {evidence.id}")
        print(f"   Storage URI: {evidence.storage_uri}")
        print(f"   Content Hash: {evidence.content_hash}")
        print(f"   Size: {evidence.size_bytes} bytes")
        
        return evidence
        
    finally:
        db_session.close()


async def example_link_evidence():
    """Example: Link evidence to resource"""
    from app.database import get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        request = None
        db = await get_tenant_scoped_db(request, db_session)
        
        storage_client = MockStorageClient()
        service = EvidenceService(db, storage_client)
        
        # Link evidence to risk run
        link = await service.link_evidence(
            evidence_id="evidence-123",
            resource_type="risk_run",
            resource_id="run-456",
            relationship_type="SUPPORTS"
        )
        
        print(f"✅ Evidence linked: {link.id}")
        print(f"   Evidence: {link.evidence_id}")
        print(f"   Resource: {link.resource_type}:{link.resource_id}")
        print(f"   Relationship: {link.relationship_type}")
        
        return link
        
    finally:
        db_session.close()


async def example_create_bundle():
    """Example: Create evidence bundle"""
    from app.database import get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        request = None
        db = await get_tenant_scoped_db(request, db_session)
        
        storage_client = MockStorageClient()
        service = EvidenceService(db, storage_client)
        
        # Create audit context
        context = AuditContext(
            request_id="req-789",
            trace_id="trace-012",
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            route="/api/v3/evidence/bundles",
            method="POST"
        )
        
        # Create bundle with evidence IDs and links
        bundle = await service.create_bundle(
            evidence_ids=["evidence-1", "evidence-2", "evidence-3"],
            links=[
                {
                    "evidence_id": "evidence-1",
                    "resource_type": "risk_run",
                    "resource_id": "run-456",
                    "relationship": "SUPPORTS"
                },
                {
                    "evidence_id": "evidence-2",
                    "resource_type": "risk_run",
                    "resource_id": "run-456",
                    "relationship": "DERIVED_FROM"
                }
            ],
            user_id="user-123",
            context=context
        )
        
        print(f"✅ Bundle created: {bundle.id}")
        print(f"   Schema Version: {bundle.schema_version}")
        print(f"   Bundle Hash: {bundle.bundle_hash}")
        print(f"   Evidence Count: {len(bundle.manifest_json['evidence_objects'])}")
        
        return bundle
        
    finally:
        db_session.close()


async def example_export_bundle():
    """Example: Export bundle for verification"""
    from app.database import get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        request = None
        db = await get_tenant_scoped_db(request, db_session)
        
        storage_client = MockStorageClient()
        service = EvidenceService(db, storage_client)
        
        # Export bundle
        export_data = await service.export_bundle("bundle-123")
        
        print(f"✅ Bundle exported: {export_data['bundle_id']}")
        print(f"   Schema Version: {export_data['schema_version']}")
        print(f"   Bundle Hash: {export_data['bundle_hash']}")
        print(f"   Verification Algorithm: {export_data['verification']['algorithm']}")
        print(f"   Computed Hash: {export_data['verification']['computed_hash']}")
        print(f"   Hash Match: {export_data['bundle_hash'] == export_data['verification']['computed_hash']}")
        
        return export_data
        
    finally:
        db_session.close()


async def example_verify_bundle_integrity():
    """Example: Verify bundle integrity"""
    from app.database import get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        request = None
        db = await get_tenant_scoped_db(request, db_session)
        
        storage_client = MockStorageClient()
        service = EvidenceService(db, storage_client)
        
        # Verify bundle integrity
        is_valid = await service.verify_bundle_integrity("bundle-123")
        
        if is_valid:
            print("✅ Bundle integrity verified: Hash matches")
        else:
            print("❌ Bundle integrity check failed: Hash mismatch")
        
        return is_valid
        
    finally:
        db_session.close()


if __name__ == "__main__":
    print("Evidence Service Examples")
    print("=" * 50)
    
    # Run examples
    # asyncio.run(example_upload_evidence())
    # asyncio.run(example_link_evidence())
    # asyncio.run(example_create_bundle())
    # asyncio.run(example_export_bundle())
    # asyncio.run(example_verify_bundle_integrity())
    
    print("\n✅ Examples defined (uncomment to run)")
