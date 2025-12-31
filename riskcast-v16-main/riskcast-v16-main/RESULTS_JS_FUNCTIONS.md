# Tài Liệu Tổng Hợp Chức Năng JavaScript - Trang ResultsOS

**Ngày tạo:** 2025-01-27  
**Phiên bản:** ResultsOS v4000  
**Mục đích:** Tài liệu đầy đủ về tất cả chức năng JavaScript trong trang Results

---

## 📋 Mục Lục

1. [Kiến Trúc Tổng Quan](#kiến-trúc-tổng-quan)
2. [File main.js - Điều Phối Chính](#file-mainjs---điều-phối-chính)
3. [File state.js - Quản Lý State](#file-statejs---quản-lý-state)
4. [Components - Các Component UI](#components---các-component-ui)
5. [Luồng Dữ Liệu](#luồng-dữ-liệu)
6. [API & Functions Reference](#api--functions-reference)

---

## 🏗️ Kiến Trúc Tổng Quan

### Nguyên Tắc Thiết Kế

- **Separation of Concerns**: Logic nghiệp vụ ở `state.js`, điều phối ở `main.js`
- **Immutability**: State được freeze sau khi tính toán để đảm bảo tính audit
- **Presentation Layer**: Components chỉ nhận dữ liệu đã tính toán, không có logic quyết định
- **Traceability**: Tất cả recommendations đều có decision trace

### Cấu Trúc File

```
app/static/js/
├── main.js                    # Điều phối chính, mount components
├── state.js                   # Quản lý state, tính toán, business logic
└── components/
    ├── ShipmentHeader.js      # Hiển thị thông tin shipment
    ├── GlobalGauge.js         # Gauge tổng thể
    ├── MiniGauges.js          # Mini gauges cho các layers
    ├── RadarChart.js          # Biểu đồ radar
    ├── LayersTable.js         # Bảng các risk layers
    ├── RiskFactorsTable.js    # Bảng các risk factors
    ├── FinancialHistogram.js   # Histogram tài chính
    ├── LossCurve.js           # Đường cong tổn thất
    ├── AINarrativePanel.js    # Panel narrative AI
    ├── DecisionSignals.js     # Tín hiệu quyết định
    ├── MiniStrategyScenarios.js # Kịch bản chiến lược
    ├── TimelineTrack.js       # Timeline rủi ro
    ├── InsuranceDecisionPanel.js # Panel khuyến nghị bảo hiểm
    ├── RiskScoreOrb.js        # Orb điểm rủi ro (Decision Hub)
    ├── RiskRingCard.js        # Card vòng tròn rủi ro (Decision Hub)
    └── RiskRadar.js           # Radar rủi ro (Decision Hub)
```

---

## 📄 File main.js - Điều Phối Chính

### Mục Đích
File điều phối chính, chỉ chứa logic mount components, không có business logic.

### Constants & Variables

```javascript
const DEBUG = true;              // Flag điều khiển verbose logging
const componentInstances = {};   // Lưu trữ instances của components
```

### Functions

#### 1. `deriveRiskLevel(globalRisk, fallbackLevel)`
**Mục đích:** Chuẩn hóa risk level thành format nội bộ  
**Tham số:**
- `globalRisk` (number): Điểm rủi ro tổng thể (0-100)
- `fallbackLevel` (string, optional): Risk level từ decision context

**Trả về:** `'low' | 'medium' | 'high'`

**Logic:**
- < 40: `'low'`
- 40-69: `'medium'`
- >= 70: `'high'`

---

#### 2. `mountComponent(slotId, ComponentClass, data, options)`
**Mục đích:** Mount component vào DOM element với error handling  
**Tham số:**
- `slotId` (string): ID của DOM element
- `ComponentClass` (Function): Constructor của component class
- `data` (*): Dữ liệu truyền vào component
- `options` (Object, optional): Tùy chọn cho component

**Trả về:** Component instance hoặc `null` nếu thất bại

**Chức năng:**
- Tìm DOM element theo ID
- Tạo instance component
- Gọi `mount()` method
- Lưu instance vào `componentInstances`
- Xử lý lỗi gracefully

---

#### 3. `renderTraceability(slotId, state)`
**Mục đích:** Render traceability block dạng HTML read-only  
**Tham số:**
- `slotId` (string): ID của DOM element
- `state` (Object): Active state object

**Chức năng:**
- Tạo collapsible structure (collapsed mặc định)
- Hiển thị:
  - Cơ sở quyết định (decision basis)
  - Tài liệu tham khảo (references)
  - Decision engine trace (nếu có)
- Inject CSS styles
- Xử lý toggle icon animation

---

#### 4. `escapeHtml(str)`
**Mục đích:** Escape HTML để ngăn XSS  
**Tham số:**
- `str` (string): String cần escape

**Trả về:** Escaped string

---

#### 5. `createResultsOSStructure()`
**Mục đích:** Tạo DOM structure cho ResultsOS  
**Chức năng:**
- Tìm `main.results-os` element
- Kiểm tra structure đã tồn tại chưa
- Tạo structure với 3 sections:
  1. **Decision Hub**: RiskScoreOrb, RiskRingCards, RiskRadar, AIInsight, InsuranceDecisionPanel
  2. **Supporting Evidence** (Collapsible): Tất cả components hỗ trợ
  3. **Traceability**: Traceability block

---

#### 6. `initResultsOS()`
**Mục đích:** Khởi tạo toàn bộ ResultsOS  
**Luồng xử lý:**

1. **Tạo DOM structure**
   ```javascript
   createResultsOSStructure();
   ```

2. **Kiểm tra Chart.js**
   - Kiểm tra Chart.js đã load chưa
   - Cảnh báo nếu thiếu (nhưng vẫn tiếp tục)

3. **Load & Transform State**
   ```javascript
   const summaryState = loadSummaryState();
   let activeState = transformSummaryToResults(summaryState);
   ```

4. **Compute Recommendations**
   ```javascript
   const recommendations = buildRecommendations(activeState);
   Object.freeze(recommendations); // Freeze để immutable
   activeState.recommendations = recommendations;
   ```

5. **Freeze State**
   - Freeze toàn bộ activeState
   - Freeze nested objects (layers, factors, decision, etc.)

6. **Mount Components - Decision Hub**
   - RiskScoreOrb
   - RiskRingCard (top 6 layers)
   - RiskRadar
   - AINarrativePanel (AI Insight)
   - InsuranceDecisionPanel

7. **Mount Components - Supporting Evidence**
   - ShipmentHeader
   - GlobalGauge
   - MiniGauges
   - RadarChart
   - LayersTable
   - RiskFactorsTable
   - FinancialHistogram
   - LossCurve
   - AINarrativePanel (narrative)
   - DecisionSignals
   - MiniStrategyScenarios
   - TimelineTrack

8. **Render Traceability**
   ```javascript
   renderTraceability('slot-traceability', activeState);
   ```

9. **Initialize Collapsible Sections**
   ```javascript
   initCollapsibleSections();
   ```

10. **Expose to Window** (Debug)
    ```javascript
    window.__RESULTSOS__ = {
      state: activeState,
      summaryState: summaryState,
      components: componentInstances,
      recommendations: activeState.recommendations
    };
    ```

---

#### 7. `initCollapsibleSections()`
**Mục đích:** Khởi tạo toggle icons cho collapsible sections  
**Chức năng:**
- Tìm tất cả `.results-collapsible` elements
- Set initial icon state (▲/▼)
- Thêm event listener cho toggle

---

## 📊 File state.js - Quản Lý State

### Mục Đích
Single source of truth cho tất cả dữ liệu ResultsOS. Chứa business logic, tính toán, validation.

### Constants

```javascript
const SUMMARY_STATE_KEY = 'RISKCAST_SUMMARY_STATE';
```

### Exported Functions

#### 1. `loadSummaryState()`
**Mục đích:** Load summary state từ storage  
**Nguồn:** sessionStorage (ưu tiên) → localStorage (fallback)  
**Trả về:** Summary state object hoặc `null`

---

#### 2. `validateState(summaryState)`
**Mục đích:** Validate cấu trúc summary state  
**Kiểm tra:**
- State là object
- Có `shipment` object
- Shipment có `route` hoặc `id`
- Recommendations structure (nếu có)

**Trả về:** `true` nếu valid, `false` nếu không

---

#### 3. `getRiskLayers(summaryState)`
**Mục đích:** Lấy risk layers từ summary state  
**Logic:**
- Map `riskInputs` thành layers với FAHP weights
- 6 layers: Port Congestion (0.22), Weather Volatility (0.18), Carrier Reliability (0.16), Geopolitical (0.14), Financial (0.12), ESG (0.18)
- Return default layers nếu không có data

**Trả về:** Array of layer objects

---

#### 4. `getGlobalRiskScore(layers)`
**Mục đích:** Tính global risk score từ layers  
**Công thức:** FAHP-weighted aggregation
```
globalRisk = Σ(layer.score × layer.weight)
```

**Trả về:** Number (0-100)

---

#### 5. `getTimelineData(summaryState, globalRisk)`
**Mục đích:** Lấy timeline data  
**Logic:**
- Nếu có timeline trong summary → dùng
- Nếu không → generate từ globalRisk với variation ±15

**Trả về:** Array of `{label, risk}` objects

---

#### 6. `transformSummaryToResults(summaryState)`
**Mục đích:** Transform summary state thành ResultsOS format  
**Output Structure:**
```javascript
{
  shipment: {...},           // Shipment context
  globalRisk: number,        // Global risk score
  layers: [...],            // Risk layers
  factors: [...],           // Risk factors
  loss: {...},              // Loss metrics (p95, p99, tailContribution)
  charts: {...},            // Chart data (radar, histogram, lossCurve)
  decision: {...},          // Decision context
  scenarios: {...},         // Scenario data
  timeline: [...],          // Timeline data
  timelineMeta: {...},      // Timeline metadata
  payloadForTimelineTrack: {...}
}
```

**Trả về:** ResultsOS state object

---

#### 7. `computeInsuranceRecommendation(resultsState)`
**Mục đích:** Tính toán khuyến nghị bảo hiểm  
**Input:** ResultsOS state  
**Output:**
```javascript
{
  required: boolean,        // Có cần bảo hiểm không
  level: 'LOW'|'MEDIUM'|'HIGH',
  package: string,          // Gói bảo hiểm đề xuất
  confidence: number,       // Độ tin cậy (0-100)
  reasons: string[],        // Lý do
  coverageChecklist: string[], // Danh sách coverage
  disclaimers: string[]     // Tuyên bố miễn trừ
}
```

**Decision Rules:**
- Overall risk >= 65 → HIGH level
- P95 loss ratio >= 10% → Required
- Tail contribution >= 20% → Required
- Climate score >= 70 → Required
- Cargo value >= $1M → Required

**Package Mapping:**
- LOW → "ICC C (Basic Cargo)"
- MEDIUM → "ICC B + Theft/Damage"
- HIGH → "ICC A (All Risks) + War & Strikes + Delay"

---

#### 8. `computeSafeShippingWindow(resultsState)`
**Mục đích:** Tính toán cửa sổ vận chuyển an toàn  
**Output:**
```javascript
{
  recommendedWindow: string,  // Cửa sổ khuyến nghị
  avoidWindow: string,        // Cửa sổ nên tránh
  riskReduction: number,      // % giảm rủi ro
  rationale: string[],        // Lý do
  assumptions: string[]        // Giả định
}
```

**Logic:**
- Climate risk >= 65 → Tránh tháng 5-7, khuyến nghị tháng 3-4
- Risk reduction: 20-35% tùy climate score

---

#### 9. `computeProviderFit(resultsState)`
**Mục đích:** Tính toán xếp hạng phù hợp nhà cung cấp  
**Output:** Array of provider objects (sorted desc by fit score)
```javascript
[{
  name: string,
  fit: number,              // 0-100
  strengths: string[],
  tradeoffs: string[],
  suggestedClauses: string[]
}, ...]
```

**Scoring Criteria:**
- Route Experience (30%)
- Claim Speed (25%)
- Clause Flexibility (25%)
- Cost Efficiency (20%)

**Providers:** Provider A, B, C (prototype)

---

#### 10. `computeDecisionTrace(resultsState)`
**Mục đích:** Tính toán decision traceability  
**Output:**
```javascript
{
  triggers: [{
    signal: string,
    value: string,
    threshold: string,
    impact: 'HIGH'|'MEDIUM'|'LOW',
    note: string
  }, ...],
  dominantSignals: string[],
  version: 'decision-engine-v1'
}
```

**Triggers:**
- Overall Risk Score
- P95 Loss Ratio
- Tail Risk Contribution
- Weather Volatility Score
- Dominant Layers

---

#### 11. `buildRecommendations(resultsState)`
**Mục đích:** Wrapper function tính toán tất cả recommendations  
**Output:**
```javascript
{
  insurance: {...},         // Insurance recommendation
  timing: {...},            // Shipping window
  providers: [...],         // Provider fit ranking
  trace: {...}             // Decision trace
}
```

**Trả về:** Complete recommendations object

---

### Helper Functions (Internal)

#### `getEmptyState()`
**Mục đích:** Trả về empty state khi không có data  
**Trả về:** Empty ResultsOS state object

---

#### `getDefaultLayers()`
**Mục đích:** Trả về default layers  
**Trả về:** Array of 6 default layers (score = 0)

---

#### `clampScore(score)`
**Mục đích:** Clamp score về range 0-100  
**Trả về:** Number (0-100)

---

#### `extractTradeLane(route)`
**Mục đích:** Extract trade lane từ route string  
**Trả về:** Trade lane string

---

#### `mapLayerToCategory(layerName)`
**Mục đích:** Map layer name sang category  
**Trả về:** 'Operational' | 'Environmental' | 'Geopolitical' | 'Financial'

---

#### `generateHistogramData(p95, p99)`
**Mục đích:** Generate histogram data từ P95/P99  
**Trả về:** `{bins: [], counts: [], currency: 'USD'}`

---

#### `generateLossCurveData(p95, p99)`
**Mục đích:** Generate loss curve points từ P95/P99  
**Trả về:** Array of `{loss: number, probability: number}`

---

#### `formatCurrency(value)`
**Mục đích:** Format currency value  
**Trả về:** Formatted currency string (USD)

---

### Default State Export

#### `resultsState`
**Mục đích:** Default state object khi không có summary data  
**Structure:**
```javascript
{
  meta: {...},              // System metadata
  methodology: {...},       // Methodology documentation
  shipment: {...},          // Default shipment
  globalRisk: 68,          // Default risk score
  layers: [...],           // Default layers
  factors: [...],          // Default factors
  loss: {...},             // Default loss metrics
  charts: {...},           // Default chart data
  decision: {...},         // Default decision context
  scenarios: {...},         // Default scenarios
  timeline: [...],         // Default timeline
  traceability: {...}      // Traceability documentation
}
```

---

## 🎨 Components - Các Component UI

### Component Pattern
Tất cả components đều follow pattern:
```javascript
class ComponentName {
  constructor() { ... }
  mount(el, data) { ... }
  update(data) { ... }
  destroy() { ... }
}
```

---

### 1. ShipmentHeader
**File:** `components/ShipmentHeader.js`  
**Mục đích:** Hiển thị thông tin shipment  
**Input:** `activeState.shipment`  
**Slot:** `slot-shipment`

---

### 2. GlobalGauge
**File:** `components/GlobalGauge.js`  
**Mục đích:** Hiển thị global risk gauge  
**Input:** `activeState.globalRisk` (number)  
**Slot:** `slot-global-risk`

---

### 3. MiniGauges
**File:** `components/MiniGauges.js`  
**Mục đích:** Hiển thị mini gauges cho các layers  
**Input:** Array of `{label: string, value: number}`  
**Slot:** `slot-mini-gauges`

---

### 4. RadarChart
**File:** `components/RadarChart.js`  
**Mục đích:** Biểu đồ radar Chart.js  
**Input:** `{labels: [], values: []}`  
**Slot:** `slot-radar`  
**Dependencies:** Chart.js

---

### 5. LayersTable
**File:** `components/LayersTable.js`  
**Mục đích:** Bảng hiển thị risk layers  
**Input:** `activeState.layers` (array)  
**Slot:** `slot-layers-table`

---

### 6. RiskFactorsTable
**File:** `components/RiskFactorsTable.js`  
**Mục đích:** Bảng hiển thị risk factors  
**Input:** `activeState.factors` (array)  
**Slot:** `slot-factors-table`

---

### 7. FinancialHistogram
**File:** `components/FinancialHistogram.js`  
**Mục đích:** Histogram phân phối tài chính  
**Input:** `activeState.charts.financialHistogram`  
**Slot:** `slot-financial-histogram`  
**Dependencies:** Chart.js

---

### 8. LossCurve
**File:** `components/LossCurve.js`  
**Mục đích:** Đường cong tổn thất  
**Input:** `activeState.charts.lossCurve`  
**Slot:** `slot-loss-curve`  
**Dependencies:** Chart.js

---

### 9. AINarrativePanel
**File:** `components/AINarrativePanel.js`  
**Mục đích:** Panel narrative AI với executive summary  
**Input:**
```javascript
{
  summary: {overallRiskScore, riskLevel},
  layers: [...],
  factors: [...],
  loss: {...}
}
```
**Slots:** `slot-ai-insight`, `slot-ai-narrative`  
**Features:**
- Executive summary (always visible)
- Collapsible detailed sections
- Vietnamese localization

---

### 10. DecisionSignals
**File:** `components/DecisionSignals.js`  
**Mục đích:** Hiển thị tín hiệu quyết định  
**Input:** `activeState.decision.payloadForDecisionSignals`  
**Slot:** `slot-decision-signals`

---

### 11. MiniStrategyScenarios
**File:** `components/MiniStrategyScenarios.js`  
**Mục đích:** Hiển thị kịch bản chiến lược  
**Input:** `activeState.scenarios.payloadForMiniScenarios`  
**Slot:** `slot-strategy-scenarios`

---

### 12. TimelineTrack
**File:** `components/TimelineTrack.js`  
**Mục đích:** Hiển thị timeline rủi ro  
**Input:** `activeState.payloadForTimelineTrack`  
**Slot:** `slot-timeline`

---

### 13. InsuranceDecisionPanel ⭐ NEW
**File:** `components/InsuranceDecisionPanel.js`  
**Mục đích:** Panel khuyến nghị bảo hiểm & thời gian vận chuyển  
**Input:** `activeState.recommendations`  
**Slot:** `insurance-decision-panel`  
**Sections:**
1. **Insurance Decision**: Badge (BUY/OPTIONAL/SKIP), package, checklist, reasons
2. **Safe Shipping Window**: Recommended window, avoid window, risk reduction
3. **Provider Fit Ranking**: Top 2-3 providers với fit bars
4. **Traceability**: Collapsible decision trace

**Features:**
- Enterprise card layout
- Vietnamese localization
- Responsive design
- Empty state handling

---

### 14. RiskScoreOrb (Decision Hub)
**File:** `components/RiskScoreOrb.js`  
**Mục đích:** Orb hiển thị điểm rủi ro tổng thể (center)  
**Input:** `{overallRiskScore: number, riskLevel: string}`  
**Slot:** `slot-risk-score-orb`

---

### 15. RiskRingCard (Decision Hub)
**File:** `components/RiskRingCard.js`  
**Mục đích:** Card vòng tròn cho top risk layers (orbit)  
**Input:** `{riskName: string, riskValue: number, iconName: string}`  
**Slots:** `slot-risk-ring-card-0` đến `slot-risk-ring-card-5`  
**Logic:** Mount top 6 layers sorted by score

---

### 16. RiskRadar (Decision Hub)
**File:** `components/RiskRadar.js`  
**Mục đích:** Radar chart cho risk layers  
**Input:** `{labels: [], values: []}`  
**Slot:** `slot-risk-radar`

---

## 🔄 Luồng Dữ Liệu

### 1. Khởi Tạo
```
Page Load
  ↓
DOM Ready
  ↓
initResultsOS()
  ↓
createResultsOSStructure()
```

### 2. Load State
```
loadSummaryState()
  ↓
sessionStorage.getItem('RISKCAST_SUMMARY_STATE')
  ↓ (nếu không có)
localStorage.getItem('RISKCAST_SUMMARY_STATE')
  ↓
summaryState hoặc null
```

### 3. Transform State
```
summaryState
  ↓
transformSummaryToResults()
  ↓
validateState()
  ↓
getRiskLayers()
  ↓
getGlobalRiskScore()
  ↓
activeState (ResultsOS format)
```

### 4. Compute Recommendations
```
activeState
  ↓
buildRecommendations()
  ↓
  ├─ computeInsuranceRecommendation()
  ├─ computeSafeShippingWindow()
  ├─ computeProviderFit()
  └─ computeDecisionTrace()
  ↓
recommendations (frozen)
  ↓
activeState.recommendations = recommendations
```

### 5. Freeze State
```
activeState
  ↓
Object.freeze(activeState)
  ↓
Freeze nested objects
  ↓
Immutable state ready
```

### 6. Mount Components
```
For each component:
  mountComponent(slotId, ComponentClass, data)
    ↓
  Find DOM element
    ↓
  Create component instance
    ↓
  instance.mount(element, data)
    ↓
  Store in componentInstances
```

---

## 📚 API & Functions Reference

### State Management API

#### `loadSummaryState()`
Load state từ storage.

#### `validateState(summaryState)`
Validate state structure.

#### `transformSummaryToResults(summaryState)`
Transform summary → ResultsOS format.

#### `buildRecommendations(resultsState)`
Tính toán tất cả recommendations.

---

### Component Mounting API

#### `mountComponent(slotId, ComponentClass, data, options)`
Mount component vào DOM.

#### `renderTraceability(slotId, state)`
Render traceability block.

---

### Utility Functions

#### `deriveRiskLevel(globalRisk, fallbackLevel)`
Chuẩn hóa risk level.

#### `escapeHtml(str)`
Escape HTML để ngăn XSS.

#### `createResultsOSStructure()`
Tạo DOM structure.

#### `initCollapsibleSections()`
Khởi tạo collapsible sections.

---

### Debug API

#### `window.__RESULTSOS__`
Exposed state cho debugging:
```javascript
{
  state: activeState,           // Frozen state
  summaryState: summaryState,   // Original summary
  components: componentInstances, // Component instances
  recommendations: recommendations // Frozen recommendations
}
```

---

## 🎯 Tóm Tắt Chức Năng Chính

### 1. State Management
- ✅ Load state từ storage (sessionStorage/localStorage)
- ✅ Validate state structure
- ✅ Transform summary → ResultsOS format
- ✅ Compute recommendations (insurance, timing, providers, trace)
- ✅ Freeze state để immutable

### 2. Component Mounting
- ✅ Mount 16 components vào DOM
- ✅ Error handling graceful
- ✅ Empty state handling
- ✅ Component lifecycle management

### 3. Decision Intelligence
- ✅ Insurance recommendations với rules-based logic
- ✅ Safe shipping window recommendations
- ✅ Provider fit ranking với weighted scoring
- ✅ Decision traceability với triggers

### 4. Visualization
- ✅ Charts (Radar, Histogram, Loss Curve) với Chart.js
- ✅ Tables (Layers, Factors)
- ✅ Gauges (Global, Mini)
- ✅ Timeline track

### 5. UI/UX
- ✅ Collapsible sections
- ✅ Responsive design
- ✅ Vietnamese localization
- ✅ Empty state messages
- ✅ Loading states

### 6. Traceability & Audit
- ✅ Methodology documentation
- ✅ Decision basis
- ✅ Decision engine trace
- ✅ References
- ✅ Frozen state cho audit trail

---

## 🔍 Debugging & Development

### Debug Flag
```javascript
const DEBUG = true; // Set false cho production
```

### Console Logging
- **Always logged**: Errors, initialization metadata
- **DEBUG only**: Verbose component mounting logs

### Window Exposure
```javascript
window.__RESULTSOS__.state          // Access state
window.__RESULTSOS__.recommendations // Access recommendations
window.__RESULTSOS__.components      // Access component instances
```

---

## 📝 Notes

### Immutability
Tất cả state sau khi tính toán đều được freeze để:
- Đảm bảo tính audit trail
- Ngăn accidental mutation
- Hỗ trợ academic/enterprise review

### Error Handling
- Graceful degradation khi thiếu data
- Empty state UI cho components
- Fallback về default state nếu transform fail

### Performance
- Components chỉ mount khi DOM ready
- Chart.js check trước khi mount chart components
- Lazy loading structure (chỉ tạo khi cần)

---

**Tài liệu này cung cấp overview đầy đủ về tất cả chức năng JavaScript trong trang ResultsOS.**
