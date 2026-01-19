# HƯỚNG DẪN FIX UI KHÔNG HIỂN THỊ

## 🔴 VẤN ĐỀ

**UI không hiển thị gì cả, chỉ có logs:**
- `[ResultsPage] No layers data available`
- `[ResultsPage] No loss data in viewModel`
- Dữ liệu load từ localStorage nhưng không có algorithm, insurance, logistics, riskDisclosure

## ✅ ĐÃ FIX

### 1. Adapter Luôn Generate Data ✅

**File:** `src/adapters/adaptResultV2.ts`

**Thay đổi:**
- ✅ Algorithm data: Luôn generate từ layers (nếu có layers)
- ✅ Insurance data: Luôn generate từ loss metrics (nếu có loss)
- ✅ Logistics data: Luôn generate từ shipment (nếu có pol/pod)
- ✅ Risk disclosure: Luôn generate từ loss thresholds (nếu có p95)

**Logic:**
- Nếu engine có data → dùng data từ engine
- Nếu engine không có → generate default data từ available data

### 2. Thêm Debug Logging ✅

**File:** `src/pages/ResultsPage.tsx`

**Thêm logging chi tiết:**
- Log viewModel đầy đủ
- Log từng Sprint data (algorithm, insurance, logistics, riskDisclosure)
- Warning nếu thiếu data

---

## 🚀 CÁCH TEST

### Bước 1: Clear localStorage và Reload

```javascript
// Browser console
localStorage.clear();
location.reload();
```

### Bước 2: Chạy Analysis Mới

1. Vào Input page
2. Điền form và submit
3. Đợi analysis hoàn thành

### Bước 3: Kiểm tra Logs

**Browser console phải thấy:**
```
[adaptResultV2] Generating algorithm data from 16 layers
[adaptResultV2] Generating insurance data from loss metrics
[adaptResultV2] Generating logistics data from shipment
[adaptResultV2] Generating risk disclosure data from loss thresholds
```

**Và:**
```
[ResultsPage] Has algorithm: true
[ResultsPage] Has insurance: true
[ResultsPage] Has logistics: true
[ResultsPage] Has riskDisclosure: true
```

### Bước 4: Kiểm tra UI

1. Vào `/results` → Analytics tab
2. **PHẢI THẤY:**
   - ✅ Algorithm Explainability Panel
   - ✅ Insurance Underwriting Panel
   - ✅ Logistics Realism Panel
   - ✅ Risk Disclosure Panel

---

## 🔍 NẾU VẪN KHÔNG HIỂN THỊ

### Kiểm tra 1: Adapter có generate không?

```javascript
// Browser console
const data = JSON.parse(localStorage.getItem('RISKCAST_RESULTS_V2') || '{}');
console.log('Raw data:', data);
console.log('Has fahp:', !!data.fahp);
console.log('Has insurance:', !!data.insurance);
console.log('Has logistics:', !!data.logistics);
console.log('Has riskDisclosure:', !!data.riskDisclosure);
```

### Kiểm tra 2: ViewModel có data không?

```javascript
// Browser console - sau khi load results
// Tìm log: [ResultsPage] ========== VIEWMODEL DEBUG ==========
// Xem có algorithm, insurance, logistics, riskDisclosure không
```

### Kiểm tra 3: Components có được render không?

**Mở React DevTools:**
1. F12 → Components tab
2. Tìm `ResultsPage`
3. Kiểm tra props `viewModel`
4. Xem có `algorithm`, `insurance`, `logistics`, `riskDisclosure` không

---

## ⚠️ LƯU Ý

1. **Phải chạy analysis MỚI** - localStorage cũ không có Sprint data
2. **Phải hard refresh** - `Ctrl + Shift + R`
3. **Clear localStorage** nếu cần - `localStorage.clear()`

---

## ✅ SAU KHI FIX

**Tất cả panels sẽ hiển thị vì:**
- ✅ Adapter luôn generate data (từ engine hoặc default)
- ✅ ViewModel luôn có đầy đủ Sprint data
- ✅ Components sẽ render vì có data

**Nếu vẫn không hiển thị, check:**
- Conditional rendering có đúng không?
- Components có lỗi không?
- Browser console có errors không?
