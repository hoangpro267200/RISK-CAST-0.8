#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Phase 4: Home Page Auth Buttons"""

import requests
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

def test_home_page():
    print("=== Testing Home Page Auth Buttons ===")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        if response.status_code != 200:
            print(f"[FAIL] Home page returned {response.status_code}")
            return False
        
        html = response.text
        
        # Check for auth buttons
        has_login = "Đăng nhập" in html or "login" in html.lower() or "/login" in html
        has_signup = "Đăng ký" in html or "signup" in html.lower() or "/signup" in html
        
        print(f"\nLogin button check: {'[PASS]' if has_login else '[FAIL]'}")
        print(f"Signup button check: {'[PASS]' if has_signup else '[FAIL]'}")
        
        # Extract relevant HTML section
        if "auth_enabled" in html or has_login or has_signup:
            # Find the auth section
            start_idx = html.find("Đăng nhập")
            if start_idx == -1:
                start_idx = html.find("/login")
            
            if start_idx != -1:
                snippet = html[max(0, start_idx-100):start_idx+200]
                print(f"\nHTML snippet:\n{snippet[:300]}")
        
        if has_login and has_signup:
            print("\n[PASS] Home page shows auth buttons")
            return True
        else:
            print("\n[FAIL] Home page does not show auth buttons")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Connection refused - is server running on {BASE_URL}?")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_home_page()
    sys.exit(0 if success else 1)
