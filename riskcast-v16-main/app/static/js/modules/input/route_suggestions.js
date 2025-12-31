
import { $id, qsa, qs, on, addClass, removeClass } from '../../core/dom.js';
import { SmartInputState } from './state_management.js';

export function initRouteBasedSuggestions() {
    
    const routeDropdown = $id('route_dropdown');
    if (!routeDropdown) {
        return;
    }
    
    // Listen for option selection in route dropdown
    const routeOptions = qsa('.dropdown-option', routeDropdown);
    routeOptions.forEach(option => {
        on(option, 'click', (e) => {
            e.stopPropagation();
            const routeKey = option.getAttribute('data-value');
            if (routeKey) {
                setTimeout(() => {
                    handleRouteSelection(routeKey);
                }, 200);
            }
        });
    });
    
    // Check if route is already selected on page load
    setTimeout(() => {
        const selectedRoute = getDropdownValue('route_dropdown');
        if (selectedRoute) {
            handleRouteSelection(selectedRoute);
        }
    }, 500);
    
    // Listen for manual selection changes via mutation observer
    const observer = new MutationObserver(() => {
        const selectedOption = qs('.dropdown-option.selected', routeDropdown);
        if (selectedOption) {
            const routeKey = selectedOption.getAttribute('data-value');
            if (routeKey && routeKey !== SmartInputState.selectedRoute) {
                handleRouteSelection(routeKey);
            }
        }
    });
    
    observer.observe(routeDropdown, { 
        childList: true, 
        subtree: true, 
        attributes: true,
        attributeFilter: ['class']
    });
}

function handleRouteSelection(routeKey) {
    if (!routeKey) {
        const routeValue = getDropdownValue('route_dropdown');
        if (!routeValue) return;
        routeKey = routeValue;
    }
    
    SmartInputState.selectedRoute = routeKey;
    
    // Populate Transport Modes with error handling
    try {
        populateTransportModes(routeKey);
    } catch (error) {
        console.error('❌ Error in populateTransportModes:', error);
        console.error('Stack:', error.stack);
    }
    
    // Reset dependent fields
    resetTransportDependentFields();
}

function populateTransportModes(routeKey) {
    const LOGISTICS_DATA = SmartInputState.getLogisticsData();
    if (!LOGISTICS_DATA) {
        console.error('❌ LOGISTICS_DATA not available in populateTransportModes');
        setTimeout(() => populateTransportModes(routeKey), 500);
        return;
    }
    
    // Map HTML route value to logistics key if needed
    const logisticsRouteKey = LOGISTICS_DATA.mapRouteFromHTML ? LOGISTICS_DATA.mapRouteFromHTML(routeKey) : routeKey;
    
    const route = LOGISTICS_DATA.getRoute(logisticsRouteKey);
    
    if (!route) {
        console.error(`❌ Route "${logisticsRouteKey}" not found in LOGISTICS_DATA`);
        return;
    }
    
    const transportModes = route.transport_modes;
    
    if (!transportModes || transportModes.length === 0) {
        return;
    }
    
    
    const transportDropdown = $id('transport_mode_dropdown');
    const transportMenu = $id('transport_mode_menu') || qs('.dropdown-menu', transportDropdown);
    const transportTrigger = qs('.dropdown-trigger .dropdown-value', transportDropdown);
    
    if (!transportMenu) {
        console.error('❌ Transport mode menu not found');
        return;
    }
    
    
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
            addClass(option, 'recommended');
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
        const riskLabel = LOGISTICS_DATA.getRiskLabel(mode.risk_level);
        optionText += ` [RỦI RO: ${riskLabel.toUpperCase()}]`;
        
        option.innerHTML = `
            <div class="transport-option-content">
                <div class="transport-label">${optionText}</div>
                <div class="transport-description">${mode.description || ''}</div>
            </div>
        `;
        
        // Add click handler
        on(option, 'click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            
            
            // Mark as selected
            qsa('.dropdown-option', transportMenu).forEach(opt => {
                removeClass(opt, 'selected');
            });
            addClass(option, 'selected');
            
            // Update dropdown display value
            if (transportTrigger) {
                transportTrigger.textContent = mode.label || mode.value;
                removeClass(transportTrigger, 'placeholder');
            }
            
            // Get full mode object
            const fullMode = route.transport_modes.find(m => m.value === mode.value);
            
            // Select the mode (this would call another function)
            if (typeof window !== 'undefined' && window.selectTransportMode) {
                window.selectTransportMode(fullMode || mode, routeKey);
            }
            
            // Close dropdown
            if (transportDropdown) {
                removeClass(transportDropdown, 'active');
            }
        });
        
        transportMenu.appendChild(option);
    });
    
}

function resetTransportDependentFields() {
    // Reset transport mode
    const transportDropdown = $id('transport_mode_dropdown');
    const transportValue = qs('.dropdown-value', transportDropdown);
    if (transportValue) {
        transportValue.textContent = 'Chọn phương thức vận tải';
        addClass(transportValue, 'placeholder');
    }
    
    // Reset POL/POD
    const polDropdown = $id('pol_dropdown');
    const podDropdown = $id('pod_dropdown');
    
    if (polDropdown) {
        const polValue = qs('.dropdown-value', polDropdown);
        if (polValue) {
            polValue.textContent = 'Chọn phương thức trước';
            addClass(polValue, 'placeholder');
        }
    }
    
    if (podDropdown) {
        const podValue = qs('.dropdown-value', podDropdown);
        if (podValue) {
            podValue.textContent = 'Chọn phương thức trước';
            addClass(podValue, 'placeholder');
        }
    }
    
    // Reset distance and transit time
    const distanceInput = $id('distance');
    const transitDisplay = $id('transit_time_display');
    
    if (distanceInput) distanceInput.value = '';
    if (transitDisplay) transitDisplay.value = '';
}

function getDropdownValue(dropdownId) {
    const dropdown = $id(dropdownId);
    if (!dropdown) return null;
    
    // Try hidden input first
    const hiddenInput = $id(dropdownId.replace('_dropdown', '_input'));
    if (hiddenInput && hiddenInput.value) {
        return hiddenInput.value;
    }
    
    // Try selected option
    const selectedOption = qs('.dropdown-option.selected', dropdown);
    if (selectedOption) {
        return selectedOption.getAttribute('data-value');
    }
    
    // Try standard select
    return dropdown.value || null;
}

