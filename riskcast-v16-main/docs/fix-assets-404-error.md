# Fix Assets 404 Error - Complete Solution
## Sửa lỗi 404 cho JS/CSS files và MIME type

**Date:** January 2026  
**Issue:** 
- JS files return 404 (Not Found)
- CSS file returns wrong MIME type (application/json instead of text/css)
- Blank page on `/input_react`

---

## 🔴 Root Cause

**Vấn đề chính:** `dist/assets` folder tồn tại nhưng **KHÔNG CÓ FILE NÀO** trong đó!

Điều này có nghĩa:
1. React app chưa được build đúng cách
2. Build process không tạo ra các file assets
3. Hoặc build bị lỗi nhưng không báo lỗi rõ ràng

---

## ✅ Solution - Rebuild React App

### Step 1: Clean và Rebuild

```bash
cd riskcast-v16-main

# Xóa dist cũ (nếu có)
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

# Rebuild React app
npm run build
```

### Step 2: Verify Build Output

Sau khi build, kiểm tra:

```bash
# Kiểm tra dist/assets có files không
Get-ChildItem dist/assets

# Phải thấy các file như:
# - index-*.js
# - index-*.css
# - vendor-*.js
# - components-*.js
```

### Step 3: Restart FastAPI Server

```bash
# Stop server (Ctrl+C)
# Restart server
python dev_run.py
```

### Step 4: Test

1. Truy cập `http://127.0.0.1:8000/input_react`
2. Mở DevTools Console
3. Kiểm tra:
   - ✅ Không còn 404 errors
   - ✅ CSS load với `text/css` MIME type
   - ✅ JS files load thành công
   - ✅ Page render đúng

---

## 🔧 Fixes Applied

### 1. ErrorHandlerMiddleware
- ✅ Skip static files trong exception handling
- ✅ Không convert static file errors thành JSON

### 2. StaticFiles Mount
- ✅ Mount `/assets` TRƯỚC các routes
- ✅ Sử dụng `html=False` để không serve index.html cho missing files

### 3. MIME Type Handling
- ✅ StaticFiles tự động set MIME type đúng
- ✅ ErrorHandlerMiddleware không modify static file responses

---

## 🐛 Troubleshooting

### Issue: Build fails

**Solution:**
```bash
# Clean install dependencies
Remove-Item -Recurse -Force node_modules
npm install

# Try build again
npm run build
```

### Issue: Build succeeds but no files in dist/assets

**Check:**
1. Vite config có đúng không?
2. `vite.config.js` có `build.outDir = 'dist'` không?
3. Có lỗi trong build output không?

**Solution:**
```bash
# Check vite config
cat vite.config.js

# Build with verbose output
npm run build -- --debug
```

### Issue: Files exist but still 404

**Check:**
1. FastAPI server logs - có mount `/assets` không?
2. File paths có đúng không?
3. Permissions có đúng không?

**Solution:**
```bash
# Check server logs for:
# [INFO] Mounted /assets from ...
# [INFO] Assets directory contains X files

# Verify file exists
Test-Path "dist/assets/index-*.js"
```

---

## 📝 Verification Checklist

- [ ] `dist/assets` folder exists
- [ ] `dist/assets` contains JS files (index-*.js, vendor-*.js, etc.)
- [ ] `dist/assets` contains CSS file (index-*.css)
- [ ] `dist/index.html` exists and references correct file names
- [ ] FastAPI server logs show `/assets` mounted
- [ ] No 404 errors in browser console
- [ ] CSS loads with `text/css` MIME type
- [ ] Page renders correctly

---

## 🚀 Quick Fix Command

```powershell
# One-command fix
cd riskcast-v16-main; Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue; npm run build; Write-Host "Build complete! Restart FastAPI server now."
```

---

**Status:** ✅ Fixes applied, waiting for rebuild  
**Next:** Run `npm run build` and restart server
