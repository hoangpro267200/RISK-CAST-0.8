/**
 * ========================================================================
 * RISKCAST v20 - Cargo Module
 * ========================================================================
 * Manages cargo fields (international standard)
 * 
 * @class CargoModule
 */
export class CargoModule {
    /**
     * @param {Object} stateManager - State manager instance
     * @param {Object} logisticsData - Logistics data object
     * @param {Object} dropdownManager - Dropdown manager instance
     * @param {Object} callbacks - Callback functions
     */
    constructor(stateManager, logisticsData, dropdownManager, callbacks = {}) {
        this.state = stateManager;
        this.data = logisticsData;
        this.dropdown = dropdownManager;
        this.callbacks = callbacks;
    }
    
    /**
     * Initialize cargo module
     */
    init() {
        if (!this.data) {
            setTimeout(() => this.init(), 500);
            return;
        }
        
        this.loadCargoTypes();
        this.loadPackingTypes();
        this.loadInsuranceCoverageTypes();
        this.loadDGClasses();
        this.initStackabilityPills();
        this.initSensitivityPills();
        this.initDGPills();
        this.initConditionalFields();
        
        console.log('🔥 Cargo module initialized ✓');
    }
    
    /**
     * Load Cargo Types
     */
    loadCargoTypes() {
        const menu = document.getElementById('cargoType-menu');
        if (!menu || !this.data.cargoTypes) return;
        
        menu.innerHTML = '';
        
        this.data.cargoTypes.forEach(type => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', type.value);
            btn.textContent = type.label;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.state.setState('cargo.cargoType', type.value);
                this.dropdown.updateSelection('cargoType', type.value, type.label);
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
            
            menu.appendChild(btn);
        });
    }
    
    /**
     * Load Packing Types
     */
    loadPackingTypes() {
        const menu = document.getElementById('packingType-menu');
        if (!menu || !this.data.packingTypes) return;
        
        menu.innerHTML = '';
        
        this.data.packingTypes.forEach(type => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', type.value);
            btn.textContent = type.label;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.state.setState('cargo.packingType', type.value);
                this.dropdown.updateSelection('packingType', type.value, type.label);
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
            
            menu.appendChild(btn);
        });
    }
    
    /**
     * Load Insurance Coverage Types
     */
    loadInsuranceCoverageTypes() {
        const menu = document.getElementById('insuranceCoverage-menu');
        if (!menu || !this.data.insuranceCoverageTypes) return;
        
        menu.innerHTML = '';
        
        this.data.insuranceCoverageTypes.forEach(type => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', type.value);
            btn.textContent = type.label;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.state.setState('cargo.insurance.coverageType', type.value);
                this.dropdown.updateSelection('insuranceCoverage', type.value, type.label);
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
            
            menu.appendChild(btn);
        });
    }
    
    /**
     * Load DG Classes
     */
    loadDGClasses() {
        const menu = document.getElementById('dgClass-menu');
        if (!menu || !this.data.dgClasses) return;
        
        menu.innerHTML = '';
        
        this.data.dgClasses.forEach(cls => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', cls.value);
            btn.textContent = cls.label;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.state.setState('cargo.dangerousGoods.dgClass', cls.value);
                this.dropdown.updateSelection('dgClass', cls.value, cls.label);
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
            
            menu.appendChild(btn);
        });
    }
    
    /**
     * Initialize Stackability Pills
     */
    initStackabilityPills() {
        const group = document.getElementById('stackableGroup');
        if (!group) return;
        
        const pills = group.querySelectorAll('.rc-pill');
        pills.forEach(pill => {
            pill.addEventListener('click', () => {
                const value = pill.getAttribute('data-value') === 'true';
                pills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.state.setState('cargo.stackable', value);
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
        });
    }
    
    /**
     * Initialize Sensitivity Pills with conditional temperature fields
     */
    initSensitivityPills() {
        const group = document.getElementById('sensitivityGroup');
        if (!group) return;
        
        const pills = group.querySelectorAll('.rc-pill');
        pills.forEach(pill => {
            pill.addEventListener('click', () => {
                const value = pill.getAttribute('data-value');
                pills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.state.setState('cargo.sensitivity', value);
                
                // Show/hide temperature fields
                const tempFields = document.getElementById('tempRangeFields');
                const tempFields2 = document.getElementById('tempRangeFields2');
                if (value === 'temperature') {
                    if (tempFields) tempFields.style.display = '';
                    if (tempFields2) tempFields2.style.display = '';
                } else {
                    if (tempFields) tempFields.style.display = 'none';
                    if (tempFields2) tempFields2.style.display = 'none';
                }
                
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
        });
    }
    
    /**
     * Initialize DG Pills with conditional DG fields
     */
    initDGPills() {
        const group = document.getElementById('dgGroup');
        if (!group) return;
        
        const pills = group.querySelectorAll('.rc-pill');
        pills.forEach(pill => {
            pill.addEventListener('click', () => {
                const value = pill.getAttribute('data-value') === 'true';
                pills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.state.setState('cargo.dangerousGoods.isDG', value);
                
                // Show/hide DG fields
                const dgFields1 = document.getElementById('dgFields1');
                const dgFields2 = document.getElementById('dgFields2');
                const dgFields3 = document.getElementById('dgFields3');
                
                if (value) {
                    if (dgFields1) dgFields1.style.display = '';
                    if (dgFields2) dgFields2.style.display = '';
                    if (dgFields3) dgFields3.style.display = '';
                } else {
                    if (dgFields1) dgFields1.style.display = 'none';
                    if (dgFields2) dgFields2.style.display = 'none';
                    if (dgFields3) dgFields3.style.display = 'none';
                }
                
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
        });
    }
    
    /**
     * Initialize conditional fields visibility
     */
    initConditionalFields() {
        // Hide temperature fields by default
        const tempFields = document.getElementById('tempRangeFields');
        const tempFields2 = document.getElementById('tempRangeFields2');
        if (tempFields) tempFields.style.display = 'none';
        if (tempFields2) tempFields2.style.display = 'none';
        
        // Hide DG fields by default
        const dgFields1 = document.getElementById('dgFields1');
        const dgFields2 = document.getElementById('dgFields2');
        const dgFields3 = document.getElementById('dgFields3');
        if (dgFields1) dgFields1.style.display = 'none';
        if (dgFields2) dgFields2.style.display = 'none';
        if (dgFields3) dgFields3.style.display = 'none';
    }
}



