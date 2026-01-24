"""
End-to-end integration tests for claims workflow.

Tests the complete flow:
1. File FNOL
2. Assign adjuster
3. Investigate
4. Request + submit evidence
5. Adjudicate
6. Authorize payout
7. Process payment via payouts service
"""

import pytest
import time
from datetime import datetime, timedelta

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
from app.services.payout_service import PayoutService, DualControlViolationError


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_tenant_and_user(db_session: Session):
    """Create test tenant and primary user."""
    # Tenant
    tenant = Tenant(
        id=generate_ulid(),
        name="Claims Test Tenant",
        status=TenantStatus.ACTIVE,
    )
    db_session.add(tenant)

    # Primary user
    user = User(
        id=generate_ulid(),
        email="claims-user@test.com",
        password_hash="hashed-password",
        status="ACTIVE",
    )
    db_session.add(user)

    # Role
    role = Role(
        id=generate_ulid(),
        name="claims_operator",
        scope=RoleScope.TENANT,
    )
    db_session.add(role)

    # Membership
    membership = Membership(
        id=generate_ulid(),
        tenant_id=tenant.id,
        user_id=user.id,
        role_id=role.id,
        status="ACTIVE",
    )
    db_session.add(membership)

    # Session (simple token)
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
    """Generate auth headers for primary user."""
    return {
        "Authorization": "Bearer test-token-123",
        "X-Tenant-Id": test_tenant_and_user["tenant"].id,
    }


@pytest.fixture
def risk_assessment_input() -> dict:
    """Sample risk assessment input used for underwriting to create active policy."""
    return {
        "shipment_data": {
            "cargo": {
                "type": "electronics",
                "value": 500_000,
                "weight": 10_000,
                "container_count": 10,
                "packaging_quality": "EXCELLENT",
            },
            "route": {
                "origin": {
                    "port": "CNSHA",
                    "country": "CN",
                    "coordinates": {"lat": 31.2304, "lon": 121.4737},
                },
                "destination": {
                    "port": "NLRTM",
                    "country": "NL",
                    "coordinates": {"lat": 51.9225, "lon": 4.4772},
                },
                "carrier_code": "MAEU",
                "estimated_departure": (datetime.utcnow() + timedelta(days=7)).isoformat()
                + "Z",
                "estimated_arrival": (datetime.utcnow() + timedelta(days=35)).isoformat()
                + "Z",
            },
            "coverage": {
                "coverage_type": "ALL_RISK",
                "insured_value_cents": 50_000_000,
                "currency": "USD",
            },
        },
        "schema_version": "v1",
    }


def wait_for_run_completion(
    client: TestClient, run_id: str, auth_headers: dict, max_wait: int = 30
) -> dict:
    """Wait for risk run to complete (helper reused from underwriting tests)."""
    start = time.time()
    while time.time() - start < max_wait:
        resp = client.get(f"/api/v3/risk/runs/{run_id}", headers=auth_headers)
        if resp.status_code == 200:
            run_data = resp.json()
            status = run_data.get("status")
            if status in ["SUCCEEDED", "FAILED"]:
                return run_data
        time.sleep(1)
    raise TimeoutError(f"Run {run_id} did not complete within {max_wait} seconds")


@pytest.fixture
def active_policy(
    test_client: TestClient,
    auth_headers: dict,
    test_tenant_and_user: dict,
    db_session: Session,
    risk_assessment_input: dict,
) -> dict:
    """
    Create an active policy for claims testing.

    Uses full underwriting flow (risk assessment -> run -> submission -> decision -> policy).
    """
    # 1. Create risk assessment
    resp = test_client.post(
        "/api/v3/risk/assessments",
        json=risk_assessment_input,
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"Failed to create assessment: {resp.text}"
    assessment = resp.json()
    assessment_id = assessment["id"]

    # 2. Create risk run
    resp = test_client.post(
        f"/api/v3/risk/assessments/{assessment_id}/runs",
        json={},
        headers=auth_headers,
    )
    assert resp.status_code in (201, 202), f"Failed to create run: {resp.text}"
    run = resp.json()
    run_id = run["id"]

    # Wait for completion
    completed_run = wait_for_run_completion(test_client, run_id, auth_headers)
    assert completed_run["status"] == "SUCCEEDED"

    # 3. Create and seal evidence bundle
    bundle_resp = test_client.post(
        "/api/v3/evidence/bundles",
        json={
            "name": f"Underwriting bundle for assessment {assessment_id}",
            "bundle_type": "UNDERWRITING",
            "description": "Underwriting evidence for policy creation",
        },
        headers=auth_headers,
    )
    assert bundle_resp.status_code == 201, f"Failed to create bundle: {bundle_resp.text}"
    bundle = bundle_resp.json()
    bundle_id = bundle["id"]

    seal_resp = test_client.post(
        f"/api/v3/evidence/bundles/{bundle_id}/seal",
        headers=auth_headers,
    )
    assert seal_resp.status_code == 200, f"Failed to seal bundle: {seal_resp.text}"

    # 4. Create underwriting submission
    submission_resp = test_client.post(
        "/api/v3/underwriting/submissions",
        json={
            "risk_assessment_id": assessment_id,
            "risk_run_id": run_id,
            "evidence_bundle_id": bundle_id,
            "requested_coverage_json": {
                "coverage_type": "ALL_RISK",
                "insured_value_cents": 50_000_000,
                "deductible_cents": 500_000,
            },
            "product_type": "COLD_CHAIN",
        },
        headers=auth_headers,
    )
    assert (
        submission_resp.status_code == 201
    ), f"Failed to create submission: {submission_resp.text}"
    submission = submission_resp.json()
    submission_id = submission["id"]

    # 5. Make QUOTE decision
    decision_resp = test_client.post(
        f"/api/v3/underwriting/submissions/{submission_id}/decisions",
        json={
            "decision": "QUOTE",
            "terms_json": {
                "premium_cents": 5_000_000,
                "deductible_cents": 500_000,
                "coverage_type": "ALL_RISK",
            },
            "evidence_bundle_id": bundle_id,
            "risk_run_id": run_id,
            "notes": "Risk acceptable for claims tests",
        },
        headers=auth_headers,
    )
    assert (
        decision_resp.status_code in (200, 201)
    ), f"Failed to make decision: {decision_resp.text}"

    # Verify submission is QUOTED via DB
    from app.modules.underwriting.models import UnderwritingSubmission, SubmissionStatus

    db_submission = (
        db_session.query(UnderwritingSubmission)
        .filter(UnderwritingSubmission.id == submission_id)
        .first()
    )
    assert db_submission is not None
    assert db_submission.status == SubmissionStatus.QUOTED

    # 6. Bind policy
    effective_from = datetime.utcnow()
    effective_to = effective_from + timedelta(days=90)

    bind_resp = test_client.post(
        "/api/v3/underwriting/policies",
        json={
            "submission_id": submission_id,
            "effective_from": effective_from.isoformat() + "Z",
            "effective_to": effective_to.isoformat() + "Z",
            "policy_number": f"POL-{generate_ulid()[:8].upper()}",
        },
        headers=auth_headers,
    )
    assert bind_resp.status_code == 201, f"Failed to bind policy: {bind_resp.text}"
    policy = bind_resp.json()

    # Basic sanity checks
    assert policy["status"] == "ACTIVE"
    assert policy["policy_number"].startswith("POL-")

    return policy


class TestClaimsE2E:
    """End-to-end claims tests."""

    def test_complete_claims_flow(
        self,
        test_client: TestClient,
        auth_headers: dict,
        active_policy: dict,
        db_session: Session,
        test_tenant_and_user: dict,
    ):
        """Test complete claims flow from FNOL to payment and closure."""
        policy_id = active_policy["id"]
        user = test_tenant_and_user["user"]

        # Step 1: File FNOL
        fnol_body = {
            "loss_date": (datetime.utcnow() - timedelta(days=2)).isoformat() + "Z",
            "loss_location": "Port of Rotterdam",
            "loss_description": "Container damage during unloading",
            "loss_type": "DAMAGE",
            "estimated_loss_cents": 2_500_000,
            "currency": "USD",
            "reported_by": "claims@shipper.com",
        }

        resp = test_client.post(
            "/api/v3/claims",
            params={"policy_id": policy_id},
            json=fnol_body,
            headers=auth_headers,
        )
        assert resp.status_code == 201, f"Failed to file FNOL: {resp.text}"
        claim = resp.json()
        claim_id = claim["id"]

        assert claim["status"] == "FNOL_RECEIVED"
        assert claim["claim_number"].startswith("CLM-")
        assert claim["fnol"]["loss_type"] == "DAMAGE"

        # Verify FNOL snapshot is immutable later
        original_fnol = claim["fnol"]

        # Step 2: Assign adjuster
        adjuster = User(
            id=generate_ulid(),
            email="adjuster@test.com",
            password_hash="hashed",
            status="ACTIVE",
        )
        db_session.add(adjuster)
        db_session.commit()

        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/assign",
            params={"adjuster_id": adjuster.id},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to assign adjuster: {resp.text}"
        claim = resp.json()
        assert claim["assigned_adjuster_id"] == adjuster.id

        # Step 3: Begin investigation
        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/investigate",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to start investigation: {resp.text}"
        claim = resp.json()
        assert claim["status"] == "UNDER_INVESTIGATION"

        # Step 4: Request evidence
        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/evidence/request",
            params={
                "evidence_request": "Please provide damage photos and survey report"
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to request evidence: {resp.text}"
        claim = resp.json()
        assert claim["status"] == "AWAITING_EVIDENCE"

        # Step 5: Create and seal evidence bundle
        bundle_resp = test_client.post(
            "/api/v3/evidence/bundles",
            json={
                "name": f"Claim evidence for {claim['claim_number']}",
                "bundle_type": "CLAIM",
            },
            headers=auth_headers,
        )
        assert (
            bundle_resp.status_code == 201
        ), f"Failed to create evidence bundle: {bundle_resp.text}"
        bundle = bundle_resp.json()
        bundle_id = bundle["id"]

        seal_resp = test_client.post(
            f"/api/v3/evidence/bundles/{bundle_id}/seal",
            headers=auth_headers,
        )
        assert seal_resp.status_code == 200, f"Failed to seal bundle: {seal_resp.text}"

        # Step 6: Submit evidence
        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/evidence",
            params={"evidence_bundle_id": bundle_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to submit evidence: {resp.text}"
        claim = resp.json()
        assert claim["status"] == "UNDER_INVESTIGATION"
        assert claim["evidence_bundle_id"] == bundle_id

        # Step 7: Adjudicate - Approve
        adjudication_request = {
            "decision": "APPROVED",
            "reason": "Valid claim, covered under policy terms",
            "coverage_applies": True,
            "approved_amount_cents": 2_000_000,  # 2.5M - 500K deductible
            "exclusions_checked": ["war", "nuclear"],
            "calculation_method": "ACTUAL_LOSS",
            "adjustments": [],
            "notes": "Survey report confirms damage",
        }

        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/adjudicate",
            json=adjudication_request,
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to adjudicate claim: {resp.text}"
        claim = resp.json()
        assert claim["status"] == "APPROVED"
        assert claim["decision"] == "APPROVED"
        assert claim["approved_amount_cents"] == 2_000_000

        # Verify FNOL unchanged (immutable)
        assert claim["fnol"] == original_fnol

        # Step 8: Authorize payout (claim-level)
        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/authorize",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to authorize claim payout: {resp.text}"
        claim = resp.json()
        assert claim["status"] == "AUTHORIZED"

        # Step 9: Create payout proposal via PayoutService (no HTTP API yet)
        payout_service = PayoutService(db_session, AuditLedger(db_session))
        payout = payout_service.create_claim_payout(
            claim_id=claim_id, proposed_by=user.id
        )
        assert payout.amount_cents == 2_000_000
        assert payout.status.name == "PROPOSED"

        # Step 10: Approve payout (dual control - different user)
        approver = User(
            id=generate_ulid(),
            email="approver@test.com",
            password_hash="hashed",
            status="ACTIVE",
        )
        db_session.add(approver)
        db_session.commit()

        payout = payout_service.approve_payout(
            payout_id=payout.id,
            approved_by=approver.id,
        )
        assert payout.status.name == "APPROVED"

        # Step 11: Authorize payout (high-value dual control, different authorizer)
        authorizer = User(
            id=generate_ulid(),
            email="authorizer@test.com",
            password_hash="hashed",
            status="ACTIVE",
        )
        db_session.add(authorizer)
        db_session.commit()

        payout = payout_service.authorize_payout(
            payout_id=payout.id,
            authorized_by=authorizer.id,
        )
        assert payout.status.name == "AUTHORIZED"

        # Step 12: Process payment
        payout = payout_service.process_payment(
            payout_id=payout.id,
            payment_method="WIRE",
            processed_by=authorizer.id,
        )
        assert payout.status.name == "PROCESSING"

        # Step 13: Confirm payment
        payout = payout_service.confirm_payment(
            payout_id=payout.id,
            payment_reference="WIRE-12345",
            confirmation_data={"bank_ref": "ABCD1234"},
            confirmed_by=authorizer.id,
        )
        assert payout.status.name == "PAID"

        # Record payment against claim via API
        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/payment",
            params={"payout_id": payout.id},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to record claim payment: {resp.text}"
        claim = resp.json()
        assert claim["status"] == "PAID"
        assert claim["payout_id"] == payout.id

        # Step 14: Close claim
        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/close",
            params={"notes": "Claim settled successfully"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to close claim: {resp.text}"
        claim = resp.json()
        assert claim["status"] == "CLOSED"

        # Step 15: Verify full history
        history_resp = test_client.get(
            f"/api/v3/claims/{claim_id}/history",
            headers=auth_headers,
        )
        assert (
            history_resp.status_code == 200
        ), f"Failed to fetch claim history: {history_resp.text}"
        history = history_resp.json()

        statuses = [e.get("to_status") for e in history if e.get("to_status")]
        # Expect key states to appear at least once
        assert "FNOL_RECEIVED" in statuses
        assert "UNDER_INVESTIGATION" in statuses
        assert "AWAITING_EVIDENCE" in statuses
        assert "APPROVED" in statuses
        assert "AUTHORIZED" in statuses
        assert "PAID" in statuses
        assert "CLOSED" in statuses

        # Optional: verify decision pack endpoint works
        pack_resp = test_client.get(
            f"/api/v3/compliance/claims/{claim_id}/decision-pack",
            headers=auth_headers,
        )
        assert pack_resp.status_code in (200, 403, 404)  # May depend on permissions

    def test_claim_dual_control_enforced(
        self,
        test_client: TestClient,
        auth_headers: dict,
        active_policy: dict,
        db_session: Session,
        test_tenant_and_user: dict,
    ):
        """Test that dual control is enforced for high-value payouts."""
        policy_id = active_policy["id"]
        primary_user = test_tenant_and_user["user"]

        # Create and approve claim (happy path up to approval)
        fnol_body = {
            "loss_date": (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z",
            "loss_location": "Port of Rotterdam",
            "loss_description": "Major container damage",
            "loss_type": "DAMAGE",
            "estimated_loss_cents": 2_500_000,
            "currency": "USD",
            "reported_by": "claims@shipper.com",
        }

        resp = test_client.post(
            "/api/v3/claims",
            params={"policy_id": policy_id},
            json=fnol_body,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        claim = resp.json()
        claim_id = claim["id"]

        # Move to approved quickly (skip detailed investigation for brevity)
        adjudication_request = {
            "decision": "APPROVED",
            "reason": "Valid claim for dual-control test",
            "coverage_applies": True,
            "approved_amount_cents": 2_000_000,
            "exclusions_checked": [],
            "calculation_method": "ACTUAL_LOSS",
            "adjustments": [],
            "notes": "Auto-approved for test",
        }

        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/adjudicate",
            json=adjudication_request,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        claim = resp.json()
        assert claim["status"] == "APPROVED"

        # Create payout proposal
        payout_service = PayoutService(db_session, AuditLedger(db_session))
        payout = payout_service.create_claim_payout(
            claim_id=claim_id,
            proposed_by=primary_user.id,
        )

        # Try to approve own payout -> dual control violation
        with pytest.raises(DualControlViolationError):
            payout_service.approve_payout(
                payout_id=payout.id,
                approved_by=primary_user.id,
            )

        # Approve with different user -> OK
        approver = User(
            id=generate_ulid(),
            email="dual-approver@test.com",
            password_hash="hashed",
            status="ACTIVE",
        )
        db_session.add(approver)
        db_session.commit()

        payout = payout_service.approve_payout(
            payout_id=payout.id,
            approved_by=approver.id,
        )
        assert payout.status.name == "APPROVED"

        # High-value authorization must also be by different user than approver
        with pytest.raises(DualControlViolationError):
            payout_service.authorize_payout(
                payout_id=payout.id,
                authorized_by=approver.id,
            )

        authorizer = User(
            id=generate_ulid(),
            email="dual-authorizer@test.com",
            password_hash="hashed",
            status="ACTIVE",
        )
        db_session.add(authorizer)
        db_session.commit()

        payout = payout_service.authorize_payout(
            payout_id=payout.id,
            authorized_by=authorizer.id,
        )
        assert payout.status.name == "AUTHORIZED"

    def test_claim_declined_flow(
        self,
        test_client: TestClient,
        auth_headers: dict,
        active_policy: dict,
    ):
        """Test claim decline flow from FNOL to closure."""
        policy_id = active_policy["id"]

        # File claim
        fnol_body = {
            "loss_date": (datetime.utcnow() - timedelta(days=10)).isoformat() + "Z",
            "loss_location": "Port of Singapore",
            "loss_description": "Delay due to port congestion",
            "loss_type": "DELAY",
            "estimated_loss_cents": 500_000,
            "currency": "USD",
            "reported_by": "claims@shipper.com",
        }

        resp = test_client.post(
            "/api/v3/claims",
            params={"policy_id": policy_id},
            json=fnol_body,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        claim = resp.json()
        claim_id = claim["id"]

        # Adjudicate - Decline (e.g., outside coverage period)
        adjudication_request = {
            "decision": "DECLINED",
            "reason": "Loss occurred outside coverage period",
            "coverage_applies": False,
            "approved_amount_cents": 0,
            "exclusions_checked": ["timing"],
            "calculation_method": "NONE",
            "adjustments": [],
            "notes": "Policy effective dates do not cover loss date",
        }

        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/adjudicate",
            json=adjudication_request,
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to adjudicate (decline): {resp.text}"
        claim = resp.json()
        assert claim["status"] == "DECLINED"
        assert claim["decision"] == "DECLINED"

        # Close claim
        resp = test_client.post(
            f"/api/v3/claims/{claim_id}/close",
            params={"notes": "Claim declined - coverage not applicable"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Failed to close declined claim: {resp.text}"
        claim = resp.json()
        assert claim["status"] == "CLOSED"

