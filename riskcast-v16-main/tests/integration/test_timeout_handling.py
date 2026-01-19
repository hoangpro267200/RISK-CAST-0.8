"""
Integration tests for Request Timeout Middleware (RC-C005)

CRITICAL: These tests verify that timeouts work correctly:
- Long-running requests are cancelled
- 504 Gateway Timeout is returned
- Timeout values are configurable
"""
import pytest
import asyncio
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.timeout_middleware import TimeoutMiddleware


def create_test_app_with_timeout(timeout: float = 1.0):
    """Create test app with timeout middleware"""
    app = FastAPI()
    
    @app.get("/fast")
    async def fast_endpoint():
        return {"status": "ok", "message": "Fast response"}
    
    @app.get("/slow")
    async def slow_endpoint():
        # Simulate slow operation
        await asyncio.sleep(2.0)  # Longer than timeout
        return {"status": "ok", "message": "Slow response"}
    
    @app.get("/slow-but-within-timeout")
    async def slow_but_ok():
        await asyncio.sleep(0.5)  # Within timeout
        return {"status": "ok", "message": "Slow but OK"}
    
    # Add timeout middleware with short timeout for testing
    app.add_middleware(TimeoutMiddleware, default_timeout=timeout)
    
    return app


class TestTimeoutMiddleware:
    """Test suite for timeout middleware"""
    
    def test_fast_request_succeeds(self):
        """
        Test that fast requests complete successfully.
        """
        app = create_test_app_with_timeout(timeout=1.0)
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_slow_request_times_out(self):
        """
        Test that slow requests are cancelled and return 504.
        
        CRITICAL: This verifies timeout middleware works.
        """
        app = create_test_app_with_timeout(timeout=1.0)
        client = TestClient(app)
        
        response = client.get("/slow")
        
        # Should return 504 Gateway Timeout
        assert response.status_code == 504, \
            f"Expected 504, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should have error message about timeout
        assert "timeout" in str(data).lower() or "error" in data
    
    def test_request_within_timeout_succeeds(self):
        """
        Test that requests completing within timeout succeed.
        """
        app = create_test_app_with_timeout(timeout=1.0)
        client = TestClient(app)
        
        response = client.get("/slow-but-within-timeout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_static_files_bypass_timeout(self):
        """
        Test that static file requests bypass timeout.
        
        Static files should be fast and not need timeout protection.
        """
        from fastapi.staticfiles import StaticFiles
        import tempfile
        from pathlib import Path
        
        app = FastAPI()
        
        # Create temp static directory
        temp_dir = Path(tempfile.mkdtemp())
        static_dir = temp_dir / "static"
        static_dir.mkdir()
        
        # Create test file
        test_file = static_dir / "test.css"
        test_file.write_text("body { color: red; }")
        
        app.mount("/assets", StaticFiles(directory=str(static_dir), html=False), name="assets")
        app.add_middleware(TimeoutMiddleware, default_timeout=0.1)  # Very short timeout
        
        client = TestClient(app)
        
        # Static file request should succeed (bypasses timeout)
        response = client.get("/assets/test.css")
        
        # Should return 200 (or 404 if file not found, but not 504)
        assert response.status_code != 504, "Static files should not timeout"
