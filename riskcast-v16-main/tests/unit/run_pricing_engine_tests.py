"""
Standalone test runner for Pricing Engine tests.

This script runs the pricing engine tests independently.

Usage:
    python run_pricing_engine_tests.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest

def main():
    """Run pricing engine tests."""
    print("=" * 70)
    print("Pricing Engine Unit Tests - Standalone Runner")
    print("=" * 70)
    print()
    
    # Test file path
    test_file = os.path.join(
        os.path.dirname(__file__),
        "test_pricing_engine.py"
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
        print("[SUCCESS] All tests passed!")
    else:
        print(f"[FAILED] Tests failed with exit code: {exit_code}")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
