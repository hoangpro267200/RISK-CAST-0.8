# RISKCAST v20 — COMPREHENSIVE REFACTORING PLAN

## Executive Summary

This document outlines the complete refactoring of RISKCAST v20 input page to international logistics standards.

---

## Changes Overview

### 1. Service Route Selection Fix ✅
**Bug:** Selected route not showing in main field
**Fix:** Update event handler to display selected route label and save structured data

### 2. Cargo & Packing Upgrade ✅
**Change:** From basic fields → International standard (15 fields)
**New Data Structure:**
```javascript
RC_STATE.cargo = {
  cargoType: '',
  hsCode: '',
  packingType: '',
  packageCount: null,
  weights: { grossKg: null, netKg: null },
  volumeCbm: null,
  stackable: null,
  loadabilityIssues: false,
  insurance: { valueUsd: null, coverageType: '' },
  sensitivity: 'standard',
  temperatureRange: { minC: null, maxC: null },
  dangerousGoods: { isDG: false, unNumber: '', dgClass: '', packingGroup: '' },
  description: '',
  specialHandling: ''
}
```

### 3. Seller & Buyer Details Upgrade ✅
**Change:** Add risk-oriented fields
**New Structure:**
```javascript
RC_STATE.seller/buyer = {
  companyName: '',
  country: { name: '', iso2: '' },
  city: '',
  address: '',
  contactPerson: '',
  contactRole: '',
  email: '',
  phone: '',
  businessType: '',
  taxId: '',
  incoterm: ''
}
```

### 4. Country Selector Component ✅
**Change:** Free text → Searchable dropdown with ISO codes
**Features:**
- 70+ countries with emoji flags
- Search functionality
- Returns { name, iso2 } object

### 5. Incoterms Selection ✅
**Change:** Add Incoterms for both parties
**Options:** EXW, FCA, FAS, FOB, CFR, CIF, CPT, CIP, DAP, DPU, DDP

---

## Implementation Status

### Phase 1: Data Layer ✅ COMPLETE
- [x] Add cargo types to logistics_data.js
- [x] Add packing types to logistics_data.js
- [x] Add insurance coverage types
- [x] Add DG classes (1-9)
- [x] Add business types
- [x] Add comprehensive countries list (70+)
- [x] Add Incoterms 2020

### Phase 2: HTML Structure 🔄 IN PROGRESS
- [ ] Fix Service Route dropdown structure
- [ ] Expand Cargo section (15 fields)
- [ ] Add country selector component
- [ ] Upgrade Seller section (11 fields)
- [ ] Upgrade Buyer section (11 fields)
- [ ] Add Incoterms dropdowns

### Phase 3: JavaScript Controller 🔄 IN PROGRESS
- [ ] Fix selectServiceRoute() handler
- [ ] Implement initCargoFields()
- [ ] Implement initCountryDropdowns()
- [ ] Implement initIncotermDropdowns()
- [ ] Update form validation
- [ ] Update RC_STATE structure

### Phase 4: Testing & Validation ⏳ PENDING
- [ ] Test Service Route selection
- [ ] Test all cargo fields
- [ ] Test country selector
- [ ] Test Incoterms
- [ ] Validate RC_STATE output
- [ ] Test form submission

---

## File Changes Required

### 1. logistics_data.js ✅ COMPLETE
**Status:** Data added
**Lines:** ~150 lines added

### 2. input_v20.html 🔄 IN PROGRESS
**Changes:**
- Service Route: Fix data-field structure
- Cargo: Replace 6 fields → 15 fields
- Seller/Buyer: Add 5 new fields each

**Estimated:** ~400 lines to modify

### 3. input_controller_v20.js 🔄 IN PROGRESS
**Changes:**
- Fix selectServiceRoute()
- Add initCargoFields()
- Add initCountryDropdowns()
- Add initIncotermDropdowns()
- Update validation logic

**Estimated:** ~600 lines to modify/add

---

## Next Steps

1. Complete HTML refactoring
2. Complete JavaScript controller
3. Test all functionality
4. Document changes

---

**Status:** Phase 1 Complete, Phase 2-3 In Progress
**ETA:** 2-3 hours for full implementation

