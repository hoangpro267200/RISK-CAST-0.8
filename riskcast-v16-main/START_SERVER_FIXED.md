# Hướng Dẫn Khởi Động Server - Đã Sửa

## Vấn Đề Đã Sửa

1. **Foreign Key Errors**: Đã sửa các foreign key trong model Policy để sử dụng `use_alter=True`
2. **Database Initialization**: Đã sửa `init_db()` để chỉ verify connection, không tạo tables tự động
3. **Model Syntax**: Đã sửa lỗi syntax trong Policy model (evidence_bundle_id)

## Cách Khởi Động Server

### Bước 1: Chạy Migrations (Nếu chưa chạy)

```powershell
cd riskcast-v16-main
alembic upgrade head
```

### Bước 2: Khởi Động Server

**Cách 1: Sử dụng dev_run.py (Khuyến nghị)**
```powershell
python dev_run.py
```

**Cách 2: Sử dụng uvicorn trực tiếp**
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Cách 3: Sử dụng script PowerShell**
```powershell
.\start-server-simple.ps1
```

### Bước 3: Kiểm Tra Server

Mở browser và truy cập:
- API: http://127.0.0.1:8000
- Health Check: http://127.0.0.1:8000/health
- API Docs: http://127.0.0.1:8000/docs

## Lưu Ý

1. **Database**: Đảm bảo MySQL đang chạy và database đã được tạo
2. **Migrations**: Phải chạy `alembic upgrade head` trước khi start server
3. **Environment Variables**: Kiểm tra file `.env` có đúng cấu hình không

## Troubleshooting

### Lỗi "Cannot find table 'quotes'"
- Chạy migrations: `alembic upgrade head`

### Lỗi "Database connection failed"
- Kiểm tra MySQL đang chạy
- Kiểm tra DATABASE_URL trong `.env`
- Kiểm tra user/password có đúng không

### Lỗi "Foreign key constraint"
- Đã được sửa bằng cách sử dụng `use_alter=True` trong models
- Nếu vẫn lỗi, chạy lại migrations

## Các File Đã Sửa

1. `app/database.py` - Sửa init_db() để không tạo tables tự động
2. `app/database/__init__.py` - Sửa init_db() để chỉ verify connection
3. `app/modules/underwriting/models.py` - Sửa foreign keys với use_alter=True
4. `app/main.py` - Sửa error handling trong lifespan
