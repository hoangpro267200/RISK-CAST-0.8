"""
RISKCAST Insurance Module V2 - Basic Tests
===========================================
Simple tests to verify core functionality.
"""

import pytest
from datetime import datetime, timedelta

from app.models.insurance import (
    InsuranceProduct, InsuranceProductCategory, InsuranceProductTier,
    ProductStatus, ParametricTrigger, PayoutStructure, PremiumBreakdown,
    InsuranceQuote, TransactionState
)
from app.services.parametric_engine import (
    ParametricPricingEngine, ParametricTriggerEvaluator
)
from app.services.insurance_quote_service import InsuranceQuoteService
from app.services.insurance_ai_advisor import InsuranceAIAdvisor
from app.services.insurance_transaction_service import (
    InsuranceTransactionService, TransactionStateMachine
)


def test_parametric_pricing_rainfall():
    """Test rainfall parametric pricing."""
    trigger = ParametricTrigger(
        product_id="weather_delay_parametric",
        trigger_type="weather",
        location={"port_code": "SGSIN"},
        metric="cumulative_rainfall_mm",
        threshold=150.0,
        data_source="tomorrow_io"
    )
    
    payout_structure = PayoutStructure(
        type="per_mm_excess",
        payout_per_unit=50.0,
        minimum_payout=500.0,
        maximum_payout=10000.0
    )
    trigger.payout_structure = payout_structure
    
    # Mock historical data
    historical_data = [
        {"rainfall_mm": r} for r in [50, 80, 120, 140, 160, 180, 200, 100, 90, 110]
    ]
    
    quote = ParametricPricingEngine.price_rainfall_parametric(
        trigger=trigger,
        historical_data=historical_data,
        cargo_value=100000
    )
    
    assert quote.premium > 0
    assert quote.expected_payout >= 0
    assert 0 <= quote.trigger_probability <= 1
    assert 0 <= quote.basis_risk_score <= 1
    print(f"✅ Rainfall pricing test passed: Premium=${quote.premium:.2f}")


def test_parametric_pricing_port_congestion():
    """Test port congestion parametric pricing."""
    trigger = ParametricTrigger(
        product_id="port_delay_parametric",
        trigger_type="port_congestion",
        location={"port_code": "USLAX"},
        metric="container_dwell_time",
        threshold=14.0,
        data_source="port_authority_api"
    )
    
    payout_structure = PayoutStructure(
        type="per_day_excess",
        payout_per_unit=1000.0,
        maximum_days=30,
        franchise_deductible=3.0
    )
    trigger.payout_structure = payout_structure
    
    # Mock historical data
    historical_data = [
        {"dwell_days": d} for d in [8, 10, 12, 15, 18, 20, 22, 25, 8, 10]
    ]
    
    quote = ParametricPricingEngine.price_port_congestion_parametric(
        trigger=trigger,
        historical_data=historical_data,
        cargo_value=100000
    )
    
    assert quote.premium > 0
    assert quote.expected_payout >= 0
    assert 0 <= quote.trigger_probability <= 1
    print(f"✅ Port congestion pricing test passed: Premium=${quote.premium:.2f}")


def test_trigger_evaluation_rainfall():
    """Test rainfall trigger evaluation."""
    trigger = ParametricTrigger(
        product_id="weather_delay_parametric",
        trigger_type="weather",
        location={"port_code": "SGSIN"},
        metric="cumulative_rainfall_mm",
        threshold=150.0,
        data_source="tomorrow_io"
    )
    
    payout_structure = PayoutStructure(
        type="per_mm_excess",
        payout_per_unit=50.0,
        minimum_payout=500.0,
        maximum_payout=10000.0
    )
    trigger.payout_structure = payout_structure
    
    # Test below threshold
    current_data = {"cumulative_rainfall_mm": 120}
    result = ParametricTriggerEvaluator.evaluate_rainfall_trigger(trigger, current_data)
    assert result.triggered == False
    
    # Test above threshold
    current_data = {"cumulative_rainfall_mm": 180}
    result = ParametricTriggerEvaluator.evaluate_rainfall_trigger(trigger, current_data)
    assert result.triggered == True
    assert result.payout_amount > 0
    print(f"✅ Rainfall trigger evaluation test passed: Payout=${result.payout_amount:.2f}")


def test_trigger_evaluation_port_congestion():
    """Test port congestion trigger evaluation."""
    trigger = ParametricTrigger(
        product_id="port_delay_parametric",
        trigger_type="port_congestion",
        location={"port_code": "USLAX"},
        metric="container_dwell_time",
        threshold=14.0,
        data_source="port_authority_api"
    )
    
    payout_structure = PayoutStructure(
        type="per_day_excess",
        payout_per_unit=1000.0,
        maximum_days=30,
        franchise_deductible=3.0
    )
    trigger.payout_structure = payout_structure
    
    # Test below threshold
    current_data = {"dwell_days": 12}
    result = ParametricTriggerEvaluator.evaluate_port_congestion_trigger(trigger, current_data)
    assert result.triggered == False
    
    # Test above threshold
    current_data = {"dwell_days": 19}
    result = ParametricTriggerEvaluator.evaluate_port_congestion_trigger(trigger, current_data)
    assert result.triggered == True
    assert result.payout_amount > 0
    print(f"✅ Port congestion trigger evaluation test passed: Payout=${result.payout_amount:.2f}")


def test_quote_generation():
    """Test quote generation service."""
    risk_assessment = {
        "risk_score": {"overallScore": 67.5},
        "layers": [
            {"name": "Port Congestion", "score": 72},
            {"name": "Weather Risk", "score": 65},
            {"name": "Route Complexity", "score": 58}
        ],
        "financial": {
            "expectedLoss": 12500,
            "var95": 45000
        }
    }
    
    shipment_data = {
        "cargo": {
            "value_usd": 100000,
            "type": "electronics"
        },
        "transport": {
            "mode": "ocean"
        },
        "route": {
            "pol": "CNSHA",
            "pod": "USLAX"
        }
    }
    
    quotes = InsuranceQuoteService.generate_quotes(
        risk_assessment=risk_assessment,
        shipment_data=shipment_data
    )
    
    assert len(quotes) > 0
    assert all(isinstance(q, InsuranceQuote) for q in quotes)
    print(f"✅ Quote generation test passed: Generated {len(quotes)} quote(s)")


def test_ai_advisor():
    """Test AI Advisor service."""
    risk_assessment = {
        "risk_score": {"overallScore": 67.5},
        "layers": [
            {"name": "Port Congestion", "score": 72},
            {"name": "Weather Risk", "score": 65}
        ],
        "financial": {
            "expectedLoss": 12500,
            "var95": 45000
        }
    }
    
    response = InsuranceAIAdvisor.answer_why_buy_insurance(
        risk_assessment=risk_assessment
    )
    
    assert response.mode == "recommendation"
    assert 0 <= response.confidence <= 1
    assert len(response.reasoning) > 0
    assert len(response.disclaimers) > 0
    print(f"✅ AI Advisor test passed: Confidence={response.confidence:.2f}")


def test_transaction_state_machine():
    """Test transaction state machine."""
    # Test valid transition
    can_transition = TransactionStateMachine.can_transition(
        TransactionState.QUOTE_GENERATED,
        TransactionState.CONFIGURING
    )
    assert can_transition == True
    
    # Test invalid transition
    can_transition = TransactionStateMachine.can_transition(
        TransactionState.QUOTE_GENERATED,
        TransactionState.BOUND
    )
    assert can_transition == False
    print("✅ Transaction state machine test passed")


if __name__ == "__main__":
    print("🧪 Running Insurance Module V2 Tests...\n")
    
    try:
        test_parametric_pricing_rainfall()
        test_parametric_pricing_port_congestion()
        test_trigger_evaluation_rainfall()
        test_trigger_evaluation_port_congestion()
        test_quote_generation()
        test_ai_advisor()
        test_transaction_state_machine()
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
