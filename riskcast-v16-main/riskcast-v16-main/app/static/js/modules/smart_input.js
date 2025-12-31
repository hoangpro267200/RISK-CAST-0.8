
/**
 * ========================================
 * RATING INTERPRETER - Dynamic Badge Logic
 * ========================================
 */
const RatingInterpreter = {
    /**
     * Get rating interpretation for reliability score (0-100)
     */
    getReliabilityRating: function(value) {
        const num = parseInt(value);
        if (num >= 86) {
            return {
                label: 'Excellent',
                icon: '✓✓',
                class: 'excellent',
                color: '#10b981',
                bg: 'linear-gradient(135deg, #10b981, #059669)'
            };
        } else if (num >= 61) {
            return {
                label: 'Good',
                icon: '✓',
                class: 'good',
                color: '#3b82f6',
                bg: 'linear-gradient(135deg, #3b82f6, #2563eb)'
            };
        } else if (num >= 31) {
            return {
                label: 'Fair',
                icon: '⚠️',
                class: 'fair',
                color: '#fbbf24',
                bg: 'linear-gradient(135deg, #fbbf24, #f59e0b)'
            };
        } else {
            return {
                label: 'Unreliable',
                icon: '❌',
                class: 'poor',
                color: '#ef4444',
                bg: 'linear-gradient(135deg, #ef4444, #dc2626)'
            };
        }
    },
    
    /**
     * Get rating interpretation for carrier rating (1-5 stars)
     */
    getCarrierRating: function(value) {
        const num = parseFloat(value);
        if (num >= 4.6) {
            return {
                label: 'Outstanding',
                icon: '⭐⭐⭐⭐⭐',
                class: 'excellent',
                color: '#10b981'
            };
        } else if (num >= 3.6) {
            return {
                label: 'Good',
                icon: '⭐⭐⭐',
                class: 'good',
                color: '#3b82f6'
            };
        } else if (num >= 2.1) {
            return {
                label: 'Average',
                icon: '⭐⭐',
                class: 'fair',
                color: '#fbbf24'
            };
        } else {
            return {
                label: 'Poor',
                icon: '⭐',
                class: 'poor',
                color: '#ef4444'
            };
        }
    },
    
    /**
     * Get rating interpretation for weather/port risk (1-10)
     */
    getRiskRating: function(value) {
        const num = parseFloat(value);
        if (num >= 8.1) {
            return {
                label: 'Extreme Risk',
                icon: '🌪️',
                class: 'extreme',
                color: '#dc2626',
                suggestion: 'Delay Recommended'
            };
        } else if (num >= 6.1) {
            return {
                label: 'High Risk',
                icon: '⛈️',
                class: 'high',
                color: '#ef4444',
                suggestion: 'Monitor Closely'
            };
        } else if (num >= 3.1) {
            return {
                label: 'Moderate Risk',
                icon: '🌤️',
                class: 'moderate',
                color: '#fbbf24',
                suggestion: 'Normal Conditions'
            };
        } else {
            return {
                label: 'Low Risk',
                icon: '☀️',
                class: 'low',
                color: '#10b981',
                suggestion: 'Favorable'
            };
        }
    },
    
    /**
     * Get rating interpretation for container match (1-10)
     */
    getContainerMatchRating: function(value) {
        const num = parseFloat(value);
        if (num >= 8.5) {
            return {
                label: 'Optimal',
                icon: '✓✓',
                class: 'excellent',
                color: '#10b981'
            };
        } else if (num >= 6.0) {
            return {
                label: 'Good',
                icon: '✓',
                class: 'good',
                color: '#3b82f6'
            };
        } else if (num >= 4.0) {
            return {
                label: 'Fair',
                icon: '⚠️',
                class: 'fair',
                color: '#fbbf24'
            };
        } else {
            return {
                label: 'Poor',
                icon: '❌',
                class: 'poor',
                color: '#ef4444'
            };
        }
    },
    
    /**
     * Get rating interpretation for priority level (1-10)
     */
    getPriorityRating: function(value) {
        const num = parseInt(value);
        if (num >= 8) {
            return {
                label: 'Highest',
                icon: '🔴',
                class: 'highest',
                color: '#ef4444'
            };
        } else if (num >= 5) {
            return {
                label: 'High',
                icon: '🟡',
                class: 'high',
                color: '#fbbf24'
            };
        } else {
            return {
                label: 'Low',
                icon: '🟢',
                class: 'low',
                color: '#10b981'
            };
        }
    }
};

// ==================== PRIORITY WEIGHTS MAPPING ====================
(function injectPriorityWeightsHelpers() {
    if (window.__priorityWeightsInjected) {
        return;
    }
    
    const PRIORITY_WEIGHT_MAPPING = {
        economy: {
            speed: 20,
            cost: 60,
            risk: 20,
            description: 'Ưu tiên chi phí thấp, chấp nhận thời gian lâu hơn'
        },
        standard: {
            speed: 40,
            cost: 40,
            risk: 20,
            description: 'Cân bằng giữa chi phí, thời gian và rủi ro'
        },
        express: {
            speed: 70,
            cost: 20,
            risk: 10,
            description: 'Ưu tiên tốc độ, chấp nhận chi phí cao hơn'
        },
        critical: {
            speed: 80,
            cost: 10,
            risk: 10,
            description: 'Giao hàng cấp bách, tối thiểu hóa rủi ro trễ'
        }
    };
    
    function getPriorityWeights(profile) {
        return PRIORITY_WEIGHT_MAPPING[profile] || PRIORITY_WEIGHT_MAPPING.standard;
    }
    
    function updatePriorityWeightsDisplay() {
        const profileInput = document.getElementById('priority_input');
        const profile = profileInput?.value || 'standard';
        const weights = getPriorityWeights(profile);
        
        const speedDisplay = document.getElementById('priority_speed_display');
        const costDisplay = document.getElementById('priority_cost_display');
        const riskDisplay = document.getElementById('priority_risk_display');
        const descDisplay = document.getElementById('priority_description');
        
        if (speedDisplay) speedDisplay.textContent = `${weights.speed}%`;
        if (costDisplay) costDisplay.textContent = `${weights.cost}%`;
        if (riskDisplay) riskDisplay.textContent = `${weights.risk}%`;
        if (descDisplay) descDisplay.textContent = weights.description;
    }
    
    if (typeof window.getPriorityWeights !== 'function') {
        window.getPriorityWeights = getPriorityWeights;
    }
    if (typeof window.updatePriorityWeightsDisplay !== 'function') {
        window.updatePriorityWeightsDisplay = updatePriorityWeightsDisplay;
    }
    
    document.addEventListener('DOMContentLoaded', () => {
        const priorityDropdown = document.getElementById('priority_dropdown');
        if (priorityDropdown) {
            priorityDropdown.addEventListener('change', () => {
                if (typeof window.updatePriorityWeightsDisplay === 'function') {
                    window.updatePriorityWeightsDisplay();
                }
            });
            setTimeout(() => {
                if (typeof window.updatePriorityWeightsDisplay === 'function') {
                    window.updatePriorityWeightsDisplay();
                }
            }, 500);
        }
    });
    
    window.__priorityWeightsInjected = true;
})();

/**
 * ========================================
 * BENCHMARK DATA - Industry Standards
 * ========================================
 */
const BenchmarkData = {
    reliability: {
        industryAvg: 65,
        excellent: 85,
        poor: 30
    },
    carrierRating: {
        industryAvg: 3.5,
        excellent: 4.5,
        poor: 2.0
    },
    esgScore: {
        industryAvg: 65,
        excellent: 80,
        poor: 40
    },
    containerMatch: {
        isoStandard: 8.0,
        optimal: 9.0,
        minimum: 6.0
    },
    portClimateStress: {
        noaaAlert: 7.0,
        critical: 8.5,
        safe: 4.0
    },
    climateVolatility: {
        stable: 30,
        moderate: 50,
        high: 70
    }
};

// ============================================================
// GLOBAL STATE MANAGEMENT
// ============================================================

const SmartInputState = {
    selectedRoute: null,
    selectedTransportMode: null,
    selectedPOL: null,
    selectedPOD: null,
    selectedCargoType: null,
    recentShipments: [],
    validationErrors: {},
    
    /**
     * Helper: Get LOGISTICS_DATA safely
     */
    getLogisticsData: function() {
        return window._LOGISTICS_DATA_REF || window.LOGISTICS_DATA || (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null);
    },
    completedFields: new Set(),
    initialized: false
};

const SmartInputSystem = {
    /**
     * ========================================
     * PART 1: INITIALIZATION
     * ========================================
     */
    /**
     * Helper: Get LOGISTICS_DATA safely
     */
    getLogisticsData: function() {
        return SmartInputState.getLogisticsData ? SmartInputState.getLogisticsData() : (window.LOGISTICS_DATA || window._LOGISTICS_DATA_REF || (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null));
    },
    
    init: function() {
        // Prevent multiple initialization - STRICT MODE
        if (window.__SMART_INPUT_INITIALIZED__ && SmartInputState.initialized) {
            console.warn('[SmartInput] Already initialized, skipping auto-init...');
            return; // Stop here to prevent conflicts
        }
        
        if (SmartInputState.initialized) {
            console.log('⚠️ Smart Input System already initialized');
            return;
        }
        
        console.log('🚀 Initializing Smart Input System v13.0 ULTIMATE...');
        
        // Check if LOGISTICS_DATA is loaded (check both global and window)
        if (typeof LOGISTICS_DATA === 'undefined' && typeof window.LOGISTICS_DATA === 'undefined') {
            console.error('❌ LOGISTICS_DATA not loaded! Please load logistics_data.js first.');
            console.warn('⚠️ Retrying in 500ms...');
            setTimeout(() => {
                if (typeof LOGISTICS_DATA !== 'undefined' || typeof window.LOGISTICS_DATA !== 'undefined') {
                    console.log('✅ LOGISTICS_DATA loaded, re-initializing...');
                    this.init();
                } else {
                    console.error('❌ LOGISTICS_DATA still not available after retry');
                }
            }, 500);
            return;
        }
        
        // Use window.LOGISTICS_DATA if available, fallback to LOGISTICS_DATA
        const LOGISTICS_DATA_SOURCE = window.LOGISTICS_DATA || (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null);
        
        if (!LOGISTICS_DATA_SOURCE) {
            console.error('❌ LOGISTICS_DATA not available!');
            return;
        }
        
        // Store reference globally for use in other methods
        window._LOGISTICS_DATA_REF = LOGISTICS_DATA_SOURCE;
        
        // Initialize all features
        this.initRouteBasedSuggestions();
        this.initCountryAutoSuggest();
        this.initPortSelectors();
        this.initContainerRecommendation();
        this.initTransitTimeCalculation();
        this.initClimateAutoFetch();
        this.initRealtimeValidation();
        this.initProgressTracking();
        this.initSliderDisplays();
        this.initStarRating();
        this.initCollapsibleSections();
        this.initTooltips();
        this.initPresetButtons();
        this.initSectionEnhancements();
        this.initProgressRings();
        this.initSparklines();
        this.initPresetExportImport();
        this.initKeyboardShortcuts();
        this.initSmartDefaults();
        this.initConditionalFields();
        this.initCopyPreviousShipment();
        this.initMobileOptimization();
        this.initEnhancedDemoMode();
        
        SmartInputState.initialized = true;
        
        console.log('✅ Smart Input System initialized successfully');
    },
    
    /**
     * ========================================
     * PART 2: ROUTE-BASED SUGGESTIONS (CORE FEATURE)
     * ========================================
     */
    initRouteBasedSuggestions: function() {
        console.log('✓ [INIT] Route-Based Suggestions activated');
        
        const routeDropdown = document.getElementById('route_dropdown');
        if (!routeDropdown) {
            // Only warn if we're on input page
            if (window.location.pathname.includes('/input')) {
                console.warn('⚠️ Route dropdown not found');
            }
            return;
        }
        
        // Listen for option selection trong route dropdown
        const routeOptions = routeDropdown.querySelectorAll('.dropdown-option');
        routeOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                const routeKey = option.getAttribute('data-value');
                if (routeKey) {
                    console.log('📍 Route option clicked:', routeKey);
                    setTimeout(() => {
                        this.handleRouteSelection(routeKey);
                    }, 200);
                }
            });
        });
        
        // Check if route is already selected on page load
        setTimeout(() => {
            const selectedRoute = this.getDropdownValue('route_dropdown');
            if (selectedRoute) {
                console.log('📍 Found pre-selected route:', selectedRoute);
                this.handleRouteSelection(selectedRoute);
            }
        }, 500);
        
        // Listen for manual selection changes via mutation observer
        const observer = new MutationObserver(() => {
            const selectedOption = routeDropdown.querySelector('.dropdown-option.selected');
            if (selectedOption) {
                const routeKey = selectedOption.getAttribute('data-value');
                if (routeKey && routeKey !== SmartInputState.selectedRoute) {
                    console.log('📍 Route changed via mutation:', routeKey);
                    this.handleRouteSelection(routeKey);
                }
            }
        });
        
        observer.observe(routeDropdown, { 
            childList: true, 
            subtree: true, 
            attributes: true,
            attributeFilter: ['class']
        });
    },
    
    handleRouteSelection: function(routeKey) {
        if (!routeKey) {
            const routeValue = this.getDropdownValue('route_dropdown');
            if (!routeValue) return;
            routeKey = routeValue;
        }
        
        console.log(`📍 Route selected: ${routeKey}`);
        SmartInputState.selectedRoute = routeKey;
        
        // Populate Transport Modes with error handling
        try {
            this.populateTransportModes(routeKey);
        } catch (error) {
            console.error('❌ Error in populateTransportModes:', error);
            console.error('Stack:', error.stack);
        }
        
        // Reset dependent fields
        this.resetTransportDependentFields();
    },
    
    populateTransportModes: function(routeKey) {
        // Use SmartInputState.getLogisticsData() or fallback to window.LOGISTICS_DATA
        const LOGISTICS_DATA = SmartInputState.getLogisticsData ? SmartInputState.getLogisticsData() : (window.LOGISTICS_DATA || window._LOGISTICS_DATA_REF || (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null));
        if (!LOGISTICS_DATA) {
            console.error('❌ LOGISTICS_DATA not available in populateTransportModes');
            console.warn('⚠️ Retrying in 500ms...');
            setTimeout(() => this.populateTransportModes(routeKey), 500);
            return;
        }
        
        // Map HTML route value to logistics key if needed
        const logisticsRouteKey = LOGISTICS_DATA.mapRouteFromHTML ? LOGISTICS_DATA.mapRouteFromHTML(routeKey) : routeKey;
        console.log(`📍 populateTransportModes: HTML key="${routeKey}", logistics key="${logisticsRouteKey}"`);
        
        const route = LOGISTICS_DATA.getRoute(logisticsRouteKey);
        
        if (!route) {
            console.error(`❌ Route "${logisticsRouteKey}" not found in LOGISTICS_DATA`);
            console.log('Available routes:', Object.keys(LOGISTICS_DATA.routes || {}));
            return;
        }
        
        const transportModes = route.transport_modes;
        
        if (!transportModes || transportModes.length === 0) {
            console.warn('⚠️ No transport modes for route:', routeKey);
            return;
        }
        
        console.log(`✓ Found ${transportModes.length} transport modes for ${routeKey}`);
        
        const transportDropdown = document.getElementById('transport_mode_dropdown');
        const transportMenu = document.getElementById('transport_mode_menu') || transportDropdown?.querySelector('.dropdown-menu');
        const transportTrigger = transportDropdown?.querySelector('.dropdown-trigger .dropdown-value');
        
        if (!transportMenu) {
            console.error('❌ Transport mode menu not found');
            console.log('Debug info:', {
                transportDropdown: !!transportDropdown,
                transportMenuById: !!document.getElementById('transport_mode_menu'),
                transportMenuByQuery: !!transportDropdown?.querySelector('.dropdown-menu'),
                dropdownHTML: transportDropdown ? transportDropdown.outerHTML.substring(0, 200) : 'null'
            });
            return;
        }
        
        console.log(`✓ Transport menu found, populating ${transportModes.length} options...`);
        
        // Clear existing options
        transportMenu.innerHTML = '';
        
        // Sort modes: default first, then by share
        transportModes.sort((a, b) => {
            if (a.default && !b.default) return -1;
            if (!a.default && b.default) return 1;
            return (b.share || 0) - (a.share || 0);
        });
        
        // Populate new options
        transportModes.forEach(mode => {
            const option = document.createElement('div');
            option.className = 'dropdown-option';
            if (mode.default) {
                option.classList.add('recommended');
            }
            option.setAttribute('data-value', mode.value);
            option.setAttribute('role', 'option');
            
            // Build option HTML
            let optionText = mode.label;
            if (mode.default) optionText += ' [ĐỀ XUẤT]';
            if (mode.hours) {
                optionText += ` • ${mode.hours} giờ`;
            } else if (mode.days) {
                optionText += ` • ${mode.days} ngày`;
            }
            if (mode.share) {
                optionText += ` • ${mode.share}% thị phần`;
            }
            // Use the LOGISTICS_DATA already retrieved at the start of the function
            const riskLabel = LOGISTICS_DATA.getRiskLabel(mode.risk_level);
            optionText += ` [RỦI RO: ${riskLabel.toUpperCase()}]`;
            
            option.innerHTML = `
                <div class="transport-option-content">
                    <div class="transport-label">
                        ${optionText}
                    </div>
                    <div class="transport-description">${mode.description || ''}</div>
                </div>
            `;
            
            // Add click handler with proper event handling
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                e.stopImmediatePropagation();
                
                console.log(`✓ Transport mode clicked: ${mode.value}`);
                
                // Mark as selected
                transportMenu.querySelectorAll('.dropdown-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                option.classList.add('selected');
                
                // Update dropdown display value
                if (transportTrigger) {
                    transportTrigger.textContent = mode.label || mode.value;
                    transportTrigger.classList.remove('placeholder');
                }
                
                // Get full mode object
                const fullMode = route.transport_modes.find(m => m.value === mode.value);
                
                // Select the mode
                this.selectTransportMode(fullMode || mode, routeKey);
                
                // Close dropdown
                if (transportDropdown) {
                    transportDropdown.classList.remove('active');
                }
            });
            
            transportMenu.appendChild(option);
        });
        
        console.log(`✅ Successfully populated ${transportModes.length} transport mode options into menu`);
        console.log(`   Menu now has ${transportMenu.children.length} children`);
        
        // Ensure menu is visible when dropdown is active
        if (transportDropdown) {
            const menu = transportDropdown.querySelector('.dropdown-menu') || transportMenu;
            if (menu) {
                menu.style.setProperty('display', 'block', 'important');
                menu.style.setProperty('visibility', 'visible', 'important');
                menu.style.setProperty('opacity', '1', 'important');
                menu.style.setProperty('z-index', '10003', 'important');
            }
        }
        
        // Setup dropdown trigger
        if (transportDropdown) {
            const trigger = transportDropdown.querySelector('.dropdown-trigger');
            if (trigger) {
                // CRITICAL FIX: Close all other dropdowns first to prevent ghost dropdowns
                document.querySelectorAll('.custom-dropdown.active').forEach(dd => {
                    if (dd !== transportDropdown) {
                        dd.classList.remove('active');
                        const menu = dd.querySelector('.dropdown-menu');
                        if (menu) {
                            menu.style.display = 'none';
                            menu.style.visibility = 'hidden';
                            menu.style.opacity = '0';
                        }
                    }
                });
                
                const newTrigger = trigger.cloneNode(true);
                trigger.parentNode.replaceChild(newTrigger, trigger);
                
                newTrigger.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    
                    // CRITICAL FIX: Use global closeAllDropdowns function to prevent ghost dropdowns
                    if (typeof closeAllDropdowns === 'function') {
                        closeAllDropdowns(transportDropdown.id);
                    } else {
                        // Fallback: Close all other dropdowns
                        document.querySelectorAll('.custom-dropdown.active').forEach(dd => {
                            if (dd !== transportDropdown) {
                                dd.classList.remove('active');
                                const menu = dd.querySelector('.dropdown-menu');
                                if (menu) {
                                    menu.style.display = 'none';
                                    menu.style.visibility = 'hidden';
                                    menu.style.opacity = '0';
                                    menu.classList.remove('active');
                                }
                            }
                        });
                    }
                    
                    // Toggle this dropdown
                    const isActive = transportDropdown.classList.contains('active');
                    if (isActive) {
                        transportDropdown.classList.remove('active');
                        const menu = transportDropdown.querySelector('.dropdown-menu');
                        if (menu) {
                            menu.style.display = 'none';
                            menu.style.visibility = 'hidden';
                            menu.style.opacity = '0';
                            menu.classList.remove('active');
                        }
                    } else {
                        transportDropdown.classList.add('active');
                        const menu = transportDropdown.querySelector('.dropdown-menu');
                        if (menu) {
                            menu.style.display = 'block';
                            menu.style.visibility = 'visible';
                            menu.style.opacity = '1';
                            menu.classList.add('active');
                        }
                    }
                });
            }
        }
        
        // Enable dropdown
        if (transportTrigger) {
            transportTrigger.textContent = 'Chọn phương thức vận tải';
            transportTrigger.classList.remove('placeholder');
        }
        
        // Auto-select default mode
        const defaultMode = transportModes.find(m => m.default);
        if (defaultMode) {
            setTimeout(() => {
                const fullDefaultMode = route.transport_modes.find(m => m.value === defaultMode.value);
                this.selectTransportMode(fullDefaultMode || defaultMode, routeKey);
            }, 300);
        }
        
        console.log('✓ Transport modes populated successfully');
    },
    
    selectTransportMode: function(mode, routeKey) {
        console.log(`🚢 Transport mode selected: ${mode.label}`);
        
        // Update dropdown UI
        const transportDropdown = document.getElementById('transport_mode_dropdown');
        const valueSpan = transportDropdown?.querySelector('.dropdown-value');
        if (valueSpan) {
            valueSpan.textContent = mode.label;
            valueSpan.classList.remove('placeholder');
        }
        
        // Update hidden input
        const hiddenInput = document.getElementById('transport_mode_input');
        if (hiddenInput) {
            hiddenInput.value = mode.value;
        }
        
        // Mark selected option
        transportDropdown?.querySelectorAll('.dropdown-option').forEach(opt => {
            opt.classList.remove('selected');
            if (opt.getAttribute('data-value') === mode.value) {
                opt.classList.add('selected');
            }
        });
        
        // Close dropdown
        transportDropdown?.classList.remove('active');
        
        SmartInputState.selectedTransportMode = mode.value;
        
        // Populate POL/POD options
        this.populatePortOptions(mode, routeKey);
    },
    
    /**
     * ========================================
     * PART 3: PORT OPTIONS (POL/POD)
     * ========================================
     */
    populatePortOptions: function(mode, routeKey) {
        console.log('🔍 populatePortOptions called with mode:', mode);
        
        if (!mode.routes || mode.routes.length === 0) {
            console.warn('⚠️ No port routes available for this mode:', mode.value);
            return;
        }
        
        console.log(`✓ Found ${mode.routes.length} port routes:`, mode.routes);
        
        const polDropdown = document.getElementById('pol_dropdown');
        const polMenu = document.getElementById('pol_menu') || polDropdown?.querySelector('.dropdown-menu');
        const polTrigger = polDropdown?.querySelector('.dropdown-value');
        
        const podDropdown = document.getElementById('pod_dropdown');
        const podMenu = document.getElementById('pod_menu') || podDropdown?.querySelector('.dropdown-menu');
        const podTrigger = podDropdown?.querySelector('.dropdown-value');
        
        if (!polMenu || !podMenu) {
            console.error('❌ POL/POD menus not found');
            console.log('Debug info:', {
                polDropdown: !!polDropdown,
                polMenuById: !!document.getElementById('pol_menu'),
                polMenuByQuery: !!polDropdown?.querySelector('.dropdown-menu'),
                podDropdown: !!podDropdown,
                podMenuById: !!document.getElementById('pod_menu'),
                podMenuByQuery: !!podDropdown?.querySelector('.dropdown-menu')
            });
            return;
        }
        
        console.log(`✓ POL/POD menus found, populating options...`);
        
        // Clear existing
        polMenu.innerHTML = '';
        podMenu.innerHTML = '';
        
        // Get unique POLs
        const uniquePOLs = [...new Set(mode.routes.map(r => r.pol))];
        uniquePOLs.forEach(pol => {
            const polOption = document.createElement('div');
            polOption.className = 'dropdown-option';
            polOption.setAttribute('data-value', pol);
            polOption.setAttribute('role', 'option');
            polOption.textContent = pol;
            
            polOption.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                
                // Mark as selected
                polMenu.querySelectorAll('.dropdown-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                polOption.classList.add('selected');
                
                // Select POL
                this.selectPOL(pol, mode, polDropdown, podDropdown);
                
                // Close dropdown
                if (polDropdown) {
                    polDropdown.classList.remove('active');
                }
            });
            
            polMenu.appendChild(polOption);
        });
        
        // Enable POL dropdown
        if (polTrigger) {
            polTrigger.textContent = 'Chọn cảng bốc hàng';
            polTrigger.classList.remove('placeholder');
        }
        
        // Setup POL dropdown trigger
        if (polDropdown) {
            const polTriggerBtn = polDropdown.querySelector('.dropdown-trigger');
            if (polTriggerBtn) {
                const newTrigger = polTriggerBtn.cloneNode(true);
                polTriggerBtn.parentNode.replaceChild(newTrigger, polTriggerBtn);
                
                newTrigger.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    
                    // CRITICAL FIX: Use global closeAllDropdowns function to prevent ghost dropdowns
                    if (typeof closeAllDropdowns === 'function') {
                        closeAllDropdowns(polDropdown.id);
                    } else {
                        // Fallback: Close all other dropdowns
                        document.querySelectorAll('.custom-dropdown.active').forEach(dd => {
                            if (dd !== polDropdown) {
                                dd.classList.remove('active');
                                const menu = dd.querySelector('.dropdown-menu');
                                if (menu) {
                                    menu.style.display = 'none';
                                    menu.style.visibility = 'hidden';
                                    menu.style.opacity = '0';
                                    menu.classList.remove('active');
                                }
                            }
                        });
                    }
                    
                    // Toggle this dropdown
                    const isActive = polDropdown.classList.contains('active');
                    if (isActive) {
                        polDropdown.classList.remove('active');
                        const menu = polDropdown.querySelector('.dropdown-menu');
                        if (menu) {
                            menu.style.display = 'none';
                            menu.style.visibility = 'hidden';
                            menu.style.opacity = '0';
                            menu.classList.remove('active');
                        }
                    } else {
                        polDropdown.classList.add('active');
                        const menu = polDropdown.querySelector('.dropdown-menu');
                        if (menu) {
                            menu.style.display = 'block';
                            menu.style.visibility = 'visible';
                            menu.style.opacity = '1';
                            menu.classList.add('active');
                        }
                    }
                });
            }
        }
        
        // Auto-select first POL
        if (uniquePOLs.length > 0) {
            setTimeout(() => {
                this.selectPOL(uniquePOLs[0], mode, polDropdown, podDropdown);
            }, 200);
        }
    },
    
    selectPOL: function(pol, mode, polDropdown, podDropdown) {
        console.log(`📍 POL selected: ${pol}`);
        
        // Update POL UI
        const polValue = polDropdown?.querySelector('.dropdown-value');
        if (polValue) {
            polValue.textContent = pol;
            polValue.classList.remove('placeholder');
        }
        polDropdown?.classList.remove('active');
        
        // Update hidden input
        const polInput = document.getElementById('pol_input');
        if (polInput) {
            polInput.value = pol;
        }
        
        SmartInputState.selectedPOL = pol;
        
        // Get matching PODs
        const matchingRoutes = mode.routes.filter(r => r.pol === pol);
        const podMenu = document.getElementById('pod_menu') || podDropdown?.querySelector('.dropdown-menu');
        const podTrigger = podDropdown?.querySelector('.dropdown-value');
        
        if (!podMenu) {
            console.error('❌ POD menu not found in selectPOL');
            return;
        }
        
        console.log(`✓ Found ${matchingRoutes.length} matching POD routes for POL: ${pol}`);
        
        podMenu.innerHTML = '';
        
        matchingRoutes.forEach(route => {
            const podOption = document.createElement('div');
            podOption.className = 'dropdown-option';
            podOption.setAttribute('data-value', route.pod);
            
            let podText = route.pod;
            if (route.km) podText += ` • ${route.km.toLocaleString()} km`;
            if (route.days) {
                podText += ` • ${route.days} ngày`;
            } else if (route.hours) {
                podText += ` • ${route.hours} giờ`;
            }
            if (route.cost) podText += ` • ${route.cost}`;
            
            podOption.innerHTML = `
                <div class="port-option-content">
                    <div class="port-name">${podText}</div>
                </div>
            `;
            
            podOption.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                
                // Mark as selected
                podMenu.querySelectorAll('.dropdown-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                podOption.classList.add('selected');
                
                // Select POD
                this.selectPOD(route, podDropdown);
                
                // Close dropdown
                if (podDropdown) {
                    podDropdown.classList.remove('active');
                }
            });
            
            podMenu.appendChild(podOption);
        });
        
        console.log(`✅ Successfully populated POD options into menu`);
        
        // Ensure POD menu is visible when dropdown is active
        if (podDropdown) {
            const menu = podDropdown.querySelector('.dropdown-menu') || podMenu;
            if (menu) {
                menu.style.setProperty('display', 'block', 'important');
                menu.style.setProperty('visibility', 'visible', 'important');
                menu.style.setProperty('opacity', '1', 'important');
                menu.style.setProperty('z-index', '10003', 'important');
            }
        }
        
        // Setup POD dropdown trigger
        if (podDropdown) {
            const podTriggerBtn = podDropdown.querySelector('.dropdown-trigger');
            if (podTriggerBtn) {
                const newTrigger = podTriggerBtn.cloneNode(true);
                podTriggerBtn.parentNode.replaceChild(newTrigger, podTriggerBtn);
                
                newTrigger.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    
                    // CRITICAL FIX: Use global closeAllDropdowns function to prevent ghost dropdowns
                    if (typeof closeAllDropdowns === 'function') {
                        closeAllDropdowns(podDropdown.id);
                    } else {
                        // Fallback: Close all other dropdowns
                        document.querySelectorAll('.custom-dropdown.active').forEach(dd => {
                            if (dd !== podDropdown) {
                                dd.classList.remove('active');
                                const menu = dd.querySelector('.dropdown-menu');
                                if (menu) {
                                    menu.style.display = 'none';
                                    menu.style.visibility = 'hidden';
                                    menu.style.opacity = '0';
                                    menu.classList.remove('active');
                                }
                            }
                        });
                    }
                    
                    // Toggle this dropdown
                    const isActive = podDropdown.classList.contains('active');
                    if (isActive) {
                        podDropdown.classList.remove('active');
                        const menu = podDropdown.querySelector('.dropdown-menu');
                        if (menu) {
                            menu.style.display = 'none';
                            menu.style.visibility = 'hidden';
                            menu.style.opacity = '0';
                            menu.classList.remove('active');
                        }
                    } else {
                        podDropdown.classList.add('active');
                        const menu = podDropdown.querySelector('.dropdown-menu');
                        if (menu) {
                            menu.style.display = 'block';
                            menu.style.visibility = 'visible';
                            menu.style.opacity = '1';
                            menu.classList.add('active');
                        }
                    }
                });
            }
        }
        
        // Enable POD dropdown
        if (podTrigger) {
            podTrigger.textContent = 'Chọn cảng dỡ hàng';
            podTrigger.classList.remove('placeholder');
        }
        
        // Auto-select first POD
        if (matchingRoutes.length > 0) {
            setTimeout(() => {
                this.selectPOD(matchingRoutes[0], podDropdown);
            }, 200);
        }
    },
    
    selectPOD: function(route, podDropdown) {
        console.log(`🏁 POD selected: ${route.pod}`);
        
        // Update POD UI
        const podValue = podDropdown?.querySelector('.dropdown-value');
        if (podValue) {
            podValue.textContent = route.pod;
            podValue.classList.remove('placeholder');
        }
        podDropdown?.classList.remove('active');
        
        // Update hidden input
        const podInput = document.getElementById('pod_input');
        if (podInput) {
            podInput.value = route.pod;
        }
        
        SmartInputState.selectedPOD = route.pod;
        
        // Auto-fill distance
        if (route.km) {
            const distanceInput = document.getElementById('distance');
            if (distanceInput) {
                distanceInput.value = route.km;
                this.animateAutoFill(distanceInput);
                console.log(`✓ Auto-filled distance: ${route.km} km`);
            }
        }
        
        // Auto-fill transit time
        if (route.days || route.hours) {
            const transitDisplay = document.getElementById('transit_time_display');
            const transitHidden = document.getElementById('transit_time');
            
            if (transitDisplay) {
                if (route.days) {
                    transitDisplay.value = `${route.days} ngày`;
                    if (transitHidden) transitHidden.value = route.days;
                } else if (route.hours) {
                    const days = Math.ceil(route.hours / 24);
                    transitDisplay.value = `${route.hours} giờ (${days} ngày)`;
                    if (transitHidden) transitHidden.value = days;
                }
                this.animateAutoFill(transitDisplay);
                console.log(`✓ Auto-filled transit time: ${route.days || route.hours}`);
            }
        }
    },
    
    resetTransportDependentFields: function() {
        // Reset transport mode
        const transportDropdown = document.getElementById('transport_mode_dropdown');
        const transportValue = transportDropdown?.querySelector('.dropdown-value');
        if (transportValue) {
            transportValue.textContent = 'Chọn phương thức vận tải';
            transportValue.classList.add('placeholder');
        }
        
        // Reset POL/POD
        const polDropdown = document.getElementById('pol_dropdown');
        const podDropdown = document.getElementById('pod_dropdown');
        
        if (polDropdown) {
            const polValue = polDropdown.querySelector('.dropdown-value');
            if (polValue) {
                polValue.textContent = 'Chọn phương thức trước';
                polValue.classList.add('placeholder');
            }
        }
        
        if (podDropdown) {
            const podValue = podDropdown.querySelector('.dropdown-value');
            if (podValue) {
                podValue.textContent = 'Chọn phương thức trước';
                podValue.classList.add('placeholder');
            }
        }
        
        // Reset distance and transit time
        const distanceInput = document.getElementById('distance');
        const transitDisplay = document.getElementById('transit_time_display');
        
        if (distanceInput) distanceInput.value = '';
        if (transitDisplay) transitDisplay.value = '';
    },
    
    /**
     * ========================================
     * PART 4: COUNTRY AUTO-SUGGEST
     * ========================================
     */
    initCountryAutoSuggest: function() {
        console.log('✓ [INIT] Country Auto-suggest activated');
        
        const sellerDropdown = document.getElementById('seller_country_dropdown') || 
                               document.querySelector('[id*="seller_country"]');
        const buyerDropdown = document.getElementById('buyer_country_dropdown') || 
                              document.querySelector('[id*="buyer_country"]');
        
        if (!sellerDropdown || !buyerDropdown) {
            // Only warn if we're on input page
            if (window.location.pathname.includes('/input')) {
                // Silently skip - country dropdowns may not exist on all pages
            }
            return;
        }
        
        sellerDropdown.addEventListener('change', () => this.handleCountryChange());
        buyerDropdown.addEventListener('change', () => this.handleCountryChange());
    },
    
    handleCountryChange: function() {
        const sellerCountry = this.getDropdownValue('seller_country_dropdown') || 
                             this.getDropdownValue('seller_country');
        const buyerCountry = this.getDropdownValue('buyer_country_dropdown') || 
                            this.getDropdownValue('buyer_country');
        
        if (!sellerCountry || !buyerCountry) {
            console.log('⏸️ Waiting for both countries to be selected');
            return;
        }
        
        this.autoSuggestRoute(sellerCountry, buyerCountry);
    },
    
    autoSuggestRoute: function(seller, buyer) {
        console.log(`🔍 Auto-suggesting route: ${seller} → ${buyer}`);
        
        let routeKey = null;
        
        if (seller === 'vn' || seller === 'vietnam') {
            if (buyer === 'us' || buyer === 'united_states') routeKey = 'vn_us';
            else if (buyer === 'cn' || buyer === 'china') routeKey = 'vn_cn';
            else if (buyer === 'kr' || buyer === 'south_korea') routeKey = 'vn_kr';
            else if (buyer === 'jp' || buyer === 'japan') routeKey = 'vn_jp';
            else if (buyer === 'eu' || buyer === 'nl' || buyer === 'de' || buyer === 'europe') routeKey = 'vn_eu';
            else if (buyer === 'hk' || buyer === 'hong_kong') routeKey = 'vn_hk';
            else if (buyer === 'in' || buyer === 'india') routeKey = 'vn_in';
            else if (buyer === 'th' || buyer === 'thailand') routeKey = 'vn_th';
            else if (buyer === 'tw' || buyer === 'taiwan') routeKey = 'vn_tw';
        }
        
        if (seller === buyer || (seller === 'vn' && buyer === 'vn')) {
            routeKey = 'domestic';
        }
        
        const LOGISTICS_DATA = SmartInputSystem.getLogisticsData();
        if (!LOGISTICS_DATA) return;
        if (routeKey && LOGISTICS_DATA.routes[routeKey]) {
            const routeData = LOGISTICS_DATA.routes[routeKey];
            console.log(`✓ Found route: ${routeData.name_vi || routeData.name}`);
            
            setTimeout(() => {
                this.selectDropdownOption('route_dropdown', routeKey);
                SmartInputState.selectedRoute = routeKey;
                this.handleRouteSelection(routeKey);
            }, 200);
        }
    },
    
    /**
     * ========================================
     * PART 5: PORT SELECTORS WITH SEARCH
     * ========================================
     */
    initPortSelectors: function() {
        console.log('✓ [INIT] Port Selectors activated');
        // Port search functionality already handled by POL/POD dropdowns
    },
    
    /**
     * ========================================
     * PART 6: CONTAINER RECOMMENDATION
     * ========================================
     */
    initContainerRecommendation: function() {
        console.log('✓ [INIT] Container Recommendation activated');
        
        const cargoDropdown = document.getElementById('cargo_type_dropdown') ||
                             document.querySelector('[id*="cargo_type"]');
        
        if (!cargoDropdown) {
            // Only warn if we're on input page
            if (window.location.pathname.includes('/input')) {
                // Silently skip - cargo dropdown may not exist on all pages
            }
            return;
        }
        
        cargoDropdown.addEventListener('change', () => this.handleCargoTypeChange());
    },
    
    handleCargoTypeChange: function() {
        const cargoType = this.getDropdownValue('cargo_type_dropdown') || 
                         this.getDropdownValue('cargo_type');
        
        if (!cargoType) return;
        
        console.log(`📦 Cargo type changed: ${cargoType}`);
        SmartInputState.selectedCargoType = cargoType;
        
        // Container recommendation logic can be added here
    },
    
    /**
     * ========================================
     * PART 7: TRANSIT TIME CALCULATION
     * ========================================
     */
    initTransitTimeCalculation: function() {
        console.log('✓ [INIT] Enhanced Transit Time Calculation activated');
        
        const etdInput = document.getElementById('etd') || document.getElementById('etd_input');
        const etaInput = document.getElementById('eta') || document.getElementById('eta_input');
        const transitDisplay = document.getElementById('transit_time_display');
        const transitHidden = document.getElementById('transit_time');
        
        if (!etdInput || !etaInput) {
            // Only warn if we're on input page
            if (window.location.pathname.includes('/input')) {
                // Silently skip - ETD/ETA inputs may not exist on all pages
            }
            return;
        }
        
        // Function to calculate and display transit time from ETD/ETA
        const updateTransitTime = () => {
            if (!etdInput.value || !etaInput.value) {
                if (transitDisplay) {
                    transitDisplay.value = '';
                    transitDisplay.style.borderColor = '';
                    transitDisplay.style.background = '';
                }
                if (transitHidden) transitHidden.value = '';
                return;
            }
            
            const etdDate = new Date(etdInput.value);
            const etaDate = new Date(etaInput.value);
            
            // Validate dates
            if (etaDate <= etdDate) {
                if (transitDisplay) {
                    transitDisplay.value = '';
                    transitDisplay.style.borderColor = '#ef4444';
                    transitDisplay.style.background = 'rgba(239, 68, 68, 0.1)';
                }
                if (transitHidden) transitHidden.value = '';
                this.showError('eta', 'ETA phải sau ETD');
                return;
            }
            
            // Calculate days
            const diffTime = Math.abs(etaDate - etdDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            // Update displays with animation
            if (transitDisplay) {
                transitDisplay.value = `${diffDays} ngày`;
                transitDisplay.style.background = 'rgba(0, 255, 136, 0.1)';
                transitDisplay.style.borderColor = '#00ffc3';
                transitDisplay.classList.add('glow-animation');
                
                setTimeout(() => {
                    transitDisplay.style.background = '';
                    transitDisplay.classList.remove('glow-animation');
                }, 1000);
            }
            
            if (transitHidden) {
                transitHidden.value = diffDays;
            }
            
            this.clearError('eta');
            
            console.log(`✓ Transit time calculated: ${diffDays} days`);
        };
        
        // Attach event listeners
        etdInput.addEventListener('change', updateTransitTime);
        etaInput.addEventListener('change', updateTransitTime);
        
        // Initial calculation if both dates exist
        if (etdInput.value && etaInput.value) {
            updateTransitTime();
        }
    },
    
    calculateTransitTime: function() {
        // Keep for backward compatibility
        const etdInput = document.getElementById('etd') || document.getElementById('etd_input');
        const etaInput = document.getElementById('eta') || document.getElementById('eta_input');
        
        if (!etdInput || !etdInput.value) return;
        
        const routeKey = SmartInputState.selectedRoute;
        const transportMode = SmartInputState.selectedTransportMode;
        
        if (!routeKey || !transportMode) return;
        
        // Get transit days from current selection
        const LOGISTICS_DATA = window._LOGISTICS_DATA_REF || window.LOGISTICS_DATA || (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null);
        if (!LOGISTICS_DATA) {
            console.error('❌ LOGISTICS_DATA not available in handleRouteSelection');
            return;
        }
        const route = LOGISTICS_DATA.getRoute(routeKey);
        if (!route) return;
        
        const mode = route.transport_modes.find(m => m.value === transportMode);
        if (!mode) return;
        
        let days = 0;
        if (mode.days) {
            // Parse days string (e.g., "7-10" → take average)
            const daysParts = mode.days.split('-').map(d => parseInt(d.trim()));
            days = daysParts.length > 1 ? Math.ceil((daysParts[0] + daysParts[1]) / 2) : daysParts[0];
        } else if (mode.hours) {
            const hoursParts = mode.hours.split('-').map(h => parseInt(h.trim()));
            const avgHours = hoursParts.length > 1 ? (hoursParts[0] + hoursParts[1]) / 2 : hoursParts[0];
            days = Math.ceil(avgHours / 24);
        }
        
        if (days > 0) {
            const etd = new Date(etdInput.value);
            const eta = new Date(etd);
            eta.setDate(eta.getDate() + days);
            
            etaInput.value = eta.toISOString().split('T')[0];
            this.animateAutoFill(etaInput);
            
            console.log(`📅 Calculated ETA: ${eta.toLocaleDateString()} (${days} days)`);
        }
    },
    
    /**
     * ========================================
     * CLIMATE DATA AUTO-FETCH
     * ========================================
     */
    initClimateAutoFetch: function() {
        console.log('✓ [INIT] Climate Data Auto-Fetch activated');
        
        const etdInput = document.getElementById('etd') || document.getElementById('etd_input');
        const etaInput = document.getElementById('eta') || document.getElementById('eta_input');
        const routeDropdown = document.getElementById('route_dropdown');
        
        const tryFetchClimate = () => {
            const route = SmartInputState.selectedRoute;
            const etd = etdInput?.value;
            const eta = etaInput?.value;
            
            if (route && etd && eta) {
                this.fetchClimateData(route, etd, eta);
            }
        };
        
        if (etdInput) etdInput.addEventListener('change', tryFetchClimate);
        if (etaInput) etaInput.addEventListener('change', tryFetchClimate);
        if (routeDropdown) routeDropdown.addEventListener('change', tryFetchClimate);
    },
    
    async fetchClimateData(route, etd, eta) {
        const transitMonth = new Date(etd).getMonth() + 1;
        const transitYear = new Date(etd).getFullYear();
        
        const startDate = new Date(etd);
        const endDate = new Date(eta);
        
        try {
            const response = await fetch('/api/climate_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    route: route,
                    start_date: startDate.toISOString().split('T')[0],
                    end_date: endDate.toISOString().split('T')[0],
                    pol: SmartInputState.selectedPOL || '',
                    pod: SmartInputState.selectedPOD || ''
                })
            });
            
            if (!response.ok) throw new Error('Climate API failed');
            
            const climateData = await response.json();
            this.populateClimateFields(climateData);
            
        } catch (error) {
            console.warn('⚠️ Climate API unavailable, using defaults');
            this.populateClimateDefaults(route, transitMonth);
        }
    },
    
    populateClimateFields(data) {
        const fields = {
            'enso_index': data.enso || 0.0,
            'typhoon_frequency': data.typhoon_freq || 0.5,
            'sst_anomaly': data.sst_anomaly || 0.0,
            'port_climate_stress': data.port_stress || 5.0,
            'climate_volatility_index': data.volatility || 50
        };
        
        Object.keys(fields).forEach(fieldId => {
            const input = document.getElementById(fieldId);
            if (input) {
                input.value = fields[fieldId];
                
                // Trigger slider display update
                if (input.type === 'range') {
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
                
                // Animation
                input.style.background = 'rgba(0, 255, 136, 0.1)';
                setTimeout(() => {
                    input.style.background = '';
                }, 1000);
            }
        });
        
        // Show notification
        this.showNotification('✓ Climate data loaded from NOAA/NASA', 'success');
    },
    
    populateClimateDefaults(route, month) {
        // Fallback: Use seasonal patterns
        const isTyphoonSeason = [6, 7, 8, 9, 10].includes(month);
        
        const defaults = {
            'enso_index': 0.0,
            'typhoon_frequency': isTyphoonSeason ? 0.7 : 0.3,
            'sst_anomaly': 0.0,
            'port_climate_stress': 5.0,
            'climate_volatility_index': isTyphoonSeason ? 65 : 45
        };
        
        Object.keys(defaults).forEach(fieldId => {
            const input = document.getElementById(fieldId);
            if (input && !input.value) {
                input.value = defaults[fieldId];
                if (input.type === 'range') {
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
        });
    },
    
    showNotification(message, type) {
        // Simple notification - can be enhanced later
        console.log(`[${type.toUpperCase()}] ${message}`);
    },
    
    /**
     * ========================================
     * PART 8: REAL-TIME VALIDATION
     * ========================================
     */
    initRealtimeValidation: function() {
        console.log('✓ [INIT] Real-time Validation activated');
        
        const requiredFields = document.querySelectorAll('input[required], select[required]');
        
        requiredFields.forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('input', () => {
                if (field.classList.contains('error-field')) {
                    this.validateField(field);
                } else {
                    this.markFieldValid(field);
                }
            });
        });
    },
    
    validateField: function(field) {
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        
        if (isRequired && !value) {
            field.classList.add('error-field');
            field.classList.remove('field-completed');
            return false;
        }
        
        field.classList.remove('error-field');
        this.markFieldValid(field);
        return true;
    },
    
    markFieldValid: function(field) {
        if (field.value && field.value.trim()) {
            field.classList.add('field-completed');
            SmartInputState.completedFields.add(field.id);
        }
    },
    
    // Helper functions for error display
    showError: function(fieldId, message) {
        const field = document.getElementById(fieldId);
        const errorElement = document.getElementById(fieldId + '_error') || 
                            field?.parentElement?.querySelector('.error-message');
        
        if (field) {
            field.classList.add('error-field');
            field.style.borderColor = '#ef4444';
        }
        
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    },
    
    clearError: function(fieldId) {
        const field = document.getElementById(fieldId);
        const errorElement = document.getElementById(fieldId + '_error') || 
                            field?.parentElement?.querySelector('.error-message');
        
        if (field) {
            field.classList.remove('error-field');
            field.style.borderColor = '';
        }
        
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.style.display = 'none';
        }
    },
    
    /**
     * ========================================
     * PART 9: PROGRESS TRACKING
     * ========================================
     */
    initProgressTracking: function() {
        console.log('✓ [INIT] Progress Tracking activated');

        // If the host page already injected its own progress tracker, avoid adding duplicate listeners
        if (window.disableSmartProgressTracking || typeof window.scheduleProgressUpdate === 'function' || typeof window.updateProgress === 'function') {
            console.log('↪ Detected host progress tracker, skipping SmartInput duplicate listeners');
            return;
        }
        
        const calculateProgress = () => {
            const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
            const filledFields = Array.from(requiredFields).filter(field => {
                if (field.tagName === 'INPUT' && field.type !== 'checkbox') {
                    return field.value && field.value.trim() !== '';
                }
                if (field.tagName === 'SELECT') {
                    return field.value;
                }
                if (field.tagName === 'TEXTAREA') {
                    return field.value && field.value.trim() !== '';
                }
                return false;
            });
            
            const progress = requiredFields.length > 0 
                ? Math.round((filledFields.length / requiredFields.length) * 100) 
                : 0;
            
            // Update progress bar
            const progressBar = document.getElementById('header_progress_bar');
            const progressText = document.getElementById('header_progress_text');
            
            if (progressBar) {
                progressBar.style.width = progress + '%';
            }
            if (progressText) {
                progressText.textContent = progress + '%';
            }
            
            return progress;
        };
        
        document.addEventListener('input', calculateProgress);
        document.addEventListener('change', calculateProgress);
        
        setTimeout(calculateProgress, 500);
    },
    
    /**
     * ========================================
     * PART 10: SLIDER DISPLAYS
     * ========================================
     */
    initSliderDisplays: function() {
        console.log('✓ [INIT] Slider Displays with Dynamic Badges activated');
        
        const sliders = [
            { 
                id: 'carrier_rating', 
                format: (val) => `${parseFloat(val).toFixed(1)} ⭐`,
                bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
                interpreter: (val) => RatingInterpreter.getCarrierRating(val),
                benchmark: BenchmarkData.carrierRating
            },
            { 
                id: 'weather_risk', 
                format: (val) => `${parseFloat(val).toFixed(1)}/10`,
                interpreter: (val) => RatingInterpreter.getRiskRating(val),
                bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
                benchmark: null
            },
            { 
                id: 'port_risk', 
                format: (val) => `${parseFloat(val).toFixed(1)}/10`,
                interpreter: (val) => RatingInterpreter.getRiskRating(val),
                bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
                benchmark: null
            },
            { 
                id: 'priority_level', 
                format: (val) => `${parseInt(val)}/10`,
                interpreter: (val) => RatingInterpreter.getPriorityRating(val),
                bubbleFormat: (val) => `${parseInt(val)}`,
                benchmark: null
            },
            { 
                id: 'container_match', 
                format: (val) => `${parseFloat(val).toFixed(1)}/10`,
                interpreter: (val) => RatingInterpreter.getContainerMatchRating(val),
                bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
                benchmark: BenchmarkData.containerMatch
            },
            { 
                id: 'seller_reliability', 
                format: (val) => `${parseInt(val)}/100`,
                interpreter: (val) => RatingInterpreter.getReliabilityRating(val),
                bubbleFormat: (val) => `${parseInt(val)}`,
                benchmark: BenchmarkData.reliability
            },
            { 
                id: 'buyer_reliability', 
                format: (val) => `${parseInt(val)}/100`,
                interpreter: (val) => RatingInterpreter.getReliabilityRating(val),
                bubbleFormat: (val) => `${parseInt(val)}`,
                benchmark: BenchmarkData.reliability
            },
            { 
                id: 'port_climate_stress', 
                format: (val) => `${parseFloat(val).toFixed(1)}/10`,
                interpreter: (val) => RatingInterpreter.getRiskRating(val),
                bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
                benchmark: BenchmarkData.portClimateStress
            },
            { 
                id: 'climate_volatility_index', 
                format: (val) => `${parseInt(val)}/100`,
                interpreter: null,
                bubbleFormat: (val) => `${parseInt(val)}`,
                benchmark: BenchmarkData.climateVolatility
            },
            { 
                id: 'climate_resilience', 
                format: (val) => `${parseFloat(val).toFixed(1)}/10`,
                interpreter: null,
                bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
                benchmark: null
            },
            { 
                id: 'green_packaging', 
                format: (val) => `${parseInt(val)}%`,
                interpreter: null,
                bubbleFormat: (val) => `${parseInt(val)}%`,
                benchmark: null
            }
        ];
        
        let initializedCount = 0;
        
        sliders.forEach(slider => {
            const input = document.getElementById(slider.id);
            const display = document.getElementById(`${slider.id}_display`);
            
            // Skip if input doesn't exist or is not a range slider
            if (!input || input.type !== 'range') {
                // Silently skip - element may have been removed during refactor
                return;
            }
            
            // Skip if display element doesn't exist
            if (!display) {
                // Silently skip - display element may not be needed for this slider
                return;
            }
            
            const formGroup = input?.closest('.form-group');
            
            if (input && display) {
                const minValue = parseFloat(input.min) || 0;
                const maxValue = parseFloat(input.max) || 100;
                const sliderRange = maxValue - minValue;
                const numberInput = document.getElementById(`${slider.id}_number`);
                
                // Create or get dynamic badge element
                let dynamicBadge = formGroup?.querySelector('.dynamic-badge');
                if (!dynamicBadge && slider.interpreter) {
                    dynamicBadge = document.createElement('span');
                    dynamicBadge.className = 'dynamic-badge';
                    dynamicBadge.setAttribute('data-value', input.value);
                    // Insert after display element
                    display.parentNode.insertBefore(dynamicBadge, display.nextSibling);
                }

                // Create value bubble (only for long-range sliders)
                const shouldShowBubble = !input.classList.contains('slider-hidden') && (sliderRange > 20 || !!numberInput);
                let valueBubble = null;
                if (shouldShowBubble) {
                    valueBubble = formGroup?.querySelector('.slider-value-bubble');
                    if (!valueBubble) {
                        valueBubble = document.createElement('div');
                        valueBubble.className = 'slider-value-bubble';
                        formGroup?.appendChild(valueBubble);
                    }
                }
                
                // Create benchmark hint if benchmark data exists
                let benchmarkHint = formGroup?.querySelector('.benchmark-hint');
                if (!benchmarkHint && slider.benchmark) {
                    benchmarkHint = document.createElement('div');
                    benchmarkHint.className = 'benchmark-hint';
                    formGroup.appendChild(benchmarkHint);
                }
                
                // Initialize display with current value
                const currentValue = input.value || input.getAttribute('value') || input.defaultValue || '0';
                display.textContent = slider.format(currentValue);
                
                // Update dynamic badge if interpreter exists
                const updateBadge = (value) => {
                    if (dynamicBadge && slider.interpreter) {
                        const rating = slider.interpreter(value);
                        dynamicBadge.className = `dynamic-badge ${rating.class}`;
                        dynamicBadge.setAttribute('data-value', value);
                        dynamicBadge.innerHTML = `
                            <span class="badge-icon">${rating.icon}</span>
                            <span class="badge-text">${rating.label}</span>
                        `;
                        
                        // Add animation
                        dynamicBadge.style.transform = 'scale(1.05)';
                        setTimeout(() => {
                            dynamicBadge.style.transform = 'scale(1)';
                        }, 150);
                    }
                };
                
                // Update benchmark hint
                const updateBenchmark = (value) => {
                    if (benchmarkHint && slider.benchmark) {
                        const num = parseFloat(value);
                        const avg = slider.benchmark.industryAvg || slider.benchmark.isoStandard || slider.benchmark.noaaAlert;
                        const diff = num - avg;
                        const diffText = diff >= 0 ? `+${diff.toFixed(0)}` : diff.toFixed(0);
                        const comparison = diff >= 0 ? 'Above' : 'Below';
                        const benchmarkLabel = slider.benchmark.industryAvg ? 'Industry Avg' : 
                                               slider.benchmark.isoStandard ? 'ISO Standard' : 
                                               slider.benchmark.noaaAlert ? 'NOAA Alert' : 'Benchmark';
                        
                        benchmarkHint.innerHTML = `
                            <span class="benchmark-marker">${benchmarkLabel}: ${avg}</span>
                            <span class="benchmark-marker">Your Score: ${num.toFixed(1)} (${comparison} ${Math.abs(diff).toFixed(0)})</span>
                        `;
                    }
                };
                
                // Update slider bubble position/value
                const updateValueBubble = (value) => {
                    if (!valueBubble) return;
                    const numericValue = parseFloat(value) || 0;
                    const percent = ((numericValue - minValue) / (maxValue - minValue)) * 100;
                    const bubbleFormatter = slider.bubbleFormat || ((val) => {
                        const step = parseFloat(input.step) || 1;
                        return step < 1 ? parseFloat(val).toFixed(1) : parseFloat(val).toFixed(0);
                    });
                    valueBubble.textContent = bubbleFormatter(value);

                    const sliderRect = input.getBoundingClientRect();
                    const groupRect = formGroup?.getBoundingClientRect();
                    if (!groupRect.width || !sliderRect.width) return;

                    const sliderOffsetLeft = sliderRect.left - groupRect.left;
                    const sliderOffsetTop = sliderRect.top - groupRect.top;
                    const clampedPercent = Math.min(Math.max(percent, 0), 100) / 100;
                    const bubbleLeft = sliderOffsetLeft + clampedPercent * sliderRect.width;

                    valueBubble.style.left = `${bubbleLeft}px`;
                    valueBubble.style.top = `${sliderOffsetTop - 36}px`;
                };

                const updateNumberInput = (value) => {
                    if (!numberInput) return;
                    numberInput.value = Math.round(parseFloat(value) || 0);
                };

                // Update display on input change (real-time as user moves slider)
                const updateDisplay = (e) => {
                    const value = e ? e.target.value : input.value;
                    display.textContent = slider.format(value);
                    updateBadge(value);
                    updateBenchmark(value);
                    updateValueBubble(value);
                    updateNumberInput(value);
                };
                
                // Initialize badge and benchmark
                updateBadge(currentValue);
                updateBenchmark(currentValue);
                updateValueBubble(currentValue);
                updateNumberInput(currentValue);
                
                // Listen for input event (fires continuously as slider moves)
                input.addEventListener('input', updateDisplay);
                
                // Also listen for change event (fires when slider is released)
                input.addEventListener('change', updateDisplay);
                
                // Listen for mousemove on slider (for better real-time feedback)
                input.addEventListener('mousemove', (e) => {
                    if (e.buttons === 1) { // Only if mouse button is pressed
                        updateDisplay(e);
                    }
                });

                if (numberInput) {
                    numberInput.addEventListener('input', (e) => {
                        let newValue = parseFloat(e.target.value);
                        if (isNaN(newValue)) newValue = minValue;
                        newValue = Math.min(maxValue, Math.max(minValue, newValue));
                        input.value = newValue;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    });
                }
                
                initializedCount++;
                console.log(`✅ Slider display initialized: ${slider.id} → ${display.id}`);
            }
        });
        
        console.log(`✅ Slider displays: ${initializedCount}/${sliders.length} initialized`);
        
        // Only retry if we have at least one slider initialized (meaning sliders exist in DOM)
        // and we haven't initialized all of them yet
        if (initializedCount > 0 && initializedCount < sliders.length) {
            setTimeout(() => {
                console.log('🔄 Retrying slider initialization for missing elements...');
                this.initSliderDisplays();
            }, 500);
        } else if (initializedCount === 0) {
            console.log('ℹ️ No slider displays found in DOM - this is normal if sliders were removed during refactor');
        }
    },

    initStarRating: function() {
        const slider = document.getElementById('carrier_rating');
        const starContainer = document.getElementById('carrier_rating_stars');
        
        // Skip if slider doesn't exist or is not a range slider
        if (!slider || slider.type !== 'range') {
            // Silently skip - element may have been removed during refactor
            return;
        }
        
        // Skip if star container doesn't exist
        if (!starContainer) {
            // Silently skip - star rating UI may not be needed
            return;
        }

        const stars = starContainer.querySelectorAll('.star');
        
        if (stars.length === 0) {
            // Silently skip - no star elements found
            return;
        }

        const updateStars = (value) => {
            stars.forEach(star => {
                const starValue = parseInt(star.getAttribute('data-value'), 10);
                if (starValue <= value) {
                    star.classList.add('active');
                } else {
                    star.classList.remove('active');
                }
            });
        };

        stars.forEach(star => {
            star.addEventListener('click', () => {
                const starValue = parseInt(star.getAttribute('data-value'), 10);
                slider.value = starValue;
                slider.dispatchEvent(new Event('input', { bubbles: true }));
            });
        });

        slider.addEventListener('input', () => {
            updateStars(parseFloat(slider.value) || 0);
        });

        updateStars(parseFloat(slider.value) || 0);
    },
    
    /**
     * ========================================
     * PART 11: COLLAPSIBLE SECTIONS
     * ========================================
     */
    initCollapsibleSections: function() {
        console.log('✓ [INIT] Collapsible Sections activated');
        
        const sections = document.querySelectorAll('.form-section.collapsible');
        
        sections.forEach(section => {
            const header = section.querySelector('.section-header');
            
            if (header) {
                header.addEventListener('click', () => {
                    this.toggleSection(section);
                });
            }
        });
    },
    
    toggleSection: function(section) {
        const content = section.querySelector('.section-content');
        const icon = section.querySelector('.collapse-icon');
        
        if (!content) return;
        
        const isCollapsed = content.classList.contains('collapsed') || 
                           content.style.display === 'none' ||
                           window.getComputedStyle(content).display === 'none';
        
        if (isCollapsed) {
            // Expand
            content.classList.remove('collapsed');
            content.style.display = '';
            if (icon) icon.style.transform = 'rotate(180deg)';
        } else {
            // Collapse
            content.classList.add('collapsed');
            content.style.display = 'none';
            if (icon) icon.style.transform = 'rotate(0deg)';
        }
        
        console.log(`✓ Section ${section.id} toggled:`, isCollapsed ? 'expanded' : 'collapsed');
    },
    
    /**
     * ========================================
     * PART 12: STUB FUNCTIONS (TO BE IMPLEMENTED)
     * ========================================
     */
    initSmartDefaults: function() {
        console.log('✓ [INIT] Smart Defaults activated');
        // Smart defaults are handled by individual init functions
    },
    
    initConditionalFields: function() {
        console.log('✓ [INIT] Conditional Fields activated');
        // Conditional fields logic can be added here if needed
    },
    
    /**
     * ========================================
     * PART 13: TOOLTIP SYSTEM
     * ========================================
     */
    initTooltips: function() {
        console.log('✓ [INIT] Tooltip System activated');
        
        const tooltipData = {
            'carrier_rating': {
                title: 'Carrier Rating',
                content: 'Rate the reliability and performance of your shipping carrier. Higher ratings indicate better on-time delivery, fewer damages, and superior customer service.',
                benchmarks: 'Industry Average: 3.5/5.0'
            },
            'weather_risk': {
                title: 'Weather Risk Assessment',
                content: 'Evaluate potential weather-related delays. Consider seasonal patterns, typhoon seasons, and historical weather data for your route.',
                benchmarks: 'Low (1-3): Favorable | Moderate (3-6): Normal | High (6-8): Monitor | Extreme (8-10): Delay Recommended'
            },
            'port_risk': {
                title: 'Port Risk Level',
                content: 'Assess port infrastructure, congestion, labor disputes, and security concerns. Higher risk may require alternative routing or additional insurance.',
                benchmarks: 'Safe (1-3) | Moderate (3-6) | Dangerous (6-8) | Critical (8-10)'
            },
            'priority_level': {
                title: 'Shipment Priority',
                content: 'Set priority based on delivery urgency, customer importance, and cargo value. Higher priority may incur premium shipping costs.',
                benchmarks: 'Low (1-4) | High (5-7) | Highest (8-10)'
            },
            'container_match': {
                title: 'Container Suitability',
                content: 'How well your cargo fits the selected container type. Optimal match reduces damage risk and maximizes space utilization.',
                benchmarks: 'ISO Standard: 8.0+ | Optimal: 9.0+ | Minimum: 6.0'
            },
            'seller_reliability': {
                title: 'Seller Reliability Score',
                content: 'Historical performance of the seller including on-time shipments, quality consistency, and communication reliability.',
                benchmarks: 'Industry Average: 65/100 | Excellent: 85+ | Poor: <30'
            },
            'buyer_reliability': {
                title: 'Buyer Reliability Score',
                content: 'Buyer payment history, order fulfillment rate, and dispute resolution. Higher scores indicate more reliable partners.',
                benchmarks: 'Industry Average: 65/100 | Excellent: 85+ | Poor: <30'
            },
            'port_climate_stress': {
                title: 'Port Climate Stress',
                content: 'NOAA climate data indicating port vulnerability to extreme weather, sea level rise, and climate-related disruptions.',
                benchmarks: 'NOAA Alert Threshold: 7.0 | Critical: 8.5+ | Safe: <4.0'
            },
            'climate_volatility_index': {
                title: 'Climate Volatility Index',
                content: 'Measure of climate variability affecting shipping routes. Higher values indicate more unpredictable weather patterns.',
                benchmarks: 'Stable: <30 | Moderate: 30-70 | High: >70'
            },
            'climate_resilience': {
                title: 'Climate Resilience Score',
                content: 'Port and route ability to withstand and recover from climate-related disruptions. Higher scores indicate better infrastructure.',
                benchmarks: 'Weak (1-4) | Moderate (4-7) | Strong (7-10)'
            },
            'green_packaging': {
                title: 'Green Packaging Percentage',
                content: 'Percentage of packaging materials that are recyclable, biodegradable, or sustainably sourced. Higher values improve ESG scores.',
                benchmarks: 'Target: 50%+ | Excellent: 80%+ | Industry Standard: 30%'
            }
        };
        
        // Create tooltip container
        let tooltipContainer = document.getElementById('tooltip-container');
        if (!tooltipContainer) {
            tooltipContainer = document.createElement('div');
            tooltipContainer.id = 'tooltip-container';
            tooltipContainer.className = 'tooltip-container';
            document.body.appendChild(tooltipContainer);
        }
        
        // Add info icons to labels
        Object.keys(tooltipData).forEach(sliderId => {
            const slider = document.getElementById(sliderId);
            if (!slider) return;
            
            const formGroup = slider.closest('.form-group');
            if (!formGroup) return;
            
            const label = formGroup.querySelector('.form-label');
            if (!label) return;
            
            // Check if tooltip icon already exists
            if (label.querySelector('.tooltip-icon')) return;
            
            const tooltipIcon = document.createElement('span');
            tooltipIcon.className = 'tooltip-icon';
            tooltipIcon.innerHTML = 'ⓘ';
            tooltipIcon.setAttribute('data-tooltip', sliderId);
            tooltipIcon.setAttribute('aria-label', 'More information');
            
            label.appendChild(tooltipIcon);
            
            // Add event listeners
            tooltipIcon.addEventListener('mouseenter', (e) => {
                this.showTooltip(e, tooltipData[sliderId]);
            });
            
            tooltipIcon.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    },
    
    showTooltip: function(event, data) {
        const tooltipContainer = document.getElementById('tooltip-container');
        if (!tooltipContainer) return;
        
        tooltipContainer.innerHTML = `
            <div class="tooltip-content">
                <div class="tooltip-header">
                    <h4>${data.title}</h4>
                </div>
                <div class="tooltip-body">
                    <p>${data.content}</p>
                    ${data.benchmarks ? `<div class="tooltip-benchmark">📊 ${data.benchmarks}</div>` : ''}
                </div>
            </div>
        `;
        
        tooltipContainer.style.display = 'block';
        
        // Position tooltip
        const rect = event.target.getBoundingClientRect();
        const tooltipRect = tooltipContainer.getBoundingClientRect();
        
        let top = rect.top - tooltipRect.height - 10;
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        
        // Adjust if tooltip goes off screen
        if (left < 10) left = 10;
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }
        if (top < 10) {
            top = rect.bottom + 10;
        }
        
        tooltipContainer.style.top = top + 'px';
        tooltipContainer.style.left = left + 'px';
    },
    
    hideTooltip: function() {
        const tooltipContainer = document.getElementById('tooltip-container');
        if (tooltipContainer) {
            tooltipContainer.style.display = 'none';
        }
    },
    
    /**
     * ========================================
     * PART 14: PRESET BUTTONS
     * ========================================
     */
    initPresetButtons: function() {
        console.log('✓ [INIT] Preset Buttons activated');
        
        const presets = {
            conservative: {
                carrier_rating: 5,
                weather_risk: 3.0,
                port_risk: 3.0,
                priority_level: 8,
                container_match: 9.0,
                seller_reliability: 85,
                buyer_reliability: 85
            },
            balanced: {
                carrier_rating: 4,
                weather_risk: 5.0,
                port_risk: 5.0,
                priority_level: 5,
                container_match: 7.0,
                seller_reliability: 65,
                buyer_reliability: 65
            },
            aggressive: {
                carrier_rating: 2,
                weather_risk: 7.0,
                port_risk: 7.0,
                priority_level: 3,
                container_match: 5.0,
                seller_reliability: 45,
                buyer_reliability: 45
            }
        };
        
        // Find or create preset buttons container
        const advancedParamsSection = document.getElementById('advanced-params');
        if (!advancedParamsSection) return;
        
        let presetContainer = advancedParamsSection.querySelector('.preset-buttons-container');
        if (!presetContainer) {
            presetContainer = document.createElement('div');
            presetContainer.className = 'preset-buttons-container';
            
            const sectionHeader = advancedParamsSection.querySelector('.section-header');
            if (sectionHeader) {
                sectionHeader.insertAdjacentElement('afterend', presetContainer);
            }
        }
        
        presetContainer.innerHTML = `
            <div class="preset-buttons">
                <button type="button" class="preset-btn conservative" data-preset="conservative">
                    <span class="preset-icon">🛡️</span>
                    <span class="preset-label">Conservative</span>
                    <span class="preset-desc">Low risk, high reliability</span>
                </button>
                <button type="button" class="preset-btn balanced active" data-preset="balanced">
                    <span class="preset-icon">⚖️</span>
                    <span class="preset-label">Balanced</span>
                    <span class="preset-desc">Standard settings</span>
                </button>
                <button type="button" class="preset-btn aggressive" data-preset="aggressive">
                    <span class="preset-icon">⚡</span>
                    <span class="preset-label">Aggressive</span>
                    <span class="preset-desc">Cost-optimized</span>
                </button>
            </div>
        `;
        
        // Add click handlers
        presetContainer.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const presetName = e.currentTarget.getAttribute('data-preset');
                this.applyPreset(presets[presetName]);
                
                // Update active state
                presetContainer.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });
    },
    
    applyPreset: function(preset) {
        console.log('📋 Applying preset:', preset);
        
        Object.keys(preset).forEach(sliderId => {
            const slider = document.getElementById(sliderId);
            if (!slider) return;
            
            const value = preset[sliderId];
            slider.value = value;
            
            // Trigger input event to update displays and badges
            const event = new Event('input', { bubbles: true });
            slider.dispatchEvent(event);
            
            // Add visual feedback
            slider.style.transform = 'scale(1.02)';
            setTimeout(() => {
                slider.style.transform = 'scale(1)';
            }, 200);
        });
        
        // Show notification
        this.showNotification('Preset applied successfully', 'success');
    },
    
    showNotification: function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    },
    
    /**
     * ========================================
     * PART 15: SECTION-SPECIFIC ENHANCEMENTS
     * ========================================
     */
    initSectionEnhancements: function() {
        console.log('✓ [INIT] Section Enhancements activated');
        
        // Add verified supplier badge for high reliability
        this.initVerifiedBadges();
        
        // Add risk heatmap indicator
        this.initRiskHeatmap();
        
        // Add company size icons
        this.initCompanySizeIcons();
    },
    
    initVerifiedBadges: function() {
        const sellerReliability = document.getElementById('seller_reliability');
        const buyerReliability = document.getElementById('buyer_reliability');
        
        const addVerifiedBadge = (slider, sectionId) => {
            if (!slider) return;
            
            const formGroup = slider.closest('.form-group');
            if (!formGroup) return;
            
            const section = document.getElementById(sectionId);
            if (!section) return;
            
            const updateBadge = () => {
                const value = parseInt(slider.value);
                let badge = section.querySelector('.verified-badge');
                
                if (value >= 90) {
                    if (!badge) {
                        badge = document.createElement('div');
                        badge.className = 'verified-badge';
                        badge.innerHTML = `
                            <span class="verified-icon">✓</span>
                            <span class="verified-text">Verified Supplier</span>
                        `;
                        
                        const sectionHeader = section.querySelector('.section-header');
                        if (sectionHeader) {
                            sectionHeader.appendChild(badge);
                        }
                    }
                    badge.style.display = 'flex';
                } else if (badge) {
                    badge.style.display = 'none';
                }
            };
            
            slider.addEventListener('input', updateBadge);
            slider.addEventListener('change', updateBadge);
            updateBadge();
        };
        
        addVerifiedBadge(sellerReliability, 'seller-info');
        addVerifiedBadge(buyerReliability, 'buyer-info');
    },
    
    initRiskHeatmap: function() {
        const advancedSection = document.getElementById('advanced-params');
        if (!advancedSection) return;
        
        // Create risk heatmap indicator
        const heatmapContainer = document.createElement('div');
        heatmapContainer.className = 'risk-heatmap-container';
        heatmapContainer.innerHTML = `
            <div class="risk-heatmap-header">
                <span class="heatmap-icon">🔥</span>
                <span class="heatmap-title">Overall Risk Assessment</span>
            </div>
            <div class="risk-heatmap">
                <div class="heatmap-bar">
                    <div class="heatmap-fill" id="risk_heatmap_fill"></div>
                </div>
                <div class="heatmap-label" id="risk_heatmap_label">Calculating...</div>
            </div>
        `;
        
        const formGrid = advancedSection.querySelector('.form-grid');
        if (formGrid) {
            formGrid.insertAdjacentElement('beforebegin', heatmapContainer);
        }
        
        // Calculate overall risk
        const calculateRisk = () => {
            const weatherRisk = parseFloat(document.getElementById('weather_risk')?.value || 5);
            const portRisk = parseFloat(document.getElementById('port_risk')?.value || 5);
            const carrierRating = parseFloat(document.getElementById('carrier_rating')?.value || 3);
            const containerMatch = parseFloat(document.getElementById('container_match')?.value || 7);
            
            // Normalize carrier rating (inverse: higher rating = lower risk)
            const carrierRisk = 10 - (carrierRating * 2);
            
            // Normalize container match (inverse: higher match = lower risk)
            const containerRisk = 10 - containerMatch;
            
            // Weighted average
            const overallRisk = (
                weatherRisk * 0.3 +
                portRisk * 0.3 +
                carrierRisk * 0.2 +
                containerRisk * 0.2
            );
            
            const fill = document.getElementById('risk_heatmap_fill');
            const label = document.getElementById('risk_heatmap_label');
            
            if (fill && label) {
                const percentage = (overallRisk / 10) * 100;
                fill.style.width = percentage + '%';
                
                let riskLevel, riskColor;
                if (overallRisk >= 7.5) {
                    riskLevel = 'Extreme Risk';
                    riskColor = '#dc2626';
                } else if (overallRisk >= 6.0) {
                    riskLevel = 'High Risk';
                    riskColor = '#ef4444';
                } else if (overallRisk >= 4.0) {
                    riskLevel = 'Moderate Risk';
                    riskColor = '#fbbf24';
                } else {
                    riskLevel = 'Low Risk';
                    riskColor = '#10b981';
                }
                
                fill.style.background = `linear-gradient(90deg, ${riskColor}, ${riskColor}dd)`;
                label.textContent = `${overallRisk.toFixed(1)}/10 - ${riskLevel}`;
                label.style.color = riskColor;
            }
        };
        
        // Listen to relevant sliders
        ['weather_risk', 'port_risk', 'carrier_rating', 'container_match'].forEach(id => {
            const slider = document.getElementById(id);
            if (slider) {
                slider.addEventListener('input', calculateRisk);
                slider.addEventListener('change', calculateRisk);
            }
        });
        
        // Initial calculation
        setTimeout(calculateRisk, 500);
    },
    
    initCompanySizeIcons: function() {
        const sizeDropdowns = [
            { id: 'seller_size_dropdown', icon: '🏢' },
            { id: 'buyer_size_dropdown', icon: '🏢' }
        ];
        
        const sizeIcons = {
            'SME': '🏢',
            'Small/Medium': '🏢',
            'Medium': '🏭',
            'Medium Enterprise': '🏭',
            'Large': '🌐',
            'Large Corporation': '🌐'
        };
        
        sizeDropdowns.forEach(({ id, defaultIcon }) => {
            const dropdown = document.getElementById(id);
            if (!dropdown) return;
            
            const trigger = dropdown.querySelector('.dropdown-trigger');
            if (!trigger) return;
            
            const updateIcon = () => {
                const value = this.getDropdownValue(id);
                const icon = sizeIcons[value] || defaultIcon;
                
                let iconElement = trigger.querySelector('.size-icon');
                if (!iconElement) {
                    iconElement = document.createElement('span');
                    iconElement.className = 'size-icon';
                    trigger.insertBefore(iconElement, trigger.firstChild);
                }
                iconElement.textContent = icon;
            };
            
            dropdown.addEventListener('change', updateIcon);
            updateIcon();
        });
    },
    
    initCopyPreviousShipment: function() {
        console.log('✓ [INIT] Copy Previous Shipment (stub)');
        // To be implemented
    },
    
    initMobileOptimization: function() {
        console.log('✓ [INIT] Mobile Optimization activated');
        // Mobile optimizations are handled via CSS media queries
    },
    
    initEnhancedDemoMode: function() {
        console.log('✓ [INIT] Enhanced Demo Mode activated');
        // Demo mode can be enhanced here if needed
    },
    
    /**
     * ========================================
     * PART 16: MINI PROGRESS RINGS
     * ========================================
     */
    initProgressRings: function() {
        console.log('✓ [INIT] Progress Rings activated');
        
        const metrics = [
            { id: 'seller_reliability', label: 'Seller', max: 100 },
            { id: 'buyer_reliability', label: 'Buyer', max: 100 },
            { id: 'carrier_rating', label: 'Carrier', max: 5, multiplier: 20 },
            { id: 'container_match', label: 'Container', max: 10, multiplier: 10 }
        ];
        
        // Find or create progress rings container
        const advancedSection = document.getElementById('advanced-params');
        if (!advancedSection) return;
        
        let ringsContainer = advancedSection.querySelector('.progress-ring-container');
        if (!ringsContainer) {
            ringsContainer = document.createElement('div');
            ringsContainer.className = 'progress-ring-container';
            
            const sectionHeader = advancedSection.querySelector('.section-header');
            if (sectionHeader) {
                sectionHeader.insertAdjacentElement('afterend', ringsContainer);
            }
        }
        
        ringsContainer.innerHTML = '';
        
        metrics.forEach(metric => {
            const ring = this.createProgressRing(metric);
            ringsContainer.appendChild(ring);
        });
        
        // Update rings on slider changes
        metrics.forEach(metric => {
            const slider = document.getElementById(metric.id);
            if (slider) {
                const updateRing = () => {
                    const value = slider.value || slider.getAttribute('value') || slider.defaultValue || '0';
                    this.updateProgressRing(metric.id, value, metric);
                };
                
                // Remove existing listeners to avoid duplicates
                slider.removeEventListener('input', updateRing);
                slider.removeEventListener('change', updateRing);
                
                // Add new listeners
                slider.addEventListener('input', updateRing);
                slider.addEventListener('change', updateRing);
                
                // Initial update
                setTimeout(() => {
                    updateRing();
                }, 100);
            } else {
                console.warn(`⚠️ Slider not found for progress ring: ${metric.id}`);
            }
        });
    },
    
    createProgressRing: function(metric) {
        const ring = document.createElement('div');
        ring.className = 'progress-ring';
        ring.id = `ring_${metric.id}`;
        
        const circumference = 2 * Math.PI * 35; // radius = 35
        
        ring.innerHTML = `
            <svg width="80" height="80">
                <circle class="progress-ring-circle progress-ring-bg" 
                        cx="40" cy="40" r="35" />
                <circle class="progress-ring-circle progress-ring-fill" 
                        cx="40" cy="40" r="35" 
                        stroke-dasharray="${circumference}"
                        stroke-dashoffset="${circumference}" />
            </svg>
            <div class="progress-ring-label">
                <span class="progress-ring-value" id="ring_value_${metric.id}">0</span>
                <span class="progress-ring-title">${metric.label}</span>
            </div>
        `;
        
        return ring;
    },
    
    updateProgressRing: function(sliderId, value, metric) {
        // Fix: Use correct ring ID format
        const ringId = `ring_${sliderId}`;
        const ring = document.getElementById(ringId);
        if (!ring) {
            console.warn(`⚠️ Progress ring not found: ${ringId}`);
            return;
        }
        
        const fill = ring.querySelector('.progress-ring-fill');
        const valueLabel = document.getElementById(`ring_value_${sliderId}`);
        
        if (!fill || !valueLabel) {
            console.warn(`⚠️ Progress ring elements not found for: ${sliderId}`);
            return;
        }
        
        const numValue = parseFloat(value) || 0;
        const percentage = (numValue / metric.max) * 100;
        const circumference = 2 * Math.PI * 35;
        const offset = circumference - (percentage / 100) * circumference;
        
        // Update stroke dash offset
        fill.style.strokeDashoffset = offset;
        
        // Update value label with correct format
        if (metric.max === 5) {
            // Carrier rating: show as "3.0" format
            valueLabel.textContent = numValue.toFixed(1);
        } else if (metric.max === 10) {
            // Container match: show as "8.0" format
            valueLabel.textContent = numValue.toFixed(1);
        } else {
            // Reliability: show as integer "55"
            valueLabel.textContent = Math.round(numValue).toString();
        }
        
        // Update color based on percentage
        if (percentage >= 85) {
            fill.style.stroke = '#10b981';
            valueLabel.style.color = '#10b981';
        } else if (percentage >= 60) {
            fill.style.stroke = '#3b82f6';
            valueLabel.style.color = '#3b82f6';
        } else if (percentage >= 40) {
            fill.style.stroke = '#fbbf24';
            valueLabel.style.color = '#fbbf24';
        } else {
            fill.style.stroke = '#ef4444';
            valueLabel.style.color = '#ef4444';
        }
    },
    
    /**
     * ========================================
     * PART 17: SPARKLINE CHARTS
     * ========================================
     */
    initSparklines: function() {
        console.log('✓ [INIT] Sparkline Charts activated');
        
        // Add sparkline for climate volatility
        const climateSection = document.getElementById('climate-esg');
        if (!climateSection) return;
        
        const volatilityInput = document.getElementById('climate_volatility_index');
        if (!volatilityInput) return;
        
        const formGroup = volatilityInput.closest('.form-group');
        if (!formGroup) return;
        
        // Create sparkline container
        let sparklineContainer = formGroup.querySelector('.sparkline-container');
        if (!sparklineContainer) {
            sparklineContainer = document.createElement('div');
            sparklineContainer.className = 'sparkline-container';
            formGroup.appendChild(sparklineContainer);
        }
        
        // Generate sample data (in real app, this would come from API)
        const generateSparklineData = () => {
            const baseValue = parseFloat(volatilityInput.value) || 50;
            const data = [];
            for (let i = 0; i < 12; i++) {
                data.push(baseValue + (Math.random() - 0.5) * 20);
            }
            return data;
        };
        
        const drawSparkline = (data) => {
            const width = 200;
            const height = 40;
            const padding = 4;
            const max = Math.max(...data, 100);
            const min = Math.min(...data, 0);
            const range = max - min || 1;
            
            const points = data.map((value, index) => {
                const x = (index / (data.length - 1)) * (width - padding * 2) + padding;
                const y = height - ((value - min) / range) * (height - padding * 2) - padding;
                return `${x},${y}`;
            }).join(' ');
            
            sparklineContainer.innerHTML = `
                <div class="sparkline-header">
                    <span class="sparkline-label">12-Month Trend</span>
                </div>
                <svg width="${width}" height="${height}" class="sparkline-svg">
                    <polyline
                        points="${points}"
                        fill="none"
                        stroke="url(#sparklineGradient)"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                    <defs>
                        <linearGradient id="sparklineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#10b981;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                </svg>
            `;
        };
        
        // Initial draw
        drawSparkline(generateSparklineData());
        
        // Update on change
        volatilityInput.addEventListener('change', () => {
            drawSparkline(generateSparklineData());
        });
    },
    
    /**
     * ========================================
     * PART 18: EXPORT/IMPORT PRESETS
     * ========================================
     */
    initPresetExportImport: function() {
        console.log('✓ [INIT] Preset Export/Import activated');
        
        const advancedSection = document.getElementById('advanced-params');
        if (!advancedSection) return;
        
        let presetContainer = advancedSection.querySelector('.preset-buttons-container');
        if (!presetContainer) return;
        
        // Add export/import buttons
        const exportImportContainer = document.createElement('div');
        exportImportContainer.className = 'preset-export-import';
        exportImportContainer.innerHTML = `
            <button type="button" class="export-btn" id="export_preset_btn" title="Export current settings">
                <span>💾</span> Export
            </button>
            <button type="button" class="import-btn" id="import_preset_btn" title="Import saved settings">
                <span>📥</span> Import
            </button>
            <input type="file" id="import_preset_file" accept=".json" style="display: none;">
        `;
        
        presetContainer.appendChild(exportImportContainer);
        
        // Export functionality
        document.getElementById('export_preset_btn')?.addEventListener('click', () => {
            this.exportPreset();
        });
        
        // Import functionality
        document.getElementById('import_preset_btn')?.addEventListener('click', () => {
            document.getElementById('import_preset_file')?.click();
        });
        
        document.getElementById('import_preset_file')?.addEventListener('change', (e) => {
            this.importPreset(e);
        });
    },
    
    exportPreset: function() {
        const sliders = [
            'carrier_rating', 'weather_risk', 'port_risk', 'priority_level',
            'container_match', 'seller_reliability', 'buyer_reliability'
        ];
        
        const preset = {};
        sliders.forEach(id => {
            const slider = document.getElementById(id);
            if (slider) {
                preset[id] = parseFloat(slider.value);
            }
        });
        
        const dataStr = JSON.stringify(preset, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `riskcast-preset-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
        this.showNotification('Preset exported successfully', 'success');
    },
    
    importPreset: function(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const preset = JSON.parse(e.target.result);
                this.applyPreset(preset);
                this.showNotification('Preset imported successfully', 'success');
            } catch (error) {
                this.showNotification('Invalid preset file', 'error');
                console.error('Import error:', error);
            }
        };
        reader.readAsText(file);
        
        // Reset file input
        event.target.value = '';
    },
    
    /**
     * ========================================
     * PART 19: KEYBOARD SHORTCUTS
     * ========================================
     */
    initKeyboardShortcuts: function() {
        console.log('✓ [INIT] Keyboard Shortcuts activated');
        
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S: Save preset
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.exportPreset();
            }
            
            // Ctrl/Cmd + O: Import preset
            if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
                e.preventDefault();
                document.getElementById('import_preset_file')?.click();
            }
            
            // Ctrl/Cmd + 1-3: Apply presets
            if ((e.ctrlKey || e.metaKey) && ['1', '2', '3'].includes(e.key)) {
                e.preventDefault();
                const presetMap = {
                    '1': 'conservative',
                    '2': 'balanced',
                    '3': 'aggressive'
                };
                const presetName = presetMap[e.key];
                const presetBtn = document.querySelector(`[data-preset="${presetName}"]`);
                presetBtn?.click();
            }
            
            // Escape: Close tooltips/dropdowns
            if (e.key === 'Escape') {
                this.hideTooltip();
                document.querySelectorAll('.custom-dropdown.active').forEach(dd => {
                    dd.classList.remove('active');
                });
            }
        });
        
        // Show shortcuts hint
        setTimeout(() => {
            console.log('⌨️ Keyboard Shortcuts: Ctrl+S (Export), Ctrl+O (Import), Ctrl+1-3 (Presets)');
        }, 2000);
    },
    
    /**
     * ========================================
     * PART 13: UTILITY FUNCTIONS
     * ========================================
     */
    getDropdownValue: function(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return null;
        
        // Try hidden input first
        const hiddenInput = document.getElementById(dropdownId.replace('_dropdown', '_input'));
        if (hiddenInput && hiddenInput.value) {
            return hiddenInput.value;
        }
        
        // Try selected option
        const selectedOption = dropdown.querySelector('.dropdown-option.selected');
        if (selectedOption) {
            return selectedOption.getAttribute('data-value');
        }
        
        // Try standard select
        return dropdown.value || null;
    },
    
    selectDropdownOption: function(dropdownId, value) {
        const dropdown = document.getElementById(dropdownId);
        
        if (!dropdown) return;
        
        if (dropdown.tagName === 'SELECT') {
            dropdown.value = value;
            const event = new Event('change', { bubbles: true });
            dropdown.dispatchEvent(event);
        } else {
            // Custom dropdown
            const option = dropdown.querySelector(`.dropdown-option[data-value="${value}"]`);
            if (option) {
                option.click();
            }
        }
    },
    
    animateAutoFill: function(element) {
        element.style.transition = 'all 0.5s ease';
        element.style.backgroundColor = 'rgba(0, 255, 136, 0.2)';
        element.style.borderColor = '#00ffc3';
        
        setTimeout(() => {
            element.style.backgroundColor = 'rgba(0, 255, 136, 0.05)';
        }, 1000);
    }
};

/**
 * ========================================
 * GLOBAL FUNCTION: toggleSection()
 * ========================================
 * Called from HTML onclick attributes
 */
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) {
        console.warn('⚠️ Section not found:', sectionId);
        return;
    }
    
    // Use SmartInputSystem method
    SmartInputSystem.toggleSection(section);
}

/**
 * ========================================
 * AUTO-INITIALIZATION
 * ========================================
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if already initialized
    if (window.__SMART_INPUT_INITIALIZED__ && SmartInputState.initialized) {
        console.warn('[SmartInput] Already initialized, skipping auto-init...');
        return;
    }
    
    console.log('🚀 DOM Ready - Starting Smart Input Init...');
    
    setTimeout(() => {
        const LOGISTICS_DATA = window.LOGISTICS_DATA || (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null);
        if (!LOGISTICS_DATA) {
            console.error('❌ LOGISTICS_DATA not loaded! Please check logistics_data.js');
            console.warn('⚠️ Retrying in 1000ms...');
            setTimeout(() => {
                const retryData = window.LOGISTICS_DATA || (typeof LOGISTICS_DATA !== 'undefined' ? LOGISTICS_DATA : null);
                if (retryData) {
                    console.log('✅ LOGISTICS_DATA loaded, initializing...');
                    SmartInputSystem.init();
                } else {
                    console.error('❌ LOGISTICS_DATA still not available after retry');
                }
            }, 1000);
            return;
        }
        
        SmartInputSystem.init();
    }, 300);
});

/**
 * ========================================
 * SMART INPUT SYSTEM CLASS - Advanced Features
 * ========================================
 * Provides smart suggestions, compatibility scoring, and real-time feedback
 */
class SmartInputSystemClass {
    constructor() {
        this.currentSelection = {
            route: null,
            cargo: null,
            container: null,
            carrier: null
        };
    }

    // ===== CORE FUNCTIONS =====
    
    /**
     * Tính compatibility score cho container
     * Accepts HTML values and converts to logistics keys internally
     */
    getCompatibilityScore(cargoType, containerType) {
        if (!window.LOGISTICS_DATA || !window.LOGISTICS_DATA.containerCompatibility) {
            return { score: 0, status: 'unknown' };
        }
        
        // Convert HTML values to logistics keys
        const cargoKey = window.LOGISTICS_DATA.mapCargoTypeFromHTML(cargoType);
        const containerKey = window.LOGISTICS_DATA.mapContainerTypeFromHTML(containerType);
        
        const compatibility = window.LOGISTICS_DATA.containerCompatibility;
        if (!compatibility[cargoKey]) {
            return { score: 0, status: 'unknown' };
        }
        
        const score = compatibility[cargoKey][containerKey] || 0;
        
        let status = 'excellent';
        if (score < 6.0) status = 'bad';
        else if (score < 7.5) status = 'warning';
        
        return { score, status };
    }

    /**
     * Lấy thông tin carrier theo tuyến
     */
    getCarrierInfo(route, carrierName) {
        if (!window.LOGISTICS_DATA || !window.LOGISTICS_DATA.carrierRatings) {
            return null;
        }
        
        const carriers = window.LOGISTICS_DATA.carrierRatings[route] || [];
        return carriers.find(c => c.name === carrierName);
    }

    /**
     * Tính carrier rating status
     */
    getCarrierStatus(rating) {
        if (rating < 4.2) return 'bad';
        if (rating < 4.4) return 'warning';
        return 'excellent';
    }

    /**
     * Tạo smart suggestion cho container
     * Accepts HTML values and converts to logistics keys internally
     */
    generateContainerSuggestion(cargoType, currentContainer) {
        if (!window.LOGISTICS_DATA || !window.LOGISTICS_DATA.containerCompatibility) {
            return null;
        }
        
        // Convert HTML values to logistics keys
        const cargoKey = window.LOGISTICS_DATA.mapCargoTypeFromHTML(cargoType);
        const currentContainerKey = window.LOGISTICS_DATA.mapContainerTypeFromHTML(currentContainer);
        
        const compatibility = window.LOGISTICS_DATA.containerCompatibility;
        if (!compatibility[cargoKey]) return null;
        
        const scores = compatibility[cargoKey];
        const currentScore = scores[currentContainerKey] || 0;
        
        // Tìm container tốt nhất (trong logistics keys)
        let bestContainerKey = currentContainerKey;
        let bestScore = currentScore;
        
        Object.entries(scores).forEach(([containerKey, score]) => {
            if (score > bestScore) {
                bestScore = score;
                bestContainerKey = containerKey;
            }
        });
        
        // Convert back to HTML value for suggestion
        const bestContainerHTML = window.LOGISTICS_DATA.mapContainerTypeToHTML(bestContainerKey);
        
        if (bestContainerKey === currentContainerKey) {
            return {
                type: 'success',
                message: `✅ Container ${currentContainer.toUpperCase()} là lựa chọn tối ưu cho loại hàng này (${currentScore}/10)`
            };
        }
        
        return {
            type: 'suggestion',
            message: `💡 Container hiện tại: ${currentContainer.toUpperCase()} (${currentScore}/10). Gợi ý: ${bestContainerHTML.toUpperCase()} (${bestScore}/10) phù hợp hơn cho ${this.getCargoDisplayName(cargoKey)}.`,
            suggestion: bestContainerHTML, // Return HTML value for applyContainerSuggestion
            improvement: (bestScore - currentScore).toFixed(1)
        };
    }

    /**
     * Tạo smart suggestion cho carrier
     */
    generateCarrierSuggestion(route, currentCarrier) {
        if (!window.LOGISTICS_DATA || !window.LOGISTICS_DATA.carrierRatings) {
            return null;
        }
        
        const carriers = window.LOGISTICS_DATA.carrierRatings[route] || [];
        const current = carriers.find(c => c.name === currentCarrier);
        
        if (!current) return null;
        
        // Tìm carrier tốt nhất
        const best = carriers.reduce((prev, curr) => 
            curr.rating > prev.rating ? curr : prev
        );
        
        if (best.name === currentCarrier) {
            return {
                type: 'success',
                message: `✅ ${currentCarrier} là hãng tàu top-rated cho tuyến này (${current.rating}⭐, on-time ${current.ontime}%)`
            };
        }
        
        const avgOntime = carriers.reduce((sum, c) => sum + c.ontime, 0) / carriers.length;
        const ontimeDiff = current.ontime - avgOntime;
        
        if (ontimeDiff < -3) {
            return {
                type: 'warning',
                message: `⚠️ ${currentCarrier} có on-time thấp hơn trung bình tuyến ${Math.abs(ontimeDiff).toFixed(0)}%. Gợi ý: ${best.name} (${best.rating}⭐, on-time ${best.ontime}%) đáng tin hơn.`,
                suggestion: best.name,
                improvement: `+${(best.ontime - current.ontime).toFixed(0)}% on-time`
            };
        }
        
        return {
            type: 'info',
            message: `${currentCarrier} là lựa chọn tốt. Nếu muốn on-time cao hơn, thử ${best.name} (${best.rating}⭐).`,
            suggestion: best.name
        };
    }

    /**
     * Tạo tooltip cho container
     */
    getContainerTooltip(containerType, cargoType) {
        if (!window.LOGISTICS_DATA) return "Không có thông tin";
        
        // Convert HTML value to logistics key for description
        const containerKey = window.LOGISTICS_DATA.mapContainerTypeFromHTML(containerType);
        const description = window.LOGISTICS_DATA.getContainerDescription(containerKey) || "Không có thông tin";
        const score = this.getCompatibilityScore(cargoType, containerType);
        
        let scoreText = "";
        if (score.status === 'excellent') {
            scoreText = "✅ Rất phù hợp";
        } else if (score.status === 'warning') {
            scoreText = "⚠️ Phù hợp vừa phải";
        } else {
            scoreText = "❌ Không khuyến nghị";
        }
        
        return `
            <div class="smart-tooltip">
                <strong>${containerType.toUpperCase()}</strong>
                <p>${description}</p>
                <div class="tooltip-score">
                    ${scoreText} (${score.score}/10)
                </div>
            </div>
        `;
    }

    /**
     * Tạo tooltip cho carrier
     */
    getCarrierTooltip(route, carrierName) {
        const carrier = this.getCarrierInfo(route, carrierName);
        if (!carrier) return "Không có thông tin";
        
        return `
            <div class="smart-tooltip">
                <strong>${carrier.name}</strong>
                <div class="tooltip-rating">⭐ ${carrier.rating}/5.0</div>
                <div class="tooltip-ontime">📦 On-time: ${carrier.ontime}%</div>
                <div class="tooltip-price">💰 ${carrier.price}</div>
                <p class="tooltip-note">${carrier.note}</p>
            </div>
        `;
    }

    /**
     * Update UI với real-time feedback
     */
    updateUIFeedback(selection) {
        this.currentSelection = { ...this.currentSelection, ...selection };
        
        const { route, cargo, container, carrier } = this.currentSelection;
        
        // Update container feedback
        if (cargo && container) {
            this.highlightContainer(container, cargo);
            this.showContainerSuggestion(cargo, container);
        }
        
        // Update carrier feedback
        if (route && carrier) {
            this.highlightCarrier(carrier, route);
            this.showCarrierSuggestion(route, carrier);
        }
    }

    /**
     * Highlight container theo score
     */
    highlightContainer(container, cargo) {
        const score = this.getCompatibilityScore(cargo, container);
        const element = document.querySelector(`#container-${container}`);
        
        if (!element) {
            console.warn(`Container element not found: #container-${container}`);
            return;
        }
        
        // Remove all status classes
        element.classList.remove('status-excellent', 'status-warning', 'status-bad');
        element.classList.add(`status-${score.status}`);
        
        // Update score badge
        let badge = element.querySelector('.compatibility-badge');
        if (!badge) {
            // Create badge if it doesn't exist
            badge = document.createElement('span');
            badge.className = 'compatibility-badge';
            element.appendChild(badge);
        }
        
        badge.textContent = `${score.score.toFixed(1)}/10`;
        badge.className = `compatibility-badge status-${score.status}`;
        badge.style.display = 'inline-block';
        
        // Also highlight all container options in dropdown
        document.querySelectorAll(`[data-container-type="${container}"]`).forEach(el => {
            el.classList.remove('status-excellent', 'status-warning', 'status-bad');
            el.classList.add(`status-${score.status}`);
        });
    }

    /**
     * Highlight carrier theo rating
     */
    highlightCarrier(carrierName, route) {
        // Convert route if needed
        const logisticsRoute = window.LOGISTICS_DATA ? window.LOGISTICS_DATA.mapRouteFromHTML(route) : route;
        const carrier = this.getCarrierInfo(logisticsRoute, carrierName);
        if (!carrier) {
            console.warn(`Carrier not found: ${carrierName} for route: ${route}`);
            return;
        }
        
        const status = this.getCarrierStatus(carrier.rating);
        const carrierId = carrierName.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '');
        const element = document.querySelector(`#carrier-${carrierId}`);
        
        if (!element) {
            // Try to find by data attribute
            const elementByData = document.querySelector(`[data-carrier-name="${carrierName}"]`);
            if (elementByData) {
                elementByData.classList.remove('status-excellent', 'status-warning', 'status-bad');
                elementByData.classList.add(`status-${status}`);
                
                const badge = elementByData.querySelector('.rating-badge');
                if (badge) {
                    badge.textContent = `${carrier.rating.toFixed(1)}⭐`;
                    badge.className = `rating-badge status-${status}`;
                }
            }
            return;
        }
        
        element.classList.remove('status-excellent', 'status-warning', 'status-bad');
        element.classList.add(`status-${status}`);
        
        // Update rating badge
        const badge = element.querySelector('.rating-badge');
        if (badge) {
            badge.textContent = `${carrier.rating.toFixed(1)}⭐`;
            badge.className = `rating-badge status-${status}`;
        }
        
        // Also highlight all carrier options with same name
        document.querySelectorAll(`[data-carrier-name="${carrierName}"]`).forEach(el => {
            el.classList.remove('status-excellent', 'status-warning', 'status-bad');
            el.classList.add(`status-${status}`);
        });
    }

    /**
     * Hiển thị suggestion cho container
     */
    showContainerSuggestion(cargo, container) {
        const suggestion = this.generateContainerSuggestion(cargo, container);
        if (!suggestion) return;
        
        const panel = document.getElementById('container-suggestion');
        if (!panel) return;
        
        panel.className = `suggestion-panel ${suggestion.type}`;
        panel.innerHTML = `
            <div class="suggestion-content">
                ${suggestion.message}
                ${suggestion.suggestion ? `
                    <button type="button" class="suggestion-btn" data-container-value="${suggestion.suggestion}">
                        Đổi sang ${suggestion.suggestion.toUpperCase()}
                    </button>
                ` : ''}
            </div>
        `;
        panel.style.display = 'block';
        
        // Add event listener to button (prevent form submit)
        if (suggestion.suggestion) {
            const btn = panel.querySelector('.suggestion-btn');
            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    console.log('[Smart Input] Container suggestion button clicked');
                    const result = this.applyContainerSuggestion(suggestion.suggestion);
                    return false;
                }, true); // Use capture phase to prevent other handlers
            }
        }
    }

    /**
     * Hiển thị suggestion cho carrier
     */
    showCarrierSuggestion(route, carrier) {
        const suggestion = this.generateCarrierSuggestion(route, carrier);
        if (!suggestion) return;
        
        const panel = document.getElementById('carrier-suggestion');
        if (!panel) return;
        
        panel.className = `suggestion-panel ${suggestion.type}`;
        panel.innerHTML = `
            <div class="suggestion-content">
                ${suggestion.message}
                ${suggestion.suggestion ? `
                    <button type="button" class="suggestion-btn" data-carrier-value="${suggestion.suggestion}">
                        Đổi sang ${suggestion.suggestion}
                    </button>
                ` : ''}
            </div>
        `;
        panel.style.display = 'block';
        
        // Add event listener to button (prevent form submit)
        if (suggestion.suggestion) {
            const btn = panel.querySelector('.suggestion-btn');
            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    console.log('[Smart Input] Carrier suggestion button clicked');
                    const result = this.applyCarrierSuggestion(suggestion.suggestion);
                    return false;
                }, true); // Use capture phase to prevent other handlers
            }
        }
    }

    /**
     * Apply suggestion (để gọi từ button)
     */
    applyContainerSuggestion(containerType) {
        console.log('[Smart Input] Applying container suggestion:', containerType);
        
        // Normalize container type to lowercase with underscore (e.g., "40ft_standard")
        const normalizedType = containerType.toLowerCase().replace(/\s+/g, '_');
        console.log('[Smart Input] Normalized container type:', normalizedType);
        
        // Find the option in dropdown
        const dropdown = document.getElementById('container_dropdown');
        if (!dropdown) {
            console.warn('[Smart Input] Container dropdown not found');
            return false; // Prevent form submission
        }
        
        const options = dropdown.querySelectorAll('.dropdown-option');
        let foundIndex = -1;
        let foundValue = null;
        
        // Search for matching option (case-insensitive)
        options.forEach((option, index) => {
            const value = option.getAttribute('data-value');
            if (value && value.toLowerCase() === normalizedType) {
                foundIndex = index;
                foundValue = value;
            }
        });
        
        if (foundIndex >= 0 && foundValue) {
            console.log('[Smart Input] Found container option at index:', foundIndex, 'value:', foundValue);
            
            // Close dropdown if open
            const dropdownState = window.dropdownState?.['container_dropdown'];
            if (dropdownState && dropdownState.isOpen) {
                dropdown.classList.remove('open');
                dropdownState.isOpen = false;
            }
            
            // Use selectOption function if available
            if (typeof window.selectOption === 'function') {
                try {
                    window.selectOption('container_dropdown', foundValue, foundIndex);
                    console.log('[Smart Input] Container selected via selectOption');
                } catch (e) {
                    console.error('[Smart Input] Error calling selectOption:', e);
                    // Fallback: manually trigger selection
                    const option = options[foundIndex];
                    if (option) {
                        option.click();
                        console.log('[Smart Input] Container selected via click (fallback)');
                    }
                }
            } else {
                // Fallback: manually trigger selection
                const option = options[foundIndex];
                if (option) {
                    option.click();
                    console.log('[Smart Input] Container selected via click');
                }
            }
            
            // Update smart input feedback
            setTimeout(() => {
                if (window.updateSmartInputFeedback) {
                    window.updateSmartInputFeedback();
                }
            }, 200);
            
            return false; // Prevent form submission
        } else {
            console.warn('[Smart Input] Container option not found:', normalizedType, 'Available options:', Array.from(options).map(o => o.getAttribute('data-value')));
            return false; // Prevent form submission
        }
    }

    applyCarrierSuggestion(carrierName) {
        console.log('[Smart Input] Applying carrier suggestion:', carrierName);
        
        // Find the option in dropdown
        const dropdown = document.getElementById('carrier_dropdown');
        if (!dropdown) {
            console.warn('[Smart Input] Carrier dropdown not found');
            return false; // Prevent form submission
        }
        
        const options = dropdown.querySelectorAll('.dropdown-option');
        let foundIndex = -1;
        let foundValue = null;
        
        // Search for matching option (exact match)
        options.forEach((option, index) => {
            const value = option.getAttribute('data-value');
            if (value === carrierName) {
                foundIndex = index;
                foundValue = value;
            }
        });
        
        if (foundIndex >= 0 && foundValue) {
            console.log('[Smart Input] Found carrier option at index:', foundIndex, 'value:', foundValue);
            
            // Close dropdown if open
            const dropdownState = window.dropdownState?.['carrier_dropdown'];
            if (dropdownState && dropdownState.isOpen) {
                dropdown.classList.remove('open');
                dropdownState.isOpen = false;
            }
            
            // Use selectOption function if available
            if (typeof window.selectOption === 'function') {
                try {
                    window.selectOption('carrier_dropdown', foundValue, foundIndex);
                    console.log('[Smart Input] Carrier selected via selectOption');
                } catch (e) {
                    console.error('[Smart Input] Error calling selectOption:', e);
                    // Fallback: manually trigger selection
                    const option = options[foundIndex];
                    if (option) {
                        option.click();
                        console.log('[Smart Input] Carrier selected via click (fallback)');
                    }
                }
            } else {
                // Fallback: manually trigger selection
                const option = options[foundIndex];
                if (option) {
                    option.click();
                    console.log('[Smart Input] Carrier selected via click');
                }
            }
            
            // Update smart input feedback
            setTimeout(() => {
                if (window.updateSmartInputFeedback) {
                    window.updateSmartInputFeedback();
                }
            }, 200);
            
            return false; // Prevent form submission
        } else {
            console.warn('[Smart Input] Carrier option not found:', carrierName, 'Available options:', Array.from(options).map(o => o.getAttribute('data-value')));
            return false; // Prevent form submission
        }
    }

    /**
     * Helper: Get cargo display name
     * Accepts both HTML values and logistics keys
     */
    getCargoDisplayName(cargoType) {
        // Convert HTML value to logistics key if needed
        let cargoKey = cargoType;
        if (window.LOGISTICS_DATA && window.LOGISTICS_DATA.mapCargoTypeFromHTML) {
            const mapped = window.LOGISTICS_DATA.mapCargoTypeFromHTML(cargoType);
            // If mapping changed it, use the mapped value
            if (mapped !== cargoType) {
                cargoKey = mapped;
            }
        }
        
        const names = {
            'thong_thuong': 'hàng thông thường',
            'dien_tu': 'hàng điện tử',
            'thuc_pham_do_uong': 'thực phẩm',
            'may_mac_det_may': 'dệt may',
            'nong_san': 'nông sản',
            'hang_lanh_dong_lanh': 'hàng lạnh',
            'hoa_chat': 'hóa chất',
            'may_moc_thiet_bi': 'máy móc',
            'hang_de_vo': 'hàng dễ vỡ',
            'linh_kien_o_to': 'linh kiện ô tô',
            'hang_nguy_hiem_dg': 'hàng nguy hiểm',
            'duoc_pham': 'dược phẩm'
        };
        return names[cargoKey] || cargoType;
    }

    /**
     * Init tooltips cho tất cả elements
     */
    initTooltips() {
        // Use event delegation for dynamic elements
        const containerDropdown = document.getElementById('container_dropdown');
        const carrierDropdown = document.getElementById('carrier_dropdown');
        
        // Container tooltips with event delegation
        if (containerDropdown) {
            containerDropdown.addEventListener('mouseenter', (e) => {
                const option = e.target.closest('[data-container-type]');
                if (option) {
                    const containerType = option.dataset.containerType;
                    const cargoType = this.currentSelection.cargo;
                    if (cargoType) {
                        this.showTooltip(option, this.getContainerTooltip(containerType, cargoType));
                    }
                }
            }, true);
            
            containerDropdown.addEventListener('mouseleave', (e) => {
                if (!e.target.closest('[data-container-type]')) {
                    this.hideTooltip();
                }
            }, true);
        }
        
        // Carrier tooltips with event delegation
        if (carrierDropdown) {
            carrierDropdown.addEventListener('mouseenter', (e) => {
                const option = e.target.closest('[data-carrier-name]');
                if (option) {
                    const carrierName = option.dataset.carrierName;
                    const route = this.currentSelection.route;
                    if (route) {
                        this.showTooltip(option, this.getCarrierTooltip(route, carrierName));
                    }
                }
            }, true);
            
            carrierDropdown.addEventListener('mouseleave', (e) => {
                if (!e.target.closest('[data-carrier-name]')) {
                    this.hideTooltip();
                }
            }, true);
        }
        
        // Also add direct listeners for static elements
        document.querySelectorAll('[data-container-type]').forEach(el => {
            el.addEventListener('mouseenter', (e) => {
                const containerType = e.currentTarget.dataset.containerType;
                const cargoType = this.currentSelection.cargo;
                if (cargoType) {
                    this.showTooltip(e.currentTarget, this.getContainerTooltip(containerType, cargoType));
                }
            });
            el.addEventListener('mouseleave', () => this.hideTooltip());
        });
        
        document.querySelectorAll('[data-carrier-name]').forEach(el => {
            el.addEventListener('mouseenter', (e) => {
                const carrierName = e.currentTarget.dataset.carrierName;
                const route = this.currentSelection.route;
                if (route) {
                    this.showTooltip(e.currentTarget, this.getCarrierTooltip(route, carrierName));
                }
            });
            el.addEventListener('mouseleave', () => this.hideTooltip());
        });
    }

    /**
     * Show tooltip at element position
     */
    showTooltip(element, content) {
        let tooltip = document.getElementById('smart-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'smart-tooltip';
            tooltip.style.cssText = `
                position: absolute;
                background: rgba(10, 15, 20, 0.98);
                border: 2px solid #10b981;
                border-radius: 12px;
                padding: 12px;
                max-width: 300px;
                z-index: 10000;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
                color: #ffffff;
                font-size: 13px;
                display: none;
            `;
            document.body.appendChild(tooltip);
        }
        
        tooltip.innerHTML = content;
        tooltip.style.display = 'block';
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = `${rect.left}px`;
        tooltip.style.top = `${rect.bottom + 10}px`;
    }

    /**
     * Hide tooltip
     */
    hideTooltip() {
        const tooltip = document.getElementById('smart-tooltip');
        if (tooltip) tooltip.style.display = 'none';
    }
}

// Initialize global instance
const smartInputClass = new SmartInputSystemClass();

// Auto-init on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        smartInputClass.initTooltips();
    });
} else {
    smartInputClass.initTooltips();
}

// ============================================
// AUTO-CLOSE DROPDOWNS WHEN CLICKING OUTSIDE
// ============================================
document.addEventListener("click", (e) => {
    // Close all custom-dropdowns with .open or .active class
    document.querySelectorAll(".custom-dropdown.open, .custom-dropdown.active").forEach(dropdown => {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove("open", "active");
        }
    });
    
    // Close all custom-selects with .open class (if using custom-select class)
    document.querySelectorAll(".custom-select.open").forEach(sel => {
        if (!sel.contains(e.target)) {
            sel.classList.remove("open");
        }
    });
});

// Export
if (typeof window !== 'undefined') {
    window.SmartInputSystem = SmartInputSystem;
    window.SmartInputSystemClass = SmartInputSystemClass;
    window.smartInputClass = smartInputClass;
    window.smartInput = smartInputClass; // Alias for compatibility
    // Ensure toggleSection is available globally (override any previous definition)
    window.toggleSection = toggleSection;
    console.log('✅ SmartInputSystem v13.0 ULTIMATE loaded successfully');
    console.log('✅ SmartInputSystemClass loaded with advanced features');
    console.log('✅ toggleSection function available globally');
    console.log('✅ Auto-close dropdowns on outside click enabled');
}