"""
Security Test Suite for RiskCast

Comprehensive security testing covering OWASP Top 10 and common vulnerabilities.

Usage:
    # Run all security tests
    pytest tests/security/ -v
    
    # Run specific test file
    pytest tests/security/test_security.py -v
    pytest tests/security/test_injection.py -v
    
    # Run with coverage
    pytest tests/security/ --cov=app.core.security --cov-report=html
"""

__version__ = "1.0.0"
__author__ = "RiskCast Security Team"
