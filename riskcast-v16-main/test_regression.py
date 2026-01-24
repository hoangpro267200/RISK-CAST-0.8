#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Phase 6: Regression Tests"""

import requests
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

def test_route(path, expected_codes=[200], description=""):
    """Test a route"""
    try:
        response = requests.get(f"{BASE_URL}{path}", timeout=5, allow_redirects=False)
        status_ok = response.status_code in expected_codes
        status = "[PASS]" if status_ok else "[FAIL]"
        print(f"{status} {description or path}: HTTP {response.status_code}")
        return status_ok
    except Exception as e:
        print(f"[FAIL] {description or path}: Error - {e}")
        return False

def main():
    print("=== Regression Tests ===")
    print("Testing existing features still work after auth integration\n")
    
    results = []
    
    # Test existing routes
    results.append(test_route("/", [200], "Home Page"))
    results.append(test_route("/results", [200, 302], "Results Page"))
    results.append(test_route("/input_react", [200, 302], "Input Page"))
    results.append(test_route("/health", [200], "Health Endpoint"))
    
    # Test static assets (optional - may not exist)
    try:
        response = requests.get(f"{BASE_URL}/static/js/home_futureos.js", timeout=3)
        if response.status_code in [200, 304, 404]:
            print(f"[INFO] Static JS: HTTP {response.status_code} (may not exist)")
        results.append(True)  # Don't fail on static assets
    except:
        print("[INFO] Static JS: Not accessible (this is OK)")
        results.append(True)
    
    # Summary
    print(f"\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
