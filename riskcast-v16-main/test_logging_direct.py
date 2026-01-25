"""
Direct test of logging functionality without pytest

Run with: python test_logging_direct.py
"""

import json
import logging
from io import StringIO

from app.core.logging import (
    mask_sensitive_data,
    JSONFormatter,
    StructuredLogger,
    set_request_context,
    clear_request_context,
    request_id_ctx,
    trace_id_ctx,
)


def test_sensitive_data_masking():
    """Test sensitive data masking."""
    print("\n=== Testing Sensitive Data Masking ===")
    
    # Test 1: Password masking
    data = {"username": "john", "password": "secret123"}
    masked = mask_sensitive_data(data)
    assert masked["password"] == "***MASKED***"
    print("[PASS] Password masking works")
    
    # Test 2: API key masking
    data = {"api_key": "sk-abc123", "app_name": "test"}
    masked = mask_sensitive_data(data)
    assert masked["api_key"] == "***MASKED***"
    print("[PASS] API key masking works")
    
    # Test 3: Nested masking
    data = {
        "user": {
            "name": "John",
            "password": "secret123"
        },
        "api_key": "sk-abc"
    }
    masked = mask_sensitive_data(data)
    assert masked["user"]["password"] == "***MASKED***"
    assert masked["api_key"] == "***MASKED***"
    print("[PASS] Nested dictionary masking works")
    
    # Test 4: Bearer token masking
    data = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    masked = mask_sensitive_data(data)
    assert "***MASKED***" in masked
    print("[PASS] Bearer token masking works")


def test_json_formatter():
    """Test JSON formatter."""
    print("\n=== Testing JSON Formatter ===")
    
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
    print("[PASS] JSON formatting works")
    
    # Test with extra data
    record.extra_data = {"user_id": "123", "action": "login"}
    output = formatter.format(record)
    log_dict = json.loads(output)
    
    assert log_dict["extra"]["user_id"] == "123"
    print("[PASS] Extra data formatting works")


def test_context_management():
    """Test context management."""
    print("\n=== Testing Context Management ===")
    
    # Set context
    set_request_context(
        request_id="req-123",
        trace_id="trace-456",
        user_id="user-789",
        tenant_id="tenant-abc"
    )
    
    assert request_id_ctx.get() == "req-123"
    assert trace_id_ctx.get() == "trace-456"
    print("[PASS] Context setting works")
    
    # Clear context
    clear_request_context()
    assert request_id_ctx.get() is None
    print("[PASS] Context clearing works")


def test_structured_logger():
    """Test structured logger."""
    print("\n=== Testing Structured Logger ===")
    
    logging.setLoggerClass(StructuredLogger)
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # Test info with kwargs
    logger.info("User login", user_id="123", method="oauth")
    output = stream.getvalue()
    log_dict = json.loads(output.strip().split('\n')[0])
    
    assert log_dict["message"] == "User login"
    assert log_dict["extra"]["user_id"] == "123"
    print("[PASS] Info logging with kwargs works")
    
    # Clear stream
    stream.truncate(0)
    stream.seek(0)
    
    # Test audit method
    logger.audit("policy_created", "policy", "POL-123", user_id="user-456")
    output = stream.getvalue()
    log_dict = json.loads(output.strip().split('\n')[0])
    
    assert "AUDIT: policy_created" in log_dict["message"]
    assert log_dict["extra"]["entity_type"] == "policy"
    print("[PASS] Audit logging works")
    
    # Clear stream
    stream.truncate(0)
    stream.seek(0)
    
    # Test business event
    logger.business_event("quote_generated", quote_id="QTE-789")
    output = stream.getvalue()
    log_dict = json.loads(output.strip().split('\n')[0])
    
    assert "BUSINESS_EVENT: quote_generated" in log_dict["message"]
    assert log_dict["extra"]["event_type"] == "business"
    print("[PASS] Business event logging works")
    
    # Clear stream
    stream.truncate(0)
    stream.seek(0)
    
    # Test security event
    logger.security_event("failed_login", severity="high", username="john")
    output = stream.getvalue()
    log_dict = json.loads(output.strip().split('\n')[0])
    
    assert "SECURITY: failed_login" in log_dict["message"]
    assert log_dict["extra"]["severity"] == "high"
    print("[PASS] Security event logging works")


def test_full_integration():
    """Full integration test."""
    print("\n=== Full Integration Test ===")
    
    # Set up logger
    logging.setLoggerClass(StructuredLogger)
    logger = logging.getLogger("integration_test")
    logger.setLevel(logging.DEBUG)
    
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter(service_name="test-service"))
    logger.addHandler(handler)
    
    # Set context
    set_request_context(
        request_id="req-integration-123",
        user_id="user-integration-456"
    )
    
    # Log with sensitive data
    logger.info(
        "User authenticated",
        username="john",
        password="secret123",  # Should be masked
        api_key="sk-abc",      # Should be masked
        ip_address="203.0.113.42"
    )
    
    # Verify output
    output = stream.getvalue()
    log_dict = json.loads(output.strip().split('\n')[0])
    
    assert log_dict["message"] == "User authenticated"
    assert log_dict["request_id"] == "req-integration-123"
    assert log_dict["user_id"] == "user-integration-456"
    assert log_dict["extra"]["username"] == "john"
    assert log_dict["extra"]["password"] == "***MASKED***"
    assert log_dict["extra"]["api_key"] == "***MASKED***"
    assert log_dict["extra"]["ip_address"] == "203.0.113.42"
    
    print("[PASS] Full integration test passed")
    print("\nSample log output:")
    print(json.dumps(log_dict, indent=2))
    
    clear_request_context()


def main():
    """Run all tests."""
    print("=" * 60)
    print("STRUCTURED LOGGING SYSTEM - VERIFICATION TESTS")
    print("=" * 60)
    
    try:
        test_sensitive_data_masking()
        test_json_formatter()
        test_context_management()
        test_structured_logger()
        test_full_integration()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe structured logging system is working correctly.")
        print("You can now integrate it into your application.")
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
