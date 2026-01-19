#!/usr/bin/env python3
"""
Script kiểm tra vị trí file .env mà api_ai.py đang tìm
"""
from pathlib import Path
import sys
import os

print("=" * 70)
print("  KIỂM TRA VỊ TRÍ FILE .ENV")
print("=" * 70)
print()

# Simulate what api_ai.py does
api_ai_path = Path(__file__).resolve().parent / "app" / "api_ai.py"
if api_ai_path.exists():
    print(f"1. File api_ai.py tại: {api_ai_path}")
    print()
    
    # Simulate: Path(__file__).resolve().parent.parent
    # When api_ai.py runs, __file__ = app/api_ai.py
    # So we simulate that
    simulated_file = Path(__file__).resolve().parent / "app" / "api_ai.py"
    root_dir_from_api_ai = simulated_file.resolve().parent.parent
    env_file_from_api_ai = root_dir_from_api_ai / ".env"
    
    print(f"2. api_ai.py tính toán:")
    print(f"   - __file__ sẽ là: {simulated_file}")
    print(f"   - .parent = {simulated_file.resolve().parent}")
    print(f"   - .parent.parent = {root_dir_from_api_ai}")
    print(f"   - env_file = {env_file_from_api_ai}")
    print()

# Simulate what main.py does
main_path = Path(__file__).resolve().parent / "app" / "main.py"
if main_path.exists():
    print(f"3. File main.py tại: {main_path}")
    print()
    
    simulated_main_file = Path(__file__).resolve().parent / "app" / "main.py"
    root_dir_from_main = simulated_main_file.resolve().parent.parent
    env_file_from_main = root_dir_from_main / ".env"
    
    print(f"4. main.py tính toán:")
    print(f"   - __file__ sẽ là: {simulated_main_file}")
    print(f"   - .parent = {simulated_main_file.resolve().parent}")
    print(f"   - .parent.parent = {root_dir_from_main}")
    print(f"   - env_file = {env_file_from_main}")
    print()

# Current directory
print(f"5. Thư mục hiện tại (working directory):")
print(f"   {Path.cwd()}")
print()

# Check actual .env location
actual_env = Path(__file__).resolve().parent / ".env"
print(f"6. File .env thực tế tại:")
print(f"   {actual_env}")
print(f"   - Tồn tại: {actual_env.exists()}")
print()

# Compare
print("7. So sánh:")
if env_file_from_api_ai == actual_env:
    print(f"   ✅ api_ai.py tìm đúng vị trí!")
    print(f"   ✅ {env_file_from_api_ai}")
else:
    print(f"   ❌ KHÔNG KHỚP!")
    print(f"   api_ai.py tìm tại: {env_file_from_api_ai}")
    print(f"   File thực tế tại:  {actual_env}")

if env_file_from_main == actual_env:
    print(f"   ✅ main.py tìm đúng vị trí!")
    print(f"   ✅ {env_file_from_main}")
else:
    print(f"   ❌ KHÔNG KHỚP!")
    print(f"   main.py tìm tại: {env_file_from_main}")
    print(f"   File thực tế tại:  {actual_env}")

print()
print("=" * 70)

# Check if file exists
if actual_env.exists():
    print("✅ File .env TỒN TẠI tại vị trí thực tế")
    print()
    print("Đang kiểm tra nội dung...")
    try:
        with open(actual_env, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'ANTHROPIC_API_KEY' in content:
                print("✅ File .env có chứa 'ANTHROPIC_API_KEY'")
                # Find the line
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if line.strip().startswith('ANTHROPIC_API_KEY'):
                        key_line = line.strip()
                        if '=' in key_line:
                            key_value = key_line.split('=', 1)[1].strip()
                            if key_value and key_value not in ['', 'dummy', 'YOUR_API_KEY_HERE', 'your_anthropic_api_key_here']:
                                print(f"✅ Key có giá trị (độ dài: {len(key_value)} ký tự)")
                                print(f"   Dòng {i}: ANTHROPIC_API_KEY=...")
                            else:
                                print(f"❌ Key không có giá trị hoặc là placeholder")
                                print(f"   Dòng {i}: {key_line[:60]}...")
                        else:
                            print(f"❌ Key không có dấu =")
                            print(f"   Dòng {i}: {key_line}")
                        break
            else:
                print("❌ File .env KHÔNG chứa 'ANTHROPIC_API_KEY'")
    except Exception as e:
        print(f"❌ Lỗi khi đọc file: {str(e)}")
else:
    print("❌ File .env KHÔNG TỒN TẠI tại vị trí thực tế")
    print()
    print("File .env cần được tạo tại:")
    print(f"   {actual_env}")


