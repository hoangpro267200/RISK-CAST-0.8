"""
Pytest configuration and fixtures
"""
import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )


@pytest.fixture
def sample_shipment_data():
    """Sample shipment data for testing"""
    return {
        "transport": {
            "tradeLane": "vn_us",
            "mode": "SEA",
            "shipmentType": "FCL",
            "pol": "VNSGN",
            "pod": "USNYC",
            "containerType": "40GP",
            "etd": "2025-02-01",
            "transitDays": 30
        },
        "cargo": {
            "cargoType": "Electronics",
            "hsCode": "8471.30",
            "grossWeightKg": 15000,
            "volumeCbm": 65.5,
            "cargoValue": 50000
        },
        "seller": {
            "company": "Test Seller Co.",
            "country": "Vietnam",
            "email": "seller@test.com"
        },
        "buyer": {
            "company": "Test Buyer Co.",
            "country": "USA",
            "email": "buyer@test.com"
        }
    }


@pytest.fixture
def sample_risk_state():
    """Sample RISKCAST_STATE for testing"""
    return {
        "shipment": {
            "trade_route": {
                "pol": "VNSGN",
                "pod": "USNYC",
                "mode": "SEA",
                "container_type": "40GP",
                "etd": "2025-02-01",
                "transit_time_days": 30
            },
            "cargo_packing": {
                "cargo_type": "Electronics",
                "hs_code": "8471.30",
                "gross_weight_kg": 15000,
                "volume_cbm": 65.5
            },
            "seller": {
                "company": "Test Seller Co.",
                "country": "Vietnam"
            },
            "buyer": {
                "company": "Test Buyer Co.",
                "country": "USA"
            }
        },
        "riskModules": {
            "esg": True,
            "weather": True,
            "congestion": True,
            "carrier_perf": True,
            "market": True,
            "insurance": True
        }
    }

