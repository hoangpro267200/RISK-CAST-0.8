"""
Integration Tests for Determinism

Tests that same inputs produce same outputs (hashes, seeds, etc.)
"""
import pytest
import time
from fastapi.testclient import TestClient

from app.modules.tenancy.models import Tenant, User, Membership, Role, RoleScope, TenantStatus
from app.modules.identity_access.models import Session as AuthSession
from app.shared.utils import generate_ulid


@pytest.fixture
def test_tenant_and_user(db_session):
    """Create test tenant and user"""
    tenant = Tenant(
        id=generate_ulid(),
        name="Test Tenant",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant)
    
    user = User(
        id=generate_ulid(),
        email="test@example.com",
        password_hash="hashed-password",
        status="ACTIVE"
    )
    db_session.add(user)
    
    role = Role(
        id=generate_ulid(),
        name="operator",
        scope=RoleScope.TENANT
    )
    db_session.add(role)
    
    membership = Membership(
        id=generate_ulid(),
        tenant_id=tenant.id,
        user_id=user.id,
        role_id=role.id,
        status="ACTIVE"
    )
    db_session.add(membership)
    
    auth_session = AuthSession(
        id=generate_ulid(),
        user_id=user.id,
        token="test-token-123",
        expires_at=None  # No expiration for tests
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


def create_assessment(client: TestClient, input_data: dict, auth_headers: dict):
    """Helper to create assessment"""
    response = client.post(
        "/api/v3/risk-assessments",
        json={"input_data": input_data},
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()


def wait_for_run_completion(client: TestClient, run_id: str, auth_headers: dict, max_wait: int = 30):
    """Wait for risk run to complete"""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = client.get(
            f"/api/v3/risk-runs/{run_id}",
            headers=auth_headers
        )
        if response.status_code == 200:
            run_data = response.json()
            status = run_data.get('status')
            if status in ['SUCCEEDED', 'FAILED']:
                return run_data
        time.sleep(1)
    raise TimeoutError(f"Run {run_id} did not complete within {max_wait} seconds")


def create_and_wait_run(client: TestClient, assessment_id: str, auth_headers: dict):
    """Helper to create run and wait for completion"""
    response = client.post(
        f"/api/v3/risk-assessments/{assessment_id}/runs",
        json={},
        headers=auth_headers
    )
    assert response.status_code in [201, 202]
    run = response.json()
    return wait_for_run_completion(client, run['id'], auth_headers)


class TestDeterminism:
    """Tests for determinism guarantees"""

    def test_same_input_produces_same_hash(
        self,
        client: TestClient,
        db_session,
        auth_headers: dict
    ):
        """Same input should produce identical result hash"""
        # Fixed input data
        input_data = {
            "origin": {
                "port": "CNSHA",
                "country": "CN",
                "coordinates": {"lat": 31.2304, "lon": 121.4737}
            },
            "destination": {
                "port": "USLAX",
                "country": "US",
                "coordinates": {"lat": 34.0522, "lon": -118.2437}
            },
            "cargo": {
                "type": "electronics",
                "value": 100000,
                "weight": 5000
            }
        }
        
        # Create first assessment and run
        assessment1 = create_assessment(client, input_data, auth_headers)
        run1 = create_and_wait_run(client, assessment1['id'], auth_headers)
        
        # Create second assessment with same input
        assessment2 = create_assessment(client, input_data, auth_headers)
        run2 = create_and_wait_run(client, assessment2['id'], auth_headers)
        
        # Hashes should match
        assert run1.get('result_hash') is not None
        assert run2.get('result_hash') is not None
        assert run1['result_hash'] == run2['result_hash'], \
            f"Hashes don't match: {run1['result_hash']} != {run2['result_hash']}"
        
        # Seeds should be same due to same input hash
        if run1.get('seed') is not None and run2.get('seed') is not None:
            assert run1['seed'] == run2['seed'], \
                f"Seeds don't match: {run1['seed']} != {run2['seed']}"

    def test_replay_produces_same_hash(
        self,
        client: TestClient,
        db_session,
        auth_headers: dict
    ):
        """Replaying a run with same parameters should produce identical hash"""
        input_data = {
            "origin": {
                "port": "CNSHA",
                "country": "CN",
                "coordinates": {"lat": 31.2304, "lon": 121.4737}
            },
            "destination": {
                "port": "USLAX",
                "country": "US",
                "coordinates": {"lat": 34.0522, "lon": -118.2437}
            },
            "cargo": {
                "type": "electronics",
                "value": 100000,
                "weight": 5000
            }
        }
        
        # Create and complete a run
        assessment = create_assessment(client, input_data, auth_headers)
        original_run = create_and_wait_run(client, assessment['id'], auth_headers)
        
        # Create another run with explicit same parameters
        run_params = {}
        if original_run.get('seed') is not None:
            run_params['seed'] = original_run['seed']
        if original_run.get('iterations') is not None:
            run_params['iterations'] = original_run['iterations']
        if original_run.get('model_version_id') is not None:
            run_params['model_version_id'] = original_run['model_version_id']
        
        response = client.post(
            f"/api/v3/risk-assessments/{assessment['id']}/runs",
            json=run_params,
            headers=auth_headers
        )
        assert response.status_code in [201, 202]
        replay_run = wait_for_run_completion(client, response.json()['id'], auth_headers)
        
        # Hashes should match
        assert original_run.get('result_hash') is not None
        assert replay_run.get('result_hash') is not None
        assert replay_run['result_hash'] == original_run['result_hash'], \
            f"Replay hash doesn't match: {replay_run['result_hash']} != {original_run['result_hash']}"
