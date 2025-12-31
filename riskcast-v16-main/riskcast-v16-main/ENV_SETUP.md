# Hướng dẫn cấu hình API Key cho RISKCAST AI

## Vấn đề
Nếu AI chat hiển thị lỗi "Xin lỗi, đã xảy ra lỗi khi kết nối với AI", có thể do API key chưa được cấu hình.

## Cách khắc phục

### Bước 1: Tạo file .env
Tạo file `.env` trong thư mục gốc của project (cùng cấp với thư mục `app/`)

### Bước 2: Thêm API Key
Thêm dòng sau vào file `.env`:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### Bước 3: Lấy API Key
1. Truy cập: https://console.anthropic.com/
2. Đăng ký/Đăng nhập tài khoản Anthropic
3. Vào phần "API Keys"
4. Tạo API key mới
5. Copy API key và paste vào file `.env` (thay thế `your_actual_api_key_here`)

### Bước 4: Restart Server
Sau khi thêm API key, **bắt buộc phải restart server**:
1. Dừng server hiện tại (nhấn `Ctrl+C` trong terminal)
2. Khởi động lại server:
   ```bash
   python app.py
   ```

### Bước 5: Kiểm tra
- Mở browser và vào trang web
- Thử gửi tin nhắn trong AI chat
- Nếu vẫn lỗi, kiểm tra Console (F12) để xem log chi tiết

## Lưu ý
- File `.env` không nên được commit lên Git (đã có trong .gitignore)
- API key là thông tin bảo mật, không chia sẻ với người khác
- Nếu API key hết hạn hoặc bị thu hồi, cần tạo key mới

## Ví dụ file .env
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```






















