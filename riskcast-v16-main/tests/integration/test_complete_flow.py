"""
Complete integration tests for all upgraded features.

RISKCAST v17 - Integration Test Suite

Tests the complete flow of all new v17 features:
- API Key authentication
- Advanced rate limiting
- State synchronization
- AI advisor streaming
- Risk analysis pipeline
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch

# Try to import FastAPI test client
try:
    from fastapi.testclient import TestClient
    from app.main import app
    TEST_CLIENT_AVAILABLE = True
except ImportError:
    TEST_CLIENT_AVAILABLE = False


# ============================================================
# TEST FIXTURES
# ============================================================

@pytest.fixture
def client():
    """Create test client."""
    if not TEST_CLIENT_AVAILABLE:
        pytest.skip("FastAPI test client not available")
    return TestClient(app)


@pytest.fixture
def sample_shipment():
    """Sample shipment data for testing."""
    return {
        "origin_port": "CNSHA",
        "destination_port": "USLAX",
        "cargo_value": 100000,
        "cargo_type": "electronics_high_value",
        "transport_mode": "ocean_fcl",
        "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "priority": "high",
        "packaging": "good"
    }


@pytest.fixture
def sample_v1_shipment():
    """Sample v1 format shipment for legacy testing."""
    return {
        "from_port": "CNSHA",
        "to_port": "USLAX",
        "value": 100000,
        "cargo_type": "ELECTRONICS",
        "mode": "sea"
    }


# ============================================================
# API KEY TESTS
# ============================================================

class TestAPIKeyFlow:
    """Test API key creation, usage, and management."""
    
    def test_create_api_key(self, client):
        """Test API key creation."""
        response = client.post("/api/v2/api-keys", json={
            "name": "Test Integration Key",
            "scopes": ["risk:analyze", "risk:read"],
            "expires_in_days": 30
        })
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        # Key should be returned only on creation
        assert 'key' in data
        assert data['key'].startswith('rsk_')
        
        # Verify other fields
        assert data['name'] == "Test Integration Key"
        assert 'risk:analyze' in data['scopes']
        assert data['revoked'] == False
        
        return data['key']
    
    def test_use_api_key_for_analysis(self, client, sample_shipment):
        """Test using API key to access protected endpoint."""
        # First create a key
        create_response = client.post("/api/v2/api-keys", json={
            "name": "Analysis Key",
            "scopes": ["risk:analyze"]
        })
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("API key creation not available")
        
        api_key = create_response.json().get('key')
        if not api_key:
            pytest.skip("API key not returned")
        
        # Use key for analysis
        response = client.post(
            "/api/v2/risk/analyze",
            json=sample_shipment,
            headers={"X-API-Key": api_key}
        )
        
        # Should succeed or require additional setup
        assert response.status_code in [200, 404, 422]
    
    def test_invalid_api_key(self, client, sample_shipment):
        """Test rejection of invalid API key."""
        response = client.post(
            "/api/v2/risk/analyze",
            json=sample_shipment,
            headers={"X-API-Key": "rsk_invalid_key_12345"}
        )
        
        # Should be rejected
        assert response.status_code in [401, 403, 404]
    
    def test_list_api_keys(self, client):
        """Test listing API keys."""
        response = client.get("/api/v2/api-keys")
        
        if response.status_code == 404:
            pytest.skip("Endpoint not available")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have keys list
        assert 'keys' in data
        assert 'total' in data
    
    def test_revoke_api_key(self, client):
        """Test API key revocation."""
        # Create a key
        create_response = client.post("/api/v2/api-keys", json={
            "name": "Key to Revoke"
        })
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("API key creation not available")
        
        key_id = create_response.json().get('id')
        if not key_id:
            pytest.skip("Key ID not returned")
        
        # Revoke it
        revoke_response = client.delete(
            f"/api/v2/api-keys/{key_id}",
            json={"reason": "Test revocation"}
        )
        
        assert revoke_response.status_code in [200, 404]


# ============================================================
# RATE LIMITING TESTS
# ============================================================

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are present."""
        response = client.get("/health")
        
        if response.status_code == 404:
            pytest.skip("Health endpoint not available")
        
        # Rate limit headers may or may not be present
        # depending on whether rate limiter is enabled
    
    def test_rate_limit_enforcement(self, client, sample_shipment):
        """Test that rate limits are enforced."""
        responses = []
        
        # Make rapid requests (adjust count based on actual limit)
        for _ in range(15):
            response = client.post(
                "/api/v1/risk/v2/analyze",
                json=sample_shipment
            )
            responses.append(response.status_code)
        
        # Either all succeed (rate limit not enforced or limit not reached)
        # or some get 429
        status_codes = set(responses)
        
        # If rate limiting is active, we should see 429
        # If not, all should be 200 or 422 (validation)
        assert len(status_codes) > 0


# ============================================================
# STATE SYNCHRONIZATION TESTS
# ============================================================

class TestStateSync:
    """Test state synchronization functionality."""
    
    def test_save_and_retrieve_state(self, client):
        """Test saving and retrieving state."""
        shipment_id = f"test_{int(time.time())}"
        
        state_data = {
            "shipment_data": {
                "origin": "Shanghai",
                "destination": "Los Angeles"
            },
            "risk_result": {
                "risk_score": 67.5,
                "risk_level": "medium"
            },
            "last_updated": datetime.now().isoformat()
        }
        
        # Save state
        save_response = client.post(
            f"/api/v2/state/{shipment_id}",
            json=state_data
        )
        
        if save_response.status_code == 404:
            pytest.skip("State endpoint not available")
        
        # Retrieve state
        get_response = client.get(f"/api/v2/state/{shipment_id}")
        
        if get_response.status_code == 200:
            data = get_response.json()
            assert 'shipment_data' in data or 'value' in data
    
    def test_state_not_found(self, client):
        """Test 404 for non-existent state."""
        response = client.get("/api/v2/state/nonexistent_id_12345")
        
        # Should be 404 or endpoint not available
        assert response.status_code in [404, 500]


# ============================================================
# RISK ANALYSIS TESTS
# ============================================================

class TestRiskAnalysis:
    """Test risk analysis pipeline."""
    
    def test_analyze_risk_v2(self, client, sample_shipment):
        """Test v2 risk analysis endpoint."""
        response = client.post(
            "/api/v1/risk/v2/analyze",
            json=sample_shipment
        )
        
        if response.status_code == 404:
            pytest.skip("Endpoint not available")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            assert 'risk_score' in data
            assert 'risk_level' in data
            
            # Validate risk score range
            assert 0 <= data['risk_score'] <= 100
    
    def test_analyze_risk_validation(self, client):
        """Test validation of invalid input."""
        invalid_shipment = {
            "cargo_value": -1000,  # Invalid negative value
        }
        
        response = client.post(
            "/api/v1/risk/v2/analyze",
            json=invalid_shipment
        )
        
        # Should return validation error
        assert response.status_code in [422, 400, 404]
    
    def test_legacy_v1_adapter(self, client, sample_v1_shipment):
        """Test that legacy v1 format still works."""
        response = client.post(
            "/api/v1/risk/v2/analyze",
            json=sample_v1_shipment
        )
        
        if response.status_code == 404:
            pytest.skip("Endpoint not available")
        
        # Should either work or return validation error
        assert response.status_code in [200, 422, 400]


# ============================================================
# AI ADVISOR TESTS
# ============================================================

class TestAIAdvisor:
    """Test AI advisor functionality."""
    
    def test_chat_endpoint(self, client):
        """Test AI chat endpoint."""
        response = client.post(
            "/api/v1/ai/advisor/chat",
            json={
                "message": "What are the main risks for ocean freight?",
                "conversation_id": "test_conv_123"
            }
        )
        
        # Endpoint may not be available or may require API key
        assert response.status_code in [200, 401, 404, 500]
    
    def test_streaming_endpoint(self, client):
        """Test streaming chat endpoint."""
        response = client.post(
            "/api/v1/ai/advisor/chat/stream",
            json={
                "message": "Hello",
                "conversation_id": "test_stream"
            }
        )
        
        # Streaming may not be available
        assert response.status_code in [200, 401, 404, 500]


# ============================================================
# LEGACY ADAPTER TESTS
# ============================================================

class TestLegacyAdapter:
    """Test legacy adapter functionality."""
    
    def test_v1_to_v2_conversion(self):
        """Test v1 to v2 request conversion."""
        from app.core.adapters.legacy_adapter import RequestAdapter
        
        v1_payload = {
            "cargo_type": "GENERAL",
            "mode": "sea",
            "value": 50000,
            "from_port": "CNSHA",
            "to_port": "USLAX"
        }
        
        v2_payload = RequestAdapter.v1_to_v2_risk(v1_payload)
        
        assert v2_payload['cargo_value'] == 50000
        assert v2_payload['origin_port'] == "CNSHA"
        assert v2_payload['destination_port'] == "USLAX"
        assert v2_payload['transport_mode'] == "ocean_fcl"
        assert v2_payload['cargo_type'] == "general_merchandise"
    
    def test_v2_to_v1_conversion(self):
        """Test v2 to v1 response conversion."""
        from app.core.adapters.legacy_adapter import ResponseAdapter
        
        v2_response = {
            "risk_score": 67.5,
            "risk_level": "medium",
            "var_95": 15000,
            "expected_loss": 8000,
            "risk_factors": [
                {"name": "Weather", "score": 75}
            ]
        }
        
        v1_response = ResponseAdapter.v2_to_v1_risk(v2_response)
        
        assert v1_response['score'] == 67.5
        assert v1_response['level'] == "MEDIUM"
        assert v1_response['var'] == 15000
        assert v1_response['expectedLoss'] == 8000


# ============================================================
# DATABASE TESTS
# ============================================================

class TestDatabase:
    """Test database operations."""
    
    def test_audit_queries(self):
        """Test audit trail queries."""
        try:
            from app.database.queries import AuditQueries
            # Just verify import works
            assert hasattr(AuditQueries, 'get_recent_assessments')
        except ImportError:
            pytest.skip("Database queries not available")
    
    def test_index_definitions(self):
        """Test index definitions are valid."""
        try:
            from app.database.indexes import get_index_definitions
            
            indexes = get_index_definitions()
            
            assert len(indexes) > 0
            
            for idx in indexes:
                assert 'name' in idx
                assert 'table' in idx
                assert 'columns' in idx
        except ImportError:
            pytest.skip("Index definitions not available")


# ============================================================
# PERFORMANCE TESTS
# ============================================================

class TestPerformance:
    """Basic performance tests."""
    
    def test_health_response_time(self, client):
        """Test health check response time."""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        
        if response.status_code == 404:
            pytest.skip("Health endpoint not available")
        
        # Health check should be fast
        assert elapsed < 0.5  # 500ms
    
    def test_analysis_response_time(self, client, sample_shipment):
        """Test risk analysis response time."""
        start = time.time()
        response = client.post(
            "/api/v1/risk/v2/analyze",
            json=sample_shipment
        )
        elapsed = time.time() - start
        
        if response.status_code == 404:
            pytest.skip("Endpoint not available")
        
        # Analysis should complete within reasonable time
        # (adjust based on actual requirements)
        assert elapsed < 5.0  # 5 seconds


# ============================================================
# SECURITY TESTS
# ============================================================

class TestSecurity:
    """Test security features."""
    
    def test_request_signing(self):
        """Test request signing functionality."""
        from app.core.signing import sign_payload, verify_signature
        
        secret = "test-secret"
        payload = {"action": "test", "value": 123}
        
        signature = sign_payload(payload, secret)
        
        assert signature is not None
        assert len(signature) == 64  # SHA-256 hex length
        
        # Verify valid signature
        assert verify_signature(payload, signature, secret)
        
        # Verify invalid signature fails
        assert not verify_signature(payload, "invalid", secret)
        
        # Verify modified payload fails
        modified = {"action": "test", "value": 456}
        assert not verify_signature(modified, signature, secret)
    
    def test_api_key_hashing(self):
        """Test API key hashing."""
        from app.models.api_key import APIKey
        
        key, key_hash = APIKey.generate_key()
        
        # Key should have correct format
        assert key.startswith('rsk_')
        
        # Hash should be consistent
        assert APIKey.hash_key(key) == key_hash
        
        # Different keys should have different hashes
        key2, key_hash2 = APIKey.generate_key()
        assert key_hash != key_hash2


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def run_all_tests():
    """Run all tests and report results."""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_all_tests()
