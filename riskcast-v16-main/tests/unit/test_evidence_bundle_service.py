"""
Tests for evidence bundle service.
"""

import pytest
from datetime import datetime
from app.shared.utils import generate_ulid
from app.models.evidence import EvidenceObject
from app.models.evidence_bundle import (
    EvidenceBundle,
    EvidenceBundleItem
)
from app.services.evidence_bundle_service import (
    EvidenceBundleService,
    BundleSealedError,
    EmptyBundleError,
    DuplicateItemError,
    BundleNotFoundError,
    EvidenceNotFoundError
)
from app.schemas.evidence_bundle import (
    BundleCreateRequest,
    BundleItemAddRequest,
    RetentionClass,
    BundleType,
    ItemRole,
    LinkType
)
from app.core.audit_ledger.ledger import AuditLedger


class TestEvidenceBundleService:
    """Unit tests for evidence bundle service."""
    
    @pytest.fixture
    def service(self, db_session):
        """Create service instance."""
        audit = AuditLedger(db_session)
        return EvidenceBundleService(db_session, audit)
    
    @pytest.fixture
    def tenant_id(self):
        """Test tenant ID."""
        return generate_ulid()
    
    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return generate_ulid()
    
    @pytest.fixture
    def evidence_object(self, db_session, tenant_id, user_id):
        """Create a test evidence object."""
        evidence = EvidenceObject(
            id=generate_ulid(),
            tenant_id=tenant_id,
            content_hash="test_hash_" + generate_ulid()[:10],
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
    
    @pytest.fixture
    def open_bundle(self, service, tenant_id, user_id):
        """Create an open bundle."""
        request = BundleCreateRequest(
            name="Test Bundle",
            bundle_type=BundleType.UNDERWRITING,
            retention_class=RetentionClass.STANDARD
        )
        return service.create_bundle(tenant_id, request, user_id)
    
    @pytest.fixture
    def bundle_with_item(self, service, open_bundle, evidence_object, user_id):
        """Create a bundle with one item."""
        request = BundleItemAddRequest(
            evidence_id=evidence_object.id,
            role=ItemRole.PRIMARY
        )
        item = service.add_item(open_bundle.id, request, user_id)
        return open_bundle, item
    
    @pytest.fixture
    def bundle_with_items(self, service, open_bundle, db_session, tenant_id, user_id):
        """Create a bundle with multiple items."""
        # Create additional evidence objects
        evidence1 = EvidenceObject(
            id=generate_ulid(),
            tenant_id=tenant_id,
            content_hash="hash1_" + generate_ulid()[:10],
            content_type="application/pdf",
            content_size_bytes=2048,
            storage_uri="file:///test/path1",
            storage_provider="local",
            filename="doc1.pdf",
            is_pii=False,
            created_by_user_id=user_id
        )
        evidence2 = EvidenceObject(
            id=generate_ulid(),
            tenant_id=tenant_id,
            content_hash="hash2_" + generate_ulid()[:10],
            content_type="image/png",
            content_size_bytes=512,
            storage_uri="file:///test/path2",
            storage_provider="local",
            filename="image.png",
            is_pii=False,
            created_by_user_id=user_id
        )
        db_session.add(evidence1)
        db_session.add(evidence2)
        db_session.commit()
        
        # Add items
        request1 = BundleItemAddRequest(evidence_id=evidence1.id, role=ItemRole.PRIMARY)
        request2 = BundleItemAddRequest(evidence_id=evidence2.id, role=ItemRole.SUPPORTING)
        service.add_item(open_bundle.id, request1, user_id)
        service.add_item(open_bundle.id, request2, user_id)
        
        db_session.refresh(open_bundle)
        return open_bundle
    
    @pytest.fixture
    def sealed_bundle(self, service, bundle_with_items, user_id):
        """Create a sealed bundle."""
        return service.seal_bundle(bundle_with_items.id, user_id)
    
    def test_create_bundle(self, service, tenant_id, user_id):
        """Test creating a new bundle."""
        request = BundleCreateRequest(
            name="Test Bundle",
            bundle_type=BundleType.UNDERWRITING,
            retention_class=RetentionClass.STANDARD
        )
        
        bundle = service.create_bundle(tenant_id, request, user_id)
        
        assert bundle.id is not None
        assert bundle.status == 'OPEN'
        assert bundle.bundle_type == "UNDERWRITING"
        assert bundle.retention_class == "STANDARD"
        assert bundle.tenant_id == tenant_id
    
    def test_add_item_to_bundle(self, service, open_bundle, evidence_object, user_id):
        """Test adding an item to a bundle."""
        request = BundleItemAddRequest(
            evidence_id=evidence_object.id,
            role=ItemRole.PRIMARY
        )
        
        item = service.add_item(open_bundle.id, request, user_id)
        
        assert item.evidence_id == evidence_object.id
        assert item.content_hash_at_addition == evidence_object.content_hash
        assert item.sequence == 1
        assert item.role == "PRIMARY"
    
    def test_cannot_add_to_sealed_bundle(self, service, sealed_bundle, evidence_object, user_id):
        """Cannot add items to sealed bundle."""
        request = BundleItemAddRequest(evidence_id=evidence_object.id)
        
        with pytest.raises(BundleSealedError):
            service.add_item(sealed_bundle.id, request, user_id)
    
    def test_cannot_add_duplicate_item(self, service, bundle_with_item, user_id):
        """Cannot add same evidence twice."""
        bundle, existing_item = bundle_with_item
        
        request = BundleItemAddRequest(evidence_id=existing_item.evidence_id)
        
        with pytest.raises(DuplicateItemError):
            service.add_item(bundle.id, request, user_id)
    
    def test_remove_item_from_bundle(self, service, bundle_with_item, user_id):
        """Test removing an item from a bundle."""
        bundle, item = bundle_with_item
        
        service.remove_item(bundle.id, item.evidence_id, user_id)
        
        # Verify item is removed
        remaining = service.db.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == bundle.id
        ).all()
        
        assert len(remaining) == 0
    
    def test_cannot_remove_from_sealed_bundle(self, service, sealed_bundle, user_id):
        """Cannot remove items from sealed bundle."""
        # Get first item
        items = service.db.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == sealed_bundle.id
        ).all()
        
        if items:
            with pytest.raises(BundleSealedError):
                service.remove_item(sealed_bundle.id, items[0].evidence_id, user_id)
    
    def test_seal_bundle(self, service, bundle_with_items, user_id):
        """Test sealing a bundle."""
        bundle = service.seal_bundle(bundle_with_items.id, user_id)
        
        assert bundle.status == 'SEALED'
        assert bundle.manifest_hash is not None
        assert bundle.manifest_json is not None
        assert bundle.sealed_at is not None
        assert bundle.sealed_by_user_id == user_id
        
        # Verify manifest structure
        manifest = bundle.manifest_json
        assert manifest['item_count'] == 2
        assert 'items' in manifest
        assert len(manifest['items']) == 2
    
    def test_cannot_seal_empty_bundle(self, service, open_bundle, user_id):
        """Cannot seal bundle with no items."""
        with pytest.raises(EmptyBundleError):
            service.seal_bundle(open_bundle.id, user_id)
    
    def test_cannot_seal_already_sealed_bundle(self, service, sealed_bundle, user_id):
        """Cannot seal an already sealed bundle."""
        with pytest.raises(BundleSealedError):
            service.seal_bundle(sealed_bundle.id, user_id)
    
    def test_verify_sealed_bundle_integrity(self, service, sealed_bundle):
        """Verify integrity of sealed bundle."""
        result = service.verify_bundle_integrity(sealed_bundle.id)
        
        assert result["valid"] is True
        assert result["manifest_hash"] == sealed_bundle.manifest_hash
        assert result["item_count"] > 0
        assert "verified_at" in result
    
    def test_verify_open_bundle_fails(self, service, open_bundle):
        """Verification fails for open bundles."""
        result = service.verify_bundle_integrity(open_bundle.id)
        
        assert result["valid"] is False
        assert result["error"] == "Bundle not sealed"
    
    def test_manifest_hash_deterministic(self, service, bundle_with_items, user_id, db_session):
        """Manifest hash should be deterministic for same items."""
        # Seal first time
        bundle1 = service.seal_bundle(bundle_with_items.id, user_id)
        hash1 = bundle1.manifest_hash
        
        # Get items
        items = db_session.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == bundle_with_items.id
        ).order_by(EvidenceBundleItem.sequence).all()
        
        # Rebuild manifest manually
        manifest = service._build_manifest(items)
        computed_hash = service._compute_manifest_hash(manifest)
        
        # Should match
        assert computed_hash == hash1
    
    def test_get_bundles_for_entity(self, service, sealed_bundle, user_id):
        """Test getting bundles linked to an entity."""
        from app.schemas.evidence_bundle import BundleLinkRequest, LinkType
        
        # Link bundle to entity
        link_request = BundleLinkRequest(
            entity_type="policy",
            entity_id=generate_ulid(),
            link_type=LinkType.PRIMARY
        )
        service.link_to_entity(sealed_bundle.id, link_request, user_id)
        
        # Get bundles
        bundles = service.get_bundles_for_entity(
            link_request.entity_type,
            link_request.entity_id
        )
        
        assert len(bundles) == 1
        assert bundles[0].id == sealed_bundle.id
    
    def test_set_legal_hold(self, service, sealed_bundle, user_id):
        """Test setting legal hold on bundle."""
        bundle = service.set_legal_hold(
            sealed_bundle.id,
            "Litigation pending",
            user_id
        )
        
        assert bundle.legal_hold is True
        assert bundle.legal_hold_reason == "Litigation pending"
        assert bundle.retention_class == "LEGAL_HOLD"
        assert bundle.expires_at is None
    
    def test_bundle_not_found_error(self, service, user_id):
        """Test bundle not found error."""
        fake_id = generate_ulid()
        
        with pytest.raises(BundleNotFoundError):
            service._get_bundle(fake_id)
    
    def test_add_nonexistent_evidence(self, service, open_bundle, user_id):
        """Test adding non-existent evidence."""
        request = BundleItemAddRequest(evidence_id=generate_ulid())
        
        with pytest.raises(EvidenceNotFoundError):
            service.add_item(open_bundle.id, request, user_id)
    
    def test_sequence_numbers(self, service, open_bundle, db_session, tenant_id, user_id):
        """Test sequence numbers are assigned correctly."""
        # Create multiple evidence objects
        evidence1 = EvidenceObject(
            id=generate_ulid(),
            tenant_id=tenant_id,
            content_hash="hash1",
            content_type="application/pdf",
            storage_uri="file:///test1",
            storage_provider="local",
            created_by_user_id=user_id
        )
        evidence2 = EvidenceObject(
            id=generate_ulid(),
            tenant_id=tenant_id,
            content_hash="hash2",
            content_type="application/pdf",
            storage_uri="file:///test2",
            storage_provider="local",
            created_by_user_id=user_id
        )
        db_session.add(evidence1)
        db_session.add(evidence2)
        db_session.commit()
        
        # Add items
        request1 = BundleItemAddRequest(evidence_id=evidence1.id)
        request2 = BundleItemAddRequest(evidence_id=evidence2.id)
        
        item1 = service.add_item(open_bundle.id, request1, user_id)
        item2 = service.add_item(open_bundle.id, request2, user_id)
        
        assert item1.sequence == 1
        assert item2.sequence == 2
