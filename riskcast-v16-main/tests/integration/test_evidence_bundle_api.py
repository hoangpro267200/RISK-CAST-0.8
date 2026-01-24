"""
Integration tests for evidence bundle API.
"""

import pytest
from datetime import datetime
from app.shared.utils import generate_ulid
from app.models.evidence import EvidenceObject
from app.models.evidence_bundle import EvidenceBundle, BundleType, BundleStatus


def create_evidence_object(db_session, tenant_id, user_id, content_hash=None):
    """Helper to create a test evidence object."""
    if content_hash is None:
        content_hash = "test_hash_" + generate_ulid()[:10]
    
    evidence = EvidenceObject(
        id=generate_ulid(),
        tenant_id=tenant_id,
        content_hash=content_hash,
        content_type="application/pdf",
        content_size_bytes=1024,
        storage_uri="file:///test/path",
        storage_provider="local",
        filename="test.pdf",
        is_pii=False,
        created_by_user_id=user_id
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    return evidence


class TestEvidenceBundleAPI:
    """Integration tests for evidence bundle API."""
    
    @pytest.fixture
    def evidence_objects(self, db_session, tenant_id, user_id):
        """Create test evidence objects."""
        evidence1 = create_evidence_object(db_session, tenant_id, user_id)
        evidence2 = create_evidence_object(db_session, tenant_id, user_id)
        evidence3 = create_evidence_object(db_session, tenant_id, user_id)
        return [evidence1, evidence2, evidence3]
    
    @pytest.fixture
    def sealed_bundle(self, db_session, tenant_id, user_id, evidence_objects):
        """Create a sealed bundle with items."""
        from app.services.evidence_bundle_service import EvidenceBundleService
        from app.core.audit_ledger.ledger import AuditLedger
        from app.schemas.evidence_bundle import BundleCreateRequest, BundleItemAddRequest
        
        service = EvidenceBundleService(db_session, AuditLedger(db_session))
        
        # Create bundle
        request = BundleCreateRequest(
            name="Test Bundle",
            bundle_type=BundleType.UNDERWRITING,
            retention_class="STANDARD"
        )
        bundle = service.create_bundle(tenant_id, request, user_id)
        
        # Add items
        for evidence in evidence_objects:
            item_request = BundleItemAddRequest(evidence_id=evidence.id)
            service.add_item(bundle.id, item_request, user_id)
        
        # Seal bundle
        sealed = service.seal_bundle(bundle.id, user_id)
        return sealed
    
    def test_create_seal_export_workflow(self, client, auth_headers, evidence_objects, tenant_id, user_id):
        """Test complete bundle workflow."""
        # 1. Create bundle
        response = client.post(
            "/api/v3/evidence/bundles",
            headers=auth_headers,
            json={
                "name": "Underwriting Evidence",
                "bundle_type": "UNDERWRITING",
                "retention_class": "STANDARD"
            }
        )
        assert response.status_code == 201
        bundle_id = response.json()["id"]
        
        # 2. Add items
        for evidence in evidence_objects:
            response = client.post(
                f"/api/v3/evidence/bundles/{bundle_id}/items",
                headers=auth_headers,
                json={"evidence_id": evidence.id, "role": "SUPPORTING"}
            )
            assert response.status_code == 201
        
        # 3. Seal bundle
        response = client.post(
            f"/api/v3/evidence/bundles/{bundle_id}/seal",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "SEALED"
        assert response.json()["manifest_hash"] is not None
        
        # 4. Verify integrity
        response = client.get(
            f"/api/v3/evidence/bundles/{bundle_id}/verify",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True
        
        # 5. Export
        response = client.get(
            f"/api/v3/evidence/bundles/{bundle_id}/export",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "manifest_hash" in data
        assert len(data["download_urls"]) == len(evidence_objects)
        assert "verification_instructions" in data
    
    def test_cannot_modify_sealed_bundle(self, client, auth_headers, sealed_bundle, evidence_objects):
        """Cannot add items to sealed bundle."""
        # Try to add item
        response = client.post(
            f"/api/v3/evidence/bundles/{sealed_bundle.id}/items",
            headers=auth_headers,
            json={"evidence_id": evidence_objects[0].id}
        )
        assert response.status_code == 409
        
        # Try to remove item
        items = client.get(
            f"/api/v3/evidence/bundles/{sealed_bundle.id}",
            headers=auth_headers
        ).json()["items"]
        
        if items:
            response = client.delete(
                f"/api/v3/evidence/bundles/{sealed_bundle.id}/items/{items[0]['evidence_id']}",
                headers=auth_headers
            )
            assert response.status_code == 409
    
    def test_export_zip(self, client, auth_headers, sealed_bundle):
        """Test exporting bundle as ZIP."""
        response = client.get(
            f"/api/v3/evidence/bundles/{sealed_bundle.id}/export/zip",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "attachment" in response.headers["content-disposition"]
        
        # Verify ZIP contains manifest
        import zipfile
        import io
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, 'r') as zf:
            assert 'manifest.json' in zf.namelist()
            assert 'verification.json' in zf.namelist()
    
    def test_list_bundles(self, client, auth_headers, sealed_bundle):
        """Test listing bundles."""
        response = client.get(
            "/api/v3/evidence/bundles",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        bundles = response.json()
        assert isinstance(bundles, list)
        assert len(bundles) >= 1
    
    def test_get_bundle_detail(self, client, auth_headers, sealed_bundle):
        """Test getting bundle details."""
        response = client.get(
            f"/api/v3/evidence/bundles/{sealed_bundle.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sealed_bundle.id
        assert "items" in data
        assert "links" in data
        assert "manifest" in data
    
    def test_link_bundle_to_entity(self, client, auth_headers, sealed_bundle):
        """Test linking bundle to entity."""
        entity_id = generate_ulid()
        
        response = client.post(
            f"/api/v3/evidence/bundles/{sealed_bundle.id}/links",
            headers=auth_headers,
            json={
                "entity_type": "policy",
                "entity_id": entity_id,
                "link_type": "PRIMARY"
            }
        )
        
        assert response.status_code == 201
        assert response.json()["entity_type"] == "policy"
        assert response.json()["entity_id"] == entity_id
    
    def test_cannot_export_open_bundle(self, client, auth_headers, evidence_objects, tenant_id, user_id):
        """Cannot export open bundle."""
        from app.services.evidence_bundle_service import EvidenceBundleService
        from app.core.audit_ledger.ledger import AuditLedger
        from app.schemas.evidence_bundle import BundleCreateRequest
        
        # Create open bundle
        service = EvidenceBundleService(client.app.state.db, AuditLedger(client.app.state.db))
        request = BundleCreateRequest(
            name="Open Bundle",
            bundle_type=BundleType.UNDERWRITING
        )
        bundle = service.create_bundle(tenant_id, request, user_id)
        
        # Try to export
        response = client.get(
            f"/api/v3/evidence/bundles/{bundle.id}/export",
            headers=auth_headers
        )
        
        assert response.status_code == 400
