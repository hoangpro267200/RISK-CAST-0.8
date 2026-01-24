"""
Integration Tests for Risk Assessment and Run Flow
Tests complete flow: create assessment -> run -> get result
RISKCAST V3 - Modular Monolith
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import time

from app.main import app
from app.modules.risk_assessments.models import RiskAssessment, AssessmentStatus
from app.modules.risk_runs.models import RiskRun, RiskRunStatus
from app.modules.tenancy.models import Tenant, User, Membership, Role, RoleScope, TenantStatus
from app.modules.identity_access.models import Session as AuthSession
from app.database import SessionLocal
from app.shared.utils import generate_ulid


@pytest.fixture
def test_tenant_and_user(db_session):
    """Create test tenant and user"""
    # Create tenant
    tenant = Tenant(
        id=generate_ulid(),
        name="Test Tenant",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant)
    
    # Create user
    user = User(
        id=generate_ulid(),
        email="test@example.com",
        password_hash="hashed-password",
        status="ACTIVE"
    )
    db_session.add(user)
    
    # Create role
    role = Role(
        id=generate_ulid(),
        name="operator",
        scope=RoleScope.TENANT
    )
    db_session.add(role)
    
    # Create membership
    membership = Membership(
        id=generate_ulid(),
        tenant_id=tenant.id,
        user_id=user.id,
        role_id=role.id,
        status="ACTIVE"
    )
    db_session.add(membership)
    
    # Create session
    auth_session = AuthSession(
        id=generate_ulid(),
        user_id=user.id,
        token="test-token-123",
        expires_at=datetime(2025, 12, 31, 23, 59, 59)
    )
    db_session.add(auth_session)
    
    db_session.commit()
    
    return {
        "tenant": tenant,
        "user": user,
        "role": role,
        "membership": membership,
        "session": auth_session
    }


@pytest.fixture
def auth_headers(test_tenant_and_user):
    """Get authentication headers"""
    return {
        "Authorization": "Bearer test-token-123",
        "X-Tenant-Id": test_tenant_and_user["tenant"].id
    }


class TestRiskFlow:
    """Tests for complete risk assessment and run flow"""
    
    @pytest.mark.asyncio
    async def test_full_risk_assessment_flow(self, client: AsyncClient, auth_headers, db_session):
        """Test complete flow: create assessment -> run -> get result"""
        # Step 1: Create assessment
        response = client.post(
            "/api/v3/risk-assessments",
            json={
                "input_data": {
                    "origin": {"port_code": "VNHPH", "country": "VN"},
                    "destination": {"port_code": "USLAX", "country": "US"},
                    "cargo": {
                        "type": "electronics",
                        "value_usd": 100000
                    }
                },
                "shipment_id": "SHIP-12345"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        assessment_data = response.json()
        assessment_id = assessment_data["id"]
        
        assert assessment_data["status"] == "READY"
        assert assessment_data["input_hash"] is not None
        assert len(assessment_data["input_hash"]) == 64  # SHA256 hex
        
        # Step 2: Create run
        response = await client.post(
            f"/api/v3/risk-assessments/{assessment_id}/runs",
            json={
                "iterations": 1000,
                "seed_strategy": "DETERMINISTIC_INPUT_HASH"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 202
        run_data = response.json()
        run_id = run_data["id"]
        
        assert run_data["status"] == "QUEUED"
        assert run_data["seed"] is not None
        
        # Step 3: Poll until complete (or timeout)
        max_wait = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = client.get(
                f"/api/v3/risk-runs/{run_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            run_data = response.json()
            status = run_data["status"]
            
            if status == "SUCCEEDED":
                # Verify result
                assert run_data["result_hash"] is not None
                assert len(run_data["result_hash"]) == 64
                assert run_data["result_json"] is not None
                assert run_data["completed_at"] is not None
                break
            elif status == "FAILED":
                assert run_data["error_json"] is not None
                pytest.fail(f"Run failed: {run_data.get('error_json')}")
            
            # Wait before next poll
            await asyncio.sleep(1)
        else:
            pytest.fail(f"Run did not complete within {max_wait} seconds")
    
    def test_get_assessment(self, client: TestClient, auth_headers, db_session):
        """Test getting assessment by ID"""
        # Create assessment first
        create_response = await client.post(
            "/api/v3/risk-assessments",
            json={
                "input_data": {
                    "origin": {"port_code": "VNHPH", "country": "VN"},
                    "destination": {"port_code": "USLAX", "country": "US"}
                }
            },
            headers=auth_headers
        )
        assessment_id = create_response.json()["id"]
        
        # Get assessment
        response = client.get(
            f"/api/v3/risk-assessments/{assessment_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == assessment_id
        assert data["input_hash"] is not None
    
    @pytest.mark.asyncio
    async def test_list_assessments(self, client: AsyncClient, auth_headers, db_session):
        """Test listing assessments"""
        # Create multiple assessments
        for i in range(3):
            client.post(
                "/api/v3/risk-assessments",
                json={
                    "input_data": {
                        "origin": {"port_code": "VNHPH", "country": "VN"},
                        "destination": {"port_code": "USLAX", "country": "US"},
                        "value": 100000 + i * 10000
                    }
                },
                headers=auth_headers
            )
        
        # List assessments
        response = client.get(
            "/api/v3/risk-assessments",
            headers=auth_headers,
            params={"skip": 0, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3
        assert data["total"] >= 3
        assert data["page"] == 1
    
    @pytest.mark.asyncio
    async def test_list_runs(self, client: AsyncClient, auth_headers, db_session):
        """Test listing runs"""
        # Create assessment and run
        create_response = await client.post(
            "/api/v3/risk-assessments",
            json={
                "input_data": {
                    "origin": {"port_code": "VNHPH", "country": "VN"},
                    "destination": {"port_code": "USLAX", "country": "US"}
                }
            },
            headers=auth_headers
        )
        assessment_id = create_response.json()["id"]
        
        # Create run
        run_response = client.post(
            f"/api/v3/risk-assessments/{assessment_id}/runs",
            json={},
            headers=auth_headers
        )
        run_id = run_response.json()["id"]
        
        # List runs
        response = await client.get(
            "/api/v3/risk-runs",
            headers=auth_headers,
            params={"assessment_id": assessment_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(run["id"] == run_id for run in data["items"])
    
    def test_tenant_isolation(self, client: TestClient, db_session):
        """Test that tenants cannot access each other's data"""
        # Create two tenants
        tenant1 = Tenant(id=generate_ulid(), name="Tenant 1", status="ACTIVE")
        tenant2 = Tenant(id=generate_ulid(), name="Tenant 2", status="ACTIVE")
        
        user1 = User(id=generate_ulid(), email="user1@test.com", password_hash="hash", status="ACTIVE")
        user2 = User(id=generate_ulid(), email="user2@test.com", password_hash="hash", status="ACTIVE")
        
        role = Role(id=generate_ulid(), name="operator", scope=RoleScope.TENANT)
        
        membership1 = Membership(id=generate_ulid(), tenant_id=tenant1.id, user_id=user1.id, role_id=role.id, status="ACTIVE")
        membership2 = Membership(id=generate_ulid(), tenant_id=tenant2.id, user_id=user2.id, role_id=role.id, status="ACTIVE")
        
        session1 = AuthSession(id=generate_ulid(), user_id=user1.id, token="token1", expires_at=datetime(2025, 12, 31))
        session2 = AuthSession(id=generate_ulid(), user_id=user2.id, token="token2", expires_at=datetime(2025, 12, 31))
        
        db_session.add_all([tenant1, tenant2, user1, user2, role, membership1, membership2, session1, session2])
        db_session.commit()
        
        # Create assessment for tenant1
        response1 = await client.post(
            "/api/v3/risk-assessments",
            json={"input_data": {"origin": "VN", "destination": "US"}},
            headers={"Authorization": "Bearer token1", "X-Tenant-Id": tenant1.id}
        )
        assessment_id = response1.json()["id"]
        
        # Try to access with tenant2's credentials
        response2 = client.get(
            f"/api/v3/risk-assessments/{assessment_id}",
            headers={"Authorization": "Bearer token2", "X-Tenant-Id": tenant2.id}
        )
        
        # Should return 404 (not found) or 403 (forbidden)
        assert response2.status_code in [404, 403]
