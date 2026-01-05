"""
Integration tests for complete workflows
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestInputToSummaryWorkflow:
    """Test complete workflow from input to summary"""
    
    @pytest.mark.slow
    def test_input_page_loads(self):
        """Test input page loads correctly"""
        response = client.get("/input_v20")
        assert response.status_code == 200
    
    @pytest.mark.slow
    def test_summary_page_loads(self):
        """Test summary page loads correctly"""
        response = client.get("/summary")
        assert response.status_code == 200
    
    @pytest.mark.slow
    def test_input_redirects_to_v20(self):
        """Test /input redirects to /input_v20"""
        response = client.get("/input", follow_redirects=False)
        assert response.status_code == 307
        assert "/input_v20" in response.headers.get("location", "")


class TestAPIAnalysisWorkflow:
    """Test API analysis workflow"""
    
    @pytest.mark.slow
    def test_risk_analysis_endpoint_exists(self):
        """Test risk analysis endpoint exists"""
        # This is a basic check - actual analysis may require valid data
        response = client.post(
            "/api/v1/risk/v2/analyze",
            json={
                "shipment": {
                    "trade_route": {
                        "pol": "VNSGN",
                        "pod": "USNYC",
                        "mode": "SEA"
                    }
                }
            }
        )
        # Should return either success or validation error, not 404
        assert response.status_code != 404
    
    @pytest.mark.slow
    def test_risk_analysis_validation(self):
        """Test risk analysis validation"""
        response = client.post(
            "/api/v1/risk/v2/analyze",
            json={}  # Empty payload should fail validation
        )
        # Should return validation error (400 or 422)
        assert response.status_code in [400, 422]
        data = response.json()
        assert data.get("success") == False or "error" in data

