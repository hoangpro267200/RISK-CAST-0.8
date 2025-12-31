/**
 * ========================================================================
 * RISKCAST v20 - Auto Suggest Manager
 * ========================================================================
 * Manages auto-suggest functionality for POL/POD and countries
 * 
 * @class AutoSuggestManager
 */
export class AutoSuggestManager {
    /**
     * @param {Array} portDatabase - Port database array
     * @param {Array} countries - Countries array
     * @param {Object} callbacks - Callback functions (selectPOL, selectPOD, onFormDataChange)
     */
    constructor(portDatabase, countries, callbacks = {}) {
        this.portDatabase = portDatabase || [];
        this.countries = countries || [];
        this.callbacks = callbacks;
        this.activeSuggest = null;
        this.availablePOL = [];
        this.availablePOD = [];
    }
    
    /**
     * Initialize auto-suggest for all fields
     */
    initAutoSuggest() {
        const autosuggestFields = document.querySelectorAll('.rc-autosuggest');
        
        autosuggestFields.forEach(field => {
            const input = field.querySelector('.rc-input');
            const menu = field.querySelector('.rc-suggest-menu');
            const fieldName = field.getAttribute('data-field');
            
            if (!input || !menu) return;
            
            input.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                
                if (query.length < 1) {
                    menu.classList.remove('active');
                    return;
                }
                
                const results = this.getSuggestions(query, fieldName);
                
                if (results.length > 0) {
                    this.renderSuggestions(menu, results, query, fieldName, input);
                    menu.classList.add('active');
                    this.activeSuggest = field;
                } else {
                    menu.classList.remove('active');
                }
            });
            
            input.addEventListener('focus', () => {
                const query = input.value.trim();
                
                // For POL/POD: show all available ports on focus (if route is selected)
                if ((fieldName === 'pol' || fieldName === 'pod') && query.length === 0) {
                    if (fieldName === 'pol' && this.availablePOL.length > 0) {
                        menu.classList.add('active');
                        return;
                    } else if (fieldName === 'pod' && this.availablePOD.length > 0) {
                        menu.classList.add('active');
                        return;
                    }
                }
                
                if (query.length >= 1) {
                    const results = this.getSuggestions(query, fieldName);
                    if (results.length > 0) {
                        this.renderSuggestions(menu, results, query, fieldName, input);
                        menu.classList.add('active');
                    }
                }
            });
        });
        
        // Close suggest menu when clicking outside
        document.addEventListener('click', (e) => {
            if (this.activeSuggest && !this.activeSuggest.contains(e.target)) {
                const menu = this.activeSuggest.querySelector('.rc-suggest-menu');
                menu.classList.remove('active');
                this.activeSuggest = null;
            }
        });
        
        console.log('🔥 Auto-suggest initialized ✓');
    }
    
    /**
     * Get suggestions based on query and field name
     * @param {string} query - Search query
     * @param {string} fieldName - Field name
     * @returns {Array} Array of suggestion objects
     */
    getSuggestions(query, fieldName) {
        query = query.toLowerCase();
        
        if (fieldName === 'pol') {
            if (this.availablePOL.length > 0) {
                return this.availablePOL
                    .filter(port => port.toLowerCase().includes(query))
                    .slice(0, 15)
                    .map(port => ({ name: port, code: port }));
            } else {
                return this.portDatabase.filter(port => 
                    port.code.toLowerCase().includes(query) ||
                    port.name.toLowerCase().includes(query) ||
                    port.country.toLowerCase().includes(query)
                ).slice(0, 10);
            }
        }
        
        if (fieldName === 'pod') {
            if (this.availablePOD.length > 0) {
                return this.availablePOD
                    .filter(port => port.toLowerCase().includes(query))
                    .slice(0, 15)
                    .map(port => ({ name: port, code: port }));
            } else {
                return this.portDatabase.filter(port => 
                    port.code.toLowerCase().includes(query) ||
                    port.name.toLowerCase().includes(query) ||
                    port.country.toLowerCase().includes(query)
                ).slice(0, 10);
            }
        }
        
        if (fieldName === 'sellerCountry' || fieldName === 'buyerCountry') {
            return this.countries.filter(country =>
                country.toLowerCase().includes(query)
            ).slice(0, 10);
        }
        
        return [];
    }
    
    /**
     * Render suggestions in menu
     * @param {HTMLElement} menu - Menu element
     * @param {Array} results - Results array
     * @param {string} query - Search query
     * @param {string} fieldName - Field name
     * @param {HTMLElement} input - Input element
     */
    renderSuggestions(menu, results, query, fieldName, input) {
        const isPort = fieldName === 'pol' || fieldName === 'pod';
        
        menu.innerHTML = results.map(result => {
            if (isPort) {
                const code = result.code;
                const name = result.name;
                const country = result.country || '';
                const codeMatch = this.highlightMatch(code, query);
                const nameMatch = this.highlightMatch(name, query);
                
                return `
                    <div class="rc-suggest-item" data-value="${code}" data-name="${name}">
                        <strong>${codeMatch}</strong> — ${nameMatch}${country ? `, ${country}` : ''}
                    </div>
                `;
            } else {
                const match = this.highlightMatch(result, query);
                return `
                    <div class="rc-suggest-item" data-value="${result}">
                        ${match}
                    </div>
                `;
            }
        }).join('');
        
        // Add click handlers
        menu.querySelectorAll('.rc-suggest-item').forEach(item => {
            item.addEventListener('click', () => {
                const value = item.getAttribute('data-value');
                const name = item.getAttribute('data-name') || value;
                
                input.value = name;
                menu.classList.remove('active');
                
                // Handle POL/POD selection via callbacks
                if (fieldName === 'pol' && this.callbacks.selectPOL) {
                    this.callbacks.selectPOL(value, name);
                } else if (fieldName === 'pod' && this.callbacks.selectPOD) {
                    this.callbacks.selectPOD(value, name);
                } else if ((fieldName === 'sellerCountry' || fieldName === 'buyerCountry') && this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
                
                console.log(`✅ Auto-suggest selected: ${fieldName} = ${value}`);
            });
        });
    }
    
    /**
     * Highlight matching text
     * @param {string} text - Text to highlight
     * @param {string} query - Search query
     * @returns {string} HTML with highlighted matches
     */
    highlightMatch(text, query) {
        if (!text) return '';
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
    
    /**
     * Set available POL/POD from route
     * @param {Array} pol - Available POL array
     * @param {Array} pod - Available POD array
     */
    setAvailablePorts(pol, pod) {
        this.availablePOL = pol || [];
        this.availablePOD = pod || [];
    }
}



