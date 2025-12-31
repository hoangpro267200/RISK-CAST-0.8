# 🔧 RISKCAST v20 — COMPREHENSIVE REFACTORING GUIDE

## International Standard Cargo Documentation & Risk-Oriented Party Information

---

## 📋 OVERVIEW

This refactoring upgrades RISKCAST v20 input page to international logistics standards:

1. **Fix Service Route Selection** — Dropdown updates main field correctly
2. **Upgrade Cargo & Packing** — 15 international standard fields (HS code, DG, temperature, etc.)
3. **Upgrade Seller & Buyer Details** — Risk-oriented with business type, tax ID, contact role
4. **Add Country Selector** — Searchable dropdown with ISO codes and emojis
5. **Add Incoterms Selection** — For both Seller and Buyer responsibility points

---

## 🎯 IMPLEMENTATION STEPS

### STEP 1: Update HTML Template

**File:** `app/templates/input/input_v20.html`

#### 1.1 Replace CARGO Section (Line ~329-458)

Find the existing `<section id="section-cargo">` and replace it with:

```html
<!-- Include partial -->
{% include 'input/partials/_v20_cargo_section.html' %}
```

Or manually copy content from: `app/templates/input/partials/_v20_cargo_section.html`

#### 1.2 Replace SELLER Section (Line ~459-536)

Find `<section id="section-seller">` and replace with:

```html
{% include 'input/partials/_v20_seller_section.html' %}
```

Or copy from: `app/templates/input/partials/_v20_seller_section.html`

#### 1.3 Replace BUYER Section (Line ~537-614)

Find `<section id="section-buyer">` and replace with:

```html
{% include 'input/partials/_v20_buyer_section.html' %}
```

Or copy from: `app/templates/input/partials/_v20_buyer_section.html`

---

### STEP 2: Update JavaScript Controller

**File:** `app/static/js/pages/input/input_controller_v20.js`

#### 2.1 Update Form Data Structure

In the `constructor()`, replace `this.formData` with:

```javascript
constructor() {
    // Updated form data structure
    this.formData = {
        // Transport (existing - keep as is)
        transport: {
            tradeLane: '',
            mode: '',
            shipmentType: '',
            priority: 'balanced',
            serviceRoute: null,      // Will be object: { id, label, pol, pod, carrier, transitDays }
            carrier: '',
            pol: '',
            pod: '',
            containerType: '',
            etd: '',
            schedule: '',
            transitDays: null,
            seasonality: null,
            eta: '',
            reliability: null
        },
        
        // Cargo (NEW - International Standard)
        cargo: {
            cargoType: '',
            hsCode: '',
            packingType: '',
            packageCount: null,
            weights: {
                grossKg: null,
                netKg: null
            },
            volumeCbm: null,
            stackable: true,
            loadabilityIssues: false,
            insurance: {
                valueUsd: null,
                coverageType: ''
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
            description: '',
            specialHandling: ''
        },
        
        // Seller (NEW - Risk-Oriented)
        seller: {
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
        },
        
        // Buyer (NEW - Risk-Oriented)
        buyer: {
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
        },
        
        // Modules (existing - keep as is)
        modules: {
            esg: false,
            weather: false,
            portCongestion: false,
            carrier: false,
            market: false,
            insurance: false
        }
    };
    
    // ... rest of constructor
}
```

#### 2.2 Fix Service Route Selection

Add this method after `selectServiceRoute()`:

```javascript
/**
 * Select Service Route and update UI + state
 */
selectServiceRoute(routeData) {
    // Build structured route object
    const selectedRoute = {
        id: routeData.route_id,
        label: routeData.route_name || `${routeData.pol} → ${routeData.pod}`,
        pol: routeData.pol,
        pod: routeData.pod,
        carrier: routeData.carrier || '',
        transitDays: routeData.transit_days || 0,
        reliability: routeData.reliability || 0,
        schedule: routeData.schedule || ''
    };
    
    // Update state
    this.formData.transport.serviceRoute = selectedRoute;
    
    // Update UI - set dropdown label
    this.updateDropdownSelection('serviceRoute', selectedRoute.id, selectedRoute.label);
    
    // Auto-fill related fields
    this.autoFillFromRoute(routeData);
    
    console.log('✅ Service route selected:', selectedRoute);
    this.onFormDataChange();
}

/**
 * Update dropdown selection UI helper
 */
updateDropdownSelection(dropdownId, value, label) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;
    
    // Update dataset
    dropdown.dataset.value = value;
    
    // Update visible label
    const valueSpan = dropdown.querySelector('.rc-dropdown-value');
    if (valueSpan) {
        valueSpan.textContent = label;
        valueSpan.classList.add('rc-has-value'); // Add class to show it's filled
    }
    
    // Close dropdown
    dropdown.classList.remove('active');
    
    console.log(`✅ Updated dropdown ${dropdownId}: ${label}`);
}
```

#### 2.3 Initialize Cargo Fields

Add to `init()` method:

```javascript
init() {
    // ... existing init code ...
    
    this.initCargoFields();
    this.initCountryDropdowns();
    this.initIncotermDropdowns();
    
    // ... rest of init
}
```

Add these new methods:

```javascript
/**
 * Initialize Cargo & Packing fields
 */
initCargoFields() {
    console.log('🔧 Initializing Cargo fields...');
    
    // Load cargo types
    this.loadCargoTypes();
    
    // Load packing types
    this.loadPackingTypes();
    
    // Load insurance coverage types
    this.loadInsuranceCoverageTypes();
    
    // Load DG classes
    this.loadDGClasses();
    
    // Initialize stackability pills
    this.initStackabilityPills();
    
    // Initialize sensitivity pills
    this.initSensitivityPills();
    
    // Initialize DG toggle
    this.initDGToggle();
    
    // Bind input fields to state
    this.bindCargoInputs();
    
    console.log('✅ Cargo fields initialized');
}

loadCargoTypes() {
    const menu = document.getElementById('cargoType-menu');
    if (!menu || !this.logisticsData) return;
    
    menu.innerHTML = '';
    
    const cargoTypes = this.logisticsData.cargoTypes || [];
    cargoTypes.forEach(type => {
        const btn = document.createElement('button');
        btn.className = 'rc-dropdown-item';
        btn.setAttribute('data-value', type.value);
        btn.textContent = type.label;
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.formData.cargo.cargoType = type.value;
            this.updateDropdownSelection('cargoType', type.value, type.label);
            this.onFormDataChange();
        });
        
        menu.appendChild(btn);
    });
    
    console.log(`✅ Loaded ${cargoTypes.length} cargo types`);
}

loadPackingTypes() {
    const menu = document.getElementById('packingType-menu');
    if (!menu || !this.logisticsData) return;
    
    menu.innerHTML = '';
    
    const packingTypes = this.logisticsData.packingTypes || [];
    packingTypes.forEach(type => {
        const btn = document.createElement('button');
        btn.className = 'rc-dropdown-item';
        btn.setAttribute('data-value', type.value);
        btn.textContent = type.label;
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.formData.cargo.packingType = type.value;
            this.updateDropdownSelection('packingType', type.value, type.label);
            this.onFormDataChange();
        });
        
        menu.appendChild(btn);
    });
    
    console.log(`✅ Loaded ${packingTypes.length} packing types`);
}

loadInsuranceCoverageTypes() {
    const menu = document.getElementById('insuranceCoverage-menu');
    if (!menu || !this.logisticsData) return;
    
    menu.innerHTML = '';
    
    const coverageTypes = this.logisticsData.insuranceCoverageTypes || [];
    coverageTypes.forEach(type => {
        const btn = document.createElement('button');
        btn.className = 'rc-dropdown-item';
        btn.setAttribute('data-value', type.value);
        btn.textContent = type.label;
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.formData.cargo.insurance.coverageType = type.value;
            this.updateDropdownSelection('insuranceCoverage', type.value, type.label);
            this.onFormDataChange();
        });
        
        menu.appendChild(btn);
    });
    
    console.log(`✅ Loaded ${coverageTypes.length} insurance coverage types`);
}

loadDGClasses() {
    const menu = document.getElementById('dgClass-menu');
    if (!menu || !this.logisticsData) return;
    
    menu.innerHTML = '';
    
    const dgClasses = this.logisticsData.dgClasses || [];
    dgClasses.forEach(dgClass => {
        const btn = document.createElement('button');
        btn.className = 'rc-dropdown-item';
        btn.setAttribute('data-value', dgClass.value);
        btn.textContent = dgClass.label;
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.formData.cargo.dangerousGoods.dgClass = dgClass.value;
            this.updateDropdownSelection('dgClass', dgClass.value, dgClass.label);
            this.onFormDataChange();
        });
        
        menu.appendChild(btn);
    });
    
    console.log(`✅ Loaded ${dgClasses.length} DG classes`);
}

initStackabilityPills() {
    const group = document.getElementById('stackableGroup');
    if (!group) return;
    
    const pills = group.querySelectorAll('.rc-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            const value = pill.getAttribute('data-value') === 'true';
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            this.formData.cargo.stackable = value;
            this.onFormDataChange();
        });
    });
}

initSensitivityPills() {
    const group = document.getElementById('sensitivityGroup');
    if (!group) return;
    
    const pills = group.querySelectorAll('.rc-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            const value = pill.getAttribute('data-value');
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            this.formData.cargo.sensitivity = value;
            
            // Show/hide temperature fields
            const tempFields = [
                document.getElementById('tempRangeFields'),
                document.getElementById('tempRangeFields2')
            ];
            if (value === 'temperature') {
                tempFields.forEach(f => f && (f.style.display = ''));
            } else {
                tempFields.forEach(f => f && (f.style.display = 'none'));
            }
            
            this.onFormDataChange();
        });
    });
}

initDGToggle() {
    const group = document.getElementById('dgGroup');
    if (!group) return;
    
    const pills = group.querySelectorAll('.rc-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            const isDG = pill.getAttribute('data-value') === 'true';
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            this.formData.cargo.dangerousGoods.isDG = isDG;
            
            // Show/hide DG fields
            const dgFields = [
                document.getElementById('dgFields1'),
                document.getElementById('dgFields2'),
                document.getElementById('dgFields3')
            ];
            if (isDG) {
                dgFields.forEach(f => f && (f.style.display = ''));
            } else {
                dgFields.forEach(f => f && (f.style.display = 'none'));
            }
            
            this.onFormDataChange();
        });
    });
}

bindCargoInputs() {
    // Bind weight inputs
    const grossWeight = document.getElementById('grossWeight');
    const netWeight = document.getElementById('netWeight');
    const volumeCbm = document.getElementById('volumeCbm');
    const packageCount = document.getElementById('packageCount');
    const hsCode = document.getElementById('hsCode');
    const insuranceValue = document.getElementById('insuranceValue');
    const cargoDescription = document.getElementById('cargoDescription');
    const specialHandling = document.getElementById('specialHandling');
    const tempMin = document.getElementById('tempMin');
    const tempMax = document.getElementById('tempMax');
    const dgUnNumber = document.getElementById('dgUnNumber');
    const loadabilityIssues = document.getElementById('loadabilityIssues');
    
    if (grossWeight) {
        grossWeight.addEventListener('change', () => {
            this.formData.cargo.weights.grossKg = parseFloat(grossWeight.value) || null;
            this.onFormDataChange();
        });
    }
    
    if (netWeight) {
        netWeight.addEventListener('change', () => {
            this.formData.cargo.weights.netKg = parseFloat(netWeight.value) || null;
            this.onFormDataChange();
        });
    }
    
    if (volumeCbm) {
        volumeCbm.addEventListener('change', () => {
            this.formData.cargo.volumeCbm = parseFloat(volumeCbm.value) || null;
            this.onFormDataChange();
        });
    }
    
    if (packageCount) {
        packageCount.addEventListener('change', () => {
            this.formData.cargo.packageCount = parseInt(packageCount.value) || null;
            this.onFormDataChange();
        });
    }
    
    if (hsCode) {
        hsCode.addEventListener('change', () => {
            this.formData.cargo.hsCode = hsCode.value;
            this.onFormDataChange();
        });
    }
    
    if (insuranceValue) {
        insuranceValue.addEventListener('change', () => {
            this.formData.cargo.insurance.valueUsd = parseFloat(insuranceValue.value) || null;
            this.onFormDataChange();
        });
    }
    
    if (cargoDescription) {
        cargoDescription.addEventListener('change', () => {
            this.formData.cargo.description = cargoDescription.value;
            this.onFormDataChange();
        });
    }
    
    if (specialHandling) {
        specialHandling.addEventListener('change', () => {
            this.formData.cargo.specialHandling = specialHandling.value;
            this.onFormDataChange();
        });
    }
    
    if (tempMin) {
        tempMin.addEventListener('change', () => {
            this.formData.cargo.temperatureRange.minC = parseFloat(tempMin.value) || null;
            this.onFormDataChange();
        });
    }
    
    if (tempMax) {
        tempMax.addEventListener('change', () => {
            this.formData.cargo.temperatureRange.maxC = parseFloat(tempMax.value) || null;
            this.onFormDataChange();
        });
    }
    
    if (dgUnNumber) {
        dgUnNumber.addEventListener('change', () => {
            this.formData.cargo.dangerousGoods.unNumber = dgUnNumber.value;
            this.onFormDataChange();
        });
    }
    
    if (loadabilityIssues) {
        loadabilityIssues.addEventListener('change', () => {
            this.formData.cargo.loadabilityIssues = loadabilityIssues.checked;
            this.onFormDataChange();
        });
    }
    
    // Bind DG Packing Group dropdown
    const dgPackingGroup = document.getElementById('dgPackingGroup');
    if (dgPackingGroup) {
        const items = dgPackingGroup.querySelectorAll('.rc-dropdown-item');
        items.forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const value = item.getAttribute('data-value');
                this.formData.cargo.dangerousGoods.packingGroup = value;
                this.updateDropdownSelection('dgPackingGroup', value, `Packing Group ${value}`);
                this.onFormDataChange();
            });
        });
    }
}
```

#### 2.4 Initialize Country Dropdowns

```javascript
/**
 * Initialize Country Dropdowns for Seller & Buyer
 */
initCountryDropdowns() {
    console.log('🌍 Initializing Country dropdowns...');
    
    if (!this.logisticsData || !this.logisticsData.countries) {
        console.warn('⚠️ Countries data not available');
        return;
    }
    
    // Initialize seller country
    this.initCountryDropdown('sellerCountry', 'seller');
    
    // Initialize buyer country
    this.initCountryDropdown('buyerCountry', 'buyer');
    
    console.log('✅ Country dropdowns initialized');
}

initCountryDropdown(dropdownId, partyType) {
    const dropdown = document.getElementById(dropdownId);
    const menu = document.getElementById(`${dropdownId}-menu`);
    const searchInput = document.getElementById(`${dropdownId}Search`);
    
    if (!dropdown || !menu) return;
    
    const countries = this.logisticsData.countries;
    
    // Render all countries
    const renderCountries = (filter = '') => {
        menu.innerHTML = '';
        
        const filtered = countries.filter(c => 
            c.name.toLowerCase().includes(filter.toLowerCase()) ||
            c.iso2.toLowerCase().includes(filter.toLowerCase())
        );
        
        filtered.forEach(country => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', country.iso2);
            btn.innerHTML = `${country.emoji} ${country.name}`;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // Update state
                if (partyType === 'seller') {
                    this.formData.seller.country = { name: country.name, iso2: country.iso2 };
                } else {
                    this.formData.buyer.country = { name: country.name, iso2: country.iso2 };
                }
                
                // Update UI
                this.updateDropdownSelection(dropdownId, country.iso2, `${country.emoji} ${country.name}`);
                
                // Clear search
                if (searchInput) searchInput.value = '';
                
                this.onFormDataChange();
            });
            
            menu.appendChild(btn);
        });
        
        if (filtered.length === 0) {
            menu.innerHTML = '<div style="padding: 1rem; text-align: center; opacity: 0.6;">No countries found</div>';
        }
    };
    
    // Initial render
    renderCountries();
    
    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            renderCountries(e.target.value);
        });
    }
}
```

#### 2.5 Initialize Incoterms Dropdowns

```javascript
/**
 * Initialize Incoterms Dropdowns for Seller & Buyer
 */
initIncotermDropdowns() {
    console.log('📦 Initializing Incoterm dropdowns...');
    
    if (!this.logisticsData || !this.logisticsData.incoterms) {
        console.warn('⚠️ Incoterms data not available');
        return;
    }
    
    // Initialize seller incoterm
    this.initIncotermDropdown('sellerIncoterm', 'seller');
    
    // Initialize buyer incoterm
    this.initIncotermDropdown('buyerIncoterm', 'buyer');
    
    console.log('✅ Incoterm dropdowns initialized');
}

initIncotermDropdown(dropdownId, partyType) {
    const menu = document.getElementById(`${dropdownId}-menu`);
    if (!menu) return;
    
    menu.innerHTML = '';
    
    const incoterms = this.logisticsData.incoterms;
    
    incoterms.forEach(incoterm => {
        const btn = document.createElement('button');
        btn.className = 'rc-dropdown-item';
        btn.setAttribute('data-value', incoterm.code);
        btn.textContent = incoterm.label;
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            
            // Update state
            if (partyType === 'seller') {
                this.formData.seller.incoterm = incoterm.code;
            } else {
                this.formData.buyer.incoterm = incoterm.code;
            }
            
            // Update UI
            this.updateDropdownSelection(dropdownId, incoterm.code, incoterm.label);
            
            this.onFormDataChange();
        });
        
        menu.appendChild(btn);
    });
}
```

#### 2.6 Bind Seller & Buyer Input Fields

Add this method:

```javascript
/**
 * Bind Seller & Buyer input fields
 */
bindSellerBuyerInputs() {
    // Seller fields
    const sellerFields = {
        companyName: 'sellerCompany',
        city: 'sellerCity',
        address: 'sellerAddress',
        contactPerson: 'sellerContact',
        contactRole: 'sellerContactRole',
        email: 'sellerEmail',
        phone: 'sellerPhone',
        taxId: 'sellerTaxId'
    };
    
    Object.entries(sellerFields).forEach(([key, id]) => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('change', () => {
                this.formData.seller[key] = input.value;
                this.onFormDataChange();
            });
        }
    });
    
    // Buyer fields
    const buyerFields = {
        companyName: 'buyerCompany',
        city: 'buyerCity',
        address: 'buyerAddress',
        contactPerson: 'buyerContact',
        contactRole: 'buyerContactRole',
        email: 'buyerEmail',
        phone: 'buyerPhone',
        taxId: 'buyerTaxId'
    };
    
    Object.entries(buyerFields).forEach(([key, id]) => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('change', () => {
                this.formData.buyer[key] = input.value;
                this.onFormDataChange();
            });
        }
    });
    
    // Business types
    this.initBusinessTypeDropdown('sellerBusinessType', 'seller');
    this.initBusinessTypeDropdown('buyerBusinessType', 'buyer');
}

initBusinessTypeDropdown(dropdownId, partyType) {
    const menu = document.getElementById(`${dropdownId}-menu`);
    if (!menu || !this.logisticsData) return;
    
    menu.innerHTML = '';
    
    const businessTypes = this.logisticsData.businessTypes || [];
    businessTypes.forEach(type => {
        const btn = document.createElement('button');
        btn.className = 'rc-dropdown-item';
        btn.setAttribute('data-value', type.value);
        btn.textContent = type.label;
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            
            if (partyType === 'seller') {
                this.formData.seller.businessType = type.value;
            } else {
                this.formData.buyer.businessType = type.value;
            }
            
            this.updateDropdownSelection(dropdownId, type.value, type.label);
            this.onFormDataChange();
        });
        
        menu.appendChild(btn);
    });
}
```

#### 2.7 Update Validation

Update `validateForm()` method:

```javascript
validateForm() {
    const errors = [];
    
    // Transport (required)
    if (!this.formData.transport.tradeLane) errors.push('tradeLane');
    if (!this.formData.transport.mode) errors.push('mode');
    if (!this.formData.transport.pol) errors.push('pol');
    if (!this.formData.transport.pod) errors.push('pod');
    
    // Cargo (required fields)
    if (!this.formData.cargo.cargoType) errors.push('cargoType');
    if (!this.formData.cargo.packingType) errors.push('packingType');
    if (!this.formData.cargo.weights.grossKg) errors.push('grossWeight');
    if (!this.formData.cargo.insurance.valueUsd) errors.push('insuranceValue');
    
    // DG validation
    if (this.formData.cargo.dangerousGoods.isDG) {
        if (!this.formData.cargo.dangerousGoods.unNumber) errors.push('dgUnNumber');
        if (!this.formData.cargo.dangerousGoods.dgClass) errors.push('dgClass');
    }
    
    // Temperature validation
    if (this.formData.cargo.sensitivity === 'temperature') {
        if (this.formData.cargo.temperatureRange.minC === null) errors.push('tempMin');
        if (this.formData.cargo.temperatureRange.maxC === null) errors.push('tempMax');
    }
    
    // Seller (required fields)
    if (!this.formData.seller.companyName) errors.push('sellerCompany');
    if (!this.formData.seller.country.name) errors.push('sellerCountry');
    
    // Buyer (required fields)
    if (!this.formData.buyer.companyName) errors.push('buyerCompany');
    if (!this.formData.buyer.country.name) errors.push('buyerCountry');
    
    return errors;
}
```

---

### STEP 3: Update CSS (if needed)

**File:** `app/static/css/pages/input/input_v20.css`

Add these styles if not already present:

```css
/* Country dropdown with emoji support */
.rc-country-list .rc-dropdown-item {
    font-size: 0.9375rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Has value indicator */
.rc-dropdown-value.rc-has-value {
    color: var(--rc-text-primary);
    font-weight: 500;
}

/* Required field indicator */
.rc-required {
    color: #ef4444;
    margin-left: 4px;
}

/* Temperature and DG fields animation */
#tempRangeFields,
#tempRangeFields2,
#dgFields1,
#dgFields2,
#dgFields3 {
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

---

### STEP 4: Update Form Submission

In the existing form submission code, make sure `window.RC_STATE` is set to the new structure:

```javascript
submitForm() {
    console.log('📊 Submitting form:', this.formData);
    
    // Validate
    const errors = this.validateForm();
    if (errors.length > 0) {
        this.showToast(`Missing required fields: ${errors.join(', ')}`, 'error');
        this.highlightErrors(errors);
        return;
    }
    
    // Set global state
    window.RC_STATE = this.formData;
    
    // Show loading
    this.showToast('Running AI risk analysis...', 'success');
    
    // Submit to backend
    setTimeout(() => {
        window.location.href = '/results';
    }, 1500);
}
```

---

## ✅ TESTING CHECKLIST

### Service Route Selection
- [ ] Open Service Route dropdown
- [ ] Click a route
- [ ] Verify dropdown label updates with route name
- [ ] Verify `window.RC_STATE.transport.serviceRoute` contains full object
- [ ] Verify dropdown closes after selection

### Cargo & Packing
- [ ] All dropdowns (Cargo Type, Packing Type, Insurance Coverage, DG Class) load data
- [ ] Stackability pills toggle correctly
- [ ] Sensitivity pills toggle correctly
- [ ] Temperature fields appear when "Temperature Sensitive" selected
- [ ] DG toggle works
- [ ] DG fields appear when "DG Cargo" selected
- [ ] All inputs bind to `window.RC_STATE.cargo.*`

### Seller Details
- [ ] Country dropdown loads with search
- [ ] Search filters countries correctly
- [ ] Selected country shows emoji + name
- [ ] Business Type dropdown loads
- [ ] Incoterm dropdown loads
- [ ] All inputs bind to `window.RC_STATE.seller.*`

### Buyer Details
- [ ] Same checks as Seller
- [ ] All inputs bind to `window.RC_STATE.buyer.*`

### Validation
- [ ] Submit without required fields shows error
- [ ] DG validation: if isDG=true, requires UN number + class
- [ ] Temperature validation: if sensitivity=temperature, requires min/max
- [ ] Seller/Buyer validation: requires company name + country

---

## 📊 DATA STRUCTURE REFERENCE

### RC_STATE.transport.serviceRoute

```javascript
{
    id: 'VN-CN-CM-SZ-001',
    label: 'Cái Mép → Shenzhen Express',
    pol: 'Cái Mép',
    pod: 'Shenzhen',
    carrier: 'Maersk Line',
    transitDays: 7,
    reliability: 88,
    schedule: '3 sailings/week'
}
```

### RC_STATE.cargo

```javascript
{
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
    description: 'Electronic components...',
    specialHandling: ''
}
```

### RC_STATE.seller / RC_STATE.buyer

```javascript
{
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
}
```

---

## 🎯 COMPLETION CRITERIA

✅ Service Route selection updates UI correctly
✅ 15 Cargo fields collect international standard data
✅ Seller/Buyer sections have risk-oriented fields
✅ Country selector with search + ISO codes
✅ Incoterms selection for both parties
✅ All data from LOGISTICS_DATA (no hardcoded arrays)
✅ Form validation includes new required fields
✅ No breaking changes to existing functionality
✅ VisionOS neon UI style maintained

---

**Status:** Ready for implementation
**Version:** RISKCAST v20 — International Standard Edition
**Date:** December 3, 2025






