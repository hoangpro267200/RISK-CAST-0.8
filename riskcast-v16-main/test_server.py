#!/usr/bin/env python3
"""
Test script để verify server đang chạy và hoạt động đúng
"""
import requests
import time
import sys

def test_server(base_url="http://127.0.0.1:8000", max_retries=10, retry_delay=2):
    """Test server endpoints"""
    print("="*60)
    print("RISKCAST V3 - Server Test")
    print("="*60)
    
    # Wait for server to be ready
    print(f"\n[INFO] Waiting for server at {base_url}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"[OK] Server is running!")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                print(f"[INFO] Retry {i+1}/{max_retries}...")
                time.sleep(retry_delay)
            else:
                print(f"[ERROR] Server not responding after {max_retries} retries")
                print("[INFO] Make sure server is running: python start_server.py")
                return False
    
    # Test root endpoint
    print("\n[TEST] Testing root endpoint (/)...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Root endpoint: {data}")
        else:
            print(f"[ERROR] Root endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Root endpoint test failed: {e}")
        return False
    
    # Test health endpoint
    print("\n[TEST] Testing health endpoint (/health)...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Health endpoint: {data}")
        else:
            print(f"[ERROR] Health endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Health endpoint test failed: {e}")
        return False
    
    # Test API v3 endpoint (if available)
    print("\n[TEST] Testing API v3 endpoint (/api/v3)...")
    try:
        response = requests.get(f"{base_url}/api/v3", timeout=5)
        print(f"[INFO] API v3 endpoint status: {response.status_code}")
        if response.status_code in [200, 404]:  # 404 is OK if endpoint doesn't exist
            print("[OK] API v3 endpoint accessible")
        else:
            print(f"[WARNING] API v3 endpoint returned status {response.status_code}")
    except Exception as e:
        print(f"[WARNING] API v3 endpoint test: {e}")
    
    # Test docs endpoint
    print("\n[TEST] Testing docs endpoint (/docs)...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("[OK] API documentation available at /docs")
        else:
            print(f"[INFO] Docs endpoint status: {response.status_code}")
    except Exception as e:
        print(f"[WARNING] Docs endpoint test: {e}")
    
    print("\n" + "="*60)
    print("[SUCCESS] Server tests completed!")
    print(f"[INFO] Server URL: {base_url}")
    print(f"[INFO] API Docs: {base_url}/docs")
    print(f"[INFO] Health Check: {base_url}/health")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)
