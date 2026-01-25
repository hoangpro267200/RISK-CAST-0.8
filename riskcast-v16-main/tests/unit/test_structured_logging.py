"""
Unit Tests for Structured Logging System

Tests the core logging functionality including:
- Sensitive data masking
- Context management
- JSON formatting
- Custom logger methods
"""

import pytest
import json
import logging
from io import StringIO
from unittest.mock import patch

from app.core.logging import (
    mask_sensitive_data,
    JSONFormatter,
    StructuredLogger,
    setup_logging,
    get_logger,
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
    
    def test_mask_api_key_field(self):
        """Test masking of API key field."""
        data = {"api_key": "sk-abc123", "app_name": "test"}
        masked = mask_sensitive_data(data)
        
        assert masked["app_name"] == "test"
        assert masked["api_key"] == "***MASKED***"
    
    def test_mask_bearer_token(self):
        """Test masking of Bearer token in string."""
        data = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        masked = mask_sensitive_data(data)
        
        assert "***MASKED***" in masked
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked
    
    def test_mask_credit_card(self):
        """Test masking of credit card numbers."""
        data = "Card: 4111-1111-1111-1111"
        masked = mask_sensitive_data(data)
        
        assert "***MASKED***" in masked
        assert "4111-1111-1111-1111" not in masked
    
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
    
    def test_mask_list_of_dicts(self):
        """Test masking in list of dictionaries."""
        data = [
            {"user": "john", "password": "pass1"},
            {"user": "jane", "password": "pass2"}
        ]
        masked = mask_sensitive_data(data)
        
        assert masked[0]["user"] == "john"
        assert masked[0]["password"] == "***MASKED***"
        assert masked[1]["user"] == "jane"
        assert masked[1]["password"] == "***MASKED***"
    
    def test_mask_case_insensitive(self):
        """Test masking is case-insensitive."""
        data = {"PASSWORD": "secret", "Api_Key": "key123"}
        masked = mask_sensitive_data(data)
        
        assert masked["PASSWORD"] == "***MASKED***"
        assert masked["Api_Key"] == "***MASKED***"
    
    def test_no_masking_normal_fields(self):
        """Test that normal fields are not masked."""
        data = {
            "username": "john",
            "email": "john@example.com",
            "age": 30,
            "active": True
        }
        masked = mask_sensitive_data(data)
        
        assert masked == data
    
    def test_depth_limit(self):
        """Test recursion depth limit."""
        # Create deeply nested structure
        data = {"level1": {}}
        current = data["level1"]
        for i in range(20):
            current[f"level{i+2}"] = {}
            current = current[f"level{i+2}"]
        
        # Should not raise RecursionError
        masked = mask_sensitive_data(data)
        assert masked is not None


class TestJSONFormatter:
    """Test JSON formatter."""
    
    def test_json_formatter_basic(self):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        
        # Create log record
        logger = logging.getLogger("test")
        record = logger.makeRecord(
            "test", logging.INFO, "test.py", 10,
            "Test message", (), None
        )
        
        # Format
        output = formatter.format(record)
        log_dict = json.loads(output)
        
        assert log_dict["message"] == "Test message"
        assert log_dict["level"] == "INFO"
        assert log_dict["logger"] == "test"
    
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
    
    def test_json_formatter_with_exception(self):
        """Test JSON formatting with exception."""
        formatter = JSONFormatter()
        
        logger = logging.getLogger("test")
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            
            record = logger.makeRecord(
                "test", logging.ERROR, "test.py", 10,
                "Error occurred", (), exc_info
            )
            
            output = formatter.format(record)
            log_dict = json.loads(output)
            
            assert "exception" in log_dict
            assert log_dict["exception"]["type"] == "ValueError"
            assert log_dict["exception"]["message"] == "Test error"
            assert "traceback" in log_dict["exception"]
    
    def test_json_formatter_context(self):
        """Test JSON formatting includes context."""
        set_request_context(
            request_id="req-123",
            trace_id="trace-456",
            user_id="user-789",
            tenant_id="tenant-abc"
        )
        
        try:
            formatter = JSONFormatter()
            
            logger = logging.getLogger("test")
            record = logger.makeRecord(
                "test", logging.INFO, "test.py", 10,
                "Test message", (), None
            )
            
            output = formatter.format(record)
            log_dict = json.loads(output)
            
            assert log_dict["request_id"] == "req-123"
            assert log_dict["trace_id"] == "trace-456"
            assert log_dict["user_id"] == "user-789"
            assert log_dict["tenant_id"] == "tenant-abc"
        finally:
            clear_request_context()


class TestStructuredLogger:
    """Test custom structured logger."""
    
    def setup_method(self):
        """Set up test logger."""
        logging.setLoggerClass(StructuredLogger)
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        
        # Capture output
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
    
    def test_error_with_kwargs(self):
        """Test error logging with kwargs."""
        self.logger.error("Operation failed", operation="payment", error="timeout")
        
        log = self.get_last_log()
        assert log["message"] == "Operation failed"
        assert log["level"] == "ERROR"
        assert log["extra"]["operation"] == "payment"
    
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
        assert log["extra"]["event_type"] == "audit"
    
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
        assert log["extra"]["quote_id"] == "QTE-789"
    
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
        assert log["level"] == "ERROR"  # High severity = ERROR level


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
    
    def test_partial_context(self):
        """Test setting partial context."""
        set_request_context(request_id="req-123")
        
        assert request_id_ctx.get() == "req-123"
        assert trace_id_ctx.get() is None
        assert user_id_ctx.get() is None
        assert tenant_id_ctx.get() is None


class TestLoggerSetup:
    """Test logger setup and configuration."""
    
    def test_setup_logging_production(self):
        """Test production logging setup."""
        logger = setup_logging(
            service_name="test-service",
            environment="production",
            log_level="INFO",
            json_output=True
        )
        
        assert logger is not None
        assert logger.name == "test-service"
        assert logger.level == logging.INFO
    
    def test_setup_logging_development(self):
        """Test development logging setup."""
        logger = setup_logging(
            service_name="test-service",
            environment="development",
            log_level="DEBUG",
            json_output=False
        )
        
        assert logger is not None
        assert logger.level == logging.DEBUG
    
    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger("test.module")
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)


class TestSensitiveDataMaskingIntegration:
    """Integration tests for sensitive data masking in logging."""
    
    def setup_method(self):
        """Set up test logger."""
        logging.setLoggerClass(StructuredLogger)
        self.logger = logging.getLogger("test_masked")
        self.logger.setLevel(logging.DEBUG)
        
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(JSONFormatter())
        self.logger.addHandler(self.handler)
    
    def teardown_method(self):
        """Clean up."""
        self.logger.removeHandler(self.handler)
    
    def get_last_log(self) -> dict:
        """Get last log entry as dict."""
        output = self.stream.getvalue()
        lines = [line for line in output.strip().split('\n') if line]
        if lines:
            return json.loads(lines[-1])
        return {}
    
    def test_password_masked_in_log(self):
        """Test that passwords are masked in logs."""
        self.logger.info("User login", username="john", password="secret123")
        
        log = self.get_last_log()
        assert log["extra"]["username"] == "john"
        assert log["extra"]["password"] == "***MASKED***"
    
    def test_api_key_masked_in_log(self):
        """Test that API keys are masked in logs."""
        self.logger.info("API call", api_key="sk-abc123", endpoint="/users")
        
        log = self.get_last_log()
        assert log["extra"]["endpoint"] == "/users"
        assert log["extra"]["api_key"] == "***MASKED***"
    
    def test_nested_sensitive_data_masked(self):
        """Test that nested sensitive data is masked."""
        self.logger.info(
            "User data",
            user={
                "username": "john",
                "password": "secret",
                "profile": {
                    "email": "john@example.com",
                    "api_key": "key123"
                }
            }
        )
        
        log = self.get_last_log()
        user = log["extra"]["user"]
        assert user["username"] == "john"
        assert user["password"] == "***MASKED***"
        assert user["profile"]["email"] == "john@example.com"
        assert user["profile"]["api_key"] == "***MASKED***"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
