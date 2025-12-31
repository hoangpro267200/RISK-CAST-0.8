/**
 * ========================================================================
 * RISKCAST v20 - Transport Module
 * ========================================================================
 * Manages transport-related fields: trade lanes, modes, POL/POD, routes
 * 
 * @class TransportModule
 */
export class TransportModule {
    /**
     * @param {Object} stateManager - State manager instance
     * @param {Object} logisticsData - Logistics data object
     * @param {Object} dropdownManager - Dropdown manager instance
     * @param {Object} toastManager - Toast manager instance
     * @param {Object} callbacks - Callback functions
     */
    constructor(stateManager, logisticsData, dropdownManager, toastManager, callbacks = {}) {
        this.state = stateManager;
        this.data = logisticsData;
        this.dropdown = dropdownManager;
        this.toast = toastManager;
        this.callbacks = callbacks;
        this.availablePOL = [];
        this.availablePOD = [];
        this.core = window.RISKCAST_INPUT_CORE || null;
    }
    
    /**
     * Initialize transport module
     */
    init() {
        if (!this.data) {
            setTimeout(() => this.init(), 500);
            return;
        }
        
        this.loadTradeLanes();
        this.loadCarriers();
        this.loadIncoterms();
        this.loadContainerTypes();
        
        // If trade lane and mode are already set, load dependent fields
        const tradeLane = this.state.getStateValue('tradeLane');
        if (tradeLane) {
            this.loadModes();
            this.loadPOL();
            this.loadPOD();
            
            const mode = this.state.getStateValue('mode');
            if (mode) {
                this.loadShipmentTypes();
                this.loadContainerTypes();
                
                const shipmentType = this.state.getStateValue('shipmentType');
                if (shipmentType) {
                    this.loadServiceRoutes();
                }
            }
        } else {
            this.loadServiceRoutes();
        }
        
        console.log('🔥 Transport module initialized ✓');
    }
    
    /**
     * Load Trade Lanes
     */
    loadTradeLanes() {
        const menu = document.getElementById('tradeLane-menu');
        if (!menu || !this.data) {
            console.warn('⚠️ Cannot load trade lanes');
            return;
        }
        
        menu.innerHTML = '';
        
        const routes = this.data.routes || {};
        const tradeLanes = Object.keys(routes).map(key => {
            const route = routes[key];
            return {
                id: key,
                name: route.name || key,
                name_vi: route.name_vi || route.name || key,
                flag: route.flag || ''
            };
        });
        
        tradeLanes.forEach(lane => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', lane.id);
            btn.innerHTML = `${lane.flag} <strong>${lane.name}</strong>`;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectTradeLane(lane.id, lane.name);
            });
            
            menu.appendChild(btn);
        });
        
        console.log(`🔥 Loaded ${tradeLanes.length} trade lanes`);
    }
    
    /**
     * Select Trade Lane
     */
    selectTradeLane(value, label) {
        this.state.setState('tradeLane', value);
        this.dropdown.updateSelection('tradeLane', value, label);
        
        // Clear dependent fields
        this.state.setState('mode', '');
        this.state.setState('shipmentType', '');
        this.state.setState('serviceRoute', '');
        this.state.setState('carrier', '');
        
        // Reload dependent dropdowns
        setTimeout(() => {
            this.loadModes();
            this.loadPOL();
            this.loadPOD();
        }, 50);
        
        console.log('🔥 Trade lane selected:', value);
        if (this.callbacks.onFormDataChange) {
            this.callbacks.onFormDataChange();
        }
    }
    
    /**
     * Load Modes based on selected trade lane
     */
    loadModes() {
        const menu = document.getElementById('mode-menu');
        if (!menu || !this.data) {
            const tradeLane = this.state.getStateValue('tradeLane');
            if (!tradeLane) return;
        }
        
        menu.innerHTML = '';
        
        const tradeLane = this.state.getStateValue('tradeLane');
        const route = this.data.getRoute(tradeLane);
        if (!route || !route.transport_modes) return;
        
        // Extract unique mode categories
        const modeMap = new Map();
        route.transport_modes.forEach(mode => {
            let category = 'SEA';
            let icon = 'ship';
            let label = 'Sea Freight';
            
            if (mode.value.startsWith('air')) {
                category = 'AIR';
                icon = 'plane';
                label = 'Air Freight';
            } else if (mode.value.startsWith('road')) {
                category = 'ROAD';
                icon = 'truck';
                label = 'Road Transport';
            } else if (mode.value.startsWith('rail')) {
                category = 'RAIL';
                icon = 'train';
                label = 'Rail Transport';
            }
            
            if (!modeMap.has(category)) {
                modeMap.set(category, { label, icon });
            }
        });
        
        modeMap.forEach((data, category) => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', category);
            btn.innerHTML = `<i data-lucide="${data.icon}"></i> ${data.label}`;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectMode(category, data.label);
            });
            
            menu.appendChild(btn);
        });
        
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        console.log(`🔥 Loaded ${modeMap.size} modes`);
    }
    
    /**
     * Select Mode
     */
    selectMode(value, label) {
        this.state.setState('mode', value);
        this.dropdown.updateSelection('mode', value, label);
        
        // Clear dependent fields
        this.state.setState('shipmentType', '');
        this.state.setState('serviceRoute', '');
        this.state.setState('carrier', '');
        this.dropdown.updateSelection('carrier', '', 'Select carrier');
        
        // Load shipment types and service routes
        setTimeout(() => {
            this.loadShipmentTypes();
            this.loadServiceRoutes();
            this.loadContainerTypes();
            this.loadCarriers();
            this.loadPOL();
            this.loadPOD();
        }, 50);
        
        console.log('🔥 Mode selected:', value);
        if (this.callbacks.onFormDataChange) {
            this.callbacks.onFormDataChange();
        }
    }
    
    /**
     * Load Shipment Types
     */
    loadShipmentTypes() {
        const menu = document.getElementById('shipmentType-menu');
        if (!menu || !this.data) {
            const tradeLane = this.state.getStateValue('tradeLane');
            const mode = this.state.getStateValue('mode');
            if (!tradeLane || !mode) return;
        }
        
        menu.innerHTML = '';
        
        const tradeLane = this.state.getStateValue('tradeLane');
        const route = this.data.getRoute(tradeLane);
        if (!route || !route.transport_modes) return;
        
        const mode = this.state.getStateValue('mode');
        const modePrefix = {
            'SEA': 'ocean',
            'AIR': 'air',
            'ROAD': 'road',
            'RAIL': 'rail'
        }[mode];
        
        if (!modePrefix) return;
        
        const matchingModes = route.transport_modes.filter(mode => 
            mode.value.startsWith(modePrefix)
        );
        
        matchingModes.forEach(mode => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', mode.value);
            btn.textContent = mode.label || mode.value;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectShipmentType(mode.value, mode.label);
            });
            
            menu.appendChild(btn);
        });
        
        console.log(`🔥 Loaded ${matchingModes.length} shipment types`);
    }
    
    /**
     * Select Shipment Type
     */
    selectShipmentType(value, label) {
        this.state.setState('shipmentType', value);
        this.dropdown.updateSelection('shipmentType', value, label || value);
        
        setTimeout(() => {
            this.loadServiceRoutes();
        }, 50);
        
        console.log('🔥 Shipment type selected:', value);
        if (this.callbacks.onFormDataChange) {
            this.callbacks.onFormDataChange();
        }
    }
    
    /**
     * Load Service Routes with PRIORITY FILTERING
     */
    loadServiceRoutes() {
        const menu = document.getElementById('serviceRoute-menu');
        
        // Check if POL/POD missing (only show message in UI, don't log warning on init)
        const pol = this.state.getStateValue('pol');
        const pod = this.state.getStateValue('pod');
        if (!pol || !pod || pol === '' || pod === '') {
            // Only show UI message, don't log warning (reduces console noise)
            if (menu) {
                menu.innerHTML = '<div style="padding: 1rem; text-align: center; opacity: 0.6;">⚠️ Please select <strong>POL</strong> and <strong>POD</strong> first.</div>';
            }
            return;
        }
        
        if (!menu || !this.data) {
            const tradeLane = this.state.getStateValue('tradeLane');
            const mode = this.state.getStateValue('mode');
            if (!tradeLane || !mode) {
                if (menu) {
                    menu.innerHTML = '<div style="padding: 1rem; text-align: center; opacity: 0.6;">⚠️ Please select <strong>Trade Lane</strong> and <strong>Mode</strong> first.</div>';
                }
                return;
            }
        }
        
        menu.innerHTML = '';
        
        const tradeLane = this.state.getStateValue('tradeLane');
        const mode = this.state.getStateValue('mode');
        let allRoutes = this.data.getServiceRoutes(tradeLane, mode);
        
        if (!allRoutes || allRoutes.length === 0) {
            if (menu) {
                menu.innerHTML = '<div style="padding: 1rem; text-align: center; opacity: 0.6;">⚠️ No service routes available for this route.</div>';
            }
            return;
        }
        
        // Filter by shipment type if selected
        const shipmentType = this.state.getStateValue('shipmentType');
        if (shipmentType) {
            allRoutes = allRoutes.filter(r => 
                !r.shipmentType || r.shipmentType === shipmentType
            );
        }
        
        // Apply priority sorting
        const priority = this.state.getStateValue('priority') || 'balanced';
        if (priority === 'fastest') {
            allRoutes.sort((a, b) => (a.transit_days || 999) - (b.transit_days || 999));
        } else if (priority === 'cheapest') {
            allRoutes.sort((a, b) => (a.cost || 999999) - (b.cost || 999999));
        } else if (priority === 'reliable') {
            allRoutes.sort((a, b) => (b.reliability || 0) - (a.reliability || 0));
        } else if (priority === 'balanced') {
            allRoutes = allRoutes.map(r => ({
                ...r,
                _compositeScore: this.calculatePriorityScore(r, 'balanced')
            }));
            allRoutes.sort((a, b) => b._compositeScore - a._compositeScore);
        }
        
        // Render routes
        allRoutes.forEach((r, index) => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            if (index === 0) {
                btn.classList.add('rc-recommended');
            }
            btn.setAttribute('data-value', r.route_id);
            
            btn.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    <div><strong>${r.route_name || 'Route'}</strong>${index === 0 ? ' <span style="color: var(--rc-neon-primary); font-size: 0.75rem;">✓ RECOMMENDED</span>' : ''}</div>
                    <div style="font-size: 0.875rem; opacity: 0.7;">
                        ${r.pol} → ${r.pod} • ${r.carrier || 'Carrier'} • ${r.transit_days || 0}d
                        • ${r.reliability}% reliable • Cost: ${(r.cost || 0).toFixed(0)}
                    </div>
                </div>
            `;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectServiceRoute(r);
            });
            
            menu.appendChild(btn);
        });
        
        console.log(`🔥 Loaded ${allRoutes.length} service routes (priority: ${priority})`);
    }
    
    /**
     * Calculate priority score for balanced mode
     */
    calculatePriorityScore(route, priority) {
        const transit = route.transit_days || 15;
        const cost = route.cost || 1000;
        const reliability = route.reliability || 80;
        
        const speedScore = Math.max(0, 100 - transit * 2);
        const costScore = Math.max(0, 100 - (cost - 1000) / 10);
        const reliabilityScore = reliability;
        
        if (priority === 'balanced') {
            return (speedScore + costScore + reliabilityScore) / 3;
        }
        
        return reliabilityScore;
    }
    
    /**
     * Select Service Route
     */
    selectServiceRoute(routeData) {
        this.state.setState('serviceRoute', routeData.route_id);
        this.state.setState('serviceRouteData', routeData);
        
        const label = `${routeData.pol} → ${routeData.pod} • ${routeData.carrier || 'Carrier'} • ${routeData.transit_days || 0}d`;
        this.dropdown.updateSelection('serviceRoute', routeData.route_id, label);
        
        // Auto-fill from route
        this.autoFillFromRoute(routeData);
        
        // Update POL/POD dropdowns
        this.loadPOL();
        this.loadPOD();
        
        console.log('🔥 Service route selected:', routeData.route_id);
        if (this.callbacks.onFormDataChange) {
            this.callbacks.onFormDataChange();
        }
    }
    
    /**
     * Auto-fill fields from selected route
     */
    autoFillFromRoute(route) {
        if (route.transit_days) {
            const transitInput = document.getElementById('transitDays');
            if (transitInput) {
                transitInput.value = route.transit_days;
                this.state.setState('transitDays', route.transit_days);
            }
        }
        
        if (route.schedule) {
            const scheduleInput = document.getElementById('schedule');
            if (scheduleInput) {
                scheduleInput.value = route.schedule;
                this.state.setState('schedule', route.schedule);
            }
        }
        
        if (route.reliability) {
            this.state.setState('reliability', route.reliability);
        }
        
        if (route.carrier) {
            this.state.setState('carrier', route.carrier);
            this.dropdown.updateSelection('carrier', route.carrier, route.carrier);
        }
        
        if (this.callbacks.calculateETA && this.state.getStateValue('etd') && route.transit_days) {
            this.callbacks.calculateETA();
        }
    }
    
    /**
     * Load POL (Port of Loading)
     */
    loadPOL() {
        // Extract available POL from selected route
        const routeData = this.state.getStateValue('serviceRouteData');
        if (routeData && routeData.pol) {
            this.availablePOL = [routeData.pol];
        }
        
        // Update auto-suggest manager if available
        if (this.callbacks.setAvailablePorts) {
            this.callbacks.setAvailablePorts(this.availablePOL, this.availablePOD);
        }
    }
    
    /**
     * Load POD (Port of Discharge)
     */
    loadPOD() {
        // Extract available POD from selected route
        const routeData = this.state.getStateValue('serviceRouteData');
        if (routeData && routeData.pod) {
            this.availablePOD = [routeData.pod];
        }
        
        // Update auto-suggest manager if available
        if (this.callbacks.setAvailablePorts) {
            this.callbacks.setAvailablePorts(this.availablePOL, this.availablePOD);
        }
    }
    
    /**
     * Load Carriers
     */
    loadCarriers() {
        const menu = document.getElementById('carrier-menu');
        if (!menu) return;
        
        menu.innerHTML = '';
        
        const mode = this.state.getStateValue('mode');
        const carrierList = (this.core && this.core.getOptionsForField) 
            ? this.core.getOptionsForField('transport', 'carrier', { mode, transport: { mode } }) 
            : (window.CARRIER_BY_MODE?.[mode] || []);
        
        if (carrierList.length === 0) {
            menu.innerHTML = '<div style="padding: 1rem; text-align: center; opacity: 0.6; font-size: 0.875rem;">Select mode first</div>';
            return;
        }
        
        carrierList.forEach(carrier => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', carrier.value || carrier);
            btn.textContent = carrier.label || carrier;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const value = carrier.value || carrier;
                const label = carrier.label || carrier;
                this.state.setState('carrier', value);
                this.dropdown.updateSelection('carrier', value, label);
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
            
            menu.appendChild(btn);
        });
    }
    
    /**
     * Load Container Types
     */
    loadContainerTypes() {
        const menu = document.getElementById('containerType-menu');
        if (!menu) {
            console.warn('⚠️ Container Type menu not found');
            return;
        }
        
        menu.innerHTML = '';
        
        const mode = this.state.getStateValue('mode') || 'sea';
        let containerTypes = [];
        
        // Try multiple data sources
        if (this.core && this.core.getOptionsForField) {
            containerTypes = this.core.getOptionsForField('transport', 'container', { mode, transport: { mode } }) || [];
        }
        
        // Fallback to CONTAINER_TYPES_BY_MODE
        if (containerTypes.length === 0 && window.CONTAINER_TYPES_BY_MODE) {
            const modeKey = mode.toLowerCase();
            containerTypes = window.CONTAINER_TYPES_BY_MODE[modeKey] || window.CONTAINER_TYPES_BY_MODE['sea'] || [];
        }
        
        // Fallback to LOGISTICS_DATA
        if (containerTypes.length === 0 && window.LOGISTICS_DATA && window.LOGISTICS_DATA.CONTAINER_TYPES) {
            const modeKey = mode.toLowerCase();
            const types = window.LOGISTICS_DATA.CONTAINER_TYPES[modeKey] || [];
            containerTypes = types.map(t => {
                if (typeof t === 'string') {
                    // Parse string like "20DC (Dry Container)" to {value, label}
                    const match = t.match(/^([^(]+)\s*\(([^)]+)\)?$/);
                    if (match) {
                        return { value: match[1].trim().toLowerCase().replace(/\s+/g, '_'), label: t };
                    }
                    return { value: t.toLowerCase().replace(/\s+/g, '_'), label: t };
                }
                return t;
            });
        }
        
        // Final fallback - default container types
        if (containerTypes.length === 0) {
            containerTypes = [
                { value: '20ft', label: '20ft Standard' },
                { value: '40ft', label: '40ft Standard' },
                { value: '40hc', label: '40ft High Cube' },
                { value: 'reefer', label: 'Reefer Container' },
                { value: 'opentop', label: 'Open Top' },
                { value: 'flatrack', label: 'Flat Rack' }
            ];
        }
        
        console.log(`🔥 Loading ${containerTypes.length} container types for mode: ${mode}`);
        
        containerTypes.forEach(type => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.type = 'button';
            const value = type.value || (typeof type === 'string' ? type.toLowerCase().replace(/\s+/g, '_') : '');
            const label = type.label || type || 'Unknown';
            btn.setAttribute('data-value', value);
            btn.textContent = label;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                
                // Update state
                this.state.setState('containerType', value);
                
                // Update dropdown display
                this.dropdown.updateSelection('containerType', value, label);
                
                // Close dropdown
                const dropdown = document.getElementById('containerType');
                if (dropdown && this.dropdown) {
                    this.dropdown.closeDropdown(dropdown);
                }
                
                // Trigger callbacks
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
                
                console.log(`✅ Container Type selected: ${value} (${label})`);
            });
            
            menu.appendChild(btn);
        });
    }
    
    /**
     * Load Incoterms
     */
    loadIncoterms() {
        const menu = document.getElementById('incoterm-menu');
        if (!menu) return;
        
        menu.innerHTML = '';
        
        const incoterms = (this.core && this.core.OPTIONS && this.core.OPTIONS.incoterms) 
            ? this.core.OPTIONS.incoterms 
            : ['EXW', 'FCA', 'FAS', 'FOB', 'CFR', 'CIF', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP'];
        
        incoterms.forEach(term => {
            const btn = document.createElement('button');
            btn.className = 'rc-dropdown-item';
            btn.setAttribute('data-value', term);
            btn.textContent = term;
            
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectIncoterm(term);
            });
            
            menu.appendChild(btn);
        });
    }
    
    /**
     * Select Incoterm
     */
    selectIncoterm(value) {
        this.state.setState('incoterm', value);
        this.dropdown.updateSelection('incoterm', value, value);
        if (this.callbacks.onFormDataChange) {
            this.callbacks.onFormDataChange();
        }
    }
}

