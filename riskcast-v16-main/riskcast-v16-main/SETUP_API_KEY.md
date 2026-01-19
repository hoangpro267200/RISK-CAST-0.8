# 🔑 Hướng dẫn cấu hình ANTHROPIC_API_KEY

## ⚠️ Lỗi hiện tại
API key không hợp lệ hoặc đã hết hạn. Bạn cần lấy API key mới từ Anthropic.

## 📝 Các bước cấu hình API key

### Bước 1: Lấy API key từ Anthropic Console

1. **Truy cập Anthropic Console**
   - Mở trình duyệt và vào: https://console.anthropic.com/
   - Đăng nhập vào tài khoản Anthropic của bạn
   - Nếu chưa có tài khoản, đăng ký tại: https://www.anthropic.com/

2. **Tạo API key mới**
   - Vào **Settings** → **API Keys**
   - Click **Create Key** hoặc **New Key**
   - Copy API key (bắt đầu bằng `sk-ant-api03-`)
   - ⚠️ **Lưu ý**: API key chỉ hiển thị một lần, hãy copy ngay!

### Bước 2: Cập nhật file .env

1. **Mở file .env**
   - Đường dẫn: `C:\Users\ADMIN\Desktop\HoangBui\riskcast-v16\.env`
   - Mở bằng Notepad hoặc bất kỳ text editor nào

2. **Cập nhật API key**
   - Tìm dòng: `ANTHROPIC_API_KEY=sk-ant-api03-...`
   - Thay thế bằng API key mới của bạn:
     ```
     ANTHROPIC_API_KEY=sk-ant-api03-YOUR_NEW_API_KEY_HERE
     ```
   - ⚠️ **Quan trọng**: 
     - Không có khoảng trắng trước/sau dấu `=`
     - Không có dấu ngoặc kép
     - Copy toàn bộ API key (thường dài khoảng 100-110 ký tự)

3. **Lưu file**

### Bước 3: Khởi động lại server

1. **Dừng server hiện tại**
   - Trong terminal đang chạy server, nhấn `Ctrl+C`

2. **Khởi động lại server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

3. **Kiểm tra**
   - Bạn sẽ thấy trong console:
     ```
     [INFO] Anthropic client initialized (API key: sk-ant-api03-...)
     ```

### Bước 4: Kiểm tra API key

Chạy script kiểm tra:
```bash
python check_env.py
```

Hoặc test trực tiếp:
```bash
python -c "from app.api_ai import ANTHROPIC_API_KEY, client; print('API Key:', 'SET' if ANTHROPIC_API_KEY else 'NOT SET'); print('Client:', 'OK' if client else 'NOT INITIALIZED')"
```

## ✅ Xác nhận thành công

Khi API key hợp lệ, bạn sẽ thấy:
- Console: `[INFO] Anthropic client initialized`
- Health check: `{"status": "ok", "model": "claude-3-5-sonnet"}`
- AI chat hoạt động bình thường

## 🔍 Troubleshooting

### Lỗi: "File .env does not exist"
- Tạo file `.env` mới trong thư mục gốc dự án
- Copy nội dung từ `.env_1` và cập nhật API key

### Lỗi: "Permission denied"
- Đảm bảo file `.env` không bị lock bởi ứng dụng khác
- Thử chạy text editor với quyền Administrator

### Lỗi: "API key vẫn không hợp lệ"
- Kiểm tra lại API key đã copy đúng chưa
- Đảm bảo không có khoảng trắng thừa
- Thử tạo API key mới từ Anthropic Console
- Đảm bảo đã khởi động lại server sau khi sửa file `.env`

## 📞 Hỗ trợ

Nếu vẫn gặp vấn đề:
1. Kiểm tra logs server để xem chi tiết lỗi
2. Xác nhận API key có quyền truy cập Anthropic API
3. Kiểm tra kết nối internet
4. Xác nhận tài khoản Anthropic có credit/quota

