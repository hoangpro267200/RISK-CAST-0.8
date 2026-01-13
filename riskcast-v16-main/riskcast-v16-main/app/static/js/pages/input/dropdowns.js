
import { $id, qsa, addClass, removeClass, toggleClass, on } from '../../core/dom.js';
import { debounce } from '../../core/utils.js';

export function initDropdowns() {
    const dropdowns = qsa('.custom-dropdown');
    
    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('.dropdown-trigger');
        const menu = dropdown.querySelector('.dropdown-menu');
        const options = dropdown.querySelectorAll('.dropdown-option');
        const hiddenInput = dropdown.querySelector('input[type="hidden"]') || 
                          $id(dropdown.id.replace('_dropdown', '_input'));
        
        if (!trigger || !menu) return;
        
        // Toggle dropdown
        on(trigger, 'click', (e) => {
            e.stopPropagation();
            const isOpen = dropdown.classList.contains('open') || dropdown.classList.contains('active');
            
            if (isOpen) {
                removeClass(dropdown, 'open');
                removeClass(dropdown, 'active');
            } else {
                // Close all other dropdowns first
                dropdowns.forEach(other => {
                    if (other !== dropdown) {
                        removeClass(other, 'open');
                        removeClass(other, 'active');
                    }
                });
                // Open this dropdown
                addClass(dropdown, 'open');
                addClass(dropdown, 'active');
            }
        });
        
        // Select option
        options.forEach(option => {
            on(option, 'click', (e) => {
                e.stopPropagation();
                const value = option.getAttribute('data-value') || option.textContent.trim();
                const displayValue = option.textContent.trim();
                
                // Update display
                const valueSpan = trigger.querySelector('.dropdown-value');
                if (valueSpan) {
                    valueSpan.textContent = displayValue;
                    removeClass(valueSpan, 'placeholder');
                }
                
                // Update hidden input
                if (hiddenInput) {
                    hiddenInput.value = value;
                }
                
                // Update dropdown state
                removeClass(dropdown, 'open');
                removeClass(dropdown, 'active');
                addClass(option, 'selected');
                
                // Remove selected from other options
                options.forEach(opt => {
                    if (opt !== option) {
                        removeClass(opt, 'selected');
                    }
                });
                
                // Trigger change event
                const changeEvent = new CustomEvent('change', { bubbles: true });
                dropdown.dispatchEvent(changeEvent);
                
                if (hiddenInput) {
                    hiddenInput.dispatchEvent(changeEvent);
                }
            });
        });
    });
    
    // Close dropdowns when clicking outside
    on(document, 'click', (e) => {
        if (!e.target.closest('.custom-dropdown')) {
            dropdowns.forEach(dropdown => {
                removeClass(dropdown, 'open');
                removeClass(dropdown, 'active');
            });
        }
    });
    
    // Close dropdowns on ESC key
    on(document, 'keydown', (e) => {
        if (e.key === 'Escape') {
            dropdowns.forEach(dropdown => {
                removeClass(dropdown, 'open');
                removeClass(dropdown, 'active');
            });
        }
    });
}

