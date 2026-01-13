/**
 * =====================================================
 * SUMMARY_STATE_SYNC.JS – State Synchronization Engine
 * RISKCAST FutureOS v100
 * =====================================================
 * 
 * Manages real-time synchronization between UI and localStorage
 * Handles RISKCAST_STATE loading, updating, and persistence
 */

const StateSync = (function() {
    'use strict';

    let currentState = null;
    let stateListeners = [];

    /**
     * Initialize state from localStorage
     */
    function init() {
        console.log('[StateSync] Initializing state synchronization...');
        loadState();
        return currentState !== null;
    }

    /**
     * Load RISKCAST_STATE from localStorage
     */
    function loadState() {
        try {
            const storedState = localStorage.getItem('RISKCAST_STATE');
            
            if (!storedState) {
                console.warn('[StateSync] No RISKCAST_STATE found in localStorage');
                currentState = createEmptyState();
                return false;
            }

            currentState = JSON.parse(storedState);
            console.log('[StateSync] State loaded successfully:', currentState);
            notifyListeners('load');
            return true;

        } catch (error) {
            console.error('[StateSync] Error loading state:', error);
            currentState = createEmptyState();
            return false;
        }
    }

    /**
     * Save current state to localStorage
     */
    function saveState() {
        try {
            localStorage.setItem('RISKCAST_STATE', JSON.stringify(currentState));
            console.log('[StateSync] State saved successfully');
            notifyListeners('save');
            return true;
        } catch (error) {
            console.error('[StateSync] Error saving state:', error);
            return false;
        }
    }

    /**
     * Get current state
     */
    function getState() {
        return currentState;
    }

    /**
     * Update a specific field in the state
     */
    function updateField(section, field, value) {
        if (!currentState || !currentState[section]) {
            console.error(`[StateSync] Invalid section: ${section}`);
            return false;
        }

        currentState[section][field] = value;
        console.log(`[StateSync] Updated ${section}.${field} =`, value);
        
        // Auto-save after update
        saveState();
        notifyListeners('update', { section, field, value });
        
        return true;
    }

    /**
     * Update multiple fields at once
     */
    function updateFields(updates) {
        try {
            updates.forEach(({ section, field, value }) => {
                if (currentState[section]) {
                    currentState[section][field] = value;
                }
            });
            
            saveState();
            notifyListeners('batch-update', updates);
            return true;
        } catch (error) {
            console.error('[StateSync] Error in batch update:', error);
            return false;
        }
    }

    /**
     * Register a listener for state changes
     */
    function addListener(callback) {
        stateListeners.push(callback);
    }

    /**
     * Remove a listener
     */
    function removeListener(callback) {
        stateListeners = stateListeners.filter(cb => cb !== callback);
    }

    /**
     * Notify all listeners of state change
     */
    function notifyListeners(eventType, data = null) {
        stateListeners.forEach(callback => {
            try {
                callback(eventType, data, currentState);
            } catch (error) {
                console.error('[StateSync] Error in listener callback:', error);
            }
        });
    }

    /**
     * Create empty state structure
     */
    function createEmptyState() {
        return {
            trade_route: {
                trade_lane: '',
                mode_of_transport: '',
                shipment_type: '',
                service_route: '',
                carrier: '',
                priority: 'Balanced',
                incoterm: '',
                incoterm_location: '',
                pol: '',
                pod: '',
                container_type: '',
                etd: '',
                schedule_frequency: '',
                transit_time: '',
                eta: '',
                reliability_score: ''
            },
            cargo_packing: {
                cargo_type: '',
                hs_code: '',
                packing_type: '',
                number_of_packages: '',
                gross_weight: '',
                net_weight: '',
                volume_cbm: '',
                stackability: 'Yes',
                insurance_value_usd: '',
                insurance_coverage_type: '',
                cargo_sensitivity: '',
                dangerous_goods: 'No',
                cargo_description: '',
                special_handling: ''
            },
            seller: {
                company_name: '',
                address: '',
                contact_person: '',
                role: '',
                email: '',
                phone: '',
                vat: ''
            },
            buyer: {
                company_name: '',
                address: '',
                contact_person: '',
                role: '',
                email: '',
                phone: '',
                vat: ''
            },
            risk_modules: {
                esg_risk: false,
                weather_climate: false,
                port_congestion: false,
                carrier_performance: false,
                market_scanner: false,
                insurance_optimization: false
            }
        };
    }

    /**
     * Validate state structure
     */
    function validateState(state) {
        const requiredSections = ['trade_route', 'cargo_packing', 'seller', 'buyer', 'risk_modules'];
        
        for (const section of requiredSections) {
            if (!state[section]) {
                console.error(`[StateSync] Missing section: ${section}`);
                return false;
            }
        }
        
        return true;
    }

    /**
     * Export state as JSON
     */
    function exportState() {
        return JSON.stringify(currentState, null, 2);
    }

    /**
     * Calculate ETA based on ETD and transit time
     */
    function calculateETA(etd, transitDays) {
        if (!etd || !transitDays) return '';
        
        try {
            const etdDate = new Date(etd);
            etdDate.setDate(etdDate.getDate() + parseInt(transitDays));
            return etdDate.toISOString().split('T')[0];
        } catch (error) {
            console.error('[StateSync] Error calculating ETA:', error);
            return '';
        }
    }

    /**
     * Auto-calculate dependent fields
     */
    function autoCalculateFields(section, field, value) {
        // ETD changed → calculate ETA
        if (section === 'trade_route' && field === 'etd') {
            const transitTime = currentState.trade_route.transit_time;
            if (transitTime) {
                const eta = calculateETA(value, transitTime);
                updateField('trade_route', 'eta', eta);
            }
        }
        
        // Transit time changed → recalculate ETA
        if (section === 'trade_route' && field === 'transit_time') {
            const etd = currentState.trade_route.etd;
            if (etd) {
                const eta = calculateETA(etd, value);
                updateField('trade_route', 'eta', eta);
            }
        }
    }

    // Public API
    return {
        init,
        loadState,
        saveState,
        getState,
        updateField,
        updateFields,
        addListener,
        removeListener,
        validateState,
        exportState,
        calculateETA,
        autoCalculateFields
    };

})();

// Make StateSync available globally
window.StateSync = StateSync;

console.log('[StateSync] Module loaded successfully');
