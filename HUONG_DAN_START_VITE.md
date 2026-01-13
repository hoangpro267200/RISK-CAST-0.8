# HƯỚNG DẪN KHỞI ĐỘNG VITE DEV SERVER

## 🚀 Cách khởi động Vite Dev Server

### Bước 1: Mở PowerShell
Mở PowerShell trong thư mục gốc (`cc`)

### Bước 2: Chuyển đến thư mục project
```powershell
cd riskcast-v16-main
```

### Bước 3: Kiểm tra dependencies
```powershell
# Nếu chưa có node_modules, cài đặt:
npm install
```

### Bước 4: Khởi động Vite dev server
```powershell
npm run dev
```

### Bước 5: Đợi server khởi động
Bạn sẽ thấy output như:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### Bước 6: Mở browser
Truy cập: `http://localhost:3000`

## ⚠️ Lưu ý quan trọng

### 1. Cần 2 terminal chạy đồng thời:

**Terminal 1 - Backend (port 8000):**
```powershell
cd riskcast-v16-main
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend (port 3000):**
```powershell
cd riskcast-v16-main
npm run dev
```

### 2. Nếu port 3000 đã được sử dụng:
Vite sẽ tự động chọn port khác (3001, 3002, ...)
Xem terminal để biết port mới.

### 3. Kiểm tra server đang chạy:
```powershell
# Kiểm tra port 3000
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

# Kiểm tra port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

## 🐛 Troubleshooting

### Lỗi: "Cannot find module"
```powershell
cd riskcast-v16-main
npm install
```

### Lỗi: "Port 3000 already in use"
```powershell
# Tìm process đang dùng port 3000
Get-NetTCPConnection -LocalPort 3000 | Select-Object OwningProcess

# Kill process (thay PID bằng process ID)
Stop-Process -Id <PID> -Force
```

### Lỗi: "npm: command not found"
Cài đặt Node.js từ: https://nodejs.org/

## 📝 Quick Commands

**Start Backend:**
```powershell
.\start-server.ps1
```

**Start Frontend:**
```powershell
cd riskcast-v16-main
npm run dev
```

**Check both servers:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000


