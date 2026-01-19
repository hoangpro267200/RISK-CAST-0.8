# HƯỚNG DẪN RELOAD SAU KHI SỬA CODE

## ⚠️ VẤN ĐỀ: Code đã sửa nhưng không thấy thay đổi

Sau khi sửa code React/TypeScript, bạn cần:

### 1. Nếu đang chạy Vite Dev Server:
```bash
# Dừng server (Ctrl+C) và chạy lại:
npm run dev
```

### 2. Nếu đang dùng Production Build:
```bash
# Build lại:
npm run build

# Sau đó restart Python server nếu cần
```

### 3. Hard Refresh Browser:
- **Windows/Linux**: `Ctrl + Shift + R` hoặc `Ctrl + F5`
- **Mac**: `Cmd + Shift + R`

### 4. Clear Browser Cache:
- Mở DevTools (F12)
- Right-click vào nút Refresh
- Chọn "Empty Cache and Hard Reload"

---

## 🔍 KIỂM TRA CODE ĐÃ ĐƯỢC SỬA

### File đã được cập nhật:
1. ✅ `src/hooks/useResults.ts` - Multiple endpoints, retry, timeout
2. ✅ `src/utils/normalizeEngineResult.ts` - Improved unwrapRoot, relaxed normalization
3. ✅ `src/components/results/HeroSection.tsx` - Partial rendering
4. ✅ `src/components/results/DecisionSection.tsx` - Show scenarios without decisionSignal
5. ✅ `src/components/results/EvidenceSection.tsx` - Show drivers without layers
6. ✅ `src/App.tsx` - Handle new status

### Cách kiểm tra trong Console (F12):

1. **Kiểm tra useResults logs:**
```
[useResults] Attempt 1: /api/results
[useResults] Response: 200 (123ms)
[useResults] Response keys: [...]
[useResults] Normalized summary: {...}
```

2. **Kiểm tra normalizeEngineResult logs:**
```
[normalizeEngineResult] Array input with X objects, selected best (score: Y)
[normalizeEngineResult] Unwrapped N levels
```

3. **Kiểm tra errors:**
- Nếu thấy lỗi trong console → code có vấn đề
- Nếu không thấy logs → code chưa được load

---

## 🚀 CÁCH CHẠY ĐÚNG

### Option 1: Vite Dev Server (Recommended)
```bash
cd riskcast-v16-main
npm run dev
```
Sau đó truy cập: `http://localhost:3000/results`

### Option 2: Production Build
```bash
cd riskcast-v16-main
npm run build
```
Sau đó truy cập: `http://localhost:8000/results` (Python server)

---

## 🐛 DEBUG

Nếu vẫn không thấy thay đổi:

1. **Kiểm tra file đã save chưa:**
   - Mở file trong editor
   - Kiểm tra xem có dấu "*" (unsaved) không

2. **Kiểm tra TypeScript errors:**
```bash
npm run typecheck
```

3. **Kiểm tra build errors:**
```bash
npm run build
```

4. **Kiểm tra browser console:**
   - Mở F12 → Console tab
   - Tìm lỗi JavaScript/TypeScript

5. **Kiểm tra Network tab:**
   - F12 → Network tab
   - Reload page
   - Kiểm tra xem có file `.js` nào fail không

---

## ✅ VERIFY CHANGES

Sau khi reload, bạn sẽ thấy:

1. **Multiple endpoint attempts** trong console (nếu endpoint đầu fail)
2. **Partial rendering** - UI hiển thị ngay cả khi thiếu data
3. **Better error messages** - Error messages rõ ràng hơn
4. **Status indicators** - 'partial' hoặc 'ready' status

---

**Nếu vẫn không thấy thay đổi, hãy:**
1. Restart dev server
2. Hard refresh browser
3. Check console for errors
4. Verify file paths are correct

