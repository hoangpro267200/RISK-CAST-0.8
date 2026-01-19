/**
 * ========================================================================
 * RISKCAST v20 - Party Module
 * ========================================================================
 * Manages Seller/Buyer information
 * 
 * @class PartyModule
 */
export class PartyModule {
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
     * Initialize party module
     */
    init() {
        if (!this.data) {
            setTimeout(() => this.init(), 500);
            return;
        }
        
        this.initCountryDropdown('seller');
        this.initCountryDropdown('buyer');
        this.initBusinessTypeDropdown('seller');
        this.initBusinessTypeDropdown('buyer');
        this.bindSellerInputs();
        this.bindBuyerInputs();
        
        console.log('🔥 Party module initialized ✓');
    }
    
    /**
     * Initialize country dropdown for seller or buyer
     */
    initCountryDropdown(party) {
        const dropdownId = `${party}Country`;
        const dropdown = document.getElementById(dropdownId);
        const menu = document.getElementById(`${dropdownId}-menu`);
        const searchInput = document.getElementById(`${dropdownId}Search`);
        
        if (!dropdown || !menu || !this.data.countries) return;
        
        const renderCountries = (filter = '') => {
            menu.innerHTML = '';
            
            const filtered = this.data.countries.filter(country =>
                country.name.toLowerCase().includes(filter.toLowerCase()) ||
                country.iso2.toLowerCase().includes(filter.toLowerCase())
            );
            
            filtered.forEach(country => {
                const btn = document.createElement('button');
                btn.className = 'rc-dropdown-item';
                btn.setAttribute('data-value', country.iso2);
                btn.innerHTML = `${country.emoji} ${country.name}`;
                
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    
                    const countryData = {
                        name: country.name,
                        iso2: country.iso2
                    };
                    
                    this.state.setState(`${party}.country`, countryData);
                    this.dropdown.updateSelection(dropdownId, country.iso2, `${country.emoji} ${country.name}`);
                    
                    if (this.callbacks.onFormDataChange) {
                        this.callbacks.onFormDataChange();
                    }
                });
                
                menu.appendChild(btn);
            });
        };
        
        renderCountries();
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                renderCountries(e.target.value);
            });
        }
    }
    
    /**
     * Initialize business type dropdown
     */
    initBusinessTypeDropdown(party) {
        const dropdownId = `${party}BusinessType`;
        const menu = document.getElementById(`${dropdownId}-menu`);
        
        if (!menu || !this.data.businessTypes) return;
        
        menu.innerHTML = '';
        
        this.data.businessTypes.forEach(type => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', type.value);
            btn.textContent = type.label;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.state.setState(`${party}.businessType`, type.value);
                this.dropdown.updateSelection(dropdownId, type.value, type.label);
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
            
            menu.appendChild(btn);
        });
    }
    
    /**
     * Bind seller input handlers
     */
    bindSellerInputs() {
        const fields = [
            'sellerCompany', 'sellerCity', 'sellerAddress', 'sellerContact',
            'sellerContactRole', 'sellerEmail', 'sellerPhone', 'sellerTaxId'
        ];
        
        fields.forEach(fieldId => {
            const input = document.getElementById(fieldId);
            if (!input) return;
            
            const fieldKey = fieldId.replace('seller', '').charAt(0).toLowerCase() + fieldId.replace('seller', '').slice(1);
            const stateKey = `seller.${fieldKey === 'company' ? 'companyName' : fieldKey}`;
            
            input.addEventListener('input', () => {
                this.state.setState(stateKey, input.value);
            });
            
            input.addEventListener('change', () => {
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
        });
    }
    
    /**
     * Bind buyer input handlers
     */
    bindBuyerInputs() {
        const fields = [
            'buyerCompany', 'buyerCity', 'buyerAddress', 'buyerContact',
            'buyerContactRole', 'buyerEmail', 'buyerPhone', 'buyerTaxId'
        ];
        
        fields.forEach(fieldId => {
            const input = document.getElementById(fieldId);
            if (!input) return;
            
            const fieldKey = fieldId.replace('buyer', '').charAt(0).toLowerCase() + fieldId.replace('buyer', '').slice(1);
            const stateKey = `buyer.${fieldKey === 'company' ? 'companyName' : fieldKey}`;
            
            input.addEventListener('input', () => {
                this.state.setState(stateKey, input.value);
            });
            
            input.addEventListener('change', () => {
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
        });
    }
}



