"""
Test script to verify AI Advisor API key is working
"""

import os
import sys
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
print(f"\n[TEST] API Key Status:")
print(f"  - Found: {bool(api_key)}")
if api_key:
    print(f"  - Length: {len(api_key)}")
    print(f"  - Starts with: {api_key[:20]}...")
    print(f"  - Valid format: {api_key.startswith('sk-ant-api03-')}")
else:
    print("  - ERROR: API key not found!")
    sys.exit(1)

# Test Anthropic client initialization
try:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    print(f"\n[TEST] Anthropic Client:")
    print(f"  - Initialized: OK")
    
    # Test a simple API call
    print(f"\n[TEST] Testing API call...")
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say 'Hello, RISKCAST!' in one sentence."}]
    )
    
    reply = response.content[0].text
    print(f"  - Response: {reply}")
    print(f"\n[TEST] SUCCESS! API key is working correctly!")
    
except Exception as e:
    print(f"\n[TEST] ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
