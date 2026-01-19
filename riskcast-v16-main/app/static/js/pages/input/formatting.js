
import { $id, on, qs } from '../../core/dom.js';

function formatCurrency(value) {
    const numValue = value.replace(/\D/g, '');
    if (!numValue) return '';
    return numValue.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

export function initFormatting() {
    const cargoInput = $id('cargo_value');
    if (!cargoInput) {
        setTimeout(initFormatting, 100);
        return;
    }
    
    // Store raw value (without commas) in a hidden field for form submission
    let hiddenInput = $id('cargo_value_raw');
    if (!hiddenInput) {
        hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'cargo_value_raw';
        hiddenInput.id = 'cargo_value_raw';
        if (cargoInput.parentNode) {
            cargoInput.parentNode.appendChild(hiddenInput);
        }
    }
    
    // Allow typing numbers freely - only remove non-digits, no formatting while typing
    on(cargoInput, 'input', (e) => {
        const input = e.target;
        const cursorPos = input.selectionStart;
        const oldValue = input.value;
        
        // Get raw numeric value (remove all non-digits)
        const rawValue = oldValue.replace(/\D/g, '');
        
        // Update hidden field with raw value
        hiddenInput.value = rawValue;
        
        // Only update if value changed (to avoid cursor jumping)
        if (input.value !== rawValue) {
            // Count digits before cursor to restore position
            const digitsBeforeCursor = oldValue.substring(0, cursorPos).replace(/\D/g, '').length;
            
            // Set raw value (no commas while typing)
            input.value = rawValue;
            
            // Restore cursor position after digits
            setTimeout(() => {
                const newPos = Math.min(digitsBeforeCursor, rawValue.length);
                input.setSelectionRange(newPos, newPos);
            }, 0);
        }
    });
    
    // Format on blur if needed
    on(cargoInput, 'blur', (e) => {
        const value = e.target.value.replace(/\D/g, '');
        if (value) {
            e.target.value = formatCurrency(value);
        } else {
            e.target.value = '';
        }
    });
    
    // Update the original input's value before form submit (remove commas)
    const form = cargoInput.closest('form');
    if (form) {
        on(form, 'submit', () => {
            const rawValue = cargoInput.value.replace(/\D/g, '');
            cargoInput.value = rawValue;
        });
    }
}
