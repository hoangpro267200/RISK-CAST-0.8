"""
Unit Tests for Evidence Service
Tests for evidence upload, linking, and management.
"""
import pytest
import hashlib
import tempfile
import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.services.evidence_service import EvidenceService
from app.core.evidence.storage import LocalEvidenceStorage
from app.core.audit_ledger.ledger import AuditLedger
from app.models.evidence import EvidenceObject
from app.models.evidence_link import EvidenceLink
from app.shared.exceptions import NotFoundError


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage(temp_storage_dir):
    """Create local storage instance"""
    return LocalEvidenceStorage(base_path=temp_storage_dir)


@pytest.fixture
def evidence_service(db_session, storage):
    """Create evidence service instance"""
    audit = AuditLedger(db_session)
    return EvidenceService(db=db_session, storage=storage, audit=audit)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return b"This is test evidence content for risk assessment."


class TestEvidenceService:
    """Tests for EvidenceService"""
    
    def test_create_evidence_creates_record_with_correct_hash(
        self, evidence_service, tenant_id, sample_content
    ):
        """Test that create_evidence creates record with correct hash"""
        evidence = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain",
            filename="test.txt",
            evidence_type="DOCUMENT"
        )
        
        # Verify hash
        expected_hash = hashlib.sha256(sample_content).hexdigest()
        assert evidence.content_hash == expected_hash
        assert evidence.content_type == "text/plain"
        assert evidence.filename == "test.txt"
        assert evidence.evidence_type == "DOCUMENT"
        assert evidence.content_size_bytes == len(sample_content)
        assert evidence.storage_uri is not None
        assert evidence.storage_provider == "local"
    
    def test_create_evidence_deduplicates_by_hash(
        self, evidence_service, tenant_id, sample_content
    ):
        """Test that duplicate content returns existing evidence"""
        # Create first evidence
        evidence1 = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain",
            filename="test1.txt"
        )
        
        # Create second evidence with same content (different filename)
        evidence2 = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain",
            filename="test2.txt"  # Different filename
        )
        
        # Should return same evidence (deduplication)
        assert evidence1.id == evidence2.id
        assert evidence1.content_hash == evidence2.content_hash
        
        # Verify only one record in database
        count = evidence_service.db.query(EvidenceObject).filter(
            EvidenceObject.content_hash == evidence1.content_hash
        ).count()
        assert count == 1
    
    def test_link_evidence_creates_link(
        self, evidence_service, tenant_id, sample_content
    ):
        """Test that link_evidence creates link"""
        # Create evidence
        evidence = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain"
        )
        
        # Link to entity
        link = evidence_service.link_evidence(
            tenant_id=tenant_id,
            evidence_id=evidence.id,
            entity_type="risk_assessment",
            entity_id="assessment-123",
            link_type="ATTACHMENT"
        )
        
        assert link.evidence_id == evidence.id
        assert link.entity_type == "risk_assessment"
        assert link.entity_id == "assessment-123"
        assert link.link_type == "ATTACHMENT"
    
    def test_link_evidence_prevents_duplicate_links(
        self, evidence_service, tenant_id, sample_content
    ):
        """Test that duplicate links are prevented by unique constraint"""
        # Create evidence
        evidence = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain"
        )
        
        # Create first link
        link1 = evidence_service.link_evidence(
            tenant_id=tenant_id,
            evidence_id=evidence.id,
            entity_type="risk_assessment",
            entity_id="assessment-123",
            link_type="ATTACHMENT"
        )
        
        # Try to create duplicate link (should raise IntegrityError)
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            evidence_service.link_evidence(
                tenant_id=tenant_id,
                evidence_id=evidence.id,
                entity_type="risk_assessment",
                entity_id="assessment-123",
                link_type="ATTACHMENT"
            )
    
    def test_get_evidence_for_entity_returns_linked_evidence(
        self, evidence_service, tenant_id, sample_content
    ):
        """Test that get_evidence_for_entity returns linked evidence"""
        # Create evidence
        evidence = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain"
        )
        
        # Link to entity
        evidence_service.link_evidence(
            tenant_id=tenant_id,
            evidence_id=evidence.id,
            entity_type="risk_assessment",
            entity_id="assessment-123"
        )
        
        # Get evidence for entity
        linked_evidence = evidence_service.get_evidence_for_entity(
            tenant_id=tenant_id,
            entity_type="risk_assessment",
            entity_id="assessment-123"
        )
        
        assert len(linked_evidence) == 1
        assert linked_evidence[0].id == evidence.id
    
    def test_download_evidence_returns_content(
        self, evidence_service, tenant_id, sample_content
    ):
        """Test that download_evidence returns content"""
        # Create evidence
        evidence = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain"
        )
        
        # Download evidence
        content, content_type = evidence_service.download_evidence(
            tenant_id=tenant_id,
            evidence_id=evidence.id
        )
        
        assert content == sample_content
        assert content_type == "text/plain"
    
    def test_download_evidence_raises_not_found(
        self, evidence_service, tenant_id
    ):
        """Test that download_evidence raises NotFoundError for non-existent evidence"""
        with pytest.raises(NotFoundError):
            evidence_service.download_evidence(
                tenant_id=tenant_id,
                evidence_id="non-existent-id"
            )
    
    def test_create_evidence_emits_audit_event(
        self, evidence_service, tenant_id, sample_content
    ):
        """Test that create_evidence emits audit event"""
        evidence = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain",
            created_by_user_id="user-123"
        )
        
        # Check audit event - query directly from database
        from app.models.audit import AuditEvent
        events = evidence_service.db.query(AuditEvent).filter(
            AuditEvent.tenant_id == tenant_id,
            AuditEvent.entity_type == "evidence_object",
            AuditEvent.entity_id == evidence.id
        ).order_by(AuditEvent.created_at.desc()).all()
        
        assert len(events) >= 1
        created_event = events[0]
        assert created_event.action == "CREATED"
        assert created_event.event_type == "EVIDENCE"
        assert created_event.entity_id == evidence.id
    
    def test_link_evidence_emits_audit_event(
        self, evidence_service, tenant_id, sample_content
    ):
        """Test that link_evidence emits audit event"""
        # Create evidence
        evidence = evidence_service.create_evidence(
            tenant_id=tenant_id,
            content=sample_content,
            content_type="text/plain"
        )
        
        # Link to entity
        link = evidence_service.link_evidence(
            tenant_id=tenant_id,
            evidence_id=evidence.id,
            entity_type="risk_assessment",
            entity_id="assessment-123",
            created_by_user_id="user-123"
        )
        
        # Check audit event - query directly from database
        from app.models.audit import AuditEvent
        events = evidence_service.db.query(AuditEvent).filter(
            AuditEvent.tenant_id == tenant_id,
            AuditEvent.entity_type == "risk_assessment",
            AuditEvent.entity_id == "assessment-123"
        ).order_by(AuditEvent.created_at.desc()).all()
        
        assert len(events) >= 1
        link_event = next((e for e in events if e.action == "CREATED" and e.event_type == "EVIDENCE_LINK"), None)
        assert link_event is not None
        assert link_event.payload_json.get("evidence_id") == evidence.id


class TestEvidenceStorage:
    """Tests for storage implementations"""
    
    def test_local_storage_upload_download(
        self, temp_storage_dir
    ):
        """Test local storage upload and download"""
        storage = LocalEvidenceStorage(base_path=temp_storage_dir)
        content = b"test content"
        
        # Upload
        uri = storage.upload(content, "test/file.txt")
        
        assert uri.startswith("file://")
        assert storage.exists(uri)
        
        # Download
        downloaded = storage.download(uri)
        assert downloaded == content
    
    def test_local_storage_delete(
        self, temp_storage_dir
    ):
        """Test local storage delete"""
        storage = LocalEvidenceStorage(base_path=temp_storage_dir)
        content = b"test content"
        
        # Upload
        uri = storage.upload(content, "test/file.txt")
        assert storage.exists(uri)
        
        # Delete
        result = storage.delete(uri)
        assert result is True
        assert not storage.exists(uri)
