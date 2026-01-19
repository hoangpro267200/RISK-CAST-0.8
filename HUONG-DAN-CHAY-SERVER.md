# 🚀 HƯỚNG DẪN CHẠY RISKCAST SERVER

## ⚠️ VẤN ĐỀ HIỆN TẠI

Bạn đang gặp lỗi `ModuleNotFoundError: No module named 'app'` vì đang chạy uvicorn từ **sai thư mục**.

## ✅ GIẢI PHÁP

### Cách 1: Sử dụng script tự động (KHUYẾN NGHỊ)

**Từ thư mục gốc** (`risk cast 2`), chạy:

```powershell
.\START-SERVER.ps1
```

Script này sẽ:
- ✅ Tự động chuyển đến đúng thư mục
- ✅ Dừng process cũ nếu có
- ✅ Khởi động server đúng cách

### Cách 2: Chạy thủ công

**Bước 1:** Mở PowerShell

**Bước 2:** Chuyển đến thư mục project:
```powershell
cd "C:\Users\RIM\OneDrive\Desktop\risk cast 2\riskcast-v16-main"
```

**Bước 3:** Chạy server:
```powershell
python dev_run.py
```

### Cách 3: Sử dụng script có sẵn

```powershell
cd riskcast-v16-main
python dev_run.py
```

## 🔍 KIỂM TRA SERVER ĐÃ CHẠY

Sau khi khởi động, bạn sẽ thấy:
```
🚀 Starting RISKCAST Development Server
📍 Server will run at: http://127.0.0.1:8000
📁 Working directory: C:\Users\RIM\OneDrive\Desktop\risk cast 2\riskcast-v16-main
[INFO] App imported successfully ✓
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## 🌐 TRUY CẬP TRANG WEB

Mở trình duyệt và truy cập:
- **Trang chủ:** http://127.0.0.1:8000/
- **Input page:** http://127.0.0.1:8000/input_v20
- **Dashboard:** http://127.0.0.1:8000/dashboard

## ⛔ DỪNG SERVER

Nhấn `CTRL+C` trong terminal để dừng server.

## ❌ LỖI THƯỜNG GẶP

### Lỗi: "ModuleNotFoundError: No module named 'app'"

**Nguyên nhân:** Đang chạy từ sai thư mục

**Giải pháp:** 
- Đảm bảo bạn đang ở trong thư mục `riskcast-v16-main`
- Hoặc sử dụng script `START-SERVER.ps1`

### Lỗi: "Port 8000 already in use"

**Giải pháp:**
```powershell
# Tìm và dừng process đang dùng port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

## 📝 LƯU Ý

- ✅ Luôn chạy từ thư mục `riskcast-v16-main`
- ✅ Sử dụng `python dev_run.py` thay vì `uvicorn app.main:app --reload` trực tiếp
- ✅ Script `dev_run.py` đã xử lý đúng đường dẫn và Python path








