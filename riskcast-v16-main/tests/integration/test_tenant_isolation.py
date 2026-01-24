"""
Integration Tests for Tenant Isolation

Tests that tenants cannot access each other's data and that
API endpoints respect tenant boundaries.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.modules.tenancy.models import Tenant, User, Membership, Role, RoleScope, TenantStatus
from app.modules.identity_access.models import Session as AuthSession
from app.modules.claims.models import Claim, ClaimStatus
from app.shared.utils import generate_ulid


@pytest.fixture
def two_tenants_and_users(db_session):
    """Create two separate tenants with users"""
    # Tenant 1
    tenant1 = Tenant(
        id=generate_ulid(),
        name="Tenant 1",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant1)
    
    user1 = User(
        id=generate_ulid(),
        email="user1@test.com",
        password_hash="hash",
        status="ACTIVE"
    )
    db_session.add(user1)
    
    # Tenant 2
    tenant2 = Tenant(
        id=generate_ulid(),
        name="Tenant 2",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant2)
    
    user2 = User(
        id=generate_ulid(),
        email="user2@test.com",
        password_hash="hash",
        status="ACTIVE"
    )
    db_session.add(user2)
    
    # Create role
    role = Role(
        id=generate_ulid(),
        name="operator",
        scope=RoleScope.TENANT
    )
    db_session.add(role)
    
    # Memberships
    membership1 = Membership(
        id=generate_ulid(),
        tenant_id=tenant1.id,
        user_id=user1.id,
        role_id=role.id,
        status="ACTIVE"
    )
    db_session.add(membership1)
    
    membership2 = Membership(
        id=generate_ulid(),
        tenant_id=tenant2.id,
        user_id=user2.id,
        role_id=role.id,
        status="ACTIVE"
    )
    db_session.add(membership2)
    
    # Sessions
    session1 = AuthSession(
        id=generate_ulid(),
        user_id=user1.id,
        token="token1",
        expires_at=datetime(2025, 12, 31, 23, 59, 59)
    )
    db_session.add(session1)
    
    session2 = AuthSession(
        id=generate_ulid(),
        user_id=user2.id,
        token="token2",
        expires_at=datetime(2025, 12, 31, 23, 59, 59)
    )
    db_session.add(session2)
    
    db_session.commit()
    
    return {
        "tenant1": tenant1,
        "user1": user1,
        "session1": session1,
        "tenant1_headers": {
            "Authorization": "Bearer token1",
            "X-Tenant-Id": tenant1.id
        },
        "tenant2": tenant2,
        "user2": user2,
        "session2": session2,
        "tenant2_headers": {
            "Authorization": "Bearer token2",
            "X-Tenant-Id": tenant2.id
        }
    }


class TestTenantIsolation:
    """Tests for tenant isolation"""

    def test_cannot_access_other_tenant_data(
        self,
        client: TestClient,
        db_session,
        two_tenants_and_users: dict
    ):
        """Users cannot access resources from other tenants"""
        tenant1_headers = two_tenants_and_users["tenant1_headers"]
        tenant2_headers = two_tenants_and_users["tenant2_headers"]
        
        # Create assessment in tenant 1
        response = client.post(
            "/api/v3/risk-assessments",
            json={"input_data": {"origin": "VN", "destination": "US"}},
            headers=tenant1_headers
        )
        assert response.status_code == 201
        assessment_id = response.json()["id"]
        
        # Try to access from tenant 2
        response = client.get(
            f"/api/v3/risk-assessments/{assessment_id}",
            headers=tenant2_headers
        )
        # Should return 404 (not found) - tenant isolation
        assert response.status_code == 404, \
            f"Expected 404 but got {response.status_code}. Tenant isolation may be broken."

    def test_audit_events_are_tenant_scoped(
        self,
        client: TestClient,
        db_session,
        two_tenants_and_users: dict
    ):
        """Audit queries only return events for own tenant"""
        tenant1_headers = two_tenants_and_users["tenant1_headers"]
        tenant2_headers = two_tenants_and_users["tenant2_headers"]
        tenant1_id = two_tenants_and_users["tenant1"].id
        tenant2_id = two_tenants_and_users["tenant2"].id
        
        # Create assessment in tenant 1
        response = client.post(
            "/api/v3/risk-assessments",
            json={"input_data": {"origin": "VN", "destination": "US"}},
            headers=tenant1_headers
        )
        assessment1_id = response.json()["id"]
        
        # Create assessment in tenant 2
        response = client.post(
            "/api/v3/risk-assessments",
            json={"input_data": {"origin": "CN", "destination": "US"}},
            headers=tenant2_headers
        )
        assessment2_id = response.json()["id"]
        
        # Query audit events from tenant 1
        response = client.get(
            "/api/v3/audit/events",
            headers=tenant1_headers
        )
        
        if response.status_code == 200:
            events = response.json()
            # May be paginated
            if isinstance(events, dict) and 'items' in events:
                events = events['items']
            elif not isinstance(events, list):
                events = []
            
            # All events should belong to tenant 1
            for event in events:
                event_tenant_id = event.get('tenant_id')
                if event_tenant_id:
                    assert event_tenant_id == tenant1_id, \
                        f"Event {event.get('id')} belongs to wrong tenant: {event_tenant_id} != {tenant1_id}"
        
        # Query audit events from tenant 2
        response = client.get(
            "/api/v3/audit/events",
            headers=tenant2_headers
        )
        
        if response.status_code == 200:
            events = response.json()
            # May be paginated
            if isinstance(events, dict) and 'items' in events:
                events = events['items']
            elif not isinstance(events, list):
                events = []
            
            # All events should belong to tenant 2
            for event in events:
                event_tenant_id = event.get('tenant_id')
                if event_tenant_id:
                    assert event_tenant_id == tenant2_id, \
                        f"Event {event.get('id')} belongs to wrong tenant: {event_tenant_id} != {tenant2_id}"

    def test_cannot_access_other_tenant_runs(
        self,
        client: TestClient,
        db_session,
        two_tenants_and_users: dict
    ):
        """Users cannot access risk runs from other tenants"""
        tenant1_headers = two_tenants_and_users["tenant1_headers"]
        tenant2_headers = two_tenants_and_users["tenant2_headers"]
        
        # Create assessment and run in tenant 1
        response = client.post(
            "/api/v3/risk-assessments",
            json={"input_data": {"origin": "VN", "destination": "US"}},
            headers=tenant1_headers
        )
        assessment_id = response.json()["id"]
        
        response = client.post(
            f"/api/v3/risk-assessments/{assessment_id}/runs",
            json={},
            headers=tenant1_headers
        )
        run_id = response.json()["id"]
        
        # Try to access run from tenant 2
        response = client.get(
            f"/api/v3/risk-runs/{run_id}",
            headers=tenant2_headers
        )
        # Should return 404 (not found)
        assert response.status_code == 404, \
            f"Expected 404 but got {response.status_code}. Tenant isolation may be broken."

    def test_claim_isolation(
        self,
        client: TestClient,
        db_session,
        two_tenants_and_users: dict
    ):
        """Test that claims are isolated between tenants."""
        tenant1 = two_tenants_and_users["tenant1"]
        tenant1_headers = two_tenants_and_users["tenant1_headers"]
        tenant2_headers = two_tenants_and_users["tenant2_headers"]

        # Create a minimal claim in tenant 1 directly in DB
        claim = Claim(
            id=generate_ulid(),
            tenant_id=tenant1.id,
            claim_number="CLM-TENANT1-TEST",
            policy_id="POL-DUMMY",
            status=ClaimStatus.FNOL_RECEIVED,
            fnol_json={
                "loss_date": datetime.utcnow().isoformat() + "Z",
                "loss_location": "Test Port",
                "loss_description": "Test loss",
                "loss_type": "DAMAGE",
                "estimated_loss_cents": 100000,
                "currency": "USD",
                "reported_by": "user1@test.com",
            },
        )
        db_session.add(claim)
        db_session.commit()

        # Tenant 1 can view their claim
        response = client.get(
            f"/api/v3/claims/{claim.id}",
            headers=tenant1_headers,
        )
        assert response.status_code == 200, \
            f"Tenant 1 should see their own claim, got {response.status_code}"

        # Tenant 2 cannot view tenant 1's claim
        response = client.get(
            f"/api/v3/claims/{claim.id}",
            headers=tenant2_headers,
        )
        assert response.status_code == 404, \
            f"Expected 404 for cross-tenant claim access, got {response.status_code}"

        # Tenant 2 cannot modify tenant 1's claim
        response = client.post(
            f"/api/v3/claims/{claim.id}/investigate",
            headers=tenant2_headers,
        )
        assert response.status_code in (403, 404), \
            f"Expected 403/404 for cross-tenant claim modification, got {response.status_code}"

    def test_evidence_bundle_isolation(
        self,
        client: TestClient,
        db_session,
        two_tenants_and_users: dict
    ):
        """Test that evidence bundles are isolated between tenants."""
        tenant1_headers = two_tenants_and_users["tenant1_headers"]
        tenant2_headers = two_tenants_and_users["tenant2_headers"]

        # Create bundle in tenant 1
        response = client.post(
            "/api/v3/evidence/bundles",
            json={"name": "Tenant 1 Bundle", "bundle_type": "UNDERWRITING"},
            headers=tenant1_headers,
        )
        assert response.status_code == 201, \
            f"Failed to create evidence bundle for tenant 1: {response.text}"
        bundle = response.json()
        bundle_id = bundle["id"]

        # Tenant 1 can access their bundle
        response = client.get(
            f"/api/v3/evidence/bundles/{bundle_id}",
            headers=tenant1_headers,
        )
        assert response.status_code == 200, \
            f"Tenant 1 should see their bundle, got {response.status_code}"

        # Tenant 2 cannot access tenant 1's bundle
        response = client.get(
            f"/api/v3/evidence/bundles/{bundle_id}",
            headers=tenant2_headers,
        )
        assert response.status_code == 404, \
            f"Expected 404 for cross-tenant bundle access, got {response.status_code}"

        # Tenant 2 cannot seal tenant 1's bundle
        response = client.post(
            f"/api/v3/evidence/bundles/{bundle_id}/seal",
            headers=tenant2_headers,
        )
        assert response.status_code == 404, \
            f"Expected 404 for cross-tenant bundle seal, got {response.status_code}"

    def test_cross_tenant_reference_prevented(
        self,
        client: TestClient,
        db_session,
        two_tenants_and_users: dict
    ):
        """Test that cross-tenant references (e.g. submissions) are prevented."""
        tenant1_headers = two_tenants_and_users["tenant1_headers"]
        tenant2_headers = two_tenants_and_users["tenant2_headers"]

        # Create assessment in tenant 1
        response = client.post(
            "/api/v3/risk-assessments",
            json={"input_data": {"origin": "VN", "destination": "US"}},
            headers=tenant1_headers,
        )
        assert response.status_code == 201
        assessment = response.json()
        assessment_id = assessment["id"]

        # Tenant 2 tries to create submission referencing tenant 1's assessment
        submission_request = {
            "risk_assessment_id": assessment_id,
            "requested_coverage_json": {"coverage_type": "ALL_RISK"},
        }

        response = client.post(
            "/api/v3/underwriting/submissions",
            json=submission_request,
            headers=tenant2_headers,
        )
        # Should fail - assessment not found for tenant 2
        assert response.status_code == 404, \
            f"Expected 404 for cross-tenant submission reference, got {response.status_code}"

    def test_global_corridors_accessible_to_all_tenants(
        self,
        client: TestClient,
        db_session,
        two_tenants_and_users: dict
    ):
        """
        Test that global resources (corridor intelligence) are accessible to all tenants.

        This does not assert existence of specific corridors, but verifies that
        both tenants see the same result for a given global resource.
        """
        tenant1_headers = two_tenants_and_users["tenant1_headers"]
        tenant2_headers = two_tenants_and_users["tenant2_headers"]

        # Use a well-known port code; underlying data may or may not exist,
        # but both tenants should see the same status code.
        port_code = "NLRTM"

        response_a = client.get(
            f"/api/v3/corridors/ports/{port_code}",
            headers=tenant1_headers,
        )
        response_b = client.get(
            f"/api/v3/corridors/ports/{port_code}",
            headers=tenant2_headers,
        )

        assert response_a.status_code == response_b.status_code, (
            f"Global corridor endpoint should behave the same for all tenants, "
            f"got {response_a.status_code} vs {response_b.status_code}"
        )
