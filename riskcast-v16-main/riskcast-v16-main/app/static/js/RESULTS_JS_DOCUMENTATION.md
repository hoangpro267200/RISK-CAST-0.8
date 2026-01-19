# TÀI LIỆU CHI TIẾT CÁC FILE JAVASCRIPT TRONG TRANG RESULTS

## TỔNG QUAN
Trang Results sử dụng kiến trúc component-based với các file JS được tổ chức theo mô hình orchestration. Tất cả logic nghiệp vụ nằm trong `state.js`, còn `main.js` chỉ điều phối việc mount các components.

---

## 1. FILE ĐIỀU PHỐI CHÍNH (ORCHESTRATION)

### 1.1. `main.js`
**Đường dẫn:** `/static/js/main.js`

**Chức năng chính:**
- **Điều phối toàn bộ hệ thống ResultsOS:** Không chứa logic nghiệp vụ, chỉ điều phối việc mount components
- **Load dữ liệu:** Gọi `loadSummaryStateWithAPI()` từ `state.js` để lấy dữ liệu (ưu tiên Backend API, fallback về Storage)
- **Tính toán Recommendations:** Gọi `buildRecommendations()` để tạo khuyến nghị bảo hiểm, cửa sổ vận chuyển, provider fit
- **Mount tất cả components:** Khởi tạo và mount 16 components vào các slot DOM tương ứng
- **Freeze state:** Đảm bảo immutability cho mục đích audit trail
- **Xử lý Traceability:** Render phần truy vết quyết định dưới dạng HTML collapsible

**Các components được mount:**
1. RiskScoreOrb (Decision Hub - trung tâm)
2. RiskRingCard (Decision Hub - các thẻ orbit)
3. RiskRadar (Decision Hub - biểu đồ radar)
4. AINarrativePanel (Decision Hub - AI insight)
5. InsuranceDecisionPanel (Decision Hub - khuyến nghị)
6. ShipmentHeader (Supporting Evidence)
7. GlobalGauge (Supporting Evidence)
8. MiniGauges (Supporting Evidence)
9. RadarChart (Supporting Evidence)
10. LayersTable (Supporting Evidence)
11. RiskFactorsTable (Supporting Evidence)
12. FinancialHistogram (Supporting Evidence)
13. LossCurve (Supporting Evidence)
14. DecisionSignals (Supporting Evidence)
15. MiniStrategyScenarios (Supporting Evidence)
16. TimelineTrack (Supporting Evidence)

**Các hàm chính:**
- `initResultsOS()`: Hàm khởi tạo chính
- `mountComponent()`: Helper để mount component với error handling
- `renderTraceability()`: Render phần traceability
- `deriveRiskLevel()`: Chuẩn hóa risk level thành format nội bộ ('low'|'medium'|'high')

---

### 1.2. `state.js`
**Đường dẫn:** `/static/js/state.js`

**Chức năng chính:**
- **Single Source of Truth:** Chứa tất cả dữ liệu và logic nghiệp vụ cho ResultsOS
- **Data Loading:** 
  - `loadFromBackendAPI()`: Load dữ liệu từ endpoint `/results/data`
  - `loadSummaryState()`: Load từ sessionStorage/localStorage
  - `loadSummaryStateWithAPI()`: Ưu tiên API, fallback storage
- **Data Transformation:**
  - `transformBackendAPIToResults()`: Chuyển format API backend → ResultsOS format
  - `transformSummaryToResults()`: Chuyển format summary state → ResultsOS format
- **Risk Calculation:**
  - `getRiskLayers()`: Extract và normalize risk layers từ summary state
  - `getGlobalRiskScore()`: Tính điểm rủi ro tổng thể bằng FAHP-weighted aggregation
  - `getTimelineData()`: Generate timeline data từ global risk
- **Recommendations Engine:**
  - `computeInsuranceRecommendation()`: Tính khuyến nghị bảo hiểm dựa trên risk score, P95/P99, tail contribution
  - `computeSafeShippingWindow()`: Tính cửa sổ vận chuyển an toàn dựa trên climate risk
  - `computeProviderFit()`: Ranking các nhà cung cấp bảo hiểm dựa trên route, cargo value, risk level
  - `computeDecisionTrace()`: Tạo traceability với các triggers và signals
  - `buildRecommendations()`: Tổng hợp tất cả recommendations
- **Default State:** Export `resultsState` object chứa default/demo data

**Các hàm helper:**
- `validateState()`: Validate structure của summary state
- `clampScore()`: Clamp score về range 0-100
- `extractTradeLane()`: Extract trade lane từ route string
- `mapLayerToCategory()`: Map layer name sang category
- `generateHistogramData()`: Generate histogram bins từ P95/P99
- `generateLossCurveData()`: Generate loss curve points từ P95/P99
- `formatCurrency()`: Format số tiền USD

---

## 2. COMPONENTS - DECISION HUB (PRIMARY VIEW)

### 2.1. `RiskScoreOrb.js`
**Đường dẫn:** `/static/js/components/RiskScoreOrb.js`

**Chức năng:**
- **Hiển thị điểm rủi ro tổng thể** dưới dạng orb lớn ở trung tâm Decision Hub
- **Visual dominant element:** Component quan trọng nhất trên trang Results
- **Risk level visualization:** Màu sắc thay đổi theo risk level (low/medium/high)
- **Pulse animation:** Hiệu ứng pulse dựa trên risk level
- **Responsive:** Tự động inject CSS styles

**Input data:**
```javascript
{
  overallRiskScore: number,  // 0-100
  riskLevel: string         // 'low'|'medium'|'high'
}
```

**Methods:**
- `mount(el, data)`: Mount component vào DOM element
- `update(data)`: Update với dữ liệu mới
- `destroy()`: Cleanup animations và references

---

### 2.2. `RiskRingCard.js`
**Đường dẫn:** `/static/js/components/RiskRingCard.js`

**Chức năng:**
- **Hiển thị các risk driver** dưới dạng thẻ compact orbit-style
- **Thiết kế để xếp quanh RiskScoreOrb** trong layout radial
- **Progress bar visualization:** Thanh progress thể hiện mức rủi ro
- **Icon support:** Hỗ trợ icon cho từng loại risk
- **Risk level coloring:** Màu sắc theo risk level

**Input data:**
```javascript
{
  riskName: string,     // Tên risk driver (VN)
  riskValue: number,    // 0-100
  iconName: string      // Optional icon name
}
```

**Methods:**
- `mount(el, data)`: Mount component
- `update(data)`: Update data
- `destroy()`: Cleanup

---

### 2.3. `RiskRadar.js`
**Đường dẫn:** `/static/js/components/RiskRadar.js`

**Chức năng:**
- **Biểu đồ radar chính** trong Decision Hub
- **Tóm tắt cách điểm rủi ro tổng thể được cấu thành** từ các risk layers
- **Trả lời câu hỏi:** "Risk dimensions nào đang drive overall risk?"
- **Chart.js integration:** Sử dụng Chart.js radar chart với dark theme
- **Error handling:** Fallback UI nếu Chart.js không available

**Input data:**
```javascript
{
  labels: string[],   // Array tên các risk layers
  values: number[]    // Array điểm số (0-100)
}
```

**Methods:**
- `mount(el, data)`: Mount và khởi tạo chart
- `update(data)`: Update chart data
- `destroy()`: Destroy chart instance

---

### 2.4. `InsuranceDecisionPanel.js`
**Đường dẫn:** `/static/js/components/InsuranceDecisionPanel.js`

**Chức năng:**
- **Khuyến nghị điều hành chính:** Hiển thị insurance recommendations, shipping windows, provider fit
- **4 sections chính:**
  1. **Insurance Decision:** Khuyến nghị bảo hiểm (required/level/package/confidence)
  2. **Safe Shipping Window:** Cửa sổ vận chuyển an toàn (recommended/avoid windows)
  3. **Provider Fit:** Ranking các nhà cung cấp bảo hiểm (fit score, strengths, tradeoffs)
  4. **Decision Traceability:** Truy vết quyết định (collapsible, chứa triggers và signals)

**Input data:**
```javascript
{
  insurance: {
    required: boolean,
    level: string,        // 'LOW'|'MEDIUM'|'HIGH'
    package: string,      // Package type (ICC A/B/C)
    confidence: number,   // 0-100
    reasons: string[],
    coverageChecklist: string[],
    disclaimers: string[]
  },
  timing: {
    recommendedWindow: string,
    avoidWindow: string,
    riskReduction: number,
    rationale: string[],
    assumptions: string[]
  },
  providers: [{
    name: string,
    fit: number,         // 0-100
    strengths: string[],
    tradeoffs: string[],
    suggestedClauses: string[]
  }],
  trace: {
    triggers: [{signal, value, threshold, impact, note}],
    dominantSignals: string[],
    version: string
  }
}
```

**Methods:**
- `mount(el, data)`: Mount panel và render tất cả sections
- `update(data)`: Update với recommendations mới
- `destroy()`: Cleanup

---

### 2.5. `AINarrativePanel.js`
**Đường dẫn:** `/static/js/components/AINarrativePanel.js`

**Chức năng:**
- **Executive narrative panel:** Giải thích risk intelligence bằng ngôn ngữ rõ ràng
- **Phục vụ enterprise và academic review:** Ngôn ngữ defensible và traceable
- **2 sections:**
  1. **Executive Summary:** Tóm tắt ngắn gọn risk assessment
  2. **Detailed Analysis:** Phân tích chi tiết (collapsible)

**Input data:**
```javascript
{
  summary: {
    overallRiskScore: number,  // 0-100
    riskLevel: string          // 'low'|'medium'|'high'
  },
  layers: [{name, score, note}],
  factors: [{factor, impact, probability, compositeScore}],
  loss: {p95, p99, tailContribution}
}
```

**Methods:**
- `mount(el, data)`: Mount panel
- `update(data)`: Update narrative
- `destroy()`: Cleanup

---

## 3. COMPONENTS - SUPPORTING EVIDENCE

### 3.1. `ShipmentHeader.js`
**Đường dẫn:** `/static/js/components/ShipmentHeader.js`

**Chức năng:**
- **Hiển thị shipment metadata** trong glassmorphic card
- **Thông tin hiển thị:** ID, route, incoterms, cargo type, value (USD), ETA
- **Data normalization:** Tự động normalize và format dữ liệu

**Input data:**
```javascript
{
  id: string,
  route: string,
  incoterms: string,
  cargo: string,        // cargo type
  value_usd: number,    // cargo value
  eta: string           // ISO date
}
```

**Methods:**
- `mount(el, shipment)`: Mount component
- `update(shipment)`: Update shipment data

---

### 3.2. `GlobalGauge.js`
**Đường dẫn:** `/static/js/components/GlobalGauge.js`

**Chức năng:**
- **Circular SVG gauge** hiển thị global risk score (0-100)
- **Color-coded zones:** Green (low), yellow (medium), red (high)
- **Smooth animations:** Animation khi update score
- **SVG-based:** Sử dụng SVG để đảm bảo crisp rendering

**Input data:**
```javascript
score: number  // 0-100
```

**Methods:**
- `mount(el, score)`: Mount gauge với initial score
- `update(newScore)`: Update với animation
- `destroy()`: Cleanup animation frames

---

### 3.3. `MiniGauges.js`
**Đường dẫn:** `/static/js/components/MiniGauges.js`

**Chức năng:**
- **Responsive grid của mini gauge cards**
- **Mỗi card hiển thị:** Label, percentage value, progress bar
- **Adaptive layout:** Tự động adapt với số lượng gauges
- **Risk level coloring:** Màu sắc theo risk level

**Input data:**
```javascript
[
  {label: string, value: number},  // 0-100
  ...
]
```

**Methods:**
- `mount(el, gauges)`: Mount grid
- `update(gauges)`: Update gauge data

---

### 3.4. `RadarChart.js`
**Đường dẫn:** `/static/js/components/RadarChart.js`

**Chức năng:**
- **Radar chart component** sử dụng Chart.js
- **Dark minimalist styling:** Theme tối với neon accents
- **Single hoặc multiple datasets:** Hỗ trợ cả 2 modes
- **Risk-based coloring:** Màu sắc dựa trên risk level
- **Smooth animations:** Chart.js animations

**Input data:**
```javascript
{
  labels: string[],
  values: number[]      // Single dataset mode
}
// HOẶC
{
  labels: string[],
  datasets: [{values: number[], label: string}]
}
```

**Methods:**
- `mount(el, data)`: Mount chart
- `update(data)`: Update chart data
- `destroy()`: Destroy chart instance

---

### 3.5. `LayersTable.js`
**Đường dẫn:** `/static/js/components/LayersTable.js`

**Chức năng:**
- **Enterprise table format** hiển thị risk layers overview
- **Sorted by score:** Sắp xếp giảm dần theo score
- **Color-coded:** Màu sắc theo risk level
- **3 columns:** Tên, Điểm, Note

**Input data:**
```javascript
[
  {
    name: string,
    score: number,  // 0-100
    note: string
  },
  ...
]
```

**Methods:**
- `mount(el, data)`: Mount table
- `update(data)`: Update table rows
- `destroy()`: Cleanup

---

### 3.6. `RiskFactorsTable.js`
**Đường dẫn:** `/static/js/components/RiskFactorsTable.js`

**Chức năng:**
- **Hiển thị atomic risk drivers** với impact và probability metrics
- **Sorted by impact:** Sắp xếp giảm dần theo impact, sau đó probability
- **Composite score support:** Hỗ trợ hiển thị composite score (impact × probability)
- **Columns:** Factor, Category, Impact, Probability, Composite Score (optional)

**Input data:**
```javascript
[
  {
    factor: string,
    category: string,
    impact: number,        // 0-1
    probability: number,   // 0-1
    compositeScore: number // 0-1 (optional)
  },
  ...
]
```

**Methods:**
- `mount(el, data)`: Mount table
- `update(data)`: Update table
- `destroy()`: Cleanup

---

### 3.7. `FinancialHistogram.js`
**Đường dẫn:** `/static/js/components/FinancialHistogram.js`

**Chức năng:**
- **Bar chart visualization** của loss distribution
- **Chart.js integration:** Sử dụng Chart.js bar chart
- **Shows most likely loss range vs extreme tail risk**
- **Dark theme:** Styling tối với risk-based coloring

**Input data:**
```javascript
{
  bins: number[],    // Loss buckets (USD)
  counts: number[],  // Frequency per bucket
  currency: string   // 'USD'
}
```

**Methods:**
- `mount(el, data)`: Mount histogram
- `update(data)`: Update chart data
- `destroy()`: Destroy chart

---

### 3.8. `LossCurve.js`
**Đường dẫn:** `/static/js/components/LossCurve.js`

**Chức năng:**
- **Loss curve visualization** sử dụng Chart.js line chart
- **Shows probability vs loss relationship**
- **P95/P99 annotations:** Đánh dấu các điểm P95 và P99
- **Tail risk visualization:** Làm nổi bật tail risk region

**Input data:**
```javascript
{
  points: [
    {loss: number, probability: number},  // 0-1
    ...
  ]
}
```

**Methods:**
- `mount(el, data)`: Mount curve chart
- `update(data)`: Update curve
- `destroy()`: Destroy chart

---

### 3.9. `DecisionSignals.js`
**Đường dẫn:** `/static/js/components/DecisionSignals.js`

**Chức năng:**
- **Executive Decision Signals panel**
- **Chuyển đổi risk intelligence thành actionable decisions**
- **Read-only mode:** Không có interaction, chỉ hiển thị
- **Sections:**
  - Overall Risk Signal
  - Dominant Layers
  - Key Drivers
  - Loss Metrics

**Input data:**
```javascript
{
  decision: {
    riskLevel: string,           // 'low'|'medium'|'high'
    overallRiskScore: number,    // 0-100
    dominantLayers: [{name, score}],
    keyDrivers: [{factor, impact, probability}],
    loss: {p95, p99, tailContribution}
  }
}
```

**Methods:**
- `mount(el, data)`: Mount panel
- `update(data)`: Update signals
- `destroy()`: Cleanup

---

### 3.10. `MiniStrategyScenarios.js`
**Đường dẫn:** `/static/js/components/MiniStrategyScenarios.js`

**Chức năng:**
- **2 executive strategy scenarios** derived từ global risk movement
- **Scenario A:** Risk increase (+10% delta)
- **Scenario B:** Risk decrease (-15% delta)
- **Posture mapping:** Defensive/Balanced/Opportunistic dựa trên risk thresholds

**Input data:**
```javascript
{
  baseRiskScore: number,  // 0-100
  basePosture: string     // 'low'|'medium'|'high'
}
```

**Methods:**
- `mount(el, data)`: Mount scenarios
- `update(data)`: Update scenarios
- `destroy()`: Cleanup

---

### 3.11. `TimelineTrack.js`
**Đường dẫn:** `/static/js/components/TimelineTrack.js`

**Chức năng:**
- **Sequential risk assessment points visualization**
- **Hiển thị risk stability và volatility** across evaluation iterations
- **Lưu ý:** Timeline này là assessment iterations, KHÔNG phải historical dates
- **Labels:** T-3, T-2, T-1, T0 (evaluation steps)

**Input data:**
```javascript
{
  timeline: [
    {label: string, risk: number},  // 0-100
    ...
  ]
}
```

**Methods:**
- `mount(el, data)`: Mount timeline
- `update(data)`: Update timeline
- `destroy()`: Cleanup

---

## 4. CẤU TRÚC DỮ LIỆU

### 4.1. ResultsOS State Format
Tất cả components nhận data từ `state.js` đã được transform về format chuẩn:

```javascript
{
  shipment: {
    id: string,
    route: string,
    incoterms: string,
    cargo: string,
    value_usd: number,
    eta: string,
    context: {mode, tradeLane, riskSensitivity}
  },
  globalRisk: number,           // 0-100
  layers: [{name, score, weight, note}],
  factors: [{factor, category, impact, probability, compositeScore}],
  loss: {currency, p95, p99, tailContribution, confidenceLevel, note},
  charts: {
    radar: {labels, values},
    financialHistogram: {bins, counts, currency},
    lossCurve: {points}
  },
  decision: {
    riskLevel: string,
    overallRiskScore: number,
    dominantLayers: [{name, score}],
    keyDrivers: [{factor, impact, probability}],
    loss: {p95, p99, tailContribution},
    decisionRationale: string[],
    payloadForDecisionSignals: {...}
  },
  scenarios: {
    baseRiskScore: number,
    basePosture: string,
    payloadForMiniScenarios: {...}
  },
  payloadForTimelineTrack: {
    timeline: [{label, risk}]
  },
  recommendations: {
    insurance: {...},
    timing: {...},
    providers: [...],
    trace: {...}
  },
  meta: {version, source, timestamp},
  methodology: {...},
  traceability: {decisionBasis: string[], references: string[]}
}
```

---

## 5. DEPENDENCIES

### 5.1. External Libraries
- **Chart.js 4.4.1:** Required cho RadarChart, FinancialHistogram, LossCurve, RiskRadar
- **Chart.js Plugin Annotation 3.0.1:** Required cho LossCurve annotations

### 5.2. Browser APIs
- **Fetch API:** Để load data từ backend (`/results/data`)
- **sessionStorage/localStorage:** Để load data từ storage
- **DOM APIs:** Tất cả components tương tác với DOM

---

## 6. FLOW HOẠT ĐỘNG

1. **Page Load:** `results.html` load và gọi `main.js`
2. **main.js init:**
   - Gọi `loadSummaryStateWithAPI()` từ `state.js`
   - Transform data về ResultsOS format
   - Tính toán recommendations bằng `buildRecommendations()`
   - Freeze state để đảm bảo immutability
3. **Component Mounting:**
   - `main.js` mount từng component vào các slot DOM tương ứng
   - Mỗi component tự inject CSS styles
   - Components render dữ liệu đã được pre-computed
4. **User Interaction:**
   - Các components chủ yếu là read-only
   - Chỉ có collapsible sections (traceability, details) có thể toggle
5. **State Exposure:**
   - `window.__RESULTSOS__` được expose để debugging
   - Chứa frozen state, component instances, recommendations

---

## 7. KIẾN TRÚC & NGUYÊN TẮC

### 7.1. Separation of Concerns
- **state.js:** Tất cả business logic và data transformation
- **main.js:** Chỉ orchestration và component lifecycle
- **Components:** Chỉ presentation, không có business logic

### 7.2. Immutability
- State được freeze sau khi compute để đảm bảo audit trail integrity
- Components nhận pre-computed data, không modify state

### 7.3. Defensive Programming
- Tất cả components có error handling
- Validation data trước khi render
- Graceful degradation nếu data thiếu

### 7.4. Self-contained Components
- Mỗi component tự inject CSS styles
- Không phụ thuộc external CSS files
- Isolated styling để tránh conflicts

---

## 8. SLOT ID MAPPING

Các slot DOM IDs được sử dụng trong `main.js`:

| Slot ID | Component | Vị trí |
|---------|-----------|--------|
| `slot-risk-score-orb` | RiskScoreOrb | Decision Hub (trung tâm) |
| `slot-risk-ring-cards` | RiskRingCard (multiple) | Decision Hub (orbit) |
| `slot-risk-radar` | RiskRadar | Decision Hub |
| `slot-ai-insight` | AINarrativePanel | Decision Hub |
| `insurance-decision-panel` | InsuranceDecisionPanel | Decision Hub |
| `slot-shipment` | ShipmentHeader | Supporting Evidence |
| `slot-global-risk` | GlobalGauge | Supporting Evidence |
| `slot-mini-gauges` | MiniGauges | Supporting Evidence |
| `slot-radar` | RadarChart | Supporting Evidence |
| `slot-layers-table` | LayersTable | Supporting Evidence |
| `slot-factors-table` | RiskFactorsTable | Supporting Evidence |
| `slot-financial-histogram` | FinancialHistogram | Supporting Evidence |
| `slot-loss-curve` | LossCurve | Supporting Evidence |
| `slot-ai-narrative` | AINarrativePanel | Supporting Evidence |
| `slot-decision-signals` | DecisionSignals | Supporting Evidence |
| `slot-strategy-scenarios` | MiniStrategyScenarios | Supporting Evidence |
| `slot-timeline` | TimelineTrack | Supporting Evidence |
| `slot-traceability` | Traceability (HTML) | Traceability Section |

---

## 9. GHI CHÚ QUAN TRỌNG

1. **Không có HTML/CSS trong results.html:** Tất cả structure được tạo bởi JS components
2. **Chart.js dependency:** Một số components cần Chart.js, phải load trước khi init
3. **Data format consistency:** Tất cả data phải đúng format như mô tả, components sẽ validate
4. **Risk level standardization:** Internal format là 'low'|'medium'|'high', UI formatting do components handle
5. **Immutability:** State được freeze, không modify sau khi compute
6. **Error handling:** Components có defensive checks, nhưng vẫn cần đảm bảo data đúng format

---

## 10. TESTING & DEBUGGING

### 10.1. Debug Mode
- Set `DEBUG = true` trong `main.js` để enable verbose logging
- Console logs sẽ hiển thị chi tiết mounting process

### 10.2. Window Exposure
- `window.__RESULTSOS__` chứa:
  - `state`: Frozen state object
  - `components`: Mounted component instances
  - `recommendations`: Frozen recommendations object

### 10.3. Common Issues
- **Chart.js not loaded:** Components sẽ show error message
- **Missing DOM slots:** Components sẽ skip mounting với warning
- **Invalid data format:** Components sẽ use safe defaults
- **State not loaded:** System sẽ use default state từ `resultsState`

---

*Tài liệu này mô tả toàn bộ các file JavaScript và chức năng của chúng trong trang Results. Để biết thêm chi tiết về implementation, vui lòng tham khảo code comments trong từng file.*
