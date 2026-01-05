# BÁO CÁO CHI TIẾT TRANG INPUT - RISKCAST v16

## 1. TỔNG QUAN

Trang **Input** (Input v20 - Premium VisionOS Edition) là trang nhập liệu chính của hệ thống RISKCAST. Đây là bước đầu tiên trong workflow, nơi người dùng nhập tất cả thông tin về lô hàng (shipment) để hệ thống có thể phân tích rủi ro.

**URL Route:** `/input` → redirect đến `/input_v20`  
**Template:** `app/templates/input/input_v20.html`  
**Controller Backend:** `app/main.py` (routes `/input`, `/input_v20`)  
**Controller Frontend:** `app/static/js/v20/core/RiskcastInputController.js`

**Version hiện tại:** v20.3 (Premium VisionOS Edition with Luxurious Glow)

---

## 2. KIẾN TRÚC TỔNG THỂ

### 2.1. Cấu trúc Module JavaScript (v20 Architecture)

Trang Input v20 sử dụng kiến trúc **modular ES6 classes** với cấu trúc rõ ràng:

```
v20/
├── index.js                          # Entry point
├── core/
│   ├── RiskcastInputController.js   # Main orchestrator
│   ├── StateManager.js              # State management
│   └── APIClient.js                 # API communication
├── modules/
│   ├── TransportModule.js           # Transport section logic
│   ├── CargoModule.js               # Cargo section logic
│   ├── PartyModule.js               # Seller/Buyer logic
│   ├── PriorityManager.js           # Priority selection
│   └── ModuleCardsManager.js        # Risk modules toggle
├── ui/
│   ├── DropdownManager.js           # Dropdown UI
│   ├── AutoSuggestManager.js        # Autocomplete
│   ├── PillGroupManager.js          # Pill button groups
│   ├── UploadZoneManager.js         # File upload
│   └── ToastManager.js              # Notifications
├── effects/
│   ├── ThemeManager.js              # Dark/Light theme
│   ├── ParticleBackground.js        # Particle effects
│   ├── FormPanelGlow.js             # Glow effects
│   ├── NavigationSpy.js             # Scroll spy
│   └── SidebarManager.js            # Sidebar toggle
└── utils/
    ├── DataLoaders.js               # Load logistics data
    ├── DateCalculators.js           # ETA calculation
    ├── DemoAutoFill.js              # Demo data
    ├── SanitizeHelpers.js           # Data sanitization
    └── Validators.js                # Input validation
```

### 2.2. State Management

**Primary Key:** `RISKCAST_STATE` trong `localStorage`  
**Secondary Key:** `rc-input-state` trong `localStorage` (fallback)

**Cấu trúc State (v20 format):**
```javascript
{
  transport: {
    tradeLane: string,              // e.g., "vn_us", "vn_cn"
    mode: string,                   // "SEA", "AIR", "ROAD", "RAIL", "MULTIMODAL"
    shipmentType: string,           // "FCL", "LCL", "BREAK_BULK", etc.
    serviceRoute: string,           // Service route ID
    carrier: string,                // Carrier name
    containerType: string,          // "20GP", "40GP", "40HC", etc.
    pol: string,                    // Port of Loading code
    pod: string,                    // Port of Discharge code
    etd: string,                    // Estimated Time of Departure (date)
    eta: string,                    // Estimated Time of Arrival (date, auto-calculated)
    transitTimeDays: number,        // Transit time in days
    incoterm: string,               // "EXW", "FOB", "CIF", "DDP", etc.
    incotermLocation: string,       // Incoterm location
    priority: string,               // "STANDARD", "EXPRESS", "URGENT"
    reliabilityScore: number        // Auto-filled from route data
  },
  cargo: {
    cargoType: string,              // Cargo category
    hsCode: string,                 // HS Code
    cargoCategory: string,          // "General", "Electronics", etc.
    packingType: string,            // "Pallet", "Box", "Crate", etc.
    packages: number,               // Number of packages
    grossWeightKg: number,          // Gross weight (kg)
    netWeightKg: number,            // Net weight (kg)
    volumeCbm: number,              // Volume (CBM)
    stackability: boolean,          // Can stack
    tempControlRequired: boolean,   // Requires temperature control
    isDangerousGoods: boolean,      // Dangerous goods flag
    cargoValue: number,             // Cargo value (USD)
    packingList: Array<Object>      // Detailed packing list items
  },
  seller: {
    name: string,
    company: string,
    email: string,
    phone: string,
    country: string,
    city: string,
    address: string,
    taxId: string
  },
  buyer: {
    name: string,
    company: string,
    email: string,
    phone: string,
    country: string,
    city: string,
    address: string,
    taxId: string
  },
  priority: {
    profile: string,                // "FASTEST", "BALANCED", "CHEAPEST", "SAFEST"
    speedWeight: number,
    costWeight: number,
    riskWeight: number
  },
  modules: {
    esg: boolean,
    weather: boolean,
    congestion: boolean,
    carrier_perf: boolean,
    market: boolean,
    insurance: boolean
  }
}
```

**State Flow:**
1. Load từ `RISKCAST_STATE` (nếu có)
2. Fallback to `rc-input-state` (nếu không có)
3. Merge với default state
4. Sanitize state
5. Save to `RISKCAST_STATE` khi có thay đổi

---

## 3. GIAO DIỆN NGƯỜI DÙNG

### 3.1. Layout Chính

```
┌─────────────────────────────────────────────────────────┐
│  HEADER (Fixed)                                         │
│  [Logo RISKCAST v20] [AI Ready] [Theme] [Notifications] │
├──────────────────┬──────────────────────────────────────┤
│  SIDEBAR         │  MAIN CONTENT                        │
│  (Fixed)         │  (Scrollable)                        │
│                  │                                      │
│  Navigation:     │  ┌────────────────────────────────┐ │
│  [Transport]     │  │ SECTION 01: TRANSPORT SETUP   │ │
│  [Cargo]         │  │  - Trade Lane                  │ │
│  [Seller]        │  │  - Mode of Transport           │ │
│  [Buyer]         │  │  - Service Route               │ │
│  [Modules]       │  │  - Container Type              │ │
│  [Upload]        │  │  - POL/POD                     │ │
│                  │  │  - ETD/ETA                     │ │
│  [Save Draft]    │  └────────────────────────────────┘ │
│                  │                                      │
│                  │  ┌────────────────────────────────┐ │
│                  │  │ SECTION 02: CARGO & PACKING   │ │
│                  │  │  - Cargo Type                  │ │
│                  │  │  - HS Code                     │ │
│                  │  │  - Packing List (Table)        │ │
│                  │  │  - Weight/Volume               │ │
│                  │  └────────────────────────────────┘ │
│                  │                                      │
│                  │  ┌────────────────────────────────┐ │
│                  │  │ SECTION 03: SELLER DETAILS    │ │
│                  │  │  - Company Info                │ │
│                  │  │  - Contact Info                │ │
│                  │  │  - Address                     │ │
│                  │  └────────────────────────────────┘ │
│                  │                                      │
│                  │  ┌────────────────────────────────┐ │
│                  │  │ SECTION 04: BUYER DETAILS     │ │
│                  │  │  - Company Info                │ │
│                  │  │  - Contact Info                │ │
│                  │  │  - Address                     │ │
│                  │  └────────────────────────────────┘ │
│                  │                                      │
│                  │  ┌────────────────────────────────┐ │
│                  │  │ SECTION 05: RISK MODULES      │ │
│                  │  │  [ESG] [Weather] [Congestion] │ │
│                  │  │  [Carrier] [Market] [Insurance]│ │
│                  │  └────────────────────────────────┘ │
│                  │                                      │
│                  │  ┌────────────────────────────────┐ │
│                  │  │ SECTION 06: FILE UPLOAD       │ │
│                  │  │  - Drag & drop zone            │ │
│                  │  └────────────────────────────────┘ │
│                  │                                      │
│                  │  [Continue to Summary]              │
└──────────────────┴──────────────────────────────────────┘
```

### 3.2. Các Component Chính

#### 3.2.1. Header (Fixed Top Bar)
- **Logo:** RISKCAST v20 với icon
- **Status Indicator:** "AI Ready" với dot indicator
- **Actions:**
  - Theme toggle (Dark/Light)
  - Notifications (với badge count)
  - User avatar

#### 3.2.2. Sidebar Navigation (Fixed Left)
- **Navigation Items:**
  1. Transport (icon: ship)
  2. Cargo (icon: package)
  3. Seller (icon: building-2)
  4. Buyer (icon: users)
  5. Modules (icon: layers)
  6. Upload (icon: upload-cloud)

- **Footer:**
  - Save Draft button

- **Features:**
  - Active section highlighting
  - Smooth scroll to section
  - Toggle collapse/expand

#### 3.2.3. Section 01: Transport Setup

**Fields:**
1. **Trade Lane** (Required) - Dropdown với search
   - Options: vn_us, vn_cn, vn_kr, vn_jp, vn_eu, vn_hk, vn_in, vn_th, vn_tw, domestic
   - Dynamic options từ LOGISTICS_DATA

2. **Mode of Transport** (Required) - Dropdown
   - Options: SEA, AIR, ROAD, RAIL, MULTIMODAL
   - Filtered based on selected trade lane
   - Recommended badge nếu có recommendation

3. **Shipment Type** (Required) - Dropdown
   - Options: FCL, LCL, BREAK_BULK, etc.
   - Filtered based on mode

4. **Service Route** (Optional) - Dropdown với search
   - Dynamic options từ LOGISTICS_DATA
   - Route details panel (transit time, surcharge, reliability)

5. **Carrier** (Optional) - Text input với autocomplete
   - Auto-suggest từ carrier database

6. **Container Type** (Required) - Dropdown
   - Options: 20GP, 40GP, 40HC, 45HC, REEFER 20, REEFER 40, etc.
   - Filtered based on mode

7. **POL (Port of Loading)** (Required) - Autocomplete input
   - Port database với search
   - Auto-suggest based on trade lane

8. **POD (Port of Discharge)** (Required) - Autocomplete input
   - Port database với search
   - Auto-suggest based on trade lane

9. **ETD (Estimated Time of Departure)** (Required) - Date picker
   - Date input với calendar icon

10. **ETA (Estimated Time of Arrival)** (Auto-calculated) - Date input (disabled)
    - Auto-calculated từ ETD + Transit Time

11. **Transit Time (days)** (Required) - Number input
    - Auto-filled từ route data
    - Manual override allowed

12. **Incoterm** (Optional) - Dropdown
    - Options: EXW, FCA, FOB, CFR, CIF, CPT, CIP, DAP, DPU, DDP

13. **Incoterm Location** (Optional) - Text input
    - Required for certain incoterms

14. **Priority** (Optional) - Pill group
    - Options: STANDARD, EXPRESS, URGENT

15. **Reliability Score** (Auto-filled) - Text input (disabled)
    - From service route data

**Actions:**
- Reset form button
- Auto-Fill Demo button

#### 3.2.4. Section 02: Cargo & Packing

**Fields:**
1. **Cargo Type** (Required) - Dropdown với search
   - Options từ LOGISTICS_DATA.cargoTypes
   - Searchable

2. **Cargo Category** (Optional) - Dropdown
   - Options: General Cargo, Electronics, Perishable, High Value, Fragile, Pharmaceuticals, Textiles

3. **HS Code** (Required) - Text input
   - Format: 6-10 digits
   - HS Chapter auto-extracted

4. **HS Chapter** (Auto-extracted) - Text input (disabled)

5. **Packing Type** (Optional) - Dropdown
   - Options: Pallet, Box, Crate, Bag, Drum, Bulk

6. **Packages** (Required) - Number input
   - Total number of packages

7. **Gross Weight (kg)** (Required) - Number input
   - Total gross weight

8. **Net Weight (kg)** (Optional) - Number input
   - Total net weight

9. **Volume (CBM)** (Required) - Number input
   - Total volume

10. **Stackability** (Optional) - Checkbox/Toggle
    - Can stack items

11. **Temp Control Required** (Optional) - Checkbox/Toggle
    - Requires temperature control

12. **Dangerous Goods** (Optional) - Checkbox/Toggle
    - Is dangerous goods

13. **Cargo Value (USD)** (Required) - Number input với currency selector
    - Currency prefix ($)
    - Currency selector (USD, EUR, etc.)

**Packing List Table:**
- Dynamic table với add/remove rows
- Columns:
  - STT (Serial number)
  - Mô Tả Hàng Hóa (Description)
  - Số Kiện (Packages)
  - Loại Đóng Gói (Packing Type)
  - Dài x Rộng x Cao (Dimensions in cm)
  - Trọng Lượng Kiện (Weight per package in kg)
  - Stackable (Checkbox)
  - Actions (Delete button)

**Auto-Calculation Panel:**
- Total Packages (sum from table)
- Total Gross Weight (sum from table)
- Total Volume (calculated from dimensions)
- Container Fit Analysis (suggested container types)

#### 3.2.5. Section 03: Seller Details

**Fields:**
1. **Contact Name** (Optional) - Text input
2. **Company Name** (Required) - Text input
3. **Email** (Required) - Email input
4. **Phone** (Required) - Tel input
5. **Country** (Required) - Autocomplete input
   - Country database với search
6. **City** (Optional) - Text input
7. **Address** (Optional) - Textarea
8. **Tax ID / VAT** (Optional) - Text input

#### 3.2.6. Section 04: Buyer Details

**Fields:** Tương tự Seller
1. Contact Name
2. Company Name (Required)
3. Email (Required)
4. Phone (Required)
5. Country (Required) - Autocomplete
6. City
7. Address
8. Tax ID / VAT

#### 3.2.7. Section 05: Risk Modules

**6 Risk Modules (Toggle cards):**
1. **ESG Risk** - Environmental, Social, Governance risk analysis
2. **Weather & Climate** - Weather and climate risk assessment
3. **Port Congestion** - Port congestion risk analysis
4. **Carrier Performance** - Carrier reliability analysis
5. **Market Condition** - Market condition scanner
6. **Insurance Optimization** - Insurance optimization analysis

**Mỗi module có:**
- Toggle switch (ON/OFF)
- Description
- Icon
- Impact indicator (nếu có)

#### 3.2.8. Section 06: File Upload

**Upload Zone:**
- Drag & drop area
- Click to browse
- Supported file types: PDF, Excel, Word, Images
- File preview
- Remove file button

**Purpose:**
- Upload shipping documents
- Upload packing lists
- Upload invoices
- Upload certificates

#### 3.2.9. Action Buttons (Bottom)

- **Save Draft** - Lưu state vào localStorage
- **Continue to Summary** - Validate → Save → Redirect to `/summary`

---

## 4. CHỨC NĂNG CHI TIẾT

### 4.1. Khởi tạo (Initialization)

**Flow khởi tạo:**
1. DOMContentLoaded event
2. Sanitize existing RISKCAST_STATE
3. Create RiskcastInputController instance
4. Controller.init():
   - Sanitize state
   - Load logistics data (LOGISTICS_DATA)
   - Initialize effects (Theme, Particles, Glow, Navigation, Sidebar)
   - Initialize UI (Dropdowns, AutoSuggest, Pills, Upload)
   - Initialize modules (Transport, Cargo, Party, Priority, Modules)
   - Initialize demo auto-fill
   - Initialize input handlers
   - Initialize buttons
   - Load state into UI
5. Controller ready

**Code location:** `v20/index.js` → `RiskcastInputController.init()`

### 4.2. State Management

#### 4.2.1. Load State
- Đọc từ `localStorage.getItem('RISKCAST_STATE')`
- Fallback to `localStorage.getItem('rc-input-state')`
- Parse JSON
- Map RISKCAST_STATE format to v20 format (nếu cần)
- Merge với default state
- Sanitize state (remove null/undefined, validate types)

#### 4.2.2. Save State
- Lưu vào `localStorage.setItem('RISKCAST_STATE', JSON.stringify(state))`
- Also save to `rc-input-state` (backup)
- Trigger sau mỗi field change (debounced)
- Or khi click "Save Draft"

**Code location:** `v20/core/StateManager.js`

### 4.3. Auto-Suggest & Autocomplete

#### 4.3.1. Port Autocomplete (POL/POD)
- Search trong port database
- Filter by trade lane (available ports)
- Show: Code, Name, Country
- Select → Update field + trigger change event

#### 4.3.2. Country Autocomplete (Seller/Buyer)
- Search trong country database
- Show country names
- Select → Update field

#### 4.3.3. Route Auto-Suggest
- Based on seller country + buyer country
- Auto-select trade lane
- Trigger route selection logic

**Code location:** `v20/ui/AutoSuggestManager.js`

### 4.4. Dropdown Manager

**Features:**
- Custom dropdown UI (không dùng native select)
- Search functionality
- Keyboard navigation
- Multi-select support (nếu cần)
- Dynamic options loading
- Value binding với state

**Code location:** `v20/ui/DropdownManager.js`

### 4.5. Dynamic Field Dependencies

#### 4.5.1. Trade Lane → Mode
- Select trade lane → Filter available modes
- Show recommended mode (nếu có)

#### 4.5.2. Mode → Shipment Type
- Select mode → Filter shipment types
- SEA → FCL, LCL, BREAK_BULK
- AIR → ULD types
- ROAD → FTL, LTL
- RAIL → FCL, LCL

#### 4.5.3. Mode → Container Type
- Select mode → Filter container types
- Auto-fix container type nếu không hợp lệ

#### 4.5.4. Route → Transit Time
- Select service route → Auto-fill transit time
- Auto-fill reliability score
- Show route details panel

#### 4.5.5. ETD + Transit Time → ETA
- Change ETD hoặc Transit Time → Auto-calculate ETA
- Formula: ETA = ETD + Transit Time (days)

**Code location:** `v20/modules/TransportModule.js`

### 4.6. Packing List Management

#### 4.6.1. Add Row
- Click "Thêm Hàng Hóa" → Add new row to table
- Default values
- Auto-focus first field

#### 4.6.2. Remove Row
- Click delete button → Remove row
- Update totals

#### 4.6.3. Auto-Calculate Totals
- Sum packages
- Sum weights
- Calculate volume from dimensions
- Container fit analysis

**Code location:** `v20/modules/CargoModule.js`

### 4.7. Validation

#### 4.7.1. Real-time Validation
- Validate on field blur
- Validate on form submit
- Show error messages
- Highlight error fields

#### 4.7.2. Required Fields
- Check required fields trước khi submit
- Show error nếu thiếu

#### 4.7.3. Format Validation
- Email format
- Phone format
- Date format
- Number format
- HS Code format

**Code location:** `v20/utils/Validators.js`

### 4.8. Form Submission

#### 4.8.1. Save Draft
- Save current state to localStorage
- Show toast notification
- Không redirect

#### 4.8.2. Continue to Summary
- Validate all required fields
- Nếu có lỗi → Show errors, không submit
- Nếu OK → Save state → Redirect to `/summary`

**Code location:** `v20/core/RiskcastInputController.js` → `handleContinue()`

### 4.9. Effects & Animations

#### 4.9.1. Theme Manager
- Dark/Light theme toggle
- Persist theme preference
- Smooth transition

#### 4.9.2. Particle Background
- Canvas-based particle animation
- Configurable particle count
- Performance optimized

#### 4.9.3. Form Panel Glow
- Glow effect on focus
- Section highlighting
- Smooth animations

#### 4.9.4. Navigation Spy
- Highlight active section in sidebar
- Smooth scroll to section
- Update on scroll

#### 4.9.5. Sidebar Manager
- Toggle collapse/expand
- Responsive behavior
- Smooth animations

**Code location:** `v20/effects/`

### 4.10. Demo Auto-Fill

**Purpose:** Fill form with sample data for testing/demo

**Features:**
- Click "Auto-Fill Demo" button
- Fill all sections với realistic data
- Useful for:
  - Testing
  - Demo purposes
  - Learning the form

**Code location:** `v20/utils/DemoAutoFill.js`

---

## 5. DATA FLOW

### 5.1. Load Flow
```
User visits /input_v20
  ↓
DOMContentLoaded
  ↓
RiskcastInputController constructor
  ↓
StateManager constructor
  - Load RISKCAST_STATE from localStorage
  - Load rc-input-state (fallback)
  - Map to v20 format
  - Sanitize
  ↓
Controller.init()
  ↓
Load LOGISTICS_DATA (async)
  ↓
Initialize all modules
  ↓
Load state into UI (populate fields)
  ↓
Attach event handlers
  ↓
Ready
```

### 5.2. Input Change Flow
```
User changes field value
  ↓
Input event handler
  ↓
Update StateManager state
  ↓
Debounce (250ms)
  ↓
Save to localStorage (RISKCAST_STATE + rc-input-state)
  ↓
Trigger dependent field updates (nếu có)
  - Trade Lane → Filter Modes
  - Mode → Filter Container Types
  - ETD + Transit → Calculate ETA
  ↓
Update UI (nếu cần)
```

### 5.3. Submit Flow
```
User clicks "Continue to Summary"
  ↓
handleContinue()
  ↓
Validate required fields
  ↓
If errors → Show errors, stop
  ↓
If OK → Get state from StateManager
  ↓
Sanitize state
  ↓
Save to RISKCAST_STATE
  ↓
Redirect to /summary
```

### 5.4. Auto-Suggest Flow
```
User types in POL/POD field
  ↓
Input event
  ↓
AutoSuggestManager.getSuggestions(query, fieldName)
  ↓
Filter port database (or available ports)
  ↓
Render suggestions dropdown
  ↓
User selects suggestion
  ↓
Update field value
  ↓
Trigger state update
  ↓
Trigger dependent updates (nếu có)
```

---

## 6. MODULE ARCHITECTURE

### 6.1. TransportModule

**Responsibility:** Manage Transport section logic

**Functions:**
- Handle trade lane selection
- Filter modes based on trade lane
- Filter shipment types based on mode
- Handle route selection
- Auto-fill transit time
- Calculate ETA
- Handle container type selection
- Manage POL/POD autocomplete

**Code location:** `v20/modules/TransportModule.js`

### 6.2. CargoModule

**Responsibility:** Manage Cargo section logic

**Functions:**
- Handle cargo type selection
- Manage packing list table
- Add/remove packing list rows
- Calculate totals (packages, weight, volume)
- Container fit analysis
- Handle cargo value input

**Code location:** `v20/modules/CargoModule.js`

### 6.3. PartyModule

**Responsibility:** Manage Seller/Buyer sections logic

**Functions:**
- Handle seller/buyer inputs
- Country autocomplete
- Address management
- Contact info validation

**Code location:** `v20/modules/PartyModule.js`

### 6.4. PriorityManager

**Responsibility:** Manage Priority selection

**Functions:**
- Handle priority profile selection
- Calculate priority weights
- Update priority indicators

**Code location:** `v20/modules/PriorityManager.js`

### 6.5. ModuleCardsManager

**Responsibility:** Manage Risk Modules toggle

**Functions:**
- Toggle risk modules ON/OFF
- Update module indicators
- Handle module selection logic

**Code location:** `v20/modules/ModuleCardsManager.js`

---

## 7. LOGISTICS DATA

### 7.1. Data Source

**File:** `app/static/js/data/logistics_data.js` hoặc từ API

**Structure:**
```javascript
{
  routes: {
    "vn_us": {
      name: "Vietnam → USA",
      name_vi: "Việt Nam → Mỹ",
      modes: ["SEA", "AIR"],
      defaultMode: "SEA",
      // ... route details
    },
    // ... more routes
  },
  cargoTypes: ["Electronics", "Textiles", "Furniture", ...],
  ports: [
    { code: "VNSGN", name: "Sai Gon", country: "VN", ... },
    // ... more ports
  ],
  carriers: ["Maersk", "MSC", "CMA CGM", ...],
  serviceRoutes: {
    "vn_us": {
      "SEA": [
        {
          id: "TP1",
          name: "Transpacific Express",
          transitTime: 30,
          reliability: 0.92,
          // ... more details
        }
      ]
    }
  }
}
```

### 7.2. Data Loading

- Load async từ file hoặc API
- Cache trong controller
- Pass to modules when ready
- Used for dropdowns, autocomplete, validation

**Code location:** `v20/utils/DataLoaders.js`

---

## 8. CSS & STYLING

### 8.1. CSS Files

**Main stylesheet:**
- `css/global_visionos.css` - Global VisionOS styles
- `css/pages/input/input_v20.css` - Input page specific styles

**Design System:**
- VisionOS-style (glass morphism, gradients, neon)
- Dark theme by default
- Light theme support
- Responsive design
- Smooth animations

### 8.2. Key Styles

- **Glass cards:** Backdrop blur, transparent backgrounds
- **Neon accents:** Cyan/purple gradients
- **Smooth transitions:** All interactions animated
- **Focus states:** Glow effects
- **Error states:** Red highlights
- **Success states:** Green indicators

---

## 9. API & BACKEND INTEGRATION

### 9.1. Backend Routes

- **GET /input_v20** - Render input page
- **POST /input_v20/submit** - Handle form submission (if needed)

### 9.2. Data Source

- **Primary:** `localStorage['RISKCAST_STATE']`
- **Logistics Data:** Static file hoặc API endpoint
- **No direct API calls** trong input page (state-based)

### 9.3. Next Step

- **After Continue:** Redirect to `/summary`
- Summary page reads from `RISKCAST_STATE`

---

## 10. ERROR HANDLING

### 10.1. State Loading Errors
- Nếu parse JSON fail → Use default state
- Console warning logged

### 10.2. Validation Errors
- Show error messages under fields
- Highlight error fields (red border)
- Prevent submission nếu có errors

### 10.3. API Errors (nếu có)
- Show toast notification
- Retry logic (nếu cần)

---

## 11. BROWSER COMPATIBILITY

### 11.1. Required Features
- `localStorage` API
- `JSON.parse/stringify`
- ES6+ (classes, arrow functions, const/let, template literals)
- CSS Grid, Flexbox
- Canvas API (for particles)
- Backdrop-filter (cho glass effect)

### 11.2. Browser Support
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (iOS 9+)
- IE11: Not supported (ES6 classes)

---

## 12. PERFORMANCE CONSIDERATIONS

### 12.1. Optimizations
- **Debouncing:** Input events debounced (250ms)
- **Lazy loading:** Logistics data loaded async
- **Event delegation:** Sử dụng event delegation
- **State caching:** State cached in memory
- **Particle optimization:** Limited particle count, requestAnimationFrame

### 12.2. State Size
- State thường < 20KB (JSON)
- localStorage limit: ~5-10MB (đủ)

---

## 13. TESTING CHECKLIST

### 13.1. Functional Tests
- [ ] Load state từ localStorage
- [ ] Save state to localStorage
- [ ] All fields render correctly
- [ ] Dropdowns work
- [ ] Autocomplete works
- [ ] Dynamic dependencies work (trade lane → mode → container)
- [ ] ETA calculation works
- [ ] Packing list add/remove works
- [ ] Validation works
- [ ] Submit redirects to summary
- [ ] Save draft saves state
- [ ] Demo auto-fill works

### 13.2. Edge Cases
- [ ] Empty state (no localStorage)
- [ ] Invalid JSON trong localStorage
- [ ] Missing logistics data
- [ ] Very long values
- [ ] Special characters
- [ ] Browser back/forward navigation

---

## 14. TÓM TẮT CHO AI

Trang Input là một **comprehensive data entry form** với các đặc điểm:

1. **Mục đích:** Nhập tất cả thông tin về lô hàng để phân tích risk
2. **Data source:** `localStorage['RISKCAST_STATE']`
3. **UI pattern:** VisionOS-style với glass morphism, dark theme
4. **Core features:**
   - 6 sections (Transport, Cargo, Seller, Buyer, Modules, Upload)
   - Dynamic field dependencies
   - Auto-suggest/autocomplete
   - Real-time validation
   - Packing list table
   - Auto-calculations (ETA, totals)
   - Risk modules toggle
   - File upload
5. **State management:** Client-side, localStorage-based với StateManager class
6. **Architecture:** Modular ES6 classes, separation of concerns
7. **Navigation:** Continue → Summary page

**Key files:**
- HTML: `app/templates/input/input_v20.html`
- Controller: `app/static/js/v20/core/RiskcastInputController.js`
- State: `app/static/js/v20/core/StateManager.js`
- Modules: `app/static/js/v20/modules/*.js`
- UI: `app/static/js/v20/ui/*.js`
- Effects: `app/static/js/v20/effects/*.js`

