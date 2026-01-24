#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Phase 5: End-to-End Auth Flow"""

import requests
import time
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

def main():
    print("="*60)
    print("E2E TEST: Complete Auth Flow")
    print("="*60)
    
    session = requests.Session()
    results = []
    
    # Generate unique email
    test_email = f"e2e_{int(time.time())}@test.com"
    test_pass = "E2ETestPass123!"
    new_pass = "NewE2EPass456!"
    
    print(f"\nUsing test email: {test_email}")
    
    # Step 1: Visit Home (should see login button)
    print("\nStep 1: Visit Home (should see login button)")
    try:
        response = session.get(f"{BASE_URL}/")
        home_check = "Đăng nhập" in response.text or "/login" in response.text
        if home_check:
            print("[PASS] Step 1: Home page shows login button")
            results.append(True)
        else:
            print("[FAIL] Step 1: Home page does not show login button")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 1: Error - {e}")
        results.append(False)
    
    # Step 2: Signup new user
    print(f"\nStep 2: Signup new user ({test_email})")
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/signup",
            json={"email": test_email, "password": test_pass, "name": "E2E Tester"}
        )
        if response.status_code in [200, 201]:
            print(f"[PASS] Step 2: User created (HTTP {response.status_code})")
            results.append(True)
        else:
            print(f"[FAIL] Step 2: Signup failed (HTTP {response.status_code})")
            print(f"Response: {response.text[:200]}")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 2: Error - {e}")
        results.append(False)
    
    # Step 3: Login
    print(f"\nStep 3: Login")
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": test_pass}
        )
        if response.status_code == 200:
            print(f"[PASS] Step 3: Login successful (HTTP {response.status_code})")
            results.append(True)
        else:
            print(f"[FAIL] Step 3: Login failed (HTTP {response.status_code})")
            print(f"Response: {response.text[:200]}")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 3: Error - {e}")
        results.append(False)
    
    # Step 4: Access /api/auth/me
    print(f"\nStep 4: Access /api/auth/me")
    try:
        response = session.get(f"{BASE_URL}/api/auth/me")
        if response.status_code == 200:
            user_data = response.json()
            if user_data.get("email") == test_email:
                print(f"[PASS] Step 4: /me returns user data")
                results.append(True)
            else:
                print(f"[FAIL] Step 4: /me returned wrong user data")
                results.append(False)
        else:
            print(f"[FAIL] Step 4: /me failed (HTTP {response.status_code})")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 4: Error - {e}")
        results.append(False)
    
    # Step 5: Access Overview page
    print(f"\nStep 5: Access Overview page")
    try:
        response = session.get(f"{BASE_URL}/overview")
        if response.status_code == 200:
            print(f"[PASS] Step 5: Overview page accessible (HTTP {response.status_code})")
            results.append(True)
        else:
            print(f"[FAIL] Step 5: Overview page failed (HTTP {response.status_code})")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 5: Error - {e}")
        results.append(False)
    
    # Step 6: Change password
    print(f"\nStep 6: Change password")
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": test_pass, "new_password": new_pass}
        )
        if response.status_code == 200:
            print(f"[PASS] Step 6: Password changed successfully")
            results.append(True)
        else:
            print(f"[FAIL] Step 6: Password change failed (HTTP {response.status_code})")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 6: Error - {e}")
        results.append(False)
    
    # Step 7: Logout
    print(f"\nStep 7: Logout")
    try:
        response = session.post(f"{BASE_URL}/api/auth/logout")
        if response.status_code == 200:
            print(f"[PASS] Step 7: Logout successful")
            results.append(True)
        else:
            print(f"[FAIL] Step 7: Logout failed (HTTP {response.status_code})")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 7: Error - {e}")
        results.append(False)
    
    # Step 8: Verify logged out
    print(f"\nStep 8: Verify logged out")
    try:
        response = session.get(f"{BASE_URL}/api/auth/me")
        if response.status_code == 401:
            print(f"[PASS] Step 8: Correctly returns 401 after logout")
            results.append(True)
        else:
            print(f"[FAIL] Step 8: Should return 401, got {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 8: Error - {e}")
        results.append(False)
    
    # Step 9: Login with new password
    print(f"\nStep 9: Login with new password")
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": new_pass}
        )
        if response.status_code == 200:
            print(f"[PASS] Step 9: Login with new password successful")
            results.append(True)
        else:
            print(f"[FAIL] Step 9: Login with new password failed (HTTP {response.status_code})")
            results.append(False)
    except Exception as e:
        print(f"[FAIL] Step 9: Error - {e}")
        results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("E2E TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    for i, result in enumerate(results, 1):
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} Step {i}")
    print(f"\nTotal: {passed}/{total} passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
