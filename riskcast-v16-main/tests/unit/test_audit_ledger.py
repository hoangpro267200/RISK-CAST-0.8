"""
Unit Tests for Audit Ledger Service
Tests for hash chaining, canonicalization, and chain integrity
RISKCAST V3 - Modular Monolith
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import Mock, MagicMock

from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.models import AuditEvent, AuditChainHead, ActorType
from app.modules.audit_ledger.schemas import AuditContext


class TestAuditHashChaining:
    """Tests for audit ledger hash chaining"""
    
    def test_canonicalize_json_stable_ordering(self):
        """JSON canonicalization should produce stable output regardless of key order"""
        data1 = {"b": 1, "a": 2, "c": {"z": 3, "y": 4}}
        data2 = {"a": 2, "b": 1, "c": {"y": 4, "z": 3}}
        
        service = AuditLedgerService(None)
        canonical1 = service._canonicalize_json(data1)
        canonical2 = service._canonicalize_json(data2)
        
        assert canonical1 == canonical2
        # Verify it's valid JSON
        import json
        assert json.loads(canonical1) == json.loads(canonical2)
    
    def test_canonicalize_json_handles_datetime(self):
        """Canonicalization should handle datetime objects"""
        service = AuditLedgerService(None)
        dt = datetime(2024, 1, 1, 12, 0, 0)
        data = {"timestamp": dt, "value": 123}
        
        canonical = service._canonicalize_json(data)
        # Should not raise exception
        assert isinstance(canonical, str)
        assert "2024" in canonical
    
    def test_event_hash_includes_prev_hash(self):
        """Event hash should change when prev_hash changes"""
        service = AuditLedgerService(None)
        
        event_data = {
            'tenant_id': 'test-tenant',
            'occurred_at': datetime(2024, 1, 1, 12, 0, 0),
            'actor_type': 'USER',
            'actor_id': 'user-1',
            'action': 'test.action',
            'resource_type': 'test',
            'resource_id': 'res-1',
            'context_json': {},
            'diff_json': {}
        }
        
        hash1 = service._compute_event_hash(event_data, None)
        hash2 = service._compute_event_hash(event_data, "abc123")
        hash3 = service._compute_event_hash(event_data, "xyz789")
        
        # All hashes should be different
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3
        
        # Hashes should be 64 characters (SHA256 hex)
        assert len(hash1) == 64
        assert len(hash2) == 64
        assert len(hash3) == 64
    
    def test_event_hash_deterministic(self):
        """Same event data and prev_hash should produce same hash"""
        service = AuditLedgerService(None)
        
        event_data = {
            'tenant_id': 'test-tenant',
            'occurred_at': datetime(2024, 1, 1, 12, 0, 0),
            'actor_type': 'USER',
            'actor_id': 'user-1',
            'action': 'test.action',
            'resource_type': 'test',
            'resource_id': 'res-1',
            'context_json': {},
            'diff_json': {}
        }
        
        prev_hash = "prev-hash-123"
        hash1 = service._compute_event_hash(event_data, prev_hash)
        hash2 = service._compute_event_hash(event_data, prev_hash)
        
        assert hash1 == hash2
    
    def test_event_hash_includes_all_fields(self):
        """Event hash should include all relevant fields"""
        service = AuditLedgerService(None)
        
        event_data1 = {
            'tenant_id': 'tenant-1',
            'occurred_at': datetime(2024, 1, 1, 12, 0, 0),
            'actor_type': 'USER',
            'actor_id': 'user-1',
            'action': 'test.action',
            'resource_type': 'test',
            'resource_id': 'res-1',
            'context_json': {},
            'diff_json': {}
        }
        
        event_data2 = event_data1.copy()
        event_data2['action'] = 'test.action2'  # Change action
        
        hash1 = service._compute_event_hash(event_data1, "prev")
        hash2 = service._compute_event_hash(event_data2, "prev")
        
        assert hash1 != hash2  # Different action should produce different hash
    
    @pytest.mark.asyncio
    async def test_chain_integrity_verification(self, db_session):
        """Chain verification should detect tampering"""
        service = AuditLedgerService(db_session)
        
        tenant_id = "test-tenant-1"
        context = AuditContext()
        
        # Insert first event
        event1 = await service.log_event(
            tenant_id=tenant_id,
            actor_type=ActorType.USER,
            actor_id="user-1",
            action="test.action1",
            resource_type="test",
            resource_id="res-1",
            context=context
        )
        
        # Insert second event (chained to first)
        event2 = await service.log_event(
            tenant_id=tenant_id,
            actor_type=ActorType.USER,
            actor_id="user-1",
            action="test.action2",
            resource_type="test",
            resource_id="res-2",
            context=context
        )
        
        # Insert third event (chained to second)
        event3 = await service.log_event(
            tenant_id=tenant_id,
            actor_type=ActorType.USER,
            actor_id="user-1",
            action="test.action3",
            resource_type="test",
            resource_id="res-3",
            context=context
        )
        
        db_session.commit()
        
        # Verify chain passes
        result = await service.verify_chain(tenant_id)
        assert result.is_valid is True
        assert result.total_events == 3
        assert result.verified_events == 3
        
        # Tamper with middle event (change action)
        event2.action = "tampered.action"
        db_session.commit()
        
        # Verify chain fails
        result = await service.verify_chain(tenant_id)
        assert result.is_valid is False
        assert result.verified_events < result.total_events
    
    @pytest.mark.asyncio
    async def test_chain_verification_empty_chain(self, db_session):
        """Chain verification should handle empty chain"""
        service = AuditLedgerService(db_session)
        
        tenant_id = "empty-tenant"
        
        result = await service.verify_chain(tenant_id)
        assert result.is_valid is True
        assert result.total_events == 0
        assert result.verified_events == 0
    
    @pytest.mark.asyncio
    async def test_log_event_creates_chain_head(self, db_session):
        """Logging first event should create chain head"""
        service = AuditLedgerService(db_session)
        
        tenant_id = "new-tenant"
        context = AuditContext()
        
        # Check no chain head exists
        chain_head = db_session.query(AuditChainHead).filter(
            AuditChainHead.tenant_id == tenant_id
        ).first()
        assert chain_head is None
        
        # Log first event
        event = await service.log_event(
            tenant_id=tenant_id,
            actor_type=ActorType.USER,
            actor_id="user-1",
            action="test.action",
            resource_type="test",
            resource_id="res-1",
            context=context
        )
        
        db_session.commit()
        
        # Check chain head was created
        chain_head = db_session.query(AuditChainHead).filter(
            AuditChainHead.tenant_id == tenant_id
        ).first()
        assert chain_head is not None
        assert chain_head.latest_event_id == event.id
        assert chain_head.latest_hash == event.event_hash
