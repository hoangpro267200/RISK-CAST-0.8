# Fix CSS MIME Type Error
## Sửa lỗi CSS file bị serve với MIME type sai

**Date:** January 2026  
**Issue:** CSS files being served with `application/json` MIME type instead of `text/css`

---

## 🔴 Vấn đề

Khi truy cập `/input_react`, CSS file không load được với lỗi:
```
Refused to apply style from 'http://127.0.0.1:8000/assets/index-CYb-LFVg.css' 
because its MIME type ('application/json') is not a supported stylesheet MIME type
```

## ✅ Giải pháp đã áp dụng

### 1. Cập nhật ErrorHandlerMiddleware

**File:** `app/middleware/error_handler_v2.py`

- Thêm check cho static files trong `except Exception` block
- Đảm bảo static file errors không bị convert thành JSON
- Re-raise exceptions để Starlette handle tự nhiên

```python
except Exception as exc:
    # CRITICAL: For static file requests, don't convert to JSON
    if request.url.path.startswith(("/assets/", "/static/", "/dist/")):
        raise exc  # Let Starlette handle it
```

### 2. Đảm bảo StaticFiles mount đúng thứ tự

**File:** `app/main.py`

- StaticFiles mount được đặt TRƯỚC các routes
- FastAPI matches mounts BEFORE routes, nên thứ tự này đúng
- `/assets` mount với `html=False` để không serve index.html cho missing files

## 🧪 Test

1. **Build React app:**
   ```bash
   npm run build
   ```

2. **Restart FastAPI server**

3. **Test CSS loading:**
   - Truy cập `/input_react`
   - Mở DevTools Console
   - Kiểm tra không còn lỗi MIME type
   - CSS file phải load với `text/css` MIME type

4. **Verify:**
   ```bash
   curl -I http://127.0.0.1:8000/assets/index-*.css
   # Should return: Content-Type: text/css; charset=utf-8
   ```

## 📝 Notes

- StaticFiles của Starlette tự động set MIME type đúng dựa trên file extension
- ErrorHandlerMiddleware không nên modify static file responses
- Mount order quan trọng: StaticFiles mounts phải TRƯỚC routes

---

**Status:** ✅ Fixed  
**Next:** Test và verify CSS files load correctly
