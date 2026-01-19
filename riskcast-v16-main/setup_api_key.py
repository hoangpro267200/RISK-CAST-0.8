"""
Script to set up ANTHROPIC_API_KEY in .env file
SECURITY: This script does NOT contain API keys - users must provide their own key
"""

import os
import sys
from pathlib import Path

def setup_api_key():
    """Set up API key in .env file"""
    # Get API key from user input or environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY_INPUT")
    
    if not api_key:
        print("=" * 60)
        print("RISKCAST - API Key Setup")
        print("=" * 60)
        print("\nPlease enter your Anthropic API key.")
        print("You can get it from: https://console.anthropic.com/")
        print("\nAPI key format: sk-ant-api03-...")
        print("\n⚠️  SECURITY: Your API key will be stored in .env file (already in .gitignore)")
        print("=" * 60)
        
        api_key = input("\nEnter your API key (or press Enter to use environment variable): ").strip()
        
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("\n❌ ERROR: No API key provided!")
                print("Please provide API key either:")
                print("  1. As input when running this script")
                print("  2. As environment variable: ANTHROPIC_API_KEY")
                print("  3. Set ANTHROPIC_API_KEY_INPUT environment variable")
                sys.exit(1)
    
    # Validate API key format
    if not api_key.startswith("sk-ant-api03-"):
        print("\n⚠️  WARNING: API key format may be invalid!")
        print("Expected format: sk-ant-api03-...")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    
    # Get project root directory
    root_dir = Path(__file__).resolve().parent
    env_file = root_dir / ".env"
    
    # Create .env file
    env_content = f"ANTHROPIC_API_KEY={api_key}\n"
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"\n✅ Created .env file at: {env_file}")
        print(f"✅ API key has been set (length: {len(api_key)})")
        
        # Verify
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if api_key in content:
                    print("✅ Verification: API key is correctly written to .env file")
                else:
                    print("❌ ERROR: Verification failed: API key not found in .env file")
        else:
            print("❌ ERROR: .env file was not created")
            
    except Exception as e:
        print(f"❌ ERROR: Error creating .env file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    setup_api_key()
