/**
 * ========================================================================
 * RISKCAST v20 - Main Input Controller
 * ========================================================================
 * Main orchestrator for RISKCAST v20 input form
 * Coordinates all modules and manages the overall flow
 * 
 * @class RiskcastInputController
 */

// Core imports
import { StateManager } from './StateManager.js';
import { APIClient } from './APIClient.js';

// Utils imports
import { sanitizeGlobalState, sanitizeAPIPayload, RC_getState, RC_setState } from '../utils/SanitizeHelpers.js';
import { validateRequiredFields, highlightErrors } from '../utils/Validators.js';
import { calculateETA, diffDays } from '../utils/DateCalculators.js';
import { loadLogisticsData } from '../utils/DataLoaders.js';
import { DemoAutoFill } from '../utils/DemoAutoFill.js';

// Effects imports
import { ThemeManager } from '../effects/ThemeManager.js';
import { ParticleBackground } from '../effects/ParticleBackground.js';
import { FormPanelGlow } from '../effects/FormPanelGlow.js';
import { NavigationSpy } from '../effects/NavigationSpy.js';
import { SidebarManager } from '../effects/SidebarManager.js';

// UI imports
import { ToastManager } from '../ui/ToastManager.js';
import { DropdownManager } from '../ui/DropdownManager.js';
import { AutoSuggestManager } from '../ui/AutoSuggestManager.js';
import { PillGroupManager } from '../ui/PillGroupManager.js';
import { UploadZoneManager } from '../ui/UploadZoneManager.js';

// Modules imports
import { TransportModule } from '../modules/TransportModule.js';
import { CargoModule } from '../modules/CargoModule.js';
import { PartyModule } from '../modules/PartyModule.js';
import { PriorityManager } from '../modules/PriorityManager.js';
import { ModuleCardsManager } from '../modules/ModuleCardsManager.js';

export class RiskcastInputController {
    constructor() {
        // Core dependencies
        this.stateManager = new StateManager();
        this.apiClient = new APIClient(this.stateManager);
        this.toastManager = new ToastManager();
        
        // Effects
        this.themeManager = new ThemeManager();
        this.particleBackground = new ParticleBackground();
        this.formPanelGlow = new FormPanelGlow();
        this.navigationSpy = new NavigationSpy();
        this.sidebarManager = new SidebarManager();
        
        // UI
        this.dropdownManager = new DropdownManager();
        this.pillGroupManager = new PillGroupManager({
            onPillSelect: (field, value) => {
                this.stateManager.setState(field, value);
            },
            onFormDataChange: () => this.onFormDataChange()
        });
        this.uploadZoneManager = new UploadZoneManager({
            onFileUpload: (file) => {
                this.uploadedFile = file;
            },
            showToast: (msg, type) => this.toastManager.showToast(msg, type)
        });
        
        // Auto-suggest (needs port database and countries)
        this.core = window.RISKCAST_INPUT_CORE || null;
        this.portDatabase = (this.core && this.core.OPTIONS && this.core.OPTIONS.ports) ? this.core.OPTIONS.ports : [
            { code: 'LAX', name: 'Los Angeles', country: 'US' },
            { code: 'LGB', name: 'Long Beach', country: 'US' },
            { code: 'VNSGN', name: 'Sai Gon (HCMC)', country: 'VN' },
            { code: 'CMIT', name: 'Cai Mep', country: 'VN' },
            { code: 'CNSHA', name: 'Shanghai', country: 'CN' },
            { code: 'VNHPH', name: 'Hai Phong', country: 'VN' },
            { code: 'NLRTM', name: 'Rotterdam', country: 'NL' },
            { code: 'SGSIN', name: 'Singapore', country: 'SG' },
            { code: 'HKHKG', name: 'Hong Kong', country: 'HK' },
            { code: 'DEHAM', name: 'Hamburg', country: 'DE' },
            { code: 'USNYC', name: 'New York', country: 'US' },
            { code: 'JPTYO', name: 'Tokyo', country: 'JP' },
            { code: 'KRPUS', name: 'Busan', country: 'KR' },
            { code: 'AEDXB', name: 'Dubai', country: 'AE' },
            { code: 'GBLON', name: 'London', country: 'GB' },
            { code: 'USOAK', name: 'Oakland', country: 'US' },
            { code: 'USSEA', name: 'Seattle', country: 'US' }
        ];
        this.countries = [
            'USA', 'China', 'Germany', 'Japan', 'United Kingdom',
            'France', 'Netherlands', 'Singapore', 'South Korea', 'Vietnam',
            'India', 'Thailand', 'Malaysia', 'Indonesia', 'UAE', 'Belgium',
            'Italy', 'Spain', 'Australia', 'Brazil', 'Canada', 'Mexico'
        ];
        
        this.autoSuggestManager = new AutoSuggestManager(
            this.portDatabase,
            this.countries,
            {
                selectPOL: (value, name) => this.selectPOL(value, name),
                selectPOD: (value, name) => this.selectPOD(value, name),
                onFormDataChange: () => this.onFormDataChange()
            }
        );
        
        // Demo auto-fill
        this.demoAutoFill = new DemoAutoFill(this);
        
        // Logistics data
        this.logisticsData = null;
        this.availablePOL = [];
        this.availablePOD = [];
        this.uploadedFile = null;
        
        // Initialize modules (after dependencies are set)
        this.transportModule = new TransportModule(
            this.stateManager,
            null, // Will be set when logisticsData loads
            this.dropdownManager,
            this.toastManager,
            {
                onFormDataChange: () => this.onFormDataChange(),
                calculateETA: () => this.calculateETA(),
                setAvailablePorts: (pol, pod) => {
                    this.availablePOL = pol;
                    this.availablePOD = pod;
                    this.autoSuggestManager.setAvailablePorts(pol, pod);
                }
            }
        );
        
        this.cargoModule = new CargoModule(
            this.stateManager,
            null, // Will be set when logisticsData loads
            this.dropdownManager,
            {
                onFormDataChange: () => this.onFormDataChange()
            }
        );
        
        this.partyModule = new PartyModule(
            this.stateManager,
            null, // Will be set when logisticsData loads
            this.dropdownManager,
            {
                onFormDataChange: () => this.onFormDataChange()
            }
        );
        
        this.priorityManager = new PriorityManager(
            this.stateManager,
            this.transportModule,
            {
                onFormDataChange: () => this.onFormDataChange()
            }
        );
        
        this.moduleCardsManager = new ModuleCardsManager(
            this.stateManager,
            {
                onFormDataChange: () => this.onFormDataChange()
            }
        );
        
        // Expose formData for backward compatibility
        this.formData = this.stateManager.getState();
    }
    
    /**
     * Initialize the controller
     */
    async init() {
        console.log('🔥 RISKCAST v20.3 Controller initializing...');
        
        // Sanitize state on page load
        this.stateManager.sanitize();
        
        // Load logistics data
        await loadLogisticsData(
            (data) => {
                this.logisticsData = data;
                // Update modules with logistics data
                this.transportModule.data = data;
                this.cargoModule.data = data;
                this.partyModule.data = data;
                console.log('✅ LOGISTICS_DATA loaded');
            }
        );
        
        // Initialize effects
        this.themeManager.init();
        this.sidebarManager.init();
        this.navigationSpy.init();
        this.formPanelGlow.init();
        this.particleBackground.init();
        
        // Initialize UI
        this.dropdownManager.initDropdowns();
        this.autoSuggestManager.initAutoSuggest();
        this.pillGroupManager.initPillGroups();
        this.uploadZoneManager.initUploadZone();
        
        // Initialize modules
        this.transportModule.init();
        this.cargoModule.init();
        this.partyModule.init();
        this.priorityManager.init();
        this.moduleCardsManager.init();
        
        // Initialize demo auto-fill
        this.demoAutoFill.init();
        
        // Initialize input handlers
        this.initInputHandlers();
        this.initButtons();
        
        // Load and sanitize RISKCAST_STATE on init
        sanitizeGlobalState();
        
        // Load state from RISKCAST_STATE into UI
        this.loadStateIntoUI();
        
        console.log('✅ RISKCAST v20.3 Controller ready ✓');
    }
    
    /**
     * Initialize input handlers
     * Maps field names to state structure and persists on input
     */
    initInputHandlers() {
        // Field mapping: HTML field name -> State path
        const fieldMap = {
            // Cargo fields
            'hsCode': 'cargo.hsCode',
            'packageCount': 'cargo.packageCount',
            'grossWeight': 'cargo.weights.grossKg',
            'netWeight': 'cargo.weights.netKg',
            'volumeCbm': 'cargo.volumeCbm',
            'insuranceValue': 'cargo.insurance.valueUsd',
            'cargoDescription': 'cargo.description',
            
            // Transport fields
            'etd': 'etd',
            'eta': 'eta',
            'transitDays': 'transitDays',
            'incotermLocation': 'incotermLocation',
            
            // Seller fields
            'sellerCompany': 'seller.companyName',
            'sellerCity': 'seller.city',
            'sellerAddress': 'seller.address',
            'sellerContact': 'seller.contactPerson',
            'sellerContactRole': 'seller.contactRole',
            'sellerEmail': 'seller.email',
            'sellerPhone': 'seller.phone',
            'sellerTaxId': 'seller.taxId',
            
            // Buyer fields
            'buyerCompany': 'buyer.companyName',
            'buyerCity': 'buyer.city',
            'buyerAddress': 'buyer.address',
            'buyerContact': 'buyer.contactPerson',
            'buyerContactRole': 'buyer.contactRole',
            'buyerEmail': 'buyer.email',
            'buyerPhone': 'buyer.phone',
            'buyerTaxId': 'buyer.taxId'
        };
        
        // Bind all inputs (with data-field or id)
        const inputs = document.querySelectorAll('input, textarea');
        
        inputs.forEach(input => {
            // Get field name from data-field or id
            let fieldName = input.getAttribute('data-field');
            if (!fieldName && input.id) {
                fieldName = input.id;
            }
            
            if (!fieldName) return; // Skip if no identifier
            
            // Map to state path
            const statePath = fieldMap[fieldName] || fieldName;
            
            // Bind input event (immediate update)
            input.addEventListener('input', () => {
                const value = input.type === 'number' ? (input.value ? Number(input.value) : null) : input.value;
                this.stateManager.setState(statePath, value);
                this.onFormDataChange(); // Persist immediately
            });
            
            // Bind change event (for validation, etc.)
            input.addEventListener('change', () => {
                const value = input.type === 'number' ? (input.value ? Number(input.value) : null) : input.value;
                this.stateManager.setState(statePath, value);
                
                // Special handling for ETD
                if (fieldName === 'etd' || statePath === 'etd') {
                    this.calculateETA();
                }
                
                this.onFormDataChange();
            });
            
            // Load saved value from state
            const savedValue = this.getStateValueByPath(statePath);
            if (savedValue !== undefined && savedValue !== null && savedValue !== '') {
                input.value = savedValue;
            }
        });
        
        console.log(`🔥 Input handlers initialized ✓ (${inputs.length} inputs bound)`);
    }
    
    /**
     * Get state value by path (helper for input handlers)
     * @param {string} path - State path (e.g., 'cargo.weights.grossKg')
     * @returns {*} State value
     */
    getStateValueByPath(path) {
        const keys = path.split('.');
        let obj = this.stateManager.getState();
        
        for (const key of keys) {
            if (obj === null || obj === undefined) return undefined;
            obj = obj[key];
        }
        
        return obj;
    }
    
    /**
     * Load state from RISKCAST_STATE into UI elements
     */
    loadStateIntoUI() {
        const state = this.stateManager.getState();
        
        // Load transport dropdowns
        if (state.tradeLane && this.transportModule) {
            // Find label from logistics data
            const logisticsData = this.logisticsData || window.LOGISTICS_DATA;
            if (logisticsData?.routes?.[state.tradeLane]) {
                const lane = logisticsData.routes[state.tradeLane];
                const label = lane.name || state.tradeLane;
                this.dropdownManager.updateSelection('tradeLane', state.tradeLane, label);
            } else {
                this.dropdownManager.updateSelection('tradeLane', state.tradeLane, state.tradeLane);
            }
        }
        
        if (state.mode && this.transportModule) {
            const modeLabels = {
                'SEA': 'Sea Freight',
                'AIR': 'Air Freight',
                'ROAD': 'Road Transport',
                'RAIL': 'Rail Transport'
            };
            const label = modeLabels[state.mode] || state.mode;
            this.dropdownManager.updateSelection('mode', state.mode, label);
        }
        
        if (state.shipmentType) {
            this.dropdownManager.updateSelection('shipmentType', state.shipmentType, state.shipmentType);
        }
        
        if (state.serviceRoute) {
            this.dropdownManager.updateSelection('serviceRoute', state.serviceRoute, state.serviceRoute);
        }
        
        if (state.carrier) {
            this.dropdownManager.updateSelection('carrier', state.carrier, state.carrier);
        }
        
        if (state.containerType) {
            // Find label for container type from available options
            const mode = state.mode || 'sea';
            let containerLabel = state.containerType;
            
            // Try to find label from CONTAINER_TYPES_BY_MODE
            if (window.CONTAINER_TYPES_BY_MODE) {
                const modeKey = mode.toLowerCase();
                const types = window.CONTAINER_TYPES_BY_MODE[modeKey] || window.CONTAINER_TYPES_BY_MODE['sea'] || [];
                const found = types.find(t => {
                    const val = t.value || (typeof t === 'string' ? t.toLowerCase().replace(/\s+/g, '_') : '');
                    return val === state.containerType || val === state.containerType.toLowerCase();
                });
                if (found) {
                    containerLabel = found.label || found;
                }
            }
            
            // Fallback to LOGISTICS_DATA
            if (containerLabel === state.containerType && window.LOGISTICS_DATA && window.LOGISTICS_DATA.CONTAINER_TYPES) {
                const modeKey = mode.toLowerCase();
                const types = window.LOGISTICS_DATA.CONTAINER_TYPES[modeKey] || [];
                const found = types.find(t => {
                    if (typeof t === 'string') {
                        const val = t.toLowerCase().replace(/\s+/g, '_');
                        return val === state.containerType || val === state.containerType.toLowerCase();
                    }
                    return false;
                });
                if (found) {
                    containerLabel = found;
                }
            }
            
            this.dropdownManager.updateSelection('containerType', state.containerType, containerLabel);
        }
        
        if (state.incoterm) {
            this.dropdownManager.updateSelection('incoterm', state.incoterm, state.incoterm);
        }
        
        // Load priority buttons
        if (state.priority) {
            const priorityPills = document.querySelectorAll('.rc-pill-group[data-field="priority"] .rc-pill');
            priorityPills.forEach(p => {
                p.classList.remove('active');
                if (p.getAttribute('data-value') === state.priority) {
                    p.classList.add('active');
                }
            });
        }
        
        // Load POL/POD (auto-suggest fields)
        if (state.pol) {
            const polInput = document.querySelector('#pol .rc-input');
            if (polInput) {
                polInput.value = state.pol;
            }
        }
        
        if (state.pod) {
            const podInput = document.querySelector('#pod .rc-input');
            if (podInput) {
                podInput.value = state.pod;
            }
        }
        
        // Load cargo dropdowns
        if (state.cargo?.cargoType) {
            this.dropdownManager.updateSelection('cargoType', state.cargo.cargoType, state.cargo.cargoType);
        }
        
        if (state.cargo?.packingType) {
            this.dropdownManager.updateSelection('packingType', state.cargo.packingType, state.cargo.packingType);
        }
        
        if (state.cargo?.insurance?.coverageType) {
            this.dropdownManager.updateSelection('insuranceCoverage', state.cargo.insurance.coverageType, state.cargo.insurance.coverageType);
        }
        
        // Load seller/buyer dropdowns
        if (state.seller?.businessType) {
            this.dropdownManager.updateSelection('sellerBusinessType', state.seller.businessType, state.seller.businessType);
        }
        
        if (state.buyer?.businessType) {
            this.dropdownManager.updateSelection('buyerBusinessType', state.buyer.businessType, state.buyer.businessType);
        }
        
        // Load seller/buyer country (auto-suggest)
        if (state.seller?.country?.name) {
            const sellerCountryInput = document.querySelector('#sellerCountry .rc-input');
            if (sellerCountryInput) {
                sellerCountryInput.value = state.seller.country.name;
            }
        }
        
        if (state.buyer?.country?.name) {
            const buyerCountryInput = document.querySelector('#buyerCountry .rc-input');
            if (buyerCountryInput) {
                buyerCountryInput.value = state.buyer.country.name;
            }
        }
        
        console.log('✅ State loaded into UI from RISKCAST_STATE');
    }
    
    /**
     * Initialize button handlers
     */
    initButtons() {
        // Reset
        const resetBtn = document.getElementById('rc-btn-reset');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                if (confirm('Reset form? All data will be lost.')) {
                    this.resetForm();
                }
            });
        }
        
        // Submit
        const submitBtn = document.getElementById('rc-btn-submit');
        if (submitBtn) {
            submitBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.submitForm();
            });
        }
    }
    
    /**
     * Calculate ETA from ETD and transit days
     */
    calculateETA() {
        const etdInput = document.getElementById('etd');
        const transitInput = document.getElementById('transitDays');
        const etaInput = document.getElementById('eta');
        
        if (!etdInput || !transitInput || !etaInput) return;
        
        const etd = etdInput.value;
        const transit = parseInt(transitInput.value);
        
        if (!etd || !transit) return;
        
        const eta = calculateETA(etd, transit);
        if (eta) {
            etaInput.value = eta;
            this.stateManager.setState('eta', eta);
        }
    }
    
    /**
     * Handle form data change
     */
    onFormDataChange() {
        this.stateManager.persist();
        // Update global reference for backward compatibility
        this.formData = this.stateManager.getState();
        window.RC_STATE = this.formData;
        // Additional logic can be added here
    }
    
    /**
     * Show toast notification (wrapper for toastManager)
     * @param {string} message - Toast message
     * @param {string} type - Toast type
     */
    showToast(message, type = 'info') {
        this.toastManager.showToast(message, type);
    }
    
    /**
     * Select POL (Port of Loading)
     * @param {string} value - POL code
     * @param {string} name - POL name
     */
    selectPOL(value, name) {
        this.stateManager.setState('pol', value);
        // Update UI and trigger dependent field updates
        this.onFormDataChange();
    }
    
    /**
     * Select POD (Port of Discharge)
     * @param {string} value - POD code
     * @param {string} name - POD name
     */
    selectPOD(value, name) {
        this.stateManager.setState('pod', value);
        // Update UI and trigger dependent field updates
        this.onFormDataChange();
    }
    
    /**
     * Submit form
     */
    async submitForm() {
        console.log('📊 Submitting form:', this.stateManager.getState());
        
        // 1. Sanitize state first
        this.stateManager.sanitize();
        
        // 2. Validate required fields
        const errors = validateRequiredFields(this.stateManager.getState());
        
        if (errors.length > 0) {
            this.toastManager.showToast('Vui lòng nhập đầy đủ thông tin.', 'error');
            highlightErrors(errors);
            console.warn('⚠️ Validation failed:', errors);
            return;
        }
        
        const submitBtn = document.getElementById('rc-btn-submit');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader-2"></i> Đang phân tích...';
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
        
        this.toastManager.showToast('Đang chạy phân tích rủi ro AI...', 'info');
        
        try {
            // 3. Sync current formData to RISKCAST_STATE first
            this.stateManager.syncToRISKCAST_STATE();
            
            // 4. Build RISKCAST_STATE from form data (full state with derived values)
            const state = this.buildRiskcastState();
            
            // 5. Save RISKCAST_STATE to localStorage
            RC_setState(state);
            
            // 6. Sanitize state
            sanitizeGlobalState();
            let RISKCAST_STATE = RC_getState();
            
            // 7. Build API payload (already cleaned in APIClient)
            let apiPayload = this.apiClient.buildShipmentPayloadForAPI(RISKCAST_STATE);
            
            // 8. ULTIMATE FAILSAFE: Force ALL string fields (backend calls .upper() on many fields)
            // CRITICAL FIELDS that backend uses .upper() on: pol, pod, route, carrier, port
            const ensureString = (val, defaultVal) => {
                if (val === null || val === undefined || val === '') return defaultVal;
                return String(val);
            };
            
            // CRITICAL: Backend calls .upper() on these - MUST be strings
            apiPayload.pol = ensureString(apiPayload.pol, 'UNKNOWN_POL');
            apiPayload.pod = ensureString(apiPayload.pod, 'UNKNOWN_POD');
            apiPayload.route = ensureString(apiPayload.route, 'UNKNOWN_ROUTE');
            apiPayload.carrier = ensureString(apiPayload.carrier, 'UNKNOWN_CARRIER');
            apiPayload.transport_mode = ensureString(apiPayload.transport_mode, 'SEA');
            apiPayload.cargo_type = ensureString(apiPayload.cargo_type, 'general');
            apiPayload.incoterm = ensureString(apiPayload.incoterm, 'EXW');
            apiPayload.container = ensureString(apiPayload.container, 'STANDARD');
            apiPayload.packaging = ensureString(apiPayload.packaging, 'carton');
            apiPayload.priority = ensureString(apiPayload.priority, 'standard');
            
            // Ensure nested objects have safe strings
            if (apiPayload.seller) {
                Object.keys(apiPayload.seller).forEach(key => {
                    apiPayload.seller[key] = ensureString(apiPayload.seller[key], '');
                });
            }
            if (apiPayload.buyer) {
                Object.keys(apiPayload.buyer).forEach(key => {
                    apiPayload.buyer[key] = ensureString(apiPayload.buyer[key], '');
                });
            }
            
            // Force numeric fields to be numbers
            apiPayload.packages = Number(apiPayload.packages) || 1;
            apiPayload.transit_time = Number(apiPayload.transit_time) || 15;
            apiPayload.cargo_value = Math.max(Number(apiPayload.cargo_value) || 1000, 1000); // Minimum 1000 to ensure financial calculations
            apiPayload.distance = Number(apiPayload.distance) || 1000;
            apiPayload.shipment_value = Math.max(Number(apiPayload.shipment_value) || 1000, 1000); // Minimum 1000 to ensure financial calculations
            
            // Ensure optional string fields are strings (not null)
            apiPayload.etd = ensureString(apiPayload.etd, '');
            apiPayload.eta = ensureString(apiPayload.eta, '');
            apiPayload.route_type = ensureString(apiPayload.route_type, '');
            apiPayload.hs_code = ensureString(apiPayload.hs_code, '');
            apiPayload.language = ensureString(apiPayload.language, 'vi');
            
            // FINAL VALIDATION: Check critical fields one more time
            const criticalCheck = ['pol', 'pod', 'route', 'carrier', 'transport_mode', 'cargo_type'];
            criticalCheck.forEach(field => {
                if (typeof apiPayload[field] !== 'string') {
                    console.error(`❌ CRITICAL ERROR: ${field} is not a string!`, apiPayload[field]);
                    apiPayload[field] = 'UNKNOWN';
                }
            });
            
            console.log('%c🔥 FINAL FAILSAFE PAYLOAD (NO NULL):', 'color:lime;font-weight:bold', apiPayload);
            console.log('%c🔍 Critical Fields:', 'color:cyan;font-weight:bold', {
                pol: apiPayload.pol + ' (' + typeof apiPayload.pol + ')',
                pod: apiPayload.pod + ' (' + typeof apiPayload.pod + ')',
                route: apiPayload.route + ' (' + typeof apiPayload.route + ')',
                carrier: apiPayload.carrier + ' (' + typeof apiPayload.carrier + ')'
            });
            
            // 7. Submit to API
            const result = await this.apiClient.submitToEngine(apiPayload);
            
            // 8. Save results
            localStorage.removeItem('RISKCAST_RESULTS');
            localStorage.removeItem('RISKCAST_RESULTS_V38');
            localStorage.removeItem('RISKCAST_RESULTS_V1');
            localStorage.setItem('RISKCAST_RESULTS_V2', JSON.stringify(result));
            
            this.toastManager.showToast('Phân tích hoàn tất! Đang chuyển đến trang tóm tắt...', 'success');
            
            // 9. Redirect to summary first (then user can go to results from there)
            setTimeout(() => {
                window.location.href = '/summary';
            }, 500);
            
        } catch (err) {
            console.error('❌ Failed to submit form:', err);
            this.toastManager.showToast(`Lỗi: ${err.message}`, 'error');
            
            // Re-enable button on error
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i data-lucide="zap"></i> Run Risk Analysis <i data-lucide="arrow-right"></i>';
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        }
    }
    
    /**
     * Build RISKCAST_STATE from form data
     * @returns {Object} RISKCAST_STATE object
     */
    buildRiskcastState() {
        const f = this.stateManager.getState();
        const c = f.cargo || {};
        const weights = c.weights || {};
        const insurance = c.insurance || {};
        const dg = c.dangerousGoods || {};
        const seller = f.seller || {};
        const buyer = f.buyer || {};
        const modulesForm = f.modules || {};
        
        // Calculate derived values
        const tradeLane = f.tradeLane || '';
        const pol = f.pol || '';
        const pod = f.pod || '';
        const transitDays = f.transitDays || f.transit_time || 15;
        const onTimeProbability = Math.max(0.5, 1 - (transitDays / 30) * 0.3);
        const reliabilityScore = f.reliability || 85;
        
        // Build route legs
        const routeLegs = this.apiClient.buildRouteLegs(pol, pod);
        const totalDistance = routeLegs.reduce((sum, l) => sum + (Number(l.distanceNm) || 0), 0);
        const grossWeight = Number(weights.grossKg || 0);
        const eta = f.eta || calculateETA(f.etd, transitDays);
        
        // Calculate ETA if not set
        const calculateEtaFromEtd = (etd, days) => {
            if (!etd || !days) return '';
            return calculateETA(etd, days);
        };
        
        const finalEta = eta || calculateEtaFromEtd(f.etd, transitDays);
        const transitDaysProjected = finalEta && f.etd ? diffDays(f.etd, finalEta) : transitDays;
        const shipmentId = f.reference || f.bookingNumber || `SHIP-${Date.now()}`;
        const shipmentTitle = tradeLane || `${pol || "Origin"} → ${pod || "Destination"}`;
        
        // Regional scores
        const regionalScores = this.detectRegionalScores(pod);
        
        // Overall risk
        const overallRisk = this.calculateOverallRisk();
        const delayRisk = Math.max(0, 1 - onTimeProbability);
        
        // Derived KPIs
        const emissionFactor = 0.00008;
        const carbonFootprintTons = +(grossWeight * emissionFactor).toFixed(2);
        const estimatedCost = Math.max(0, grossWeight * (totalDistance || 1) * 0.02);
        
        // Active modules list
        const activeModulesList = Object.keys(modulesForm).filter(k => modulesForm[k]);
        
        let state = {
            shipment: {
                id: shipmentId,
                title: shipmentTitle,
                status: "In Transit",
                mode: f.mode || "",
                carrier: f.carrier || "",
                valueUSD: Number(insurance.valueUsd || f.cargo_value || f.cargoValue || 0),
                onTimeProbability,
                transitPlannedDays: transitDays,
                transitActualDays: transitDaysProjected,
                carbonFootprintTons
            },
            transport: {
                tradeLane,
                mode: f.mode || "",
                modeOfTransport: f.mode || "",
                shipmentType: f.shipmentType || "",
                carrier: f.carrier || "",
                priority: f.priority || "",
                serviceRoute: f.serviceRoute || "",
                incoterm: f.incoterm || "",
                incotermLocation: f.incotermLocation || "",
                pol,
                pod,
                containerType: f.containerType || "",
                etd: f.etd || "",
                eta: finalEta || "",
                transitTime: transitDays,
                transitTimeDays: transitDays,
                scheduleFrequency: f.schedule || f.scheduleFrequency || "",
                reliabilityScore,
                distance: totalDistance,
                distanceUnit: "NM",
                costUSD: estimatedCost
            },
            cargo: {
                cargoType: c.cargoType || "",
                hsCode: c.hsCode || "",
                packingType: c.packingType || "",
                numberOfPackages: Number(c.packageCount || 0),
                grossWeight: grossWeight,
                netWeight: Number(weights.netKg || 0),
                volumeM3: Number(c.volumeCbm || 0),
                stackability: c.stackable === false ? "Non-stackable" : c.stackable === true ? "Stackable" : "",
                insuranceValue: Number(insurance.valueUsd || 0),
                // CRITICAL: cargo_value for Summary page compatibility
                cargo_value: Number(insurance.valueUsd || 0),
                value: Number(insurance.valueUsd || 0),
                insuranceCoverage: insurance.coverageType || "",
                sensitivity: c.sensitivity || "",
                dangerousGoods: dg.isDG || false,
                description: c.description || "",
                specialInstructions: c.specialHandling || ""
            },
            seller: {
                companyName: seller.companyName || "",
                businessType: seller.businessType || "",
                country: seller.country?.name || seller.country || "",
                city: seller.city || "",
                address: seller.address || "",
                contactPerson: seller.contactPerson || "",
                contactRole: seller.contactRole || "",
                email: seller.email || "",
                phone: seller.phone || "",
                taxId: seller.taxId || ""
            },
            buyer: {
                companyName: buyer.companyName || "",
                businessType: buyer.businessType || "",
                country: buyer.country?.name || buyer.country || "",
                city: buyer.city || "",
                address: buyer.address || "",
                contactPerson: buyer.contactPerson || "",
                contactRole: buyer.contactRole || "",
                email: buyer.email || "",
                phone: buyer.phone || "",
                taxId: buyer.taxId || ""
            },
            modules: {
                esgRisk: Boolean(modulesForm.esg),
                weatherClimateRisk: Boolean(modulesForm.weather),
                portCongestionRisk: Boolean(modulesForm.portCongestion),
                carrierPerformance: Boolean(modulesForm.carrier),
                marketConditionScanner: Boolean(modulesForm.market),
                insuranceOptimization: Boolean(modulesForm.insurance)
            },
            routeLegs,
            kpi: {
                shipmentValue: Number(insurance.valueUsd || f.cargo_value || f.cargoValue || 0),
                transitDaysPlanned: transitDays,
                transitDaysProjected,
                onTimeProbability,
                carbonFootprint: carbonFootprintTons
            },
            risk: {
                overallScore: overallRisk,
                delayRisk,
                weatherRisk: regionalScores.weatherImpact,
                congestionRisk: regionalScores.congestionIndex
            },
            summary: {
                modules: activeModulesList
            }
        };
        
        if (window.RISKCAST_INPUT_CORE && window.RISKCAST_INPUT_CORE.recomputeDerivedState) {
            state = window.RISKCAST_INPUT_CORE.recomputeDerivedState(state);
        }
        
        return state;
    }
    
    /**
     * Calculate overall risk score
     * @returns {number} Risk score (0-100)
     */
    calculateOverallRisk() {
        const f = this.stateManager.getState();
        const reliability = Number(f.reliability || 0);
        const transitDays = Number(f.transitDays || 0);
        let risk = 0;
        
        if (transitDays > 30) risk += 25;
        else if (transitDays > 20) risk += 15;
        else if (transitDays > 10) risk += 8;
        
        if (reliability && reliability < 70) risk += 25;
        else if (reliability && reliability < 85) risk += 10;
        
        if (!f.carrier) risk += 5;
        if (!f.cargo?.cargoType) risk += 5;
        
        return Math.min(100, risk);
    }
    
    /**
     * Detect regional scores based on POD
     * @param {string} pod - Port of Discharge
     * @returns {Object} Regional scores
     */
    detectRegionalScores(pod) {
        // Simplified regional detection
        const podUpper = (pod || '').toUpperCase();
        
        let weatherImpact = 5.0;
        let congestionIndex = 5.0;
        
        // High congestion ports
        if (podUpper.includes('SINGAPORE') || podUpper.includes('ROTTERDAM') || podUpper.includes('SHANGHAI')) {
            congestionIndex = 7.5;
        }
        
        // High weather risk regions
        if (podUpper.includes('US') || podUpper.includes('JP') || podUpper.includes('KR')) {
            weatherImpact = 6.5;
        }
        
        return {
            weatherImpact,
            congestionIndex
        };
    }
    
    /**
     * Reset form
     */
    resetForm() {
        this.stateManager.reset();
        // Clear UI
        document.querySelectorAll('input, textarea, select').forEach(el => {
            if (el.type !== 'checkbox' && el.type !== 'radio') {
                el.value = '';
            }
        });
        console.log('🔄 Form reset');
    }
}

