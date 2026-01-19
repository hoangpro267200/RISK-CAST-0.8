
(function() {
    'use strict';

    // Section configuration
    const sections = [
        {
            id: 'shipping-info',
            name: 'Transport Setup',
            fields: ['route', 'transport_mode', 'pol', 'pod', 'distance', 'transit_time', 'carrier', 'cargo_type', 'container', 'incoterm', 'packaging', 'priority']
        },
        {
            id: 'cargo-details',
            name: 'Cargo & Packing',
            fields: ['etd', 'eta', 'cargo_value', 'packages']
        },
        {
            id: 'seller-info',
            name: 'Seller Information',
            fields: ['seller_name', 'seller_country', 'seller_email', 'seller_phone', 'seller_address', 'seller_pic']
        },
        {
            id: 'buyer-info',
            name: 'Buyer Information',
            fields: ['buyer_name', 'buyer_country', 'buyer_email', 'buyer_phone', 'buyer_address', 'buyer_pic']
        },
        {
            id: 'algorithm-modules',
            name: 'Algorithm Modules',
            fields: ['use_fuzzy', 'use_forecast', 'use_mc', 'use_var']
        },
        {
            id: 'summaryOverviewSection',
            name: 'Summary Overview',
            fields: [] // Read-only section, no fields to track
        }
    ];

    /**
     * Initialize Enterprise Input System
     */
    function initEnterpriseInput() {
        console.log('✓ Enterprise Input Layout initialized');
        
        setupSidebarNavigation();
        setupIntersectionObserver();
        setupCompletionTracking();
        wrapSectionsInCards();
        
        // Initial update
        updateCompletionStatus();
    }

    /**
     * Setup sidebar navigation
     */
    function setupSidebarNavigation() {
        const navItems = document.querySelectorAll('.sidebar-nav-item');
        
        navItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const sectionId = this.getAttribute('data-section');
                const section = document.getElementById(sectionId);
                
                if (section) {
                    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    
                    // Update active state
                    navItems.forEach(nav => nav.classList.remove('active'));
                    this.classList.add('active');
                }
            });
        });
    }

    /**
     * Setup IntersectionObserver for active section highlighting
     */
    function setupIntersectionObserver() {
        const observerOptions = {
            root: null,
            rootMargin: '-20% 0px -60% 0px',
            threshold: 0
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const sectionId = entry.target.id;
                const navItem = document.querySelector(`.sidebar-nav-item[data-section="${sectionId}"]`);
                const sectionCard = entry.target.closest('.enterprise-section-card');
                
                if (entry.isIntersecting) {
                    // Update sidebar
                    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    if (navItem) navItem.classList.add('active');
                    
                    // Update section card
                    if (sectionCard) {
                        document.querySelectorAll('.enterprise-section-card').forEach(card => {
                            card.classList.remove('active');
                        });
                        sectionCard.classList.add('active');
                    }
                }
            });
        }, observerOptions);

        // Observe all sections
        sections.forEach(section => {
            const element = document.getElementById(section.id);
            if (element) {
                observer.observe(element);
            }
        });
    }

    /**
     * Wrap sections in enterprise cards
     */
    function wrapSectionsInCards() {
        sections.forEach(section => {
            const sectionEl = document.getElementById(section.id);
            if (!sectionEl) return;

            // Check if already wrapped
            if (sectionEl.classList.contains('already-wrapped')) return;
            
            // Create card wrapper
            const card = document.createElement('div');
            card.className = 'enterprise-section-card';
            
            // Create card header
            const header = document.createElement('div');
            header.className = 'section-card-header';
            
            const titleEl = sectionEl.querySelector('.section-header h2');
            const subtitleEl = sectionEl.querySelector('.section-header p');
            
            if (titleEl) {
                header.innerHTML = `
                    <div class="section-card-title">${titleEl.textContent}</div>
                    ${subtitleEl ? `<div class="section-card-subtitle">${subtitleEl.textContent}</div>` : ''}
                `;
            }
            
            // Move content into card
            const sectionContent = sectionEl.querySelector('.form-grid, .form-group, .packing-list-section');
            if (sectionContent || sectionEl.children.length > 1) {
                card.appendChild(header);
                
                // Move all children except header into card (DO NOT CLONE - move directly to avoid duplicate dropdowns)
                const childrenToMove = Array.from(sectionEl.children).filter(child => !child.classList.contains('section-header'));
                childrenToMove.forEach(child => {
                    card.appendChild(child); // Move directly, don't clone
                });
                
                // Clear and replace
                sectionEl.innerHTML = '';
                sectionEl.appendChild(card);
                sectionEl.classList.add('already-wrapped');
            }
        });
    }

    /**
     * Calculate completion percentage for a section
     */
    function calculateSectionCompletion(sectionId) {
        const section = sections.find(s => s.id === sectionId);
        if (!section) return 0;

        let filledCount = 0;
        const totalFields = section.fields.length;

        section.fields.forEach(fieldName => {
            let field = null;
            
            // Try different selectors
            field = document.getElementById(fieldName) || 
                    document.getElementById(`${fieldName}_input`) ||
                    document.getElementById(`${fieldName}_dropdown`) ||
                    document.querySelector(`[name="${fieldName}"]`);
            
            if (field) {
                let value = '';
                
                // Handle different input types
                if (field.type === 'checkbox') {
                    value = field.checked ? 'checked' : '';
                } else if (field.tagName === 'SELECT') {
                    value = field.value;
                } else if (field.classList && field.classList.contains('custom-dropdown')) {
                    const dropdownValue = field.querySelector('.dropdown-value');
                    value = dropdownValue && !dropdownValue.classList.contains('placeholder') ? dropdownValue.textContent : '';
                } else {
                    value = field.value || field.textContent;
                }
                
                if (value && value.trim() !== '' && value !== 'Chọn' && value !== 'Select') {
                    filledCount++;
                }
            }
        });

        return Math.round((filledCount / totalFields) * 100);
    }

    /**
     * Update completion status for all sections
     */
    function updateCompletionStatus() {
        sections.forEach(section => {
            const percent = calculateSectionCompletion(section.id);
            
            // Update sidebar
            const navItem = document.querySelector(`.sidebar-nav-item[data-section="${section.id}"]`);
            if (navItem) {
                if (percent === 100) {
                    navItem.classList.add('completed');
                } else {
                    navItem.classList.remove('completed');
                }
            }
            
            // Update AI panel
            const aiItem = document.querySelector(`.ai-section-item[data-section="${section.id}"]`);
            if (aiItem) {
                const percentEl = aiItem.querySelector('.ai-section-percent');
                const progressFill = aiItem.querySelector('.ai-progress-fill');
                const badge = aiItem.querySelector('.completion-badge');
                
                if (percentEl) percentEl.textContent = `${percent}%`;
                if (progressFill) progressFill.style.width = `${percent}%`;
                
                if (percent === 100) {
                    aiItem.classList.add('completed');
                    if (badge) badge.style.display = 'inline-flex';
                } else {
                    aiItem.classList.remove('completed');
                    if (badge) badge.style.display = 'none';
                }
            }
        });
    }

    /**
     * Setup completion tracking with field listeners
     */
    function setupCompletionTracking() {
        // Track all form fields
        const form = document.getElementById('risk_form');
        if (!form) return;

        // Debounce function
        let updateTimeout;
        function debouncedUpdate() {
            clearTimeout(updateTimeout);
            updateTimeout = setTimeout(updateCompletionStatus, 200);
        }

        // Listen to all form changes
        form.addEventListener('input', debouncedUpdate);
        form.addEventListener('change', debouncedUpdate);
        form.addEventListener('click', function(e) {
            if (e.target.type === 'checkbox' || e.target.classList.contains('dropdown-option')) {
                debouncedUpdate();
            }
        });

        // Also listen for custom dropdown changes (they use different events)
        document.addEventListener('dropdownChange', debouncedUpdate);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEnterpriseInput);
    } else {
        initEnterpriseInput();
    }

    // Re-initialize after a delay to catch dynamically loaded content
    setTimeout(initEnterpriseInput, 1000);

    /**
     * Setup Algorithm Module Toggles
     * Supports both old toggle-switch-enterprise and new toggle-cont
     */
    function setupAlgorithmToggles() {
        document.querySelectorAll('.algorithm-module-card').forEach(card => {
            const checkbox = card.querySelector('input[type="checkbox"]');
            if (!checkbox) return;
            
            const moduleName = card.getAttribute('data-module');
            if (!moduleName) return;
            
            // Map module names to checkbox IDs
            const moduleToIdMap = {
                'fuzzy': 'use_fuzzy',
                'arima': 'use_forecast',
                'monte-carlo': 'use_mc',
                'var': 'use_var'
            };
            
            const checkboxId = moduleToIdMap[moduleName] || checkbox.id;
            
            // Check if toggle is new style (toggle-cont) or old style (toggle-switch-enterprise)
            const toggleCont = card.querySelector('.toggle-cont');
            const toggleSwitch = card.querySelector('.toggle-switch-enterprise');
            
            // Auto-check on load: Default to checked if not set in state (auto bật sẵn)
            // Check localStorage/state for saved value
            let shouldBeChecked = checkbox.checked; // Default from HTML (should be checked)
            
            try {
                // Map module names to state keys
                const moduleKeyMap = {
                    'fuzzy': ['fuzzy', 'use_fuzzy'],
                    'arima': ['arima', 'use_forecast'],
                    'monte-carlo': ['monte_carlo', 'use_mc'],
                    'var': ['var', 'use_var']
                };
                
                const stateKeys = moduleKeyMap[moduleName] || [moduleName];
                
                // Try to get from RISKCAST_STATE
                if (typeof window.RISKCAST_STATE !== 'undefined' && window.RISKCAST_STATE.modules) {
                    let foundValue = undefined;
                    
                    // Try all possible key names
                    for (const key of stateKeys) {
                        if (window.RISKCAST_STATE.modules[key] !== undefined) {
                            foundValue = window.RISKCAST_STATE.modules[key] === true;
                            break;
                        }
                    }
                    
                    if (foundValue !== undefined) {
                        shouldBeChecked = foundValue;
                    } else {
                        // Auto-enable if not set (auto bật sẵn)
                        shouldBeChecked = true;
                        // Set in state for all key variations
                        stateKeys.forEach(key => {
                            if (window.RISKCAST_STATE.modules) {
                                window.RISKCAST_STATE.modules[key] = true;
                            }
                        });
                        // Save to localStorage
                        try {
                            localStorage.setItem('RISKCAST_STATE', JSON.stringify(window.RISKCAST_STATE));
                        } catch (e) {
                            console.warn('[Algorithm Toggles] Failed to save state:', e);
                        }
                    }
                } else {
                    // No state found, default to checked (auto bật sẵn)
                    shouldBeChecked = true;
                    // Initialize state
                    if (typeof window.RISKCAST_STATE === 'undefined') {
                        window.RISKCAST_STATE = { modules: {} };
                    }
                    if (!window.RISKCAST_STATE.modules) {
                        window.RISKCAST_STATE.modules = {};
                    }
                    stateKeys.forEach(key => {
                        window.RISKCAST_STATE.modules[key] = true;
                    });
                    try {
                        localStorage.setItem('RISKCAST_STATE', JSON.stringify(window.RISKCAST_STATE));
                    } catch (e) {
                        console.warn('[Algorithm Toggles] Failed to save state:', e);
                    }
                }
            } catch (e) {
                console.warn('[Algorithm Toggles] Error reading state:', e);
                shouldBeChecked = true; // Default to checked (auto bật sẵn)
            }
            
            // Set checkbox state
            checkbox.checked = shouldBeChecked;
            
            // Update UI based on toggle type
            if (toggleCont) {
                // New toggle style - CSS handles visual state via :has() selector
                // Just ensure checkbox is checked
                if (shouldBeChecked) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            } else if (toggleSwitch) {
                // Old toggle style
                if (shouldBeChecked) {
                    toggleSwitch.classList.add('active');
                    card.classList.add('active');
                } else {
                    toggleSwitch.classList.remove('active');
                    card.classList.remove('active');
                }
            }
            
            // Handle click on toggle (works for both styles)
            const toggleElement = toggleCont || toggleSwitch;
            if (toggleElement) {
                toggleElement.addEventListener('click', function(e) {
                    e.preventDefault();
                    checkbox.checked = !checkbox.checked;
                    
                    // Update state
                    const moduleKey = moduleName === 'monte-carlo' ? 'monte_carlo' : moduleName;
                    if (typeof window.RISKCAST_STATE !== 'undefined' && window.RISKCAST_STATE.modules) {
                        window.RISKCAST_STATE.modules[moduleKey] = checkbox.checked;
                        // Save to localStorage
                        try {
                            localStorage.setItem('RISKCAST_STATE', JSON.stringify(window.RISKCAST_STATE));
                        } catch (e) {
                            console.warn('[Algorithm Toggles] Failed to save state:', e);
                        }
                    }
                    
                    // Update UI
                    if (checkbox.checked) {
                        card.classList.add('active');
                        if (toggleSwitch) toggleSwitch.classList.add('active');
                    } else {
                        card.classList.remove('active');
                        if (toggleSwitch) toggleSwitch.classList.remove('active');
                    }
                    
                    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                });
            }
            
            // Handle checkbox change (for programmatic changes like auto-fill)
            checkbox.addEventListener('change', function() {
                const moduleKey = moduleName === 'monte-carlo' ? 'monte_carlo' : moduleName;
                
                // Update state
                if (typeof window.RISKCAST_STATE !== 'undefined' && window.RISKCAST_STATE.modules) {
                    window.RISKCAST_STATE.modules[moduleKey] = this.checked;
                    try {
                        localStorage.setItem('RISKCAST_STATE', JSON.stringify(window.RISKCAST_STATE));
                    } catch (e) {
                        console.warn('[Algorithm Toggles] Failed to save state:', e);
                    }
                }
                
                // Update UI
                if (this.checked) {
                    card.classList.add('active');
                    if (toggleSwitch) toggleSwitch.classList.add('active');
                } else {
                    card.classList.remove('active');
                    if (toggleSwitch) toggleSwitch.classList.remove('active');
                }
            });
        });
    }

    // Setup algorithm toggles - run immediately and also after delay to catch late DOM updates
    setupAlgorithmToggles();
    setTimeout(setupAlgorithmToggles, 500);
    setTimeout(setupAlgorithmToggles, 1500);
    
    // Also setup when state is loaded (for auto-fill scenarios)
    if (typeof window.addEventListener !== 'undefined') {
        window.addEventListener('RISKCAST_STATE_LOADED', function() {
            setTimeout(setupAlgorithmToggles, 100);
        });
    }

    /**
     * Update Climate Risk Panel when month is selected
     */
    function setupClimatePanel() {
        const monthInput = document.getElementById('shipment-month');
        const climatePanel = document.getElementById('climate-risk-panel');
        
        if (monthInput && climatePanel) {
            monthInput.addEventListener('change', function() {
                if (this.value) {
                    climatePanel.style.display = 'block';
                    // Update climate data will be handled by existing ai_adviser.js
                }
            });
        }
        
        // Also listen to the display input
        const monthDisplay = document.getElementById('shipment-month-display');
        if (monthDisplay) {
            monthDisplay.addEventListener('click', function() {
                setTimeout(() => {
                    const monthInput = document.getElementById('shipment-month');
                    if (monthInput && monthInput.value && climatePanel) {
                        climatePanel.style.display = 'block';
                    }
                }, 100);
            });
        }
    }

    // Setup climate panel
    setTimeout(setupClimatePanel, 1500);

})();

/**
 * Toggle Climate Risk Panel
 */
function toggleClimate() {
    const panel = document.getElementById('climate-panel');
    if (panel) {
        panel.classList.toggle('expanded');
        const body = panel.querySelector('#climate-body');
        const arrow = panel.querySelector('#climate-arrow');
        if (body) {
            body.classList.toggle('hidden');
            // Update max-height for smooth animation
            if (body.classList.contains('hidden')) {
                body.style.maxHeight = '0';
            } else {
                body.style.maxHeight = body.scrollHeight + 'px';
            }
        }
        if (arrow) {
            // Arrow rotation is handled by CSS class 'expanded'
        }
    }
}

function toggleClimatePanel() {
    toggleClimate(); // Alias for backward compatibility
}

// Make it globally available
window.toggleClimate = toggleClimate;
window.toggleClimatePanel = toggleClimatePanel;

/**
 * Toggle Left Sidebar (Navigation)
 */
function toggleLeftSidebar() {
    const sidebar = document.querySelector('.enterprise-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        // Save state to localStorage
        localStorage.setItem('leftSidebarCollapsed', sidebar.classList.contains('collapsed'));
    }
}

/**
 * Toggle Right Sidebar (AI Panel) - Legacy function
 */
function toggleRightSidebar() {
    toggleAIPanel(); // Use new premium toggle function
}

/**
 * Premium AI Panel Toggle with Transition Lock
 * Implements smooth collapse/expand with ghost spacing, fade, and slide animations
 */
let isAIPanelTransitioning = false;

function toggleAIPanel() {
    // Prevent multi-click glitches with transition lock
    if (isAIPanelTransitioning) {
        return;
    }
    
    const panel = document.getElementById('aiSmartPanel');
    const body = document.body;
    
    if (!panel) {
        console.warn('AI Smart Panel not found');
        return;
    }
    
    // Set transition lock
    isAIPanelTransitioning = true;
    
    // Toggle panel state
    const isCurrentlyHidden = body.classList.contains('body--ai-panel-hidden');
    
    if (isCurrentlyHidden) {
        // Show panel
        body.classList.remove('body--ai-panel-hidden');
        panel.classList.remove('collapsed');
    } else {
        // Hide panel
        body.classList.add('body--ai-panel-hidden');
        panel.classList.add('collapsed');
    }
    
    // Save state to localStorage
    localStorage.setItem('aiPanelHidden', !isCurrentlyHidden);
    
    // Release lock after transition completes (600ms for smooth animation)
    setTimeout(() => {
        isAIPanelTransitioning = false;
    }, 600);
}

// Restore sidebar states on page load
document.addEventListener('DOMContentLoaded', function() {
    // Restore left sidebar state
    const leftCollapsed = localStorage.getItem('leftSidebarCollapsed') === 'true';
    const leftSidebar = document.querySelector('.enterprise-sidebar');
    if (leftSidebar && leftCollapsed) {
        leftSidebar.classList.add('collapsed');
    }
    const rightCollapsed = localStorage.getItem('rightSidebarCollapsed') === 'true';
    const rightSidebar = document.querySelector('.enterprise-ai-panel');
    if (rightSidebar && rightCollapsed) {
        rightSidebar.classList.add('collapsed');
    }
    
    // Restore AI panel state (new premium system)
    const aiPanelHidden = localStorage.getItem('aiPanelHidden') === 'true';
    const aiPanel = document.getElementById('aiSmartPanel');
    if (aiPanel && aiPanelHidden) {
        document.body.classList.add('body--ai-panel-hidden');
        aiPanel.classList.add('collapsed');
    }
});

// Make toggle functions globally available
window.toggleLeftSidebar = toggleLeftSidebar;
window.toggleRightSidebar = toggleRightSidebar;
window.toggleAIPanel = toggleAIPanel;

