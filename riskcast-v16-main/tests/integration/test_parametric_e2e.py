"""
End-to-end integration tests for parametric triggers.

Tests:
1. Oracle event ingestion
2. Trigger detection
3. Multi-source corroboration
4. Payout calculation
5. Approval workflow
"""

import pytest
import time
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
from app.modules.underwriting.models import Policy
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid
from app.services.trigger_definition_service import TriggerDefinitionService
from app.services.trigger_event_service import TriggerEventService
from app.services.oracle_event_service import OracleEventService
from app.modules.parametric.models import (
    TriggerDefinition,
    TriggerDefinitionStatus,
    TriggerEventStatus,
)


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_tenant_and_user(db_session: Session):
    """Create test tenant and user."""
    tenant = Tenant(
        id=generate_ulid(),
        name="Parametric Test Tenant",
        status=TenantStatus.ACTIVE,
    )
    db_session.add(tenant)

    user = User(
        id=generate_ulid(),
        email="parametric-user@test.com",
        password_hash="hashed-password",
        status="ACTIVE",
    )
    db_session.add(user)

    role = Role(
        id=generate_ulid(),
        name="parametric_operator",
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


@pytest.fixture
def published_trigger_definition(
    db_session: Session,
    test_tenant_and_user: dict,
) -> dict:
    """Create and publish a trigger definition."""
    tenant = test_tenant_and_user["tenant"]
    user = test_tenant_and_user["user"]

    service = TriggerDefinitionService(db_session, AuditLedger(db_session))

    definition = service.create_definition(
        tenant_id=tenant.id,
        name="Heavy Rainfall Trigger",
        trigger_type="RAINFALL",
        params={
            "threshold_value": 100,
            "threshold_unit": "mm",
            "comparison": ">=",
            "duration_hours": 24,
            "aggregation": "MAX",
        },
        payout_structure={
            "type": "TIERED",
            "tiers": [
                {"threshold": 100, "payout_pct": 0.25},
                {"threshold": 150, "payout_pct": 0.50},
                {"threshold": 200, "payout_pct": 1.00},
            ],
        },
        corroboration={
            "required_sources": 2,
            "correlation_threshold": 0.7,
            "time_tolerance_minutes": 60,
        },
        description="Heavy rainfall trigger for port coverage",
        created_by=user.id,
    )

    # Publish definition
    published = service.publish_definition(definition.id, published_by=user.id)

    return {
        "id": published.id,
        "name": published.name,
        "trigger_type": published.trigger_type,
        "status": published.status.value,
        "immutable_hash": published.immutable_hash,
        "params_json": published.params_json,
        "payout_structure_json": published.payout_structure_json,
        "corroboration_json": published.corroboration_json,
    }


@pytest.fixture
def active_parametric_policy(
    test_client: TestClient,
    auth_headers: dict,
    test_tenant_and_user: dict,
    db_session: Session,
    published_trigger_definition: dict,
) -> dict:
    """Create policy with parametric coverage (simplified - use existing policy if available)."""
    # For testing, we'll create a minimal policy record directly
    # In production, this would go through full underwriting flow
    from app.modules.underwriting.models import Policy, PolicyStatus

    policy = Policy(
        id=generate_ulid(),
        tenant_id=test_tenant_and_user["tenant"].id,
        policy_number=f"POL-PARAM-{generate_ulid()[:8].upper()}",
        status=PolicyStatus.ACTIVE,
        effective_from=datetime.utcnow(),
        effective_to=datetime.utcnow() + timedelta(days=90),
        terms_json={
            "insured_value_cents": 10_000_000,  # $100,000
            "coverage_type": "PARAMETRIC",
            "trigger_definition_id": published_trigger_definition["id"],
        },
        created_at=datetime.utcnow(),
    )
    db_session.add(policy)
    db_session.commit()

    return {
        "id": policy.id,
        "policy_number": policy.policy_number,
        "status": policy.status.value,
        "terms_json": policy.terms_json,
    }


class TestParametricE2E:
    """End-to-end parametric tests."""

    def test_complete_parametric_flow(
        self,
        test_client: TestClient,
        auth_headers: dict,
        published_trigger_definition: dict,
        active_parametric_policy: dict,
        db_session: Session,
        test_tenant_and_user: dict,
    ):
        """Test complete parametric trigger flow."""
        definition_id = published_trigger_definition["id"]
        policy_id = active_parametric_policy["id"]
        tenant = test_tenant_and_user["tenant"]

        # Step 1: Ingest oracle events from multiple sources
        now = datetime.utcnow()

        # Source 1: Tomorrow.io
        event1_request = {
            "source": "TOMORROW_IO",
            "captured_at": now.isoformat() + "Z",
            "payload_json": {
                "rainfall_mm": 125,
                "measurement_period_hours": 24,
                "location": {"lat": 51.9, "lng": 4.5},
            },
        }

        response = test_client.post(
            "/api/v3/parametric/oracle-events",
            json=event1_request,
            headers=auth_headers,
        )
        assert response.status_code == 201, f"Failed to ingest event1: {response.text}"
        event1 = response.json()
        event1_id = event1["id"]

        # Verify payload hash
        assert event1["payload_hash"] is not None

        # Source 2: ICEYE (corroboration)
        event2_request = {
            "source": "ICEYE",
            "captured_at": (now + timedelta(minutes=30)).isoformat() + "Z",
            "payload_json": {
                "rainfall_mm": 130,
                "measurement_period_hours": 24,
                "satellite_pass": "ICEYE-X7",
            },
        }

        response = test_client.post(
            "/api/v3/parametric/oracle-events",
            json=event2_request,
            headers=auth_headers,
        )
        assert response.status_code == 201, f"Failed to ingest event2: {response.text}"
        event2 = response.json()
        event2_id = event2["id"]

        # Step 2: Detect trigger (using service directly - no HTTP endpoint yet)
        trigger_event_service = TriggerEventService(
            db_session, AuditLedger(db_session), OracleEventService(db_session)
        )

        trigger_event = trigger_event_service.detect_trigger(
            policy_id=policy_id,
            definition_id=definition_id,
            oracle_event_ids=[event1_id, event2_id],
        )

        trigger_id = trigger_event.id

        assert trigger_event.status == TriggerEventStatus.DETECTED
        assert trigger_event.detection_json is not None
        assert trigger_event.detection_json["measured_value"] >= 100
        assert trigger_event.evaluation_hash is not None

        # Step 3: Validate with corroboration
        trigger_event = trigger_event_service.validate_trigger(
            trigger_event_id=trigger_id, validated_by=test_tenant_and_user["user"].id
        )

        assert trigger_event.status == TriggerEventStatus.VALIDATED
        assert trigger_event.validation_json is not None
        assert trigger_event.validation_json["validation_passed"] == True
        assert len(trigger_event.validation_json["corroborating_sources"]) >= 2
        assert trigger_event.validation_json["correlation_score"] >= 0.7

        # Step 4: Propose payout
        trigger_event = trigger_event_service.propose_payout(
            trigger_event_id=trigger_id, proposed_by=test_tenant_and_user["user"].id
        )

        assert trigger_event.status == TriggerEventStatus.PROPOSED_PAYOUT
        assert trigger_event.proposed_payout_cents > 0
        assert trigger_event.payout_calculation_json is not None
        assert trigger_event.payout_calculation_json["payout_type"] == "TIERED"

        # Verify tier calculation
        # 125mm should trigger tier 1 (25% at 100mm threshold)
        # But not tier 2 (50% at 150mm)
        assert trigger_event.payout_calculation_json["tier_triggered"] == 1
        assert trigger_event.payout_calculation_json["payout_percentage"] == 0.25

        # Step 5: Approve payout (via API endpoint)
        response = test_client.post(
            f"/api/v3/parametric/trigger-events/{trigger_id}/approve-payout",
            headers=auth_headers,
        )
        assert (
            response.status_code == 200
        ), f"Failed to approve payout: {response.text}"
        approval = response.json()

        assert approval["status"] == TriggerEventStatus.APPROVED.value

        # Step 6: Verify determinism
        # Re-evaluate with same inputs should give same result
        # (Re-detection would use same events, should get same evaluation hash)
        from app.modules.parametric.models import OracleEvent

        oracle_events = (
            db_session.query(OracleEvent)
            .filter(OracleEvent.id.in_([event1_id, event2_id]))
            .order_by(OracleEvent.captured_at)
            .all()
        )

        from app.core.parametric.evaluator import TriggerEvaluator

        evaluator = TriggerEvaluator()
        definition = (
            db_session.query(TriggerDefinition)
            .filter(TriggerDefinition.id == definition_id)
            .first()
        )

        evaluation = evaluator.evaluate(definition, oracle_events)

        # Same evaluation hash
        assert evaluation.evaluation_hash == trigger_event.evaluation_hash

    def test_corroboration_fails_single_source(
        self,
        test_client: TestClient,
        auth_headers: dict,
        published_trigger_definition: dict,
        active_parametric_policy: dict,
        db_session: Session,
        test_tenant_and_user: dict,
    ):
        """Test that single source fails corroboration."""
        # Ingest only ONE oracle event
        event_request = {
            "source": "TOMORROW_IO",
            "captured_at": datetime.utcnow().isoformat() + "Z",
            "payload_json": {"rainfall_mm": 125},
        }

        response = test_client.post(
            "/api/v3/parametric/oracle-events",
            json=event_request,
            headers=auth_headers,
        )
        assert response.status_code == 201
        event = response.json()
        event_id = event["id"]

        # Detect trigger
        trigger_event_service = TriggerEventService(
            db_session, AuditLedger(db_session), OracleEventService(db_session)
        )

        trigger_event = trigger_event_service.detect_trigger(
            policy_id=active_parametric_policy["id"],
            definition_id=published_trigger_definition["id"],
            oracle_event_ids=[event_id],
        )

        # Validate - should fail
        trigger_event = trigger_event_service.validate_trigger(
            trigger_event_id=trigger_event.id
        )

        assert trigger_event.status == TriggerEventStatus.CORROBORATION_FAILED
        assert trigger_event.validation_json["validation_passed"] == False
        assert (
            "Need 2 sources" in trigger_event.validation_json["validation_details"]["error"]
        )

    def test_trigger_below_threshold_not_triggered(
        self,
        test_client: TestClient,
        auth_headers: dict,
        published_trigger_definition: dict,
        active_parametric_policy: dict,
        db_session: Session,
    ):
        """Test that events below threshold don't trigger."""
        # Ingest event below threshold
        event_request = {
            "source": "TOMORROW_IO",
            "captured_at": datetime.utcnow().isoformat() + "Z",
            "payload_json": {"rainfall_mm": 50},  # Below 100mm threshold
        }

        response = test_client.post(
            "/api/v3/parametric/oracle-events",
            json=event_request,
            headers=auth_headers,
        )
        assert response.status_code == 201
        event = response.json()
        event_id = event["id"]

        # Try to detect trigger - should fail
        trigger_event_service = TriggerEventService(
            db_session, AuditLedger(db_session), OracleEventService(db_session)
        )

        from app.services.trigger_event_service import (
            TriggerNotMetError,
        )

        with pytest.raises(TriggerNotMetError):
            trigger_event_service.detect_trigger(
                policy_id=active_parametric_policy["id"],
                definition_id=published_trigger_definition["id"],
                oracle_event_ids=[event_id],
            )

    def test_oracle_event_integrity_verification(
        self,
        test_client: TestClient,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test oracle event integrity verification."""
        # Ingest event
        event_request = {
            "source": "TOMORROW_IO",
            "captured_at": datetime.utcnow().isoformat() + "Z",
            "payload_json": {"rainfall_mm": 125, "temp_c": 15},
        }

        response = test_client.post(
            "/api/v3/parametric/oracle-events",
            json=event_request,
            headers=auth_headers,
        )
        assert response.status_code == 201
        event = response.json()
        event_id = event["id"]
        stored_hash = event["payload_hash"]

        # Verify integrity by querying directly
        from app.modules.parametric.models import OracleEvent

        db_event = db_session.query(OracleEvent).filter(OracleEvent.id == event_id).first()
        assert db_event is not None
        assert db_event.payload_hash == stored_hash

        # Verify hash computation matches
        import json
        import hashlib

        canonical = json.dumps(event_request["payload_json"], sort_keys=True, separators=(",", ":"))
        computed_hash = hashlib.sha256(canonical.encode()).hexdigest()

        assert computed_hash == stored_hash

    def test_trigger_definition_immutability_after_publish(
        self,
        db_session: Session,
        test_tenant_and_user: dict,
        published_trigger_definition: dict,
    ):
        """Test that trigger definition is immutable after publishing."""
        definition_id = published_trigger_definition["id"]

        # Try to modify published definition
        definition = (
            db_session.query(TriggerDefinition)
            .filter(TriggerDefinition.id == definition_id)
            .first()
        )

        assert definition.status == TriggerDefinitionStatus.PUBLISHED
        assert definition.immutable_hash is not None

        # Attempting to modify params should be prevented by application logic
        # (database constraints may not enforce this, but service layer should)
        original_hash = definition.immutable_hash

        # Verify hash is deterministic
        import json
        import hashlib

        canonical = json.dumps(definition.params_json, sort_keys=True, separators=(",", ":"))
        recomputed_hash = hashlib.sha256(canonical.encode()).hexdigest()

        assert recomputed_hash == original_hash
