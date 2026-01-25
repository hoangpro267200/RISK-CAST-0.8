#!/usr/bin/env python3
"""
Generate test coverage report for Risk Engine.

This script runs the risk engine tests with coverage analysis
and generates an HTML report.

Usage:
    python generate_coverage_report.py
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Generate coverage report."""
    print("=" * 70)
    print("Risk Engine Test Coverage Report Generator")
    print("=" * 70)
    print()
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    test_file = Path(__file__).parent / "test_risk_engine.py"
    source_file = project_root / "app" / "core" / "risk_engine" / "v16" / "risk_engine_calibrated.py"
    
    # Coverage command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        f"--cov={source_file.parent}",
        "--cov-report=html:htmlcov/risk_engine",
        "--cov-report=term-missing",
        "--cov-report=json:coverage_risk_engine.json",
        "-v",
        "--tb=short",
    ]
    
    print(f"Test file: {test_file}")
    print(f"Source file: {source_file}")
    print()
    print("Running coverage analysis...")
    print()
    
    # Check if pytest-cov is installed
    try:
        import pytest_cov
    except ImportError:
        print("❌ pytest-cov not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-cov"])
    
    # Run coverage
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=False)
        exit_code = result.returncode
    except Exception as e:
        print(f"❌ Error running coverage: {e}")
        return 1
    
    print()
    print("=" * 70)
    
    if exit_code == 0:
        print("✅ Coverage report generated successfully!")
        print()
        print(f"HTML report: {project_root}/htmlcov/risk_engine/index.html")
        print(f"JSON report: {project_root}/coverage_risk_engine.json")
        print()
        print("Open the HTML report in your browser to view detailed coverage.")
    else:
        print(f"❌ Coverage analysis failed with exit code: {exit_code}")
    
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
