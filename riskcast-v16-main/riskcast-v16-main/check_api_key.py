#!/usr/bin/env python3
"""
Script kiểm tra ANTHROPIC_API_KEY
Chạy script này để kiểm tra xem API key có được cấu hình đúng không
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("  KIỂM TRA ANTHROPIC_API_KEY")
print("=" * 60)
print()

# Tìm file .env
root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"

print(f"1. Đang tìm file .env tại: {env_file}")
print(f"   - File tồn tại: {env_file.exists()}")
print()

if not env_file.exists():
    print("❌ FILE .ENV KHÔNG TỒN TẠI!")
    print()
    print("   Cần tạo file .env tại thư mục root project với nội dung:")
    print("   ANTHROPIC_API_KEY=sk-ant-api03-YOUR_API_KEY_HERE")
    print()
    print("   Lấy API key tại: https://console.anthropic.com/")
    exit(1)

# Load .env
print(f"2. Đang load file .env...")
load_dotenv(env_file, override=True)
print(f"   ✅ Đã load file .env")
print()

# Kiểm tra key
print("3. Đang kiểm tra ANTHROPIC_API_KEY...")
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("   ❌ ANTHROPIC_API_KEY KHÔNG TỒN TẠI trong file .env!")
    print()
    print("   Vui lòng thêm dòng sau vào file .env:")
    print("   ANTHROPIC_API_KEY=sk-ant-api03-YOUR_API_KEY_HERE")
    exit(1)

print(f"   ✅ Key tồn tại (độ dài: {len(api_key)} ký tự)")
print()

# Validate key
print("4. Đang validate key...")
if api_key == "dummy":
    print("   ❌ Key là giá trị mặc định 'dummy'")
    print("   Vui lòng cập nhật key thực tế trong file .env")
    exit(1)

if api_key == "your_anthropic_api_key_here":
    print("   ❌ Key vẫn là placeholder")
    print("   Vui lòng thay thế bằng key thực tế")
    exit(1)

if len(api_key) <= 20:
    print(f"   ❌ Key quá ngắn (độ dài: {len(api_key)}), cần > 20 ký tự")
    print(f"   Key hiện tại: {api_key[:30]}...")
    exit(1)

if not api_key.startswith("sk-ant-"):
    print(f"   ⚠️  Key không bắt đầu bằng 'sk-ant-' (có thể không phải Anthropic key)")
    print(f"   Key bắt đầu bằng: {api_key[:10]}...")

print(f"   ✅ Key hợp lệ")
print(f"   Key bắt đầu bằng: {api_key[:20]}...")
print()

print("=" * 60)
print("  ✅ TẤT CẢ KIỂM TRA ĐỀU THÀNH CÔNG!")
print("=" * 60)
print()
print("Nếu server vẫn báo lỗi, hãy:")
print("1. Restart server để load lại .env")
print("2. Kiểm tra log khi server khởi động")
print("3. Xem console logs trong browser để debug")


