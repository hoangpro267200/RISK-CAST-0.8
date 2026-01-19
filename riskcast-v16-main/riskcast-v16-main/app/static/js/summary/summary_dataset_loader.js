/**
 * =====================================================
 * SUMMARY_DATASET_LOADER.JS – Expert Dataset Loader
 * RISKCAST FutureOS v100
 * =====================================================
 * 
 * Loads and caches expert datasets from JSON files
 * Provides search and filter capabilities
 */

const DatasetLoader = (function() {
    'use strict';

    const datasets = {
        carriers: null,
        containerTypes: null,
        packingTypes: null,
        hsRules: null,
        tradeLanes: null,
        airportsPorts: null,
        serviceRoutes: null
    };

    const BASE_PATH = '/static/data/expert/';

    /**
     * Initialize and load all datasets
     */
    async function init() {
        console.log('[DatasetLoader] Loading expert datasets...');
        
        try {
            await Promise.all([
                loadCarriers(),
                loadContainerTypes(),
                loadPackingTypes(),
                loadHSRules(),
                loadTradeLanes(),
                loadAirportsPorts(),
                loadServiceRoutes()
            ]);
            
            console.log('[DatasetLoader] All datasets loaded successfully');
            return true;
        } catch (error) {
            console.error('[DatasetLoader] Error loading datasets:', error);
            return false;
        }
    }

    /**
     * Load carriers dataset
     */
    async function loadCarriers() {
        try {
            const response = await fetch(BASE_PATH + 'carriers.json');
            datasets.carriers = await response.json();
            console.log('[DatasetLoader] Carriers loaded:', datasets.carriers.length);
        } catch (error) {
            console.error('[DatasetLoader] Error loading carriers:', error);
            datasets.carriers = [];
        }
    }

    /**
     * Load container types dataset
     */
    async function loadContainerTypes() {
        try {
            const response = await fetch(BASE_PATH + 'container_types.json');
            datasets.containerTypes = await response.json();
            console.log('[DatasetLoader] Container types loaded:', datasets.containerTypes.length);
        } catch (error) {
            console.error('[DatasetLoader] Error loading container types:', error);
            datasets.containerTypes = [];
        }
    }

    /**
     * Load packing types dataset
     */
    async function loadPackingTypes() {
        try {
            const response = await fetch(BASE_PATH + 'packing_types.json');
            datasets.packingTypes = await response.json();
            console.log('[DatasetLoader] Packing types loaded:', datasets.packingTypes.length);
        } catch (error) {
            console.error('[DatasetLoader] Error loading packing types:', error);
            datasets.packingTypes = [];
        }
    }

    /**
     * Load HS code rules dataset
     */
    async function loadHSRules() {
        try {
            const response = await fetch(BASE_PATH + 'hs_rules.json');
            datasets.hsRules = await response.json();
            console.log('[DatasetLoader] HS rules loaded:', datasets.hsRules.length);
        } catch (error) {
            console.error('[DatasetLoader] Error loading HS rules:', error);
            datasets.hsRules = [];
        }
    }

    /**
     * Load trade lanes dataset
     */
    async function loadTradeLanes() {
        try {
            const response = await fetch(BASE_PATH + 'trade_lanes.json');
            datasets.tradeLanes = await response.json();
            console.log('[DatasetLoader] Trade lanes loaded:', datasets.tradeLanes.length);
        } catch (error) {
            console.error('[DatasetLoader] Error loading trade lanes:', error);
            datasets.tradeLanes = [];
        }
    }

    /**
     * Load airports and ports dataset
     */
    async function loadAirportsPorts() {
        try {
            const response = await fetch(BASE_PATH + 'airports_ports.json');
            datasets.airportsPorts = await response.json();
            console.log('[DatasetLoader] Airports/Ports loaded:', datasets.airportsPorts.length);
        } catch (error) {
            console.error('[DatasetLoader] Error loading airports/ports:', error);
            datasets.airportsPorts = [];
        }
    }

    /**
     * Load service routes dataset
     */
    async function loadServiceRoutes() {
        try {
            const response = await fetch(BASE_PATH + 'service_routes.json');
            datasets.serviceRoutes = await response.json();
            console.log('[DatasetLoader] Service routes loaded:', datasets.serviceRoutes.length);
        } catch (error) {
            console.error('[DatasetLoader] Error loading service routes:', error);
            datasets.serviceRoutes = [];
        }
    }

    /**
     * Get carriers, optionally filtered by service route
     */
    function getCarriers(serviceRoute = null) {
        if (!serviceRoute) return datasets.carriers || [];
        
        // Filter carriers by service route
        return (datasets.carriers || []).filter(carrier => 
            carrier.routes && carrier.routes.includes(serviceRoute)
        );
    }

    /**
     * Get container types
     */
    function getContainerTypes() {
        return datasets.containerTypes || [];
    }

    /**
     * Get packing types
     */
    function getPackingTypes() {
        return datasets.packingTypes || [];
    }

    /**
     * Search HS codes
     */
    function searchHSCodes(query) {
        if (!query || !datasets.hsRules) return [];
        
        const lowerQuery = query.toLowerCase();
        return datasets.hsRules.filter(rule => 
            rule.code.includes(query) || 
            rule.description.toLowerCase().includes(lowerQuery)
        );
    }

    /**
     * Get HS code details
     */
    function getHSCodeDetails(code) {
        if (!code || !datasets.hsRules) return null;
        
        return datasets.hsRules.find(rule => rule.code === code);
    }

    /**
     * Get trade lanes
     */
    function getTradeLanes() {
        return datasets.tradeLanes || [];
    }

    /**
     * Search trade lanes
     */
    function searchTradeLanes(query) {
        if (!query || !datasets.tradeLanes) return [];
        
        const lowerQuery = query.toLowerCase();
        return datasets.tradeLanes.filter(lane => 
            lane.name.toLowerCase().includes(lowerQuery) ||
            lane.origin.toLowerCase().includes(lowerQuery) ||
            lane.destination.toLowerCase().includes(lowerQuery)
        );
    }

    /**
     * Search airports and ports
     */
    function searchAirportsPorts(query, type = null) {
        if (!query || !datasets.airportsPorts) return [];
        
        const lowerQuery = query.toLowerCase();
        let results = datasets.airportsPorts.filter(location => 
            location.code.toLowerCase().includes(lowerQuery) ||
            location.name.toLowerCase().includes(lowerQuery) ||
            location.city.toLowerCase().includes(lowerQuery) ||
            location.country.toLowerCase().includes(lowerQuery)
        );
        
        // Filter by type if specified (airport or port)
        if (type) {
            results = results.filter(location => location.type === type);
        }
        
        return results;
    }

    /**
     * Get service routes filtered by POL and POD
     */
    function getServiceRoutes(pol = null, pod = null) {
        if (!datasets.serviceRoutes) return [];
        
        let routes = datasets.serviceRoutes;
        
        if (pol) {
            routes = routes.filter(route => route.pol === pol);
        }
        
        if (pod) {
            routes = routes.filter(route => route.pod === pod);
        }
        
        return routes;
    }

    /**
     * Get service route details
     */
    function getServiceRouteDetails(routeId) {
        if (!routeId || !datasets.serviceRoutes) return null;
        
        return datasets.serviceRoutes.find(route => route.id === routeId);
    }

    /**
     * Search all datasets
     */
    function searchAll(query) {
        const results = {
            carriers: [],
            tradeLanes: [],
            airportsPorts: [],
            hsRules: []
        };
        
        if (!query) return results;
        
        const lowerQuery = query.toLowerCase();
        
        // Search carriers
        if (datasets.carriers) {
            results.carriers = datasets.carriers.filter(carrier => 
                carrier.name.toLowerCase().includes(lowerQuery)
            );
        }
        
        // Search trade lanes
        results.tradeLanes = searchTradeLanes(query);
        
        // Search airports/ports
        results.airportsPorts = searchAirportsPorts(query);
        
        // Search HS codes
        results.hsRules = searchHSCodes(query);
        
        return results;
    }

    /**
     * Check if all datasets are loaded
     */
    function isLoaded() {
        return Object.values(datasets).every(dataset => dataset !== null);
    }

    /**
     * Get dataset statistics
     */
    function getStats() {
        return {
            carriers: datasets.carriers?.length || 0,
            containerTypes: datasets.containerTypes?.length || 0,
            packingTypes: datasets.packingTypes?.length || 0,
            hsRules: datasets.hsRules?.length || 0,
            tradeLanes: datasets.tradeLanes?.length || 0,
            airportsPorts: datasets.airportsPorts?.length || 0,
            serviceRoutes: datasets.serviceRoutes?.length || 0,
            loaded: isLoaded()
        };
    }

    // Public API
    return {
        init,
        getCarriers,
        getContainerTypes,
        getPackingTypes,
        searchHSCodes,
        getHSCodeDetails,
        getTradeLanes,
        searchTradeLanes,
        searchAirportsPorts,
        getServiceRoutes,
        getServiceRouteDetails,
        searchAll,
        isLoaded,
        getStats
    };

})();

// Make DatasetLoader available globally
window.DatasetLoader = DatasetLoader;

console.log('[DatasetLoader] Module loaded successfully');
