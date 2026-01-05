# BÁO CÁO CHI TIẾT TRANG SUMMARY - RISKCAST v16

## 1. TỔNG QUAN

Trang **Summary** (Summary v400/v550 Ultra) là trang tổng hợp và xác nhận thông tin lô hàng trước khi tiến hành phân tích rủi ro. Đây là trang trung gian giữa trang Input (nhập liệu) và trang Results (kết quả phân tích).

**URL Route:** `/summary`  
**Template:** `app/templates/summary/summary_v400.html`  
**Controller Backend:** `app/main.py` (route `/summary`)  
**Controller Frontend:** `app/static/js/summary_v400/v400_controller.js`

---

## 2. KIẾN TRÚC TỔNG THỂ

### 2.1. Cấu trúc Module JavaScript

Trang Summary sử dụng kiến trúc module pattern với các component chính:

```
summary_v400/
├── v400_controller.js      # Điều phối chính, khởi tạo và quản lý lifecycle
├── v400_state.js           # Quản lý state (load/save từ localStorage)
├── v400_renderer.js        # Render UI (panels, banner, tiles)
├── v400_validator.js       # Validation engine (kiểm tra dữ liệu)
├── v400_inline_editor.js   # Editor bubble (chỉnh sửa inline)
├── v400_ai_advisor.js      # AI advisor panel (gợi ý và cảnh báo)
└── v400_risk_row.js        # Risk modules row (toggle các module risk)
```

### 2.2. State Management

**Key:** `RISKCAST_STATE` trong `localStorage`

**Cấu trúc State:**
```javascript
{
  shipment: {
    trade_route: {
      pol: string,              // Port of Loading
      pod: string,              // Port of Discharge
      mode: string,             // SEA/AIR/ROAD/RAIL/MULTIMODAL
      service_route: string,
      carrier: string,
      container_type: string,   // 20GP, 40GP, 40HC, etc.
      etd: string,              // Estimated Time of Departure (date)
      eta: string,              // Estimated Time of Arrival (date)
      transit_time_days: number,
      incoterm: string,         // EXW, FOB, CIF, DDP, etc.
      incoterm_location: string,
      priority: string          // STANDARD, EXPRESS, URGENT
    },
    cargo_packing: {
      cargo_type: string,
      cargo_category: string,
      hs_code: string,
      hs_chapter: string,
      packing_type: string,
      packages: number,
      gross_weight_kg: number,
      net_weight_kg: number,
      volume_cbm: number,
      stackability: boolean,
      temp_control_required: boolean,
      is_dg: boolean            // Dangerous Goods
    },
    seller: {
      name: string,
      company: string,
      email: string,
      phone: string,
      country: string,
      city: string,
      address: string,
      tax_id: string
    },
    buyer: {
      name: string,
      company: string,
      email: string,
      phone: string,
      country: string,
      city: string,
      address: string,
      tax_id: string
    }
  },
  riskModules: {
    esg: boolean,
    weather: boolean,
    congestion: boolean,
    carrier_perf: boolean,
    market: boolean,
    insurance: boolean
  }
}
```

---

## 3. GIAO DIỆN NGƯỜI DÙNG

### 3.1. Layout Chính

```
┌─────────────────────────────────────────────────────────┐
│  HEADER BAR (Top)                                       │
│  [Logo] [Back] [Save Draft] [Confirm & Analyze]        │
├─────────────────────────────────────────────────────────┤
│  MEGA SUMMARY TILE (5 columns banner)                   │
│  [Route] [Mode] [Container] [Transit/ETD→ETA] [Weight] │
├─────────────────────────────────────────────────────────┤
│  MAIN GRID (2x2 Matrix + Sidebar)                       │
│  ┌───────────────┬───────────────┐ ┌─────────────┐     │
│  │ Panel 01:     │ Panel 02:     │ │ AI ADVISOR  │     │
│  │ Trade & Route │ Cargo &       │ │ PANEL       │     │
│  │               │ Packing       │ │             │     │
│  ├───────────────┼───────────────┤ │ - Critical  │     │
│  │ Panel 03:     │ Panel 04:     │ │ - Warnings  │     │
│  │ Seller        │ Buyer         │ │ - Suggestions│     │
│  │               │               │ │             │     │
│  └───────────────┴───────────────┘ └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│  RISK MODULES ROW                                       │
│  [ESG] [Weather] [Congestion] [Carrier] [Market] [Ins] │
├─────────────────────────────────────────────────────────┤
│  ACTION STRIP (Bottom)                                  │
│  [Completeness Bar] [Error Chips] [Save] [Confirm]     │
└─────────────────────────────────────────────────────────┘
```

### 3.2. Các Component Chính

#### 3.2.1. Mega Summary Tile (Banner)
- **Vị trí:** Phía trên cùng, sau header
- **Mục đích:** Hiển thị thông tin tóm tắt quan trọng nhất
- **5 tiles:**
  1. Tuyến đường (POL → POD)
  2. Phương thức vận chuyển (Mode)
  3. Loại container
  4. Vận chuyển / ETD→ETA
  5. Trọng lượng / Thể tích
- **Tương tác:** Click vào tile → mở inline editor

#### 3.2.2. Panel 01: Trade & Route
- **Fields:**
  - POL (Port of Loading) - Required
  - POD (Port of Discharge) - Required
  - Mode (SEA/AIR/ROAD/RAIL/MULTIMODAL) - Required
  - Service Route ID
  - Carrier
  - Container Type - Required
  - ETD (date) - Required
  - ETA (date, auto-calculated, disabled)
  - Transit Time (days) - Required
  - Incoterm
  - Incoterm Location
  - Priority (STANDARD/EXPRESS/URGENT)

#### 3.2.3. Panel 02: Cargo & Packing
- **Fields:**
  - Loại hàng (Cargo Type) - Required
  - Nhóm hàng (Cargo Category)
  - HS Code - Required
  - Chương HS (HS Chapter, auto-extracted)
  - Đóng gói (Packing Type)
  - Số kiện (Packages) - Required
  - Trọng lượng tổng (Gross Weight kg) - Required
  - Trọng lượng tịnh (Net Weight kg)
  - Thể tích (Volume CBM) - Required
  - Có thể xếp chồng (Stackability) - Checkbox
  - Yêu cầu kiểm soát nhiệt độ (Temp Control) - Checkbox
  - Hàng nguy hiểm (Dangerous Goods) - Checkbox

#### 3.2.4. Panel 03: Seller (Người bán)
- **Fields:**
  - Tên liên hệ (Name)
  - Tên công ty (Company) - Required
  - Email - Required
  - Phone - Required
  - Country - Required
  - City
  - Address
  - Tax ID / VAT

#### 3.2.5. Panel 04: Buyer (Người mua)
- **Fields:** Tương tự Seller
  - Tên liên hệ (Name)
  - Tên công ty (Company) - Required
  - Email - Required
  - Phone - Required
  - Country - Required
  - City
  - Address
  - Tax ID / VAT

#### 3.2.6. AI Advisor Panel (Sidebar bên phải)
- **Mục đích:** Hiển thị kết quả validation và gợi ý từ AI
- **3 nhóm:**
  1. **Lỗi nghiêm trọng (Critical)** - Đỏ, cần sửa ngay
  2. **Cảnh báo (Warning)** - Vàng, nên sửa
  3. **Gợi ý (Suggestion)** - Xanh, có thể cải thiện
- **Tương tác:** Click vào item → highlight field liên quan → mở editor

#### 3.2.7. Risk Modules Row
- **6 modules:**
  1. ESG Risk
  2. Weather & Climate
  3. Port Congestion
  4. Carrier Performance
  5. Market Condition
  6. Insurance Optimization
- **Tương tác:** Toggle ON/OFF bằng switch

#### 3.2.8. Action Strip (Footer)
- **Completeness Bar:** Thanh tiến trình % hoàn thiện
- **Error Chips:**
  - Lỗi nghiêm trọng (Critical count)
  - Cảnh báo (Warning count)
- **Buttons:**
  - Lưu bản nháp (Save Draft)
  - Xác nhận & Phân tích (Confirm & Analyze)

---

## 4. CHỨC NĂNG CHI TIẾT

### 4.1. Khởi tạo (Initialization)

**Flow khởi tạo:**
1. Load state từ `localStorage` (key: `RISKCAST_STATE`)
2. Nếu không có state → tạo state rỗng (fallback)
3. Init V400InlineEditor (editor bubble)
4. Chạy validation lần đầu
5. Render tất cả components:
   - Render Banner (Mega Summary)
   - Render 4 Panels (Trade, Cargo, Seller, Buyer)
   - Render AI Advisor
   - Render Risk Modules Row
6. Attach event handlers (buttons, field clicks)
7. Update completeness bar và error chips
8. Show action strip

**Code location:** `v400_controller.js` → `init()`

### 4.2. State Management

#### 4.2.1. Load State
- Đọc từ `localStorage.getItem('RISKCAST_STATE')`
- Parse JSON
- Transform format nếu cần (backward compatibility)
- Nếu không có → return default empty state

#### 4.2.2. Save State
- Lưu vào `localStorage.setItem('RISKCAST_STATE', JSON.stringify(state))`
- Trigger sau mỗi edit hoặc khi click "Save Draft"

**Code location:** `v400_state.js`

### 4.3. Rendering

#### 4.3.1. Banner Rendering
- Render 5 tiles trong Mega Summary Grid
- Format dữ liệu:
  - Route: `POL → POD`
  - Transit/Dates: `ETD → ETA (transit_time_days days)`
  - Weight/Volume: `weight kg / volume CBM`
- Highlight empty fields (màu xám)

#### 4.3.2. Panel Rendering
- Mỗi panel render dưới dạng field tiles
- Mỗi field tile có:
  - Label
  - Value (hoặc placeholder "Not set")
  - Validation indicator (nếu có lỗi/cảnh báo)
- Click vào tile → mở inline editor

**Code location:** `v400_renderer.js`

### 4.4. Inline Editor (Editor Bubble)

#### 4.4.1. Mở Editor
- Click vào field tile/banner tile/mega tile
- Editor bubble xuất hiện gần vị trí click
- Hiển thị:
  - Header: Field label + Section path
  - Body: Input/Select/Textarea/Checkbox (tùy field type)
  - Footer: Status + Cancel/Save buttons

#### 4.4.2. Loại Input
- **Text:** Input type="text"
- **Number:** Input type="number"
- **Date:** Input type="date"
- **Select:** Dropdown với options
- **Checkbox:** Toggle switch
- **Email:** Input type="email"

#### 4.4.3. Lưu Thay Đổi
- Validate input
- Update state tại path tương ứng
- Save state vào localStorage
- Close editor
- Refresh UI (re-render + re-validate)
- Show toast notification

#### 4.4.4. Đóng Editor
- Click Cancel hoặc Close (×)
- Press Escape key
- Click outside editor bubble

**Code location:** `v400_inline_editor.js`

### 4.5. Validation Engine

#### 4.5.1. Validation Rules (25 Rules)

Hệ thống có **25 validation rules** được phân loại theo severity và scope:

**TRADE & ROUTE RULES (9 rules):**
1. `MODE_PORT_MISMATCH_SEA` (Critical) - Mode SEA nhưng POL/POD là sân bay
2. `MODE_PORT_MISMATCH_AIR` (Critical) - Mode AIR nhưng POL/POD là cảng biển
3. `ETD_IN_PAST` (Critical) - ETD đã qua (trong quá khứ)
4. `ETA_BEFORE_ETD` (Critical) - ETA trước ETD
5. `TRANSIT_DAYS_MISSING` (Warning) - Thiếu transit time khi đã có mode
6. `TRANSIT_DAYS_OUTLIER` (Warning) - Transit time bất thường cho mode (SEA < 3 hoặc > 90 ngày, AIR > 15 ngày)
7. `INCOTERM_LOCATION_REQUIRED` (Warning) - Incoterm cần location nhưng thiếu (FOB, CIF, CFR, DAP, DPU, DDP)
8. `PRIORITY_WITH_WEIRD_MODE` (Suggestion) - Priority EXPRESS nhưng mode là SEA (nên dùng AIR)
9. `SERVICE_ROUTE_SUGGEST` (Suggestion) - Service route trống khi đã có POL/POD

**CARGO & PACKING RULES (8 rules):**
10. `HS_CODE_REQUIRED` (Critical) - HS Code bắt buộc khi có weight/volume
11. `HS_DG_ENFORCED` (Critical) - HS Chapter 28/29 thường là DG nhưng chưa bật flag
12. `HS_REEFER_ENFORCED` (Warning) - Cargo category Perishable nhưng container không phải REEFER
13. `STACKABILITY_CHECK` (Warning) - Cargo category Fragile nhưng stackability = true
14. `WEIGHT_VOLUME_INCONSISTENT` (Warning) - Tỷ lệ weight/volume < 50 hoặc > 1500 kg/CBM
15. `WEIGHT_GREATER_THAN_NET` (Critical) - Net weight > Gross weight
16. `PACKAGES_REQUIRED` (Warning) - Thiếu packages khi có volume
17. `PACKING_TYPE_MISMATCH` (Warning) - Packing type Pallet nhưng không stackable

**SELLER / BUYER RULES (6 rules):**
18. `SELLER_CONTACT_REQUIRED` (Critical) - Seller có company nhưng thiếu email/phone
19. `BUYER_CONTACT_REQUIRED` (Critical) - Buyer có company nhưng thiếu email/phone
20. `COUNTRY_MISMATCH_POL` (Warning) - Seller country không khớp với POL prefix
21. `COUNTRY_MISMATCH_POD` (Warning) - Buyer country không khớp với POD prefix
22. `EMAIL_FORMAT_CHECK` (Warning) - Email format không hợp lệ
23. `PHONE_FORMAT_CHECK` (Warning) - Phone format không hợp lệ

**RISK MODULES RULES (2 rules):**
24. `RISK_MODULES_OFF_FOR_LONG_ROUTE` (Suggestion) - Route dài (>30 ngày) nhưng risk modules đều tắt
25. `INSURANCE_ADVICE_HIGH_RISK` (Suggestion) - Có nhiều risk factors nhưng insurance module tắt

#### 4.5.2. Validation Results
- **Critical:** Lỗi nghiêm trọng, không thể proceed (must fix)
- **Warning:** Cảnh báo, nên sửa (should fix)
- **Suggestion:** Gợi ý cải thiện (nice to have)

#### 4.5.3. Validation Display
- AI Advisor Panel hiển thị danh sách issues theo 3 nhóm (Critical/Warning/Suggestion)
- Field tiles highlight nếu có lỗi (visual indicator)
- Error chips ở action strip hiển thị count (critical count, warning count)
- Validation chạy real-time khi state thay đổi

**Code location:** `v400_validator.js`

### 4.6. AI Advisor

#### 4.6.1. Render Issues
- Group theo type (critical/warning/suggestion)
- Mỗi item có:
  - Icon
  - Message
  - Field path(s) affected
  - Action button (nếu có)

#### 4.6.2. Tương tác
- Click vào item → highlight field(s) liên quan
- Click "Sửa ngay" → mở editor cho field đầu tiên
- Click "Bỏ qua" → dismiss issue (tạm thời)

**Code location:** `v400_ai_advisor.js`

### 4.7. Risk Modules Toggle

- Mỗi module có switch ON/OFF
- Toggle → update `riskModules[key]` trong state
- Save state
- Re-validate (một số rules phụ thuộc vào modules enabled)

**Code location:** `v400_risk_row.js`

### 4.8. Completeness Calculation

- Tính % hoàn thiện dựa trên số fields required đã điền
- Formula: `(filled_required_fields / total_required_fields) * 100`
- Update completeness bar và value display

### 4.9. Action Buttons

#### 4.9.1. Back Button
- Quay lại trang trước (history.back())
- Confirm nếu có thay đổi chưa lưu

#### 4.9.2. Save Draft
- Lưu state hiện tại vào localStorage
- Show toast "Draft saved successfully!"
- Không redirect

#### 4.9.3. Confirm & Analyze
- Validate lại toàn bộ
- Nếu có critical errors → show toast error, không proceed
- Nếu OK → Save state → Redirect (hiện tại bị disable, code comment lại)

**Code location:** `v400_controller.js` → `attachEventHandlers()`

---

## 5. DATA FLOW

### 5.1. Load Flow
```
User visits /summary
  ↓
V400Controller.init()
  ↓
V400State.loadState() → Read localStorage['RISKCAST_STATE']
  ↓
V400Controller.refresh()
  ↓
V400Validator.evaluateAll(state) → Validation results
  ↓
V400Renderer.renderBanner(state, validationResults)
V400Renderer.renderAllPanels(state, validationResults)
V400AIAdvisor.render(validationResults, callback)
V400RiskRow.render(state, callback)
  ↓
Update completeness & error chips
  ↓
UI ready
```

### 5.2. Edit Flow
```
User clicks field tile
  ↓
V400InlineEditor.open(fieldKey, element, state)
  ↓
Render input based on field type
Position bubble near clicked element
Show bubble
  ↓
User edits value
  ↓
User clicks Save
  ↓
V400InlineEditor.validateInput()
  ↓
Update state: V400State.setValueAtPath(state, path, value)
  ↓
V400State.saveState(state) → Write to localStorage
  ↓
Close editor
  ↓
V400Controller.refresh() → Re-render + Re-validate
```

### 5.3. Validation Flow
```
State change detected
  ↓
V400Validator.evaluateAll(state)
  ↓
Run all validation rules
  ↓
Collect issues (critical/warning/suggestion)
  ↓
Update validationResults
  ↓
V400AIAdvisor.render(validationResults)
  ↓
Update error chips (count)
  ↓
Highlight fields with errors
```

---

## 6. FIELD MAP CONFIGURATION

Tất cả fields được định nghĩa trong `V400Renderer.FIELD_MAP` với cấu trúc:

```javascript
'field.key': {
  section: 'trade|cargo|seller|buyer',
  path: 'shipment.trade_route.pol',  // Path trong state
  type: 'text|number|date|select|checkbox|email',
  label: 'Tên hiển thị',
  placeholder: 'Placeholder text',
  options: ['option1', 'option2'],  // Cho select
  disabled: false,                   // Cho date/calculated fields
  required: true|false
}
```

**Ví dụ:**
- `'trade.pol'` → `shipment.trade_route.pol`
- `'cargo.gross_weight_kg'` → `shipment.cargo_packing.gross_weight_kg`
- `'seller.email'` → `shipment.seller.email`

---

## 7. CSS & STYLING

### 7.1. CSS Files Load Order
1. `summary_reset.css` - Reset styles
2. `summary_typography.css` - Typography
3. `summary_layout_v500.css` - Layout
4. `summary_components_v500.css` - Components
5. `summary_editor.css` - Editor styles
6. `summary_theme_visionos.css` - Theme (VisionOS style)
7. `summary_effects.css` - Effects & animations
8. `summary_editor_fix.css` - Editor positioning fixes

### 7.2. Design System
- **Theme:** VisionOS-style (glass morphism, gradients, neon accents)
- **Colors:**
  - Primary: Cyan (#00ffff) → Purple (#7B4DFF) gradient
  - Success: Green (#00ff88)
  - Error: Red
  - Warning: Yellow/Orange
- **Typography:** Inter (body), Space Mono (code)
- **Effects:** Backdrop blur, glass cards, particle background

---

## 8. API & BACKEND INTEGRATION

### 8.1. Backend Route
- **Endpoint:** `GET /summary`
- **Handler:** `app/main.py` → `summary_page()`
- **Response:** HTML template `summary/summary_v400.html`

### 8.2. Data Source
- **Primary:** `localStorage['RISKCAST_STATE']`
- **No direct API calls** trong summary page
- State được lưu từ Input page và được load ở Summary page

### 8.3. Next Step (After Confirm)
- **Current:** Redirect bị disable (code comment)
- **Original intention:** Redirect đến `/results` để phân tích risk

---

## 9. ERROR HANDLING

### 9.1. State Loading Errors
- Nếu parse JSON fail → fallback to empty state
- Console warning logged

### 9.2. Editor Errors
- Validation errors hiển thị trong editor bubble status
- Invalid input → disable Save button

### 9.3. Render Errors
- Missing elements → console error, graceful degradation
- Missing state paths → display "Not set" hoặc empty

---

## 10. BROWSER COMPATIBILITY

### 10.1. Required Features
- `localStorage` API
- `JSON.parse/stringify`
- ES6+ (arrow functions, const/let, template literals)
- CSS Grid, Flexbox
- Backdrop-filter (cho glass effect)

### 10.2. Browser Support
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (iOS 9+)
- IE11: Not supported

---

## 11. PERFORMANCE CONSIDERATIONS

### 11.1. Optimizations
- **Debouncing:** Input events debounced (250ms)
- **Re-render:** Chỉ re-render khi state thay đổi
- **Event delegation:** Sử dụng event delegation cho dynamic elements
- **Lazy loading:** Modules load khi cần

### 11.2. State Size
- State thường < 10KB (JSON)
- localStorage limit: ~5-10MB (đủ cho nhiều shipments)

---

## 12. TESTING CHECKLIST

### 12.1. Functional Tests
- [ ] Load state từ localStorage
- [ ] Render tất cả panels
- [ ] Edit field → state update
- [ ] Save draft → state persisted
- [ ] Validation rules chạy đúng
- [ ] Error chips update
- [ ] Completeness bar update
- [ ] Risk modules toggle
- [ ] AI advisor render issues
- [ ] Click advisor item → open editor

### 12.2. Edge Cases
- [ ] Empty state (no localStorage)
- [ ] Invalid JSON trong localStorage
- [ ] Missing fields trong state
- [ ] Very long values (truncate/scroll)
- [ ] Special characters trong input
- [ ] Browser back/forward navigation

---

## 13. FUTURE ENHANCEMENTS (Potential)

1. **Auto-save:** Auto-save state mỗi N giây
2. **Undo/Redo:** History stack cho edits
3. **Field dependencies:** Auto-fill dựa trên field khác
4. **Search/Filter:** Search fields trong panels
5. **Export/Import:** Export state as JSON, import từ file
6. **Real-time collaboration:** Multiple users edit cùng lúc (WebSocket)
7. **Mobile optimization:** Responsive design improvements
8. **Accessibility:** ARIA labels, keyboard navigation improvements

---

## 14. TÓM TẮT CHO AI

Trang Summary là một **review & confirmation page** với các đặc điểm:

1. **Mục đích:** Tổng hợp, xem lại, và chỉnh sửa thông tin lô hàng trước khi phân tích risk
2. **Data source:** `localStorage['RISKCAST_STATE']`
3. **UI pattern:** Glass morphism, VisionOS-style, với inline editing
4. **Core features:**
   - Display 4 panels (Trade, Cargo, Seller, Buyer)
   - Inline editor (click field → edit)
   - Real-time validation
   - AI advisor (gợi ý/cảnh báo)
   - Risk modules toggle
   - Completeness tracking
5. **State management:** Pure client-side, localStorage-based
6. **No API calls:** Tất cả data từ localStorage
7. **Navigation:** Back → Input page, Confirm → Results page (currently disabled)

**Key files:**
- HTML: `app/templates/summary/summary_v400.html`
- Controller: `app/static/js/summary_v400/v400_controller.js`
- State: `app/static/js/summary_v400/v400_state.js`
- Renderer: `app/static/js/summary_v400/v400_renderer.js`
- Validator: `app/static/js/summary_v400/v400_validator.js`
- Editor: `app/static/js/summary_v400/v400_inline_editor.js`
- Advisor: `app/static/js/summary_v400/v400_ai_advisor.js`

