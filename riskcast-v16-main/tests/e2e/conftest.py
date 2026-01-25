"""
End-to-End Test Fixtures and Configuration
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from datetime import datetime, timedelta
import jwt


# ============================================================================
# Async Client Fixture
# ============================================================================

@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for E2E tests.
    
    Uses the actual FastAPI app with test database.
    """
    try:
        from app.main import app
        from httpx import AsyncClient
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    except ImportError:
        # Fallback: create client without app
        async with AsyncClient(base_url="http://localhost:8000") as client:
            yield client


@pytest.fixture(scope="function")
def test_db():
    """
    Create test database session.
    
    Uses in-memory SQLite for fast E2E tests.
    """
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.database import Base
        
        # Create in-memory test database
        engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    except ImportError:
        # No database available
        yield None


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def auth_headers() -> dict:
    """
    Generate authentication headers for regular user.
    """
    try:
        from app.core.security import create_access_token
        
        token = create_access_token(
            subject="test-user-001",
            role="user",
            tenant_id="test-tenant-001"
        )
    except ImportError:
        # Fallback: create JWT manually
        payload = {
            "sub": "test-user-001",
            "role": "user",
            "tenant_id": "test-tenant-001",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
    
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "test-tenant-001",
        "Content-Type": "application/json"
    }


@pytest.fixture
def admin_headers() -> dict:
    """
    Generate authentication headers for admin user.
    """
    try:
        from app.core.security import create_access_token
        
        token = create_access_token(
            subject="admin-user-001",
            role="admin",
            tenant_id="admin-tenant"
        )
    except ImportError:
        payload = {
            "sub": "admin-user-001",
            "role": "admin",
            "tenant_id": "admin-tenant",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
    
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "admin-tenant",
        "Content-Type": "application/json"
    }


@pytest.fixture
def customer_headers() -> dict:
    """
    Generate authentication headers for customer user.
    """
    try:
        from app.core.security import create_access_token
        
        token = create_access_token(
            subject="customer-user-001",
            role="customer",
            tenant_id="customer-tenant-001"
        )
    except ImportError:
        payload = {
            "sub": "customer-user-001",
            "role": "customer",
            "tenant_id": "customer-tenant-001",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
    
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "customer-tenant-001",
        "Content-Type": "application/json"
    }


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_quote_request() -> dict:
    """Sample quote request data."""
    from datetime import date, timedelta
    
    return {
        "origin_port": "CNSHA",
        "destination_port": "USLAX",
        "cargo_type": "ELECTRONICS",
        "cargo_value_usd": 500000,
        "container_count": 2,
        "departure_date": (date.today() + timedelta(days=14)).isoformat(),
        "arrival_date": (date.today() + timedelta(days=35)).isoformat(),
        "coverage_type": "ALL_RISKS",
        "deductible_type": "PERCENTAGE",
        "deductible_value": 0.01,
        "carrier_code": "MAEU"
    }


@pytest.fixture
def sample_claim_request() -> dict:
    """Sample claim request data."""
    from datetime import date, timedelta
    
    return {
        "loss_date": (date.today() - timedelta(days=5)).isoformat(),
        "loss_type": "CARGO_DAMAGE",
        "loss_location": "Port of Los Angeles",
        "loss_description": "Container dropped during unloading.",
        "claimed_amount_usd": 50000,
        "contact_name": "John Doe",
        "contact_phone": "+1-555-123-4567",
        "contact_email": "john.doe@example.com"
    }


@pytest.fixture
def sample_customer_registration() -> dict:
    """Sample customer registration data."""
    import random
    
    random_id = random.randint(10000, 99999)
    
    return {
        "company_name": f"E2E Test Company {random_id}",
        "legal_name": f"E2E Test Company {random_id} Inc.",
        "registration_number": f"REG{random_id}",
        "tax_id": f"TAX{random_id}",
        "address_line_1": "123 Test Street",
        "city": "San Francisco",
        "state_province": "CA",
        "postal_code": "94105",
        "country": "US",
        "primary_contact_name": "Test User",
        "primary_contact_email": f"test{random_id}@example.com",
        "primary_contact_phone": "+1-555-000-0000",
        "industry": "LOGISTICS",
        "annual_shipment_volume": 100,
        "average_cargo_value_usd": 100000
    }


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_token(
    user_id: str = "test-user",
    role: str = "user",
    tenant_id: str = "test-tenant",
    hours_valid: int = 24
) -> str:
    """
    Create a test JWT token.
    
    Args:
        user_id: User identifier
        role: User role (user, admin, customer)
        tenant_id: Tenant identifier
        hours_valid: Token validity in hours
    
    Returns:
        JWT token string
    """
    payload = {
        "sub": user_id,
        "role": role,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(hours=hours_valid)
    }
    
    try:
        from app.core.security import SECRET_KEY, ALGORITHM
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    except ImportError:
        return jwt.encode(payload, "test-secret-key", algorithm="HS256")


def create_expired_token(user_id: str = "test-user") -> str:
    """Create an expired JWT token for testing."""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    return jwt.encode(payload, "test-secret-key", algorithm="HS256")


async def wait_for_async_task(
    check_func,
    max_attempts: int = 30,
    wait_seconds: float = 1.0
) -> bool:
    """
    Wait for an async task to complete.
    
    Args:
        check_func: Async function that returns True when task is complete
        max_attempts: Maximum number of attempts
        wait_seconds: Seconds to wait between attempts
    
    Returns:
        True if task completed, False if timeout
    """
    for _ in range(max_attempts):
        if await check_func():
            return True
        await asyncio.sleep(wait_seconds)
    return False


# ============================================================================
# Pytest Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )


# ============================================================================
# Mock Data Generators
# ============================================================================

@pytest.fixture
def port_codes() -> list:
    """Common port codes for testing."""
    return [
        "CNSHA",  # Shanghai
        "SGSIN",  # Singapore
        "USLAX",  # Los Angeles
        "NLRTM",  # Rotterdam
        "DEHAM",  # Hamburg
        "KRPUS",  # Busan
        "HKHKG",  # Hong Kong
        "AEJEA",  # Jebel Ali
    ]


@pytest.fixture
def cargo_types() -> list:
    """Common cargo types for testing."""
    return [
        "ELECTRONICS",
        "MACHINERY",
        "AUTOMOTIVE",
        "TEXTILES",
        "CHEMICALS",
        "FOOD_BEVERAGES",
        "GENERAL_CARGO",
    ]


@pytest.fixture
def carrier_codes() -> list:
    """Common carrier codes for testing."""
    return [
        "MAEU",  # Maersk
        "MSCU",  # MSC
        "CMDU",  # CMA CGM
        "COSU",  # COSCO
        "HLCU",  # Hapag-Lloyd
    ]


# ============================================================================
# Database Utilities
# ============================================================================

@pytest.fixture
def clean_database(test_db):
    """
    Clean database before each test.
    
    Truncates all tables to ensure test isolation.
    """
    if test_db is None:
        yield
        return
    
    try:
        # Delete all data
        from app.database import Base
        
        for table in reversed(Base.metadata.sorted_tables):
            test_db.execute(table.delete())
        
        test_db.commit()
        yield test_db
    except Exception as e:
        test_db.rollback()
        yield test_db


# ============================================================================
# Performance Monitoring
# ============================================================================

@pytest.fixture
def performance_monitor():
    """Monitor test performance."""
    import time
    
    start_time = time.time()
    
    yield
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Warn if E2E test is too slow
    if duration > 30:
        print(f"\n⚠️  Slow E2E test: {duration:.2f}s")
