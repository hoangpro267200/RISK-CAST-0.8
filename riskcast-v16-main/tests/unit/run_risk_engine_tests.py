"""
Standalone test runner for Risk Engine tests.

This script runs the risk engine tests independently without requiring
the full application context (avoids conftest.py import issues).

Usage:
    python run_risk_engine_tests.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

def main():
    """Run risk engine tests."""
    print("=" * 70)
    print("Risk Engine Unit Tests - Standalone Runner")
    print("=" * 70)
    print()
    
    # Test file path
    test_file = os.path.join(
        os.path.dirname(__file__),
        "test_risk_engine.py"
    )
    
    # Run tests with verbose output
    args = [
        test_file,
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "-ra",  # Show summary of all test outcomes
        "--color=yes",  # Color output
        "-W", "ignore::DeprecationWarning",  # Ignore deprecation warnings
    ]
    
    print(f"Running tests from: {test_file}")
    print()
    
    # Run pytest
    exit_code = pytest.main(args)
    
    print()
    print("=" * 70)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {exit_code}")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
