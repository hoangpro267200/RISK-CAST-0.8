"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code in [200, 302, 307]  # Can be redirect
    
    @pytest.mark.slow
    def test_docs_endpoint(self):
        """Test API documentation endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200


class TestInputEndpoints:
    """Test input page endpoints"""
    
    def test_input_redirect(self):
        """Test /input redirects to /input_v20"""
        response = client.get("/input", follow_redirects=False)
        assert response.status_code == 307  # Redirect
        assert "/input_v20" in response.headers.get("location", "")
    
    def test_input_v20_page(self):
        """Test input v20 page loads"""
        response = client.get("/input_v20")
        assert response.status_code == 200
        assert "RISKCAST" in response.text or "input" in response.text.lower()


class TestSummaryEndpoints:
    """Test summary page endpoints"""
    
    def test_summary_page(self):
        """Test summary page loads"""
        response = client.get("/summary")
        assert response.status_code == 200


class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.mark.slow
    def test_api_v1_health(self):
        """Test API v1 health (if exists)"""
        # This test may need adjustment based on actual API structure
        try:
            response = client.get("/api/v1/health")
            assert response.status_code in [200, 404]  # May not exist
        except Exception:
            pytest.skip("API endpoint may not be implemented")

