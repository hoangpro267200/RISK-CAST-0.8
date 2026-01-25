"""
Load Testing Suite for RiskCast

This package contains comprehensive load testing scenarios using Locust.

Usage:
    # Run predefined tests
    python tests/load/run_load_tests.py --quick
    python tests/load/run_load_tests.py --baseline
    python tests/load/run_load_tests.py --stress
    
    # Run custom test
    python tests/load/run_load_tests.py --scenario mixed --users 100 --duration 10m
    
    # Validate performance
    python tests/load/performance_requirements.py reports/load_tests/test_stats.csv
    
    # With web UI
    locust -f tests/load/locustfile.py MixedWorkloadUser --host http://localhost:8000
"""

__version__ = "1.0.0"
__author__ = "RiskCast Team"
