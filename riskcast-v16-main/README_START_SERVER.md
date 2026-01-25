# Hướng Dẫn Khởi Động Server RISKCAST V3

## Cách Khởi Động Server

### Phương Pháp 1: Sử dụng Script Python (Khuyến nghị)

```bash
python start_server.py
```

### Phương Pháp 2: Sử dụng Batch File (Windows)

```bash
start_server.bat
```

### Phương Pháp 3: Sử dụng Uvicorn trực tiếp

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Kiểm Tra Server

Sau khi khởi động server, bạn có thể:

1. **Kiểm tra server đang chạy:**
   ```bash
   python test_server.py
   ```

2. **Truy cập các endpoints:**
   - Root: http://127.0.0.1:8000/
   - Health Check: http://127.0.0.1:8000/health
   - API Documentation: http://127.0.0.1:8000/docs (nếu DEBUG=true)
   - API v3: http://127.0.0.1:8000/api/v3

## Cấu Hình

File `.env` chứa các cấu hình quan trọng:

- `ENVIRONMENT=development` - Môi trường chạy
- `DEBUG=true` - Bật debug mode và API docs
- `DATABASE_URL=sqlite:///./riskcast.db` - Database SQLite cho development
- `LOG_LEVEL=INFO` - Mức độ logging

## Xử Lý Lỗi

### Server không khởi động được

1. Kiểm tra Python version: `python --version` (cần Python 3.8+)
2. Cài đặt dependencies: `pip install -r requirements.txt`
3. Kiểm tra port 8000 có đang được sử dụng không

### Database connection error

- SQLite sẽ tự động tạo database file nếu chưa tồn tại
- Nếu dùng MySQL/PostgreSQL, đảm bảo database đã được tạo và credentials đúng

### Import errors

- Đảm bảo đang ở đúng thư mục gốc của project
- Kiểm tra `PYTHONPATH` nếu cần

## Troubleshooting

### Port đã được sử dụng

Nếu port 8000 đã được sử dụng, bạn có thể:
1. Dừng process đang sử dụng port 8000
2. Hoặc thay đổi port trong `start_server.py` hoặc `.env`

### Dependencies thiếu

```bash
pip install -r requirements.txt
```

### Database migrations

Nếu cần tạo/update database tables:
```bash
alembic upgrade head
```

## Logs

Server logs sẽ hiển thị:
- Startup messages
- Database connection status
- Request logs (nếu bật)
- Error messages (nếu có)

## Dừng Server

Nhấn `CTRL+C` trong terminal để dừng server.
