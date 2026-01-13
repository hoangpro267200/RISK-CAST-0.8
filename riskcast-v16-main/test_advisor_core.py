"""
Test script to verify AdvisorCore is working with API key
"""

import os
import sys
import asyncio
from pathlib import Path

# Load .env file
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[TEST] Loaded .env from: {env_file}")
else:
    print(f"[TEST] WARNING: .env file not found at {env_file}")
    load_dotenv(override=False)

# Check API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("[TEST] ERROR: API key not found!")
    sys.exit(1)

print(f"[TEST] API Key found (length: {len(api_key)})")

# Test AdvisorCore
try:
    from app.ai_system_advisor.advisor_core import AdvisorCore
    
    print("\n[TEST] Initializing AdvisorCore...")
    advisor = AdvisorCore()
    
    if advisor.use_llm:
        print("[TEST] AdvisorCore initialized with LLM support: OK")
    else:
        print("[TEST] WARNING: AdvisorCore initialized but LLM is disabled")
        sys.exit(1)
    
    # Test processing a message
    print("\n[TEST] Testing message processing...")
    
    async def test_message():
        response = await advisor.process_message(
            message="What is the current risk score?",
            session_id="test-session-001",
            context={"page": "results"},
            language="en"
        )
        
        print(f"[TEST] Response received:")
        print(f"  - Reply length: {len(response.reply)} characters")
        print(f"  - Reply preview: {response.reply[:100]}...")
        print(f"  - Actions: {len(response.actions)}")
        print(f"  - Function calls: {len(response.function_calls)}")
        print(f"  - Metadata: {response.metadata}")
        
        if response.reply and len(response.reply) > 0:
            print("\n[TEST] SUCCESS! AdvisorCore is working correctly!")
            return True
        else:
            print("\n[TEST] WARNING: Response is empty")
            return False
    
    result = asyncio.run(test_message())
    
    if result:
        print("\n[TEST] All tests passed!")
        sys.exit(0)
    else:
        print("\n[TEST] Some tests failed")
        sys.exit(1)
    
except Exception as e:
    print(f"\n[TEST] ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
