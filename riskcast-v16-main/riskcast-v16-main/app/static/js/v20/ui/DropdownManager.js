/**
 * ========================================================================
 * RISKCAST v20 - Dropdown Manager
 * ========================================================================
 * Manages dropdown functionality
 * 
 * @class DropdownManager
 */
export class DropdownManager {
    constructor() {
        this.activeDropdown = null;
        this.dropdowns = [];
    }
    
    /**
     * Initialize all dropdowns
     */
    initDropdowns() {
        this.dropdowns = document.querySelectorAll('.rc-dropdown-v20');
        
        console.log(`🔥 Found ${this.dropdowns.length} dropdowns`);
        
        this.dropdowns.forEach(dropdown => {
            const trigger = dropdown.querySelector('.rc-dropdown-trigger');
            if (!trigger) return;
            
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown(dropdown);
            });
            
            // Search functionality
            const searchInput = dropdown.querySelector('.rc-search-input');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    const query = e.target.value.toLowerCase();
                    const items = dropdown.querySelectorAll('.rc-dropdown-item');
                    
                    items.forEach(item => {
                        const text = item.textContent.toLowerCase();
                        item.style.display = text.includes(query) ? '' : 'none';
                    });
                });
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            if (this.activeDropdown) {
                this.closeDropdown(this.activeDropdown);
            }
        });
        
        console.log('🔥 Dropdowns initialized ✓');
    }
    
    /**
     * Toggle dropdown open/close
     * @param {HTMLElement} dropdown - Dropdown element
     */
    toggleDropdown(dropdown) {
        if (this.activeDropdown && this.activeDropdown !== dropdown) {
            this.closeDropdown(this.activeDropdown);
        }
        
        if (dropdown.classList.contains('active')) {
            this.closeDropdown(dropdown);
        } else {
            dropdown.classList.add('active');
            this.activeDropdown = dropdown;
            
            const searchInput = dropdown.querySelector('.rc-search-input');
            if (searchInput) {
                setTimeout(() => searchInput.focus(), 100);
            }
        }
    }
    
    /**
     * Close dropdown
     * @param {HTMLElement} dropdown - Dropdown element
     */
    closeDropdown(dropdown) {
        dropdown.classList.remove('active');
        if (this.activeDropdown === dropdown) {
            this.activeDropdown = null;
        }
    }
    
    /**
     * Update dropdown selection display
     * @param {string} dropdownId - Dropdown ID
     * @param {string} value - Selected value
     * @param {string} label - Selected label
     */
    updateSelection(dropdownId, value, label) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) {
            console.warn(`⚠️ Dropdown with ID '${dropdownId}' not found`);
            return;
        }
        
        const trigger = dropdown.querySelector('.rc-dropdown-trigger');
        if (!trigger) {
            console.warn(`⚠️ Dropdown trigger not found for '${dropdownId}'`);
            return;
        }
        
        // Try multiple possible selectors for the display element
        const displaySelectors = [
            '.rc-dropdown-display',
            '.rc-dropdown-value',
            '.rc-dropdown-selected',
            'span'
        ];
        
        let display = null;
        for (const selector of displaySelectors) {
            display = trigger.querySelector(selector);
            if (display) break;
        }
        
        // If no display element found, use trigger's first text node or create one
        if (!display) {
            // Try to find any text node or create a span
            const existingText = trigger.textContent.trim();
            if (existingText && !trigger.querySelector('i')) {
                // If trigger has text but no display element, replace it
                trigger.innerHTML = `<span class="rc-dropdown-value">${label || value}</span><i data-lucide="chevron-down" class="rc-dropdown-arrow"></i>`;
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            } else {
                // Create display element
                display = document.createElement('span');
                display.className = 'rc-dropdown-value';
                trigger.insertBefore(display, trigger.firstChild);
            }
        }
        
        if (display) {
            display.textContent = label || value || 'Select...';
        }
        
        // Set data attributes
        dropdown.setAttribute('data-value', value || '');
        dropdown.setAttribute('data-selected-value', value || '');
        
        // Close dropdown if open
        this.closeDropdown(dropdown);
        
        console.log(`✅ Updated dropdown '${dropdownId}': ${label || value}`);
    }
}

