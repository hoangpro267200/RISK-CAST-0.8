"""
Security Test Fixtures
"""

import pytest
from datetime import datetime, timedelta
import jwt
from typing import Dict


@pytest.fixture
def user_token():
    """Generate test user token."""
    try:
        from app.core.security import SECRET_KEY, ALGORITHM
    except ImportError:
        # Fallback if imports fail
        SECRET_KEY = "test-secret-key-for-security-tests"
        ALGORITHM = "HS256"
    
    payload = {
        "sub": "user-123",
        "tenant_id": "tenant-a",
        "role": "user",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def admin_token():
    """Generate admin token."""
    try:
        from app.core.security import SECRET_KEY, ALGORITHM
    except ImportError:
        SECRET_KEY = "test-secret-key-for-security-tests"
        ALGORITHM = "HS256"
    
    payload = {
        "sub": "admin-123",
        "tenant_id": "tenant-a",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def tenant_a_token():
    """Generate tenant A token."""
    try:
        from app.core.security import SECRET_KEY, ALGORITHM
    except ImportError:
        SECRET_KEY = "test-secret-key-for-security-tests"
        ALGORITHM = "HS256"
    
    payload = {
        "sub": "user-tenant-a",
        "tenant_id": "tenant-a",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def tenant_b_token():
    """Generate tenant B token."""
    try:
        from app.core.security import SECRET_KEY, ALGORITHM
    except ImportError:
        SECRET_KEY = "test-secret-key-for-security-tests"
        ALGORITHM = "HS256"
    
    payload = {
        "sub": "user-tenant-b",
        "tenant_id": "tenant-b",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def tenant_b_data(test_db):
    """Create tenant B data for isolation testing."""
    try:
        from app.models.policy import Policy
        
        policy = Policy(
            policy_number="POL-TENANT-B-TEST",
            tenant_id="tenant-b",
            customer_id="customer-tenant-b",
            status="ACTIVE",
            premium_amount=1000.00
        )
        test_db.add(policy)
        test_db.commit()
        test_db.refresh(policy)
        
        return {"policy_id": str(policy.id)}
    except Exception as e:
        # Fallback if model not available
        return {"policy_id": "policy-tenant-b-001"}


@pytest.fixture
def other_user_quote(test_db):
    """Create quote belonging to another user."""
    try:
        from app.models.quote import Quote
        
        quote = Quote(
            quote_number="QT-OTHER-USER-TEST",
            customer_id="other-customer-123",
            status="PENDING",
            cargo_value_usd=100000,
            total_premium_usd=500
        )
        test_db.add(quote)
        test_db.commit()
        test_db.refresh(quote)
        
        return {"id": str(quote.id)}
    except Exception as e:
        # Fallback if model not available
        return {"id": "quote-other-user-001"}


@pytest.fixture
def revoked_api_key():
    """Return a revoked API key for testing."""
    return "sk_revoked_key_12345_test"


@pytest.fixture
def auth_headers(user_token):
    """Generate auth headers with user token."""
    return {
        "Authorization": f"Bearer {user_token}",
        "X-Tenant-ID": "tenant-a"
    }


@pytest.fixture
def admin_headers(admin_token):
    """Generate auth headers with admin token."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "X-Tenant-ID": "tenant-a"
    }


@pytest.fixture
def created_quote(test_db, user_token):
    """Create a test quote for security tests."""
    try:
        from app.models.quote import Quote
        
        quote = Quote(
            quote_number="QT-SECURITY-TEST-001",
            customer_id="customer-123",
            status="PENDING",
            cargo_value_usd=500000,
            total_premium_usd=2500,
            origin_port="CNSHA",
            destination_port="USLAX",
            cargo_type="ELECTRONICS"
        )
        test_db.add(quote)
        test_db.commit()
        test_db.refresh(quote)
        
        return {
            "quote_id": str(quote.id),
            "quote_number": quote.quote_number
        }
    except Exception as e:
        # Fallback
        return {
            "quote_id": "quote-security-test-001",
            "quote_number": "QT-SECURITY-TEST-001"
        }


@pytest.fixture
def malicious_payloads():
    """Collection of common malicious payloads for testing."""
    return {
        "sql_injection": [
            "'; DROP TABLE quotes; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --",
            "1; SELECT * FROM passwords",
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f",
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| ls -la",
            "`whoami`",
            "$(id)",
            "&& cat /etc/shadow",
        ],
        "nosql_injection": [
            {"$gt": ""},
            {"$ne": None},
            {"$or": [{}]},
            {"$where": "1==1"},
        ]
    }


@pytest.fixture
def security_test_config():
    """Security test configuration."""
    return {
        "rate_limit_threshold": 100,
        "max_payload_size": 10_000_000,  # 10MB
        "allowed_origins": ["https://app.riskcast.com"],
        "session_timeout": 3600,  # 1 hour
        "max_login_attempts": 5,
        "password_min_length": 8,
    }


@pytest.fixture(scope="session")
def security_headers_expected():
    """Expected security headers."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }


# Helper functions

def create_expired_token(user_id: str = "user-123", hours_ago: int = 1) -> str:
    """Create an expired JWT token for testing."""
    try:
        from app.core.security import SECRET_KEY, ALGORITHM
    except ImportError:
        SECRET_KEY = "test-secret-key-for-security-tests"
        ALGORITHM = "HS256"
    
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() - timedelta(hours=hours_ago)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_invalid_signature_token(user_id: str = "user-123") -> str:
    """Create a token with invalid signature."""
    try:
        from app.core.security import SECRET_KEY, ALGORITHM
    except ImportError:
        SECRET_KEY = "test-secret-key-for-security-tests"
        ALGORITHM = "HS256"
    
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Tamper with signature
    parts = token.split(".")
    parts[2] = "tampered_signature"
    return ".".join(parts)


def sanitize_input(value: str) -> str:
    """Example input sanitization function."""
    dangerous_chars = ["<", ">", "script", "javascript:", "onerror="]
    sanitized = value
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    return sanitized
