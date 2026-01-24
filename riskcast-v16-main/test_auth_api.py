#!/usr/bin/env python3
"""Test all auth API endpoints"""
import sys
sys.path.insert(0, '.')
import requests
import time
import json

BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePass123!"
TEST_NAME = "Test User"

print("=== PHASE 2: BACKEND API VERIFICATION ===")
print()

# Wait for server to be ready
print("Waiting for server to be ready...")
for i in range(10):
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        if r.status_code == 200:
            print("PASS: Server is ready")
            break
    except:
        time.sleep(1)
else:
    print("FAIL: Server not responding. Start server with: uvicorn app.main:app --reload")
    sys.exit(1)

print()

# Test 1: GET /api/auth/me (No Auth)
print("TEST 1: GET /api/auth/me (No Auth)")
try:
    r = requests.get(f"{BASE_URL}/api/auth/me")
    print(f"HTTP: {r.status_code}")
    if r.status_code == 401:
        print("PASS: Returns 401 Unauthorized")
    else:
        print(f"FAIL: Expected 401, got {r.status_code}")
        print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"FAIL: {e}")
print()

# Test 2: POST /api/auth/signup
print("TEST 2: POST /api/auth/signup")
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/signup",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        },
        headers={"Content-Type": "application/json"}
    )
    print(f"HTTP: {r.status_code}")
    print(f"Response: {r.text[:200]}")
    if r.status_code in [200, 201]:
        print("PASS: Signup successful")
        signup_data = r.json() if r.headers.get('content-type', '').startswith('application/json') else {}
        print(f"User created: {signup_data.get('email', 'N/A')}")
    else:
        print(f"FAIL: Expected 200/201, got {r.status_code}")
except Exception as e:
    print(f"FAIL: {e}")
print()

# Test 3: POST /api/auth/login
print("TEST 3: POST /api/auth/login")
session = requests.Session()
try:
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        },
        headers={"Content-Type": "application/json"}
    )
    print(f"HTTP: {r.status_code}")
    print(f"Response: {r.text[:200]}")
    cookies = dict(session.cookies)
    print(f"Cookies: {list(cookies.keys())}")
    if r.status_code == 200:
        print("PASS: Login successful")
        if 'session_token' in cookies or len(cookies) > 0:
            print("PASS: Session cookie set")
        else:
            print("FAIL: No session cookie")
    else:
        print(f"FAIL: Expected 200, got {r.status_code}")
except Exception as e:
    print(f"FAIL: {e}")
print()

# Test 4: GET /api/auth/me (With Auth)
print("TEST 4: GET /api/auth/me (With Auth)")
try:
    r = session.get(f"{BASE_URL}/api/auth/me")
    print(f"HTTP: {r.status_code}")
    print(f"Response: {r.text[:200]}")
    if r.status_code == 200:
        print("PASS: Returns user data")
        data = r.json() if r.headers.get('content-type', '').startswith('application/json') else {}
        print(f"User: {data.get('email', 'N/A')}")
    else:
        print(f"FAIL: Expected 200, got {r.status_code}")
except Exception as e:
    print(f"FAIL: {e}")
print()

# Test 5: GET /api/auth/sessions
print("TEST 5: GET /api/auth/sessions")
try:
    r = session.get(f"{BASE_URL}/api/auth/sessions")
    print(f"HTTP: {r.status_code}")
    if r.status_code == 200:
        print("PASS: Returns sessions list")
        data = r.json() if r.headers.get('content-type', '').startswith('application/json') else {}
        print(f"Sessions: {len(data) if isinstance(data, list) else 'N/A'}")
    else:
        print(f"FAIL: Expected 200, got {r.status_code}")
        print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"FAIL: {e}")
print()

# Test 6: POST /api/auth/change-password
print("TEST 6: POST /api/auth/change-password")
NEW_PASSWORD = "NewSecurePass456!"
try:
    r = session.post(
        f"{BASE_URL}/api/auth/change-password",
        json={
            "current_password": TEST_PASSWORD,
            "new_password": NEW_PASSWORD
        },
        headers={"Content-Type": "application/json"}
    )
    print(f"HTTP: {r.status_code}")
    print(f"Response: {r.text[:200]}")
    if r.status_code == 200:
        print("PASS: Password changed")
        TEST_PASSWORD = NEW_PASSWORD  # Update for next login
    else:
        print(f"FAIL: Expected 200, got {r.status_code}")
except Exception as e:
    print(f"FAIL: {e}")
print()

# Test 7: POST /api/auth/forgot-password
print("TEST 7: POST /api/auth/forgot-password")
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/forgot-password",
        json={"email": TEST_EMAIL},
        headers={"Content-Type": "application/json"}
    )
    print(f"HTTP: {r.status_code}")
    print(f"Response: {r.text[:200]}")
    if r.status_code == 200:
        print("PASS: Password reset requested")
    else:
        print(f"FAIL: Expected 200, got {r.status_code}")
except Exception as e:
    print(f"FAIL: {e}")
print()

# Test 8: POST /api/auth/logout
print("TEST 8: POST /api/auth/logout")
try:
    r = session.post(f"{BASE_URL}/api/auth/logout")
    print(f"HTTP: {r.status_code}")
    print(f"Response: {r.text[:200]}")
    if r.status_code == 200:
        print("PASS: Logout successful")
    else:
        print(f"FAIL: Expected 200, got {r.status_code}")
except Exception as e:
    print(f"FAIL: {e}")
print()

# Test 9: GET /api/auth/me (After Logout)
print("TEST 9: GET /api/auth/me (After Logout)")
try:
    r = session.get(f"{BASE_URL}/api/auth/me")
    print(f"HTTP: {r.status_code}")
    if r.status_code == 401:
        print("PASS: Returns 401 after logout")
    else:
        print(f"FAIL: Expected 401, got {r.status_code}")
        print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"FAIL: {e}")
print()

print("=== PHASE 2 SUMMARY ===")
print("All tests completed. Check results above.")
