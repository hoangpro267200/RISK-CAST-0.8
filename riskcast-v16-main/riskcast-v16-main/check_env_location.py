#!/usr/bin/env python3
"""
Kiểm tra vị trí file .env mà api_ai.py đang tìm
"""
from pathlib import Path
import os

print("=" * 70)
print("  KIỂM TRA VỊ TRÍ FILE .ENV")
print("=" * 70)
print()

# Giả lập cách api_ai.py tìm file .env
# api_ai.py nằm tại: c:\Users\ASUS\RICK CAST\app\api_ai.py
api_ai_file_path = Path(__file__).resolve().parent / "app" / "api_ai.py"
print(f"1. Đường dẫn file api_ai.py:")
print(f"   {api_ai_file_path}")
print()

# Khi api_ai.py chạy, __file__ = "app/api_ai.py"
# Path(__file__).resolve() = "C:\Users\ASUS\RICK CAST\app\api_ai.py"
# .parent = "C:\Users\ASUS\RICK CAST\app"
# .parent.parent = "C:\Users\ASUS\RICK CAST"
# root_dir / ".env" = "C:\Users\ASUS\RICK CAST\.env"

simulated_api_ai = Path("app/api_ai.py").resolve()
root_dir = simulated_api_ai.parent.parent
env_file_location = root_dir / ".env"

print(f"2. api_ai.py tính toán vị trí .env như sau:")
print(f"   - __file__ (khi api_ai.py chạy): {simulated_api_ai}")
print(f"   - .parent: {simulated_api_ai.parent}")
print(f"   - .parent.parent (root_dir): {root_dir}")
print(f"   - root_dir / '.env': {env_file_location}")
print()

# Kiểm tra file có tồn tại không
print(f"3. Kiểm tra file .env:")
print(f"   Vị trí api_ai.py tìm: {env_file_location}")
print(f"   File tồn tại: {env_file_location.exists()}")
print()

# Kiểm tra các vị trí khác có thể có
possible_locations = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent / ".env",
    Path("app/api_ai.py").resolve().parent.parent / ".env",
]

print(f"4. Các vị trí có thể có file .env:")
for loc in possible_locations:
    exists = loc.exists()
    marker = "✅" if exists else "❌"
    print(f"   {marker} {loc}")
    print(f"      Tồn tại: {exists}")
print()

# Tìm file .env thực tế
print(f"5. Tìm file .env thực tế:")
found_env = None
for loc in possible_locations:
    if loc.exists():
        found_env = loc
        print(f"   ✅ Tìm thấy tại: {loc}")
        break

if not found_env:
    print(f"   ❌ Không tìm thấy file .env ở bất kỳ vị trí nào!")
    print()
    print(f"   File .env cần được tạo tại:")
    print(f"   {env_file_location}")
else:
    if found_env == env_file_location:
        print(f"   ✅ Vị trí file khớp với nơi api_ai.py đang tìm!")
    else:
        print(f"   ⚠️  Vị trí file KHÔNG khớp!")
        print(f"   api_ai.py tìm tại: {env_file_location}")
        print(f"   File thực tế tại:  {found_env}")

print()
print("=" * 70)


