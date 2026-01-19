/* ==========================================================================
   SUMMARY_V400 - STATE MANAGEMENT
   Load/save RISKCAST_STATE from localStorage
   ========================================================================== */

const V400State = (() => {
    const STATE_KEY = 'RISKCAST_STATE';
    
    // Default state structure matching FIELD_MAP v400
    const DEFAULT_STATE = {
        shipment: {
            trade_route: {
                pol: '',
                pod: '',
                mode: '',
                service_route: '',
                carrier: '',
                container_type: '',
                etd: '',
                eta: '',
                transit_time_days: null,
                incoterm: '',
                incoterm_location: '',
                priority: ''
            },
            cargo_packing: {
                cargo_type: '',
                cargo_category: '',
                hs_code: '',
                hs_chapter: '',
                packing_type: '',
                packages: null,
                gross_weight_kg: null,
                net_weight_kg: null,
                volume_cbm: null,
                stackability: false,
                temp_control_required: false,
                is_dg: false
            },
            seller: {
                name: '',
                company: '',
                email: '',
                phone: '',
                address: '',
                country: ''
            },
            buyer: {
                name: '',
                company: '',
                email: '',
                phone: '',
                address: '',
                country: ''
            },
            route_tags: {
                tradelane: '',
                region: '',
                inland_needed: false
            }
        },
        riskModules: {
            esg: false,
            weather: false,
            congestion: false,
            carrier_perf: false,
            market: false,
            insurance: false
        }
    };
    
    /**
     * Load state from localStorage and transform from existing format if needed
     */
    function loadState() {
        try {
            const stored = localStorage.getItem(STATE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                // Transform existing state format to v400 format
                return transformToV400Format(parsed);
            }
        } catch (error) {
            console.error('Error loading state:', error);
        }
        return deepClone(DEFAULT_STATE);
    }
    
    /**
     * Transform existing RISKCAST_STATE format to v400 format
     */
    function transformToV400Format(existingState) {
        const v400 = deepClone(DEFAULT_STATE);
        
        // Transform transport -> trade_route
        if (existingState.transport) {
            const t = existingState.transport;
            v400.shipment.trade_route = {
                pol: t.pol || '',
                pod: t.pod || '',
                mode: t.mode || t.modeOfTransport || '',
                service_route: t.serviceRoute || '',
                carrier: t.carrier || '',
                container_type: t.containerType || '',
                etd: t.etd || '',
                eta: t.eta || '',
                transit_time_days: t.transitTimeDays || t.transitTime || null,
                incoterm: t.incoterm || '',
                incoterm_location: t.incotermLocation || '',
                priority: t.priority || ''
            };
        }
        
        // Transform cargo -> cargo_packing
        if (existingState.cargo) {
            const c = existingState.cargo;
            v400.shipment.cargo_packing = {
                cargo_type: c.cargoType || '',
                cargo_category: c.cargoType || '', // Map cargoType to category
                hs_code: c.hsCode || '',
                hs_chapter: extractHSChapter(c.hsCode || ''),
                packing_type: c.packingType || '',
                packages: c.numberOfPackages || null,
                gross_weight_kg: c.grossWeight || null,
                net_weight_kg: c.netWeight || null,
                volume_cbm: c.volumeM3 || null,
                stackability: c.stackability === 'Stackable' || c.stackability === true,
                temp_control_required: false, // Not in existing format
                is_dg: c.dangerousGoods || false
            };
        }
        
        // Transform seller
        if (existingState.seller) {
            const s = existingState.seller;
            v400.shipment.seller = {
                name: s.contactPerson || '',
                company: s.companyName || '',
                email: s.email || '',
                phone: s.phone || '',
                address: s.address || '',
                country: s.country || ''
            };
        }
        
        // Transform buyer
        if (existingState.buyer) {
            const b = existingState.buyer;
            v400.shipment.buyer = {
                name: b.contactPerson || '',
                company: b.companyName || '',
                email: b.email || '',
                phone: b.phone || '',
                address: b.address || '',
                country: b.country || ''
            };
        }
        
        // Transform modules -> riskModules
        if (existingState.modules) {
            const m = existingState.modules;
            v400.riskModules = {
                esg: m.esgRisk || false,
                weather: m.weatherClimateRisk || false,
                congestion: m.portCongestionRisk || false,
                carrier_perf: m.carrierPerformance || false,
                market: m.marketConditionScanner || false,
                insurance: m.insuranceOptimization || false
            };
        }
        
        return v400;
    }
    
    /**
     * Extract HS chapter from HS code
     */
    function extractHSChapter(hsCode) {
        if (!hsCode) return '';
        const match = hsCode.match(/^(\d{2})/);
        return match ? match[1] : '';
    }
    
    /**
     * Save state to localStorage
     */
    function saveState(state) {
        try {
            localStorage.setItem(STATE_KEY, JSON.stringify(state));
            return true;
        } catch (error) {
            console.error('Error saving state:', error);
            return false;
        }
    }
    
    /**
     * Get value at path (e.g., "shipment.trade_route.pol")
     */
    function getValueAtPath(state, path) {
        const keys = path.split('.');
        let value = state;
        for (const key of keys) {
            if (value === null || value === undefined) return null;
            value = value[key];
        }
        return value;
    }
    
    /**
     * Set value at path
     */
    function setValueAtPath(state, path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        let target = state;
        
        for (const key of keys) {
            if (!(key in target)) {
                target[key] = {};
            }
            target = target[key];
        }
        
        target[lastKey] = value;
        return state;
    }
    
    /**
     * Deep clone object
     */
    function deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }
    
    /**
     * Deep merge objects
     */
    function deepMerge(target, source) {
        const result = deepClone(target);
        
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = deepMerge(result[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }
        
        return result;
    }
    
    /**
     * Calculate completeness percentage
     */
    function calculateCompleteness(state) {
        const required = [
            'shipment.trade_route.pol',
            'shipment.trade_route.pod',
            'shipment.trade_route.mode',
            'shipment.trade_route.etd',
            'shipment.trade_route.container_type',
            'shipment.cargo_packing.cargo_type',
            'shipment.cargo_packing.hs_code',
            'shipment.cargo_packing.gross_weight_kg',
            'shipment.cargo_packing.volume_cbm',
            'shipment.seller.company',
            'shipment.seller.email',
            'shipment.buyer.company',
            'shipment.buyer.email'
        ];
        
        let filled = 0;
        for (const path of required) {
            const value = getValueAtPath(state, path);
            if (value !== null && value !== undefined && value !== '') {
                filled++;
            }
        }
        
        return Math.round((filled / required.length) * 100);
    }
    
    /**
     * Get POL country from code (simplified)
     */
    function getCountryFromPortCode(code) {
        if (!code) return '';
        const mapping = {
            'CNSHA': 'CN', 'CNYTN': 'CN', 'CNNGB': 'CN', 'CNTAO': 'CN',
            'USNYC': 'US', 'USLAX': 'US', 'USORF': 'US', 'USSEA': 'US',
            'DEHAM': 'DE', 'NLRTM': 'NL', 'GBSOU': 'GB', 'FRLEH': 'FR',
            'SGSIN': 'SG', 'HKHKG': 'HK', 'JPYOK': 'JP', 'KRPUS': 'KR',
            'AEJEA': 'AE', 'SAJED': 'SA', 'INMUN': 'IN', 'INNSA': 'IN',
            'VNSGN': 'VN', 'VNHPH': 'VN', 'CMIT': 'VN'
        };
        // Try exact match first
        if (mapping[code]) return mapping[code];
        // Try prefix match
        for (const [key, country] of Object.entries(mapping)) {
            if (code.toUpperCase().startsWith(key.substring(0, 2))) {
                return country;
            }
        }
        return '';
    }
    
    /**
     * Format date for display
     */
    function formatDate(dateString) {
        if (!dateString) return '';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        } catch (e) {
            return dateString;
        }
    }
    
    /**
     * Check if value is empty
     */
    function isEmpty(value) {
        return value === null || value === undefined || value === '';
    }
    
    // Public API
    return {
        loadState,
        saveState,
        getValueAtPath,
        setValueAtPath,
        calculateCompleteness,
        getCountryFromPortCode,
        formatDate,
        isEmpty,
        deepClone,
        DEFAULT_STATE
    };
})();




