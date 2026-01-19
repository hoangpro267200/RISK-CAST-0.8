/**
 * ========================================================================
 * RISKCAST v20 - Sanitize Helpers
 * ========================================================================
 * Utility functions for sanitizing state and payload data
 * Ensures no null/undefined values break API calls
 */

/**
 * Get RISKCAST_STATE from localStorage (global state)
 * @returns {Object} RISKCAST_STATE object
 */
export function RC_getState() {
    try {
        const state = localStorage.getItem('RISKCAST_STATE');
        return state ? JSON.parse(state) : {};
    } catch (e) {
        console.warn('Failed to parse RISKCAST_STATE:', e);
        return {};
    }
}

/**
 * Set RISKCAST_STATE to localStorage (global state)
 * @param {Object} newState - New state object
 */
export function RC_setState(newState) {
    try {
        localStorage.setItem('RISKCAST_STATE', JSON.stringify(newState));
        window.RISKCAST_STATE = newState; // Also set global reference
    } catch (e) {
        console.error('Failed to save RISKCAST_STATE:', e);
    }
}

/**
 * Sanitize global RISKCAST_STATE from localStorage
 * Fixes null/undefined values before API submission
 */
export function sanitizeGlobalState() {
    // Load RISKCAST_STATE from localStorage
    let RISKCAST_STATE = JSON.parse(localStorage.getItem('RISKCAST_STATE') || '{}');
    if (!RISKCAST_STATE || typeof RISKCAST_STATE !== 'object') {
        RISKCAST_STATE = {};
    }
    
    const fixNum = (v) => {
        if (v === null || v === undefined || v === '') return 0;
        const num = Number(v);
        return isNaN(num) ? 0 : num;
    };
    
    const fixStr = (v) => {
        return (v === null || v === undefined || v === '') ? '' : String(v);
    };
    
    // --- Transport ---
    RISKCAST_STATE.transport = RISKCAST_STATE.transport || {};
    RISKCAST_STATE.transport.pol = fixStr(RISKCAST_STATE.transport.pol);
    RISKCAST_STATE.transport.pod = fixStr(RISKCAST_STATE.transport.pod);
    RISKCAST_STATE.transport.distance_km = fixNum(RISKCAST_STATE.transport.distance_km);
    RISKCAST_STATE.transport.distance = fixNum(RISKCAST_STATE.transport.distance);
    RISKCAST_STATE.transport.baseRate = fixNum(RISKCAST_STATE.transport.baseRate);
    RISKCAST_STATE.transport.transitTime = fixNum(RISKCAST_STATE.transport.transitTime);
    RISKCAST_STATE.transport.transitTimeDays = fixNum(RISKCAST_STATE.transport.transitTimeDays);
    RISKCAST_STATE.transport.reliabilityScore = fixNum(RISKCAST_STATE.transport.reliabilityScore);
    RISKCAST_STATE.transport.costUSD = fixNum(RISKCAST_STATE.transport.costUSD);
    
    // --- Cargo ---
    RISKCAST_STATE.cargo = RISKCAST_STATE.cargo || {};
    RISKCAST_STATE.cargo.weight = fixNum(RISKCAST_STATE.cargo.weight);
    RISKCAST_STATE.cargo.volume = fixNum(RISKCAST_STATE.cargo.volume);
    RISKCAST_STATE.cargo.value = fixNum(RISKCAST_STATE.cargo.value);
    RISKCAST_STATE.cargo.grossWeight = fixNum(RISKCAST_STATE.cargo.grossWeight);
    RISKCAST_STATE.cargo.netWeight = fixNum(RISKCAST_STATE.cargo.netWeight);
    RISKCAST_STATE.cargo.volumeM3 = fixNum(RISKCAST_STATE.cargo.volumeM3);
    RISKCAST_STATE.cargo.numberOfPackages = fixNum(RISKCAST_STATE.cargo.numberOfPackages);
    RISKCAST_STATE.cargo.insuranceValue = fixNum(RISKCAST_STATE.cargo.insuranceValue);
    
    // --- Seller/Buyer ---
    RISKCAST_STATE.seller = RISKCAST_STATE.seller || {};
    RISKCAST_STATE.buyer = RISKCAST_STATE.buyer || {};
    
    if (typeof RISKCAST_STATE.seller.country === 'string') {
        RISKCAST_STATE.seller.country = fixStr(RISKCAST_STATE.seller.country);
    } else if (RISKCAST_STATE.seller.country && typeof RISKCAST_STATE.seller.country === 'object') {
        RISKCAST_STATE.seller.country.name = fixStr(RISKCAST_STATE.seller.country.name);
    } else {
        RISKCAST_STATE.seller.country = '';
    }
    
    if (typeof RISKCAST_STATE.buyer.country === 'string') {
        RISKCAST_STATE.buyer.country = fixStr(RISKCAST_STATE.buyer.country);
    } else if (RISKCAST_STATE.buyer.country && typeof RISKCAST_STATE.buyer.country === 'object') {
        RISKCAST_STATE.buyer.country.name = fixStr(RISKCAST_STATE.buyer.country.name);
    } else {
        RISKCAST_STATE.buyer.country = '';
    }
    
    // --- Modules ---
    RISKCAST_STATE.riskModules = RISKCAST_STATE.riskModules || {};
    const modules = ['esg', 'weather', 'portCongestion', 'carrierPerformance', 'geopolitical', 'financial'];
    modules.forEach(m => {
        if (RISKCAST_STATE.riskModules[m] == null) {
            RISKCAST_STATE.riskModules[m] = true;
        }
    });
    
    // --- Algorithm Modules (for algorithm toggles) ---
    // Auto-enable all algorithm modules by default (auto bật sẵn)
    RISKCAST_STATE.modules = RISKCAST_STATE.modules || {};
    const algorithmModules = ['fuzzy', 'monte_carlo', 'arima', 'var'];
    algorithmModules.forEach(m => {
        if (RISKCAST_STATE.modules[m] == null) {
            RISKCAST_STATE.modules[m] = true; // Auto bật sẵn
        }
    });
    
    // Also support legacy field names
    if (!RISKCAST_STATE.modules.use_fuzzy && RISKCAST_STATE.modules.fuzzy !== undefined) {
        RISKCAST_STATE.modules.use_fuzzy = RISKCAST_STATE.modules.fuzzy;
    }
    if (!RISKCAST_STATE.modules.use_forecast && RISKCAST_STATE.modules.arima !== undefined) {
        RISKCAST_STATE.modules.use_forecast = RISKCAST_STATE.modules.arima;
    }
    if (!RISKCAST_STATE.modules.use_mc && RISKCAST_STATE.modules.monte_carlo !== undefined) {
        RISKCAST_STATE.modules.use_mc = RISKCAST_STATE.modules.monte_carlo;
    }
    if (!RISKCAST_STATE.modules.use_var && RISKCAST_STATE.modules.var !== undefined) {
        RISKCAST_STATE.modules.use_var = RISKCAST_STATE.modules.var;
    }
    
    // Set defaults for legacy names if not set
    if (RISKCAST_STATE.modules.use_fuzzy == null) RISKCAST_STATE.modules.use_fuzzy = true;
    if (RISKCAST_STATE.modules.use_forecast == null) RISKCAST_STATE.modules.use_forecast = true;
    if (RISKCAST_STATE.modules.use_mc == null) RISKCAST_STATE.modules.use_mc = true;
    if (RISKCAST_STATE.modules.use_var == null) RISKCAST_STATE.modules.use_var = true;
    
    // --- Shipment ---
    if (RISKCAST_STATE.shipment) {
        RISKCAST_STATE.shipment.valueUSD = fixNum(RISKCAST_STATE.shipment.valueUSD);
        RISKCAST_STATE.shipment.onTimeProbability = fixNum(RISKCAST_STATE.shipment.onTimeProbability);
        RISKCAST_STATE.shipment.transitPlannedDays = fixNum(RISKCAST_STATE.shipment.transitPlannedDays);
        RISKCAST_STATE.shipment.transitActualDays = fixNum(RISKCAST_STATE.shipment.transitActualDays);
        RISKCAST_STATE.shipment.carbonFootprintTons = fixNum(RISKCAST_STATE.shipment.carbonFootprintTons);
    }
    
    // --- Risk ---
    if (RISKCAST_STATE.risk) {
        RISKCAST_STATE.risk.overallScore = fixNum(RISKCAST_STATE.risk.overallScore);
        RISKCAST_STATE.risk.delayRisk = fixNum(RISKCAST_STATE.risk.delayRisk);
        RISKCAST_STATE.risk.weatherRisk = fixNum(RISKCAST_STATE.risk.weatherRisk);
        RISKCAST_STATE.risk.congestionRisk = fixNum(RISKCAST_STATE.risk.congestionRisk);
    }
    
    // --- KPI ---
    if (RISKCAST_STATE.kpi) {
        RISKCAST_STATE.kpi.shipmentValue = fixNum(RISKCAST_STATE.kpi.shipmentValue);
        RISKCAST_STATE.kpi.transitDaysPlanned = fixNum(RISKCAST_STATE.kpi.transitDaysPlanned);
        RISKCAST_STATE.kpi.transitDaysProjected = fixNum(RISKCAST_STATE.kpi.transitDaysProjected);
        RISKCAST_STATE.kpi.onTimeProbability = fixNum(RISKCAST_STATE.kpi.onTimeProbability);
        RISKCAST_STATE.kpi.carbonFootprint = fixNum(RISKCAST_STATE.kpi.carbonFootprint);
    }
    
    // PHASE 4: FAILSAFE - Convert all numeric fields from "" to 0 recursively
    const sanitizeNumericFields = (obj) => {
        for (const key in obj) {
            if (obj[key] === '') {
                // If it's a numeric field, convert to 0
                if (key.includes('weight') || key.includes('volume') || key.includes('value') || 
                    key.includes('score') || key.includes('distance') || key.includes('days') ||
                    key.includes('km') || key.includes('rate') || key.includes('cost') ||
                    key.includes('probability') || key.includes('risk') || key.includes('USD') ||
                    key.includes('Tons') || key.includes('footprint')) {
                    obj[key] = 0;
                }
            } else if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
                sanitizeNumericFields(obj[key]);
            }
        }
    };
    sanitizeNumericFields(RISKCAST_STATE);
    
    // Save sanitized state back to localStorage
    localStorage.setItem('RISKCAST_STATE', JSON.stringify(RISKCAST_STATE));
    
    // Expose to window for debugging
    window.RISKCAST_STATE = RISKCAST_STATE;
}

/**
 * Sanitize RISKCAST_STATE object (recursive)
 * @param {Object} state - State object to sanitize
 */
export function sanitizeRiskcastState(state) {
    const sanitizeObj = (obj) => {
        for (const key in obj) {
            if (obj[key] === null || obj[key] === undefined) {
                // Determine type and set default
                if (typeof obj[key] === 'number' || key.includes('weight') || key.includes('volume') || 
                    key.includes('value') || key.includes('score') || key.includes('distance') || 
                    key.includes('days')) {
                    obj[key] = 0;
                } else if (Array.isArray(obj[key])) {
                    obj[key] = [];
                } else if (typeof obj[key] === 'object') {
                    obj[key] = {};
                } else {
                    obj[key] = '';
                }
            } else if (typeof obj[key] === 'object' && !Array.isArray(obj[key]) && obj[key] !== null) {
                sanitizeObj(obj[key]);
            }
        }
    };
    sanitizeObj(state);
}

/**
 * Sanitize API Payload - Remove null values recursively
 * @param {Object} payload - API payload to sanitize
 */
export function sanitizeAPIPayload(payload) {
    for (const key in payload) {
        if (payload[key] === null) {
            delete payload[key];
        } else if (typeof payload[key] === 'object' && !Array.isArray(payload[key]) && payload[key] !== null) {
            sanitizeAPIPayload(payload[key]);
        }
    }
}

/**
 * Safely convert value to number
 * @param {*} val - Value to convert
 * @param {number} defaultVal - Default value if conversion fails
 * @returns {number}
 */
export const safeNum = (val, defaultVal = 0) => {
    if (val === null || val === undefined || val === '') return defaultVal;
    const num = Number(val);
    return isNaN(num) ? defaultVal : num;
};

/**
 * Safely convert value to string
 * @param {*} val - Value to convert
 * @param {string} defaultVal - Default value if conversion fails
 * @returns {string}
 */
export const safeStr = (val, defaultVal = '') => {
    return (val === null || val === undefined) ? defaultVal : String(val);
};

