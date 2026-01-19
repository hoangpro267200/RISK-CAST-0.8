"""
Test script to verify AI Advisor endpoint is working
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_ai_chat():
    """Test the AI chat endpoint"""
    print("\n[TEST] Testing AI Advisor Chat Endpoint...")
    print("="*50)
    
    # Test data
    test_message = {
        "message": "Hello, what can you help me with?",
        "session_id": "test-session-001",
        "context": {
            "page": "results"
        },
        "options": {
            "language": "en"
        }
    }
    
    try:
        print(f"\n[TEST] Sending request to: {BASE_URL}/api/v1/advisor/chat")
        print(f"[TEST] Message: {test_message['message']}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/advisor/chat",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n[TEST] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[TEST] Response Status: {data.get('status')}")
            
            if data.get('status') == 'success':
                reply = data.get('data', {}).get('reply', '')
                session_id = data.get('data', {}).get('session_id', '')
                
                print(f"\n[OK] SUCCESS!")
                print(f"[OK] Session ID: {session_id}")
                print(f"[OK] AI Reply (first 200 chars): {reply[:200]}...")
                print(f"[OK] Reply length: {len(reply)} characters")
                
                actions = data.get('data', {}).get('actions', [])
                if actions:
                    print(f"[OK] Actions available: {len(actions)}")
                    for action in actions:
                        print(f"     - {action.get('label', 'Unknown')}")
                
                return True
            else:
                error = data.get('error', {})
                print(f"\n[ERROR] API returned error:")
                print(f"  Code: {error.get('code', 'Unknown')}")
                print(f"  Message: {error.get('message', 'Unknown')}")
                return False
        else:
            print(f"\n[ERROR] HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data}")
            except:
                print(f"  Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Cannot connect to server at {BASE_URL}")
        print("[INFO] Make sure the server is running:")
        print("  python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        return response.status_code in [200, 303, 307]
    except:
        return False

if __name__ == "__main__":
    print("="*50)
    print("AI ADVISOR ENDPOINT TEST")
    print("="*50)
    
    # Check if server is running
    print("\n[TEST] Checking if server is running...")
    if test_health():
        print("[OK] Server is running")
    else:
        print("[ERROR] Server is not running!")
        print("[INFO] Start the server with:")
        print("  python -m uvicorn app.main:app --reload")
        exit(1)
    
    # Test chat endpoint
    success = test_ai_chat()
    
    print("\n" + "="*50)
    if success:
        print("[OK] ALL TESTS PASSED!")
        print("="*50)
        print("\nAI Advisor is working correctly!")
        print("You can now use the chat panel in the Results/Summary pages.")
    else:
        print("[ERROR] TESTS FAILED")
        print("="*50)
        print("\nPlease check the error messages above.")
