"""
Standalone Unit Tests for Structured Logging System

Tests the core logging functionality without importing the full application.
Run with: python -m pytest tests/unit/test_logging_standalone.py -v
"""

import sys
import os
import pytest
import json
import logging
from io import StringIO

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import only the logging module
from app.core.logging import (
    mask_sensitive_data,
    JSONFormatter,
    StructuredLogger,
    set_request_context,
    clear_request_context,
    request_id_ctx,
    trace_id_ctx,
    user_id_ctx,
    tenant_id_ctx,
)


class TestSensitiveDataMasking:
    """Test sensitive data masking functionality."""
    
    def test_mask_password_field(self):
        """Test masking of password field."""
        data = {"username": "john", "password": "secret123"}
        masked = mask_sensitive_data(data)
        
        assert masked["username"] == "john"
        assert masked["password"] == "***MASKED***"
        print("✓ Password field masking works")
    
    def test_mask_api_key_field(self):
        """Test masking of API key field."""
        data = {"api_key": "sk-abc123", "app_name": "test"}
        masked = mask_sensitive_data(data)
        
        assert masked["app_name"] == "test"
        assert masked["api_key"] == "***MASKED***"
        print("✓ API key masking works")
    
    def test_mask_bearer_token(self):
        """Test masking of Bearer token in string."""
        data = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        masked = mask_sensitive_data(data)
        
        assert "***MASKED***" in masked
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked
        print("✓ Bearer token masking works")
    
    def test_mask_nested_dict(self):
        """Test masking in nested dictionaries."""
        data = {
            "user": {
                "name": "John",
                "password": "secret123"
            },
            "api_key": "sk-abc"
        }
        masked = mask_sensitive_data(data)
        
        assert masked["user"]["name"] == "John"
        assert masked["user"]["password"] == "***MASKED***"
        assert masked["api_key"] == "***MASKED***"
        print("✓ Nested dictionary masking works")


class TestJSONFormatter:
    """Test JSON formatter."""
    
    def test_json_formatter_basic(self):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        
        logger = logging.getLogger("test")
        record = logger.makeRecord(
            "test", logging.INFO, "test.py", 10,
            "Test message", (), None
        )
        
        output = formatter.format(record)
        log_dict = json.loads(output)
        
        assert log_dict["message"] == "Test message"
        assert log_dict["level"] == "INFO"
        assert log_dict["logger"] == "test"
        print("✓ JSON formatting works")
    
    def test_json_formatter_with_extra(self):
        """Test JSON formatting with extra data."""
        formatter = JSONFormatter()
        
        logger = logging.getLogger("test")
        record = logger.makeRecord(
            "test", logging.INFO, "test.py", 10,
            "Test message", (), None
        )
        record.extra_data = {"user_id": "123", "action": "login"}
        
        output = formatter.format(record)
        log_dict = json.loads(output)
        
        assert log_dict["extra"]["user_id"] == "123"
        assert log_dict["extra"]["action"] == "login"
        print("✓ Extra data formatting works")


class TestContextManagement:
    """Test logging context management."""
    
    def teardown_method(self):
        """Clean up context."""
        clear_request_context()
    
    def test_set_request_context(self):
        """Test setting request context."""
        set_request_context(
            request_id="req-123",
            trace_id="trace-456",
            user_id="user-789",
            tenant_id="tenant-abc"
        )
        
        assert request_id_ctx.get() == "req-123"
        assert trace_id_ctx.get() == "trace-456"
        assert user_id_ctx.get() == "user-789"
        assert tenant_id_ctx.get() == "tenant-abc"
        print("✓ Context setting works")
    
    def test_clear_request_context(self):
        """Test clearing request context."""
        set_request_context(
            request_id="req-123",
            trace_id="trace-456"
        )
        
        assert request_id_ctx.get() == "req-123"
        
        clear_request_context()
        
        assert request_id_ctx.get() is None
        assert trace_id_ctx.get() is None
        print("✓ Context clearing works")


class TestStructuredLogger:
    """Test custom structured logger."""
    
    def setup_method(self):
        """Set up test logger."""
        logging.setLoggerClass(StructuredLogger)
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(JSONFormatter())
        self.logger.addHandler(self.handler)
    
    def teardown_method(self):
        """Clean up."""
        self.logger.removeHandler(self.handler)
        clear_request_context()
    
    def get_last_log(self) -> dict:
        """Get last log entry as dict."""
        output = self.stream.getvalue()
        lines = [line for line in output.strip().split('\n') if line]
        if lines:
            return json.loads(lines[-1])
        return {}
    
    def test_info_with_kwargs(self):
        """Test info logging with kwargs."""
        self.logger.info("User login", user_id="123", method="oauth")
        
        log = self.get_last_log()
        assert log["message"] == "User login"
        assert log["extra"]["user_id"] == "123"
        assert log["extra"]["method"] == "oauth"
        print("✓ Info logging with kwargs works")
    
    def test_audit_method(self):
        """Test audit logging method."""
        self.logger.audit(
            "policy_created",
            "policy",
            "POL-123",
            user_id="user-456",
            premium=150000.00
        )
        
        log = self.get_last_log()
        assert "AUDIT: policy_created" in log["message"]
        assert log["extra"]["action"] == "policy_created"
        assert log["extra"]["entity_type"] == "policy"
        assert log["extra"]["entity_id"] == "POL-123"
        print("✓ Audit logging works")
    
    def test_business_event_method(self):
        """Test business event logging method."""
        self.logger.business_event(
            "quote_generated",
            quote_id="QTE-789",
            premium=125000.00
        )
        
        log = self.get_last_log()
        assert "BUSINESS_EVENT: quote_generated" in log["message"]
        assert log["extra"]["event_name"] == "quote_generated"
        assert log["extra"]["event_type"] == "business"
        print("✓ Business event logging works")
    
    def test_security_event_method(self):
        """Test security event logging method."""
        self.logger.security_event(
            "failed_login",
            severity="high",
            username="john",
            ip="203.0.113.42"
        )
        
        log = self.get_last_log()
        assert "SECURITY: failed_login" in log["message"]
        assert log["extra"]["event_type"] == "security"
        assert log["extra"]["severity"] == "high"
        print("✓ Security event logging works")


def test_integration():
    """Integration test demonstrating full workflow."""
    print("\n=== Integration Test ===")
    
    # 1. Set up logger
    logging.setLoggerClass(StructuredLogger)
    logger = logging.getLogger("integration_test")
    logger.setLevel(logging.DEBUG)
    
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter(service_name="test-service"))
    logger.addHandler(handler)
    
    # 2. Set context
    set_request_context(
        request_id="req-integration-123",
        user_id="user-integration-456"
    )
    
    # 3. Log with sensitive data
    logger.info(
        "User authenticated",
        username="john",
        password="secret123",  # This should be masked
        api_key="sk-abc",      # This should be masked
        ip_address="203.0.113.42"
    )
    
    # 4. Verify output
    output = stream.getvalue()
    log_dict = json.loads(output.strip().split('\n')[0])
    
    assert log_dict["message"] == "User authenticated"
    assert log_dict["request_id"] == "req-integration-123"
    assert log_dict["user_id"] == "user-integration-456"
    assert log_dict["extra"]["username"] == "john"
    assert log_dict["extra"]["password"] == "***MASKED***"
    assert log_dict["extra"]["api_key"] == "***MASKED***"
    assert log_dict["extra"]["ip_address"] == "203.0.113.42"
    
    print("✓ Full integration test passed")
    print("\nSample log output:")
    print(json.dumps(log_dict, indent=2))
    
    clear_request_context()


if __name__ == "__main__":
    print("Running Structured Logging Tests...")
    print("=" * 60)
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])
