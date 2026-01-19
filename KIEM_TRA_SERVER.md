# ✅ KIỂM TRA VÀ CHẠY RISKCAST SERVER

## 📊 Trạng thái hiện tại

- ✅ **Port 8000 đang được sử dụng** (Process ID: 4164)
- ✅ Server có thể đã đang chạy

## 🚀 Cách chạy server đúng

### **Cách 1: Sử dụng script tự động (KHUYẾN NGHỊ)**

Từ thư mục `vcl`, chạy:

```powershell
.\start-server.ps1
```

Script này sẽ:
- ✅ Tự động kiểm tra và dừng process cũ nếu cần
- ✅ Chuyển đến đúng thư mục (`riskcast-v16-main`)
- ✅ Khởi động server với cấu hình đúng

### **Cách 2: Chạy thủ công**

```powershell
# Bước 1: Chuyển đến thư mục project
cd riskcast-v16-main

# Bước 2: Chạy server
python dev_run.py
```

### **Cách 3: Sử dụng run_server.py**

```powershell
cd riskcast-v16-main
python run_server.py
```

## ⚠️ LƯU Ý QUAN TRỌNG

**KHÔNG BAO GIỜ chạy:**
```powershell
# ❌ SAI - Chạy từ thư mục vcl
uvicorn app.main:app --reload
```

**Lý do:** Module `app` nằm trong `riskcast-v16-main/app/`, không phải `vcl/app/`

**ĐÚNG:**
```powershell
# ✅ ĐÚNG - Chạy từ thư mục riskcast-v16-main
cd riskcast-v16-main
python dev_run.py
```

## 🔍 Kiểm tra server đang chạy

### Kiểm tra port 8000:
```powershell
netstat -ano | findstr :8000
```

### Kiểm tra process Python:
```powershell
Get-Process python | Select-Object Id, ProcessName, StartTime
```

### Test server response:
Mở trình duyệt và truy cập:
- **API Docs:** http://127.0.0.1:8000/docs
- **Trang chủ:** http://127.0.0.1:8000/
- **Input page:** http://127.0.0.1:8000/input_v20

## 🛑 Dừng server

### Cách 1: Trong terminal đang chạy server
Nhấn `CTRL+C`

### Cách 2: Kill process theo PID
```powershell
# Tìm PID
netstat -ano | findstr :8000

# Kill process (thay <PID> bằng số thực tế)
taskkill /PID <PID> /F
```

### Cách 3: Kill tất cả Python processes (CẨN THẬN!)
```powershell
Get-Process python | Stop-Process -Force
```

## 📝 Tóm tắt

1. ✅ **Luôn chạy từ thư mục `riskcast-v16-main`**
2. ✅ **Sử dụng `python dev_run.py` hoặc `python run_server.py`**
3. ✅ **Hoặc dùng script `start-server.ps1` từ thư mục `vcl`**
4. ❌ **KHÔNG chạy `uvicorn app.main:app --reload` trực tiếp từ thư mục `vcl`**

## 🎯 Server đã sẵn sàng!

Nếu port 8000 đang được sử dụng, server có thể đã chạy. Hãy mở trình duyệt và truy cập:
- http://127.0.0.1:8000/docs để xem API documentation
- http://127.0.0.1:8000/results để xem trang Results
