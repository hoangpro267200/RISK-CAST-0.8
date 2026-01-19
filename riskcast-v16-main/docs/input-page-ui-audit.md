# UI AUDIT REPORT: INPUT PAGE v20
## RISKCAST v16 - VisionOS Edition

**Date:** 2024  
**Auditor:** Product Designer + Senior Frontend Engineer  
**Template Version:** `input_v20.html`  
**CSS Version:** `input_v20.css`  
**Controller:** `RiskcastInputController.js` (v20.3)

---

## (1) OVERVIEW

### Mục tiêu trang Input hiện tại
Trang Input v20 là **entry point** của workflow RISKCAST, nơi người dùng nhập toàn bộ thông tin shipment để hệ thống phân tích rủi ro. 

**Primary CTA:** "Run Risk Analysis" (button `#rc-btn-submit`) → submit form → redirect `/overview` (Summary page)

**User Intent:**
- Nhập thông tin shipment đầy đủ (Transport, Cargo, Parties, Risk Modules)
- Xem preview/validation real-time
- Lưu draft để tiếp tục sau
- Submit để chạy AI risk analysis

### Fit với Summary/Results
**Hiện tại:**
- ✅ Cùng design system: VisionOS glassmorphism (`rc-glass-card`, `backdrop-filter: blur(40px)`)
- ✅ Cùng color tokens: neon primary (`#00ffcc`), accent (`#00d4ff`)
- ✅ Cùng typography: Inter body, Orbitron display
- ❌ **MISMATCH:** Input dùng `rc-form-panel` với glow effects phức tạp, Summary/Results dùng `visionos-card` đơn giản hơn
- ❌ **MISMATCH:** Input layout 1-column centered (max-width 900px), Summary/Results dùng 12-col grid với sidebar
- ❌ **MISMATCH:** Input không có live preview panel như Summary/Results
- ❌ **MISMATCH:** Input submit → redirect, không có "completeness meter" hay "what you'll get" preview

**Kết luận:** Input page có visual style tương đồng nhưng **thiếu decision-first UX** và **progressive disclosure** so với Summary/Results.

---

## (2) INFORMATION ARCHITECTURE (IA) & FORM SECTIONS

### Cấu trúc tổng thể

```
Page: Input v20
├── Header (Fixed, 70px height)
│   ├── Logo + Status
│   └── Theme toggle + Notifications + Avatar
├── Sidebar (Fixed, 280px width, left)
│   ├── Navigation (6 sections)
│   └── Save Draft button
└── Main Content (margin-left: 280px)
    └── Form Container (max-width: 900px, centered)
        ├── Section 01: Transport Setup (Required)
        ├── Section 02: Cargo & Packing (Required)
        ├── Section 03: Seller Details
        ├── Section 04: Buyer Details
        ├── Section 05: Risk Analysis Modules
        ├── Section 06: Upload Packing List
        └── Submit Footer (Sticky bottom)
```

### Chi tiết từng Section

#### **SECTION 01: TRANSPORT SETUP** (`#section-transport`)
**Class:** `rc-form-panel rc-section-primary`  
**Required:** Yes (badge `rc-pill-required`)

**Fields (theo thứ tự trong template):**
1. **Trade Lane** (`tradeLane`)
   - Type: Dropdown (searchable)
   - Required: Yes
   - Default: "Select trade lane"
   - Dependencies: Khi chọn → filter `mode` options

2. **Mode of Transport** (`mode`)
   - Type: Dropdown
   - Required: Yes
   - Default: "Select mode"
   - Dependencies: Phụ thuộc `tradeLane`

3. **Shipment Type** (`shipmentType`)
   - Type: Dropdown
   - Required: Yes
   - Default: "Select shipment type"
   - Dependencies: Phụ thuộc `mode`

4. **Service Route** (`serviceRoute`)
   - Type: Dropdown (searchable)
   - Required: Yes
   - Default: "Select service route"
   - Dependencies: Phụ thuộc `mode` + `priority`

5. **Carrier** (`carrier`)
   - Type: Dropdown
   - Required: No
   - Default: "Select carrier"
   - Dependencies: Phụ thuộc `serviceRoute`

6. **Priority Selection** (`priority`)
   - Type: Pill group (4 buttons)
   - Required: No
   - Default: "balanced" (active)
   - Options: `fastest`, `balanced`, `cheapest`, `reliable`
   - Dependencies: Filter `serviceRoute` options

7. **Incoterm® 2020** (`incoterm`)
   - Type: Dropdown
   - Required: No
   - Default: "Select Incoterm"
   - Dependencies: None

8. **Incoterm Location** (`incotermLocation`)
   - Type: Text input
   - Required: No
   - Default: Empty
   - Placeholder: "e.g., Shanghai, Los Angeles, Rotterdam"

9. **POL (Port of Loading)** (`pol`)
   - Type: Autosuggest
   - Required: Yes
   - Default: Empty
   - Placeholder: "e.g., LAX, Shanghai..."
   - Dependencies: Auto-filled từ `serviceRoute` nếu có

10. **POD (Port of Discharge)** (`pod`)
    - Type: Autosuggest
    - Required: Yes
    - Default: Empty
    - Placeholder: "e.g., Rotterdam, Dubai..."
    - Dependencies: Auto-filled từ `serviceRoute` nếu có

11. **Container Type** (`containerType`)
    - Type: Dropdown
    - Required: No
    - Default: "Select container"
    - Dependencies: None

12. **ETD (Estimated Departure)** (`etd`)
    - Type: Date input
    - Required: No
    - Default: Empty
    - Dependencies: Dùng để tính `eta` (auto-filled)

13. **Schedule Frequency** (`schedule`)
    - Type: Text input (readonly, disabled)
    - Required: No
    - Default: "Auto-filled"
    - Dependencies: Từ `serviceRoute` data

14. **Transit Time (days)** (`transitDays`)
    - Type: Number input (readonly, disabled)
    - Required: No
    - Default: "Auto-filled"
    - Dependencies: Từ `serviceRoute` data

15. **ETA (Estimated Arrival)** (`eta`)
    - Type: Date input (readonly, disabled)
    - Required: No
    - Default: Empty
    - Dependencies: Calculated từ `etd` + `transitDays`

16. **Reliability Score** (`reliabilityScore`)
    - Type: Text input (readonly, disabled)
    - Required: No
    - Default: "Auto-filled"
    - Dependencies: Từ `serviceRoute` data

**Layout:** 2-column grid (`rc-form-grid`), mỗi field chiếm 1 column, một số field `rc-span-2` (full width).

---

#### **SECTION 02: CARGO & PACKING** (`#section-cargo`)
**Class:** `rc-form-panel`  
**Required:** Yes (badge `rc-pill-required`)  
**Template:** `partials/_v20_cargo_section.html`

**Fields:**
1. **Cargo Type** (`cargoType`) - Dropdown, Required
2. **HS Code** (`hsCode`) - Text input, Optional
3. **Packing Type** (`packingType`) - Dropdown, Required
4. **Number of Packages** (`packageCount`) - Number input, Optional
5. **Gross Weight (kg)** (`grossWeight`) - Number input, Required
6. **Net Weight (kg)** (`netWeight`) - Number input, Optional
7. **Volume (m³)** (`volumeCbm`) - Number input (step 0.01), Optional
8. **Stackability** (`stackable`) - Pill group (2 options: `true`/`false`), Default: `true`
9. **Insurance Value (USD)** (`insuranceValue`) - Number input, Required
10. **Insurance Coverage** (`insuranceCoverage`) - Dropdown, Optional
11. **Cargo Sensitivity** (`cargoSensitivity`) - Pill group (4 options: `standard`, `fragile`, `temperature`, `high_value`), Default: `standard`, Full width
12. **Min Temperature (°C)** (`tempMin`) - Number input, Conditional (hiện khi `cargoSensitivity === "temperature"`)
13. **Max Temperature (°C)** (`tempMax`) - Number input, Conditional
14. **Dangerous Goods (DG)** (`dangerousGoods`) - Pill group (2 options: `false`/`true`), Default: `false`, Full width
15. **UN Number** (`dgUnNumber`) - Text input, Conditional (hiện khi `dangerousGoods === true`)
16. **DG Class** (`dgClass`) - Dropdown, Conditional
17. **Packing Group** (`dgPackingGroup`) - Dropdown, Conditional
18. **Loadability Issues** (`loadabilityIssues`) - Toggle checkbox, Optional, Full width
19. **Cargo Description** (`cargoDescription`) - Textarea (3 rows), Optional, Full width
20. **Special Handling Instructions** (`specialHandling`) - Textarea (2 rows), Optional, Full width

**Layout:** 2-column grid, conditional fields ẩn/hiện bằng `style="display: none"`.

---

#### **SECTION 03: SELLER DETAILS** (`#section-seller`)
**Class:** `rc-form-panel`  
**Required:** No (nhưng một số field có `*` required)  
**Template:** `partials/_v20_seller_section.html`

**Fields:**
1. **Company Name** (`sellerCompany`) - Text input, Required (`*`)
2. **Business Type** (`sellerBusinessType`) - Dropdown, Optional
3. **Country** (`sellerCountry`) - Dropdown (searchable), Required (`*`)
4. **City** (`sellerCity`) - Text input, Optional
5. **Address** (`sellerAddress`) - Text input, Optional, Full width
6. **Contact Person** (`sellerContact`) - Text input, Optional
7. **Contact Role** (`sellerContactRole`) - Text input, Optional
8. **Email** (`sellerEmail`) - Email input, Optional
9. **Phone** (`sellerPhone`) - Tel input, Optional
10. **Tax ID / VAT** (`sellerTaxId`) - Text input, Optional

**Layout:** 2-column grid.

---

#### **SECTION 04: BUYER DETAILS** (`#section-buyer`)
**Class:** `rc-form-panel`  
**Required:** No (nhưng một số field có `*` required)  
**Template:** `partials/_v20_buyer_section.html`

**Fields:** (Tương tự Seller, prefix `buyer` thay vì `seller`)
1. **Company Name** (`buyerCompany`) - Text input, Required (`*`)
2. **Business Type** (`buyerBusinessType`) - Dropdown, Optional
3. **Country** (`buyerCountry`) - Dropdown (searchable), Required (`*`)
4. **City** (`buyerCity`) - Text input, Optional
5. **Address** (`buyerAddress`) - Text input, Optional, Full width
6. **Contact Person** (`buyerContact`) - Text input, Optional
7. **Contact Role** (`buyerContactRole`) - Text input, Optional
8. **Email** (`buyerEmail`) - Email input, Optional
9. **Phone** (`buyerPhone`) - Tel input, Optional
10. **Tax ID / VAT** (`buyerTaxId`) - Text input, Optional

**Layout:** 2-column grid.

---

#### **SECTION 05: RISK ANALYSIS MODULES** (`#section-modules`)
**Class:** `rc-form-panel`  
**Required:** No (tất cả optional, default: checked)

**Fields:** 6 module cards với toggle switch (custom sparkle animation)
1. **ESG Risk** (`moduleESG`) - Checkbox, Default: checked
2. **Weather & Climate Risk** (`moduleWeather`) - Checkbox, Default: checked
3. **Port Congestion Risk** (`modulePortCongestion`) - Checkbox, Default: checked
4. **Carrier Performance** (`moduleCarrier`) - Checkbox, Default: checked
5. **Market Condition Scanner** (`moduleMarket`) - Checkbox, Default: checked
6. **Insurance Optimization** (`moduleInsurance`) - Checkbox, Default: checked

**Layout:** 2-column grid (`rc-modules-grid`).

---

#### **SECTION 06: UPLOAD PACKING LIST** (`#section-upload`)
**Class:** `rc-form-panel`  
**Required:** No

**Fields:**
1. **File Upload** (`rc-file-input`) - File input (hidden), Accept: `.pdf,.xlsx,.xls,.csv`
   - Drag & drop zone
   - Preview khi upload thành công

**Layout:** Full width upload zone (min-height 300px).

---

### Tree Outline

```
Input Page
├── Header (Fixed)
│   ├── Logo + Status
│   └── Actions
├── Sidebar (Fixed, 280px)
│   ├── Nav: Transport, Cargo, Seller, Buyer, Modules, Upload
│   └── Save Draft
└── Main (Centered, max-width 900px)
    ├── Section 01: Transport Setup (Required)
    │   ├── Trade Lane (dropdown)
    │   ├── Mode (dropdown)
    │   ├── Shipment Type (dropdown)
    │   ├── Service Route (dropdown)
    │   ├── Carrier (dropdown)
    │   ├── Priority (pills: 4 options)
    │   ├── Incoterm (dropdown)
    │   ├── Incoterm Location (text)
    │   ├── POL (autosuggest)
    │   ├── POD (autosuggest)
    │   ├── Container Type (dropdown)
    │   ├── ETD (date)
    │   ├── Schedule (readonly)
    │   ├── Transit Time (readonly)
    │   ├── ETA (readonly)
    │   └── Reliability Score (readonly)
    ├── Section 02: Cargo & Packing (Required)
    │   ├── Cargo Type (dropdown)
    │   ├── HS Code (text)
    │   ├── Packing Type (dropdown)
    │   ├── Number of Packages (number)
    │   ├── Gross Weight (number)
    │   ├── Net Weight (number)
    │   ├── Volume (number)
    │   ├── Stackability (pills: 2 options)
    │   ├── Insurance Value (number)
    │   ├── Insurance Coverage (dropdown)
    │   ├── Cargo Sensitivity (pills: 4 options)
    │   ├── Temperature Range (conditional, 2 fields)
    │   ├── Dangerous Goods (pills: 2 options)
    │   ├── DG Details (conditional, 3 fields)
    │   ├── Loadability Issues (toggle)
    │   ├── Cargo Description (textarea)
    │   └── Special Handling (textarea)
    ├── Section 03: Seller Details
    │   ├── Company Name (text, required)
    │   ├── Business Type (dropdown)
    │   ├── Country (dropdown, required)
    │   ├── City (text)
    │   ├── Address (text, full width)
    │   ├── Contact Person (text)
    │   ├── Contact Role (text)
    │   ├── Email (email)
    │   ├── Phone (tel)
    │   └── Tax ID (text)
    ├── Section 04: Buyer Details
    │   └── (Tương tự Seller, 10 fields)
    ├── Section 05: Risk Modules
    │   └── 6 module toggles (grid 2x3)
    ├── Section 06: Upload
    │   └── File upload zone
    └── Submit Footer (Sticky)
        └── "Run Risk Analysis" button
```

---

## (3) LAYOUT & GRID (ĐO ĐẠC BỐ CỤC)

### Desktop Layout (>1024px)

**Viewport Structure:**
- **Header:** Fixed top, height `70px`, full width, z-index 1000
- **Sidebar:** Fixed left, width `280px`, height `calc(100vh - 70px)`, z-index 900
- **Main Content:** `margin-left: 280px`, `margin-top: 70px`, padding `1rem 3rem`
- **Form Container:** `max-width: 900px`, `margin: 0 auto`, centered

**Form Grid:**
- **Container:** `.rc-form-container` - flex column, gap `3rem` (48px)
- **Form Grid:** `.rc-form-grid` - CSS Grid `grid-template-columns: repeat(2, 1fr)`, gap `2rem` (32px)
- **Field:** `.rc-form-field` - flex column, gap `0.5rem` (8px)
- **Full-width fields:** `.rc-span-2` - `grid-column: span 2`

**Card Style:**
- **Glass Card:** `.rc-glass-card`
  - Background: `rgba(255, 255, 255, 0.7)` (light) / `rgba(17, 24, 39, 0.6)` (dark)
  - Backdrop filter: `blur(40px)`
  - Border: `1px solid rgba(0, 0, 0, 0.08)` / `rgba(255, 255, 255, 0.08)`
  - Border radius: `24px`
  - Padding: `3rem` (48px)
  - Box shadow: `0 16px 64px rgba(0, 0, 0, 0.1)` (light) / `0 16px 64px rgba(0, 0, 0, 0.7)` (dark)

**Section Header:**
- **Height:** Auto (flex)
- **Gap:** `1.5rem` (24px)
- **Icon:** `56px × 56px` (primary section: `64px × 64px`)
- **Title:** Font size `1.75rem` (primary: `2rem`), Orbitron font
- **Description:** Font size `0.9375rem`, color secondary

**Input Fields:**
- **Wrapper:** `.rc-input-wrapper`
  - Height: Auto (padding `0.875rem 0` + border)
  - Border: `1.5px solid var(--rc-border-color)`
  - Border radius: `12px`
  - Padding: `0 1rem`
  - Background: `rgba(255, 255, 255, 0.03)`
- **Focus state:** Border `var(--rc-neon-primary)`, box-shadow `0 0 0 3px rgba(0, 255, 204, 0.1)`

**Submit Footer:**
- **Position:** Sticky bottom, `left: 280px`, `right: 0`
- **Background:** Glass với blur `30px`
- **Padding:** `2rem 3rem`
- **Button:** Primary gradient, padding `1rem 2rem`, font size `1rem`

### Responsive Breakpoints

**@media (max-width: 1024px):**
- Sidebar: `transform: translateX(-100%)` (hidden), toggle button hiện
- Main: `margin-left: 0`, padding `1rem`
- Submit footer: `left: 0`
- Form grid: `grid-template-columns: 1fr` (1 column)
- Modules grid: `grid-template-columns: 1fr`

**@media (max-width: 640px):**
- Header padding: `0 1rem`
- Main padding: `2rem 1rem`
- Form container: `max-width: 100%`
- Footer content: `flex-direction: column`
- Section title (primary): `1.25rem`

### Layout Classes Reference

**Container:**
- `.rc-form-container` - max-width 900px, centered, flex column
- `.rc-main-v20` - main wrapper với margin-left cho sidebar

**Grid:**
- `.rc-form-grid` - 2-column grid, gap 32px
- `.rc-modules-grid` - 2-column grid cho modules
- `.rc-form-field.rc-span-2` - full width field

**Card:**
- `.rc-glass-card` - glassmorphic card với blur
- `.rc-form-panel` - section wrapper với glow effects

---

## (4) VISUAL SYSTEM (TOKENS / TYPOGRAPHY / SPACING / COLORS)

### Typography

**Font Families:**
- **Body:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` (CSS var: `--rc-font-body`)
- **Display:** `'Orbitron', monospace` (CSS var: `--rc-font-display`)

**Font Sizes (từ CSS):**
- **H1 (Section Primary):** `2rem` (32px), font-weight 800, Orbitron
- **H2 (Section Title):** `1.75rem` (28px), font-weight 700, Orbitron
- **Body:** `0.9375rem` (15px), line-height 1.6, Inter
- **Label:** `0.875rem` (14px), font-weight 600
- **Hint/Caption:** `0.8125rem` (13px), color tertiary
- **Button:** `0.9375rem` (15px), font-weight 600
- **Button Large:** `1rem` (16px)

**Typography Issues:**
- ❌ **Không có typography scale nhất quán:** Mix giữa rem và px, không có design tokens rõ ràng
- ❌ **Line-height không consistent:** Body 1.6, nhưng một số text khác không set
- ❌ **Font-weight hierarchy yếu:** Chỉ có 600, 700, 800, thiếu 400, 500 cho body text
- ❌ **Khác Summary/Results:** Summary dùng `--font-h1: 32px/1.15`, `--font-h2: 24px/1.2` (tokens.css), Input không dùng tokens này

### Spacing Scale

**CSS Variables (từ input_v20.css):**
- `--rc-spacing-xs: 0.25rem` (4px)
- `--rc-spacing-sm: 0.5rem` (8px)
- `--rc-spacing-md: 1rem` (16px)
- `--rc-spacing-lg: 1.5rem` (24px)
- `--rc-spacing-xl: 2rem` (32px)
- `--rc-spacing-2xl: 3rem` (48px)
- `--rc-spacing-3xl: 4rem` (64px)

**Usage Patterns:**
- Form container gap: `3rem` (48px)
- Form grid gap: `2rem` (32px)
- Field gap: `0.5rem` (8px)
- Section header gap: `1.5rem` (24px)
- Card padding: `3rem` (48px)

**Spacing Issues:**
- ✅ **Có spacing scale:** Nhưng không dùng tokens từ `tokens.css` (`--space-4`, `--space-8`, etc.)
- ❌ **Khác Summary/Results:** Summary dùng `--space-16`, `--space-24`, `--space-32` từ tokens.css, Input dùng custom `--rc-spacing-*`
- ⚠️ **Inconsistent:** Một số chỗ hardcode `padding: 22px 26px` thay vì dùng tokens

### Color Palette

**Light Theme (từ input_v20.css):**
- Background primary: `#f5f7fa`
- Background secondary: `#ffffff`
- Background glass: `rgba(255, 255, 255, 0.7)`
- Text primary: `#1a202c`
- Text secondary: `#718096`
- Text tertiary: `#a0aec0`
- Border: `rgba(0, 0, 0, 0.08)`

**Dark Theme:**
- Background primary: `#0a0e1a`
- Background secondary: `#111827`
- Background glass: `rgba(17, 24, 39, 0.6)`
- Text primary: `#f9fafb`
- Text secondary: `#d1d5db`
- Text tertiary: `#9ca3af`
- Border: `rgba(255, 255, 255, 0.08)`

**Neon Accents:**
- Primary: `#00ffcc` (`--rc-neon-primary`)
- Secondary: `#00d4ff` (`--rc-neon-secondary`)
- Accent: `#7c3aed` (`--rc-neon-accent`)
- Glow: `rgba(0, 255, 204, 0.6)` (`--rc-neon-glow`)

**Status Colors:**
- Error: `#ef4444` (hardcoded, không có token)
- Success: Không có token rõ ràng
- Warning: Không có token rõ ràng

**Color Issues:**
- ❌ **Không dùng tokens từ tokens.css:** Summary/Results dùng `--color-primary-neon: #6ef3ff`, `--color-bg-1`, `--text-strong`, Input dùng custom `--rc-neon-primary`, `--rc-bg-primary`
- ❌ **Status colors thiếu:** Chỉ có error color hardcoded, không có success/warning/info tokens
- ❌ **Inconsistent naming:** Input dùng `--rc-text-primary`, tokens.css dùng `--text-strong`, `--text-muted`

### Design Tokens Mismatch với Summary/Results

**Summary/Results dùng (tokens.css):**
```css
--color-primary-neon: #6ef3ff;
--color-bg-1: rgba(16, 21, 35, 0.82);
--text-strong: #f7fbff;
--text-muted: #c7d2e2;
--font-h1: 32px/1.15;
--font-h2: 24px/1.2;
--space-16: 16px;
--space-24: 24px;
--radius-24: 24px;
```

**Input v20 dùng (input_v20.css):**
```css
--rc-neon-primary: #00ffcc;  /* Khác #6ef3ff */
--rc-bg-primary: #0a0e1a;     /* Khác rgba(16, 21, 35, 0.82) */
--rc-text-primary: #f9fafb;   /* Tương đương --text-strong */
--rc-spacing-md: 1rem;        /* Tương đương --space-16 */
```

**Kết luận:** Input page **KHÔNG đồng bộ** với design tokens của Summary/Results, cần migrate sang tokens.css.

---

## (5) COMPONENT AUDIT (INPUTS, BUTTONS, DROPDOWNS, STATES)

### Input Components

#### **Text Inputs**
**Class:** `.rc-input` trong `.rc-input-wrapper`

**Style:**
- Height: Auto (padding `0.875rem 0`)
- Border: `1.5px solid var(--rc-border-color)`
- Border radius: `12px`
- Background: `rgba(255, 255, 255, 0.03)`
- Padding: `0 1rem` (wrapper), `0.875rem 0` (input)
- Font: Inter, `0.9375rem`
- Icon: `18px × 18px`, color tertiary, left side

**Focus State:**
- Border: `var(--rc-neon-primary)`
- Background: `rgba(255, 255, 255, 0.05)`
- Box shadow: `0 0 0 3px rgba(0, 255, 204, 0.1), 0 0 20px rgba(0, 255, 204, 0.2)`
- Left border accent: `3px solid var(--rc-neon-primary)` (pseudo `::before`)

**Disabled State:**
- Opacity: `0.6`
- Cursor: `not-allowed`
- Background: Không đổi

**Issues:**
- ✅ Focus ring rõ ràng
- ❌ **Không có error state styling riêng** (chỉ có class `.rc-input-error` nhưng style minimal)
- ❌ **Không có success state**
- ❌ **Placeholder color:** `var(--rc-text-tertiary)` - có thể không đủ contrast

#### **Dropdowns**
**Class:** `.rc-dropdown-v20`

**Structure:**
- Trigger: `.rc-dropdown-trigger` - button với flex layout
- Menu: `.rc-dropdown-menu` - absolute positioned, glass background
- Items: `.rc-dropdown-item` - padding `0.5rem 1rem`

**Style:**
- Trigger height: Auto (padding `0.875rem 1rem`)
- Border: `1.5px solid var(--rc-border-color)`
- Border radius: `12px`
- Background: `rgba(255, 255, 255, 0.03)`
- Arrow: Chevron down icon, rotates 180deg khi active

**Menu:**
- Background: `var(--rc-bg-glass)` với `blur(40px)`
- Border: `1px solid var(--rc-border-color)`
- Border radius: `16px`
- Box shadow: `var(--rc-shadow-xl)`
- Max height: `300px`, scrollable
- Animation: Fade in + scale up (`translateY(-10px) scale(0.95)` → `translateY(0) scale(1)`)

**Search (nếu có):**
- Input trong `.rc-dropdown-search`
- Background: `rgba(255, 255, 255, 0.05)`
- Border: `1px solid var(--rc-border-color)`
- Border radius: `10px`

**Issues:**
- ✅ Animation smooth
- ❌ **Không có keyboard navigation** (arrow keys, Enter, Escape)
- ❌ **Không có "no results" state**
- ❌ **Selected item styling:** Chỉ có `.selected` class, nhưng không có visual indicator rõ ràng

#### **Autosuggest (POL/POD)**
**Class:** `.rc-autosuggest`

**Structure:**
- Input: `.rc-input` trong `.rc-input-wrapper`
- Menu: `.rc-suggest-menu` - absolute, hiện khi type

**Style:**
- Tương tự dropdown menu
- Max height: `250px`
- Highlight: `<mark>` tag với background `var(--rc-neon-primary)`

**Issues:**
- ❌ **Không có debounce** (có thể gọi API quá nhiều)
- ❌ **Không có loading state** khi search
- ❌ **Không có "no results" message**

#### **Date Inputs**
**Type:** `<input type="date">`

**Style:**
- Tương tự text input
- Icon: Calendar icon (`data-lucide="calendar"`)

**Issues:**
- ❌ **Browser default date picker** - không consistent cross-browser
- ❌ **Không có custom date picker** (như Summary/Results có thể có)

#### **Number Inputs**
**Type:** `<input type="number">`

**Style:**
- Tương tự text input
- Step: `0.01` cho volume, `1` cho packages/weight

**Issues:**
- ❌ **Không có unit display** (kg, m³) - chỉ có trong label/hint
- ❌ **Không có min/max validation** visual
- ❌ **Spinner arrows** (browser default) - không styled

#### **Pill Groups**
**Class:** `.rc-pill-group`

**Structure:**
- Container: Flex wrap, gap `0.5rem`
- Pill: `.rc-pill` - button với flex layout

**Style:**
- Padding: `0.625rem 1.5rem`
- Border: `1.5px solid var(--rc-border-color)`
- Border radius: `12px`
- Background: `rgba(255, 255, 255, 0.03)`
- Font: Inter, `0.9375rem`, font-weight 500
- Icon: `18px × 18px`

**Active State:**
- Background: `linear-gradient(135deg, rgba(0, 255, 204, 0.2), rgba(124, 58, 237, 0.2))`
- Border: `var(--rc-neon-primary)`
- Color: `var(--rc-neon-primary)`
- Box shadow: `0 0 20px rgba(0, 255, 204, 0.3)`

**Hover State:**
- Background: `rgba(255, 255, 255, 0.05)`
- Border: `var(--rc-neon-primary)`
- Transform: `translateY(-2px)`

**Issues:**
- ✅ Visual feedback rõ ràng
- ❌ **Không có keyboard navigation** (Tab, Arrow keys)
- ❌ **Active state** có thể không đủ contrast với background

#### **Textarea**
**Class:** `.rc-textarea`

**Style:**
- Border: `1.5px solid var(--rc-border-color)`
- Border radius: `12px`
- Padding: `1rem`
- Background: `rgba(255, 255, 255, 0.03)`
- Min height: `80px`
- Resize: Vertical only

**Focus State:**
- Tương tự text input

**Issues:**
- ✅ Resize handle visible
- ❌ **Không có character count** (nếu có max length)

#### **Toggle Switch (Module Cards)**
**Class:** Custom toggle với sparkle animation

**Structure:**
- Input: `.toggle-input` (hidden checkbox)
- Label: `.toggle-label` với SVG icon và sparkle spans

**Style:**
- Custom toggle với animation phức tạp
- Sparkle effects khi toggle

**Issues:**
- ⚠️ **Animation quá phức tạp** - có thể gây distraction
- ❌ **Không có keyboard support** (Space to toggle)
- ❌ **Focus state** không rõ ràng

### Buttons

#### **Primary Button**
**Class:** `.rc-btn-primary`

**Style:**
- Background: `linear-gradient(135deg, var(--rc-neon-primary), var(--rc-neon-secondary))`
- Color: `var(--rc-bg-primary)` (dark text)
- Padding: `0.75rem 1.5rem`
- Border radius: `12px`
- Font: Inter, `0.9375rem`, font-weight 600
- Box shadow: `0 4px 16px rgba(0, 255, 204, 0.3)`

**Hover State:**
- Transform: `translateY(-2px)`
- Box shadow: `0 8px 24px rgba(0, 255, 204, 0.4)`

**Large Variant:**
- Padding: `1rem 2rem`
- Font size: `1rem`

**Issues:**
- ✅ Visual hierarchy rõ ràng
- ❌ **Không có loading state** (spinner khi submit)
- ❌ **Không có disabled state** styling
- ❌ **Focus ring** có thể không đủ visible

#### **Secondary Button**
**Class:** `.rc-btn-secondary`

**Style:**
- Background: `rgba(255, 255, 255, 0.05)`
- Color: `var(--rc-text-primary)`
- Border: `1.5px solid var(--rc-border-color)`
- Padding: `0.75rem 1.5rem`
- Border radius: `12px`

**Hover State:**
- Background: `rgba(255, 255, 255, 0.1)`
- Border: `var(--rc-neon-primary)`
- Transform: `translateY(-2px)`

**Issues:**
- ✅ Contrast đủ
- ❌ **Không có active/pressed state**

#### **Ghost Button**
**Class:** `.rc-btn-ghost`

**Style:**
- Background: `transparent`
- Border: `transparent`
- Color: `var(--rc-text-primary)`

**Hover State:**
- Background: `rgba(255, 255, 255, 0.05)`
- Border: `var(--rc-border-color)`

**Issues:**
- ⚠️ **Low visibility** - có thể khó nhận biết là button

### States

#### **Empty/Default State**
- Placeholder text: `var(--rc-text-tertiary)`
- Border: `var(--rc-border-color)`
- Background: `rgba(255, 255, 255, 0.03)`

**Issues:**
- ✅ Visual distinction rõ ràng
- ❌ **Không có "empty state" message** cho sections chưa điền

#### **Hover State**
- Input: Background `rgba(255, 255, 255, 0.05)`, border `var(--rc-neon-primary)`
- Button: Transform `translateY(-2px)`, enhanced shadow
- Card: Border `rgba(0, 255, 204, 0.2)`, enhanced shadow

**Issues:**
- ✅ Feedback rõ ràng
- ⚠️ **Transform có thể gây layout shift** nếu không có space

#### **Focus State**
- Input: Border `var(--rc-neon-primary)`, box shadow với glow
- Left border accent: `3px solid var(--rc-neon-primary)`
- Label: Color `var(--rc-neon-primary)`, font-weight 600, icon "⚡" hiện

**Issues:**
- ✅ Visual feedback tốt
- ❌ **Focus ring** có thể không đủ cho keyboard navigation (WCAG)
- ❌ **Label change** có thể gây layout shift

#### **Validation Error State**
**Class:** `.rc-input-error`

**Style:**
- Border: `#ef4444 !important`
- Box shadow: `0 0 0 3px rgba(239, 68, 68, 0.1)`

**Error Message:**
- Pseudo `::after` với content "Required field"
- Font size: `0.8125rem`
- Color: `#ef4444`
- Margin top: `4px`

**Issues:**
- ❌ **Error message placement:** Dùng `::after` - không accessible (screen reader không đọc được)
- ❌ **Không có error icon** visual
- ❌ **Error message** chỉ hiện khi có class, không dynamic
- ❌ **Không có inline validation** real-time (chỉ validate on submit)

#### **Loading/Submitting State**
**Không có loading state** cho:
- Form submission
- Dropdown loading
- Autosuggest search
- File upload

**Issues:**
- ❌ **Thiếu loading indicators** - user không biết form đang process
- ❌ **Button không disable** khi submit (có thể double submit)

#### **Success/Redirect State**
- Submit → redirect `/overview` (303 redirect)
- Không có success message trước redirect

**Issues:**
- ❌ **Không có feedback** trước redirect
- ❌ **Không có "saving..." indicator**

### Accessibility & Usability

#### **Label Association**
- ✅ Labels có `<label>` tag với `for` attribute
- ✅ Một số field dùng `aria-label` (ví dụ: theme toggle)

**Issues:**
- ❌ **Dropdowns:** Dùng `<button>` thay vì `<select>`, không có `<label>` association rõ ràng
- ❌ **Pill groups:** Không có `<fieldset>` và `<legend>`

#### **Tab Order**
- Tab order: Theo DOM order (không có `tabindex` custom)
- Sidebar nav: Có thể tab được (links)

**Issues:**
- ❌ **Dropdowns:** Tab vào trigger, nhưng menu items không keyboard accessible
- ❌ **Pill groups:** Tab vào từng pill, nhưng không có arrow key navigation

#### **Keyboard Navigation**
- ✅ Basic tab navigation hoạt động
- ❌ **Dropdowns:** Không có arrow keys, Enter, Escape
- ❌ **Pill groups:** Không có arrow keys để chọn
- ❌ **Autosuggest:** Không có arrow keys để navigate suggestions

#### **Error Announcement**
- ❌ **Không có `aria-live` region** cho error messages
- ❌ **Error messages** dùng `::after` - không accessible
- ❌ **Không có `aria-invalid`** attribute trên inputs

#### **Screen Reader Support**
- ✅ Semantic HTML (headings, labels)
- ❌ **Dropdowns:** Không có `aria-expanded`, `aria-haspopup`
- ❌ **Required fields:** Không có `aria-required="true"`
- ❌ **Disabled fields:** Có `readonly` nhưng không có `aria-disabled`

---

## (6) UX ISSUES & RECOMMENDATIONS (REDESIGN GUIDELINES)

### Top Issues (P0/P1/P2)

#### **P0 - Critical (Blocking User Flow)**

1. **Cognitive Load Quá Cao**
   - **Issue:** 60+ fields hiện cùng lúc, không có progressive disclosure
   - **Impact:** User overwhelmed, không biết bắt đầu từ đâu
   - **Evidence:** Template có 6 sections, mỗi section 10-20 fields, tất cả visible ngay
   - **Recommendation:** 
     - Chia thành "Basic" (required) và "Advanced" (optional)
     - Collapsible sections với "Show more" toggle
     - Wizard/stepper cho first-time users

2. **Thiếu Live Preview/Feedback**
   - **Issue:** User không biết "what you'll get" sau khi submit
   - **Impact:** Low confidence, không biết form đã đủ chưa
   - **Evidence:** Không có preview panel, không có "completeness meter"
   - **Recommendation:**
     - 2-column layout: Form (left) + Live Preview Summary (right)
     - Progress indicator: "X of Y fields completed"
     - Preview card hiện route, cargo, parties summary

3. **Inconsistent Language**
   - **Issue:** Mix giữa "POL/POD" và "Origin/Destination", "Seller/Buyer" vs "Shipper/Consignee"
   - **Impact:** Confusion, không biết field nào là gì
   - **Evidence:** Template dùng "POL (Port of Loading)" nhưng backend có thể dùng "origin"
   - **Recommendation:**
     - Standardize: Dùng "Origin" và "Destination" (user-friendly hơn POL/POD)
     - Hoặc dùng "POL" và "POD" nhất quán
     - Tooltip giải thích nếu cần technical terms

4. **Thiếu Autosave/Draft Indicator**
   - **Issue:** User sợ mất data, không biết có draft không
   - **Impact:** User không dám refresh/close tab
   - **Evidence:** Có "Save Draft" button nhưng không có indicator "Last saved: 2 min ago"
   - **Recommendation:**
     - Auto-save mỗi 30s (debounced)
     - Toast notification "Draft saved"
     - Badge "Unsaved changes" nếu có thay đổi chưa save

#### **P1 - High Priority (UX Degradation)**

5. **Validation Chỉ Hiện Khi Submit**
   - **Issue:** User phải submit mới biết field nào sai
   - **Impact:** Frustration, phải scroll lại tìm errors
   - **Evidence:** Validator chỉ chạy trong `submitForm()`, không có real-time validation
   - **Recommendation:**
     - Inline validation on blur
     - Real-time validation cho required fields
     - Error summary ở top form (scroll to error)

6. **Thiếu Field Grouping Theo Decision Flow**
   - **Issue:** Fields không theo logic "Route → Schedule → Cargo → Value → Parties"
   - **Impact:** User phải jump giữa sections
   - **Evidence:** Transport section có ETD/ETA ở cuối, không gần Schedule
   - **Recommendation:**
     - Group: "Route Selection" → "Schedule & Dates" → "Cargo Details" → "Value & Insurance" → "Parties"
     - Visual connection giữa related fields

7. **CTA Không Nổi Bật**
   - **Issue:** "Run Risk Analysis" button ở sticky footer, có thể bị che
   - **Impact:** User không biết làm gì tiếp theo
   - **Evidence:** Footer sticky nhưng có thể bị scroll past
   - **Recommendation:**
     - Sticky CTA bar luôn visible (top hoặc bottom)
     - Progress indicator: "Step 1 of 6"
     - Disable button nếu required fields chưa đủ

8. **Thiếu Helper Text/Units**
   - **Issue:** Một số fields không có unit (kg, m³, USD) visible
   - **Impact:** User không biết format/unit
   - **Evidence:** "Gross Weight" có hint "Total weight including packaging" nhưng không có "kg" visible
   - **Recommendation:**
     - Inline units: "Gross Weight (kg)"
     - Helper text với examples: "e.g., 20915 kg"
     - Format hints: "Format: YYYY-MM-DD"

#### **P2 - Medium Priority (Polish)**

9. **Component Mismatch với Summary/Results**
   - **Issue:** Input dùng `rc-glass-card`, Summary dùng `visionos-card`
   - **Impact:** Visual inconsistency
   - **Recommendation:** Migrate sang `visionos-card` component

10. **Token Mismatch**
    - **Issue:** Input dùng `--rc-neon-primary: #00ffcc`, Summary dùng `--color-primary-neon: #6ef3ff`
    - **Impact:** Color không match
    - **Recommendation:** Dùng tokens từ `tokens.css`

11. **Thiếu Microcopy Chuẩn**
    - **Issue:** Labels/hints không consistent tone
    - **Impact:** Unprofessional feel
    - **Recommendation:** Style guide cho microcopy (tone: professional, helpful, concise)

12. **Thiếu "What You'll Get" Preview**
    - **Issue:** User không biết output sẽ như thế nào
    - **Impact:** Low confidence
    - **Recommendation:** Preview card hiện "You'll receive: Risk Score, Route Analysis, Recommendations"

### Redesign Recommendations (SaaS Enterprise-Grade)

#### **Layout: 12-Column Grid với 2-Column Split**

```
┌─────────────────────────────────────────────────────────┐
│ Header (Fixed)                                           │
├──────────┬───────────────────────────────────────────────┤
│ Sidebar  │ Main Content (12-col grid)                   │
│ (280px)  │ ┌──────────────────┬──────────────────────┐ │
│          │ │ Form (8 cols)    │ Preview (4 cols)      │ │
│          │ │                  │                       │ │
│          │ │ Section 01       │ Route Summary Card    │ │
│          │ │ Section 02       │ Cargo Summary Card    │ │
│          │ │ ...              │ Progress Meter        │ │
│          │ │                  │ "What You'll Get"     │ │
│          │ └──────────────────┴──────────────────────┘ │
│          │ Sticky CTA Bar (Run Analysis / Save Draft)  │
└──────────┴───────────────────────────────────────────────┘
```

**Implementation:**
- Form container: `grid-template-columns: 8fr 4fr`, gap `2rem`
- Left: Form sections (scrollable)
- Right: Sticky preview panel (fixed khi scroll)
- CTA bar: Sticky bottom, full width

#### **Progressive Disclosure: Basic vs Advanced**

**Basic Mode (Default):**
- Show only required fields + most common optional fields
- Collapsible "Advanced Options" cho mỗi section
- "Show all fields" toggle ở top

**Advanced Mode:**
- Show tất cả fields
- Grouped by decision flow

**Implementation:**
- Toggle switch: "Basic" / "Advanced"
- State persisted trong localStorage
- Sections có `data-basic-fields` và `data-advanced-fields` attributes

#### **Sticky CTA Bar**

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Progress: ████████░░░░ 8/12 fields completed       │
│ [Save Draft]              [Run Risk Analysis →]    │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Progress bar: "X of Y required fields completed"
- "Save Draft" button (secondary)
- "Run Risk Analysis" button (primary, disabled nếu chưa đủ required)
- Sticky bottom, z-index cao

#### **Inline Validation + Units + Helper Text**

**Field Structure:**
```
┌─────────────────────────────────────┐
│ Gross Weight (kg) *                 │
│ ┌─────────────────────────────────┐ │
│ │ [icon] 20915          [kg]      │ │
│ └─────────────────────────────────┘ │
│ ✓ Valid                            │
│ Total weight including packaging    │
│ Example: 20915 kg                   │
└─────────────────────────────────────┘
```

**Implementation:**
- Label với unit: "Gross Weight (kg)"
- Input với suffix unit (optional)
- Validation icon (✓/✗) real-time
- Helper text với example
- Error message inline (không dùng `::after`)

#### **Field Grouping Theo Decision Flow**

**New Structure:**
1. **Route Selection** (Transport Setup)
   - Trade Lane, Mode, Service Route, Carrier
   - Priority Selection
2. **Schedule & Dates** (Transport Setup - Part 2)
   - ETD, Transit Time, ETA (auto-calculated)
   - Schedule Frequency
3. **Cargo Details** (Cargo & Packing)
   - Type, Weight, Volume, Packaging
   - Sensitivity, DG (conditional)
4. **Value & Insurance** (Cargo & Packing - Part 2)
   - Insurance Value, Coverage
   - Incoterm, Location
5. **Parties** (Seller + Buyer)
   - Combined section với tabs hoặc accordion
6. **Risk Modules** (Optional)
   - Module toggles
7. **Upload** (Optional)
   - File upload

#### **Microcopy Chuẩn**

**Tone:** Professional, helpful, concise

**Examples:**
- ❌ "Select trade lane" → ✅ "Choose your trade route"
- ❌ "e.g., LAX, Shanghai..." → ✅ "Start typing port code (e.g., LAX, SGN)"
- ❌ "Origin port/location" → ✅ "Port where cargo is loaded"
- ❌ "Ready to analyze? Click the button..." → ✅ "Review your inputs and run analysis"

**Style Guide:**
- Labels: Sentence case, no period
- Hints: Full sentences, period
- Buttons: Action verbs, no period
- Errors: Clear, actionable ("Please select a trade lane")

#### **"Completeness Meter" + "What You'll Get" Preview**

**Completeness Meter:**
```
Progress: ████████░░░░ 67% (8/12 required fields)
✓ Route selected
✓ Cargo details complete
✗ Seller country required
```

**Preview Panel:**
```
┌─────────────────────────┐
│ Route Summary           │
│ VNSGN → CNSHA           │
│ Ocean FCL, 15 days      │
│                         │
│ Cargo Summary           │
│ Electronics, 20,915 kg  │
│ $85,000 insured         │
│                         │
│ You'll Receive:         │
│ • Risk Score (0-10)     │
│ • Route Analysis        │
│ • Recommendations       │
│ • Insurance Options    │
└─────────────────────────┘
```

**Implementation:**
- Real-time update khi user điền form
- Sticky panel (không scroll với form)
- Visual connection với form fields (highlight khi hover)

---

## PHỤ LỤC

### Field Inventory Table

| Field Key/Name | Label | Type | Required | Default | Source File (Line) |
|---------------|-------|------|----------|---------|-------------------|
| `tradeLane` | Trade Lane | Dropdown | Yes | "Select trade lane" | input_v20.html:132 |
| `mode` | Mode of Transport | Dropdown | Yes | "Select mode" | input_v20.html:153 |
| `shipmentType` | Shipment Type | Dropdown | Yes | "Select shipment type" | input_v20.html:170 |
| `serviceRoute` | Service Route | Dropdown | Yes | "Select service route" | input_v20.html:187 |
| `carrier` | Carrier | Dropdown | No | "Select carrier" | input_v20.html:208 |
| `priority` | Priority Selection | Pill group | No | "balanced" | input_v20.html:225 |
| `incoterm` | Incoterm® 2020 | Dropdown | No | "Select Incoterm" | input_v20.html:249 |
| `incotermLocation` | Incoterm Location | Text | No | Empty | input_v20.html:268 |
| `pol` | POL (Port of Loading) | Autosuggest | Yes | Empty | input_v20.html:276 |
| `pod` | POD (Port of Discharge) | Autosuggest | Yes | Empty | input_v20.html:291 |
| `containerType` | Container Type | Dropdown | No | "Select container" | input_v20.html:306 |
| `etd` | ETD (Estimated Departure) | Date | No | Empty | input_v20.html:325 |
| `schedule` | Schedule Frequency | Text (readonly) | No | "Auto-filled" | input_v20.html:335 |
| `transitDays` | Transit Time (days) | Number (readonly) | No | "Auto-filled" | input_v20.html:345 |
| `eta` | ETA (Estimated Arrival) | Date (readonly) | No | Empty | input_v20.html:355 |
| `reliabilityScore` | Reliability Score | Text (readonly) | No | "Auto-filled" | input_v20.html:365 |
| `cargoType` | Cargo Type | Dropdown | Yes | "Select cargo type" | _v20_cargo_section.html:21 |
| `hsCode` | HS Code | Text | No | Empty | _v20_cargo_section.html:44 |
| `packingType` | Packing Type | Dropdown | Yes | "Select packing" | _v20_cargo_section.html:52 |
| `packageCount` | Number of Packages | Number | No | Empty | _v20_cargo_section.html:71 |
| `grossWeight` | Gross Weight (kg) | Number | Yes | Empty | _v20_cargo_section.html:81 |
| `netWeight` | Net Weight (kg) | Number | No | Empty | _v20_cargo_section.html:91 |
| `volumeCbm` | Volume (m³) | Number | No | Empty | _v20_cargo_section.html:101 |
| `stackable` | Stackability | Pill group | No | "true" | _v20_cargo_section.html:109 |
| `insuranceValue` | Insurance Value (USD) | Number | Yes | Empty | _v20_cargo_section.html:127 |
| `insuranceCoverage` | Insurance Coverage | Dropdown | No | "Select coverage type" | _v20_cargo_section.html:135 |
| `cargoSensitivity` | Cargo Sensitivity | Pill group | No | "standard" | _v20_cargo_section.html:152 |
| `tempMin` | Min Temperature (°C) | Number | No | Empty | _v20_cargo_section.html:178 |
| `tempMax` | Max Temperature (°C) | Number | No | Empty | _v20_cargo_section.html:186 |
| `dangerousGoods` | Dangerous Goods (DG) | Pill group | No | "false" | _v20_cargo_section.html:193 |
| `dgUnNumber` | UN Number | Text | No | Empty | _v20_cargo_section.html:211 |
| `dgClass` | DG Class | Dropdown | No | "Select class" | _v20_cargo_section.html:217 |
| `dgPackingGroup` | Packing Group | Dropdown | No | "Select group" | _v20_cargo_section.html:232 |
| `loadabilityIssues` | Loadability Issues | Toggle | No | false | _v20_cargo_section.html:250 |
| `cargoDescription` | Cargo Description | Textarea | No | Empty | _v20_cargo_section.html:259 |
| `specialHandling` | Special Handling Instructions | Textarea | No | Empty | _v20_cargo_section.html:266 |
| `sellerCompany` | Company Name | Text | Yes | Empty | _v20_seller_section.html:22 |
| `sellerBusinessType` | Business Type | Dropdown | No | "Select business type" | _v20_seller_section.html:29 |
| `sellerCountry` | Country | Dropdown | Yes | "Select country" | _v20_seller_section.html:46 |
| `sellerCity` | City | Text | No | Empty | _v20_seller_section.html:69 |
| `sellerAddress` | Address | Text | No | Empty | _v20_seller_section.html:78 |
| `sellerContact` | Contact Person | Text | No | Empty | _v20_seller_section.html:87 |
| `sellerContactRole` | Contact Role | Text | No | Empty | _v20_seller_section.html:96 |
| `sellerEmail` | Email | Email | No | Empty | _v20_seller_section.html:105 |
| `sellerPhone` | Phone | Tel | No | Empty | _v20_seller_section.html:114 |
| `sellerTaxId` | Tax ID / VAT | Text | No | Empty | _v20_seller_section.html:123 |
| `buyerCompany` | Company Name | Text | Yes | Empty | _v20_buyer_section.html:22 |
| `buyerBusinessType` | Business Type | Dropdown | No | "Select business type" | _v20_buyer_section.html:29 |
| `buyerCountry` | Country | Dropdown | Yes | "Select country" | _v20_buyer_section.html:46 |
| `buyerCity` | City | Text | No | Empty | _v20_buyer_section.html:69 |
| `buyerAddress` | Address | Text | No | Empty | _v20_buyer_section.html:78 |
| `buyerContact` | Contact Person | Text | No | Empty | _v20_buyer_section.html:87 |
| `buyerContactRole` | Contact Role | Text | No | Empty | _v20_buyer_section.html:96 |
| `buyerEmail` | Email | Email | No | Empty | _v20_buyer_section.html:105 |
| `buyerPhone` | Phone | Tel | No | Empty | _v20_buyer_section.html:114 |
| `buyerTaxId` | Tax ID / VAT | Text | No | Empty | _v20_buyer_section.html:123 |
| `moduleESG` | ESG Risk | Checkbox | No | true | input_v20.html:414 |
| `moduleWeather` | Weather & Climate Risk | Checkbox | No | true | input_v20.html:460 |
| `modulePortCongestion` | Port Congestion Risk | Checkbox | No | true | input_v20.html:506 |
| `moduleCarrier` | Carrier Performance | Checkbox | No | true | input_v20.html:552 |
| `moduleMarket` | Market Condition Scanner | Checkbox | No | true | input_v20.html:598 |
| `moduleInsurance` | Insurance Optimization | Checkbox | No | true | input_v20.html:644 |
| `rc-file-input` | Upload Packing List | File | No | Empty | input_v20.html:699 |

**Total:** 60+ fields

### Danh sách File Liên Quan

**Templates:**
- `app/templates/input/input_v20.html` - Main template
- `app/templates/input/partials/_v20_cargo_section.html` - Cargo section
- `app/templates/input/partials/_v20_seller_section.html` - Seller section
- `app/templates/input/partials/_v20_buyer_section.html` - Buyer section
- `app/templates/layouts/input_layout.html` - Layout wrapper (nếu có)

**CSS:**
- `app/static/css/pages/input/input_v20.css` - Main stylesheet (1676 lines)
- `app/static/css/global_visionos.css` - Global VisionOS styles
- `app/static/css/tokens.css` - Design tokens (KHÔNG được Input dùng)
- `app/static/css/components/floating_lang_switcher.css` - Language switcher

**JavaScript:**
- `app/static/js/v20/index.js` - Entry point
- `app/static/js/v20/core/RiskcastInputController.js` - Main controller (943 lines)
- `app/static/js/v20/core/StateManager.js` - State management
- `app/static/js/v20/core/APIClient.js` - API client
- `app/static/js/v20/modules/TransportModule.js` - Transport logic
- `app/static/js/v20/modules/CargoModule.js` - Cargo logic
- `app/static/js/v20/modules/PartyModule.js` - Party logic
- `app/static/js/v20/modules/PriorityManager.js` - Priority logic
- `app/static/js/v20/modules/ModuleCardsManager.js` - Module toggles
- `app/static/js/v20/ui/DropdownManager.js` - Dropdown UI
- `app/static/js/v20/ui/AutoSuggestManager.js` - Autosuggest UI
- `app/static/js/v20/ui/PillGroupManager.js` - Pill groups
- `app/static/js/v20/ui/UploadZoneManager.js` - File upload
- `app/static/js/v20/ui/ToastManager.js` - Notifications
- `app/static/js/v20/utils/Validators.js` - Validation
- `app/static/js/v20/utils/DateCalculators.js` - Date calculations
- `app/static/js/data/logistics_data.js` - Logistics data
- `app/static/js/data/container_types.js` - Container types
- `app/static/js/core/floating_lang_switcher.js` - Language switcher

**Backend:**
- `app/main.py` (lines 278-397) - Route `/input_v20/submit` handler
  - Action: `POST /input_v20/submit`
  - Redirect: `/overview` (303 redirect)
  - Payload: Normalize form data → `shipment_payload` → `RISKCAST_STATE` → session storage

### Action URL & Redirect

**Submit Action:**
- **URL:** `POST /input_v20/submit`
- **Handler:** `app/main.py:278` (`input_v20_submit()`)
- **Payload Format:** Form data hoặc JSON
- **Processing:**
  1. Normalize form data → `shipment_payload` dict
  2. Build `domain_case_like` structure
  3. Save to session: `request.session["RISKCAST_STATE"]`
  4. Save to memory: `memory_system.set("latest_shipment")`
- **Redirect:** `RedirectResponse(url="/overview", status_code=303)`
- **Target:** Summary page (`/overview`)

**Note:** Backend không validate form data trước khi save, validation chỉ ở frontend (RiskcastInputController).

---

## NORTH STAR LAYOUT (Đề Xuất Bố Cục)

### Desktop Layout (12-Column Grid)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Header (Fixed, 70px)                                                │
│ [Logo] [Status]                    [Theme] [Notifications] [Avatar] │
├──────────┬──────────────────────────────────────────────────────────┤
│ Sidebar │ Main Content (12-col grid, max-width: 1400px, centered) │
│ (280px)  │                                                           │
│          │ ┌──────────────────────────┬──────────────────────────┐ │
│ Nav:     │ │ Form Panel (8 cols)      │ Preview Panel (4 cols)  │ │
│ • Trans  │ │                          │ [Sticky khi scroll]     │ │
│ • Cargo  │ │ ┌──────────────────────┐ │                         │ │
│ • Seller │ │ │ Route Selection      │ │ ┌─────────────────────┐ │ │
│ • Buyer  │ │ │ [Trade Lane] [Mode]  │ │ │ Route Summary       │ │ │
│ • Modules│ │ │ [Service Route]      │ │ │ VNSGN → CNSHA       │ │ │
│ • Upload │ │ └──────────────────────┘ │ │ Ocean FCL, 15 days  │ │ │
│          │ │                          │ └─────────────────────┘ │ │
│ [Save    │ │ ┌──────────────────────┐ │                         │ │
│  Draft]  │ │ │ Schedule & Dates     │ │ ┌─────────────────────┐ │ │
│          │ │ │ [ETD] [Transit] [ETA]│ │ │ Progress Meter      │ │ │
│          │ │ └──────────────────────┘ │ │ ████████░░ 67%       │ │ │
│          │ │                          │ │ 8/12 required        │ │ │
│          │ │ ┌──────────────────────┐ │ └─────────────────────┘ │ │
│          │ │ │ Cargo Details        │ │                         │ │
│          │ │ │ [Type] [Weight]     │ │ ┌─────────────────────┐ │ │
│          │ │ │ [Volume] [Packaging]│ │ │ What You'll Get     │ │ │
│          │ │ └──────────────────────┘ │ │ • Risk Score         │ │ │
│          │ │                          │ │ • Route Analysis     │ │ │
│          │ │ ┌──────────────────────┐ │ │ • Recommendations   │ │ │
│          │ │ │ Value & Insurance   │ │ └─────────────────────┘ │ │
│          │ │ │ [Value] [Incoterm]   │ │                         │ │
│          │ │ └──────────────────────┘ │                         │ │
│          │ │                          │                         │ │
│          │ │ ┌──────────────────────┐ │                         │ │
│          │ │ │ Parties (Tabs)       │ │                         │ │
│          │ │ │ [Seller] [Buyer]     │ │                         │ │
│          │ │ └──────────────────────┘ │                         │ │
│          │ │                          │                         │ │
│          │ │ ┌──────────────────────┐ │                         │ │
│          │ │ │ Risk Modules         │ │                         │ │
│          │ │ │ [6 toggles grid]     │ │                         │ │
│          │ │ └──────────────────────┘ │                         │ │
│          │ │                          │                         │ │
│          │ │ ┌──────────────────────┐ │                         │ │
│          │ │ │ Upload (Optional)    │ │                         │ │
│          │ │ │ [Drag & Drop Zone]   │ │                         │ │
│          │ │ └──────────────────────┘ │                         │ │
│          │ └──────────────────────────┴──────────────────────────┘ │
│          │                                                           │
│          │ ┌─────────────────────────────────────────────────────┐ │
│          │ │ Sticky CTA Bar (Full width, bottom)                 │ │
│          │ │ Progress: ████████░░ 8/12 | [Save Draft] [Run →]    │ │
│          │ └─────────────────────────────────────────────────────┘ │
└──────────┴───────────────────────────────────────────────────────────┘
```

### Key Features

1. **2-Column Split:** Form (8 cols) + Preview (4 cols)
2. **Sticky Preview:** Preview panel fixed khi scroll form
3. **Sticky CTA Bar:** Progress + actions luôn visible
4. **Progressive Disclosure:** "Basic" mode ẩn advanced fields
5. **Field Grouping:** Theo decision flow (Route → Schedule → Cargo → Value → Parties)
6. **Live Updates:** Preview panel update real-time khi user điền form
7. **Completeness Meter:** Progress bar + checklist
8. **Design Tokens:** Dùng tokens từ `tokens.css` (đồng bộ với Summary/Results)

### Responsive Behavior

**Tablet (768px - 1024px):**
- Sidebar: Collapsed (toggle button)
- Form: 1 column (full width)
- Preview: Below form (không sticky)

**Mobile (<768px):**
- Sidebar: Hidden (hamburger menu)
- Form: 1 column
- Preview: Collapsible accordion
- CTA bar: Full width, fixed bottom

---

**END OF REPORT**
