# ⚡ RELOAD NGAY BÂY GIỜ

## CÁCH NHANH NHẤT:

### 1. Nếu đang chạy `npm run dev`:
- **Dừng server**: Nhấn `Ctrl + C` trong terminal đang chạy dev server
- **Chạy lại**: `npm run dev`
- **Hard refresh browser**: `Ctrl + Shift + R` (Windows) hoặc `Cmd + Shift + R` (Mac)

### 2. Nếu đang dùng Python server (port 8000):
- Code React cần được build hoặc chạy qua Vite dev server
- **Option A**: Chạy Vite dev server riêng:
  ```bash
  npm run dev
  ```
  Sau đó truy cập: `http://localhost:3000/results`

- **Option B**: Build production (có lỗi hiện tại, cần fix):
  ```bash
  npm install terser --save-dev
  npm run build
  ```

---

## 🔍 KIỂM TRA CODE ĐÃ ĐƯỢC SỬA:

Mở file này để verify:
- `src/hooks/useResults.ts` - Dòng 24: `const isDev = import.meta.env.DEV === true`
- `src/components/results/HeroSection.tsx` - Dòng 28: `return 0.5;` (thay vì `return 0;`)

---

## 🐛 NẾU VẪN KHÔNG THẤY THAY ĐỔI:

1. **Mở Browser Console (F12)**
2. **Tìm logs:**
   - `[useResults] Attempt 1:` - Nếu thấy → code đã load
   - `[useResults] Normalized summary:` - Nếu thấy → normalization đã chạy
3. **Nếu không thấy logs:**
   - Code chưa được load → Cần restart dev server
   - Hoặc đang dùng old build → Cần build lại

---

## ✅ VERIFY SAU KHI RELOAD:

Sau khi reload, bạn sẽ thấy trong Console:
```
[useResults] Attempt 1: http://localhost:8000/api/results
[useResults] Response: 200 (123ms)
[useResults] Response keys: ['shipment', 'risk_score', ...]
[useResults] Normalized summary: { shipmentId: '...', layersCount: X, ... }
```

Nếu endpoint đầu fail, sẽ thấy:
```
[useResults] Attempt 1: http://localhost:8000/api/results
[useResults] Endpoint failed (456ms): ...
[useResults] Retrying in 500ms...
[useResults] Attempt 2: http://localhost:8000/results/data
[useResults] Response: 200 (234ms)
```

---

**QUAN TRỌNG**: Code đã được sửa trong các file:
- ✅ `src/hooks/useResults.ts`
- ✅ `src/utils/normalizeEngineResult.ts`  
- ✅ `src/components/results/HeroSection.tsx`
- ✅ `src/components/results/DecisionSection.tsx`
- ✅ `src/components/results/EvidenceSection.tsx`
- ✅ `src/App.tsx`

**Chỉ cần restart dev server là sẽ thấy thay đổi!**

