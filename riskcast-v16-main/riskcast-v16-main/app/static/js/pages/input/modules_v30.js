/**
 * ==========================================================================
 * MODULES_V30 - Risk Analysis Modules Selection Controller
 * VisionOS Edition - Auto-select all modules, toggle functionality
 * ==========================================================================
 */

(function() {
    'use strict';

    /**
     * Module Configuration
     */
    const MODULES_CONFIG = {
        esg: {
            key: 'esg',
            label: 'ESG Risk',
            description: 'Environmental, social & governance compliance analysis',
            icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor" opacity="0.6"/><path d="M12 4L9.91 8.26L5 8.77L8.5 12L7.41 16.5L12 14.27L16.59 16.5L15.5 12L19 8.77L14.09 8.26L12 4Z" fill="currentColor"/></svg>'
        },
        weather: {
            key: 'weather',
            label: 'Weather & Climate Risk',
            description: 'Real-time weather disruption and climate impact analysis',
            icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="currentColor" opacity="0.5"/><path d="M12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8ZM12 10C10.9 10 10 10.9 10 12C10 13.1 10.9 14 12 14C13.1 14 14 13.1 14 12C14 10.9 13.1 10 12 10ZM9 12C8.45 12 8 12.45 8 13C8 13.55 8.45 14 9 14C9.55 14 10 13.55 10 13C10 12.45 9.55 12 9 12ZM15 12C14.45 12 14 12.45 14 13C14 13.55 14.45 14 15 14C15.55 14 16 13.55 16 13C16 12.45 15.55 12 15 12Z" fill="currentColor"/></svg>'
        },
        portCongestion: {
            key: 'portCongestion',
            label: 'Port Congestion Risk',
            description: 'Port delays, congestion monitoring, and capacity analysis',
            icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="currentColor" opacity="0.5"/><path d="M12 6L13.09 8.26L15.5 8.77L13.91 10.73L14.18 13.27L12 12.27L9.82 13.27L10.09 10.73L8.5 8.77L10.91 8.26L12 6ZM17 11L17.5 12.5L19 13L17.5 13.5L17 15L16.5 13.5L15 13L16.5 12.5L17 11ZM7 11L7.5 12.5L9 13L7.5 13.5L7 15L6.5 13.5L5 13L6.5 12.5L7 11Z" fill="currentColor"/></svg>'
        },
        carrierPerformance: {
            key: 'carrierPerformance',
            label: 'Carrier Performance',
            description: 'Carrier reliability, history, and performance optimization',
            icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 18H20V20H4V18Z" fill="currentColor" opacity="0.6"/><path d="M2 6L12 2L22 6V18H2V6ZM4 8V16H20V8L12 5L4 8ZM8 10H16V14H8V10Z" fill="currentColor"/></svg>'
        },
        geopolitical: {
            key: 'geopolitical',
            label: 'Geopolitical Risk',
            description: 'Political stability, trade tensions, and regional risk factors',
            icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="currentColor" opacity="0.5"/><path d="M12 4C16.42 4 20 7.58 20 12C20 16.42 16.42 20 12 20C7.58 20 4 16.42 4 12C4 7.58 7.58 4 12 4ZM12 6C8.69 6 6 8.69 6 12C6 15.31 8.69 18 12 18C15.31 18 18 15.31 18 12C18 8.69 15.31 6 12 6ZM12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8Z" fill="currentColor"/></svg>'
        },
        financial: {
            key: 'financial',
            label: 'Financial & Market Risk',
            description: 'Freight rates, market volatility, and financial risk analysis',
            icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 21H21V23H3V21Z" fill="currentColor" opacity="0.6"/><path d="M3 3V5H5V3H3ZM7 3V5H9V3H7ZM11 3V5H13V3H11ZM15 3V5H17V3H15ZM19 3V5H21V3H19ZM3 7V9H5V7H3ZM3 11V13H5V11H3ZM3 15V17H5V15H3ZM3 19V21H5V19H3ZM21 7V9H19V7H21ZM21 11V13H19V11H21ZM21 15V17H19V15H21Z" fill="currentColor"/></svg>'
        }
    };

    /**
     * State Management
     */
    let currentState = {
        riskModules: {}
    };

    /**
     * Initialize Modules Page
     */
    function initModules() {
        console.log('[Modules v30] Initializing...');
        
        // Load RISKCAST_STATE from localStorage
        loadState();
        
        // Auto-select all 6 modules if riskModules is missing or empty
        if (!currentState.riskModules || Object.keys(currentState.riskModules).length === 0) {
            console.log('[Modules v30] Auto-selecting all 6 modules');
            currentState.riskModules = {
                esg: true,
                weather: true,
                portCongestion: true,
                carrierPerformance: true,
                geopolitical: true,
                financial: true
            };
            saveState();
        }
        
        // Render modules
        renderModules();
        
        // Attach event listeners
        attachEventListeners();
        
        console.log('[Modules v30] Initialization complete', currentState);
    }

    /**
     * Load State from localStorage
     */
    function loadState() {
        try {
            const stored = localStorage.getItem('RISKCAST_STATE');
            if (stored) {
                const parsed = JSON.parse(stored);
                currentState = parsed;
                
                // Ensure riskModules exists
                if (!currentState.riskModules) {
                    currentState.riskModules = {};
                }
                
                // Map old/deprecated keys to new standard keys
                if (currentState.riskModules.port && !currentState.riskModules.portCongestion) {
                    currentState.riskModules.portCongestion = currentState.riskModules.port;
                }
                if (currentState.riskModules.carrier && !currentState.riskModules.carrierPerformance) {
                    currentState.riskModules.carrierPerformance = currentState.riskModules.carrier;
                }
                if (currentState.riskModules.market && !currentState.riskModules.financial) {
                    currentState.riskModules.financial = currentState.riskModules.market;
                }
                // Clean up old keys
                delete currentState.riskModules.port;
                delete currentState.riskModules.carrier;
                delete currentState.riskModules.market;
            }
        } catch (err) {
            console.error('[Modules v30] Failed to load state:', err);
            currentState = { riskModules: {} };
        }
    }

    /**
     * Save State to localStorage
     */
    function saveState() {
        try {
            localStorage.setItem('RISKCAST_STATE', JSON.stringify(currentState));
            console.log('[Modules v30] State saved', currentState);
        } catch (err) {
            console.error('[Modules v30] Failed to save state:', err);
        }
    }

    /**
     * Render Modules Grid
     */
    function renderModules() {
        const grid = document.getElementById('modulesGrid');
        if (!grid) return;
        
        const modulesHTML = Object.values(MODULES_CONFIG).map(module => {
            const isActive = currentState.riskModules[module.key] === true;
            const activeClass = isActive ? 'module-card-v30--active' : '';
            
            return `
                <div class="module-card-v30 ${activeClass}" 
                     data-module-key="${module.key}"
                     onclick="ModulesV30.toggleModule('${module.key}')">
                    <div class="module-card-v30__status"></div>
                    <div class="module-card-v30__icon">
                        ${module.icon}
                    </div>
                    <h3 class="module-card-v30__title">${module.label}</h3>
                    <p class="module-card-v30__desc">${module.description}</p>
                </div>
            `;
        }).join('');
        
        grid.innerHTML = modulesHTML;
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * Toggle Module
     */
    function toggleModule(key) {
        if (!MODULES_CONFIG[key]) {
            console.warn('[Modules v30] Unknown module key:', key);
            return;
        }
        
        // Toggle state
        const currentValue = currentState.riskModules[key] || false;
        currentState.riskModules[key] = !currentValue;
        
        // Update UI
        const card = document.querySelector(`[data-module-key="${key}"]`);
        if (card) {
            if (currentState.riskModules[key]) {
                card.classList.add('module-card-v30--active');
            } else {
                card.classList.remove('module-card-v30--active');
            }
        }
        
        // Save state
        saveState();
        
        console.log('[Modules v30] Module toggled:', key, currentState.riskModules[key]);
    }

    /**
     * Save Modules and Continue
     */
    function saveModulesAndContinue() {
        console.log('[Modules v30] Saving modules and continuing...');
        
        // Update RISKCAST_STATE with modules
        loadState(); // Reload to get latest state
        
        // Use standard keys directly (no mapping needed)
        // Ensure all modules are in state
        Object.keys(MODULES_CONFIG).forEach(key => {
            if (currentState.riskModules[key] === undefined) {
                currentState.riskModules[key] = false;
            }
        });
        
        // Remove old/deprecated keys
        const validKeys = Object.keys(MODULES_CONFIG);
        Object.keys(currentState.riskModules).forEach(key => {
            if (!validKeys.includes(key) && key !== 'port' && key !== 'carrier' && key !== 'market') {
                delete currentState.riskModules[key];
            }
        });
        
        // Update summary.modules with list of active modules
        if (!currentState.summary) {
            currentState.summary = {};
        }
        
        const activeModules = Object.keys(MODULES_CONFIG)
            .filter(key => currentState.riskModules[key] === true)
            .map(key => MODULES_CONFIG[key]?.label || key);
        
        currentState.summary.modules = activeModules;
        
        // Save state
        saveState();
        
        console.log('[Modules v30] Active modules:', activeModules);
        console.log('[Modules v30] Redirecting to /overview');
        
        // Redirect to overview
        window.location.href = '/overview';
    }

    /**
     * Attach Event Listeners
     */
    function attachEventListeners() {
        // Continue button
        const btnContinue = document.getElementById('btnContinue');
        if (btnContinue) {
            btnContinue.addEventListener('click', saveModulesAndContinue);
        }
        
        // Review button (same as continue for now)
        const btnReview = document.getElementById('btnReview');
        if (btnReview) {
            btnReview.addEventListener('click', saveModulesAndContinue);
        }
    }

    /**
     * Public API
     */
    window.ModulesV30 = {
        init: initModules,
        toggleModule: toggleModule,
        saveModulesAndContinue: saveModulesAndContinue
    };

    /**
     * Auto-initialize on DOM ready
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initModules);
    } else {
        initModules();
    }

})();

