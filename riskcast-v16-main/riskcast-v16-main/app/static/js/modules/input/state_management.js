
export const SmartInputState = {
    selectedRoute: null,
    selectedTransportMode: null,
    selectedPOL: null,
    selectedPOD: null,
    selectedCargoType: null,
    recentShipments: [],
    validationErrors: {},
    completedFields: new Set(),
    initialized: false,
    
    /**
     * Helper: Get LOGISTICS_DATA safely
     * @returns {Object|null} The logistics data object
     */
    getLogisticsData() {
        if (typeof window === 'undefined') return null;
        return window._LOGISTICS_DATA_REF || window.LOGISTICS_DATA || 
               (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null);
    }
};




















