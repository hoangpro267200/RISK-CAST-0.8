"""
Unit Tests for Audit Ledger Core
Tests for hash-chained audit ledger with concurrent safety
"""
import pytest
import threading
import time
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.audit_ledger.ledger import AuditLedger, compute_event_hash, ChainVerificationResult
from app.models.audit import AuditEvent, AuditChainHead
from app.shared.utils import generate_ulid


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return generate_ulid()


@pytest.fixture
def ledger(db_session):
    """Audit ledger instance"""
    return AuditLedger(db_session)


class TestComputeEventHash:
    """Tests for compute_event_hash function"""
    
    def test_hash_includes_prev_hash(self):
        """Hash should change when prev_hash changes"""
        event_data = {
            "tenant_id": "test-tenant",
            "event_type": "test.event",
            "action": "created",
            "actor_type": "USER",
            "actor_id": "user-1",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }
        
        hash1 = compute_event_hash(event_data, None)
        hash2 = compute_event_hash(event_data, "prev-hash-123")
        hash3 = compute_event_hash(event_data, "prev-hash-456")
        
        # All hashes should be different
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3
        
        # Hashes should be 64 characters (SHA256 hex)
        assert len(hash1) == 64
        assert len(hash2) == 64
        assert len(hash3) == 64
    
    def test_hash_deterministic(self):
        """Same event data and prev_hash should produce same hash"""
        event_data = {
            "tenant_id": "test-tenant",
            "event_type": "test.event",
            "action": "created",
            "actor_type": "USER",
            "actor_id": "user-1",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }
        
        prev_hash = "prev-hash-123"
        hash1 = compute_event_hash(event_data, prev_hash)
        hash2 = compute_event_hash(event_data, prev_hash)
        
        assert hash1 == hash2
    
    def test_hash_includes_all_fields(self):
        """Hash should include all relevant fields"""
        event_data1 = {
            "tenant_id": "test-tenant",
            "event_type": "test.event",
            "action": "created",
            "actor_type": "USER",
            "actor_id": "user-1",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }
        
        event_data2 = event_data1.copy()
        event_data2["action"] = "updated"  # Change action
        
        hash1 = compute_event_hash(event_data1, "prev")
        hash2 = compute_event_hash(event_data2, "prev")
        
        assert hash1 != hash2  # Different action should produce different hash
    
    def test_hash_canonical_serialization(self):
        """Hash should be stable regardless of dict key order"""
        event_data1 = {
            "tenant_id": "test-tenant",
            "event_type": "test.event",
            "action": "created",
            "actor_type": "USER",
            "actor_id": "user-1",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }
        
        # Same data, different key order (Python 3.7+ preserves insertion order)
        event_data2 = {
            "action": "created",
            "tenant_id": "test-tenant",
            "actor_id": "user-1",
            "event_type": "test.event",
            "actor_type": "USER",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }
        
        hash1 = compute_event_hash(event_data1, "prev")
        hash2 = compute_event_hash(event_data2, "prev")
        
        assert hash1 == hash2  # Should be same despite key order


class TestAuditLedgerAppend:
    """Tests for append_event method"""
    
    def test_append_first_event(self, ledger, tenant_id):
        """Appending first event should create chain head"""
        event = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event",
            action="created",
            entity_type="test_entity",
            entity_id="entity-1",
            actor_type="SYSTEM",
            actor_id="system-1",
        )
        
        assert event.id is not None
        assert event.tenant_id == tenant_id
        assert event.sequence_num == 1
        assert event.prev_hash is None  # First event has no previous
        assert event.event_hash is not None
        assert len(event.event_hash) == 64
        
        # Check chain head was created
        chain_head = (
            ledger.session.query(AuditChainHead)
            .filter(AuditChainHead.tenant_id == tenant_id)
            .first()
        )
        assert chain_head is not None
        assert chain_head.latest_sequence_num == 1
        assert chain_head.latest_hash == event.event_hash
    
    def test_append_second_event(self, ledger, tenant_id):
        """Appending second event should link to first"""
        # First event
        event1 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event1",
            action="created",
            actor_type="SYSTEM",
        )
        
        # Second event
        event2 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event2",
            action="updated",
            actor_type="USER",
            actor_id="user-1",
        )
        
        assert event2.sequence_num == 2
        assert event2.prev_hash == event1.event_hash  # Links to first event
        
        # Check chain head updated
        chain_head = (
            ledger.session.query(AuditChainHead)
            .filter(AuditChainHead.tenant_id == tenant_id)
            .first()
        )
        assert chain_head.latest_sequence_num == 2
        assert chain_head.latest_hash == event2.event_hash
    
    def test_append_with_payload(self, ledger, tenant_id):
        """Append event with payload"""
        payload = {"key": "value", "number": 123}
        
        event = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event",
            action="created",
            payload=payload,
        )
        
        assert event.payload_json == payload


class TestAuditLedgerVerifyChain:
    """Tests for verify_chain method"""
    
    def test_verify_valid_chain(self, ledger, tenant_id):
        """Verify chain should pass for valid chain"""
        # Create chain of 3 events
        event1 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event1",
            action="created",
        )
        event2 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event2",
            action="updated",
        )
        event3 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event3",
            action="deleted",
        )
        
        # Verify chain
        result = ledger.verify_chain(tenant_id)
        
        assert isinstance(result, ChainVerificationResult)
        assert result.is_valid is True
        assert result.total_events == 3
        assert result.verified_events == 3
        assert len(result.errors) == 0
    
    def test_verify_empty_chain(self, ledger, tenant_id):
        """Verify chain should handle empty chain"""
        result = ledger.verify_chain(tenant_id)
        
        assert result.is_valid is True
        assert result.total_events == 0
        assert result.verified_events == 0
        assert len(result.errors) == 0
    
    def test_verify_chain_detects_tampering(self, ledger, tenant_id):
        """Verify chain should detect if event is modified"""
        # Create chain
        event1 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event1",
            action="created",
        )
        event2 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event2",
            action="updated",
        )
        
        # Tamper with event (modify action)
        event2.action = "tampered"
        ledger.session.commit()
        
        # Verify chain should fail
        result = ledger.verify_chain(tenant_id)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        # Should detect hash mismatch
        assert any("hash mismatch" in error.lower() for error in result.errors)
    
    def test_verify_chain_detects_broken_link(self, ledger, tenant_id):
        """Verify chain should detect broken prev_hash link"""
        # Create chain
        event1 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event1",
            action="created",
        )
        event2 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event2",
            action="updated",
        )
        
        # Break the chain by modifying prev_hash
        event2.prev_hash = "broken-hash"
        ledger.session.commit()
        
        # Verify chain should fail
        result = ledger.verify_chain(tenant_id)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        # Should detect broken chain
        assert any("chain broken" in error.lower() for error in result.errors)


class TestAuditLedgerGetEvents:
    """Tests for get_events method"""
    
    def test_get_all_events(self, ledger, tenant_id):
        """Get all events for tenant"""
        # Create multiple events
        for i in range(3):
            ledger.append_event(
                tenant_id=tenant_id,
                event_type=f"test.event{i}",
                action="created",
            )
        
        events = ledger.get_events(tenant_id)
        
        assert len(events) == 3
        assert all(e.tenant_id == tenant_id for e in events)
        # Should be ordered by sequence_num
        assert events[0].sequence_num == 1
        assert events[1].sequence_num == 2
        assert events[2].sequence_num == 3
    
    def test_get_events_filter_by_entity_type(self, ledger, tenant_id):
        """Filter events by entity_type"""
        # Create events with different entity types
        ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event1",
            action="created",
            entity_type="risk_assessment",
            entity_id="assess-1",
        )
        ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event2",
            action="created",
            entity_type="risk_run",
            entity_id="run-1",
        )
        ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event3",
            action="created",
            entity_type="risk_assessment",
            entity_id="assess-2",
        )
        
        events = ledger.get_events(tenant_id, entity_type="risk_assessment")
        
        assert len(events) == 2
        assert all(e.entity_type == "risk_assessment" for e in events)
    
    def test_get_events_filter_by_entity_id(self, ledger, tenant_id):
        """Filter events by entity_id"""
        ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event1",
            action="created",
            entity_type="risk_assessment",
            entity_id="assess-1",
        )
        ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event2",
            action="updated",
            entity_type="risk_assessment",
            entity_id="assess-1",
        )
        ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event3",
            action="created",
            entity_type="risk_assessment",
            entity_id="assess-2",
        )
        
        events = ledger.get_events(tenant_id, entity_id="assess-1")
        
        assert len(events) == 2
        assert all(e.entity_id == "assess-1" for e in events)
    
    def test_get_events_filter_by_date(self, ledger, tenant_id):
        """Filter events by date range"""
        # Create events at different times
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Mock created_at by creating events and updating timestamps
        event1 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event1",
            action="created",
        )
        event1.created_at = base_time
        ledger.session.commit()
        
        event2 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event2",
            action="created",
        )
        event2.created_at = base_time.replace(hour=13)
        ledger.session.commit()
        
        event3 = ledger.append_event(
            tenant_id=tenant_id,
            event_type="test.event3",
            action="created",
        )
        event3.created_at = base_time.replace(hour=14)
        ledger.session.commit()
        
        # Filter by date range
        from_date = base_time.replace(hour=12, minute=30)
        to_date = base_time.replace(hour=13, minute=30)
        
        events = ledger.get_events(tenant_id, from_date=from_date, to_date=to_date)
        
        # Should get event2 (hour 13)
        assert len(events) >= 1
        assert all(from_date <= e.created_at <= to_date for e in events)
    
    def test_get_events_with_limit(self, ledger, tenant_id):
        """Get events with limit"""
        # Create 5 events
        for i in range(5):
            ledger.append_event(
                tenant_id=tenant_id,
                event_type=f"test.event{i}",
                action="created",
            )
        
        events = ledger.get_events(tenant_id, limit=3)
        
        assert len(events) == 3
        # Should be first 3 events (ordered by sequence_num)
        assert events[0].sequence_num == 1
        assert events[1].sequence_num == 2
        assert events[2].sequence_num == 3


class TestAuditLedgerConcurrency:
    """Tests for concurrent event appending"""
    
    def test_concurrent_appends_dont_corrupt_chain(self, ledger, tenant_id):
        """Multiple threads appending events should not corrupt chain"""
        num_threads = 5
        events_per_thread = 10
        total_events = num_threads * events_per_thread
        
        errors = []
        events_created = []
        
        def append_events(thread_id):
            """Append events in a thread"""
            try:
                for i in range(events_per_thread):
                    event = ledger.append_event(
                        tenant_id=tenant_id,
                        event_type=f"test.event.{thread_id}.{i}",
                        action="created",
                        actor_type="SYSTEM",
                        actor_id=f"thread-{thread_id}",
                    )
                    events_created.append(event.id)
            except Exception as e:
                errors.append(str(e))
        
        # Start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=append_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify all events were created
        all_events = ledger.get_events(tenant_id)
        assert len(all_events) == total_events
        
        # Verify sequence numbers are unique and sequential
        sequence_nums = [e.sequence_num for e in all_events]
        assert len(sequence_nums) == len(set(sequence_nums))  # All unique
        assert min(sequence_nums) == 1
        assert max(sequence_nums) == total_events
        
        # Verify chain integrity
        result = ledger.verify_chain(tenant_id)
        assert result.is_valid is True, f"Chain verification failed: {result.errors}"
        assert result.total_events == total_events
        assert result.verified_events == total_events
    
    def test_concurrent_appends_sequential_sequence_nums(self, ledger, tenant_id):
        """Concurrent appends should produce sequential sequence numbers"""
        num_threads = 3
        events_per_thread = 5
        
        def append_events():
            """Append events"""
            for i in range(events_per_thread):
                ledger.append_event(
                    tenant_id=tenant_id,
                    event_type="test.event",
                    action="created",
                )
                time.sleep(0.01)  # Small delay to increase chance of interleaving
        
        # Start threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=append_events)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify sequence numbers are sequential (1 to total)
        all_events = ledger.get_events(tenant_id)
        sequence_nums = sorted([e.sequence_num for e in all_events])
        
        expected_sequence = list(range(1, len(all_events) + 1))
        assert sequence_nums == expected_sequence, \
            f"Sequence numbers not sequential: {sequence_nums}"
