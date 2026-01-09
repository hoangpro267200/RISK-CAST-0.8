"""
Simple script to verify API key is working
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[OK] Loaded .env from: {env_file}")
else:
    print(f"[ERROR] .env file not found!")
    sys.exit(1)

# Check API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("[ERROR] API key not found in environment!")
    sys.exit(1)

print(f"[OK] API Key found (length: {len(api_key)})")
print(f"[OK] API Key format: {'Valid' if api_key.startswith('sk-ant-api03-') else 'Invalid'}")

# Test Anthropic client
try:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    print("[OK] Anthropic client initialized")
    
    # Test API call
    print("[TEST] Testing API call...")
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say 'API key is working!'"}]
    )
    
    reply = response.content[0].text
    print(f"[OK] API Response: {reply}")
    print("\n" + "="*50)
    print("SUCCESS! API key is configured and working!")
    print("="*50)
    print("\nYou can now:")
    print("1. Start the server: python -m uvicorn app.main:app --reload")
    print("2. Navigate to /results or /summary page")
    print("3. Use the AI Chat Panel to interact with the advisor")
    
except Exception as e:
    print(f"\n[ERROR] Failed to test API: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
