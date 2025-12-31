#!/usr/bin/env python3
"""
Script test load .env và debug
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 70)
print("  TEST LOAD .ENV FILE")
print("=" * 70)
print()

env_file = Path(__file__).resolve().parent / ".env"

print(f"1. File .env:")
print(f"   {env_file}")
print(f"   Tồn tại: {env_file.exists()}")
print()

if not env_file.exists():
    print("❌ File .env không tồn tại!")
    exit(1)

# Đọc nội dung file
print("2. Đọc nội dung file .env:")
try:
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   ✅ Đã đọc được (độ dài: {len(content)} bytes)")
    print()
    
    # In ra các dòng (ẩn giá trị key)
    lines = content.split('\n')
    print("3. Nội dung file (ẩn giá trị key):")
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('ANTHROPIC_API_KEY'):
            parts = line.split('=', 1)
            if len(parts) == 2:
                key_name = parts[0]
                key_value = parts[1]
                print(f"   Dòng {i}: {key_name}={key_value[:20]}... (độ dài: {len(key_value)} ký tự)")
            else:
                print(f"   Dòng {i}: {line}")
        elif line.strip() and not line.strip().startswith('#'):
            print(f"   Dòng {i}: {line[:60]}...")
    print()
    
    # Kiểm tra encoding issues
    print("4. Kiểm tra encoding:")
    if content.startswith('\ufeff'):
        print("   ⚠️  File có BOM (Byte Order Mark) - có thể gây vấn đề")
    else:
        print("   ✅ Không có BOM")
    print()
    
except Exception as e:
    print(f"   ❌ Lỗi khi đọc file: {str(e)}")
    exit(1)

# Test load với dotenv
print("5. Test load với dotenv:")
api_key_before = os.getenv("ANTHROPIC_API_KEY")
print(f"   Key trước khi load: {api_key_before if api_key_before else 'None'}")
print()

# Load file
result = load_dotenv(env_file, override=True)
print(f"   load_dotenv() trả về: {result}")
print()

api_key_after = os.getenv("ANTHROPIC_API_KEY")
print(f"   Key sau khi load: {api_key_after if api_key_after else 'None'}")
print()

if api_key_after:
    print(f"   ✅ Key được load thành công!")
    print(f"   Độ dài: {len(api_key_after)} ký tự")
    print(f"   Bắt đầu bằng: {api_key_after[:30]}...")
else:
    print(f"   ❌ Key KHÔNG được load!")
    print()
    print("   Debug thêm:")
    print("   - Kiểm tra lại nội dung file")
    print("   - Kiểm tra encoding")
    print("   - Thử load với encoding khác")
    
    # Thử load với encoding khác
    print()
    print("   Thử load với encoding='utf-8-sig' (xử lý BOM):")
    try:
        from dotenv import dotenv_values
        env_vars = dotenv_values(env_file, encoding='utf-8-sig')
        test_key = env_vars.get('ANTHROPIC_API_KEY')
        if test_key:
            print(f"   ✅ Load được với utf-8-sig: {test_key[:30]}...")
        else:
            print(f"   ❌ Vẫn không load được")
    except Exception as e:
        print(f"   ❌ Lỗi: {str(e)}")

print()
print("=" * 70)


