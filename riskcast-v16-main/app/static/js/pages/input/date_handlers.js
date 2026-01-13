
import { $id, addClass, removeClass, on } from '../../core/dom.js';

function updateMonthDisplay() {
    const monthInput = $id('shipment-month');
    const monthDisplay = $id('shipment-month-display');
    
    if (!monthInput || !monthDisplay) {
        setTimeout(updateMonthDisplay, 100);
        return;
    }
    
    const value = monthInput.value; // Format: "2025-11"
    if (!value) {
        monthDisplay.value = 'Chọn tháng';
        removeClass(monthDisplay, 'has-value');
        return;
    }
    
    // Parse month from "2025-11" format
    const parts = value.split('-');
    if (parts.length < 2) {
        monthDisplay.value = 'Chọn tháng';
        removeClass(monthDisplay, 'has-value');
        return;
    }
    
    const year = parts[0];
    const month = parts[1];
    const monthNum = parseInt(month, 10);
    
    // Display format: "26/11/2025" (day 26 of the selected month)
    if (!isNaN(monthNum) && monthNum >= 1 && monthNum <= 12) {
        const day = '26';
        const formattedDate = `${day}/${month}/${year}`;
        monthDisplay.value = formattedDate;
        addClass(monthDisplay, 'has-value');
    } else {
        monthDisplay.value = 'Chọn tháng';
        removeClass(monthDisplay, 'has-value');
    }
}

export function initDateHandlers() {
    const monthInput = $id('shipment-month');
    const monthDisplay = $id('shipment-month-display');
    
    if (!monthInput || !monthDisplay) {
        setTimeout(initDateHandlers, 100);
        return;
    }
    
    // Initial update
    updateMonthDisplay();
    
    // Show Priority Weights Preview if month is already selected
    const priorityPreview = $id('priority-preview');
    if (priorityPreview && monthInput.value) {
        priorityPreview.style.display = 'block';
        // Update priority display if already selected (if available globally)
        if (typeof window.updatePriorityWeightsDisplay === 'function') {
            setTimeout(() => window.updatePriorityWeightsDisplay(), 200);
        }
    }
    
    // Sync display input with month input
    on(monthInput, 'change', () => {
        updateMonthDisplay();
        const priorityPreview = $id('priority-preview');
        if (priorityPreview && monthInput.value) {
            priorityPreview.style.display = 'block';
            if (typeof window.updatePriorityWeightsDisplay === 'function') {
                window.updatePriorityWeightsDisplay();
            }
        } else if (priorityPreview && !monthInput.value) {
            priorityPreview.style.display = 'none';
        }
        // Also trigger any climate data updates
        if (typeof window.updateClimateData === 'function') {
            window.updateClimateData();
        }
    });
    
    on(monthInput, 'input', () => {
        updateMonthDisplay();
        const priorityPreview = $id('priority-preview');
        if (priorityPreview && monthInput.value) {
            priorityPreview.style.display = 'block';
        } else if (priorityPreview && !monthInput.value) {
            priorityPreview.style.display = 'none';
        }
    });
    
    // Make the display input trigger the hidden month input
    on(monthDisplay, 'click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            if (monthInput.showPicker && e.isTrusted) {
                monthInput.showPicker();
            } else {
                monthInput.focus();
                monthInput.click();
            }
        } catch (err) {
            monthInput.focus();
            monthInput.click();
        }
    });
}
