
import { $id, on } from '../../core/dom.js';
import { SmartInputState } from './state_management.js';

export function initContainerRecommendation() {
    
    const cargoDropdown = $id('cargo_type_dropdown') ||
                         document.querySelector('[id*="cargo_type"]');
    
    if (!cargoDropdown) {
        return;
    }
    
    on(cargoDropdown, 'change', () => handleCargoTypeChange());
}

function handleCargoTypeChange() {
    const cargoType = getDropdownValue('cargo_type_dropdown') || 
                     getDropdownValue('cargo_type');
    
    if (!cargoType) return;
    
    SmartInputState.selectedCargoType = cargoType;
    
    // Container recommendation logic can be added here
    // This would integrate with SmartInputSystemClass
    if (typeof window !== 'undefined' && window.smartInputClass) {
        // Update container suggestions based on cargo type
        const containerDropdown = $id('container_dropdown');
        if (containerDropdown && window.smartInputClass.updateUIFeedback) {
            window.smartInputClass.updateUIFeedback({
                cargo: cargoType
            });
        }
    }
}

function getDropdownValue(dropdownId) {
    const dropdown = $id(dropdownId);
    if (!dropdown) return null;
    
    const hiddenInput = $id(dropdownId.replace('_dropdown', '_input'));
    if (hiddenInput && hiddenInput.value) {
        return hiddenInput.value;
    }
    
    const selectedOption = dropdown.querySelector('.dropdown-option.selected');
    if (selectedOption) {
        return selectedOption.getAttribute('data-value');
    }
    
    return dropdown.value || null;
}

