# AUDIT TOÀN DIỆN TRANG /results - RISKCAST
## Enterprise SaaS + Risk Intelligence + Insurance Underwriting + Shipping Advisor

**Ngày audit:** 2026-01-15  
**Auditor:** Head of Product (Enterprise) + Insurance Underwriter + Logistics Risk Analyst + UX Audit + Data Quality Inspector  
**Tiêu chuẩn:** Khó tính, có tiêu chuẩn cao, không nương tay, tìm lỗi trước, đánh giá thực dụng, no-BS

---

## 1. ENGINE-DATA VALIDATION (BẮT BUỘC)

### 1.1. Kiểm tra dữ liệu inbound từ /analyze

**TRACE EVIDENCE:**
- ✅ Endpoint: `GET /results/data` → `LAST_RESULT_V2` (từ `/api/v1/risk/v2/analyze`)
- ✅ Adapter: `adaptResultV2()` xử lý normalization
- ⚠️ **VẤN ĐỀ:** Frontend fallback vào `localStorage.getItem('RISKCAST_RESULTS_V2')` trước khi gọi API
- ⚠️ **VẤN ĐỀ:** Nếu API trả về empty object → frontend không set error, chỉ log warning

**KẾT LUẬN:**
- **Đúng:** Data flow từ engine → backend state → adapter → frontend
- **Mập mờ:** localStorage có thể chứa stale data, không có timestamp validation
- **Không có dữ liệu:** Nếu engine chưa chạy → empty state hiển thị, nhưng không rõ ràng về nguyên nhân

**YÊU CẦU SỬA:**
1. Thêm timestamp vào localStorage data, validate freshness (< 5 phút)
2. Nếu API trả về empty → set error state rõ ràng, không silent fail
3. Thêm data version check (engine_version mismatch → force refresh)

### 1.2. Loại dữ liệu chuẩn chưa?

**TRACE EVIDENCE:**
- ✅ Adapter normalize: `toPercent()`, `clamp()`, `round()` cho tất cả số
- ✅ Risk score: 0-100 scale (normalized từ 0-1 nếu cần)
- ⚠️ **VẤN ĐỀ:** `confidence` có thể là 0-1 hoặc 0-100, adapter xử lý nhưng không consistent
- ❌ **LỖI:** `lossCurve` được generate synthetic nếu không có data thật → không rõ ràng cho user

**KẾT LUẬN:**
- **Đúng:** Type coercion có, nhưng không đầy đủ
- **Sai:** Synthetic loss curve không được đánh dấu là "estimated"
- **Mập mờ:** Units không được hiển thị rõ (USD? VND? percentage?)

**YÊU CẦU SỬA:**
1. Thêm metadata flag: `lossCurve.isSynthetic: boolean`
2. Hiển thị units rõ ràng: "$" cho currency, "%" cho percentages
3. Validate confidence scale: nếu > 1 → divide by 100, log warning

### 1.3. Consistency giữa dashboard → charts → AI advisor

**TRACE EVIDENCE:**
- ✅ Risk score: `viewModel.overview.riskScore.score` → dùng ở RiskOrb, Quick Stats, Executive Summary
- ✅ Layers: `viewModel.breakdown.layers` → RiskRadar, RiskContributionWaterfall, LayersTable
- ⚠️ **VẤN ĐỀ:** `narrativeData` được build từ `explanation` + `drivers` + `scenarios`, nhưng không validate consistency
- ❌ **LỖI:** `keyTakeaways` được extract từ `riskScore`, `drivers`, `layers` → có thể mâu thuẫn với `explanation`

**KẾT LUẬN:**
- **Đúng:** Single source of truth (viewModel)
- **Mập mờ:** Narrative generation có thể không match với actual data
- **Sai:** Không có validation cross-check giữa các components

**YÊU CẦU SỬA:**
1. Thêm consistency check: `explanation` phải mention top 3 drivers
2. Validate: `keyTakeaways` phải align với `riskScore.level`
3. Warning nếu `narrativeData.actionItems` không match với `scenarios`

### 1.4. Dữ liệu có phải đang fixed/stub/fake hay actual dynamic?

**TRACE EVIDENCE:**
- ✅ `ResultsPage.tsx` line 207-303: Fetch từ API, không generate fake data
- ✅ `adaptResultV2.ts` line 447-485: Synthetic loss curve chỉ khi `expectedLoss > 0` và không có distribution
- ⚠️ **VẤN ĐỀ:** Default values trong `createDefaultViewModel()` có thể được dùng nếu data invalid
- ❌ **LỖI:** `scenarioData` empty → không render chart, nhưng không rõ là "no data" hay "loading"

**KẾT LUẬN:**
- **Đúng:** Không có hardcoded fake data generation
- **Mập mờ:** Default values có thể mask missing data
- **Không có dữ liệu:** Empty states không phân biệt "no data" vs "error"

**YÊU CẦU SỬA:**
1. Thêm data freshness indicator: "Last updated: X minutes ago"
2. Flag synthetic/estimated data: `meta.dataQuality: 'real' | 'synthetic' | 'estimated'`
3. Empty state phải rõ: "No analysis data" vs "Analysis failed" vs "Loading..."

---

## 2. CHARTS & VISUALIZATION VALIDATION

### 2.1. Bảng đánh giá charts

| Chart | Status | Binding | Dynamic | Missing Info | Fix |
|-------|--------|---------|---------|---------------|-----|
| **RiskRadar** | ✅ OK | ✅ `layers` từ viewModel | ✅ Live | ❌ Không show contribution %, không show weight | Thêm tooltip: contribution %, FAHP weight |
| **RiskContributionWaterfall** | ✅ OK | ✅ `layers` + `overallScore` | ✅ Live | ❌ Không show cumulative %, không explain "why this order" | Thêm cumulative %, thêm sort explanation |
| **RiskScenarioFanChart** | ⚠️ Conditional | ✅ `scenarioData` từ timeline | ✅ Live | ❌ Không show P10/P50/P90 explanation, không show Monte Carlo sample size | Thêm legend: "P10/P50/P90 = 10th/50th/90th percentile", show n_samples |
| **RiskSensitivityTornado** | ⚠️ Conditional | ✅ `sensitivityDrivers` từ drivers/layers | ✅ Live | ❌ Không show impact direction (+/-), không show confidence interval | Thêm +/- indicators, thêm CI bands |
| **RiskCostEfficiencyFrontier** | ⚠️ Conditional | ✅ `scenariosForFrontier` | ✅ Live | ❌ Không show baseline, không explain "efficient frontier" concept | Thêm baseline marker, thêm explanation tooltip |
| **FinancialModule** | ⚠️ Conditional | ✅ `financialMetrics` từ loss | ⚠️ Partial | ❌ Loss curve có thể synthetic, không rõ, không show tail risk | Flag synthetic data, thêm tail risk histogram (P95-P99) |
| **LayersTable** | ✅ OK | ✅ `layersData` | ✅ Live | ❌ Không show FAHP weights, không show TOPSIS scores | Thêm columns: FAHP weight, TOPSIS score |
| **DataReliabilityMatrix** | ❌ Empty | ❌ `dataReliabilityDomains = []` | ❌ Not implemented | ❌ Component tồn tại nhưng không có data | Implement data reliability từ engine |
| **ExecutiveNarrative** | ✅ OK | ✅ `narrativeData` | ✅ Live | ⚠️ Không show source attribution, không show confidence | Thêm "Based on X data points", confidence badge |

### 2.2. Vấn đề cụ thể

**RiskRadar:**
- ❌ Chỉ show score, không show contribution → user không biết layer nào quan trọng nhất
- ❌ Không show FAHP weight → không explain được "why this layer matters"
- **Fix:** Thêm tooltip: `Contribution: X%, FAHP Weight: Y, Impact: Z%`

**FinancialModule:**
- ❌ Synthetic loss curve không được đánh dấu → user nghĩ là real data
- ❌ Không show tail risk (P95-P99) riêng → insurance underwriter cần cái này
- **Fix:** Badge "Estimated" nếu synthetic, thêm "Tail Risk" section với P95/P99 breakdown

**RiskScenarioFanChart:**
- ⚠️ Chỉ render nếu `scenarioData.length > 0` → có thể empty mà không rõ lý do
- ❌ Không explain Monte Carlo methodology → user không hiểu "P10/P50/P90" là gì
- **Fix:** Empty state với explanation, thêm methodology tooltip

---

## 3. ALGORITHM TRACEABILITY

### 3.1. FAHP + TOPSIS + Monte-Carlo explanation

**TRACE EVIDENCE:**
- ❌ **KHÔNG CÓ:** Không có component nào explain FAHP weights
- ❌ **KHÔNG CÓ:** Không có component nào show TOPSIS score breakdown
- ⚠️ **MẬP MỜ:** `RiskScenarioFanChart` mention "Monte Carlo" nhưng không explain methodology
- ❌ **KHÔNG CÓ:** Không có visualization nào show "how FAHP weights affect final score"

**KẾT LUẬN:**
- **Chưa explain được:** User không biết vì sao điểm như vậy
- **Insurance underwriter:** Không đủ data để trust (thiếu algorithm transparency)
- **Thiếu:** Factor contribution plot, risk decomposition, Monte Carlo tail histogram, percentile bands, scenario compare, weight sensitivity

**YÊU CẦU THÊM:**

1. **FAHP Weight Visualization:**
   - Bar chart: FAHP weights cho từng layer
   - Tooltip: "This weight determines X% of final score"
   - Consistency ratio indicator

2. **TOPSIS Score Breakdown:**
   - Show: positive ideal, negative ideal, closeness coefficient
   - Explain: "TOPSIS score = distance to worst / (distance to best + distance to worst)"

3. **Monte Carlo Explanation:**
   - Show: n_samples, distribution type, parameters
   - Tail histogram: P95, P99, max loss
   - Explain: "10,000 simulations → P50 = median, P95 = 95% of outcomes below this"

4. **Factor Contribution Plot:**
   - Waterfall chart: Base risk → +Layer1 → +Layer2 → ... → Final score
   - Color code: positive (red), negative (green)

5. **Weight Sensitivity Analysis:**
   - Tornado chart: "If FAHP weight of Layer X changes by ±10%, final score changes by Y"
   - Show: which weights are most sensitive

---

## 4. SHIPMENT REALISM CHECK (RẤT QUAN TRỌNG)

### 4.1. Audit mức close to real logistics

**TRACE EVIDENCE:**
- ✅ `shipmentData` có: `pol`, `pod`, `carrier`, `etd`, `eta`, `cargoValue`
- ❌ **THIẾU:** `cargo` (cargo type) không được hiển thị trên ResultsPage
- ❌ **THIẾU:** `container` (container type) không được hiển thị
- ❌ **THIẾU:** `packaging` không có trong shipment data
- ❌ **THIẾU:** Không có validation "cargo type → container type match"

**KẾT LUẬN:**

**Shipment Reality Check:**
- **Cargo Type:** ❌ NOT DISPLAYED (có trong `viewModel.overview.shipment.cargo` nhưng không render)
- **Fit for Container:** ❌ NOT VALIDATED (không check: electronics → reefer? perishable → dry?)
- **Route Seasonality Risk:** ⚠️ PARTIAL (có climate data nhưng không explain seasonality)
- **Delay Risk:** ⚠️ PARTIAL (có transit time nhưng không show delay probability)
- **Port Congestion Risk:** ⚠️ PARTIAL (có port risk layer nhưng không show actual congestion data)
- **Insurance Attention:** ❌ NOT FLAGGED (không highlight: fragile cargo, high value, long transit)

**YÊU CẦU SỬA:**

1. **Hiển thị Cargo Details:**
   ```tsx
   <div>
     <span>Cargo Type:</span> {viewModel.overview.shipment.cargo}
     <span>Container:</span> {viewModel.overview.shipment.container}
   </div>
   ```

2. **Cargo-Container Validation:**
   - Check: `cargo === 'perishable' && container !== 'reefer'` → WARNING
   - Check: `cargo === 'electronics' && container === 'opentop'` → WARNING
   - Show: "⚠️ Container type may not be suitable for cargo type"

3. **Route Seasonality:**
   - Show: "Route VN→US in December → Winter storms in Pacific → HIGH delay risk"
   - Climate data: "ENSO index: +0.5 (El Niño) → increased storm frequency"

4. **Port Congestion:**
   - Show: "Singapore port: 3.2 days average dwell time (vs 1.5 days normal)"
   - Real-time: "Current congestion: MEDIUM (if API available)"

5. **Insurance Attention Flags:**
   - Fragile cargo: "⚠️ Electronics → moisture shock risk → recommend desiccant"
   - High value: "⚠️ $500K cargo → recommend full coverage + parametric delay"
   - Long transit: "⚠️ 34 days → condensation risk → recommend humidity monitoring"

---

## 5. INSURANCE DISCLOSURE & ADVISOR MODE

### 5.1. Output có đủ dữ liệu để làm insurance underwriting chưa?

**TRACE EVIDENCE:**
- ✅ Có: `expectedLoss`, `p95`, `p99`, `riskScore`, `drivers`
- ❌ **THIẾU:** Không có `loss distribution histogram` (chỉ có synthetic curve)
- ❌ **THIẾU:** Không có `basis risk score` (parametric insurance cần)
- ❌ **THIẾU:** Không có `trigger probability` (parametric triggers)
- ❌ **THIẾU:** Không có `coverage recommendations` với specific clauses

**KẾT LUẬN:**

**Missing for Underwriting:**
1. **Loss Distribution:** ❌ Không có actual histogram, chỉ có synthetic curve → không trust được
2. **Basis Risk:** ❌ Không có basis risk score → parametric insurance không thể price
3. **Trigger Probability:** ❌ Không có "probability of delay > 7 days" → không design parametric trigger
4. **Coverage Clauses:** ❌ Không recommend specific clauses (moisture, delay, war risk)
5. **Premium Logic:** ❌ Không show "why premium should be X% of cargo value"
6. **Exclusions:** ❌ Không list potential exclusions (pre-existing damage, improper packaging)
7. **Deductible Recommendation:** ❌ Không recommend optimal deductible
8. **Rider Recommendations:** ❌ Không recommend riders (delay, temperature deviation)

**YÊU CẦU THÊM:**

1. **Insurance Underwriting Panel:**
   - Loss distribution histogram (real data, not synthetic)
   - Basis risk score: "0.15 (low) → parametric trigger reliable"
   - Trigger probability: "P(delay > 7 days) = 22%"
   - Coverage recommendations: "Recommend: ICC(A) + Delay Rider + Moisture Clause"

2. **Premium Logic Explanation:**
   - "Expected loss: $12K → Premium should be $15K (1.25x load factor)"
   - "Market rate: 0.8% → RISKCAST rate: 0.6% (25% discount due to low risk score)"

3. **Exclusions Disclosure:**
   - "Potential exclusions: Pre-existing damage, improper packaging, war risk (if applicable)"
   - "Recommend: Pre-shipment inspection to avoid exclusions"

---

## 6. USER VALUE NARRATIVE (CỰC QUAN TRỌNG)

### 6.1. User nhìn vào đã thấy "nó phân tích đơn hàng của mình" chưa?

**TRACE EVIDENCE:**
- ✅ Có: `ShipmentHeader` show: `pol`, `pod`, `carrier`, `etd`, `eta`
- ⚠️ **MẬP MỜ:** `explanation` từ engine có thể generic: "Risk assessment complete. Overall risk score: X/100"
- ❌ **THIẾU:** Không có personalized narrative: "Your electronics shipment from Ho Chi Minh to Los Angeles..."
- ❌ **THIẾU:** Không có context-aware recommendations: "Given your cargo type (electronics) and route (Pacific winter)..."

**KẾT LUẬN:**
- **Không:** User không thấy "nó phân tích đơn hàng của mình"
- **Thiếu:** Personalization, context-awareness, logistics storytelling, actionable recommendations

**ĐỀ XUẤT NARRATIVE:**

**Current (Generic):**
> "Risk assessment complete. Overall risk score: 65/100 (High)."

**Proposed (Personalized):**
> "Your **electronics shipment** (value: $500K) from **Ho Chi Minh (SGN)** to **Los Angeles (LAX)** via **Ocean Carrier** has a **HIGH risk score (65/100)**.  
> 
> **Why?**  
> - **34-day transit** across Pacific during **winter season** → increased storm risk (22% delay probability)  
> - **Electronics cargo** → moisture shock risk from temperature changes  
> - **Singapore port** → 3.2 days average dwell time (congestion)  
> 
> **What to do?**  
> - **Packaging:** Use desiccant + vacuum pack + humidity indicator cards  
> - **Insurance:** Buy ICC(A) coverage + delay rider + moisture clause  
> - **Monitoring:** Enable parametric insurance for delay > 7 days (22% trigger probability)  
> 
> **Expected loss:** $12K (most likely) → $45K (95th percentile) → $78K (99th percentile)"

---

## 7. RISK DISCLOSURE (ĐIỂM CHƯA CÓ)

### 7.1. Rủi ro tiềm ẩn (latent risks)

**TRACE EVIDENCE:**
- ❌ **KHÔNG CÓ:** Không có section "Potential Hidden Risks"
- ❌ **KHÔNG CÓ:** Không có "tail events" explanation
- ❌ **KHÔNG CÓ:** Không có "thresholds" disclosure
- ❌ **KHÔNG CÓ:** Không có "mitigation actions"

**YÊU CẦU THÊM:**

**Potential Hidden Risks Section:**
```
Potential Hidden Risks:
- Climate Tail (La Niña, Pacific Storm) — HIGH
  → Probability: 5% (1 in 20 shipments)
  → Impact: 15-20 day delay, $50K+ loss
  → Mitigation: Parametric insurance for delay > 10 days

- Port Congestion Singapore — MEDIUM
  → Current: 3.2 days (vs 1.5 normal)
  → Peak season: 5-7 days expected
  → Mitigation: Alternative port (Port Klang), or buffer +2 days

- Transit Delay Probability > 22% — MEDIUM
  → P(delay > 7 days) = 22%
  → P(delay > 14 days) = 8%
  → Mitigation: Delay rider insurance, buffer inventory

- Damage Mode: Moisture + Shock — HIGH
  → Electronics → condensation from temperature changes
  → Shock from rough seas (winter storms)
  → Mitigation: Desiccant, vacuum pack, shock sensors
```

**Actionable Mitigations:**
- ✅ Add desiccant: Cost $200, reduces moisture risk by 40%
- ✅ Switch 20RF → 40RH: Cost +$500, reduces condensation risk by 60%
- ✅ Parametric insurance for delay: Cost $1.5K, covers delay > 7 days (22% probability)

---

## 8. FEATURE GAP ANALYSIS

| Dimension | Current | Required | Gap | Priority |
|-----------|---------|---------|-----|-----------|
| **Data Binding** | ✅ Engine → Adapter → ViewModel | ✅ Same | ✅ OK | P0 |
| **Charts** | ⚠️ 7/9 charts working | ✅ 9/9 + algorithm charts | ❌ Missing: FAHP weights, TOPSIS breakdown, Monte Carlo explanation | P1 |
| **Explainability** | ❌ No algorithm explanation | ✅ FAHP + TOPSIS + Monte Carlo explained | ❌ 0% coverage | P0 |
| **Insurance** | ⚠️ Basic loss metrics | ✅ Full underwriting data | ❌ Missing: basis risk, trigger prob, clauses, premium logic | P1 |
| **Realism** | ⚠️ Basic shipment data | ✅ Cargo-container validation, seasonality, port congestion | ❌ Missing: validation, real-time data | P1 |
| **Narrative** | ❌ Generic | ✅ Personalized, context-aware | ❌ 0% personalization | P0 |
| **Personalization** | ❌ None | ✅ Cargo-specific, route-specific | ❌ 0% | P0 |
| **Risk Disclosure** | ❌ None | ✅ Latent risks, tail events, thresholds | ❌ 0% | P1 |

---

## 9. ACTION PLAN (BẮT BUỘC)

### Fix 1: Algorithm Explainability (P0 - CRITICAL)
**Owner:** Frontend + Engine  
**Cost:** 3-5 days  
**Impact:** HIGH (insurance underwriter trust, user understanding)  
**ETA:** Week 1  
**Evidence:** 
- Add FAHP weight visualization (bar chart)
- Add TOPSIS score breakdown (explanation + numbers)
- Add Monte Carlo methodology explanation (tooltip + legend)
- Add factor contribution waterfall (show how layers add up)

### Fix 2: Personalized Narrative (P0 - CRITICAL)
**Owner:** Frontend + Engine  
**Cost:** 2-3 days  
**Impact:** HIGH (user value perception)  
**ETA:** Week 1  
**Evidence:**
- Replace generic explanation với personalized narrative
- Include: cargo type, route, season, specific risks
- Include: actionable recommendations với cost/benefit

### Fix 3: Shipment Realism Validation (P1 - HIGH)
**Owner:** Frontend + Engine  
**Cost:** 2-3 days  
**Impact:** MEDIUM-HIGH (logistics credibility)  
**ETA:** Week 2  
**Evidence:**
- Display cargo type + container type
- Validate cargo-container match (warnings)
- Show route seasonality risk
- Show port congestion data (if available)

### Fix 4: Insurance Underwriting Data (P1 - HIGH)
**Owner:** Engine + Frontend  
**Cost:** 4-6 days  
**Impact:** HIGH (insurance module integration)  
**ETA:** Week 2-3  
**Evidence:**
- Add loss distribution histogram (real data, not synthetic)
- Add basis risk score calculation
- Add trigger probability (P(delay > X days))
- Add coverage clause recommendations
- Add premium logic explanation

### Fix 5: Risk Disclosure Panel (P1 - MEDIUM)
**Owner:** Frontend  
**Cost:** 2-3 days  
**Impact:** MEDIUM (user trust, compliance)  
**ETA:** Week 3  
**Evidence:**
- Add "Potential Hidden Risks" section
- Add tail events explanation
- Add actionable mitigations với cost/benefit
- Add thresholds disclosure (P95, P99, max loss)

### Fix 6: Chart Enhancements (P1 - MEDIUM)
**Owner:** Frontend  
**Cost:** 3-4 days  
**Impact:** MEDIUM (user understanding)  
**ETA:** Week 3-4  
**Evidence:**
- RiskRadar: Add contribution %, FAHP weight
- FinancialModule: Flag synthetic data, add tail risk section
- RiskScenarioFanChart: Add Monte Carlo explanation
- LayersTable: Add FAHP weight, TOPSIS score columns

### Fix 7: Data Quality Indicators (P2 - LOW)
**Owner:** Frontend  
**Cost:** 1-2 days  
**Impact:** LOW-MEDIUM (transparency)  
**ETA:** Week 4  
**Evidence:**
- Add data freshness indicator
- Flag synthetic/estimated data
- Add data reliability matrix (implement từ engine)

### Fix 8: Empty State Improvements (P2 - LOW)
**Owner:** Frontend  
**Cost:** 1 day  
**Impact:** LOW (UX)  
**ETA:** Week 4  
**Evidence:**
- Distinguish: "No data" vs "Error" vs "Loading"
- Add retry mechanism
- Add "Run analysis" CTA

---

## 10. TỔNG KẾT

### Điểm mạnh:
1. ✅ Data flow đúng: Engine → Adapter → ViewModel
2. ✅ Không có fake data generation
3. ✅ Charts bind đúng với engine data
4. ✅ Có basic loss metrics (expectedLoss, p95, p99)

### Điểm yếu (CRITICAL):
1. ❌ **KHÔNG CÓ algorithm explainability** → user không hiểu vì sao điểm như vậy
2. ❌ **Narrative generic** → user không thấy "nó phân tích đơn hàng của mình"
3. ❌ **Thiếu insurance underwriting data** → không đủ để làm insurance
4. ❌ **Thiếu shipment realism validation** → không check cargo-container match
5. ❌ **Không có risk disclosure** → user không biết latent risks, tail events

### Priority Ranking:
1. **P0 (CRITICAL):** Algorithm explainability, Personalized narrative
2. **P1 (HIGH):** Insurance underwriting data, Shipment realism, Risk disclosure, Chart enhancements
3. **P2 (MEDIUM-LOW):** Data quality indicators, Empty state improvements

### Kết luận:
**Trang /results hiện tại:**
- ✅ **Đạt:** Enterprise SaaS UI/UX, basic risk intelligence
- ⚠️ **Thiếu:** Algorithm transparency, insurance-grade data, personalized narrative
- ❌ **Chưa đạt:** Insurance underwriting readiness, logistics realism validation, risk disclosure

**Để đạt tiêu chuẩn Enterprise SaaS + Risk Intelligence + Insurance Underwriting:**
- Cần implement 8 fixes trên (ưu tiên P0, P1)
- Estimated effort: 3-4 weeks (1 developer full-time)
- Impact: Tăng user trust, insurance module integration, logistics credibility

---

**END OF AUDIT**
