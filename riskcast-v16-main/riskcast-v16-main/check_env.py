#!/usr/bin/env python3
"""
RISKCAST v16 - Environment Configuration Checker
Kiểm tra và hướng dẫn cấu hình ANTHROPIC_API_KEY
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def check_env_config():
    """Check environment configuration"""
    print("=" * 60)
    print("  RISKCAST v16 - Environment Configuration Check")
    print("=" * 60)
    print()
    
    # Try to load .env from project root
    project_root = Path(__file__).parent
    env_path = project_root / ".env"
    
    if env_path.exists():
        print(f"[OK] Found .env file at: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"[WARNING] .env file not found at: {env_path}")
        print("   Trying to load from current directory...")
        load_dotenv()
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print()
        print("[ERROR] ANTHROPIC_API_KEY is NOT SET")
        print()
        print("To fix this:")
        print("   1. Open file: .env (in project root)")
        print("   2. Add this line:")
        print("      ANTHROPIC_API_KEY=your_actual_api_key_here")
        print()
        print("   Get your API key from: https://console.anthropic.com/")
        print()
        return False
    
    if api_key == "your_anthropic_api_key_here" or api_key.startswith("your_"):
        print()
        print("[WARNING] ANTHROPIC_API_KEY is set but still has placeholder value")
        print(f"   Current value: {api_key[:30]}...")
        print()
        print("To fix this:")
        print("   1. Open file: .env")
        print("   2. Replace 'your_anthropic_api_key_here' with your actual API key")
        print("   3. Get your API key from: https://console.anthropic.com/")
        print()
        return False
    
    print()
    print("[OK] ANTHROPIC_API_KEY is configured!")
    print(f"   Key starts with: {api_key[:20]}...")
    print(f"   Key length: {len(api_key)} characters")
    print()
    
    # Test API connection
    print("Testing API connection...")
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        print("[OK] Anthropic client created successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Error creating Anthropic client: {e}")
        print()
        print("Please check:")
        print("  1. API key is correct")
        print("  2. You have internet connection")
        print("  3. API key has proper permissions")
        return False

if __name__ == "__main__":
    success = check_env_config()
    if success:
        print("=" * 60)
        print("  [OK] Configuration is OK!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  [ERROR] Configuration needs attention")
        print("=" * 60)
        exit(1)

