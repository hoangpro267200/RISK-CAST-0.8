#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Phase 2 backend API verification"""

import requests
import time
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"
session = requests.Session()

def test_endpoint(method, path, data=None, cookies=None, expected_status=None, description=""):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*50}")
    print(f"TEST: {description or f'{method} {path}'}")
    print(f"{'='*50}")
    
    try:
        if method == "GET":
            response = session.get(url, cookies=cookies, timeout=5)
        elif method == "POST":
            response = session.post(url, json=data, cookies=cookies, timeout=5)
        else:
            print(f"[FAIL] Unknown method: {method}")
            return False, None
        
        status_ok = True
        if expected_status:
            if response.status_code == expected_status:
                print(f"[PASS] HTTP {response.status_code} (expected {expected_status})")
            else:
                print(f"[FAIL] HTTP {response.status_code} (expected {expected_status})")
                status_ok = False
        else:
            print(f"[INFO] HTTP {response.status_code}")
        
        try:
            body = response.json()
            print(f"Body: {body}")
        except:
            body = response.text[:200]
            print(f"Body: {body}")
        
        # Store cookies if any
        if response.cookies:
            session.cookies.update(response.cookies)
            print(f"Cookies received: {list(response.cookies.keys())}")
        
        return status_ok, response
        
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Connection refused - is server running on {BASE_URL}?")
        return False, None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    print("Starting API endpoint tests...")
    print("Make sure server is running: uvicorn app.main:app --port 8000")
    print("\nWaiting 2 seconds for server check...")
    time.sleep(2)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        print(f"[INFO] Server is running (health check: {response.status_code})")
    except:
        print("[WARN] Server health check failed - continuing anyway")
    
    results = []
    
    # Test 1: GET /api/auth/me (No Auth)
    ok, _ = test_endpoint("GET", "/api/auth/me", expected_status=401, description="GET /api/auth/me (No Auth)")
    results.append(("Test 1: GET /me (no auth)", ok))
    
    # Test 2: POST /api/auth/signup
    test_email = f"testuser_{int(time.time())}@example.com"
    test_pass = "SecurePass123!"
    ok, signup_resp = test_endpoint(
        "POST", "/api/auth/signup",
        data={"email": test_email, "password": test_pass, "name": "Test User"},
        expected_status=201,  # 201 is correct for creation
        description="POST /api/auth/signup"
    )
    results.append(("Test 2: POST /signup", ok))
    
    # Test 3: POST /api/auth/login
    ok, login_resp = test_endpoint(
        "POST", "/api/auth/login",
        data={"email": test_email, "password": test_pass},
        expected_status=200,
        description="POST /api/auth/login"
    )
    results.append(("Test 3: POST /login", ok))
    cookies = session.cookies
    
    # Test 4: GET /api/auth/me (With Auth)
    ok, _ = test_endpoint("GET", "/api/auth/me", cookies=cookies, expected_status=200, description="GET /api/auth/me (With Auth)")
    results.append(("Test 4: GET /me (with auth)", ok))
    
    # Test 5: GET /api/auth/sessions
    ok, _ = test_endpoint("GET", "/api/auth/sessions", cookies=cookies, expected_status=200, description="GET /api/auth/sessions")
    results.append(("Test 5: GET /sessions", ok))
    
    # Test 6: POST /api/auth/change-password
    ok, _ = test_endpoint(
        "POST", "/api/auth/change-password",
        data={"current_password": test_pass, "new_password": "NewSecurePass456!"},
        cookies=cookies,
        expected_status=200,
        description="POST /api/auth/change-password"
    )
    results.append(("Test 6: POST /change-password", ok))
    
    # Test 7: POST /api/auth/forgot-password
    ok, _ = test_endpoint(
        "POST", "/api/auth/forgot-password",
        data={"email": test_email},
        expected_status=200,
        description="POST /api/auth/forgot-password"
    )
    results.append(("Test 7: POST /forgot-password", ok))
    
    # Test 8: POST /api/auth/logout
    ok, _ = test_endpoint("POST", "/api/auth/logout", cookies=cookies, expected_status=200, description="POST /api/auth/logout")
    results.append(("Test 8: POST /logout", ok))
    
    # Test 9: GET /api/auth/me (After Logout)
    ok, _ = test_endpoint("GET", "/api/auth/me", cookies=cookies, expected_status=401, description="GET /api/auth/me (After Logout)")
    results.append(("Test 9: GET /me (after logout)", ok))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"{status} {name}")
    print(f"\nTotal: {passed}/{total} passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
