#!/usr/bin/env python3
"""
Verification script for Risk Engine test suite.

This script performs comprehensive checks to ensure the test suite
is properly set up and ready to run.

Usage:
    python verify_test_suite.py
"""

import sys
import os
from pathlib import Path
import importlib.util

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_file_exists(filepath: Path, description: str) -> bool:
    """Check if a file exists."""
    if filepath.exists():
        print(f"[OK] {description}: {filepath.name}")
        return True
    else:
        print(f"[FAIL] {description}: {filepath.name} NOT FOUND")
        return False

def check_imports() -> bool:
    """Check if all required imports work."""
    print("\n" + "=" * 70)
    print("Checking imports...")
    print("=" * 70)
    
    required_modules = [
        ("pytest", "pytest"),
        ("numpy", "numpy"),
        ("scipy", "scipy.stats"),
        ("app.core.risk_engine.v16.risk_engine_calibrated", "Risk Engine"),
        ("app.modules.model_versioning.models", "Model Version"),
        ("app.services.unified_data_service", "Data Service"),
    ]
    
    all_ok = True
    for module_name, description in required_modules:
        try:
            if "." in module_name and not module_name.startswith("app."):
                # For packages like scipy.stats
                parts = module_name.split(".")
                mod = __import__(parts[0])
                for part in parts[1:]:
                    mod = getattr(mod, part)
            else:
                __import__(module_name)
            print(f"[OK] {description}: OK")
        except ImportError as e:
            print(f"[FAIL] {description}: FAILED - {e}")
            all_ok = False
    
    return all_ok

def count_tests() -> dict:
    """Count tests in the test file."""
    print("\n" + "=" * 70)
    print("Counting tests...")
    print("=" * 70)
    
    test_file = Path(__file__).parent / "test_risk_engine.py"
    
    if not test_file.exists():
        print(f"[FAIL] Test file not found: {test_file}")
        return {}
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    
    # Count test classes
    classes = re.findall(r'^class (Test\w+)', content, re.MULTILINE)
    
    # Count test methods
    methods = re.findall(r'^\s+(def|async def) (test_\w+)', content, re.MULTILINE)
    
    # Count fixtures
    fixtures = re.findall(r'^@pytest\.fixture', content, re.MULTILINE)
    
    # Count lines
    lines = len(content.split('\n'))
    
    stats = {
        'classes': len(classes),
        'methods': len(methods),
        'fixtures': len(fixtures),
        'lines': lines,
        'class_names': classes
    }
    
    print(f"[OK] Test classes: {stats['classes']}")
    print(f"[OK] Test methods: {stats['methods']}")
    print(f"[OK] Fixtures: {stats['fixtures']}")
    print(f"[OK] Total lines: {stats['lines']:,}")
    
    return stats

def check_test_structure() -> bool:
    """Check test file structure."""
    print("\n" + "=" * 70)
    print("Checking test structure...")
    print("=" * 70)
    
    test_file = Path(__file__).parent / "test_risk_engine.py"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_sections = [
        ("Fixtures", "# Fixtures"),
        ("TestRiskEngineBasics", "class TestRiskEngineBasics"),
        ("TestLayerCalculations", "class TestLayerCalculations"),
        ("TestWeightApplication", "class TestWeightApplication"),
        ("TestMonteCarloSimulation", "class TestMonteCarloSimulation"),
    ]
    
    all_ok = True
    for name, marker in required_sections:
        if marker in content:
            print(f"[OK] {name}: Found")
        else:
            print(f"[FAIL] {name}: NOT FOUND")
            all_ok = False
    
    return all_ok

def verify_syntax() -> bool:
    """Verify Python syntax."""
    print("\n" + "=" * 70)
    print("Verifying syntax...")
    print("=" * 70)
    
    test_file = Path(__file__).parent / "test_risk_engine.py"
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, test_file, 'exec')
        print(f"[OK] Syntax valid")
        return True
    except SyntaxError as e:
        print(f"[FAIL] Syntax error: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Risk Engine Test Suite Verification")
    print("=" * 70)
    
    project_root = Path(__file__).parent.parent.parent
    test_dir = Path(__file__).parent
    
    print(f"\nProject root: {project_root}")
    print(f"Test directory: {test_dir}")
    
    # Check files
    print("\n" + "=" * 70)
    print("Checking files...")
    print("=" * 70)
    
    files_ok = all([
        check_file_exists(test_dir / "test_risk_engine.py", "Main test file"),
        check_file_exists(test_dir / "test_risk_engine_README.md", "README"),
        check_file_exists(test_dir / "run_risk_engine_tests.py", "Test runner"),
        check_file_exists(test_dir / "generate_coverage_report.py", "Coverage tool"),
        check_file_exists(test_dir / "RISK_ENGINE_TESTS_SUMMARY.md", "Summary"),
        check_file_exists(test_dir / "QUICK_REFERENCE.md", "Quick reference"),
    ])
    
    # Check imports
    imports_ok = check_imports()
    
    # Count tests
    stats = count_tests()
    
    # Check structure
    structure_ok = check_test_structure()
    
    # Verify syntax
    syntax_ok = verify_syntax()
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    checks = {
        "Files": files_ok,
        "Imports": imports_ok,
        "Structure": structure_ok,
        "Syntax": syntax_ok,
    }
    
    all_passed = all(checks.values())
    
    for check_name, passed in checks.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{check_name:20} {status}")
    
    if stats:
        print(f"\nTest Statistics:")
        print(f"  - Classes:  {stats['classes']}")
        print(f"  - Methods:  {stats['methods']}")
        print(f"  - Fixtures: {stats['fixtures']}")
        print(f"  - Lines:    {stats['lines']:,}")
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("[SUCCESS] ALL CHECKS PASSED - Test suite is ready!")
        print("\nNext steps:")
        print("  1. Run tests: python tests/unit/run_risk_engine_tests.py")
        print("  2. Generate coverage: python tests/unit/generate_coverage_report.py")
        return 0
    else:
        print("[FAILED] SOME CHECKS FAILED - Please review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
