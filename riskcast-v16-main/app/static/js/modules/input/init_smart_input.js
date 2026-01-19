
import { initRouteBasedSuggestions } from './route_suggestions.js';
import { initTransitTimeCalculation } from './transit_time_calculator.js';
import { initClimateAutoFetch } from './climate_auto_fetch.js';
import { initSliderDisplays } from './slider_displays.js';
import { initRealtimeValidation } from './realtime_validation.js';
import { initCountryAutoSuggest } from './country_auto_suggest.js';
import { initContainerRecommendation } from './container_recommendation.js';
import { SmartInputState } from './state_management.js';

export async function initSmartInputSystem() {
    // Prevent multiple initialization
    if (typeof window !== 'undefined' && window.__SMART_INPUT_INITIALIZED__ && SmartInputState.initialized) {
        return;
    }
    
    if (SmartInputState.initialized) {
        return;
    }
    
    
    // Check if LOGISTICS_DATA is loaded
    if (typeof LOGISTICS_DATA === 'undefined' && (typeof window === 'undefined' || typeof window.LOGISTICS_DATA === 'undefined')) {
        console.error('❌ LOGISTICS_DATA not loaded! Please load logistics_data.js first.');
        setTimeout(() => {
            if (typeof LOGISTICS_DATA !== 'undefined' || (typeof window !== 'undefined' && typeof window.LOGISTICS_DATA !== 'undefined')) {
                initSmartInputSystem();
            } else {
                console.error('❌ LOGISTICS_DATA still not available after retry');
            }
        }, 500);
        return;
    }
    
    // Use window.LOGISTICS_DATA if available, fallback to LOGISTICS_DATA
    const LOGISTICS_DATA_SOURCE = (typeof window !== 'undefined' && window.LOGISTICS_DATA) || 
                                   (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null);
    
    if (!LOGISTICS_DATA_SOURCE) {
        console.error('❌ LOGISTICS_DATA not available!');
        return;
    }
    
    // Store reference globally for use in other methods
    if (typeof window !== 'undefined') {
        window._LOGISTICS_DATA_REF = LOGISTICS_DATA_SOURCE;
    }
    
    // Initialize all features
    try {
        initRouteBasedSuggestions();
        initCountryAutoSuggest();
        initContainerRecommendation();
        initTransitTimeCalculation();
        initClimateAutoFetch();
        initRealtimeValidation();
        initSliderDisplays();
        
        SmartInputState.initialized = true;
        
        if (typeof window !== 'undefined') {
            window.__SMART_INPUT_INITIALIZED__ = true;
        }
        
    } catch (error) {
        console.error('❌ Error initializing Smart Input System:', error);
    }
}

// Auto-initialize on DOM ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                initSmartInputSystem();
            }, 300);
        });
    } else {
        setTimeout(() => {
            initSmartInputSystem();
        }, 300);
    }
}

