#!/usr/bin/env python3
"""Test script to verify .env file and API key loading"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("="*60)
print("RISKCAST - Environment Configuration Test")
print("="*60)
print()

# Check .env file
env_path = Path('.env')
print(f"[1] Checking .env file...")
print(f"    Path: {env_path.absolute()}")
print(f"    Exists: {env_path.exists()}")

if env_path.exists():
    print(f"    Size: {env_path.stat().st_size} bytes")
    content = env_path.read_text(encoding='utf-8')
    print(f"    Content length: {len(content)} chars")
    print(f"    First line: {repr(content.splitlines()[0] if content.splitlines() else '')}")
else:
    print("    ❌ .env file not found!")
    print()
    exit(1)

print()

# Load .env
print("[2] Loading .env file...")
load_dotenv(env_path)
print("    ✓ Loaded")

print()

# Check API key
print("[3] Checking ANTHROPIC_API_KEY...")
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("    ❌ ANTHROPIC_API_KEY not found in environment")
    print()
    exit(1)

print(f"    Key exists: ✓")
print(f"    Key length: {len(api_key)} chars")
print(f"    Key starts with: {api_key[:20]}...")

if len(api_key) < 20:
    print("    ❌ Key is too short (should be > 20 chars)")
    exit(1)

if api_key == "your_anthropic_api_key_here" or api_key.startswith("your_"):
    print("    ❌ Key is still a placeholder")
    exit(1)

print("    ✓ Key appears valid")
print()

print("="*60)
print("✅ ALL CHECKS PASSED!")
print("="*60)
print()
print("You can now run the server with:")
print("  python run_server.py")
print()


