
import { $id, qsa, addClass, removeClass, on } from '../../core/dom.js';
import { hasValue as checkHasValue } from '../../core/validators.js';

function checkValue(element) {
    if (checkHasValue(element)) {
        addClass(element, 'has-value');
    } else {
        removeClass(element, 'has-value');
    }
}

export function initValidation() {
    const form = $id('risk_form');
    if (!form) return;
    
    // Get all inputs, selects, textareas
    const inputs = Array.from(form.querySelectorAll('input[type="text"], input[type="number"], input[type="email"], input[type="tel"], input[type="date"], input[type="month"], input[type="time"], input[type="url"], input[type="search"], select, textarea'));
    
    // Check initial values
    inputs.forEach((input) => {
        if (input.disabled || input.readonly) return;
        checkValue(input);
        
        // Add event listeners
        on(input, 'input', () => checkValue(input));
        on(input, 'change', () => checkValue(input));
        on(input, 'blur', () => checkValue(input));
    });
    
    // Also handle dropdown selects (custom dropdowns)
    const customSelects = Array.from(form.querySelectorAll('.custom-dropdown'));
    customSelects.forEach((select) => {
        const hiddenInput = select.querySelector('input[type="hidden"]') || 
                          $id(select.id.replace('_dropdown', '_input'));
        if (hiddenInput) {
            const observer = new MutationObserver(() => {
                checkValue(hiddenInput);
            });
            observer.observe(hiddenInput, { attributes: true, attributeFilter: ['value'] });
            
            // Also check on change
            on(select, 'change', () => {
                setTimeout(() => checkValue(hiddenInput), 100);
            });
        }
    });
}

