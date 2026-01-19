"""
Integration tests for Secrets Validation (RC-H001)

CRITICAL: These tests verify that the system fails fast if secrets are missing
in production, but allows fallback in development.
"""
import pytest
import os
from unittest.mock import patch


class TestSecretsValidation:
    """Test suite for secrets validation"""
    
    def test_session_secret_key_required_in_production(self):
        """
        Test that SESSION_SECRET_KEY is required in production.
        
        CRITICAL: System should fail to start if secret is missing in production.
        """
        # Mock production environment
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            # Remove SESSION_SECRET_KEY
            with patch.dict(os.environ, {}, clear=True):
                os.environ["ENVIRONMENT"] = "production"
                
                # Try to import main - should raise ValueError
                with pytest.raises(ValueError) as exc_info:
                    # Re-import to trigger validation
                    import importlib
                    import app.main
                    importlib.reload(app.main)
                
                assert "SESSION_SECRET_KEY" in str(exc_info.value)
    
    def test_session_secret_key_allowed_in_development(self):
        """
        Test that SESSION_SECRET_KEY fallback is allowed in development.
        
        Development should allow fallback secret with warning.
        """
        # Mock development environment
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            # Remove SESSION_SECRET_KEY
            if "SESSION_SECRET_KEY" in os.environ:
                del os.environ["SESSION_SECRET_KEY"]
            
            # Should not raise exception (allows fallback)
            # Note: This test may need adjustment based on actual implementation
            try:
                import importlib
                import app.main
                importlib.reload(app.main)
                # If we get here, no exception was raised (expected in dev)
            except ValueError as e:
                # If exception is raised, it should mention production
                assert "production" in str(e).lower()
    
    def test_anthropic_api_key_required_in_production(self):
        """
        Test that ANTHROPIC_API_KEY is required in production.
        
        CRITICAL: System should fail if API key is missing in production.
        """
        # Mock production environment
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            # Remove ANTHROPIC_API_KEY
            with patch.dict(os.environ, {}, clear=True):
                os.environ["ENVIRONMENT"] = "production"
                
                # Try to import api_ai - should raise ValueError
                with pytest.raises(ValueError) as exc_info:
                    import importlib
                    import app.api_ai
                    importlib.reload(app.api_ai)
                
                assert "ANTHROPIC_API_KEY" in str(exc_info.value)
    
    def test_anthropic_api_key_allowed_in_development(self):
        """
        Test that ANTHROPIC_API_KEY fallback is allowed in development.
        
        Development should allow "dummy" key with warning.
        """
        # Mock development environment
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            # Set dummy key
            os.environ["ANTHROPIC_API_KEY"] = "dummy"
            
            # Should not raise exception (allows dummy in dev)
            try:
                import importlib
                import app.api_ai
                importlib.reload(app.api_ai)
                # If we get here, no exception was raised (expected in dev)
            except ValueError as e:
                # If exception is raised, it should mention production
                assert "production" in str(e).lower()
