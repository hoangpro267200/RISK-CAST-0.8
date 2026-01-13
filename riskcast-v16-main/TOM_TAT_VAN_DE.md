# TÓM TẮT VẤN ĐỀ TRANG RESULTS

## 🎯 VẤN ĐỀ CHÍNH

Trang Results không hiển thị đầy đủ nội dung vì:

### 1. API không nhận được dữ liệu
- ❌ Chỉ gọi 1 endpoint `/api/results` → Nếu fail thì toàn bộ UI không load
- ❌ Không có retry hoặc fallback endpoints
- ❌ Không có timeout handling

### 2. Normalize dữ liệu quá strict
- ❌ Nếu API trả về format khác → return null → UI không render
- ❌ Mất partial data (ví dụ: có actionItems nhưng không có executiveSummary → không hiển thị gì)
- ❌ Field mapping có thể miss các tên field khác

### 3. Component render quá strict
- ❌ **HeroSection**: Yêu cầu phải có `shipment` → Nếu không có → hiển thị EmptyState
- ❌ **DecisionSection**: Yêu cầu phải có `decisionSignal` → Nếu không có → không hiển thị scenarios/timing
- ❌ **EvidenceSection**: Yêu cầu phải có `layers` → Nếu không có → không hiển thị drivers/financial

### 4. Data mapping thiếu sót
- ❌ Confidence luôn = 0 nếu không có field `dataConfidence`
- ❌ Drivers phụ thuộc hoàn toàn vào layers → Nếu không có layers → không có drivers
- ❌ AINarrative chỉ return nếu có executiveSummary hoặc keyInsights → Mất actionItems, riskDrivers

---

## 🔧 CÁC ĐIỂM CẦN SỬA

### Ưu tiên cao (Critical)
1. ✅ Thêm multiple endpoint fallback trong `useResults.ts`
2. ✅ Relax điều kiện render trong HeroSection, DecisionSection, EvidenceSection
3. ✅ Cải thiện normalizeAINarrative để return partial data

### Ưu tiên trung bình (Important)
4. ⚠️ Thêm logging chi tiết để debug
5. ⚠️ Cải thiện error handling với retry mechanism
6. ⚠️ Cải thiện normalizeDrivers để không phụ thuộc hoàn toàn vào layers

### Ưu tiên thấp (Nice to have)
7. 💡 Thêm default confidence hợp lý
8. 💡 Cải thiện unwrapRoot để handle nested wrappers
9. 💡 Thêm data validation

---

## 📋 CHECKLIST DEBUG

Khi gặp vấn đề "không nhận được dữ liệu":

1. [ ] Mở Console (F12) → Kiểm tra có log `[useResults] RAW ENGINE RESPONSE`?
2. [ ] Kiểm tra Network tab → API có trả về 200 OK?
3. [ ] Kiểm tra Response body → Có đúng format JSON?
4. [ ] Kiểm tra log `[useResults] NORMALIZED` → Có return null không?
5. [ ] Kiểm tra component conditions → Có quá strict không?

---

## 📁 FILE CẦN XEM

- `src/hooks/useResults.ts` - Nơi fetch data từ API
- `src/utils/normalizeEngineResult.ts` - Nơi normalize data
- `src/components/results/HeroSection.tsx` - Hero section
- `src/components/results/DecisionSection.tsx` - Decision section
- `src/components/results/EvidenceSection.tsx` - Evidence section

---

**Xem báo cáo chi tiết:** `BAO_CAO_RESULTS_PAGE.md`

