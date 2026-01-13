#!/usr/bin/env python3
"""
Test script để kiểm tra xem API key có được load đúng không
"""
import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 70)
print("  TEST LOAD API KEY")
print("=" * 70)
print()

# Check file .env exists
env_file = Path(__file__).resolve().parent / ".env"
print(f"1. File .env:")
print(f"   Location: {env_file}")
print(f"   Exists: {env_file.exists()}")
print()

if env_file.exists():
    # Read file content
    print("2. Đọc nội dung file .env:")
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('ANTHROPIC_API_KEY'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key_value = parts[1].strip()
                    print(f"   ✅ Dòng {i}: ANTHROPIC_API_KEY={key_value[:30]}... (độ dài: {len(key_value)})")
                else:
                    print(f"   ❌ Dòng {i}: {line}")
    except Exception as e:
        print(f"   ❌ Lỗi: {str(e)}")
    print()

# Test import api_ai
print("3. Test import api_ai module:")
try:
    # Clear any existing env var first
    if 'ANTHROPIC_API_KEY' in os.environ:
        del os.environ['ANTHROPIC_API_KEY']
    
    # Import module (this will trigger the load logic)
    from app.api_ai import ANTHROPIC_API_KEY, client
    
    print(f"   ANTHROPIC_API_KEY: {'SET' if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'dummy' else 'NOT SET'}")
    if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'dummy':
        print(f"   Key length: {len(ANTHROPIC_API_KEY)}")
        print(f"   Key starts with: {ANTHROPIC_API_KEY[:30]}...")
    print(f"   Client initialized: {'YES' if client else 'NO'}")
    print()
    
    if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'dummy' and client:
        print("=" * 70)
        print("  ✅ API KEY ĐÃ ĐƯỢC LOAD THÀNH CÔNG!")
        print("=" * 70)
    else:
        print("=" * 70)
        print("  ❌ API KEY CHƯA ĐƯỢC LOAD!")
        print("=" * 70)
        print()
        print("Vui lòng:")
        print("1. Kiểm tra file .env có đúng format không")
        print("2. Restart server sau khi sửa file .env")
        print("3. Xem console logs khi server khởi động")
        
except Exception as e:
    print(f"   ❌ Lỗi khi import: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)


