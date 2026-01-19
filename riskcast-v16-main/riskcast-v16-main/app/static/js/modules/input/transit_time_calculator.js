
import { $id, on } from '../../core/dom.js';
import { SmartInputState } from './state_management.js';

export function initTransitTimeCalculation() {
    
    const etdInput = $id('etd') || $id('etd_input');
    const etaInput = $id('eta') || $id('eta_input');
    const transitDisplay = $id('transit_time_display');
    const transitHidden = $id('transit_time');
    
    if (!etdInput || !etaInput) {
        return;
    }
    
    // Function to calculate and display transit time from ETD/ETA
    const updateTransitTime = () => {
        if (!etdInput.value || !etaInput.value) {
            if (transitDisplay) {
                transitDisplay.value = '';
                transitDisplay.style.borderColor = '';
                transitDisplay.style.background = '';
            }
            if (transitHidden) transitHidden.value = '';
            return;
        }
        
        const etdDate = new Date(etdInput.value);
        const etaDate = new Date(etaInput.value);
        
        // Validate dates
        if (etaDate <= etdDate) {
            if (transitDisplay) {
                transitDisplay.value = '';
                transitDisplay.style.borderColor = '#ef4444';
                transitDisplay.style.background = 'rgba(239, 68, 68, 0.1)';
            }
            if (transitHidden) transitHidden.value = '';
            showError('eta', 'ETA phải sau ETD');
            return;
        }
        
        // Calculate days
        const diffTime = Math.abs(etaDate - etdDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        // Update displays with animation
        if (transitDisplay) {
            transitDisplay.value = `${diffDays} ngày`;
            transitDisplay.style.background = 'rgba(0, 255, 136, 0.1)';
            transitDisplay.style.borderColor = '#00ffc3';
            transitDisplay.classList.add('glow-animation');
            
            setTimeout(() => {
                transitDisplay.style.background = '';
                transitDisplay.classList.remove('glow-animation');
            }, 1000);
        }
        
        if (transitHidden) {
            transitHidden.value = diffDays;
        }
        
        clearError('eta');
    };
    
    // Attach event listeners
    on(etdInput, 'change', updateTransitTime);
    on(etaInput, 'change', updateTransitTime);
    
    // Initial calculation if both dates exist
    if (etdInput.value && etaInput.value) {
        updateTransitTime();
    }
}

export function calculateTransitTime() {
    const etdInput = $id('etd') || $id('etd_input');
    
    if (!etdInput || !etdInput.value) return;
    
    const routeKey = SmartInputState.selectedRoute;
    const transportMode = SmartInputState.selectedTransportMode;
    
    if (!routeKey || !transportMode) return;
    
    // Get transit days from current selection
    const LOGISTICS_DATA = SmartInputState.getLogisticsData();
    if (!LOGISTICS_DATA) {
        console.error('❌ LOGISTICS_DATA not available');
        return;
    }
    
    const route = LOGISTICS_DATA.getRoute(routeKey);
    if (!route) return;
    
    const mode = route.transport_modes.find(m => m.value === transportMode);
    if (!mode) return;
    
    let days = 0;
    if (mode.days) {
        // Parse days string (e.g., "7-10" → take average)
        const daysParts = mode.days.split('-').map(d => parseInt(d.trim()));
        days = daysParts.length > 1 ? Math.ceil((daysParts[0] + daysParts[1]) / 2) : daysParts[0];
    } else if (mode.hours) {
        const hoursParts = mode.hours.split('-').map(h => parseInt(h.trim()));
        const avgHours = hoursParts.length > 1 ? (hoursParts[0] + hoursParts[1]) / 2 : hoursParts[0];
        days = Math.ceil(avgHours / 24);
    }
    
    if (days > 0) {
        const etd = new Date(etdInput.value);
        const eta = new Date(etd);
        eta.setDate(eta.getDate() + days);
        
        const etaInput = $id('eta') || $id('eta_input');
        if (etaInput) {
            etaInput.value = eta.toISOString().split('T')[0];
            animateAutoFill(etaInput);
        }
    }
}

function showError(fieldId, message) {
    const field = $id(fieldId);
    const errorElement = $id(fieldId + '_error') || 
                        field?.parentElement?.querySelector('.error-message');
    
    if (field) {
        field.classList.add('error-field');
        field.style.borderColor = '#ef4444';
    }
    
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

function clearError(fieldId) {
    const field = $id(fieldId);
    const errorElement = $id(fieldId + '_error') || 
                        field?.parentElement?.querySelector('.error-message');
    
    if (field) {
        field.classList.remove('error-field');
        field.style.borderColor = '';
    }
    
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }
}

function animateAutoFill(element) {
    element.style.transition = 'all 0.5s ease';
    element.style.backgroundColor = 'rgba(0, 255, 136, 0.2)';
    element.style.borderColor = '#00ffc3';
    
    setTimeout(() => {
        element.style.backgroundColor = 'rgba(0, 255, 136, 0.05)';
    }, 1000);
}

