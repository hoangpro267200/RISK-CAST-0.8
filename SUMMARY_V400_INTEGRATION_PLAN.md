# RISKCAST SUMMARY V400 - UI INTEGRATION PLAN

## 🎯 OBJECTIVE
Tích hợp UI design mới từ `RiskcastSummary.tsx` vào trang Summary hiện tại **GIỮ NGUYÊN 100% JavaScript logic**.

---

## 📊 PHÂN TÍCH HIỆN TRẠNG

### 1. CRITICAL HTML SELECTORS & IDS (KHÔNG ĐƯỢC THAY ĐỔI)

#### A. Header Elements
```javascript
// Buttons trong header
#btnBack              // Back button
#btnSaveDraft         // Save draft button (top)
#btnConfirm           // Confirm button (top)
```

#### B. Main Content Areas
```javascript
// Mega Summary Banner
#megaSummaryGrid      // Container cho 5 tiles tổng quan
.mega-tile            // Individual tile trong banner
                      // data-field="fieldKey"

// Alternative: Banner Grid (fallback)
#bannerGrid           // Nếu không có megaSummaryGrid
.banner-tile          // Individual banner tile
                      // data-field="fieldKey"
```

####C. Panel System (2x2 Matrix)
```javascript
// Panel containers
#panelTrade           // Trade & Route panel body
#panelCargo           // Cargo & Packing panel body
#panelSeller          // Seller panel body
#panelBuyer           // Buyer panel body

// Panel wrappers với data attribute
[data-panel="trade"]
[data-panel="cargo"]
[data-panel="seller"]
[data-panel="buyer"]

// Field tiles trong panels
.field-tile           // Mỗi field tile
                      // data-field="fieldKey"
                      // REQUIRED: Clickable, có thể có classes:
                      // - .field-tile--error
                      // - .field-tile--warning
                      // - .field-tile--highlighted
```

#### D. AI Advisor Panel
```javascript
#advisorBody          // Body của AI advisor panel

// Advisor items (được render động)
.advisor-item         // Mỗi validation item
                      // data-rule-id="RULE_ID"
                      // data-fields="field1,field2,..."
.advisor-item--critical
.advisor-item--warning
.advisor-item--suggestion
```

#### E. Risk Modules Row
```javascript
#riskRow              // Container cho risk modules

// Risk cards (được render động)
.risk-card            // Mỗi risk module card
                      // data-module="esg|weather|congestion|carrier_perf|market|insurance"
.risk-card__toggle    // Toggle switch
                      // data-module="moduleKey"
                      // Class: .risk-card__toggle--on khi bật
```

#### F. Action Strip (Bottom)
```javascript
#actionStrip          // Footer container
.action-strip--visible // Class được add sau 500ms

// Completeness bar
#completenessBar      // Progress bar fill element
#completenessValue    // Text hiển thị percentage

// Error chips
#chipCritical         // Critical errors chip
#chipWarning          // Warnings chip
.error-chip__count    // Count số trong chip

// Bottom buttons
#btnSaveDraftBottom   // Save draft button (bottom)
#btnConfirmBottom     // Confirm button (bottom)
```

#### G. Inline Editor Bubble
```javascript
#editorBubble         // Editor popup container
                      // Classes:
                      // - .editor-bubble--visible (khi mở)
                      // - .editor-bubble--error (khi có lỗi)
                      // Attribute:
                      // - data-position="top|bottom" (arrow direction)

// Editor elements
#editorLabel          // Field label
#editorPath           // Section path
#editorBody           // Input area
#editorInput          // Input element (tạo động)
#editorStatus         // Status message area
#editorClose          // Close button (X)
#editorCancel         // Cancel button
#editorSave           // Save button
```

---

### 2. DATA ATTRIBUTES (BẮT BUỘC)

```javascript
// Field tiles
data-field="trade.pol"           // Field identifier (map to FIELD_MAP)
data-field="cargo.hs_code"       // etc.

// Panels
data-panel="trade|cargo|seller|buyer"

// Risk modules
data-module="esg|weather|congestion|carrier_perf|market|insurance"

// Advisor items
data-rule-id="MODE_PORT_MISMATCH_SEA"
data-fields="shipment.trade_route.pol,shipment.trade_route.pod"

// Editor bubble
data-position="top|bottom"       // Arrow position
```

---

### 3. JAVASCRIPT EVENT HANDLERS

#### A. Controller (v400_controller.js)
- **Khởi tạo**: Load state → render → attach handlers
- **Button handlers**:
  ```javascript
  #btnBack → confirm back
  #btnSaveDraft, #btnSaveDraftBottom → save to localStorage
  #btnConfirm, #btnConfirmBottom → validate → call API → redirect
  ```
- **Field click handlers**:
  ```javascript
  .field-tile click → V400InlineEditor.open(fieldKey, element, state)
  .banner-tile click → V400InlineEditor.open(fieldKey, element, state)
  .mega-tile click → V400InlineEditor.open(fieldKey, element, state)
  ```

#### B. Inline Editor (v400_inline_editor.js)
- **Init**: Move bubble to document.body (portal mode)
- **Events**:
  - Close button click
  - Cancel button click
  - Save button click → validate → callback → update state
  - Click outside → close
  - Escape key → close
  - Enter key (in input) → save
- **Positioning**: Fixed position using CSS variables `--editor-x`, `--editor-y`

#### C. AI Advisor (v400_ai_advisor.js)
- **Render**: Show validation results by severity
- **Item click**: 
  ```javascript
  .advisor-item click → highlight fields → open editor for first field
  ```
- **Highlight**: Add `.field-tile--highlighted` class

#### D. Risk Row (v400_risk_row.js)
- **Toggle click**:
  ```javascript
  .risk-card__toggle click → toggle state → callback → update state → re-render
  ```

---

### 4. STATE MANAGEMENT (v400_state.js)

#### localStorage Key
```javascript
'RISKCAST_STATE'      // Main state storage
```

#### State Structure
```javascript
{
  shipment: {
    trade_route: { pol, pod, mode, carrier, container_type, etd, eta, transit_time_days, incoterm, incoterm_location, priority, service_route },
    cargo_packing: { cargo_type, cargo_category, hs_code, hs_chapter, packing_type, packages, gross_weight_kg, net_weight_kg, volume_cbm, stackability, temp_control_required, is_dg },
    seller: { name, company, email, phone, address, country },
    buyer: { name, company, email, phone, address, country },
    route_tags: { tradelane, region, inland_needed }
  },
  riskModules: {
    esg: bool,
    weather: bool,
    congestion: bool,
    carrier_perf: bool,
    market: bool,
    insurance: bool
  }
}
```

---

### 5. FIELD MAP (v400_renderer.js)

**Total: 33 fields** grouped by section:

#### Trade & Route (12 fields)
```
trade.pol, trade.pod, trade.mode, trade.service_route, trade.carrier, 
trade.container_type, trade.etd, trade.eta, trade.transit_time_days, 
trade.incoterm, trade.incoterm_location, trade.priority
```

#### Cargo & Packing (12 fields)
```
cargo.cargo_type, cargo.cargo_category, cargo.hs_code, cargo.hs_chapter, 
cargo.packing_type, cargo.packages, cargo.gross_weight_kg, cargo.net_weight_kg, 
cargo.volume_cbm, cargo.stackability, cargo.temp_control_required, cargo.is_dg
```

#### Seller (6 fields)
```
seller.name, seller.company, seller.email, seller.phone, seller.address, seller.country
```

#### Buyer (6 fields)
```
buyer.name, buyer.company, buyer.email, buyer.phone, buyer.address, buyer.country
```

---

### 6. VALIDATION SYSTEM (v400_validator.js)

**25 validation rules** categorized by:
- **Critical** (8 rules): Blocking errors
- **Warning** (12 rules): Non-blocking issues
- **Suggestion** (5 rules): Best practices

Rules affect specific fields via `fieldRefs` array.

---

## 🎨 NEW UI DESIGN ANALYSIS (từ RiskcastSummary.tsx)

### Components được cung cấp:
1. **Header** - Logo, save state indicator, buttons
2. **HeroOverview** - Route overview card
3. **TradeRoutePanel** - Trade fields
4. **CargoPackingPanel** - Cargo fields
5. **ContactPanels** - Seller & Buyer cards (2 columns)
6. **ValidationStrip** - Warning banner (optional)
7. **IntelligenceModulesSection** - Risk modules grid
8. **ActionFooter** - Fixed bottom bar
9. **AIAdvisorPanel** - Right sidebar
10. **EnhancedInlineEditor** - Smart popup editor
11. **AIAssistantFab** - Floating chat button (optional)
12. **ToastNotification** - Toast system

### Design Characteristics:
- **VisionOS theme**: Glass morphism, gradients, neon accents
- **Dark background**: `from-[#0a1628] via-[#0d1b35] to-[#0a1628]`
- **Glassmorphism cards**: `backdrop-blur-xl bg-gradient-to-br from-white/10 to-white/5`
- **Cyan/Teal accent colors**: `#00D9FF`, `#00C896`
- **Fixed footer**: Action strip at bottom

---

## 🚀 INTEGRATION STRATEGY

### PRINCIPLE: **HTML Only** Integration

**KHÔNG ĐƯỢC THAY ĐỔI**:
- ❌ JavaScript files
- ❌ State management logic
- ❌ Event handlers
- ❌ Data flow
- ❌ Validation rules

**CHỈ ĐƯỢC THAY ĐỔI**:
- ✅ HTML template structure
- ✅ CSS styling
- ✅ Wrapper elements (for styling)
- ✅ Visual presentation
- ✅ Layout và responsiveness

---

## 📋 STEP-BY-STEP INTEGRATION PLAN

### PHASE 1: PREPARE & BACKUP ✅

1. ✅ Đã phân tích toàn bộ code hiện tại
2. ✅ Đã map tất cả selectors và IDs quan trọng
3. ✅ Đã hiểu data flow và event handlers
4. Backup file HTML gốc (sẽ thực hiện)

### PHASE 2: CREATE NEW HTML TEMPLATE

#### Step 2.1: Header Section
**Requirements**:
- Giữ IDs: `#btnBack`, `#btnSaveDraft`, `#btnConfirm`
- Thêm save state indicator
- Styling mới với VisionOS theme

**Mapping từ React → HTML**:
```jsx
// React: <Header saveState={} lastSaved={} />
// HTML: <header class="summary-topbar">
//   - Logo section (giữ nguyên)
//   - Save state indicator (thêm mới)
//   - Buttons: #btnBack, #btnSaveDraft, #btnConfirm (giữ IDs)
```

#### Step 2.2: Mega Summary / Hero Overview
**Requirements**:
- Giữ ID: `#megaSummaryGrid`
- 5 tiles: route, mode, container, transit/dates, weight/volume
- Mỗi tile có `data-field="fieldKey"` và class `.mega-tile`

**Mapping**:
```jsx
// React: <HeroOverview data={shipmentData} />
// HTML: <section class="mega-summary">
//   <div class="mega-summary__grid" id="megaSummaryGrid">
//     <!-- Tiles được render bởi v400_renderer.js -->
//   </div>
```

#### Step 2.3: Main Grid (Panels + Sidebar)
**Layout mới**: Grid 2 columns
- Left: 2x2 panel matrix
- Right: AI Advisor sticky sidebar

**Requirements**:
- Giữ IDs: `#panelTrade`, `#panelCargo`, `#panelSeller`, `#panelBuyer`, `#advisorBody`
- Giữ attributes: `data-panel="..."` 
- Panels render field tiles bởi v400_renderer.js
- AI advisor render bởi v400_ai_advisor.js

**Mapping**:
```jsx
// React: <TradeRoutePanel />, <CargoPackingPanel />, <ContactPanels />, <AIAdvisorPanel />
// HTML: <section class="summary-main-grid">
//   <div class="summary-matrix">
//     <div class="summary-panel" data-panel="trade">
//       <div id="panelTrade"></div>
//     </div>
//     <!-- Similar for cargo, seller, buyer -->
//   </div>
//   <aside class="advisor-panel">
//     <div id="advisorBody"></div>
//   </aside>
```

#### Step 2.4: Risk Modules Row
**Requirements**:
- Giữ ID: `#riskRow`
- Modules render bởi v400_risk_row.js

**Mapping**:
```jsx
// React: <IntelligenceModulesSection modules={} setModules={} />
// HTML: <section class="risk-row">
//   <div class="risk-row__inner" id="riskRow"></div>
// </section>
```

#### Step 2.5: Action Strip (Bottom Footer)
**Requirements**:
- Giữ ID: `#actionStrip`
- Giữ IDs: `#completenessBar`, `#completenessValue`, `#chipCritical`, `#chipWarning`, `#btnSaveDraftBottom`, `#btnConfirmBottom`
- Fixed position at bottom

**Mapping**:
```jsx
// React: <ActionFooter data={} modules={} onRunAnalysis={} lastSaved={} />
// HTML: <footer class="action-strip" id="actionStrip">
//   <div class="completeness-bar">
//     <div id="completenessBar"></div>
//     <span id="completenessValue">0%</span>
//   </div>
//   <div class="error-chips">
//     <div id="chipCritical"><span class="error-chip__count">0</span></div>
//     <div id="chipWarning"><span class="error-chip__count">0</span></div>
//   </div>
//   <button id="btnSaveDraftBottom">Save</button>
//   <button id="btnConfirmBottom">Confirm</button>
// </footer>
```

#### Step 2.6: Inline Editor Bubble
**Requirements**:
- Giữ ID: `#editorBubble` và tất cả child IDs
- Giữ nguyên cấu trúc (header, body, footer)
- Styling mới với glassmorphism

**Mapping**: Giữ nguyên structure, chỉ update CSS classes

### PHASE 3: UPDATE CSS

#### Step 3.1: Create Base Styles
File: `summary_layout_v550.css` (NEW)
- Grid layouts
- Spacing system
- Responsive breakpoints

#### Step 3.2: Create Component Styles
File: `summary_components_v550.css` (NEW)
- `.mega-tile` - Glassmorphism cards
- `.summary-panel` - Panel cards
- `.field-tile` - Field tiles with hover effects
- `.advisor-panel` - Sidebar styling
- `.risk-card` - Risk module cards
- `.action-strip` - Bottom fixed bar
- `.editor-bubble` - Popup editor
- Error states: `.field-tile--error`, `.field-tile--warning`, `.field-tile--highlighted`

#### Step 3.3: Create Theme & Effects
File: `summary_theme_v550.css` (NEW)
- VisionOS dark theme colors
- Gradient definitions
- Glow effects
- Animations (pulse, shimmer, scale-in)

#### Step 3.4: Update Load Order
```html
<link rel="stylesheet" href="/static/css/summary_v400/summary_reset.css">
<link rel="stylesheet" href="/static/css/summary_v400/summary_typography.css">
<link rel="stylesheet" href="/static/css/summary_v400/summary_layout_v550.css"> <!-- NEW -->
<link rel="stylesheet" href="/static/css/summary_v400/summary_components_v550.css"> <!-- NEW -->
<link rel="stylesheet" href="/static/css/summary_v400/summary_editor.css">
<link rel="stylesheet" href="/static/css/summary_v400/summary_theme_v550.css"> <!-- NEW -->
<link rel="stylesheet" href="/static/css/summary_v400/summary_effects.css">
<link rel="stylesheet" href="/static/css/summary_v400/summary_editor_fix.css">
```

### PHASE 4: TESTING & VALIDATION

#### Test Checklist:
- [ ] Page loads without errors
- [ ] State loads from localStorage
- [ ] Mega summary renders correctly (5 tiles)
- [ ] All 4 panels render with field tiles
- [ ] Click field tile → opens editor bubble
- [ ] Editor positioned correctly (không bị overflow)
- [ ] Editor saves changes → state updates → re-render
- [ ] Validation runs → AI advisor shows issues
- [ ] Click advisor item → highlights fields → opens editor
- [ ] Error chips update (critical, warning counts)
- [ ] Completeness bar updates (0-100%)
- [ ] Risk modules toggle works (on/off state)
- [ ] Save draft button works
- [ ] Back button works (with confirmation)
- [ ] Confirm button validates before proceeding
- [ ] Toast notifications work
- [ ] Responsive design (desktop, tablet, mobile)
- [ ] Dark theme looks good
- [ ] Animations smooth
- [ ] No console errors

---

## 🎯 KEY IMPLEMENTATION NOTES

### 1. Field Tiles Structure
**CRITICAL**: Mỗi field tile phải có:
```html
<div class="field-tile" data-field="trade.pol">
  <div class="field-tile__label">Cảng đi (POL)</div>
  <div class="field-tile__value">CNSHA</div>
  <!-- Optional: status message nếu có validation issue -->
  <div class="field-tile__status">
    <span class="field-tile__status-icon">⚠️</span>
    <span class="field-tile__status-text">Error message</span>
  </div>
</div>
```

### 2. Editor Bubble Positioning
- Editor được move vào `document.body` (portal mode)
- Position sử dụng CSS variables: `--editor-x`, `--editor-y`
- Arrow direction: `data-position="top|bottom"`
- Phải reposition on scroll/resize

### 3. State Update Flow
```
User clicks field tile
  → Editor opens (V400InlineEditor.open)
  → User edits value
  → User clicks Save
  → Validate input
  → Update state (V400State.setValueAtPath)
  → Callback to controller (V400Controller.handleStateSave)
  → Save to localStorage
  → Re-render all (V400Controller.refresh)
    → Render banner (V400Renderer.renderBanner)
    → Render panels (V400Renderer.renderAllPanels)
    → Run validation (V400Validator.evaluateAll)
    → Render AI advisor (V400AIAdvisor.render)
    → Render risk row (V400RiskRow.render)
    → Update completeness bar
    → Update error chips
    → Re-attach field click handlers
```

### 4. Completeness Calculation
**13 required fields** (cứng):
```javascript
shipment.trade_route.pol
shipment.trade_route.pod
shipment.trade_route.mode
shipment.trade_route.etd
shipment.trade_route.container_type
shipment.cargo_packing.cargo_type
shipment.cargo_packing.hs_code
shipment.cargo_packing.gross_weight_kg
shipment.cargo_packing.volume_cbm
shipment.seller.company
shipment.seller.email
shipment.buyer.company
shipment.buyer.email
```

Percentage = `(filled / 13) * 100`

### 5. Confirm Button Logic
```javascript
// Validate trước khi confirm
if (validationResults.critical.length > 0) {
  showToast('Please fix all critical errors', 'error');
  return;
}

if (completeness < 70) {
  confirm(`Only ${completeness}% complete. Continue?`);
}

// Call API
POST /api/v1/risk/v2/analyze
  → Save result to localStorage['RISKCAST_RESULTS_V2']
  → Export summary state for ResultsOS
  → Redirect to /results
```

---

## 🎨 VISUAL DESIGN GUIDELINES

### Color Palette
```css
/* Primary Colors */
--bg-primary: #0a1628;      /* Dark blue-black */
--bg-secondary: #0d1b35;    /* Slightly lighter */

/* Accent Colors */
--accent-cyan: #00D9FF;     /* Bright cyan */
--accent-teal: #00C896;     /* Teal green */
--accent-violet: #7B4DFF;   /* Purple */

/* Text Colors */
--text-primary: rgba(255, 255, 255, 0.9);
--text-secondary: rgba(255, 255, 255, 0.7);
--text-tertiary: rgba(255, 255, 255, 0.5);
--text-muted: rgba(255, 255, 255, 0.4);

/* Status Colors */
--success: #00C896;
--warning: #FF9500;
--error: #FF3B30;
--info: #00D9FF;

/* Glassmorphism */
--glass-bg: rgba(255, 255, 255, 0.05);
--glass-border: rgba(255, 255, 255, 0.1);
--glass-blur: 16px;
```

### Typography
```css
/* Font Family */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'Space Mono', 'Courier New', monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing System
```css
--spacing-1: 0.25rem;  /* 4px */
--spacing-2: 0.5rem;   /* 8px */
--spacing-3: 0.75rem;  /* 12px */
--spacing-4: 1rem;     /* 16px */
--spacing-6: 1.5rem;   /* 24px */
--spacing-8: 2rem;     /* 32px */
--spacing-12: 3rem;    /* 48px */
```

### Border Radius
```css
--radius-sm: 0.5rem;   /* 8px */
--radius-md: 0.75rem;  /* 12px */
--radius-lg: 1rem;     /* 16px */
--radius-xl: 1.5rem;   /* 24px */
--radius-2xl: 2rem;    /* 32px */
```

### Shadows
```css
--shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 16px rgba(0, 0, 0, 0.2);
--shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.3);
--shadow-glow-cyan: 0 0 20px rgba(0, 217, 255, 0.3);
--shadow-glow-teal: 0 0 20px rgba(0, 200, 150, 0.3);
```

---

## ✅ SUCCESS CRITERIA

### Must Have:
1. ✅ Tất cả JavaScript functions hoạt động bình thường
2. ✅ State management không thay đổi
3. ✅ Validation rules vẫn chạy đúng
4. ✅ Editor mở đóng mượt mà
5. ✅ Field tiles clickable và có feedback
6. ✅ Completeness bar cập nhật real-time
7. ✅ Error chips hiển thị đúng
8. ✅ Risk modules toggle hoạt động
9. ✅ Confirm flow không bị break
10. ✅ Responsive trên mọi thiết bị

### Should Have:
1. ✅ VisionOS theme đẹp và chuyên nghiệp
2. ✅ Glassmorphism effects mượt mà
3. ✅ Animations tinh tế
4. ✅ Hover effects rõ ràng
5. ✅ Error states dễ nhận biết
6. ✅ Loading states (nếu cần)

### Nice to Have:
1. Toast notifications đẹp
2. FAB chat assistant (optional)
3. Keyboard shortcuts support
4. Focus management tốt
5. Accessibility improvements

---

## 🚨 COMMON PITFALLS TO AVOID

1. ❌ **Thay đổi IDs/classes** mà JavaScript đang target
2. ❌ **Xóa data attributes** quan trọng
3. ❌ **Break event delegation** bằng cách wrap elements không đúng
4. ❌ **Thay đổi cấu trúc state** trong localStorage
5. ❌ **Modify JavaScript files** (kể cả chỉnh sửa nhỏ)
6. ❌ **Forget to reposition editor** khi scroll/resize
7. ❌ **Không test với state rỗng** và state đầy đủ
8. ❌ **Không test validation rules** đầy đủ

---

## 📞 NEXT STEPS

### Immediate Actions:
1. ✅ Document này đã hoàn thiện
2. Backup file HTML gốc
3. Tạo new HTML template
4. Tạo new CSS files
5. Test từng component
6. Integration testing
7. Bug fixes
8. Production deployment

### Timeline Estimate:
- Phase 1 (Analysis): ✅ COMPLETED
- Phase 2 (HTML Template): 3-4 hours
- Phase 3 (CSS Styling): 4-5 hours
- Phase 4 (Testing & Fixes): 2-3 hours
- **Total**: ~10-12 hours

---

## 📚 REFERENCE FILES

### Core Files:
1. `app/templates/summary/summary_v400.html` - Current template
2. `app/static/js/summary_v400/v400_controller.js` - Main orchestrator
3. `app/static/js/summary_v400/v400_state.js` - State management
4. `app/static/js/summary_v400/v400_renderer.js` - DOM rendering
5. `app/static/js/summary_v400/v400_inline_editor.js` - Editor logic
6. `app/static/js/summary_v400/v400_ai_advisor.js` - AI advisor
7. `app/static/js/summary_v400/v400_risk_row.js` - Risk modules
8. `app/static/js/summary_v400/v400_validator.js` - 25 validation rules

### Design Reference:
- `RiskcastSummary.tsx` - Main component
- `riskcast/*.tsx` - Sub-components
- React code chỉ dùng để tham khảo UI/UX, **KHÔNG implement React**

---

**Status**: 📋 PLAN READY - READY FOR IMPLEMENTATION

**Author**: AI Assistant
**Date**: 2026-01-07
**Version**: 1.0

