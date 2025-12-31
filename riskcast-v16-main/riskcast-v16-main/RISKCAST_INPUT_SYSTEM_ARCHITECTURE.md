# RISKCAST v12 INPUT SYSTEM - COMPLETE TECHNICAL ARCHITECTURE

**Generated:** 2025-11-27  
**System:** RISKCAST v12 Enterprise Risk Assessment Platform  
**Primary File:** `app/templates/input.html` (3,474 lines)

---

## [1] HIGH-LEVEL ARCHITECTURE

### 1.1 System Overview
- **Type:** Single-Page Application (SPA) with enterprise-grade form management
- **Architecture Pattern:** Progressive Enhancement with Custom Dropdown System
- **Form Submission:** POST to `/api/run_risk` → Redirects to `/results`
- **State Management:** 
  - Hidden inputs for backend compatibility
  - `localStorage` for form data persistence
  - `window.appData` for results data
  - `dropdownState` object for dropdown state tracking

### 1.2 Core Components
```
┌─────────────────────────────────────────────────────────────┐
│                    ENTERPRISE LAYOUT CONTAINER              │
├──────────────┬──────────────────────────────┬───────────────┤
│ LEFT SIDEBAR │      MAIN CONTENT AREA       │ RIGHT AI PANEL│
│ (Fixed 280px)│   (Scrollable, Flexible)     │ (Fixed 320px) │
│              │                              │               │
│ Navigation   │  ┌────────────────────────┐  │ AI Completion │
│ Progress     │  │ Section 01: Transport  │  │ Progress      │
│ Indicators   │  │ Section 02: Cargo       │  │ Tracking      │
│              │  │ Section 03: Seller      │  │               │
│              │  │ Section 04: Buyer       │  │               │
│              │  │ Section 05: Algorithms  │  │               │
│              │  └────────────────────────┘  │               │
│              │                              │               │
│              │  ┌────────────────────────┐  │               │
│              │  │ Summary Section        │  │               │
│              │  │ (Real-time Updates)    │  │               │
│              │  └────────────────────────┘  │               │
└──────────────┴──────────────────────────────┴───────────────┘
```

### 1.3 File Structure
```
app/
├── templates/
│   └── input.html (3,474 lines) - Main form structure
├── static/
│   ├── css/
│   │   ├── enterprise_input_layout.css - Global layout
│   │   ├── transport_setup_refactor.css - Section 01 styles
│   │   ├── smart_input_styles.css - Smart input features
│   │   ├── packing_list.css - Packing table styles
│   │   ├── summary.css - Summary section styles
│   │   ├── input_inline.css - Base form styles
│   │   └── input.css - Legacy styles
│   └── js/
│       ├── input_form.js (3,770 lines) - Core form logic
│       ├── smart_input.js (2,674 lines) - Smart features
│       ├── enterprise_input.js - Enterprise layout logic
│       ├── packing_list.js - Packing table logic
│       ├── ai_adviser.js - Climate data updates
│       ├── summary.js - Summary updates
│       ├── input_summary_init.js - Summary initialization
│       └── premium_input_tracker.js - Progress tracking
```

### 1.4 Data Flow
```
USER INPUT
    ↓
Custom Dropdown Selection
    ↓
selectOption() → Updates hidden input + dropdownState
    ↓
Triggers: populateTransportModes() / populateDetailedRoutes() / populateCarriers()
    ↓
Updates dependent fields visibility
    ↓
updateInputSummary() → Updates summary section
    ↓
scheduleProgressUpdate() → Updates sidebar progress
    ↓
FORM SUBMISSION (runAnalysis())
    ↓
Collects all hidden inputs + visible inputs
    ↓
POST /api/run_risk
    ↓
Redirect to /results
```

---

## [2] SECTION-BY-SECTION STRUCTURE

### 2.1 SECTION 01: TRANSPORT SETUP (`#shipping-info` / `#section-transport`)

**Wrapper:** `<div class="enterprise-section-card" id="section-transport">`

#### Fields (2-column grid):
1. **Commercial Route** (`route_dropdown`)
   - ID: `route_dropdown`
   - Hidden: `route_input`
   - **CRITICAL:** Triggers `populateTransportModes()`
   - Options: vn_cn, vn_us, vn_kr, vn_jp, vn_eu, vn_hk, vn_in, vn_tw, domestic

2. **Transport Mode** (`transport_mode_dropdown`)
   - ID: `transport_mode_dropdown`
   - Hidden: `transport_mode_input`
   - Group: `transport_mode_group` (hidden by default, shown when route selected)
   - Menu: `transport_mode_menu` (dynamically populated)
   - **CRITICAL:** Triggers `populateDetailedRoutes()`

3. **Detailed Route** (`detailed_route_dropdown`)
   - ID: `detailed_route_dropdown`
   - Hidden: `detailed_route_input`
   - Group: `detailed_route_group` (hidden by default)
   - Menu: `detailed_route_menu` (dynamically populated)
   - **CRITICAL:** Shows `route_details_panel` with transit time, surcharge, climate risk
   - **CRITICAL:** Triggers `populateCarriersByRoute()`

4. **Carrier** (`carrier_dropdown`)
   - ID: `carrier_dropdown`
   - Hidden: `carrier_input`
   - Group: `carrier_group` (hidden by default)
   - Menu: `carrier_dropdown_menu` (dynamically populated)
   - **CRITICAL:** Shows carrier rating via `displayCarrierRating()`
   - **CRITICAL:** Updates `carrier_rating` hidden input

5. **POL** (`pol_dropdown`)
   - ID: `pol_dropdown`
   - Hidden: `pol_input`
   - Menu: `pol_menu` (dynamically populated based on transport mode)

6. **POD** (`pod_dropdown`)
   - ID: `pod_dropdown`
   - Hidden: `pod_input`
   - Menu: `pod_menu` (dynamically populated based on transport mode)

7. **ETD** (`shipment-month`)
   - ID: `shipment-month` (hidden, type="month")
   - Display: `shipment-month-display` (readonly text input)
   - **CRITICAL:** Triggers `updateClimateData()` in `ai_adviser.js`
   - **CRITICAL:** Updates climate section with ENSO, SST, typhoon data

8. **Distance** (`distance`)
   - ID: `distance`
   - **AUTO-FILLED:** Based on route selection
   - Readonly styling (green background)

9. **Transit Time** (`transit_time_display`)
   - ID: `transit_time_display` (readonly display)
   - Hidden: `transit_time`
   - **AUTO-CALCULATED:** Based on route + transport mode

10. **Cargo Type** (`cargo_type_dropdown`)
    - ID: `cargo_type_dropdown`
    - Hidden: `cargo_type_input`
    - **CRITICAL:** Affects container match calculation

11. **Incoterm** (`incoterm_dropdown`)
    - ID: `incoterm_dropdown`
    - Hidden: `incoterm_input`

12. **Container Type** (`container_dropdown`)
    - ID: `container_dropdown`
    - Hidden: `container_input`
    - **CRITICAL:** Affects container match calculation
    - Shows compatibility badges

13. **Packing Quality** (`packaging_dropdown`)
    - ID: `packaging_dropdown`
    - Hidden: `packaging_input`

14. **Priority Profile** (`priority_dropdown`)
    - ID: `priority_dropdown`
    - Hidden: `priority_input`
    - **CRITICAL:** Triggers `updatePriorityWeightsDisplay()`

#### Climate Risk Panel (`#climate-panel`):
- **Header:** Collapsible, calls `toggleClimate()`
- **Body:** `#climate-body` (hidden by default)
- **Elements:**
  - `#enso-value` - ENSO index display
  - `#storm-value` - Typhoon frequency
  - `#sst-value` - Sea surface temperature
  - `#climate-stress-value` - Climate stress score
  - `#climate-stress-badge` - Badge (good/warning/critical)
  - `#climate-stress-slider` - Visual slider (disabled)
- **Update Trigger:** `shipment-month` change → `updateClimateData()` in `ai_adviser.js`
- **Data Source:** `window.CLIMATE_DATA_2025.climate_data_2025.months[monthIdx]`

#### Priority Preview (`#priority-preview`):
- **Box:** `#priority_preview_box`
- **Displays:**
  - `#priority_speed_display` - Speed weight %
  - `#priority_cost_display` - Cost weight %
  - `#priority_risk_display` - Risk weight %
  - `#priority_description` - Profile description
- **Update Function:** `updatePriorityWeightsDisplay()` in `smart_input.js`
- **Trigger:** `priority_dropdown` change

#### Legacy Compatibility:
- `#climate-section` (display: none) - For JS compatibility

---

### 2.2 SECTION 02: CARGO & PACKING (`#cargo-details`)

**Wrapper:** `<div class="enterprise-section-card">`

#### Basic Info (2-column grid):
1. **ETD** (`etd`)
   - Type: date
   - Required

2. **ETA** (`eta`)
   - Type: date
   - Required

3. **Cargo Value** (`cargo_value`)
   - Type: number
   - Prefix: $
   - Suffix: USD
   - **CRITICAL:** Triggers packing calculations

#### Packing List Table:
- **Table:** `#packing-list-table`
- **Tbody:** `#packing-list-tbody` (dynamically populated)
- **Add Button:** `#add-packing-row`
- **Row Structure:**
  - STT (row number)
  - Description (`data-field="description"`)
  - Quantity (`data-field="quantity"`)
  - Packaging Type (`data-field="packaging_type"`)
  - Dimensions: Length, Width, Height (`data-field="length/width/height"`)
  - Weight (`data-field="weight"`)
  - Stackable (toggle switch)
  - Delete button

#### Auto-Calculation Panel (`#packing-calc-panel`):
- **Total Packages:** `#calc-total-packages`
- **Total Weight:** `#calc-total-weight`
- **Total Volume:** `#calc-total-volume`
- **Chargeable Weight:** `#calc-chargeable-weight`
- **Container Utilization:** `#calc-container-util` + `#util-progress-bar`
- **Packing Quality Score:** `#calc-packing-score`

#### Hidden Input:
- `#packages` (name="packages") - Total package count for backend

#### Dependencies:
- `packing_list.js` handles all calculations
- `updateCalculations()` called on any input change (debounced 300ms)
- `performCalculations()` aggregates all row data

---

### 2.3 SECTION 03: SELLER INFORMATION (`#seller-info`)

**Wrapper:** `<div class="enterprise-section-card">` (2-column grid)

#### Fields:
1. **Company Name** (`seller_name`)
2. **Country** (`seller_country_dropdown` → `seller_country_input`)
3. **Email** (`seller_email`)
4. **Phone** (`seller_phone`)
5. **Address** (`seller_address`)
6. **Contact Person** (`seller_pic`)
7. **Company Size** (`seller_size_dropdown` → `seller_size_input`)
8. **ESG Score** (`seller_esg`)

---

### 2.4 SECTION 04: BUYER INFORMATION (`#buyer-info`)

**Wrapper:** `<div class="enterprise-section-card">` (2-column grid)

#### Fields:
1. **Company Name** (`buyer_name`)
2. **Country** (`buyer_country_dropdown` → `buyer_country_input`)
3. **Email** (`buyer_email`)
4. **Phone** (`buyer_phone`)
5. **Address** (`buyer_address`)
6. **Contact Person** (`buyer_pic`)
7. **Company Size** (`buyer_size_dropdown` → `buyer_size_input`)
8. **ESG Score** (`buyer_esg`)

---

### 2.5 SECTION 05: ALGORITHM MODULES (`#algorithm-modules`)

**Wrapper:** `<div class="enterprise-section-card">` (2x2 grid)

#### Modules:
1. **Fuzzy AHP** (`use_fuzzy`)
   - Checkbox (checked by default)
   - Card: `data-module="fuzzy"`

2. **ARIMA Forecast** (`use_forecast`)
   - Checkbox (checked by default)
   - Card: `data-module="arima"`

3. **Monte Carlo** (`use_mc`)
   - Checkbox (checked by default)
   - Card: `data-module="monte-carlo"`

4. **VaR / CVaR** (`use_var`)
   - Checkbox (checked by default)
   - Card: `data-module="var"`

---

### 2.6 SUMMARY SECTION (`#input-summary-section`)

**Real-time updated summary of all form data**

#### Display Elements:
- `#input-summary-route` - Route
- `#input-summary-transport-mode` - Transport mode
- `#input-summary-pol-pod` - POL/POD
- `#input-summary-distance` - Distance
- `#input-summary-transit-time` - Transit time
- `#input-summary-cargo` - Cargo type
- `#input-summary-container` - Container type
- `#input-summary-incoterm` - Incoterm
- `#input-summary-packaging` - Packaging quality
- `#input-summary-container-match` - Container match score
- `#input-summary-carrier` - Carrier name
- `#input-summary-carrier-rating-stars` - Rating stars
- `#input-summary-packages` - Total packages
- `#input-summary-cargo-value` - Cargo value
- `#input-summary-etd` - ETD
- `#input-summary-eta` - ETA
- `#input-summary-seller` - Seller name
- `#input-summary-buyer` - Buyer name
- `#input-summary-enso` - ENSO index
- `#input-summary-storms` - Storm forecast
- `#input-summary-climate-stress` - Climate stress

**Update Function:** `updateInputSummary()` in `summary.js`
**Trigger:** Any form field change (debounced 100ms)

---

## [3] REQUIRED DOM IDs

### 3.1 CRITICAL IDs (MUST NOT CHANGE)

#### Form Submission IDs:
- `risk_form` - Main form element
- `transport_mode_input` - Hidden input for transport mode
- `cargo_type_input` - Hidden input for cargo type
- `route_input` - Hidden input for route
- `incoterm_input` - Hidden input for incoterm
- `container_input` - Hidden input for container
- `packaging_input` - Hidden input for packaging
- `priority_input` - Hidden input for priority profile
- `seller_country_input` - Hidden input for seller country
- `buyer_country_input` - Hidden input for buyer country
- `carrier_input` - Hidden input for carrier
- `pol_input` - Hidden input for POL
- `pod_input` - Hidden input for POD
- `detailed_route_input` - Hidden input for detailed route
- `transit_time` - Hidden input for transit time
- `packages` - Hidden input for total packages
- `distance` - Distance input (read by backend)
- `etd` - ETD date input
- `eta` - ETA date input
- `cargo_value` - Cargo value input
- `shipment-month` - Month input for climate data

#### Dropdown IDs:
- `route_dropdown` - Commercial route dropdown
- `transport_mode_dropdown` - Transport mode dropdown
- `detailed_route_dropdown` - Detailed route dropdown
- `carrier_dropdown` - Carrier dropdown
- `pol_dropdown` - POL dropdown
- `pod_dropdown` - POD dropdown
- `cargo_type_dropdown` - Cargo type dropdown
- `incoterm_dropdown` - Incoterm dropdown
- `container_dropdown` - Container dropdown
- `packaging_dropdown` - Packaging dropdown
- `priority_dropdown` - Priority dropdown
- `seller_country_dropdown` - Seller country dropdown
- `buyer_country_dropdown` - Buyer country dropdown

#### Group IDs (Visibility Control):
- `transport_mode_group` - Transport mode field group
- `detailed_route_group` - Detailed route field group
- `carrier_group` - Carrier field group

#### Climate Panel IDs:
- `climate-panel` - Climate panel container
- `climate-body` - Climate panel body (collapsible)
- `climate-section` - Legacy climate section (for JS compatibility)
- `enso-value` - ENSO index display
- `storm-value` - Storm frequency display
- `sst-value` - SST anomaly display
- `climate-stress-value` - Climate stress value
- `climate-stress-badge` - Climate stress badge
- `climate-stress-slider` - Climate stress slider

#### Priority Preview IDs:
- `priority-preview` - Priority preview container
- `priority_preview_box` - Priority preview box
- `priority_speed_display` - Speed weight display
- `priority_cost_display` - Cost weight display
- `priority_risk_display` - Risk weight display
- `priority_description` - Priority description

#### Packing List IDs:
- `packing-list-table` - Packing table
- `packing-list-tbody` - Packing table body
- `add-packing-row` - Add row button
- `calc-total-packages` - Total packages display
- `calc-total-weight` - Total weight display
- `calc-total-volume` - Total volume display
- `calc-chargeable-weight` - Chargeable weight display
- `calc-container-util` - Container utilization display
- `calc-packing-score` - Packing quality score

#### Algorithm Module IDs:
- `use_fuzzy` - Fuzzy AHP checkbox
- `use_forecast` - ARIMA forecast checkbox
- `use_mc` - Monte Carlo checkbox
- `use_var` - VaR/CVaR checkbox

#### Summary Section IDs:
All `#input-summary-*` IDs listed in Section 2.6

### 3.2 SAFE TO RENAME IDs

- Section wrapper IDs (e.g., `#shipping-info`, `#cargo-details`) - Only used for CSS/JS targeting
- Error message IDs (e.g., `#route_error`) - Only used for error display
- Display-only IDs (e.g., `#transit_time_display`) - Not submitted to backend
- UI enhancement IDs (e.g., `#carrier_rating_info`) - Visual only

---

## [4] JS DEPENDENCIES

### 4.1 Core Functions (input_form.js)

#### Dropdown Management:
- `initializeDropdowns()` - Sets up all custom dropdowns
- `selectOption(dropdownId, value, index)` - **CRITICAL** - Handles dropdown selection
- `populateTransportModes(routeValue)` - Populates transport modes based on route
- `populateDetailedRoutes(routeValue, transportMode)` - Populates detailed routes
- `populateCarriersByRoute(routeValue)` - Populates carriers
- `populatePOLPOD(transportMode)` - Populates POL/POD options
- `getDropdownValue(fieldName)` - Gets current dropdown value
- `closeDropdown(dropdownId)` - Closes dropdown menu
- `openDropdown(dropdownId)` - Opens dropdown menu

#### Field Dependencies:
```
route_dropdown selected
    ↓
populateTransportModes() → Shows transport_mode_group
    ↓
transport_mode_dropdown selected
    ↓
populateDetailedRoutes() → Shows detailed_route_group
    ↓
detailed_route_dropdown selected
    ↓
populateCarriersByRoute() → Shows carrier_group
    ↓
carrier_dropdown selected
    ↓
displayCarrierRating() → Updates carrier_rating hidden input
```

#### Form Submission:
- `runAnalysis()` - **CRITICAL** - Collects all form data and submits
- `validateForm()` - Validates required fields
- Collects data from hidden inputs (not dropdowns directly)

#### Auto-Calculation:
- `setupAutoCalculation()` - Sets up distance/transit time auto-fill
- `updateDistanceAndTransit()` - Updates distance and transit time based on route

### 4.2 Smart Input Functions (smart_input.js)

- `initializeSmartDefaults()` - Applies smart defaults
- `updateContainerMatch()` - Calculates container match score
- `updatePriorityWeightsDisplay()` - Updates priority preview
- `getPriorityWeights(profile)` - Returns weights for priority profile
- `applySmartDefaults()` - Applies defaults based on selections

### 4.3 Climate Data (ai_adviser.js)

- `updateClimateData()` - **CRITICAL** - Updates climate panel when month changes
- Triggered by: `shipment-month` change event
- Reads from: `window.CLIMATE_DATA_2025.climate_data_2025.months[monthIdx]`
- Updates: ENSO, SST, typhoon frequency, climate stress

### 4.4 Packing List (packing_list.js)

- `initPackingList()` - Initializes packing list
- `addPackingRow()` - Adds new row to packing table
- `updateCalculations()` - Debounced calculation trigger (300ms)
- `performCalculations()` - Performs actual calculations
- Updates: Total packages, weight, volume, chargeable weight, utilization, quality score

### 4.5 Summary Updates (summary.js)

- `updateInputSummary()` - **CRITICAL** - Updates all summary displays
- Triggered by: Any form field change (debounced 100ms)
- Reads from: All form inputs and dropdowns
- Updates: All `#input-summary-*` elements

### 4.6 Enterprise Layout (enterprise_input.js)

- `toggleClimate()` - Toggles climate panel expand/collapse
- `updateCompletion()` - Updates AI completion panel
- IntersectionObserver for sidebar highlighting

### 4.7 Global Event Listeners

#### setupGlobalChangeListeners() (input_form.js):
- Listens to all `change` and `input` events
- Triggers: `updateInputSummary()`, `scheduleProgressUpdate()`, `applySmartDefaults()`

#### Dropdown Change Chain:
```
selectOption() called
    ↓
Updates hidden input
    ↓
Triggers dependent field population
    ↓
Calls updateInputSummary()
    ↓
Calls scheduleProgressUpdate()
```

---

## [5] SAFE-TO-REFACTOR AREAS

### 5.1 CSS Classes
- `.enterprise-section-card` - Can be renamed/styled
- `.form-group` - Can be restyled (but keep structure)
- `.form-label` - Can be restyled
- `.custom-dropdown` - Can be restyled (but keep structure)
- Grid classes (`.grid`, `.grid-cols-2`) - Can be changed to inline styles

### 5.2 Visual Elements
- Section titles and subtitles
- Icons and emojis
- Badges and indicators (visual only)
- Spacing and padding
- Colors and themes
- Animations and transitions

### 5.3 Layout Structure
- Card wrappers (can add/remove)
- Grid layouts (can change columns)
- Responsive breakpoints
- Sidebar styling
- AI panel styling

### 5.4 Non-Critical IDs
- Error message containers
- Display-only elements
- UI enhancement elements
- Tooltip elements

---

## [6] DANGEROUS-TO-REFACTOR AREAS

### 6.1 CRITICAL - DO NOT CHANGE

#### Input IDs and Names:
- All `*_input` hidden inputs
- All `*_dropdown` IDs
- All form field `name` attributes
- All form field `id` attributes used in `runAnalysis()`

#### JavaScript Function Names:
- `selectOption()` - Called by dropdown system
- `runAnalysis()` - Called by submit button
- `updateInputSummary()` - Called by event listeners
- `updateClimateData()` - Called by month input
- `updatePriorityWeightsDisplay()` - Called by priority dropdown
- `addPackingRow()` - Called by add button
- `updateCalculations()` - Called by packing inputs
- `toggleClimate()` - Called by climate header

#### DOM Structure Requirements:
- `.custom-dropdown` structure (`.dropdown-trigger`, `.dropdown-value`, `.dropdown-menu`, `.dropdown-option`)
- Hidden input pattern: `{field}_input` for each dropdown
- Group visibility pattern: `{field}_group` for conditional fields
- Packing table structure: `#packing-list-tbody` with `data-field` attributes

#### Data Attributes:
- `data-value` on dropdown options
- `data-field` on packing table inputs
- `data-module` on algorithm cards

### 6.2 MODERATE RISK - Test Thoroughly

#### CSS Selectors Used in JS:
- `.dropdown-value` - Used to read/update dropdown display
- `.dropdown-option` - Used to find options
- `.form-input` - Used for validation
- `.error-message` - Used for error display

#### Event Listeners:
- `change` events on all inputs
- `input` events on number inputs
- `click` events on dropdown triggers

---

## [7] STYLING SYSTEM

### 7.1 CSS Architecture

#### Base Styles (input_inline.css):
- Form input styles
- Label styles
- Error message styles
- Focus states

#### Enterprise Layout (enterprise_input_layout.css):
- 2-column layout system
- Sidebar styles
- AI panel styles
- Section card styles

#### Transport Setup (transport_setup_refactor.css):
- Section 01 specific styles
- 2-column grid
- Climate panel styles
- Priority preview styles

#### Smart Input (smart_input_styles.css):
- Smart input features
- Badge styles
- Suggestion panel styles

#### Packing List (packing_list.css):
- Table styles
- Calculation panel styles
- Row styles

### 7.2 Design Tokens

#### Colors:
- Primary: `#00ff88` (neon green)
- Background: `rgba(13, 17, 23, 0.6)` (dark translucent)
- Border: `#1f2937` (dark gray)
- Text Primary: `#ffffff`
- Text Secondary: `rgba(255, 255, 255, 0.6)`

#### Spacing:
- Section padding: `32px`
- Grid gap: `24px 32px`
- Label margin-bottom: `4px`
- Input height: `48px`

#### Typography:
- Section title: `22px`, `700` weight
- Subtitle: `13px`
- Label: `14px`, `600` weight

### 7.3 Responsive Breakpoints

- Desktop: Default (2-column grid)
- Tablet: `@media (max-width: 1024px)` - 1 column
- Mobile: `@media (max-width: 768px)` - Stack cards, hide AI panel

---

## [8] UI/UX PROBLEMS

### 8.1 Current Issues

1. **Text Overflow:** Section titles can overflow vertically (fixed with `writing-mode: horizontal-tb`)
2. **Alignment:** Labels and inputs not consistently aligned (fixed with inline styles)
3. **Spacing:** Inconsistent vertical spacing (fixed with grid gap)
4. **Climate Panel:** Hidden by default, not discoverable
5. **Priority Preview:** Opacity 0.5 makes it hard to read
6. **Packing Table:** Can become very long, no pagination
7. **Summary Section:** Large, takes up significant space

### 8.2 Known Limitations

- No form validation on blur (only on submit)
- No auto-save functionality
- No undo/redo for packing list
- Climate data only for 2025
- No real-time API for climate data (uses static JSON)

---

## [9] RECOMMENDED RESTRUCTURE MODEL

### 9.1 Proposed Improvements

#### Component-Based Structure:
```
<section id="transport-setup">
  <TransportSetupCard>
    <FormGrid columns={2}>
      <RouteSelector />
      <TransportModeSelector />
      <DetailedRouteSelector />
      <CarrierSelector />
      <POLSelector />
      <PODSelector />
      <ETDSelector />
      <DistanceDisplay />
      <TransitTimeDisplay />
      <CargoTypeSelector />
      <IncotermSelector />
      <ContainerSelector />
      <PackingQualitySelector />
      <PrioritySelector />
    </FormGrid>
    <ClimateRiskPanel collapsible />
    <PriorityPreview />
  </TransportSetupCard>
</section>
```

#### State Management:
- Use a state object instead of hidden inputs
- Single source of truth for form data
- Reactive updates to all dependent fields

#### Validation:
- Real-time validation on blur
- Visual indicators for required fields
- Error messages inline

#### Performance:
- Debounce all calculations
- Lazy load climate data
- Virtual scrolling for packing table if > 50 rows

### 9.2 Migration Strategy

1. **Phase 1:** Keep all IDs and functions, refactor CSS only
2. **Phase 2:** Refactor HTML structure, keep JS functions
3. **Phase 3:** Refactor JS to use new structure
4. **Phase 4:** Add new features (auto-save, validation, etc.)

---

## APPENDIX: COMPLETE ID REFERENCE

### Form Inputs (Backend Submission):
- `transport_mode_input`, `cargo_type_input`, `route_input`, `incoterm_input`, `container_input`, `packaging_input`, `priority_input`, `seller_country_input`, `buyer_country_input`, `carrier_input`, `pol_input`, `pod_input`, `detailed_route_input`, `transit_time`, `packages`, `distance`, `etd`, `eta`, `cargo_value`, `shipment-month`, `seller_name`, `seller_email`, `seller_phone`, `seller_address`, `seller_pic`, `seller_size_input`, `seller_esg`, `buyer_name`, `buyer_email`, `buyer_phone`, `buyer_address`, `buyer_pic`, `buyer_size_input`, `buyer_esg`, `use_fuzzy`, `use_forecast`, `use_mc`, `use_var`

### Dropdowns:
- `route_dropdown`, `transport_mode_dropdown`, `detailed_route_dropdown`, `carrier_dropdown`, `pol_dropdown`, `pod_dropdown`, `cargo_type_dropdown`, `incoterm_dropdown`, `container_dropdown`, `packaging_dropdown`, `priority_dropdown`, `seller_country_dropdown`, `buyer_country_dropdown`

### Display Elements:
- `transit_time_display`, `shipment-month-display`, `priority_speed_display`, `priority_cost_display`, `priority_risk_display`, `priority_description`, `calc-total-packages`, `calc-total-weight`, `calc-total-volume`, `calc-chargeable-weight`, `calc-container-util`, `calc-packing-score`

### Groups:
- `transport_mode_group`, `detailed_route_group`, `carrier_group`

### Panels:
- `climate-panel`, `climate-body`, `priority-preview`, `priority_preview_box`, `route_details_panel`, `packing-calc-panel`

---

**END OF DOCUMENT**

