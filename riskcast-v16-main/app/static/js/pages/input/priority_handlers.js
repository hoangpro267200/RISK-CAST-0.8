
import { $id, qsa, qs } from '../../core/dom.js';
import { formatNumber } from '../../core/formatters.js';

export function getPriorityWeights() {
    const weights = {
        climate: parseFloat($id('priority_climate')?.value || 0),
        congestion: parseFloat($id('priority_congestion')?.value || 0),
        strike: parseFloat($id('priority_strike')?.value || 0),
        esg: parseFloat($id('priority_esg')?.value || 0)
    };
    
    // Normalize to ensure sum = 100
    const total = weights.climate + weights.congestion + weights.strike + weights.esg;
    if (total > 0) {
        const factor = 100 / total;
        weights.climate = Math.round(weights.climate * factor * 10) / 10;
        weights.congestion = Math.round(weights.congestion * factor * 10) / 10;
        weights.strike = Math.round(weights.strike * factor * 10) / 10;
        weights.esg = Math.round(weights.esg * factor * 10) / 10;
    }
    
    return weights;
}

export function updatePriorityWeightsDisplay() {
    const weights = getPriorityWeights();
    const preview = $id('priority-preview');
    
    if (!preview) return;
    
    // Update display elements
    const climateEl = qs('#priority-preview .weight-climate', preview);
    const congestionEl = qs('#priority-preview .weight-congestion', preview);
    const strikeEl = qs('#priority-preview .weight-strike', preview);
    const esgEl = qs('#priority-preview .weight-esg', preview);
    
    if (climateEl) climateEl.textContent = formatNumber(weights.climate, 1) + '%';
    if (congestionEl) congestionEl.textContent = formatNumber(weights.congestion, 1) + '%';
    if (strikeEl) strikeEl.textContent = formatNumber(weights.strike, 1) + '%';
    if (esgEl) esgEl.textContent = formatNumber(weights.esg, 1) + '%';
}

export function initPriorityHandlers() {
    const inputs = qsa('#priority_climate, #priority_congestion, #priority_strike, #priority_esg');
    
    inputs.forEach(input => {
        input.addEventListener('input', updatePriorityWeightsDisplay);
        input.addEventListener('change', updatePriorityWeightsDisplay);
    });
    
    // Initial update
    updatePriorityWeightsDisplay();
    
    // Export to window for backward compatibility
    if (typeof window !== 'undefined') {
        window.getPriorityWeights = getPriorityWeights;
        window.updatePriorityWeightsDisplay = updatePriorityWeightsDisplay;
    }
}




















