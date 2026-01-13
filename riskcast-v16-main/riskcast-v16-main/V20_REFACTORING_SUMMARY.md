# ✅ RISKCAST v20 REFACTORING — IMPLEMENTATION READY

## 🎯 EXECUTIVE SUMMARY

Comprehensive refactoring của RISKCAST v20 input page đã được chuẩn bị đầy đủ:

1. **Service Route Selection Fix** — Dropdown hiển thị giá trị đã chọn
2. **International Standard Cargo** — 15 trường theo tiêu chuẩn quốc tế
3. **Risk-Oriented Party Info** — Seller/Buyer với business type, tax ID, contact role
4. **Country Selector Component** — Dropdown với search, ISO codes, emojis
5. **Incoterms Selection** — Cho cả Seller & Buyer

---

## 📁 FILES ĐÃ TẠO

### 1. HTML Partial Templates

✅ **`app/templates/input/partials/_v20_cargo_section.html`**
- 15 trường Cargo & Packing theo tiêu chuẩn quốc tế
- HS Code, DG (Dangerous Goods), Temperature Control
- Insurance Coverage Types, Stackability
- Conditional fields (temperature, DG details)

✅ **`app/templates/input/partials/_v20_seller_section.html`**
- Company info với Business Type
- Country selector (searchable với emoji)
- Contact Person + Role
- Tax ID / VAT
- Incoterm selection

✅ **`app/templates/input/partials/_v20_buyer_section.html`**
- Cùng cấu trúc với Seller
- Tất cả trường risk-oriented

### 2. Documentation

✅ **`RISKCAST_V20_REFACTORING_GUIDE.md`** (32KB)
- Step-by-step implementation guide
- Full JavaScript code cho tất cả features
- Data structure reference
- Testing checklist
- Validation logic

✅ **`V20_REFACTORING_SUMMARY.md`** (file này)
- Executive summary
- Quick start guide

---

## 🚀 QUICK START — 3 BƯỚC CHÍNH

### BƯỚC 1: Cập nhật HTML Template

**File:** `app/templates/input/input_v20.html`

```html
<!-- Thay section CARGO (Line ~329-458) -->
{% include 'input/partials/_v20_cargo_section.html' %}

<!-- Thay section SELLER (Line ~459-536) -->
{% include 'input/partials/_v20_seller_section.html' %}

<!-- Thay section BUYER (Line ~537-614) -->
{% include 'input/partials/_v20_buyer_section.html' %}
```

**Hoặc:** Copy-paste nội dung từ các file partial vào template chính.

---

### BƯỚC 2: Cập nhật JavaScript Controller

**File:** `app/static/js/pages/input/input_controller_v20.js`

Mở file `RISKCAST_V20_REFACTORING_GUIDE.md` và làm theo:

1. **Section 2.1:** Update `constructor()` — Thay `this.formData` structure
2. **Section 2.2:** Add `selectServiceRoute()` và `updateDropdownSelection()` methods
3. **Section 2.3:** Add `initCargoFields()` và các cargo-related methods
4. **Section 2.4:** Add `initCountryDropdowns()` method
5. **Section 2.5:** Add `initIncotermDropdowns()` method
6. **Section 2.6:** Add `bindSellerBuyerInputs()` method
7. **Section 2.7:** Update `validateForm()` method

**Tất cả code đã có sẵn trong guide — chỉ việc copy-paste!**

---

### BƯỚC 3: Update `init()` Method

Trong `init()` method của controller, thêm:

```javascript
init() {
    // ... existing init code ...
    
    // NEW: Initialize cargo fields
    this.initCargoFields();
    
    // NEW: Initialize country dropdowns
    this.initCountryDropdowns();
    
    // NEW: Initialize incoterm dropdowns
    this.initIncotermDropdowns();
    
    // NEW: Bind seller/buyer inputs
    this.bindSellerBuyerInputs();
    
    // ... rest of init ...
}
```

---

## 📊 DATA SOURCE

**TẤT CẢ data đã có sẵn trong `logistics_data.js`:**

```javascript
✅ LOGISTICS_DATA.cargoTypes         // 34 cargo types
✅ LOGISTICS_DATA.packingTypes       // 15 packing types
✅ LOGISTICS_DATA.insuranceCoverageTypes  // 3 types
✅ LOGISTICS_DATA.dgClasses          // 9 DG classes
✅ LOGISTICS_DATA.businessTypes      // 7 business types
✅ LOGISTICS_DATA.countries          // 50+ countries with emoji + ISO2
✅ LOGISTICS_DATA.incoterms          // 11 Incoterms 2020
```

**KHÔNG cần tạo data mới — tất cả đã sẵn sàng!**

---

## 🧪 TESTING

Sau khi implement, test các scenarios sau:

### 1. Service Route Selection
```
1. Chọn Trade Lane → Mode → Shipment Type
2. Mở Service Route dropdown
3. Click một route
4. ✅ Verify: Dropdown label hiển thị route name
5. ✅ Verify console: window.RC_STATE.transport.serviceRoute là object
```

### 2. Cargo Fields
```
1. Select Cargo Type → ✅ Dropdown updates
2. Select Packing Type → ✅ Dropdown updates
3. Enter Gross Weight → ✅ State updates
4. Click "Temperature Sensitive" → ✅ Temp fields appear
5. Toggle "DG Cargo" → ✅ DG fields appear
6. Enter DG details → ✅ State updates
```

### 3. Country Selector
```
1. Click Seller Country dropdown
2. Type "china" in search → ✅ Filters to China
3. Click "🇨🇳 China" → ✅ Updates with emoji
4. Check console: RC_STATE.seller.country = { name: 'China', iso2: 'CN' }
```

### 4. Incoterms
```
1. Click Seller Incoterm
2. Select "FOB – Free On Board"
3. ✅ Verify: RC_STATE.seller.incoterm = 'FOB'
```

### 5. Form Validation
```
1. Leave required fields empty
2. Click "Run Risk Analysis"
3. ✅ Verify: Toast shows "Missing required fields: ..."
4. ✅ Verify: Fields highlighted in red
```

---

## 🎯 KEY FEATURES

### Service Route Fix
```javascript
// BEFORE: Dropdown doesn't update
// AFTER: 
selectedRoute = {
    id: 'VN-CN-CM-SZ-001',
    label: 'Cái Mép → Shenzhen Express',
    pol: 'Cái Mép',
    pod: 'Shenzhen',
    carrier: 'Maersk Line',
    transitDays: 7,
    reliability: 88
}
// Dropdown hiển thị: "Cái Mép → Shenzhen Express"
```

### International Cargo Standard
```javascript
cargo: {
    cargoType: 'electronics',      // ✅ Dropdown
    hsCode: '8504.40',             // ✅ Text input
    packingType: 'palletized',     // ✅ Dropdown
    packageCount: 120,             // ✅ Number
    weights: {
        grossKg: 20915,            // ✅ Required
        netKg: 19500               // ✅ Optional
    },
    volumeCbm: 22.66,              // ✅ Number
    stackable: true,               // ✅ Pills
    insurance: {
        valueUsd: 85000,           // ✅ Required
        coverageType: 'all_risk'   // ✅ Dropdown
    },
    sensitivity: 'temperature',    // ✅ Pills (shows temp fields)
    temperatureRange: {
        minC: 2,                   // ✅ Conditional
        maxC: 8                    // ✅ Conditional
    },
    dangerousGoods: {
        isDG: true,                // ✅ Toggle (shows DG fields)
        unNumber: 'UN1234',        // ✅ Conditional + Required
        dgClass: '3',              // ✅ Conditional + Required
        packingGroup: 'II'         // ✅ Conditional
    },
    description: '...',            // ✅ Textarea
    specialHandling: '...',        // ✅ Textarea
    loadabilityIssues: false       // ✅ Checkbox
}
```

### Risk-Oriented Party Info
```javascript
seller: {
    companyName: 'Global Tech Ltd',    // ✅ Required
    country: {
        name: 'China',                 // ✅ From dropdown
        iso2: 'CN'                     // ✅ Auto-filled
    },
    city: 'Shanghai',
    address: '123 Business St',
    contactPerson: 'John Doe',
    contactRole: 'Export Manager',     // ✅ NEW
    email: 'john@company.com',
    phone: '+86 21 1234 5678',
    businessType: 'manufacturer',      // ✅ NEW (dropdown)
    taxId: 'CN123456789',              // ✅ NEW
    incoterm: 'FOB'                    // ✅ NEW (dropdown)
}
// buyer: same structure
```

---

## 📦 DELIVERABLES

### ✅ Đã hoàn thành:

1. **3 HTML Partial Templates** — Ready to use
2. **Complete JavaScript Code** — Copy-paste ready
3. **Comprehensive Guide** — 32KB step-by-step instructions
4. **Data Structure Reference** — Full examples
5. **Testing Checklist** — All scenarios covered
6. **Validation Logic** — Complete implementation

### 📝 Cần làm:

1. Replace HTML sections trong `input_v20.html` (5 phút)
2. Copy-paste JavaScript methods vào `input_controller_v20.js` (15 phút)
3. Update `init()` method (2 phút)
4. Test trên browser (10 phút)

**Total time:** ~30-40 phút

---

## 🔥 ADVANTAGES

### 1. International Standard
- HS Code support
- DG (Dangerous Goods) declaration theo IATA/IMDG
- Temperature-controlled cargo
- Insurance coverage types (All Risk / Total Loss / FPA)
- Stackability & loadability info

### 2. Risk Engine Ready
- Business type for risk profiling
- Country ISO codes for sanctions checking
- Incoterms for liability determination
- Tax ID for compliance verification
- Contact roles for decision-maker identification

### 3. User Experience
- Searchable country selector with emojis
- Conditional field visibility (temperature, DG)
- Comprehensive validation
- Clear error messages
- Maintains VisionOS design

### 4. Maintainability
- All data from single source (logistics_data.js)
- Modular HTML partials
- Clean separation of concerns
- Well-documented code

---

## 🎯 SUCCESS METRICS

After implementation, verify:

✅ Service Route dropdown updates correctly
✅ All 15 cargo fields functional
✅ Country selector works with search
✅ Incoterms selection saves correctly
✅ Form validation catches all required fields
✅ No console errors
✅ `window.RC_STATE` has complete data structure
✅ Form submission includes all new fields
✅ VisionOS design preserved

---

## 📞 SUPPORT

Nếu gặp vấn đề:

1. **Check console:** `console.log(window.RC_STATE)` để xem data structure
2. **Verify data:** `console.log(LOGISTICS_DATA.countries)` để check data đã load
3. **Review guide:** Mở `RISKCAST_V20_REFACTORING_GUIDE.md` section tương ứng
4. **Check HTML:** Verify các partial templates đã được include đúng

---

## 🚀 READY TO DEPLOY

**Tất cả code đã sẵn sàng!**

Chỉ cần:
1. Replace HTML sections
2. Copy-paste JavaScript methods
3. Test
4. Deploy

**Estimated implementation time: 30-40 minutes**

---

**Version:** RISKCAST v20 — International Standard Edition
**Status:** ✅ **READY FOR IMPLEMENTATION**
**Date:** December 3, 2025

---

**START HERE:** Open `RISKCAST_V20_REFACTORING_GUIDE.md` để bắt đầu!






