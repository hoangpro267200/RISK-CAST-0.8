"""
Pact test configuration and fixtures.
"""

import pytest
import os
from typing import Optional


# Pact broker configuration
PACT_BROKER_URL = os.getenv("PACT_BROKER_URL", "http://localhost:9292")
PACT_BROKER_TOKEN = os.getenv("PACT_BROKER_TOKEN", "")


@pytest.fixture(scope="session")
def pact_quote_consumer():
    """
    Pact for quote consumer (e.g., frontend app).
    """
    try:
        from pact import Pact, Consumer, Provider
        
        pact = Pact(
            consumer=Consumer("QuotePortal"),
            provider=Provider("RiskCastAPI"),
            host_name="localhost",
            port=1234,
            pact_dir="./pacts",
            log_dir="./pact_logs",
            version="1.0.0"
        )
        
        pact.start_service()
        yield pact
        pact.stop_service()
    except ImportError:
        pytest.skip("pact-python not installed")


@pytest.fixture(scope="session")
def pact_policy_consumer():
    """
    Pact for policy management consumer.
    """
    try:
        from pact import Pact, Consumer, Provider
        
        pact = Pact(
            consumer=Consumer("PolicyDashboard"),
            provider=Provider("RiskCastAPI"),
            host_name="localhost",
            port=1235,
            pact_dir="./pacts",
            log_dir="./pact_logs",
            version="1.0.0"
        )
        
        pact.start_service()
        yield pact
        pact.stop_service()
    except ImportError:
        pytest.skip("pact-python not installed")


@pytest.fixture(scope="session")
def pact_claims_consumer():
    """
    Pact for claims consumer.
    """
    try:
        from pact import Pact, Consumer, Provider
        
        pact = Pact(
            consumer=Consumer("ClaimsPortal"),
            provider=Provider("RiskCastAPI"),
            host_name="localhost",
            port=1236,
            pact_dir="./pacts",
            log_dir="./pact_logs",
            version="1.0.0"
        )
        
        pact.start_service()
        yield pact
        pact.stop_service()
    except ImportError:
        pytest.skip("pact-python not installed")


@pytest.fixture
def mock_auth_header():
    """Mock authorization header."""
    return {"Authorization": "Bearer test-token-12345"}
