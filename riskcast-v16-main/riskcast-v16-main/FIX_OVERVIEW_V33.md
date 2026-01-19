# 🔧 FIX OVERVIEW V33 - Hướng Dẫn Khắc Phục

## ❌ Vấn Đề
Trang `/overview` vẫn hiển thị bản cũ thay vì v33 (FutureOS Edition).

## ✅ Giải Pháp

### Bước 1: Clear Browser Cache
1. Mở DevTools (F12)
2. Right-click vào nút Refresh
3. Chọn **"Empty Cache and Hard Reload"**
   - Hoặc: `Ctrl + Shift + R` (Windows)
   - Hoặc: `Cmd + Shift + R` (Mac)

### Bước 2: Kiểm Tra Route
Đảm bảo route `/overview` đang dùng template v33:

**File:** `app/routes/overview.py`
- Dòng 172 phải là: `return templates.TemplateResponse("overview_v33.html", ...)`

### Bước 3: Restart Server
```bash
# Dừng server (Ctrl+C)
# Sau đó chạy lại:
uvicorn app.main:app --reload
```

### Bước 4: Kiểm Tra Console
Mở DevTools → Console, phải thấy:
```
[Overview v33] Initializing...
[Overview v33] Loaded shipment state: ...
[Overview v33] Cesium viewer initialized
```

### Bước 5: Kiểm Tra Network Tab
Trong DevTools → Network:
- `overview_v33.css` phải load (status 200)
- `overview_v33.js` phải load (status 200)
- `edit_panel.css` phải load (status 200)
- `ai_panel.css` phải load (status 200)

### Bước 6: Kiểm Tra HTML Source
Right-click → View Page Source:
- Phải thấy: `<link rel="stylesheet" href="/static/css/overview_v33.css">`
- Phải thấy: `<script src="/static/js/overview_v33.js"></script>`
- Phải thấy: `<div class="overview-v33-container">`

## 🎯 Các Tính Năng V33 Phải Thấy

1. **Top Navbar:**
   - Logo "RISKCAST" bên trái
   - "Global Supply Chain Overview" ở giữa
   - Notifications + User + **Smart Edit toggle** bên phải

2. **Right Sidebar:**
   - Card 1: Transport Details
   - Card 2: Parties
   - **Card 3: Risk Assessment (Gauge)** ← QUAN TRỌNG!

3. **Bottom-Right:**
   - **AI Floating Button** (nút tròn với icon)

4. **Edit Mode:**
   - Toggle "Smart Edit" ON
   - Hover vào field → thấy icon ✏
   - Click field → panel slide từ bên phải

## 🐛 Nếu Vẫn Không Thấy

### Kiểm Tra File Exists:
```bash
# Windows PowerShell
Test-Path "app\templates\overview_v33.html"
Test-Path "app\static\css\overview_v33.css"
Test-Path "app\static\js\overview_v33.js"
```

### Kiểm Tra Route Registration:
**File:** `app/main.py`
- Phải có: `from app.routes.overview import router as overview_router`
- Phải có: `app.include_router(overview_router)`

### Force Reload Template:
1. Sửa file `app/routes/overview.py` (thêm space)
2. Save
3. Server auto-reload
4. Refresh browser

## 📞 Debug Commands

### Check Template:
```python
# Trong Python console
from app.core.templates import templates
print(templates.env.list_templates())
# Phải thấy: overview_v33.html
```

### Check Route:
```python
# Trong Python console
from app.routes.overview import router
for route in router.routes:
    print(route.path, route.methods)
# Phải thấy: /overview GET
```

## ✅ Checklist

- [ ] Browser cache cleared (Hard Reload)
- [ ] Server restarted
- [ ] Console shows "[Overview v33]"
- [ ] Network tab shows v33 files loading
- [ ] HTML source shows overview_v33.html
- [ ] Top navbar shows "Global Supply Chain Overview"
- [ ] Risk Assessment Gauge card visible
- [ ] AI floating button visible
- [ ] Smart Edit toggle visible

---

**Nếu vẫn không thấy:** Kiểm tra xem có route nào khác đang override `/overview` không.

