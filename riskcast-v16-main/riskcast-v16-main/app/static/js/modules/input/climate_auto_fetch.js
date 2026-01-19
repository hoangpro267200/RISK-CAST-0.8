
import { $id, on } from '../../core/dom.js';
import { SmartInputState } from './state_management.js';

export function initClimateAutoFetch() {
    
    const etdInput = $id('etd') || $id('etd_input');
    const etaInput = $id('eta') || $id('eta_input');
    const routeDropdown = $id('route_dropdown');
    
    const tryFetchClimate = () => {
        const route = SmartInputState.selectedRoute;
        const etd = etdInput?.value;
        const eta = etaInput?.value;
        
        if (route && etd && eta) {
            fetchClimateData(route, etd, eta);
        }
    };
    
    if (etdInput) on(etdInput, 'change', tryFetchClimate);
    if (etaInput) on(etaInput, 'change', tryFetchClimate);
    if (routeDropdown) on(routeDropdown, 'change', tryFetchClimate);
}

export async function fetchClimateData(route, etd, eta) {
    const transitMonth = new Date(etd).getMonth() + 1;
    const startDate = new Date(etd);
    const endDate = new Date(eta);
    
    try {
        const response = await fetch('/api/climate_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                route: route,
                start_date: startDate.toISOString().split('T')[0],
                end_date: endDate.toISOString().split('T')[0],
                pol: SmartInputState.selectedPOL || '',
                pod: SmartInputState.selectedPOD || ''
            })
        });
        
        if (!response.ok) throw new Error('Climate API failed');
        
        const climateData = await response.json();
        populateClimateFields(climateData);
        
    } catch (error) {
        populateClimateDefaults(route, transitMonth);
    }
}

function populateClimateFields(data) {
    const fields = {
        'enso_index': data.enso || 0.0,
        'typhoon_frequency': data.typhoon_freq || 0.5,
        'sst_anomaly': data.sst_anomaly || 0.0,
        'port_climate_stress': data.port_stress || 5.0,
        'climate_volatility_index': data.volatility || 50
    };
    
    Object.keys(fields).forEach(fieldId => {
        const input = $id(fieldId);
        if (input) {
            input.value = fields[fieldId];
            
            // Trigger slider display update
            if (input.type === 'range') {
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            // Animation
            input.style.background = 'rgba(0, 255, 136, 0.1)';
            setTimeout(() => {
                input.style.background = '';
            }, 1000);
        }
    });
    
    // Show notification
    showNotification('✓ Climate data loaded from NOAA/NASA', 'success');
}

function populateClimateDefaults(route, month) {
    // Fallback: Use seasonal patterns
    const isTyphoonSeason = [6, 7, 8, 9, 10].includes(month);
    
    const defaults = {
        'enso_index': 0.0,
        'typhoon_frequency': isTyphoonSeason ? 0.7 : 0.3,
        'sst_anomaly': 0.0,
        'port_climate_stress': 5.0,
        'climate_volatility_index': isTyphoonSeason ? 65 : 45
    };
    
    Object.keys(defaults).forEach(fieldId => {
        const input = $id(fieldId);
        if (input && !input.value) {
            input.value = defaults[fieldId];
            if (input.type === 'range') {
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });
}

function showNotification(message, type) {
}

