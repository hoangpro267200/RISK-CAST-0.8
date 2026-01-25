"""
End-to-End Test Suite for RiskCast

Tests complete user flows and business processes.

Usage:
    # Run all E2E tests
    pytest tests/e2e/ -v -m e2e
    
    # Run specific flow
    pytest tests/e2e/test_quote_to_policy.py -v
    pytest tests/e2e/test_claim_flow.py -v
    
    # Run with coverage
    pytest tests/e2e/ --cov=app --cov-report=html
"""

__version__ = "1.0.0"
__author__ = "RiskCast QA Team"
