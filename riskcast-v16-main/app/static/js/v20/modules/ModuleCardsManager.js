/**
 * ========================================================================
 * RISKCAST v20 - Module Cards Manager
 * ========================================================================
 * Manages 6 risk modules toggle cards
 * 
 * @class ModuleCardsManager
 */
export class ModuleCardsManager {
    /**
     * @param {Object} stateManager - State manager instance
     * @param {Object} callbacks - Callback functions
     */
    constructor(stateManager, callbacks = {}) {
        this.state = stateManager;
        this.callbacks = callbacks;
        
        // Mapping từ data-field sang module key
        this.fieldToKeyMap = {
            'moduleESG': 'esg',
            'moduleWeather': 'weather',
            'modulePortCongestion': 'portCongestion',
            'moduleCarrier': 'carrier',
            'moduleMarket': 'market',
            'moduleInsurance': 'insurance'
        };
    }
    
    /**
     * Initialize module cards
     */
    init() {
        this.initModuleCards();
        this.autoSelectAllModules();
        console.log('🔥 Module cards initialized ✓ (All 6 modules auto-selected)');
    }
    
    /**
     * Initialize module cards
     */
    initModuleCards() {
        const moduleCards = document.querySelectorAll('.rc-module-card');
        
        // Auto-select all 6 modules when load (auto bật sẵn)
        moduleCards.forEach(card => {
            const checkbox = card.querySelector('.rc-module-checkbox');
            if (!checkbox) return;
            
            const fieldName = checkbox.getAttribute('data-field');
            const moduleKey = this.fieldToKeyMap[fieldName];
            
            if (moduleKey) {
                // Check RISKCAST_STATE for saved value, default to true if not set (auto bật sẵn)
                let shouldBeChecked = true; // Default: auto bật sẵn
                
                try {
                    // Try to get from RISKCAST_STATE
                    if (typeof window.RISKCAST_STATE !== 'undefined' && window.RISKCAST_STATE.riskModules) {
                        const savedValue = window.RISKCAST_STATE.riskModules[moduleKey];
                        if (savedValue !== undefined) {
                            shouldBeChecked = savedValue === true;
                        } else {
                            // Not set, default to true (auto bật sẵn)
                            shouldBeChecked = true;
                            if (!window.RISKCAST_STATE.riskModules) {
                                window.RISKCAST_STATE.riskModules = {};
                            }
                            window.RISKCAST_STATE.riskModules[moduleKey] = true;
                            // Save to localStorage
                            try {
                                localStorage.setItem('RISKCAST_STATE', JSON.stringify(window.RISKCAST_STATE));
                            } catch (e) {
                                console.warn('[ModuleCardsManager] Failed to save state:', e);
                            }
                        }
                    } else {
                        // No state, default to true (auto bật sẵn)
                        shouldBeChecked = true;
                        // Initialize state
                        if (typeof window.RISKCAST_STATE === 'undefined') {
                            window.RISKCAST_STATE = { riskModules: {} };
                        }
                        if (!window.RISKCAST_STATE.riskModules) {
                            window.RISKCAST_STATE.riskModules = {};
                        }
                        window.RISKCAST_STATE.riskModules[moduleKey] = true;
                        try {
                            localStorage.setItem('RISKCAST_STATE', JSON.stringify(window.RISKCAST_STATE));
                        } catch (e) {
                            console.warn('[ModuleCardsManager] Failed to save state:', e);
                        }
                    }
                } catch (e) {
                    console.warn('[ModuleCardsManager] Error reading state:', e);
                    shouldBeChecked = true; // Default to checked (auto bật sẵn)
                }
                
                // Ensure default value is true if not set in state manager
                const currentValue = this.state.getStateValue(`modules.${moduleKey}`);
                if (currentValue === undefined) {
                    this.state.setState(`modules.${moduleKey}`, shouldBeChecked);
                } else {
                    // Sync with RISKCAST_STATE
                    this.state.setState(`modules.${moduleKey}`, shouldBeChecked);
                }
                
                // Set checkbox state
                checkbox.checked = shouldBeChecked;
                
                // Update UI
                if (shouldBeChecked) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            }
        });
        
        // Bind click handlers
        moduleCards.forEach(card => {
            const checkbox = card.querySelector('.rc-module-checkbox');
            if (!checkbox) return;
            
            const fieldName = checkbox.getAttribute('data-field');
            const moduleKey = this.fieldToKeyMap[fieldName];
            
            if (!moduleKey) return;
            
            // Handler for checkbox change
            checkbox.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                this.state.setState(`modules.${moduleKey}`, isChecked);
                
                // Update RISKCAST_STATE
                try {
                    if (typeof window.RISKCAST_STATE === 'undefined') {
                        window.RISKCAST_STATE = { riskModules: {} };
                    }
                    if (!window.RISKCAST_STATE.riskModules) {
                        window.RISKCAST_STATE.riskModules = {};
                    }
                    window.RISKCAST_STATE.riskModules[moduleKey] = isChecked;
                    localStorage.setItem('RISKCAST_STATE', JSON.stringify(window.RISKCAST_STATE));
                } catch (e) {
                    console.warn('[ModuleCardsManager] Failed to save state:', e);
                }
                
                // Update UI
                if (isChecked) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
                
                console.log(`Module toggled: ${moduleKey} = ${isChecked}`);
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
            
            // Handler for card click (toggle checkbox) - but not if clicking on toggle itself
            card.addEventListener('click', (e) => {
                // Don't toggle if clicking on toggle input/label
                if (e.target === checkbox || 
                    e.target.closest('.toggle-cont') || 
                    e.target.closest('.toggle-label') ||
                    e.target.closest('input')) {
                    return;
                }
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            });
        });
    }
    
    /**
     * Auto-select all modules
     */
    autoSelectAllModules() {
        Object.values(this.fieldToKeyMap).forEach(moduleKey => {
            const currentValue = this.state.getStateValue(`modules.${moduleKey}`);
            if (currentValue === undefined) {
                this.state.setState(`modules.${moduleKey}`, true);
            }
        });
        
        if (this.callbacks.onFormDataChange) {
            this.callbacks.onFormDataChange();
        }
    }
}



