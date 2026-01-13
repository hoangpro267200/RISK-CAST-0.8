"""
Integration tests for risk analysis endpoints

Tests the full API workflow including:
- Request/response format validation
- Standard response envelope
- Error handling
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRiskAnalyzeEndpoint:
    """Test /api/v1/risk/analyze endpoint"""
    
    def test_risk_analyze_success(self):
        """Test successful risk analysis"""
        payload = {
            "transport_mode": "ocean_fcl",
            "cargo_type": "electronics",
            "route": "vn_us",
            "incoterm": "FOB",
            "container": "40HC",
            "packaging": "palletized",
            "priority": "standard",
            "packages": 10,
            "etd": "2025-02-01",
            "eta": "2025-03-01",
            "transit_time": 30.0,
            "cargo_value": 50000.0
        }
        
        response = client.post("/api/v1/risk/analyze", json=payload)
        
        # Should return 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Check response envelope format
        data = response.json()
        
        # New envelope format (if implemented)
        if "success" in data:
            assert data["success"] is True
            assert "data" in data
            assert "meta" in data
            assert "error" in data
            assert data["error"] is None
            
            # Check meta has request_id
            if "meta" in data:
                meta = data["meta"]
                assert "ts" in meta
                assert "version" in meta
                # request_id may be in meta or header
                assert "request_id" in meta or "X-Request-ID" in response.headers
        
        # Check response has risk data
        result_data = data.get("data", data)  # Handle both envelope and direct format
        assert "result" in result_data or "risk_score" in result_data
    
    def test_risk_analyze_validation_error(self):
        """Test validation error handling"""
        # Missing required fields
        payload = {
            "transport_mode": "ocean_fcl"
            # Missing cargo_type, route, etc.
        }
        
        response = client.post("/api/v1/risk/analyze", json=payload)
        
        # Should return 422 or 400 (validation error)
        assert response.status_code in [400, 422], \
            f"Expected 400/422, got {response.status_code}: {response.text}"
        
        # Check error envelope format
        data = response.json()
        if "success" in data:
            assert data["success"] is False
            assert "error" in data
            assert data["error"] is not None
            assert "code" in data["error"]
            assert "message" in data["error"]


class TestRiskV2AnalyzeEndpoint:
    """Test /api/v1/risk/v2/analyze endpoint"""
    
    @pytest.mark.slow
    def test_risk_v2_analyze_success(self):
        """Test successful v2 risk analysis"""
        payload = {
            "transport_mode": "ocean_fcl",
            "cargo_type": "electronics",
            "route": "vn_us",
            "incoterm": "FOB",
            "container": "40HC",
            "packaging": "palletized",
            "priority": "standard",
            "packages": 10,
            "etd": "2025-02-01",
            "eta": "2025-03-01",
            "transit_time": 30.0,
            "cargo_value": 50000.0
        }
        
        response = client.post("/api/v1/risk/v2/analyze", json=payload)
        
        # Should return 200
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"
        
        # Check response has risk data
        data = response.json()
        assert "risk_score" in data or "overall_risk" in data or "data" in data


class TestRequestIDPropagation:
    """Test that request_id is propagated correctly"""
    
    def test_request_id_in_header(self):
        """Test that X-Request-ID header is present"""
        response = client.get("/")
        
        # Should have X-Request-ID header
        assert "X-Request-ID" in response.headers, \
            "Response should include X-Request-ID header"
        
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0, "Request ID should not be empty"
        assert len(request_id) == 36, "Request ID should be UUID format (36 chars)"
    
    def test_request_id_in_response_meta(self):
        """Test that request_id is in response meta (for API endpoints)"""
        payload = {
            "transport_mode": "ocean_fcl",
            "cargo_type": "electronics",
            "route": "vn_us",
            "incoterm": "FOB",
            "container": "40HC",
            "packaging": "palletized",
            "priority": "standard",
            "packages": 10,
            "etd": "2025-02-01",
            "eta": "2025-03-01",
            "transit_time": 30.0,
            "cargo_value": 50000.0
        }
        
        response = client.post("/api/v1/risk/analyze", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if envelope format is used
            if "meta" in data:
                meta = data["meta"]
                # request_id should be in meta
                assert "request_id" in meta, "Request ID should be in response meta"
                
                # Should match header
                header_request_id = response.headers.get("X-Request-ID")
                if header_request_id:
                    assert meta["request_id"] == header_request_id, \
                        "Request ID in meta should match header"


class TestErrorHandling:
    """Test error handling and standard error format"""
    
    def test_404_error_format(self):
        """Test 404 error returns standard format"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        
        # Check error envelope format
        data = response.json()
        if "success" in data:
            assert data["success"] is False
            assert "error" in data
            assert data["error"] is not None
            assert "code" in data["error"]
            assert "message" in data["error"]
    
    def test_500_error_format(self):
        """Test 500 error returns standard format (if triggered)"""
        # Try to trigger an error with invalid data
        # This may not always trigger 500, but if it does, check format
        payload = {
            "invalid": "data",
            "that": "will",
            "cause": "error"
        }
        
        response = client.post("/api/v1/risk/analyze", json=payload)
        
        # If 500, check format
        if response.status_code == 500:
            data = response.json()
            if "success" in data:
                assert data["success"] is False
                assert "error" in data
                assert data["error"] is not None

