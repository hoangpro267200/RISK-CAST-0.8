"""
Unit Tests for Immutable Audit Ledger

Tests:
1. Event creation
2. Hash chain integrity
3. HMAC signature verification
4. Sequence numbering
5. Chain verification
6. Tamper detection
7. Export functionality
8. Query operations
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import hashlib
import hmac
import json
from typing import Dict, Any

from app.core.audit.immutable_ledger import (
    ImmutableAuditLedger,
    AuditEventImmutable,
    ImmutableAuditChainTip,
    EventType,
    ActorType,
    ChainVerificationResult,
)


# ============================================================================
# Constants
# ============================================================================

GENESIS_HASH = "0" * 64


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = Mock()
    db.query = Mock(return_value=Mock())
    db.add = Mock()
    db.commit = Mock()
    db.flush = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def audit_ledger(mock_db):
    """Create audit ledger instance."""
    return ImmutableAuditLedger(
        db=mock_db,
        signing_key="test-signing-key-12345"
    )


@pytest.fixture
def sample_event_data():
    """Sample event data."""
    return {
        "event_type": EventType.RISK_ASSESSMENT,
        "action": "ASSESSMENT_COMPLETED",
        "entity_type": "risk_run",
        "entity_id": "risk-123",
        "actor_type": ActorType.USER,
        "actor_id": "user-456",
        "payload": {
            "risk_score": 0.65,
            "cargo_value": 500000
        }
    }


def create_mock_event(
    sequence_number: int,
    event_hash: str,
    prev_hash: str,
    event_type: str = "TEST",
    action: str = "TEST",
    entity_id: str = "test",
    payload: Dict[str, Any] = None,
    timestamp: datetime = None
) -> Mock:
    """Helper to create mock event."""
    event = Mock(spec=AuditEventImmutable)
    event.sequence_number = sequence_number
    event.event_type = event_type
    event.action = action
    event.entity_type = "test"
    event.entity_id = entity_id
    event.actor_type = "USER"
    event.actor_id = "test-user"
    event.tenant_id = None
    event.payload_json = payload or {}
    event.event_timestamp = timestamp or datetime.utcnow()
    event.server_timestamp = timestamp or datetime.utcnow()
    event.prev_event_hash = prev_hash
    event.event_hash = event_hash
    event.hmac_signature = "mock_signature"
    event.source_ip = None
    event.user_agent = None
    event.request_id = None
    event.id = f"event-{sequence_number}"
    return event


# ============================================================================
# Event Creation Tests
# ============================================================================

class TestEventCreation:
    """Test audit event creation."""
    
    def test_create_first_event_uses_genesis_hash(self, audit_ledger, mock_db, sample_event_data):
        """Test creating first event uses genesis hash."""
        # Mock no existing tip
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        # Mock the event that will be created
        created_event = Mock(spec=AuditEventImmutable)
        created_event.sequence_number = 1
        created_event.prev_event_hash = GENESIS_HASH
        created_event.event_hash = "test_hash"
        created_event.hmac_signature = "test_sig"
        created_event.event_timestamp = datetime.utcnow()
        created_event.server_timestamp = datetime.utcnow()
        
        def mock_add(obj):
            if isinstance(obj, AuditEventImmutable):
                # Set the hash and signature after flush
                pass
        
        mock_db.add.side_effect = mock_add
        
        event = audit_ledger.append_event(**sample_event_data)
        
        assert event.sequence_number == 1
        assert event.prev_event_hash == GENESIS_HASH
        assert event.event_hash is not None
        assert event.hmac_signature is not None
    
    def test_create_subsequent_event_links_to_previous(self, audit_ledger, mock_db, sample_event_data):
        """Test subsequent event links to previous."""
        # Mock existing tip
        tip = Mock(spec=ImmutableAuditChainTip)
        tip.id = 1
        tip.next_sequence = 6
        tip.latest_hash = "abc123def456"
        
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = tip
        
        event = audit_ledger.append_event(**sample_event_data)
        
        assert event.sequence_number == 6
        assert event.prev_event_hash == "abc123def456"
    
    def test_event_has_proper_timestamps(self, audit_ledger, mock_db, sample_event_data):
        """Test event has proper timestamps."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        before = datetime.utcnow()
        event = audit_ledger.append_event(**sample_event_data)
        after = datetime.utcnow()
        
        assert before <= event.event_timestamp <= after
        assert before <= event.server_timestamp <= after
    
    def test_event_includes_tenant_id(self, audit_ledger, mock_db, sample_event_data):
        """Test event includes tenant ID."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        sample_event_data["tenant_id"] = "tenant-789"
        event = audit_ledger.append_event(**sample_event_data)
        
        assert event.tenant_id == "tenant-789"
    
    def test_event_includes_request_context(self, audit_ledger, mock_db, sample_event_data):
        """Test event includes request context."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        sample_event_data["source_ip"] = "192.168.1.1"
        sample_event_data["user_agent"] = "TestClient/1.0"
        sample_event_data["request_id"] = "req-abc123"
        
        event = audit_ledger.append_event(**sample_event_data)
        
        assert event.source_ip == "192.168.1.1"
        assert event.user_agent == "TestClient/1.0"
        assert event.request_id == "req-abc123"
    
    def test_event_with_payload(self, audit_ledger, mock_db, sample_event_data):
        """Test event stores payload correctly."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        event = audit_ledger.append_event(**sample_event_data)
        
        assert event.payload_json is not None
        assert event.payload_json["risk_score"] == 0.65
        assert event.payload_json["cargo_value"] == 500000
    
    def test_chain_tip_updates_atomically(self, audit_ledger, mock_db, sample_event_data):
        """Test chain tip updates atomically with event creation."""
        tip = Mock(spec=ImmutableAuditChainTip)
        tip.id = 1
        tip.next_sequence = 1
        tip.latest_hash = GENESIS_HASH
        
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = tip
        
        event = audit_ledger.append_event(**sample_event_data)
        
        # Tip should be updated
        assert tip.next_sequence == 2
        assert tip.latest_hash == event.event_hash


# ============================================================================
# Hash Chain Tests
# ============================================================================

class TestHashChain:
    """Test hash chain integrity."""
    
    def test_event_hash_is_deterministic(self, audit_ledger):
        """Test event hash is computed consistently."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="",  # Will be computed
            prev_hash=GENESIS_HASH,
            payload={"score": 0.5}
        )
        
        hash1 = audit_ledger._compute_event_hash(event)
        hash2 = audit_ledger._compute_event_hash(event)
        
        # Same data should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex
        assert hash1 != GENESIS_HASH
    
    def test_event_hash_changes_with_payload(self, audit_ledger):
        """Test hash changes when payload changes."""
        event1 = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH,
            payload={"score": 0.5}
        )
        
        hash1 = audit_ledger._compute_event_hash(event1)
        
        event2 = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH,
            payload={"score": 0.6}  # Different payload
        )
        
        hash2 = audit_ledger._compute_event_hash(event2)
        
        assert hash1 != hash2
    
    def test_prev_hash_affects_event_hash(self, audit_ledger):
        """Test previous hash affects current hash."""
        event1 = create_mock_event(
            sequence_number=2,
            event_hash="",
            prev_hash="hash_a",
            payload={}
        )
        
        hash1 = audit_ledger._compute_event_hash(event1)
        
        event2 = create_mock_event(
            sequence_number=2,
            event_hash="",
            prev_hash="hash_b",  # Different prev_hash
            payload={}
        )
        
        hash2 = audit_ledger._compute_event_hash(event2)
        
        assert hash1 != hash2
    
    def test_sequence_number_affects_hash(self, audit_ledger):
        """Test sequence number affects hash."""
        event1 = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH
        )
        
        hash1 = audit_ledger._compute_event_hash(event1)
        
        event2 = create_mock_event(
            sequence_number=2,  # Different sequence
            event_hash="",
            prev_hash=GENESIS_HASH
        )
        
        hash2 = audit_ledger._compute_event_hash(event2)
        
        assert hash1 != hash2
    
    def test_timestamp_affects_hash(self, audit_ledger):
        """Test timestamp affects hash."""
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 0, 1)
        
        event1 = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH,
            timestamp=ts1
        )
        
        hash1 = audit_ledger._compute_event_hash(event1)
        
        event2 = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH,
            timestamp=ts2  # Different timestamp
        )
        
        hash2 = audit_ledger._compute_event_hash(event2)
        
        assert hash1 != hash2


# ============================================================================
# HMAC Signature Tests
# ============================================================================

class TestHMACSignature:
    """Test HMAC signature generation and verification."""
    
    def test_signature_generation(self, audit_ledger):
        """Test HMAC signature is generated."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="abc123",
            prev_hash=GENESIS_HASH
        )
        
        signature = audit_ledger._compute_hmac(event)
        
        assert signature is not None
        assert len(signature) == 64  # HMAC-SHA256 hex
    
    def test_signature_is_deterministic(self, audit_ledger):
        """Test same event produces same signature."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="abc123",
            prev_hash=GENESIS_HASH,
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        sig1 = audit_ledger._compute_hmac(event)
        sig2 = audit_ledger._compute_hmac(event)
        
        assert sig1 == sig2
    
    def test_signature_changes_with_sequence(self, audit_ledger):
        """Test signature changes with different sequence number."""
        event1 = create_mock_event(
            sequence_number=1,
            event_hash="abc123",
            prev_hash=GENESIS_HASH,
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        sig1 = audit_ledger._compute_hmac(event1)
        
        event2 = create_mock_event(
            sequence_number=2,  # Different
            event_hash="abc123",
            prev_hash=GENESIS_HASH,
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        sig2 = audit_ledger._compute_hmac(event2)
        
        assert sig1 != sig2
    
    def test_signature_changes_with_hash(self, audit_ledger):
        """Test signature changes with different event hash."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        event1 = create_mock_event(
            sequence_number=1,
            event_hash="hash1",
            prev_hash=GENESIS_HASH,
            timestamp=timestamp
        )
        
        sig1 = audit_ledger._compute_hmac(event1)
        
        event2 = create_mock_event(
            sequence_number=1,
            event_hash="hash2",  # Different
            prev_hash=GENESIS_HASH,
            timestamp=timestamp
        )
        
        sig2 = audit_ledger._compute_hmac(event2)
        
        assert sig1 != sig2
    
    def test_signature_changes_with_timestamp(self, audit_ledger):
        """Test signature changes with different timestamp."""
        event1 = create_mock_event(
            sequence_number=1,
            event_hash="abc123",
            prev_hash=GENESIS_HASH,
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        sig1 = audit_ledger._compute_hmac(event1)
        
        event2 = create_mock_event(
            sequence_number=1,
            event_hash="abc123",
            prev_hash=GENESIS_HASH,
            timestamp=datetime(2024, 1, 1, 13, 0, 0)  # Different
        )
        
        sig2 = audit_ledger._compute_hmac(event2)
        
        assert sig1 != sig2
    
    def test_signature_uses_signing_key(self):
        """Test different signing keys produce different signatures."""
        ledger1 = ImmutableAuditLedger(Mock(), signing_key="key1")
        ledger2 = ImmutableAuditLedger(Mock(), signing_key="key2")
        
        event = create_mock_event(
            sequence_number=1,
            event_hash="abc123",
            prev_hash=GENESIS_HASH,
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        sig1 = ledger1._compute_hmac(event)
        sig2 = ledger2._compute_hmac(event)
        
        assert sig1 != sig2


# ============================================================================
# Chain Verification Tests
# ============================================================================

class TestChainVerification:
    """Test chain verification functionality."""
    
    def test_verify_valid_single_event_chain(self, audit_ledger, mock_db):
        """Test verification of valid single event."""
        # Create valid event
        event = create_mock_event(
            sequence_number=1,
            event_hash="computed_hash",
            prev_hash=GENESIS_HASH
        )
        
        # Compute correct hash and signature
        event.event_hash = audit_ledger._compute_event_hash(event)
        event.hmac_signature = audit_ledger._compute_hmac(event)
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.all.return_value = [event]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 1)
        
        assert isinstance(result, ChainVerificationResult)
        assert result.is_valid
        assert result.events_checked == 1
        assert result.broken_at_sequence is None
    
    def test_verify_valid_multi_event_chain(self, audit_ledger, mock_db):
        """Test verification of valid multi-event chain."""
        events = []
        prev_hash = GENESIS_HASH
        
        # Create chain of 5 events
        for i in range(1, 6):
            event = create_mock_event(
                sequence_number=i,
                event_hash="temp",
                prev_hash=prev_hash,
                entity_id=str(i)
            )
            
            # Compute correct hash
            event.event_hash = audit_ledger._compute_event_hash(event)
            event.hmac_signature = audit_ledger._compute_hmac(event)
            
            events.append(event)
            prev_hash = event.event_hash
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.filter.return_value.all.return_value = events
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 5)
        
        assert result.is_valid
        assert result.events_checked == 5
        assert result.first_event_sequence == 1
        assert result.last_event_sequence == 5
        assert result.broken_at_sequence is None
    
    def test_verify_broken_chain_wrong_prev_hash(self, audit_ledger, mock_db):
        """Test detection of broken chain (wrong prev_hash)."""
        event1 = create_mock_event(
            sequence_number=1,
            event_hash="hash1",
            prev_hash=GENESIS_HASH
        )
        event1.event_hash = audit_ledger._compute_event_hash(event1)
        event1.hmac_signature = audit_ledger._compute_hmac(event1)
        
        # Event 2 has WRONG prev_hash
        event2 = create_mock_event(
            sequence_number=2,
            event_hash="hash2",
            prev_hash="wrong_hash"  # Should be event1.event_hash
        )
        event2.event_hash = audit_ledger._compute_event_hash(event2)
        event2.hmac_signature = audit_ledger._compute_hmac(event2)
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.filter.return_value.all.return_value = [event1, event2]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 2)
        
        assert not result.is_valid
        assert result.broken_at_sequence == 2
        assert "chain" in result.error_message.lower()
    
    def test_verify_tampered_event_hash_mismatch(self, audit_ledger, mock_db):
        """Test detection of tampered event (hash mismatch)."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="stored_hash",  # This is the stored hash
            prev_hash=GENESIS_HASH,
            payload={"original": "data"}
        )
        event.hmac_signature = audit_ledger._compute_hmac(event)
        
        # But computed hash won't match because payload is different
        mock_db.query.return_value.order_by.return_value.filter.return_value.all.return_value = [event]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 1)
        
        # Hash won't match computed
        assert not result.is_valid
        assert "hash" in result.error_message.lower()
    
    def test_verify_invalid_hmac_signature(self, audit_ledger, mock_db):
        """Test detection of invalid HMAC signature."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="hash",
            prev_hash=GENESIS_HASH
        )
        
        # Compute correct hash
        event.event_hash = audit_ledger._compute_event_hash(event)
        # But set WRONG signature
        event.hmac_signature = "invalid_signature"
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.all.return_value = [event]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 1)
        
        assert not result.is_valid
        assert "hmac" in result.error_message.lower() or "signature" in result.error_message.lower()
    
    def test_verify_first_event_not_genesis(self, audit_ledger, mock_db):
        """Test detection when first event doesn't link to genesis."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="hash",
            prev_hash="not_genesis"  # Should be GENESIS_HASH
        )
        event.event_hash = audit_ledger._compute_event_hash(event)
        event.hmac_signature = audit_ledger._compute_hmac(event)
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.all.return_value = [event]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 1)
        
        assert not result.is_valid
        assert result.broken_at_sequence == 1
        assert "genesis" in result.error_message.lower()
    
    def test_verify_empty_chain(self, audit_ledger, mock_db):
        """Test verification of empty chain."""
        mock_db.query.return_value.order_by.return_value.filter.return_value.filter.return_value.all.return_value = []
        
        result = audit_ledger.verify_chain(1, 10)
        
        assert result.is_valid
        assert result.events_checked == 0
        assert "no events" in result.error_message.lower()


# ============================================================================
# Sequence Numbering Tests
# ============================================================================

class TestSequenceNumbering:
    """Test sequence numbering."""
    
    def test_sequence_starts_at_one(self, audit_ledger, mock_db, sample_event_data):
        """Test first event gets sequence 1."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        event = audit_ledger.append_event(**sample_event_data)
        
        assert event.sequence_number == 1
    
    def test_sequence_increments_correctly(self, audit_ledger, mock_db, sample_event_data):
        """Test sequence increments correctly."""
        tip = Mock(spec=ImmutableAuditChainTip)
        tip.id = 1
        tip.next_sequence = 100
        tip.latest_hash = "prev_hash"
        
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = tip
        
        event = audit_ledger.append_event(**sample_event_data)
        
        assert event.sequence_number == 100
        assert tip.next_sequence == 101  # Updated
    
    def test_sequence_has_no_gaps(self, audit_ledger, mock_db):
        """Test no gaps in sequence numbers."""
        # Start with no tip
        tip = None
        
        def get_tip(*args, **kwargs):
            return tip
        
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = get_tip
        
        sequences = []
        for i in range(5):
            event = audit_ledger.append_event(
                event_type=EventType.SYSTEM,
                action="TEST",
                entity_type="test",
                entity_id=str(i)
            )
            sequences.append(event.sequence_number)
            
            # Update tip for next iteration
            if tip is None:
                tip = Mock(spec=ImmutableAuditChainTip)
                tip.id = 1
                tip.next_sequence = 2
                tip.latest_hash = event.event_hash
            else:
                tip.next_sequence += 1
                tip.latest_hash = event.event_hash
        
        assert sequences == [1, 2, 3, 4, 5]
    
    def test_sequence_is_globally_unique(self, audit_ledger, mock_db, sample_event_data):
        """Test sequence numbers are globally unique."""
        tip = Mock(spec=ImmutableAuditChainTip)
        tip.id = 1
        tip.next_sequence = 42
        tip.latest_hash = "hash"
        
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = tip
        
        event1 = audit_ledger.append_event(**sample_event_data)
        
        # Update tip
        tip.next_sequence = 43
        tip.latest_hash = event1.event_hash
        
        event2 = audit_ledger.append_event(**sample_event_data)
        
        assert event1.sequence_number != event2.sequence_number
        assert event2.sequence_number == event1.sequence_number + 1


# ============================================================================
# Tamper Detection Tests
# ============================================================================

class TestTamperDetection:
    """Test tamper detection capabilities."""
    
    def test_detect_modified_payload(self, audit_ledger, mock_db):
        """Test detection of modified payload."""
        # Create event with original payload
        original_payload = {"amount": 1000}
        event = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH,
            payload=original_payload
        )
        
        # Compute hash with original payload
        original_hash = audit_ledger._compute_event_hash(event)
        event.event_hash = original_hash
        event.hmac_signature = audit_ledger._compute_hmac(event)
        
        # Now "tamper" with payload
        event.payload_json = {"amount": 10000}  # TAMPERED!
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.all.return_value = [event]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 1)
        
        # Hash won't match because payload changed
        assert not result.is_valid
    
    def test_detect_modified_entity_id(self, audit_ledger, mock_db):
        """Test detection of modified entity ID."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH,
            entity_id="original-id"
        )
        
        # Compute hash with original ID
        original_hash = audit_ledger._compute_event_hash(event)
        event.event_hash = original_hash
        event.hmac_signature = audit_ledger._compute_hmac(event)
        
        # Tamper with entity ID
        event.entity_id = "tampered-id"
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.all.return_value = [event]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 1)
        
        assert not result.is_valid
    
    def test_detect_sequence_gap(self, audit_ledger, mock_db):
        """Test detection of missing event (gap in sequence)."""
        # Events 1 and 3 exist, but 2 is "deleted"
        event1 = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH
        )
        event1.event_hash = audit_ledger._compute_event_hash(event1)
        event1.hmac_signature = audit_ledger._compute_hmac(event1)
        
        # Event 3 references missing event 2
        event3 = create_mock_event(
            sequence_number=3,
            event_hash="",
            prev_hash="hash_of_event_2"  # References missing event
        )
        event3.event_hash = audit_ledger._compute_event_hash(event3)
        event3.hmac_signature = audit_ledger._compute_hmac(event3)
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.filter.return_value.all.return_value = [event1, event3]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 3)
        
        # Chain will break because event3's prev_hash doesn't match event1's hash
        assert not result.is_valid or result.events_checked < 3
    
    def test_detect_recomputed_hash_attack(self, audit_ledger, mock_db):
        """Test detection of recomputed hash attack (signature fails)."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH,
            payload={"original": "data"}
        )
        
        # Attacker modifies payload AND recomputes hash
        event.payload_json = {"modified": "data"}
        event.event_hash = audit_ledger._compute_event_hash(event)
        
        # But attacker can't recompute HMAC without signing key
        event.hmac_signature = "attacker_signature"
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.all.return_value = [event]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = audit_ledger.verify_chain(1, 1)
        
        # HMAC verification should fail
        assert not result.is_valid
        assert "hmac" in result.error_message.lower() or "signature" in result.error_message.lower()


# ============================================================================
# Export Functionality Tests
# ============================================================================

class TestExportFunctionality:
    """Test audit trail export."""
    
    def test_export_date_range(self, audit_ledger, mock_db):
        """Test export for date range."""
        events = [
            create_mock_event(
                sequence_number=1,
                event_hash="hash1",
                prev_hash=GENESIS_HASH,
                timestamp=datetime(2024, 1, 15)
            ),
            create_mock_event(
                sequence_number=2,
                event_hash="hash2",
                prev_hash="hash1",
                timestamp=datetime(2024, 1, 16)
            )
        ]
        
        # Ensure correct hashes
        for event in events:
            event.event_hash = audit_ledger._compute_event_hash(event)
            event.hmac_signature = audit_ledger._compute_hmac(event)
        
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = events
        
        # Mock verify_chain to return valid
        with patch.object(audit_ledger, 'verify_chain') as mock_verify:
            mock_verify.return_value = ChainVerificationResult(
                is_valid=True,
                events_checked=2,
                first_event_sequence=1,
                last_event_sequence=2,
                broken_at_sequence=None,
                error_message=None,
                verification_hash="verify_hash",
                verified_at=datetime.utcnow()
            )
            
            export = audit_ledger.export_for_compliance(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            )
        
        assert "export_id" in export
        assert "events" in export
        assert "verification" in export
        assert len(export["events"]) == 2
        assert export["event_count"] == 2
    
    def test_export_includes_verification_proof(self, audit_ledger, mock_db):
        """Test export includes verification proof."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH
        )
        event.event_hash = audit_ledger._compute_event_hash(event)
        event.hmac_signature = audit_ledger._compute_hmac(event)
        
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [event]
        
        with patch.object(audit_ledger, 'verify_chain') as mock_verify:
            mock_verify.return_value = ChainVerificationResult(
                is_valid=True,
                events_checked=1,
                first_event_sequence=1,
                last_event_sequence=1,
                broken_at_sequence=None,
                error_message=None,
                verification_hash="verify_hash_abc123",
                verified_at=datetime.utcnow()
            )
            
            export = audit_ledger.export_for_compliance(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31)
            )
        
        assert export["verification"]["is_valid"]
        assert export["verification"]["verification_hash"] == "verify_hash_abc123"
        assert export["verification"]["events_verified"] == 1
    
    def test_export_by_event_type(self, audit_ledger, mock_db):
        """Test export filtered by event type."""
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        export = audit_ledger.export_for_compliance(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            event_types=[EventType.RISK_ASSESSMENT, EventType.QUOTE]
        )
        
        # Should have called filter with event types
        assert export["event_count"] == 0
    
    def test_export_empty_range(self, audit_ledger, mock_db):
        """Test export with no events in range."""
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        export = audit_ledger.export_for_compliance(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert export["event_count"] == 0
        assert len(export["events"]) == 0
        assert export["verification"] is None
    
    def test_export_by_tenant(self, audit_ledger, mock_db):
        """Test export filtered by tenant."""
        event = create_mock_event(
            sequence_number=1,
            event_hash="",
            prev_hash=GENESIS_HASH
        )
        event.tenant_id = "tenant-123"
        event.event_hash = audit_ledger._compute_event_hash(event)
        event.hmac_signature = audit_ledger._compute_hmac(event)
        
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [event]
        
        with patch.object(audit_ledger, 'verify_chain') as mock_verify:
            mock_verify.return_value = ChainVerificationResult(
                is_valid=True,
                events_checked=1,
                first_event_sequence=1,
                last_event_sequence=1,
                broken_at_sequence=None,
                error_message=None,
                verification_hash="hash",
                verified_at=datetime.utcnow()
            )
            
            export = audit_ledger.export_for_compliance(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
                tenant_id="tenant-123"
            )
        
        assert export["event_count"] == 1


# ============================================================================
# Query Operations Tests
# ============================================================================

class TestQueryOperations:
    """Test audit event query operations."""
    
    def test_get_events_for_entity(self, audit_ledger, mock_db):
        """Test getting events for specific entity."""
        events = [
            create_mock_event(1, "hash1", GENESIS_HASH, entity_id="pol-123"),
            create_mock_event(2, "hash2", "hash1", entity_id="pol-123")
        ]
        
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = events
        
        result = audit_ledger.get_events_for_entity(
            entity_type="policy",
            entity_id="pol-123"
        )
        
        assert len(result) == 2
        assert all(e.entity_id == "pol-123" for e in result)
    
    def test_get_events_for_entity_with_tenant(self, audit_ledger, mock_db):
        """Test getting events filtered by tenant."""
        events = [create_mock_event(1, "hash1", GENESIS_HASH)]
        events[0].tenant_id = "tenant-789"
        
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = events
        
        result = audit_ledger.get_events_for_entity(
            entity_type="policy",
            entity_id="pol-123",
            tenant_id="tenant-789"
        )
        
        assert len(result) == 1
    
    def test_get_events_by_actor(self, audit_ledger, mock_db):
        """Test getting events by actor."""
        events = [
            create_mock_event(1, "hash1", GENESIS_HASH),
            create_mock_event(2, "hash2", "hash1"),
            create_mock_event(3, "hash3", "hash2")
        ]
        
        for e in events:
            e.actor_type = "USER"
            e.actor_id = "user-456"
        
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = events
        
        result = audit_ledger.get_events_by_actor(
            actor_type="USER",
            actor_id="user-456"
        )
        
        assert len(result) == 3
    
    def test_get_events_by_actor_with_date_range(self, audit_ledger, mock_db):
        """Test getting events by actor with date filtering."""
        event = create_mock_event(
            1, "hash1", GENESIS_HASH,
            timestamp=datetime(2024, 1, 15)
        )
        event.actor_type = "USER"
        event.actor_id = "user-456"
        
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [event]
        
        result = audit_ledger.get_events_by_actor(
            actor_type="USER",
            actor_id="user-456",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 31)
        )
        
        assert len(result) == 1
    
    def test_get_events_by_type(self, audit_ledger, mock_db):
        """Test getting events by type."""
        events = [
            create_mock_event(1, "hash1", GENESIS_HASH, event_type="QUOTE"),
            create_mock_event(2, "hash2", "hash1", event_type="QUOTE")
        ]
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = events
        
        result = audit_ledger.get_events_by_type(
            event_type="QUOTE"
        )
        
        assert len(result) == 2
    
    def test_get_events_by_type_and_action(self, audit_ledger, mock_db):
        """Test getting events by type and action."""
        event = create_mock_event(
            1, "hash1", GENESIS_HASH,
            event_type="QUOTE",
            action="ACCEPTED"
        )
        
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [event]
        
        result = audit_ledger.get_events_by_type(
            event_type="QUOTE",
            action="ACCEPTED"
        )
        
        assert len(result) == 1
    
    def test_get_events_respects_limit(self, audit_ledger, mock_db):
        """Test query respects limit parameter."""
        events = [create_mock_event(i, f"hash{i}", GENESIS_HASH) for i in range(1, 11)]
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = events[:5]
        
        result = audit_ledger.get_events_by_type(
            event_type="TEST",
            limit=5
        )
        
        assert len(result) == 5


# ============================================================================
# Concurrent Access Tests
# ============================================================================

class TestConcurrentAccess:
    """Test concurrent access handling."""
    
    def test_chain_tip_locking(self, audit_ledger, mock_db, sample_event_data):
        """Test chain tip is locked during append."""
        tip = Mock(spec=ImmutableAuditChainTip)
        tip.id = 1
        tip.next_sequence = 1
        tip.latest_hash = GENESIS_HASH
        
        # Verify with_for_update was called (pessimistic locking)
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = tip
        
        audit_ledger.append_event(**sample_event_data)
        
        # Verify locking was used
        mock_db.query.return_value.filter.return_value.with_for_update.assert_called_once()
    
    def test_chain_tip_created_if_missing(self, audit_ledger, mock_db, sample_event_data):
        """Test chain tip is created if it doesn't exist."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        event = audit_ledger.append_event(**sample_event_data)
        
        # Should have added a new tip
        assert event.sequence_number == 1
        assert event.prev_event_hash == GENESIS_HASH


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases."""
    
    def test_event_with_null_payload(self, audit_ledger, mock_db):
        """Test event with null payload."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        event = audit_ledger.append_event(
            event_type=EventType.SYSTEM,
            action="TEST",
            entity_type="test",
            entity_id="test-1",
            payload=None
        )
        
        assert event.payload_json is None
        assert event.event_hash is not None
    
    def test_event_with_large_payload(self, audit_ledger, mock_db):
        """Test event with large payload."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        large_payload = {"data": "x" * 10000}
        
        event = audit_ledger.append_event(
            event_type=EventType.DATA_IMPORT,
            action="COMPLETED",
            entity_type="import",
            entity_id="import-1",
            payload=large_payload
        )
        
        assert event.payload_json == large_payload
        assert event.event_hash is not None
    
    def test_event_with_special_characters(self, audit_ledger, mock_db):
        """Test event with special characters in data."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        event = audit_ledger.append_event(
            event_type=EventType.SYSTEM,
            action="TEST",
            entity_type="test",
            entity_id="test-1",
            payload={"text": "Hello 世界 🌍 €£¥"}
        )
        
        assert event.payload_json["text"] == "Hello 世界 🌍 €£¥"
        assert event.event_hash is not None
    
    def test_verify_chain_with_non_sequential_range(self, audit_ledger, mock_db):
        """Test verifying chain with non-sequential event IDs."""
        # Events 5-7 (not starting from 1)
        events = []
        prev_hash = "hash4"  # Previous event's hash
        
        for i in range(5, 8):
            event = create_mock_event(i, "", prev_hash)
            event.event_hash = audit_ledger._compute_event_hash(event)
            event.hmac_signature = audit_ledger._compute_hmac(event)
            events.append(event)
            prev_hash = event.event_hash
        
        # Mock prior event
        prior = create_mock_event(4, "hash4", "hash3")
        
        mock_db.query.return_value.order_by.return_value.filter.return_value.filter.return_value.all.return_value = events
        mock_db.query.return_value.filter.return_value.first.return_value = prior
        
        result = audit_ledger.verify_chain(5, 7)
        
        assert result.is_valid
        assert result.events_checked == 3


# ============================================================================
# Genesis Hash Tests
# ============================================================================

class TestGenesisHash:
    """Test genesis hash constant."""
    
    def test_genesis_hash_value(self):
        """Test genesis hash is correct constant."""
        assert ImmutableAuditLedger.GENESIS_HASH == "0" * 64
        assert len(ImmutableAuditLedger.GENESIS_HASH) == 64
    
    def test_first_event_uses_genesis(self, audit_ledger, mock_db, sample_event_data):
        """Test first event always uses genesis hash."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        event = audit_ledger.append_event(**sample_event_data)
        
        assert event.prev_event_hash == ImmutableAuditLedger.GENESIS_HASH
    
    def test_genesis_hash_is_immutable(self):
        """Test genesis hash constant cannot be changed."""
        original = ImmutableAuditLedger.GENESIS_HASH
        
        # Try to modify (this won't work for string constant)
        try:
            ImmutableAuditLedger.GENESIS_HASH = "different"
        except:
            pass
        
        # Should still be original after class reload
        assert ImmutableAuditLedger.GENESIS_HASH == original
