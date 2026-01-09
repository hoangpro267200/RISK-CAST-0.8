"""
Test script to verify all imports work before starting server
"""

import sys
from pathlib import Path

# Load .env
from dotenv import load_dotenv
root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[OK] Loaded .env from: {env_file}")

print("\n[TEST] Testing imports...")

try:
    print("1. Testing context_manager...")
    from app.ai_system_advisor.context_manager import ContextManager
    print("   [OK] ContextManager imported")
    
    print("2. Testing data_access...")
    from app.ai_system_advisor.data_access import DataAccess
    print("   [OK] DataAccess imported")
    
    print("3. Testing function_registry...")
    from app.ai_system_advisor.function_registry import FunctionRegistry
    print("   [OK] FunctionRegistry imported")
    
    print("4. Testing action_handlers...")
    from app.ai_system_advisor.action_handlers import ActionHandlers
    print("   [OK] ActionHandlers imported")
    
    print("5. Testing advisor_core...")
    from app.ai_system_advisor.advisor_core import AdvisorCore
    print("   [OK] AdvisorCore imported")
    
    print("6. Testing API routes...")
    from app.api.v1.ai_advisor_routes import router
    print("   [OK] AI Advisor routes imported")
    
    print("7. Testing main app...")
    from app.main import app
    print("   [OK] FastAPI app imported")
    
    print("\n" + "="*50)
    print("SUCCESS! All imports working. Server should start now.")
    print("="*50)
    print("\nYou can now start the server with:")
    print("  python -m uvicorn app.main:app --reload")
    
except Exception as e:
    print(f"\n[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
