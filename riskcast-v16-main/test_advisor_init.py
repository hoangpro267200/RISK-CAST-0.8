"""
Test AdvisorCore initialization
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[OK] Loaded .env from: {env_file}")
else:
    print(f"[ERROR] .env file not found")
    exit(1)

# Check API key
api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"\n[TEST] API Key check:")
print(f"  - Found: {bool(api_key)}")
print(f"  - Length: {len(api_key) if api_key else 0}")
print(f"  - Starts with sk-ant: {api_key.startswith('sk-ant') if api_key else False}")
print(f"  - Not dummy: {api_key != 'your_anthropic_api_key_here' if api_key else False}")

# Test AdvisorCore init
print(f"\n[TEST] Initializing AdvisorCore...")
try:
    from app.ai_system_advisor.advisor_core import AdvisorCore
    
    advisor = AdvisorCore()
    
    print(f"\n[TEST] AdvisorCore initialized:")
    print(f"  - use_llm: {advisor.use_llm}")
    print(f"  - anthropic_client: {advisor.anthropic_client is not None}")
    
    if advisor.use_llm and advisor.anthropic_client:
        print(f"\n[OK] Claude client is initialized correctly!")
    else:
        print(f"\n[WARNING] Claude client not initialized")
        print(f"  - use_llm = {advisor.use_llm}")
        print(f"  - anthropic_client = {advisor.anthropic_client}")
        
        # Debug: Check API key again in advisor
        print(f"\n[DEBUG] Checking API key in advisor context...")
        import os
        key_in_env = os.getenv("ANTHROPIC_API_KEY")
        print(f"  - Key in env: {bool(key_in_env)}")
        print(f"  - Key length: {len(key_in_env) if key_in_env else 0}")
        
except Exception as e:
    print(f"\n[ERROR] Failed to initialize: {e}")
    import traceback
    traceback.print_exc()
