# Danh Sách Tất Cả File JavaScript Trong Trang Results

## 📋 Tổng Quan

Trang Results sử dụng kiến trúc component-based với các file JavaScript được tổ chức theo chức năng. Tất cả HTML và CSS được tạo động bởi JavaScript.

---

## 🎯 FILE CHÍNH (Core Files)

### 1. **`main.js`** - File Điều Phối Chính
**Đường dẫn:** `app/static/js/main.js`

**Chức năng:**
- **Điều phối toàn bộ trang Results**: File trung tâm quản lý việc mount tất cả components
- **Tạo HTML structure động**: Hàm `createResultsOSStructure()` tạo toàn bộ HTML structure (Decision Hub, collapsible sections)
- **Inject CSS styles**: Hàm `injectResultsOSStyles()` inject CSS vào document head
- **Quản lý component instances**: Lưu trữ và quản lý lifecycle của tất cả component instances
- **Mount components**: Hàm `mountComponent()` mount từng component vào DOM slots
- **Xử lý data flow**: Load `summaryState` từ storage, transform sang `resultsState`, và truyền data cho components
- **Error handling**: Xử lý lỗi khi mount components, validate data
- **Collapsible sections**: Quản lý toggle icons cho các collapsible sections
- **Traceability block**: Render block truy vết phương pháp và kiểm toán

**Các hàm chính:**
- `initResultsOS()` - Khởi tạo toàn bộ ResultsOS
- `createResultsOSStructure()` - Tạo HTML structure
- `injectResultsOSStyles()` - Inject CSS styles
- `mountComponent()` - Mount component vào DOM
- `initCollapsibleSections()` - Khởi tạo collapsible sections
- `renderTraceability()` - Render traceability block

---

### 2. **`state.js`** - Quản Lý State & Data
**Đường dẫn:** `app/static/js/state.js`

**Chức năng:**
- **Single Source of Truth**: File trung tâm chứa tất cả data cho ResultsOS
- **Load state từ storage**: Load `summaryState` từ `sessionStorage` hoặc `localStorage`
- **Transform data**: Transform `summaryState` (từ Summary page) sang `resultsState` (format cho ResultsOS)
- **Default state**: Cung cấp `resultsState` mặc định khi không có data từ Summary
- **Validate state**: Validate structure của state data
- **Risk calculations**: Tính toán risk layers, global risk score, factors từ input data
- **Data mapping**: Map risk inputs (portCongestion, weatherVolatility, etc.) sang risk layers với weights

**Các hàm chính:**
- `loadSummaryState()` - Load state từ storage
- `validateState()` - Validate state structure
- `transformSummaryToResults()` - Transform summary state sang results format
- `getRiskLayers()` - Lấy risk layers từ summary state
- `getGlobalRiskScore()` - Tính global risk score
- `getRiskFactors()` - Lấy risk factors từ summary state

**Export:**
- `resultsState` - Default state object
- `loadSummaryState()` - Function load state
- `transformSummaryToResults()` - Function transform data
- `validateState()` - Function validate state

---

## 🎨 COMPONENTS - Decision Hub (Primary View)

### 3. **`RiskScoreOrb.js`** - Component Hiển Thị Risk Score Chính
**Đường dẫn:** `app/static/js/components/RiskScoreOrb.js`

**Chức năng:**
- **Hiển thị overall risk score**: Component quan trọng nhất, hiển thị risk score tổng thể (0-100)
- **Visual hierarchy**: Thiết kế để dominate visual hierarchy, số lớn ở giữa, label bên dưới
- **Dynamic coloring**: Màu sắc thay đổi theo risk level (<40 green, 40-65 yellow, >65 red)
- **Pulse animation**: Animation pulse mỗi 4-6 giây
- **Neon glow effect**: Subtle neon glow effect theo màu risk level
- **Risk level label**: Hiển thị "THẤP", "TRUNG BÌNH", "CAO" dưới số

**Methods:**
- `mount(el, data)` - Mount component vào DOM element
- `update(data)` - Update component với data mới
- `destroy()` - Cleanup component
- `_createStructure()` - Tạo HTML structure
- `_startPulseAnimation()` - Bắt đầu pulse animation
- `_determineRiskLevel()` - Xác định risk level từ score

**Input data:**
- `overallRiskScore` (number, 0-100) - Risk score tổng thể
- `riskLevel` (string, optional) - 'LOW', 'MEDIUM', 'HIGH'

---

### 4. **`RiskRingCard.js`** - Component Hiển Thị Risk Drivers
**Đường dẫn:** `app/static/js/components/RiskRingCard.js`

**Chức năng:**
- **Hiển thị individual risk drivers**: Hiển thị từng risk driver dưới dạng card compact
- **Orbit layout**: Thiết kế để đặt xung quanh RiskScoreOrb trong radial layout
- **Large percentage value**: Số phần trăm lớn, dễ đọc
- **Progress bar**: Progress bar ngang hiển thị risk value
- **Icon support**: Hỗ trợ icon cho các risk types (weather, congestion, carrier, market, insurance, esg, delay)
- **Color coding**: Màu sắc theo risk level (green/yellow/red)
- **Subtle glow**: Glow effect nhẹ theo màu risk

**Methods:**
- `mount(el, data)` - Mount component vào DOM element
- `update(data)` - Update component với data mới
- `destroy()` - Cleanup component
- `_createStructure()` - Tạo HTML structure
- `_getIconSVG()` - Lấy SVG icon theo tên
- `_getRiskLevelCategory()` - Xác định risk level category

**Input data:**
- `riskName` (string) - Tên risk driver
- `riskValue` (number, 0-100) - Risk value
- `iconName` (string, optional) - Tên icon

---

### 5. **`RiskRadar.js`** - Component Radar Chart
**Đường dẫn:** `app/static/js/components/RiskRadar.js`

**Chức năng:**
- **Radar chart visualization**: Sử dụng Chart.js để render radar chart
- **Risk layers summary**: Hiển thị tổng hợp các risk layers và scores
- **Dark theme**: Styled với dark background, soft grid lines
- **Yellow primary color**: Stroke màu vàng (#ffcc00), fill semi-transparent
- **Error handling**: Xử lý khi Chart.js không load, data không hợp lệ
- **Empty state**: Hiển thị message khi không có data
- **Responsive**: Tự động resize theo container

**Methods:**
- `mount(el, data)` - Mount component vào DOM element
- `update(data)` - Update chart với data mới
- `destroy()` - Cleanup chart instance
- `_getChartLib()` - Kiểm tra Chart.js availability
- `_initChart()` - Khởi tạo Chart.js instance
- `_normalizeValues()` - Normalize values về 0-100
- `_renderError()` - Render error message
- `_renderEmptyState()` - Render empty state

**Input data:**
- `labels` (Array<string>) - Mảng tên risk layers
- `values` (Array<number>) - Mảng risk scores (0-100)

**Dependencies:**
- Chart.js (CDN)

---

### 6. **`AINarrativePanel.js`** - Component AI Insight Block
**Đường dẫn:** `app/static/js/components/AINarrativePanel.js`

**Chức năng:**
- **AI narrative panel**: Panel giải thích risk intelligence bằng ngôn ngữ rõ ràng
- **Executive summary**: Tóm tắt điều hành về risk assessment
- **Loss insights**: Phân tích loss metrics (P95, P99, tail contribution)
- **Dominant layers**: Xác định và giải thích các risk layers chi phối
- **Actionable insights**: Đưa ra insights có thể hành động
- **Enterprise-ready**: Ngôn ngữ phù hợp cho enterprise và academic review
- **Vietnamese localization**: Tất cả text đã được dịch sang tiếng Việt

**Methods:**
- `mount(el, data)` - Mount component vào DOM element
- `update(data)` - Update component với data mới
- `destroy()` - Cleanup component
- `_createStructure()` - Tạo HTML structure
- `_render()` - Render nội dung
- `_renderExecutiveSummary()` - Render executive summary
- `_renderLossInsight()` - Render loss insights
- `_renderDominantLayers()` - Render dominant layers

**Input data:**
- `summary.overallRiskScore` (number) - Overall risk score
- `summary.riskLevel` (string) - Risk level
- `layers` (Array) - Risk layers array
- `factors` (Array) - Risk factors array
- `loss` (Object) - Loss metrics (p95, p99, tailContribution)

---

## 📊 COMPONENTS - Supporting Evidence (Collapsible Sections)

### 7. **`ShipmentHeader.js`** - Component Hiển Thị Thông Tin Lô Hàng
**Đường dẫn:** `app/static/js/components/ShipmentHeader.js`

**Chức năng:**
- **Shipment metadata**: Hiển thị thông tin metadata của lô hàng
- **Glassmorphic card**: Thiết kế glassmorphic với backdrop blur
- **Key information**: ID, route, incoterms, cargo type, value, ETA
- **Formatted display**: Format currency, dates, routes

**Input data:**
- `id` (string) - Shipment ID
- `route` (string) - Route string
- `incoterms` (string) - Incoterms code
- `cargoType` (string) - Cargo type
- `cargoValue` (number) - Cargo value in USD
- `eta` (string) - Estimated time of arrival

---

### 8. **`DecisionSignals.js`** - Component Tín Hiệu Quyết Định
**Đường dẫn:** `app/static/js/components/DecisionSignals.js`

**Chức năng:**
- **Executive decision signals**: Convert risk intelligence thành actionable decisions
- **Decision cards**: Hiển thị các decision signals dưới dạng cards
- **Risk level indicators**: Visual indicators cho risk levels
- **Actionable recommendations**: Đưa ra recommendations có thể hành động
- **Enterprise leadership focus**: Tập trung vào nhu cầu của leadership

**Input data:**
- `decision.riskLevel` (string) - Risk level
- `decision.overallRiskScore` (number) - Overall risk score
- `decision.dominantLayers` (Array) - Top risk layers

---

### 9. **`MiniStrategyScenarios.js`** - Component Kịch Bản Chiến Lược
**Đường dẫn:** `app/static/js/components/MiniStrategyScenarios.js`

**Chức năng:**
- **Strategy scenarios**: Hiển thị các kịch bản chiến lược
- **Scenario cards**: Cards cho từng scenario
- **Risk mitigation strategies**: Các chiến lược giảm thiểu rủi ro

---

### 10. **`FinancialHistogram.js`** - Component Histogram Tài Chính
**Đường dẫn:** `app/static/js/components/FinancialHistogram.js`

**Chức năng:**
- **Financial histogram**: Histogram chart hiển thị phân phối tài chính
- **Loss distribution**: Phân phối loss values
- **Chart.js integration**: Sử dụng Chart.js để render

---

### 11. **`LossCurve.js`** - Component Đường Cong Tổn Thất
**Đường dẫn:** `app/static/js/components/LossCurve.js`

**Chức năng:**
- **Loss curve**: Line chart hiển thị đường cong tổn thất
- **P95/P99 markers**: Đánh dấu P95 và P99 trên curve
- **Tail risk visualization**: Visualization cho tail risk

---

### 12. **`LayersTable.js`** - Component Bảng Risk Layers
**Đường dẫn:** `app/static/js/components/LayersTable.js`

**Chức năng:**
- **Risk layers table**: Bảng hiển thị tất cả risk layers
- **Sortable columns**: Có thể sort theo columns
- **Score display**: Hiển thị scores, weights, notes
- **Color coding**: Màu sắc theo risk level

---

### 13. **`RiskFactorsTable.js`** - Component Bảng Risk Factors
**Đường dẫn:** `app/static/js/components/RiskFactorsTable.js`

**Chức năng:**
- **Risk factors table**: Bảng hiển thị risk factors
- **Impact & probability**: Hiển thị impact và probability
- **Composite scores**: Hiển thị composite scores

---

### 14. **`TimelineTrack.js`** - Component Dòng Thời Gian
**Đường dẫn:** `app/static/js/components/TimelineTrack.js`

**Chức năng:**
- **Risk timeline**: Timeline hiển thị risk events theo thời gian
- **Event markers**: Đánh dấu các events quan trọng
- **Risk evolution**: Hiển thị sự tiến hóa của risk theo thời gian

---

## 🔄 COMPONENTS - Legacy (Trong Collapsible Section)

### 15. **`GlobalGauge.js`** - Component Gauge Cũ
**Đường dẫn:** `app/static/js/components/GlobalGauge.js`

**Chức năng:**
- **Circular SVG gauge**: Gauge hình tròn hiển thị global risk score
- **Color-coded zones**: Zones màu xanh, vàng, đỏ
- **Smooth animations**: Animation mượt khi update score
- **Legacy component**: Component cũ, được giữ lại trong collapsible section

---

### 16. **`MiniGauges.js`** - Component Mini Gauges
**Đường dẫn:** `app/static/js/components/MiniGauges.js`

**Chức năng:**
- **Multiple mini gauges**: Nhiều gauge nhỏ cho các risk layers
- **Grid layout**: Layout dạng grid
- **Legacy component**: Component cũ

---

### 17. **`RadarChart.js`** - Component Radar Chart Cũ
**Đường dẫn:** `app/static/js/components/RadarChart.js`

**Chức năng:**
- **Legacy radar chart**: Radar chart cũ (khác với RiskRadar.js mới)
- **Chart.js integration**: Sử dụng Chart.js
- **Legacy component**: Component cũ

---

## 📦 DEPENDENCIES

### External Libraries (CDN):
- **Chart.js v4.4.1**: Sử dụng bởi `RiskRadar.js`, `FinancialHistogram.js`, `LossCurve.js`, `RadarChart.js`
- **Chart.js Plugin Annotation v3.0.1**: Plugin cho Chart.js annotations

---

## 🔄 DATA FLOW

```
Summary Page (sessionStorage/localStorage)
    ↓
state.js (loadSummaryState, transformSummaryToResults)
    ↓
main.js (initResultsOS, mountComponent)
    ↓
Components (mount, update, destroy)
    ↓
DOM (rendered UI)
```

---

## 📝 NOTES

1. **Tất cả HTML được tạo bởi JavaScript**: File `results.html` chỉ có structure tối thiểu, tất cả content được tạo bởi `createResultsOSStructure()` trong `main.js`

2. **Tất cả CSS được inject bởi JavaScript**: CSS được inject bởi `injectResultsOSStyles()` trong `main.js` và các component tự inject styles của chúng

3. **Component Architecture**: Tất cả components đều follow pattern:
   - `constructor()` - Khởi tạo
   - `mount(el, data)` - Mount vào DOM
   - `update(data)` - Update với data mới
   - `destroy()` - Cleanup

4. **State Management**: State được quản lý tập trung trong `state.js`, `main.js` chỉ điều phối việc mount components

5. **Error Handling**: Tất cả components đều có error handling và fallback UI

6. **Localization**: Tất cả user-facing text đã được dịch sang tiếng Việt

---

## 🎯 SUMMARY

**Tổng số file JS liên quan đến Results:**
- **1 file core**: `main.js`, `state.js`
- **14 component files**: Decision Hub (3) + Supporting Evidence (8) + Legacy (3)
- **Total: 16 files**

**Chức năng chính:**
- **main.js**: Điều phối, tạo HTML/CSS, mount components
- **state.js**: Quản lý state, transform data
- **Components**: Render UI, xử lý data, inject styles
