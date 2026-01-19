#!/usr/bin/env python3
"""
Script kiểm tra và sửa file .env
Giúp bạn kiểm tra và tạo/sửa file .env đúng cách
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 70)
print("  KIỂM TRA VÀ SỬA FILE .ENV")
print("=" * 70)
print()

# Tìm file .env
root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"

print(f"📍 Đường dẫn file .env: {env_file}")
print()

# Kiểm tra file tồn tại
if not env_file.exists():
    print("❌ FILE .ENV KHÔNG TỒN TẠI!")
    print()
    print("Đang tạo file .env mẫu...")
    
    # Tạo file .env mẫu
    sample_content = """# RISKCAST Configuration
# Lấy API key tại: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_API_KEY_HERE

# Optional settings
APP_NAME=RISKCAST
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        print(f"✅ Đã tạo file .env tại: {env_file}")
        print()
        print("⚠️  VUI LÒNG:")
        print("   1. Mở file .env vừa tạo")
        print("   2. Thay thế 'YOUR_API_KEY_HERE' bằng API key thực tế của bạn")
        print("   3. Lấy API key tại: https://console.anthropic.com/")
        print()
        print("   Format đúng:")
        print("   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxx")
        print()
    except Exception as e:
        print(f"❌ Không thể tạo file .env: {str(e)}")
        exit(1)
else:
    print("✅ File .env đã tồn tại")
    print()
    
    # Kiểm tra nội dung file
    print("📝 Đang kiểm tra nội dung file...")
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Tìm dòng ANTHROPIC_API_KEY
        key_line = None
        key_line_number = None
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('ANTHROPIC_API_KEY'):
                key_line = stripped
                key_line_number = i
                break
        
        if not key_line:
            print("❌ Không tìm thấy dòng 'ANTHROPIC_API_KEY' trong file .env!")
            print()
            print("Vui lòng thêm dòng sau vào file .env:")
            print("ANTHROPIC_API_KEY=sk-ant-api03-your_actual_key_here")
            print()
            print(f"File location: {env_file}")
            exit(1)
        
        print(f"✅ Tìm thấy dòng ANTHROPIC_API_KEY tại dòng {key_line_number}")
        print()
        
        # Kiểm tra format
        if '=' not in key_line:
            print(f"❌ Format sai! Dòng {key_line_number} không có dấu '='")
            print(f"   Dòng hiện tại: {key_line}")
            print()
            print("Format đúng: ANTHROPIC_API_KEY=your_key_here")
            exit(1)
        
        parts = key_line.split('=', 1)
        key_value = parts[1].strip() if len(parts) > 1 else ''
        
        if not key_value:
            print(f"❌ Key không có giá trị! Dòng {key_line_number}")
            print(f"   Dòng hiện tại: {key_line}")
            print()
            print("Vui lòng thêm giá trị sau dấu =")
            print("Format: ANTHROPIC_API_KEY=sk-ant-api03-your_actual_key_here")
            exit(1)
        
        if key_value in ['YOUR_API_KEY_HERE', 'your_anthropic_api_key_here', 'dummy']:
            print(f"⚠️  Key vẫn là placeholder!")
            print(f"   Dòng {key_line_number}: {key_line[:60]}...")
            print()
            print("Vui lòng thay thế bằng API key thực tế")
            print("Lấy API key tại: https://console.anthropic.com/")
            exit(1)
        
        if len(key_value) <= 20:
            print(f"⚠️  Key quá ngắn (độ dài: {len(key_value)})")
            print(f"   Key bắt đầu bằng: {key_value[:30]}...")
            print()
            print("API key thường có độ dài > 100 ký tự")
            print("Vui lòng kiểm tra lại key của bạn")
            exit(1)
        
        print(f"✅ Key có giá trị hợp lệ (độ dài: {len(key_value)} ký tự)")
        print(f"   Key bắt đầu bằng: {key_value[:30]}...")
        print()
        
        # Load và test
        print("🔄 Đang load file .env và kiểm tra...")
        load_dotenv(env_file, override=True)
        loaded_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not loaded_key or loaded_key != key_value:
            print("❌ Key không được load đúng!")
            print(f"   Key trong file: {key_value[:30]}...")
            print(f"   Key sau khi load: {loaded_key[:30] if loaded_key else 'None'}...")
            print()
            print("Có thể có vấn đề với:")
            print("  - Khoảng trắng thừa")
            print("  - Ký tự đặc biệt")
            print("  - Encoding của file")
            exit(1)
        
        print("✅ Key được load thành công!")
        print()
        
        print("=" * 70)
        print("  ✅ FILE .ENV ĐÃ ĐÚNG!")
        print("=" * 70)
        print()
        print("Nếu server vẫn báo lỗi:")
        print("  1. Restart server (Ctrl+C rồi chạy lại)")
        print("  2. Kiểm tra console logs khi server khởi động")
        print("  3. Đảm bảo không có khoảng trắng thừa trong file .env")
        
    except Exception as e:
        print(f"❌ Lỗi khi đọc file .env: {str(e)}")
        exit(1)


