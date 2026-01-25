"""
Integration Test Fixtures for API Tests

Provides shared fixtures for integration testing:
- Async client setup
- Authentication
- Test data creation
- Database handling
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database import Base, get_db


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_db(test_engine) -> Session:
    """Create test database session."""
    TestSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_engine
    )
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
async def async_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db) -> Dict[str, Any]:
    """Create a test user in the database."""
    from app.models.user import User
    from app.shared.utils import generate_ulid
    
    user = User(
        id=generate_ulid(),
        email="test@example.com",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        is_verified=True,
        full_name="Test User",
        tenant_id="test-tenant-1"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "tenant_id": user.tenant_id
    }


@pytest.fixture
def auth_headers(test_user) -> Dict[str, str]:
    """Create authentication headers with test user token."""
    from app.core.security import create_access_token
    
    token = create_access_token(subject=test_user["id"])
    
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": test_user["tenant_id"]
    }


@pytest.fixture
def quote_request_payload() -> Dict[str, Any]:
    """Standard quote request payload."""
    return {
        "origin_port": "CNSHA",
        "destination_port": "USLAX",
        "cargo_type": "ELECTRONICS",
        "cargo_value_usd": 500000,
        "container_count": 2,
        "packaging_quality": "STANDARD",
        "departure_date": (date.today() + timedelta(days=7)).isoformat(),
        "arrival_date": (date.today() + timedelta(days=28)).isoformat(),
        "carrier_code": "MAEU",
        "coverage_type": "ALL_RISKS",
        "deductible_type": "PERCENTAGE",
        "deductible_value": 0.01,
        "include_war_risk": False,
        "include_strikes": False
    }


@pytest.fixture
async def created_quote(
    async_client: AsyncClient, 
    auth_headers: Dict[str, str],
    quote_request_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a test quote via API."""
    response = await async_client.post(
        "/api/v3/quotes/request",
        json=quote_request_payload,
        headers=auth_headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to create quote: {response.text}")
    
    return response.json()


@pytest.fixture
async def accepted_quote(
    async_client: AsyncClient,
    auth_headers: Dict[str, str],
    created_quote: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an accepted quote."""
    response = await async_client.post(
        f"/api/v3/quotes/{created_quote['quote_id']}/accept",
        json={"acceptance_notes": "Test acceptance"},
        headers=auth_headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to accept quote: {response.text}")
    
    return response.json()


@pytest.fixture
def expired_quote(test_db, test_user) -> Dict[str, Any]:
    """Create an expired quote directly in database."""
    from app.models.quote import Quote
    from app.shared.utils import generate_ulid
    
    quote = Quote(
        id=generate_ulid(),
        quote_number="QT-TEST-EXPIRED-001",
        tenant_id=test_user["tenant_id"],
        customer_id=test_user["id"],
        status="PENDING",
        origin_port="CNSHA",
        destination_port="USLAX",
        cargo_type="ELECTRONICS",
        cargo_value_usd=500000,
        total_premium_usd=1500.00,
        rate_per_mille=3.00,
        risk_score=0.5,
        risk_grade="C",
        valid_from=datetime.utcnow() - timedelta(days=10),
        valid_until=datetime.utcnow() - timedelta(days=3),  # Expired
        created_at=datetime.utcnow() - timedelta(days=10)
    )
    
    test_db.add(quote)
    test_db.commit()
    test_db.refresh(quote)
    
    return {
        "quote_id": quote.id,
        "quote_number": quote.quote_number
    }


@pytest.fixture
def risk_assessment_payload() -> Dict[str, Any]:
    """Standard risk assessment payload."""
    return {
        "origin_port": "CNSHA",
        "destination_port": "USLAX",
        "cargo_type": "ELECTRONICS",
        "cargo_value_usd": 500000,
        "container_count": 2,
        "departure_date": (date.today() + timedelta(days=7)).isoformat(),
        "expected_arrival_date": (date.today() + timedelta(days=28)).isoformat(),
        "carrier_code": "MAEU"
    }


@pytest.fixture
async def created_risk_assessment(
    async_client: AsyncClient,
    auth_headers: Dict[str, str],
    risk_assessment_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a test risk assessment via API."""
    response = await async_client.post(
        "/api/v3/risk/assess",
        json=risk_assessment_payload,
        headers=auth_headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to create risk assessment: {response.text}")
    
    return response.json()


@pytest.fixture
def test_tenant(test_db) -> Dict[str, Any]:
    """Create a test tenant."""
    from app.models.tenant import Tenant
    from app.shared.utils import generate_ulid
    
    tenant = Tenant(
        id=generate_ulid(),
        name="Test Tenant",
        domain="test.example.com",
        is_active=True,
        tier="STANDARD"
    )
    
    test_db.add(tenant)
    test_db.commit()
    test_db.refresh(tenant)
    
    return {
        "id": tenant.id,
        "name": tenant.name
    }


@pytest.fixture
def test_customer(test_db, test_tenant) -> Dict[str, Any]:
    """Create a test customer."""
    from app.models.customer import Customer
    from app.shared.utils import generate_ulid
    
    customer = Customer(
        id=generate_ulid(),
        tenant_id=test_tenant["id"],
        name="Test Customer Company",
        email="customer@test.example.com",
        pricing_tier="STANDARD",
        is_active=True
    )
    
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)
    
    return {
        "id": customer.id,
        "name": customer.name,
        "tenant_id": customer.tenant_id
    }
