# 🎨 RISKCAST v20 REFACTORING — VISUAL GUIDE

## 📊 ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    RISKCAST v20 INPUT PAGE                      │
│                  (International Standard Edition)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         HTML TEMPLATE                            │
│                   app/templates/input/input_v20.html            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📦 Section 01: Transport Setup (EXISTING - Keep as is)         │
│     - Trade Lane, Mode, Shipment Type                           │
│     - Priority (4 modes)                                         │
│     - ✅ Service Route (FIX: Dropdown updates label)            │
│     - POL/POD, Container, ETD/ETA                               │
│                                                                  │
│  📦 Section 02: Cargo & Packing (REPLACE WITH PARTIAL)          │
│     ┌──────────────────────────────────────────┐               │
│     │ _v20_cargo_section.html                   │               │
│     │  • Cargo Type (dropdown)                  │               │
│     │  • HS Code (text)                         │               │
│     │  • Packing Type (dropdown)                │               │
│     │  • Package Count, Weights, Volume         │               │
│     │  • Stackability (pills)                   │               │
│     │  • Insurance Value + Coverage Type        │               │
│     │  • Sensitivity (pills)                    │               │
│     │  • Temperature Range (conditional)        │               │
│     │  • Dangerous Goods (toggle + fields)      │               │
│     │  • Description + Special Handling         │               │
│     └──────────────────────────────────────────┘               │
│                                                                  │
│  📦 Section 03: Seller Details (REPLACE WITH PARTIAL)           │
│     ┌──────────────────────────────────────────┐               │
│     │ _v20_seller_section.html                  │               │
│     │  • Company Name (required)                │               │
│     │  • Business Type (dropdown)               │               │
│     │  • Country (searchable with emoji)        │               │
│     │  • City, Address                          │               │
│     │  • Contact Person + Role                  │               │
│     │  • Email, Phone                           │               │
│     │  • Tax ID / VAT                           │               │
│     │  • Incoterm (dropdown)                    │               │
│     └──────────────────────────────────────────┘               │
│                                                                  │
│  📦 Section 04: Buyer Details (REPLACE WITH PARTIAL)            │
│     ┌──────────────────────────────────────────┐               │
│     │ _v20_buyer_section.html                   │               │
│     │  • Same structure as Seller               │               │
│     │  • All risk-oriented fields               │               │
│     └──────────────────────────────────────────┘               │
│                                                                  │
│  📦 Section 05-06: Modules & Upload (EXISTING - Keep as is)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    JAVASCRIPT CONTROLLER                         │
│          app/static/js/pages/input/input_controller_v20.js     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔧 constructor() → Update formData structure                   │
│                                                                  │
│  🔧 init() → Add new init calls:                                │
│     • initCargoFields()                                         │
│     • initCountryDropdowns()                                    │
│     • initIncotermDropdowns()                                   │
│     • bindSellerBuyerInputs()                                   │
│                                                                  │
│  🔧 NEW METHODS (copy from guide):                              │
│     • updateDropdownSelection()       // Fix service route      │
│     • loadCargoTypes()                // Cargo dropdown         │
│     • loadPackingTypes()              // Packing dropdown       │
│     • loadInsuranceCoverageTypes()    // Insurance dropdown     │
│     • loadDGClasses()                 // DG dropdown            │
│     • initStackabilityPills()         // Pills logic            │
│     • initSensitivityPills()          // Pills + show temp      │
│     • initDGToggle()                  // Toggle + show DG       │
│     • bindCargoInputs()               // Bind all cargo fields  │
│     • initCountryDropdown()           // Country with search    │
│     • initIncotermDropdown()          // Incoterm selection     │
│     • bindSellerBuyerInputs()         // Bind party fields      │
│     • initBusinessTypeDropdown()      // Business type          │
│                                                                  │
│  🔧 UPDATE EXISTING:                                             │
│     • validateForm() → Add cargo/seller/buyer validation        │
│     • submitForm() → Ensure RC_STATE updated                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          DATA SOURCE                             │
│              app/static/js/data/logistics_data.js               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ LOGISTICS_DATA.cargoTypes                 (34 types)        │
│  ✅ LOGISTICS_DATA.packingTypes               (15 types)        │
│  ✅ LOGISTICS_DATA.insuranceCoverageTypes     (3 types)         │
│  ✅ LOGISTICS_DATA.dgClasses                  (9 classes)       │
│  ✅ LOGISTICS_DATA.businessTypes              (7 types)         │
│  ✅ LOGISTICS_DATA.countries                  (50+ countries)   │
│  ✅ LOGISTICS_DATA.incoterms                  (11 terms)        │
│                                                                  │
│  🎯 ALL DATA READY — NO NEED TO ADD ANYTHING!                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GLOBAL STATE (window)                       │
│                         window.RC_STATE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  {                                                               │
│    transport: { ... },      // EXISTING + serviceRoute fix      │
│    cargo: { ... },          // NEW - 15 international fields    │
│    seller: { ... },         // NEW - Risk-oriented + incoterm   │
│    buyer: { ... },          // NEW - Risk-oriented + incoterm   │
│    modules: { ... }         // EXISTING                         │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 DATA FLOW DIAGRAM

### Service Route Selection (FIXED)

```
User clicks route in dropdown
         │
         ▼
selectServiceRoute(routeData)
         │
         ├─→ Build structured object:
         │   { id, label, pol, pod, carrier, transitDays, ... }
         │
         ├─→ Update state:
         │   RC_STATE.transport.serviceRoute = selectedRoute
         │
         ├─→ Update UI:
         │   updateDropdownSelection(id, value, label)
         │     └─→ Set .rc-dropdown-value text
         │     └─→ Close dropdown
         │
         └─→ Auto-fill related fields:
             autoFillFromRoute(routeData)
               └─→ Transit, Schedule, Reliability, Carrier, ETA
```

### Cargo Sensitivity (Conditional Fields)

```
User clicks "Temperature Sensitive" pill
         │
         ▼
initSensitivityPills() event handler
         │
         ├─→ Update state:
         │   RC_STATE.cargo.sensitivity = 'temperature'
         │
         ├─→ Show temperature fields:
         │   #tempRangeFields.style.display = ''
         │   #tempRangeFields2.style.display = ''
         │
         └─→ Trigger change:
             onFormDataChange()
```

### Dangerous Goods Toggle (Conditional Fields)

```
User clicks "DG Cargo" pill
         │
         ▼
initDGToggle() event handler
         │
         ├─→ Update state:
         │   RC_STATE.cargo.dangerousGoods.isDG = true
         │
         ├─→ Show DG fields:
         │   #dgFields1.style.display = ''  (UN Number)
         │   #dgFields2.style.display = ''  (DG Class)
         │   #dgFields3.style.display = ''  (Packing Group)
         │
         └─→ Trigger change:
             onFormDataChange()
```

### Country Selection (with Search)

```
User opens Seller Country dropdown
         │
         ▼
initCountryDropdown('sellerCountry', 'seller')
         │
         ├─→ Render all countries from LOGISTICS_DATA.countries
         │   (50+ countries with emoji + ISO2)
         │
         ├─→ User types in search: "china"
         │   │
         │   ├─→ Filter countries:
         │   │   countries.filter(c => c.name.includes('china'))
         │   │
         │   └─→ Re-render filtered list
         │
         └─→ User clicks "🇨🇳 China"
             │
             ├─→ Update state:
             │   RC_STATE.seller.country = { name: 'China', iso2: 'CN' }
             │
             ├─→ Update UI:
             │   updateDropdownSelection(id, 'CN', '🇨🇳 China')
             │
             └─→ Close dropdown + clear search
```

---

## 📋 IMPLEMENTATION CHECKLIST

### PHASE 1: HTML Updates (5 minutes)

```
[ ] Open app/templates/input/input_v20.html

[ ] Find Section 02: Cargo & Packing (~line 329)
    └─→ Replace entire section with:
        {% include 'input/partials/_v20_cargo_section.html' %}

[ ] Find Section 03: Seller Details (~line 459)
    └─→ Replace entire section with:
        {% include 'input/partials/_v20_seller_section.html' %}

[ ] Find Section 04: Buyer Details (~line 537)
    └─→ Replace entire section with:
        {% include 'input/partials/_v20_buyer_section.html' %}

[ ] Save file
```

### PHASE 2: JavaScript Updates (15 minutes)

```
[ ] Open app/static/js/pages/input/input_controller_v20.js

[ ] Step 1: Update constructor()
    └─→ Replace this.formData with new structure
        (from RISKCAST_V20_REFACTORING_GUIDE.md Section 2.1)

[ ] Step 2: Add updateDropdownSelection() method
    (from guide Section 2.2)

[ ] Step 3: Add all Cargo methods
    └─→ initCargoFields()
    └─→ loadCargoTypes()
    └─→ loadPackingTypes()
    └─→ loadInsuranceCoverageTypes()
    └─→ loadDGClasses()
    └─→ initStackabilityPills()
    └─→ initSensitivityPills()
    └─→ initDGToggle()
    └─→ bindCargoInputs()
    (from guide Section 2.3)

[ ] Step 4: Add Country methods
    └─→ initCountryDropdowns()
    └─→ initCountryDropdown()
    (from guide Section 2.4)

[ ] Step 5: Add Incoterm methods
    └─→ initIncotermDropdowns()
    └─→ initIncotermDropdown()
    (from guide Section 2.5)

[ ] Step 6: Add Seller/Buyer methods
    └─→ bindSellerBuyerInputs()
    └─→ initBusinessTypeDropdown()
    (from guide Section 2.6)

[ ] Step 7: Update validateForm()
    (from guide Section 2.7)

[ ] Step 8: Update init() method
    └─→ Add: this.initCargoFields()
    └─→ Add: this.initCountryDropdowns()
    └─→ Add: this.initIncotermDropdowns()
    └─→ Add: this.bindSellerBuyerInputs()

[ ] Save file
```

### PHASE 3: Testing (10 minutes)

```
[ ] Start server:
    uvicorn app.main:app --reload --port 8000

[ ] Open browser:
    http://localhost:8000/input_v20

[ ] Test Service Route:
    [ ] Select Trade Lane + Mode + Shipment Type
    [ ] Open Service Route dropdown
    [ ] Click a route
    [ ] ✅ Verify dropdown label updates
    [ ] ✅ Open console: window.RC_STATE.transport.serviceRoute

[ ] Test Cargo Fields:
    [ ] Select Cargo Type → ✅ Updates
    [ ] Select Packing Type → ✅ Updates
    [ ] Enter weights/volume → ✅ Updates state
    [ ] Click "Temperature Sensitive" → ✅ Temp fields appear
    [ ] Toggle "DG Cargo" → ✅ DG fields appear

[ ] Test Country Selector:
    [ ] Click Seller Country
    [ ] Type "china" → ✅ Filters list
    [ ] Click "🇨🇳 China" → ✅ Shows emoji + name
    [ ] Check console: RC_STATE.seller.country

[ ] Test Incoterms:
    [ ] Select Seller Incoterm → ✅ Updates
    [ ] Select Buyer Incoterm → ✅ Updates
    [ ] Check console: RC_STATE.seller.incoterm

[ ] Test Validation:
    [ ] Leave required fields empty
    [ ] Click "Run Risk Analysis"
    [ ] ✅ Shows error toast
    [ ] ✅ Highlights missing fields

[ ] No console errors
```

---

## 🎯 VALIDATION RULES

### Required Fields

```
TRANSPORT:
  ✅ tradeLane
  ✅ mode
  ✅ pol
  ✅ pod

CARGO:
  ✅ cargoType
  ✅ packingType
  ✅ weights.grossKg
  ✅ insurance.valueUsd

  IF sensitivity === 'temperature':
    ✅ temperatureRange.minC
    ✅ temperatureRange.maxC

  IF dangerousGoods.isDG === true:
    ✅ dangerousGoods.unNumber
    ✅ dangerousGoods.dgClass

SELLER:
  ✅ companyName
  ✅ country.name

BUYER:
  ✅ companyName
  ✅ country.name
```

---

## 📊 FINAL STATE STRUCTURE

```javascript
window.RC_STATE = {
  transport: {
    tradeLane: 'vietnam_china',
    mode: 'SEA',
    shipmentType: 'ocean_fcl',
    priority: 'balanced',
    serviceRoute: {                    // ✨ FIXED - Now structured object
      id: 'VN-CN-CM-SZ-001',
      label: 'Cái Mép → Shenzhen Express',
      pol: 'Cái Mép',
      pod: 'Shenzhen',
      carrier: 'Maersk Line',
      transitDays: 7,
      reliability: 88,
      schedule: '3 sailings/week'
    },
    carrier: 'Maersk Line',
    pol: 'CMIT',
    pod: 'CNSZX',
    containerType: '40hc',
    etd: '2025-12-15',
    eta: '2025-12-22',
    transitDays: 7,
    reliability: 88,
    schedule: '3 sailings/week'
  },
  
  cargo: {                            // ✨ NEW - 15 international fields
    cargoType: 'electronics',
    hsCode: '8504.40',
    packingType: 'palletized',
    packageCount: 120,
    weights: {
      grossKg: 20915,
      netKg: 19500
    },
    volumeCbm: 22.66,
    stackable: true,
    loadabilityIssues: false,
    insurance: {
      valueUsd: 85000,
      coverageType: 'all_risk'
    },
    sensitivity: 'standard',
    temperatureRange: {
      minC: null,
      maxC: null
    },
    dangerousGoods: {
      isDG: false,
      unNumber: '',
      dgClass: '',
      packingGroup: ''
    },
    description: 'Electronic components, smartphones with lithium batteries',
    specialHandling: 'Keep upright, no stacking'
  },
  
  seller: {                           // ✨ NEW - Risk-oriented
    companyName: 'Global Tech Ltd',
    country: {
      name: 'China',
      iso2: 'CN'
    },
    city: 'Shanghai',
    address: '123 Business Street',
    contactPerson: 'John Doe',
    contactRole: 'Export Manager',
    email: 'john@globaltech.com',
    phone: '+86 21 1234 5678',
    businessType: 'manufacturer',
    taxId: 'CN123456789',
    incoterm: 'FOB'
  },
  
  buyer: {                            // ✨ NEW - Risk-oriented
    companyName: 'Import Solutions GmbH',
    country: {
      name: 'Germany',
      iso2: 'DE'
    },
    city: 'Hamburg',
    address: '456 Import Avenue',
    contactPerson: 'Jane Smith',
    contactRole: 'Procurement Manager',
    email: 'jane@importsolutions.de',
    phone: '+49 40 1234 5678',
    businessType: 'distributor',
    taxId: 'DE987654321',
    incoterm: 'CIF'
  },
  
  modules: {
    esg: true,
    weather: false,
    portCongestion: true,
    carrier: false,
    market: false,
    insurance: true
  }
}
```

---

## 🚀 TIME ESTIMATES

```
┌────────────────────────────┬─────────────┐
│ Task                       │ Time        │
├────────────────────────────┼─────────────┤
│ Replace HTML sections      │ 5 minutes   │
│ Copy-paste JS methods      │ 15 minutes  │
│ Update init() method       │ 2 minutes   │
│ Test in browser            │ 10 minutes  │
│ Fix any issues             │ 5-10 minutes│
├────────────────────────────┼─────────────┤
│ TOTAL                      │ ~40 minutes │
└────────────────────────────┴─────────────┘
```

---

## ✅ SUCCESS INDICATORS

After implementation, you should see:

```
✅ Service Route dropdown updates with selected route name
✅ Cargo section has 15 fields (not 6)
✅ Seller/Buyer sections have 10 fields each (not 7)
✅ Country dropdowns show "🇨🇳 China" style (emoji + name)
✅ Incoterm dropdowns show "FOB – Free On Board" style
✅ Temperature fields appear when "Temperature Sensitive" clicked
✅ DG fields appear when "DG Cargo" toggled
✅ Form validation catches all required fields
✅ Console shows complete RC_STATE structure
✅ No JavaScript errors in console
✅ VisionOS neon design preserved
```

---

## 📚 FILE REFERENCE

```
📁 app/
├── templates/
│   └── input/
│       ├── input_v20.html              ← UPDATE THIS (3 section replacements)
│       └── partials/
│           ├── _v20_cargo_section.html  ← CREATED ✅
│           ├── _v20_seller_section.html ← CREATED ✅
│           └── _v20_buyer_section.html  ← CREATED ✅
│
└── static/
    ├── js/
    │   ├── pages/
    │   │   └── input/
    │   │       └── input_controller_v20.js  ← UPDATE THIS (add 10+ methods)
    │   │
    │   └── data/
    │       └── logistics_data.js            ← ALREADY HAS ALL DATA ✅
    │
    └── css/
        └── pages/
            └── input/
                └── input_v20.css            ← NO CHANGES NEEDED

📄 RISKCAST_V20_REFACTORING_GUIDE.md       ← IMPLEMENTATION GUIDE (32KB)
📄 V20_REFACTORING_SUMMARY.md              ← EXECUTIVE SUMMARY
📄 V20_REFACTORING_VISUAL_GUIDE.md         ← THIS FILE
```

---

## 🎉 YOU'RE READY!

**Everything is prepared. Just follow the checklist above!**

**Start here:**
1. Open `RISKCAST_V20_REFACTORING_GUIDE.md`
2. Follow Step 1-3
3. Test
4. Done!

**Total time: ~40 minutes**

---

**Version:** RISKCAST v20 — International Standard Edition
**Status:** ✅ **READY TO IMPLEMENT**
**Date:** December 3, 2025






