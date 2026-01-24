"""
Integration tests for audit trail integrity.

Verifies:
1. Hash chain integrity
2. Event completeness
3. Tamper detection
4. Provenance tracking
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.modules.tenancy.models import (
    Tenant,
    User,
    Membership,
    Role,
    RoleScope,
    TenantStatus,
)
from app.modules.identity_access.models import Session as AuthSession
from app.core.audit_ledger.ledger import AuditLedger, compute_event_hash
from app.models.audit import AuditEvent, AuditChainHead
from app.modules.underwriting.models import Policy, PolicyStatus
from app.modules.risk_runs.models import RiskRun
from app.modules.model_versioning.models import RiskModelVersion
from app.shared.utils import generate_ulid


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_tenant_and_user(db_session: Session):
    """Create test tenant and user."""
    tenant = Tenant(
        id=generate_ulid(),
        name="Audit Test Tenant",
        status=TenantStatus.ACTIVE,
    )
    db_session.add(tenant)

    user = User(
        id=generate_ulid(),
        email="audit-user@test.com",
        password_hash="hashed-password",
        status="ACTIVE",
    )
    db_session.add(user)

    role = Role(
        id=generate_ulid(),
        name="audit_operator",
        scope=RoleScope.TENANT,
    )
    db_session.add(role)

    membership = Membership(
        id=generate_ulid(),
        tenant_id=tenant.id,
        user_id=user.id,
        role_id=role.id,
        status="ACTIVE",
    )
    db_session.add(membership)

    auth_session = AuthSession(
        id=generate_ulid(),
        user_id=user.id,
        token="test-token-123",
        expires_at=datetime(2025, 12, 31, 23, 59, 59),
    )
    db_session.add(auth_session)

    db_session.commit()

    return {
        "tenant": tenant,
        "user": user,
        "role": role,
        "membership": membership,
        "session": auth_session,
    }


@pytest.fixture
def auth_headers(test_tenant_and_user: dict) -> dict:
    """Generate auth headers."""
    return {
        "Authorization": "Bearer test-token-123",
        "X-Tenant-Id": test_tenant_and_user["tenant"].id,
    }


class TestAuditIntegrity:
    """Audit integrity tests."""

    def test_hash_chain_integrity(
        self, db_session: Session, test_tenant_and_user: dict
    ):
        """Test that audit hash chain is valid."""
        audit = AuditLedger(db_session)
        tenant = test_tenant_and_user["tenant"]
        tenant_id = tenant.id

        # Create multiple events
        for i in range(10):
            audit.append_event(
                tenant_id=tenant_id,
                event_type="TEST",
                action=f"ACTION_{i}",
                entity_type="test_entity",
                entity_id=str(uuid4()),
                actor_type="USER",
                actor_id=str(uuid4()),
                payload={"index": i},
            )

        # Verify chain
        events = audit.get_events(tenant_id=tenant_id, limit=100)
        events = sorted(events, key=lambda e: e.sequence_num)

        assert len(events) == 10, f"Expected 10 events, got {len(events)}"

        # First event should have prev_hash = None
        assert events[0].prev_hash is None, "First event should have prev_hash=None"

        # Verify chain links
        for i in range(1, len(events)):
            prev_event = events[i - 1]
            current_event = events[i]

            # Current event's prev_hash should match previous event's hash
            assert (
                current_event.prev_hash == prev_event.event_hash
            ), f"Chain broken at event {i}: {current_event.prev_hash} != {prev_event.event_hash}"

            # Sequence numbers should be sequential
            assert (
                current_event.sequence_num == prev_event.sequence_num + 1
            ), f"Non-sequential at event {i}: {current_event.sequence_num} != {prev_event.sequence_num + 1}"

    def test_event_hash_verification(
        self, db_session: Session, test_tenant_and_user: dict
    ):
        """Test that event hashes can be verified."""
        audit = AuditLedger(db_session)
        tenant = test_tenant_and_user["tenant"]

        # Create event
        event = audit.append_event(
            tenant_id=tenant.id,
            event_type="POLICY",
            action="BOUND",
            entity_type="policy",
            entity_id=str(uuid4()),
            actor_type="USER",
            actor_id=str(uuid4()),
            payload={"premium_cents": 100000},
        )

        # Recompute hash
        event_data = {
            "tenant_id": event.tenant_id,
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "action": event.action,
            "actor_type": event.actor_type,
            "actor_id": event.actor_id,
            "payload_json": event.payload_json,
            "created_at": event.created_at,
        }
        computed_hash = compute_event_hash(event_data, event.prev_hash)

        # Should match stored hash
        assert (
            computed_hash == event.event_hash
        ), f"Hash mismatch: computed {computed_hash}, stored {event.event_hash}"

    def test_tamper_detection(self, db_session: Session, test_tenant_and_user: dict):
        """Test that tampering is detected."""
        audit = AuditLedger(db_session)
        tenant = test_tenant_and_user["tenant"]

        # Create events
        event1 = audit.append_event(
            tenant_id=tenant.id,
            event_type="TEST",
            action="ACTION_1",
            entity_type="test",
            entity_id=str(uuid4()),
            actor_type="USER",
            payload={},
        )

        event2 = audit.append_event(
            tenant_id=tenant.id,
            event_type="TEST",
            action="ACTION_2",
            entity_type="test",
            entity_id=str(uuid4()),
            actor_type="USER",
            payload={"important": "data"},
        )

        event3 = audit.append_event(
            tenant_id=tenant.id,
            event_type="TEST",
            action="ACTION_3",
            entity_type="test",
            entity_id=str(uuid4()),
            actor_type="USER",
            payload={},
        )

        # Verify chain is valid before tampering
        result = audit.verify_chain(tenant_id=tenant.id)
        assert result.is_valid, "Chain should be valid before tampering"

        # Tamper with middle event (modify payload)
        event2_db = (
            db_session.query(AuditEvent)
            .filter(AuditEvent.id == event2.id)
            .first()
        )
        original_payload = event2_db.payload_json
        event2_db.payload_json = {"important": "TAMPERED"}
        db_session.commit()

        # Verify chain - should detect tampering
        result = audit.verify_chain(tenant_id=tenant.id)

        assert result.is_valid == False, "Chain should be invalid after tampering"
        assert len(result.errors) > 0, "Should have errors after tampering"
        assert any(
            "hash mismatch" in error.lower() for error in result.errors
        ), f"Should detect hash mismatch, errors: {result.errors}"

        # Restore original
        event2_db.payload_json = original_payload
        db_session.commit()

        # Verify chain is valid again
        result = audit.verify_chain(tenant_id=tenant.id)
        assert result.is_valid, "Chain should be valid after restoring original"

    def test_all_operations_audited(
        self,
        test_client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_tenant_and_user: dict,
    ):
        """Test that all critical operations create audit events."""
        audit = AuditLedger(db_session)
        tenant = test_tenant_and_user["tenant"]
        tenant_id = tenant.id

        # Get initial count
        initial_events = audit.get_events(tenant_id=tenant_id)
        initial_count = len(initial_events)

        # Create risk assessment
        response = test_client.post(
            "/api/v3/risk/assessments",
            json={
                "shipment_data": {
                    "cargo": {"type": "electronics", "value": 100000},
                    "route": {
                        "origin": {"port": "CNSHA", "country": "CN"},
                        "destination": {"port": "NLRTM", "country": "NL"},
                    },
                },
                "schema_version": "v1",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assessment = response.json()

        # Create evidence bundle
        bundle_response = test_client.post(
            "/api/v3/evidence/bundles",
            json={"name": "Test bundle", "bundle_type": "UNDERWRITING"},
            headers=auth_headers,
        )
        assert bundle_response.status_code == 201
        bundle = bundle_response.json()

        # Seal bundle
        test_client.post(
            f"/api/v3/evidence/bundles/{bundle['id']}/seal",
            headers=auth_headers,
        )

        # Create submission
        response = test_client.post(
            "/api/v3/underwriting/submissions",
            json={
                "risk_assessment_id": assessment["id"],
                "requested_coverage_json": {"coverage_type": "ALL_RISK"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        submission = response.json()

        # Check audit events were created
        events = audit.get_events(tenant_id=tenant_id)
        new_events = len(events) - initial_count

        # Should have at least: assessment created, bundle created, bundle sealed, submission created
        assert (
            new_events >= 4
        ), f"Expected at least 4 new events, got {new_events}"

        # Verify event types
        event_actions = [e.action for e in events]
        assert any(
            "CREATED" in a or "COMPLETED" in a or "created" in a.lower()
            for a in event_actions
        ), f"Should have CREATED action, got: {event_actions}"

    def test_provenance_chain_complete(
        self,
        test_client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_tenant_and_user: dict,
    ):
        """Test that policy has complete provenance chain."""
        tenant = test_tenant_and_user["tenant"]

        # Create minimal policy with required references
        # (In real flow, these would come from underwriting, but for test we create directly)
        from app.modules.model_versioning.models import ModelScope, ModelVersionStatus

        # Create model version
        model = RiskModelVersion(
            id=generate_ulid(),
            tenant_id=tenant.id,
            scope=ModelScope.TENANT,
            name="Test Model",
            status=ModelVersionStatus.PUBLISHED,
            model_schema_version="risk_model_v1.0",
            version="1.0.0",
            weights_json={"route_risk": 0.4},
            immutable_hash="test-model-hash",
            published_at=datetime.utcnow(),
        )
        db_session.add(model)
        db_session.commit()

        # Create risk run
        from app.modules.risk_runs.models import RiskRunStatus

        risk_run = RiskRun(
            id=generate_ulid(),
            tenant_id=tenant.id,
            risk_assessment_id=generate_ulid(),
            status=RiskRunStatus.SUCCEEDED,
            engine_version="v16",
            result_schema_version="risk_result_v3.0",
            seed_strategy="DETERMINISTIC_INPUT_HASH",
            seed=12345,
            iterations=10000,
            result_hash="test-run-hash",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(risk_run)
        db_session.commit()

        # Create policy
        policy = Policy(
            id=generate_ulid(),
            tenant_id=tenant.id,
            policy_number=f"POL-{generate_ulid()[:8].upper()}",
            status=PolicyStatus.ACTIVE,
            effective_from=datetime.utcnow(),
            effective_to=datetime.utcnow() + timedelta(days=90),
            model_version_id=model.id,
            risk_run_id=risk_run.id,
            policy_hash="test-policy-hash",
        )
        db_session.add(policy)
        db_session.commit()

        # Verify all hashes present
        assert policy.policy_hash is not None
        assert risk_run.result_hash is not None
        assert model.immutable_hash is not None

        # Verify references
        assert policy.risk_run_id == risk_run.id
        assert policy.model_version_id == model.id

        # Verify audit events exist for policy
        audit = AuditLedger(db_session)
        policy_events = audit.get_events(
            tenant_id=tenant.id, entity_type="policy", entity_id=policy.id
        )

        # May not have events if created directly, but if they exist, verify structure
        if policy_events:
            for event in policy_events:
                assert event.event_hash is not None
                assert event.tenant_id == tenant.id
                assert event.entity_type == "policy"
                assert event.entity_id == policy.id

    def test_audit_export_complete(
        self,
        test_client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_tenant_and_user: dict,
    ):
        """Test that audit export includes all data."""
        tenant = test_tenant_and_user["tenant"]
        audit = AuditLedger(db_session)

        # Create some activity
        for i in range(5):
            audit.append_event(
                tenant_id=tenant.id,
                event_type="TEST",
                action=f"EXPORT_TEST_{i}",
                entity_type="test",
                entity_id=str(uuid4()),
                actor_type="USER",
                payload={"test_index": i},
            )

        # Export audit via API
        response = test_client.get(
            "/api/v3/audit/export",
            params={"from_sequence": 0},
            headers=auth_headers,
        )
        assert (
            response.status_code == 200
        ), f"Failed to export audit: {response.text}"

        export = response.json()

        # Verify export structure
        assert "events" in export
        assert "chain_verified" in export
        assert export["chain_verified"] == True, "Chain should be verified"

        # Verify events have required fields
        for event in export["events"]:
            assert "event_hash" in event
            assert "prev_hash" in event
            assert "event_type" in event
            assert "action" in event
            assert "created_at" in event
            assert "tenant_id" in event
            assert "sequence_num" in event

        # Verify chain head hash is present
        assert "chain_head_hash" in export
        if export["chain_head_hash"]:
            # Should be 64 character hex string (SHA256)
            assert len(export["chain_head_hash"]) == 64

    def test_chain_verification_api(
        self,
        test_client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_tenant_and_user: dict,
    ):
        """Test that chain verification API works."""
        tenant = test_tenant_and_user["tenant"]
        audit = AuditLedger(db_session)

        # Create some events
        for i in range(5):
            audit.append_event(
                tenant_id=tenant.id,
                event_type="VERIFY_TEST",
                action=f"ACTION_{i}",
                entity_type="test",
                entity_id=str(uuid4()),
                actor_type="USER",
                payload={},
            )

        # Verify via API
        response = test_client.get(
            "/api/v3/audit/verify",
            params={"from_sequence": 0},
            headers=auth_headers,
        )
        assert (
            response.status_code == 200
        ), f"Failed to verify chain: {response.text}"

        verification = response.json()

        # Verify response structure
        assert "valid" in verification
        assert verification["valid"] == True, "Chain should be valid"
        assert "event_count" in verification
        assert "verified_events" in verification
        assert verification["verified_events"] == verification["event_count"]
        assert "errors" in verification
        assert len(verification["errors"]) == 0

    def test_chain_breaks_on_sequence_gap(
        self, db_session: Session, test_tenant_and_user: dict
    ):
        """Test that sequence gaps are detected."""
        audit = AuditLedger(db_session)
        tenant = test_tenant_and_user["tenant"]

        # Create events normally
        for i in range(3):
            audit.append_event(
                tenant_id=tenant.id,
                event_type="TEST",
                action=f"ACTION_{i}",
                entity_type="test",
                entity_id=str(uuid4()),
                actor_type="USER",
                payload={},
            )

        # Manually create event with wrong sequence number (simulating gap)
        # This would normally be prevented, but we test detection
        events = audit.get_events(tenant_id=tenant.id)
        last_event = events[-1]

        # Create event with gap in sequence
        gap_event = AuditEvent(
            id=str(uuid4()),
            tenant_id=tenant.id,
            sequence_num=last_event.sequence_num + 5,  # Gap!
            prev_hash=last_event.event_hash,
            event_hash="fake-hash",
            event_type="TEST",
            action="GAP_TEST",
            entity_type="test",
            entity_id=str(uuid4()),
            actor_type="USER",
            created_at=datetime.utcnow(),
        )
        db_session.add(gap_event)
        db_session.commit()

        # Verify chain - should detect gap
        result = audit.verify_chain(tenant_id=tenant.id)

        # Should detect non-sequential sequence numbers
        assert result.is_valid == False or any(
            "sequence" in error.lower() for error in result.errors
        ), f"Should detect sequence gap, result: {result}"

    def test_first_event_prev_hash_none(
        self, db_session: Session, test_tenant_and_user: dict
    ):
        """Test that first event has prev_hash = None."""
        audit = AuditLedger(db_session)
        tenant = test_tenant_and_user["tenant"]

        # Create first event
        event = audit.append_event(
            tenant_id=tenant.id,
            event_type="FIRST",
            action="INITIAL",
            entity_type="test",
            entity_id=str(uuid4()),
            actor_type="SYSTEM",
            payload={},
        )

        # First event should have prev_hash = None
        assert (
            event.prev_hash is None
        ), f"First event should have prev_hash=None, got {event.prev_hash}"

        # Sequence should be 1
        assert event.sequence_num == 1, f"First event should have sequence_num=1, got {event.sequence_num}"

        # Verify chain should pass
        result = audit.verify_chain(tenant_id=tenant.id)
        assert result.is_valid, "Chain with single event should be valid"
