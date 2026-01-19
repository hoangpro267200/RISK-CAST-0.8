"""
Test AI Advisor with Claude API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_ai_with_claude():
    """Test AI advisor with a question that should trigger Claude"""
    print("\n[TEST] Testing AI Advisor with Claude API...")
    print("="*50)
    
    test_message = {
        "message": "What are the top 3 risk drivers for this shipment?",
        "session_id": "test-session-claude-001",
        "context": {
            "page": "results",
            "riskScore": 65.5
        },
        "options": {
            "language": "en"
        }
    }
    
    try:
        print(f"\n[TEST] Sending request...")
        print(f"[TEST] Message: {test_message['message']}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/advisor/chat",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"\n[TEST] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success':
                reply = data.get('data', {}).get('reply', '')
                metadata = data.get('data', {}).get('metadata', {})
                model = metadata.get('model', 'unknown')
                
                print(f"\n[OK] SUCCESS!")
                print(f"[OK] Model used: {model}")
                print(f"[OK] Reply length: {len(reply)} characters")
                print(f"\n[OK] AI Reply:")
                print("-" * 50)
                print(reply[:500])
                if len(reply) > 500:
                    print("...")
                print("-" * 50)
                
                if model != 'deterministic':
                    print("\n[OK] Claude API is being used!")
                else:
                    print("\n[WARNING] Using deterministic fallback (Claude not called)")
                
                return True
            else:
                error = data.get('error', {})
                print(f"\n[ERROR] API error: {error}")
                return False
        else:
            print(f"\n[ERROR] HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*50)
    print("AI ADVISOR CLAUDE API TEST")
    print("="*50)
    
    success = test_ai_with_claude()
    
    print("\n" + "="*50)
    if success:
        print("[OK] TEST COMPLETE")
    else:
        print("[ERROR] TEST FAILED")
