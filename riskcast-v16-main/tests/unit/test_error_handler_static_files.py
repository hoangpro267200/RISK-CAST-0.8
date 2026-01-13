"""
Unit tests for Error Handler Static Files Fix (RC-C001)

CRITICAL: These tests verify that static file requests return proper
404 responses, not JSON error responses.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from app.middleware.error_handler_v2 import ErrorHandlerMiddleware


def create_test_app():
    """Create test FastAPI app with static files mount"""
    app = FastAPI()
    
    # Mount static files (simulate /assets mount)
    import tempfile
    import os
    from pathlib import Path
    
    temp_dir = Path(tempfile.mkdtemp())
    assets_dir = temp_dir / "assets"
    assets_dir.mkdir()
    
    # Create a test file
    test_file = assets_dir / "test.css"
    test_file.write_text("body { color: red; }")
    
    app.mount("/assets", StaticFiles(directory=str(assets_dir), html=False), name="assets")
    
    # Add error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)
    
    return app, assets_dir


class TestErrorHandlerStaticFiles:
    """Test suite for error handler static files fix"""
    
    def test_existing_static_file_returns_correctly(self):
        """
        Test that existing static files are served correctly.
        
        Reproduces: RC-C001 (positive case)
        """
        app, assets_dir = create_test_app()
        client = TestClient(app)
        
        # Create test file
        test_file = assets_dir / "test.css"
        test_file.write_text("body { color: red; }")
        
        response = client.get("/assets/test.css")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/css; charset=utf-8"
        assert "body { color: red; }" in response.text
    
    def test_missing_static_file_returns_404_not_json(self):
        """
        Test that missing static files return 404 HTML, not JSON.
        
        CRITICAL: This was the bug - 404s were returning JSON.
        
        Reproduces: RC-C001
        """
        app, _ = create_test_app()
        client = TestClient(app)
        
        response = client.get("/assets/missing.css")
        
        # Must return 404
        assert response.status_code == 404
        
        # Must NOT return JSON (the bug)
        content_type = response.headers.get("content-type", "")
        assert "application/json" not in content_type.lower()
        
        # Should return HTML 404 or plain text, not JSON
        # Starlette's StaticFiles returns HTML 404 by default
        assert "text/html" in content_type or "text/plain" in content_type
    
    def test_api_endpoint_returns_json_on_error(self):
        """
        Test that API endpoints still return JSON errors (not static files).
        
        This ensures the fix doesn't break normal API error handling.
        """
        app, _ = create_test_app()
        
        @app.get("/api/test")
        async def test_endpoint():
            raise HTTPException(status_code=404, detail="Not found")
        
        client = TestClient(app)
        response = client.get("/api/test")
        
        # API endpoints should return JSON
        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert "error" in data or "message" in data
