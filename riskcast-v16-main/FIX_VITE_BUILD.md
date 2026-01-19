# FIX VITE BUILD - VẤN ĐỀ QUAN TRỌNG

## 🔴 VẤN ĐỀ

**Vite đang build từ template cũ thay vì React app!**

- ❌ `dist/index.html` là template "RISKCAST FutureOS" cũ
- ❌ Không phải React app với `<div id="root"></div>`
- ❌ Vite có thể đang dùng file template khác

## ✅ GIẢI PHÁP

### Cách 1: Đảm bảo Vite dùng đúng index.html

Vite mặc định tìm `index.html` ở root project. File này đã đúng:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>RISKCAST Results</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

### Cách 2: Xóa hoặc rename file template cũ

Nếu có file template khác đang được dùng, cần:
1. Tìm file template có "FutureOS" hoặc "home_v2000"
2. Rename hoặc xóa nó
3. Rebuild

### Cách 3: Explicit build config

Thêm vào `vite.config.js`:
```js
build: {
  rollupOptions: {
    input: path.resolve(__dirname, 'index.html'), // Explicit input
  }
}
```

## 🛠️ CÁC BƯỚC FIX

1. **Kiểm tra file nào đang được build:**
   ```bash
   # Xem Vite đang dùng file nào
   npm run build -- --debug
   ```

2. **Xóa dist và rebuild:**
   ```bash
   rm -rf dist
   npm run build
   ```

3. **Kiểm tra output:**
   ```bash
   head -15 dist/index.html
   # Phải thấy: <div id="root"></div>
   ```

4. **Nếu vẫn sai:**
   - Kiểm tra có file template nào trong root không
   - Rename file template cũ
   - Rebuild lại

## ⚠️ LƯU Ý

Sau khi fix, **PHẢI:**
- Hard refresh browser
- Restart backend server
- Test lại
