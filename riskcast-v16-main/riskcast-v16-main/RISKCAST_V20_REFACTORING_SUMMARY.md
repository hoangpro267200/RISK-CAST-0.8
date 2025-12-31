# RISKCAST v20.3 — Refactoring Summary

**Date:** December 3, 2025  
**Status:** ✅ Complete  
**Version:** v20.3 (VisionOS Edition with International Standards)

---

## 🎯 Goals Achieved

All 5 main objectives have been successfully implemented:

1. ✅ **Fixed Service Route selection bug**
2. ✅ **Upgraded Cargo & Packing to international standard**
3. ✅ **Upgraded Seller & Buyer Details to be risk-oriented**
4. ✅ **Added country selector with dropdown + search**
5. ✅ **Added Incoterms selection for Seller and Buyer**

---

## 📋 Detailed Changes

### 1. Service Route Selection Bug — FIXED ✅

**Problem:**
- When user selected a route from the dropdown, the main Service Route field didn't update with the selected value

**Solution:**
- Updated `selectServiceRoute()` method in `input_controller_v20.js`
- Now builds a human-readable label: `POL → POD • Carrier • Transit Days`
- Properly updates the dropdown display value using `updateDropdownSelection()`

**File Changed:**
- `app/static/js/pages/input/input_controller_v20.js` (line ~571-585)

**Code:**
```javascript
selectServiceRoute(routeData) {
    this.formData.serviceRoute = routeData.route_id;
    this.formData.serviceRouteData = routeData;
    
    // Build human-readable label
    const label = `${routeData.pol} → ${routeData.pod} • ${routeData.carrier || 'Carrier'} • ${routeData.transit_days || 0}d`;
    
    // Update UI - FIXED: ensure dropdown value is updated
    this.updateDropdownSelection('serviceRoute', routeData.route_id, label);
    
    // AUTO-FILL derived fields
    this.autoFillFromRoute(routeData);
    
    console.log('🔥 Service route selected:', routeData.route_id, label);
    this.onFormDataChange();
}
```

---

### 2. Cargo & Packing — Upgraded to International Standard ✅

**New Data Structure:**
```javascript
cargo: {
    cargoType: '',              // Required
    hsCode: '',                 // Optional but recommended
    packingType: '',            // Required
    packageCount: null,
    weights: {
        grossKg: null,          // Required
        netKg: null             // Optional
    },
    volumeCbm: null,
    stackable: true,
    loadabilityIssues: false,
    insurance: {
        valueUsd: null,         // Required
        coverageType: ''        // All Risk | Total Loss | FPA
    },
    sensitivity: 'standard',    // standard | fragile | temperature | high_value
    temperatureRange: {
        minC: null,
        maxC: null
    },
    dangerousGoods: {
        isDG: false,
        unNumber: '',
        dgClass: '',            // Class 1-9
        packingGroup: ''        // I | II | III
    },
    description: '',
    specialHandling: ''
}
```

**New Fields Added:**
1. **Cargo Type** (dropdown, searchable) — from `LOGISTICS_DATA.cargoTypes`
2. **HS Code** (text input)
3. **Packing Type** (dropdown) — Palletized, Cartons, Crates, Drums, Bags, Bulk, Flexitank, IBC, Reefer ULD
4. **Number of Packages** (numeric)
5. **Gross Weight (kg)** — Required
6. **Net Weight (kg)** — Optional
7. **Volume (m³)** (numeric with 0.01 step)
8. **Stackability** (pill buttons: Stackable | Non-stackable)
9. **Insurance Value (USD)** — Required
10. **Insurance Coverage Type** (dropdown: All Risk | Total Loss Only | FPA)
11. **Cargo Sensitivity** (pill buttons: Standard | Fragile | Temperature Sensitive | High Value)
    - **Conditional:** If "Temperature Sensitive" selected → shows Min/Max Temperature fields
12. **Dangerous Goods** (pill buttons: Not DG | DG Cargo)
    - **Conditional:** If "DG Cargo" selected → shows:
      - UN Number (text)
      - DG Class (dropdown: Class 1-9)
      - Packing Group (dropdown: I | II | III)
13. **Loadability Issues** (toggle checkbox)
14. **Cargo Description** (textarea)
15. **Special Handling Instructions** (textarea)

**Files Modified:**
- `app/templates/input/input_v20.html` — Replaced inline cargo section with partial include
- `app/templates/input/partials/_v20_cargo_section.html` — Complete international standard cargo form
- `app/static/js/pages/input/input_controller_v20.js` — Added `initCargoV20()` method

**Data Sources:**
- `LOGISTICS_DATA.cargoTypes` (14 types)
- `LOGISTICS_DATA.packingTypes` (10 types)
- `LOGISTICS_DATA.insuranceCoverageTypes` (3 types)
- `LOGISTICS_DATA.dgClasses` (9 classes)

**Conditional Logic:**
- Temperature fields appear only when "Temperature Sensitive" is selected
- DG fields (UN Number, Class, Packing Group) appear only when "DG Cargo" is selected

---

### 3. Seller Details — Risk-Oriented Upgrade ✅

**New Data Structure:**
```javascript
seller: {
    companyName: '',          // Required
    country: {                // Required, object with name + ISO2
        name: '',
        iso2: ''
    },
    city: '',
    address: '',
    contactPerson: '',
    contactRole: '',          // NEW: e.g., "Export Manager"
    email: '',
    phone: '',
    businessType: '',         // NEW: Manufacturer | Trading Company | Logistics Provider | Retailer | Other
    taxId: '',                // NEW: Optional
    incoterm: ''              // NEW: EXW | FOB | CIF | etc.
}
```

**New Fields Added:**
1. **Company Name** — Required
2. **Business Type** (dropdown) — Manufacturer, Trading Company, Logistics Provider, Retailer, Distributor, Wholesaler, Other
3. **Country** (dropdown with search) — 70+ countries with emoji flags 🇻🇳🇨🇳🇺🇸
4. **City**
5. **Address**
6. **Contact Person**
7. **Contact Role** — NEW (e.g., "Export Manager")
8. **Email**
9. **Phone**
10. **Tax ID / VAT** — NEW (optional)
11. **Incoterm (Seller)** — NEW (dropdown: EXW, FCA, FAS, FOB, CFR, CIF, CPT, CIP, DAP, DPU, DDP)

**Country Selector Features:**
- Searchable dropdown with 70+ countries
- Shows country emoji + name (e.g., 🇻🇳 Vietnam)
- Stores both `name` and `iso2` code
- Real-time search filtering

**Files Modified:**
- `app/templates/input/input_v20.html` — Replaced inline seller section with partial include
- `app/templates/input/partials/_v20_seller_section.html` — Complete risk-oriented seller form
- `app/static/js/pages/input/input_controller_v20.js` — Added `initSellerBuyerV20()` method

**Data Sources:**
- `LOGISTICS_DATA.countries` (70+ countries with emoji and ISO2 codes)
- `LOGISTICS_DATA.businessTypes` (7 types)
- `LOGISTICS_DATA.incoterms` (11 terms from Incoterms 2020)

---

### 4. Buyer Details — Risk-Oriented Upgrade ✅

**New Data Structure:**
```javascript
buyer: {
    companyName: '',          // Required
    country: {                // Required, object with name + ISO2
        name: '',
        iso2: ''
    },
    city: '',
    address: '',
    contactPerson: '',
    contactRole: '',          // NEW: e.g., "Procurement Manager"
    email: '',
    phone: '',
    businessType: '',         // NEW: Manufacturer | Trading Company | Logistics Provider | Retailer | Other
    taxId: '',                // NEW: Optional
    incoterm: ''              // NEW: EXW | FOB | CIF | etc.
}
```

**New Fields Added:**
Same structure as Seller (see above), with buyer-specific labels:
- Contact Role example: "Procurement Manager"
- Incoterm label: "Incoterm (Buyer)"

**Files Modified:**
- `app/templates/input/input_v20.html` — Replaced inline buyer section with partial include
- `app/templates/input/partials/_v20_buyer_section.html` — Complete risk-oriented buyer form
- `app/static/js/pages/input/input_controller_v20.js` — Uses same `initSellerBuyerV20()` method

---

### 5. Country Selector Component ✅

**Features:**
- **Searchable dropdown** with 70+ countries
- **Visual flags** using emoji (🇻🇳, 🇨🇳, 🇺🇸, etc.)
- **Real-time filtering** as user types
- **Structured data** — returns `{ name: 'Vietnam', iso2: 'VN' }`
- **Reusable** for both Seller and Buyer

**Implementation:**
```javascript
initCountryDropdown(party) {
    // party = 'seller' or 'buyer'
    const dropdownId = `${party}Country`;
    const menu = document.getElementById(`${dropdownId}-menu`);
    const searchInput = document.getElementById(`${dropdownId}Search`);
    
    const renderCountries = (filter = '') => {
        const filtered = this.logisticsData.countries.filter(country =>
            country.name.toLowerCase().includes(filter.toLowerCase()) ||
            country.iso2.toLowerCase().includes(filter.toLowerCase())
        );
        
        filtered.forEach(country => {
            // Create button with emoji + name
            // On click: store { name, iso2 } in formData
        });
    };
    
    // Initial render + search handler
}
```

**Data Source:**
- `LOGISTICS_DATA.countries` (70+ countries)
- Each country: `{ name: 'Vietnam', iso2: 'VN', emoji: '🇻🇳' }`

---

### 6. Incoterms Selection ✅

**Features:**
- **Separate dropdowns** for Seller and Buyer
- **Incoterms 2020** standard (11 terms)
- **Full labels** (e.g., "FOB – Free On Board")
- **Risk understanding** — helps AI understand who is responsible for which leg

**Incoterms List:**
1. EXW – Ex Works
2. FCA – Free Carrier
3. FAS – Free Alongside Ship
4. FOB – Free On Board
5. CFR – Cost and Freight
6. CIF – Cost, Insurance and Freight
7. CPT – Carriage Paid To
8. CIP – Carriage and Insurance Paid To
9. DAP – Delivered At Place
10. DPU – Delivered at Place Unloaded
11. DDP – Delivered Duty Paid

**Implementation:**
```javascript
initIncotermDropdown(party) {
    // party = 'seller' or 'buyer'
    const dropdownId = `${party}Incoterm`;
    const menu = document.getElementById(`${dropdownId}-menu`);
    
    this.logisticsData.incoterms.forEach(term => {
        // Create button with full label
        // On click: store term.code in formData
    });
}
```

**Data Source:**
- `LOGISTICS_DATA.incoterms` (11 terms)
- Each term: `{ code: 'FOB', label: 'FOB – Free On Board' }`

---

## 🔧 Technical Implementation

### New Controller Methods

**Added to `input_controller_v20.js`:**

1. **`initCargoV20()`** — Initializes all cargo-related dropdowns and fields
   - `loadCargoTypes()` — Loads 14 cargo types from logistics data
   - `loadPackingTypes()` — Loads 10 packing types
   - `loadInsuranceCoverageTypes()` — Loads 3 coverage types
   - `loadDGClasses()` — Loads 9 dangerous goods classes
   - `initStackabilityPills()` — Stackable/Non-stackable toggle
   - `initSensitivityPills()` — Sensitivity selection with conditional temperature fields
   - `initDGPills()` — DG toggle with conditional DG detail fields

2. **`initSellerBuyerV20()`** — Initializes seller and buyer sections
   - `initCountryDropdown('seller')` — Country selector for seller
   - `initCountryDropdown('buyer')` — Country selector for buyer
   - `initBusinessTypeDropdown('seller')` — Business type for seller
   - `initBusinessTypeDropdown('buyer')` — Business type for buyer
   - `initIncotermDropdown('seller')` — Incoterms for seller
   - `initIncotermDropdown('buyer')` — Incoterms for buyer

3. **`initConditionalFields()`** — Binds all nested input fields to state
   - `bindCargoInputs()` — Binds HS Code, weights, volume, temperature, DG fields, etc.
   - `bindSellerInputs()` — Binds seller contact details, tax ID, etc.
   - `bindBuyerInputs()` — Binds buyer contact details, tax ID, etc.

4. **Updated `selectServiceRoute()`** — Fixed the bug by building proper label

5. **Updated `resetForm()`** — Works with new nested data structure

6. **Updated `runAutoFillDemo()`** — Compatible with new nested structure

### Data Structure Changes

**Old (v20.2):**
```javascript
this.formData = {
    cargoType: '', packingType: '', cargoWeight: null, ...
    sellerCompany: '', sellerCountry: '', ...
    buyerCompany: '', buyerCountry: '', ...
}
```

**New (v20.3):**
```javascript
this.formData = {
    cargo: {
        cargoType: '', hsCode: '', packingType: '',
        weights: { grossKg: null, netKg: null },
        insurance: { valueUsd: null, coverageType: '' },
        ...
    },
    seller: {
        companyName: '', country: { name: '', iso2: '' },
        contactRole: '', businessType: '', taxId: '', incoterm: '', ...
    },
    buyer: {
        companyName: '', country: { name: '', iso2: '' },
        contactRole: '', businessType: '', taxId: '', incoterm: '', ...
    }
}
```

### HTML Template Changes

**`app/templates/input/input_v20.html`:**
- Replaced inline cargo section with `{% include 'input/partials/_v20_cargo_section.html' %}`
- Replaced inline seller section with `{% include 'input/partials/_v20_seller_section.html' %}`
- Replaced inline buyer section with `{% include 'input/partials/_v20_buyer_section.html' %}`

**Partials Used:**
- `app/templates/input/partials/_v20_cargo_section.html` (272 lines)
- `app/templates/input/partials/_v20_seller_section.html` (148 lines)
- `app/templates/input/partials/_v20_buyer_section.html` (148 lines)

---

## 🎨 UI/UX Preservation

✅ **VisionOS / Neon UI Style Maintained:**
- All existing CSS classes preserved (`rc-*` naming)
- Glass-card design intact
- Neon glow effects working
- Pill buttons styled consistently
- Dropdown animations unchanged

✅ **Existing Functionality Preserved:**
- Save Draft button works
- Run Risk Analysis button works
- Auto-Fill Demo works (updated for new structure)
- Navigation scroll spy works
- Theme toggle works
- All animations intact

---

## 📊 Validation Updates

**New Required Fields:**
- `cargo.cargoType` ✅
- `cargo.packingType` ✅
- `cargo.weights.grossKg` ✅
- `cargo.insurance.valueUsd` ✅
- `seller.companyName` ✅
- `seller.country.name` ✅
- `buyer.companyName` ✅
- `buyer.country.name` ✅

**Conditional Validation:**
- If `cargo.dangerousGoods.isDG === true` → require `unNumber` and `dgClass`
- If `cargo.sensitivity === 'temperature'` → require `temperatureRange.minC` and `maxC`

---

## 🗂️ Files Modified

### JavaScript
1. `app/static/js/pages/input/input_controller_v20.js` ✅
   - Updated data structure (line ~9-110)
   - Fixed `selectServiceRoute()` (line ~571-585)
   - Added `initCargoV20()` (line ~1878-2074)
   - Added `initSellerBuyerV20()` (line ~2076-2230)
   - Added `initConditionalFields()` (line ~2232-2410)
   - Updated `resetForm()` (line ~1804-1823)
   - Updated `runAutoFillDemo()` (line ~950-1036)

### HTML Templates
2. `app/templates/input/input_v20.html` ✅
   - Replaced cargo section (line ~356)
   - Replaced seller section (line ~491)
   - Replaced buyer section (line ~569)

### Partials (Already Existed, Now Used)
3. `app/templates/input/partials/_v20_cargo_section.html` ✅
4. `app/templates/input/partials/_v20_seller_section.html` ✅
5. `app/templates/input/partials/_v20_buyer_section.html` ✅

### Data File (No Changes Needed)
6. `app/static/js/data/logistics_data.js` ✅
   - All required data already present:
     - `cargoTypes` (14 types)
     - `packingTypes` (10 types)
     - `insuranceCoverageTypes` (3 types)
     - `dgClasses` (9 classes)
     - `businessTypes` (7 types)
     - `countries` (70+ countries)
     - `incoterms` (11 terms)

---

## ✅ Testing Checklist

All functionality verified:

- [x] Service Route selection now updates main field ✅
- [x] Cargo Type dropdown loads 14 types ✅
- [x] Packing Type dropdown loads 10 types ✅
- [x] Insurance Coverage dropdown loads 3 types ✅
- [x] DG Class dropdown loads 9 classes ✅
- [x] Stackability pills toggle correctly ✅
- [x] Sensitivity pills toggle and show/hide temperature fields ✅
- [x] DG pills toggle and show/hide DG detail fields ✅
- [x] Seller Country dropdown loads 70+ countries with search ✅
- [x] Buyer Country dropdown loads 70+ countries with search ✅
- [x] Seller Business Type dropdown loads 7 types ✅
- [x] Buyer Business Type dropdown loads 7 types ✅
- [x] Seller Incoterm dropdown loads 11 terms ✅
- [x] Buyer Incoterm dropdown loads 11 terms ✅
- [x] All input fields bind to nested RC_STATE ✅
- [x] Auto-Fill Demo works with new structure ✅
- [x] Save Draft preserves all fields ✅
- [x] Form Reset clears all fields correctly ✅
- [x] No JavaScript errors in console ✅
- [x] No linting errors ✅

---

## 🚀 Next Steps (Optional Enhancements)

If you want to further improve the system:

1. **Add field-level validation feedback** — Show red borders and error messages for required fields
2. **Add HS Code autocomplete** — Integrate HS Code lookup API
3. **Add country risk scores** — Display risk indicators next to country flags
4. **Add Incoterm tooltips** — Show brief explanations on hover
5. **Add cargo value calculator** — Auto-calculate insurance value based on weight/volume
6. **Add DG documentation links** — Link to IATA/IMO DG guides
7. **Add temperature presets** — Quick buttons for common ranges (Frozen: -25°C to -18°C, Chilled: 2°C to 8°C)

---

## 📝 Migration Notes for Backend

If you're updating the backend API to receive this data:

**Expected JSON structure from frontend:**
```json
{
  "tradeLane": "VN_US",
  "mode": "SEA",
  "serviceRoute": "route_123",
  "cargo": {
    "cargoType": "electronics",
    "hsCode": "8504.40",
    "packingType": "palletized",
    "packageCount": 120,
    "weights": {
      "grossKg": 20915,
      "netKg": 19500
    },
    "volumeCbm": 22.66,
    "stackable": true,
    "insurance": {
      "valueUsd": 85000,
      "coverageType": "all_risk"
    },
    "sensitivity": "standard",
    "temperatureRange": {
      "minC": null,
      "maxC": null
    },
    "dangerousGoods": {
      "isDG": false,
      "unNumber": "",
      "dgClass": "",
      "packingGroup": ""
    },
    "description": "Electronic components...",
    "specialHandling": "",
    "loadabilityIssues": false
  },
  "seller": {
    "companyName": "Global Tech Ltd",
    "country": {
      "name": "Vietnam",
      "iso2": "VN"
    },
    "city": "Ho Chi Minh City",
    "address": "123 Nguyen Hue",
    "contactPerson": "John Doe",
    "contactRole": "Export Manager",
    "email": "john@globaltech.com",
    "phone": "+84 123 456 789",
    "businessType": "manufacturer",
    "taxId": "VN123456789",
    "incoterm": "FOB"
  },
  "buyer": {
    "companyName": "Import Solutions GmbH",
    "country": {
      "name": "Germany",
      "iso2": "DE"
    },
    "city": "Hamburg",
    "address": "456 Hauptstrasse",
    "contactPerson": "Jane Smith",
    "contactRole": "Procurement Manager",
    "email": "jane@importsolutions.de",
    "phone": "+49 123 456 789",
    "businessType": "retailer",
    "taxId": "DE987654321",
    "incoterm": "CIF"
  },
  "modules": {
    "esg": true,
    "weather": true,
    "portCongestion": false,
    "carrier": false,
    "market": false,
    "insurance": true
  }
}
```

---

## 🎉 Summary

**All 5 objectives completed successfully!**

The RISKCAST v20 input page now has:
- ✅ International standard cargo documentation (15+ fields)
- ✅ Risk-oriented seller/buyer sections with countries & incoterms
- ✅ Searchable country selector with 70+ countries
- ✅ Conditional fields for temperature & dangerous goods
- ✅ Fixed service route selection bug
- ✅ All data loaded from `logistics_data.js` (no hardcoding)
- ✅ VisionOS neon UI style preserved
- ✅ Existing functionality intact (Save Draft, Run Analysis, Auto-Fill Demo)

**Ready for production!** 🚀

---

**Version:** v20.3 — VisionOS Edition with International Standards  
**Status:** ✅ Complete & Tested  
**Date:** December 3, 2025  
**Author:** AI Assistant (Claude Sonnet 4.5)






