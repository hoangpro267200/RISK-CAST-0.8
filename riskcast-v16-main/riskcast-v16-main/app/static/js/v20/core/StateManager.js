/**
 * ========================================================================
 * RISKCAST v20 - State Manager
 * ========================================================================
 * Manages form state and localStorage persistence
 * 
 * @class StateManager
 */
import { RC_getState, RC_setState } from '../utils/SanitizeHelpers.js';

export class StateManager {
    constructor() {
        this.formData = this.getDefaultState();
        this.loadFromRISKCAST_STATE(); // Load from RISKCAST_STATE first
        this.loadFromLocalStorage(); // Then load from rc-input-state (fallback)
    }
    
    /**
     * Get default state structure
     * @returns {Object} Default form data
     */
    getDefaultState() {
        return {
            // Transport
            tradeLane: '',
            mode: '',
            shipmentType: '',
            priority: 'balanced',
            serviceRoute: '',
            serviceRouteData: null,
            carrier: '',
            pol: '',
            pod: '',
            containerType: '',
            etd: '',
            schedule: '',
            transitDays: null,
            seasonality: null,
            eta: '',
            reliability: null,
            
            // Cargo (International Standard)
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
            
            // Incoterm (single unified system)
            incoterm: '',
            incotermLocation: '',
            sellerResponsibilities: {},
            buyerResponsibilities: {},
            
            // Seller (Risk-Oriented)
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
                taxId: ''
            },
            
            // Buyer (Risk-Oriented)
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
                taxId: ''
            },
            
            // Modules - Auto-select all 6 modules by default
            modules: {
                esg: true,
                weather: true,
                portCongestion: true,
                carrier: true,
                market: true,
                insurance: true
            }
        };
    }
    
    /**
     * Get current state
     * @returns {Object} Current form data
     */
    getState() {
        return this.formData;
    }
    
    /**
     * Set state value
     * @param {string} key - State key (supports dot notation)
     * @param {*} value - Value to set
     */
    setState(key, value) {
        const keys = key.split('.');
        let obj = this.formData;
        
        for (let i = 0; i < keys.length - 1; i++) {
            if (!obj[keys[i]]) {
                obj[keys[i]] = {};
            }
            obj = obj[keys[i]];
        }
        
        obj[keys[keys.length - 1]] = value;
        
        // Auto-persist on every state change
        this.persist();
        // Also sync to RISKCAST_STATE
        this.syncToRISKCAST_STATE();
    }
    
    /**
     * Sync formData to RISKCAST_STATE (global state)
     */
    syncToRISKCAST_STATE() {
        try {
            const riskcastState = this.mapFormDataToRISKCAST_STATE();
            RC_setState(riskcastState);
        } catch (err) {
            console.warn('Failed to sync to RISKCAST_STATE:', err);
        }
    }
    
    /**
     * Map formData structure to RISKCAST_STATE structure
     * @returns {Object} RISKCAST_STATE object
     */
    mapFormDataToRISKCAST_STATE() {
        const f = this.formData;
        const c = f.cargo || {};
        const weights = c.weights || {};
        const insurance = c.insurance || {};
        
        return {
            transport: {
                tradeLane: f.tradeLane || '',
                mode: f.mode || '',
                modeOfTransport: f.mode || '',
                shipmentType: f.shipmentType || '',
                priority: f.priority || 'balanced',
                serviceRoute: f.serviceRoute || '',
                carrier: f.carrier || '',
                pol: f.pol || '',
                pod: f.pod || '',
                containerType: f.containerType || '',
                incoterm: f.incoterm || '',
                incotermLocation: f.incotermLocation || '',
                etd: f.etd || '',
                eta: f.eta || '',
                transitTime: f.transitDays || null,
                transitTimeDays: f.transitDays || null,
                reliabilityScore: f.reliability || null
            },
            cargo: {
                cargoType: c.cargoType || '',
                hsCode: c.hsCode || '',
                packingType: c.packingType || '',
                packaging: c.packingType || '',
                numberOfPackages: c.packageCount || null,
                grossWeight: weights.grossKg || null,
                weight: weights.grossKg || null,
                netWeight: weights.netKg || null,
                volumeM3: c.volumeCbm || null,
                volume: c.volumeCbm || null,
                insuranceValue: insurance.valueUsd || null,
                value: insurance.valueUsd || null,
                insuranceCoverage: insurance.coverageType || '',
                stackability: c.stackable ? 'Stackable' : 'Non-stackable',
                stackable: c.stackable !== undefined ? c.stackable : true,
                sensitivity: c.sensitivity || 'standard',
                dangerousGoods: c.dangerousGoods?.isDG || false,
                description: c.description || ''
            },
            seller: {
                companyName: f.seller?.companyName || '',
                company_name: f.seller?.companyName || '',
                country: f.seller?.country?.name || f.seller?.country || '',
                city: f.seller?.city || '',
                address: f.seller?.address || '',
                contactPerson: f.seller?.contactPerson || '',
                contact_person: f.seller?.contactPerson || '',
                contactRole: f.seller?.contactRole || '',
                contact_role: f.seller?.contactRole || '',
                email: f.seller?.email || '',
                phone: f.seller?.phone || '',
                businessType: f.seller?.businessType || '',
                business_type: f.seller?.businessType || '',
                taxId: f.seller?.taxId || '',
                tax_id: f.seller?.taxId || ''
            },
            buyer: {
                companyName: f.buyer?.companyName || '',
                company_name: f.buyer?.companyName || '',
                country: f.buyer?.country?.name || f.buyer?.country || '',
                city: f.buyer?.city || '',
                address: f.buyer?.address || '',
                contactPerson: f.buyer?.contactPerson || '',
                contact_person: f.buyer?.contactPerson || '',
                contactRole: f.buyer?.contactRole || '',
                contact_role: f.buyer?.contactRole || '',
                email: f.buyer?.email || '',
                phone: f.buyer?.phone || '',
                businessType: f.buyer?.businessType || '',
                business_type: f.buyer?.businessType || '',
                taxId: f.buyer?.taxId || '',
                tax_id: f.buyer?.taxId || ''
            },
            modules: {
                esgRisk: f.modules?.esg !== undefined ? f.modules.esg : true,
                esg: f.modules?.esg !== undefined ? f.modules.esg : true,
                weatherClimateRisk: f.modules?.weather !== undefined ? f.modules.weather : true,
                weather: f.modules?.weather !== undefined ? f.modules.weather : true,
                portCongestionRisk: f.modules?.portCongestion !== undefined ? f.modules.portCongestion : true,
                port: f.modules?.portCongestion !== undefined ? f.modules.portCongestion : true,
                carrierPerformance: f.modules?.carrier !== undefined ? f.modules.carrier : true,
                carrier: f.modules?.carrier !== undefined ? f.modules.carrier : true,
                marketConditionScanner: f.modules?.market !== undefined ? f.modules.market : true,
                market: f.modules?.market !== undefined ? f.modules.market : true,
                insuranceOptimization: f.modules?.insurance !== undefined ? f.modules.insurance : true,
                insurance: f.modules?.insurance !== undefined ? f.modules.insurance : true
            },
            riskModules: {
                esg: f.modules?.esg !== undefined ? f.modules.esg : true,
                weather: f.modules?.weather !== undefined ? f.modules.weather : true,
                port: f.modules?.portCongestion !== undefined ? f.modules.portCongestion : true,
                carrier: f.modules?.carrier !== undefined ? f.modules.carrier : true,
                market: f.modules?.market !== undefined ? f.modules.market : true,
                insurance: f.modules?.insurance !== undefined ? f.modules.insurance : true
            }
        };
    }
    
    /**
     * Get state value
     * @param {string} key - State key (supports dot notation)
     * @returns {*} State value
     */
    getStateValue(key) {
        const keys = key.split('.');
        let obj = this.formData;
        
        for (const k of keys) {
            if (obj === null || obj === undefined) return undefined;
            obj = obj[k];
        }
        
        return obj;
    }
    
    /**
     * Sanitize state (ensure all required keys exist with defaults)
     */
    sanitize() {
        // Helper functions (inline to avoid circular dependencies)
        const safeNum = (val, defaultVal = 0) => {
            if (val === null || val === undefined || val === '') return defaultVal;
            const num = Number(val);
            return isNaN(num) ? defaultVal : num;
        };
        
        const safeStr = (val, defaultVal = '') => {
            return (val === null || val === undefined) ? defaultVal : String(val);
        };
        
        // Ensure nested structures exist
        if (!this.formData.cargo) this.formData.cargo = {};
        if (!this.formData.cargo.weights) this.formData.cargo.weights = {};
        if (!this.formData.cargo.insurance) this.formData.cargo.insurance = {};
        if (!this.formData.cargo.temperatureRange) this.formData.cargo.temperatureRange = {};
        if (!this.formData.cargo.dangerousGoods) this.formData.cargo.dangerousGoods = {};
        if (!this.formData.seller) this.formData.seller = {};
        if (!this.formData.seller.country) this.formData.seller.country = { name: '', iso2: '' };
        if (!this.formData.buyer) this.formData.buyer = {};
        if (!this.formData.buyer.country) this.formData.buyer.country = { name: '', iso2: '' };
        if (!this.formData.modules) {
            this.formData.modules = {
                esg: true,
                weather: true,
                portCongestion: true,
                carrier: true,
                market: true,
                insurance: true
            };
        }
        
        // Sanitize seller country
        if (typeof this.formData.seller.country === 'string') {
            this.formData.seller.country = { name: this.formData.seller.country, iso2: '' };
        }
        this.formData.seller.country.name = safeStr(this.formData.seller.country?.name);
        
        // Sanitize buyer country
        if (typeof this.formData.buyer.country === 'string') {
            this.formData.buyer.country = { name: this.formData.buyer.country, iso2: '' };
        }
        this.formData.buyer.country.name = safeStr(this.formData.buyer.country?.name);
        
        console.log('✅ State sanitized');
    }
    
    /**
     * Persist state to localStorage
     */
    persist() {
        try {
            localStorage.setItem('rc-input-state', JSON.stringify(this.formData));
        } catch (err) {
            console.warn('Failed to persist state:', err);
        }
    }
    
    /**
     * Load state from RISKCAST_STATE (global state)
     */
    loadFromRISKCAST_STATE() {
        try {
            const riskcastState = RC_getState();
            if (riskcastState && Object.keys(riskcastState).length > 0) {
                // Map RISKCAST_STATE structure to formData structure
                this.mapRISKCAST_STATEToFormData(riskcastState);
                console.log('✅ Loaded state from RISKCAST_STATE');
            }
        } catch (err) {
            console.warn('Failed to load state from RISKCAST_STATE:', err);
        }
    }
    
    /**
     * Map RISKCAST_STATE structure to formData structure
     * @param {Object} riskcastState - RISKCAST_STATE object
     */
    mapRISKCAST_STATEToFormData(riskcastState) {
        const transport = riskcastState.transport || {};
        const cargo = riskcastState.cargo || {};
        const seller = riskcastState.seller || {};
        const buyer = riskcastState.buyer || {};
        const modules = riskcastState.modules || riskcastState.riskModules || {};
        
        // Map transport
        this.formData.tradeLane = transport.tradeLane || '';
        this.formData.mode = transport.mode || transport.modeOfTransport || '';
        this.formData.shipmentType = transport.shipmentType || '';
        this.formData.priority = transport.priority || 'balanced';
        this.formData.serviceRoute = transport.serviceRoute || '';
        this.formData.carrier = transport.carrier || '';
        this.formData.pol = transport.pol || '';
        this.formData.pod = transport.pod || '';
        this.formData.containerType = transport.containerType || '';
        this.formData.incoterm = transport.incoterm || '';
        this.formData.incotermLocation = transport.incotermLocation || '';
        this.formData.etd = transport.etd || '';
        this.formData.eta = transport.eta || '';
        this.formData.transitDays = transport.transitTime || transport.transitTimeDays || null;
        this.formData.reliability = transport.reliabilityScore || null;
        
        // Map cargo
        this.formData.cargo = this.formData.cargo || {};
        this.formData.cargo.cargoType = cargo.cargoType || '';
        this.formData.cargo.hsCode = cargo.hsCode || '';
        this.formData.cargo.packingType = cargo.packingType || cargo.packaging || '';
        this.formData.cargo.packageCount = cargo.numberOfPackages || null;
        this.formData.cargo.weights = this.formData.cargo.weights || {};
        this.formData.cargo.weights.grossKg = cargo.grossWeight || cargo.weight || null;
        this.formData.cargo.weights.netKg = cargo.netWeight || null;
        this.formData.cargo.volumeCbm = cargo.volumeM3 || cargo.volume || null;
        this.formData.cargo.insurance = this.formData.cargo.insurance || {};
        this.formData.cargo.insurance.valueUsd = cargo.insuranceValue || cargo.value || null;
        this.formData.cargo.insurance.coverageType = cargo.insuranceCoverage || '';
        this.formData.cargo.stackable = cargo.stackability === 'Stackable' ? true : cargo.stackable !== undefined ? cargo.stackable : true;
        this.formData.cargo.sensitivity = cargo.sensitivity || 'standard';
        this.formData.cargo.dangerousGoods = this.formData.cargo.dangerousGoods || {};
        this.formData.cargo.dangerousGoods.isDG = cargo.dangerousGoods || false;
        this.formData.cargo.description = cargo.description || '';
        
        // Map seller
        this.formData.seller = this.formData.seller || {};
        this.formData.seller.companyName = seller.companyName || seller.company_name || '';
        // CRITICAL FIX: Handle case where this.formData.seller.country might already be a string
        // If seller.country is a string, convert it to object
        if (typeof seller.country === 'string') {
            // Ensure we're working with an object, not a string
            this.formData.seller.country = { name: seller.country, iso2: '' };
        } else if (seller.country && typeof seller.country === 'object') {
            // If it's already an object, use it
            this.formData.seller.country = {
                name: seller.country?.name || '',
                iso2: seller.country?.iso2 || ''
            };
        } else {
            // Default to empty object
            this.formData.seller.country = { name: '', iso2: '' };
        }
        this.formData.seller.city = seller.city || '';
        this.formData.seller.address = seller.address || '';
        this.formData.seller.contactPerson = seller.contactPerson || seller.contact_person || '';
        this.formData.seller.contactRole = seller.contactRole || seller.contact_role || '';
        this.formData.seller.email = seller.email || '';
        this.formData.seller.phone = seller.phone || '';
        this.formData.seller.businessType = seller.businessType || seller.business_type || '';
        this.formData.seller.taxId = seller.taxId || seller.tax_id || '';
        
        // Map buyer
        this.formData.buyer = this.formData.buyer || {};
        this.formData.buyer.companyName = buyer.companyName || buyer.company_name || '';
        // CRITICAL FIX: Handle case where this.formData.buyer.country might already be a string
        // If buyer.country is a string, convert it to object
        if (typeof buyer.country === 'string') {
            // Ensure we're working with an object, not a string
            this.formData.buyer.country = { name: buyer.country, iso2: '' };
        } else if (buyer.country && typeof buyer.country === 'object') {
            // If it's already an object, use it
            this.formData.buyer.country = {
                name: buyer.country?.name || '',
                iso2: buyer.country?.iso2 || ''
            };
        } else {
            // Default to empty object
            this.formData.buyer.country = { name: '', iso2: '' };
        }
        this.formData.buyer.city = buyer.city || '';
        this.formData.buyer.address = buyer.address || '';
        this.formData.buyer.contactPerson = buyer.contactPerson || buyer.contact_person || '';
        this.formData.buyer.contactRole = buyer.contactRole || buyer.contact_role || '';
        this.formData.buyer.email = buyer.email || '';
        this.formData.buyer.phone = buyer.phone || '';
        this.formData.buyer.businessType = buyer.businessType || buyer.business_type || '';
        this.formData.buyer.taxId = buyer.taxId || buyer.tax_id || '';
        
        // Map modules
        this.formData.modules = this.formData.modules || {};
        this.formData.modules.esg = modules.esgRisk !== undefined ? modules.esgRisk : (modules.esg !== undefined ? modules.esg : true);
        this.formData.modules.weather = modules.weatherClimateRisk !== undefined ? modules.weatherClimateRisk : (modules.weather !== undefined ? modules.weather : true);
        this.formData.modules.portCongestion = modules.portCongestionRisk !== undefined ? modules.portCongestionRisk : (modules.port !== undefined ? modules.port : true);
        this.formData.modules.carrier = modules.carrierPerformance !== undefined ? modules.carrierPerformance : (modules.carrier !== undefined ? modules.carrier : true);
        this.formData.modules.market = modules.marketConditionScanner !== undefined ? modules.marketConditionScanner : (modules.market !== undefined ? modules.market : true);
        this.formData.modules.insurance = modules.insuranceOptimization !== undefined ? modules.insuranceOptimization : (modules.insurance !== undefined ? modules.insurance : true);
    }
    
    /**
     * Load state from localStorage (fallback)
     */
    loadFromLocalStorage() {
        try {
            const saved = localStorage.getItem('rc-input-state');
            if (saved) {
                const parsed = JSON.parse(saved);
                // Merge with existing formData (from RISKCAST_STATE)
                this.formData = { ...this.formData, ...parsed };
                this.sanitize();
            }
        } catch (err) {
            console.warn('Failed to load state from localStorage:', err);
        }
    }
    
    /**
     * Reset state to defaults
     */
    reset() {
        this.formData = this.getDefaultState();
        this.persist();
    }
}

