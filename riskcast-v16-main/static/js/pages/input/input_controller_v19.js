/**
 * RISKCAST v19 Input Controller
 * Manages form data, validation, dropdowns, auto-suggestions, risk calculation, and UI updates
 */

// Global error handler to prevent crashes
window.addEventListener("error", e => {
    console.error("🔥 JS Runtime Error:", e.error);
});



class RiskcastInputController {

    constructor() {

        // Form data store

        this.formData = {

            // Section 1: Transport v20 (Dynamic from logistics_data.js)

            tradeLane: '',

            mode: '',

            serviceRoute: '',

            carrier: '',

            pol: '',

            pod: '',

            etd: '',

            schedule: '',

            transitDays: null,

            seasonality: null,

            eta: '',

            reliability: null,

            // Legacy fields (kept for compatibility)

            originPort: '',

            destinationPort: '',

            transportMode: '',

            routeCode: '',

            

            // Section 2: Cargo

            cargoType: '',

            cargoDescription: '',

            grossWeight: null,

            cargoVolume: null,

            insuranceValue: null,

            cargoSensitivity: 'standard',

            packingType: '',

            

            // Section 3: Seller

            sellerName: '',

            sellerCountry: '',

            sellerExperience: 'growing',

            incoterm: '',

            sellerContact: '',

            

            // Section 4: Buyer

            buyerName: '',

            buyerCountry: '',

            buyerSegment: '',

            buyerPriority: 'normal',

            buyerContact: '',

            

            // Section 5: Modules

            modules: {

                weather: true,

                congestion: true,

                geo: false,

                carrier: true,

                network: false

            },

            

            // Section 7: Packing List

            packingFileMeta: null

        };

        

        // UI state

        this.sections = [];

        this.activeDropdown = null;

        this.summaryUpdateTimeout = null;

        this.currentRiskScore = 0;

        

        // Logistics data reference

        this.logisticsData = null;

        // Port database for auto-suggestions (legacy, kept for compatibility)

        this.portDatabase = [

            { code: 'LAX', name: 'Los Angeles, US (LAX)', country: 'US' },

            { code: 'LGB', name: 'Long Beach, US (LGB)', country: 'US' },

            { code: 'CMIT', name: 'Cai Mep, VN (CMIT)', country: 'VN' },

            { code: 'CNSHA', name: 'Shanghai, CN (CNSHA)', country: 'CN' },

            { code: 'VNHPH', name: 'Hai Phong, VN (VNHPH)', country: 'VN' },

            { code: 'NLRTM', name: 'Rotterdam, NL (NLRTM)', country: 'NL' },

            { code: 'SGSIN', name: 'Singapore, SG (SGSIN)', country: 'SG' },

            { code: 'HKHKG', name: 'Hong Kong, HK (HKHKG)', country: 'HK' },

            { code: 'DEHAM', name: 'Hamburg, DE (DEHAM)', country: 'DE' },

            { code: 'USNYC', name: 'New York, US (USNYC)', country: 'US' },

            { code: 'JPTYO', name: 'Tokyo, JP (JPTYO)', country: 'JP' },

            { code: 'KRPUS', name: 'Busan, KR (KRPUS)', country: 'KR' },

            { code: 'AEDXB', name: 'Dubai, AE (AEDXB)', country: 'AE' },

            { code: 'GBLON', name: 'London, GB (GBLON)', country: 'GB' }

        ];

    }

    

    /**

     * Initialize all components

     */

    init() {

        console.log('🟦 RC19 Controller init()');

        

        // Load logistics data first

        this.loadLogisticsData();

        

        this.cacheDOMElements();

        this.initDropdowns();

        this.initPillGroups();

        this.initPortSuggestions();

        this.initInputHandlers();

        this.initModules();

        this.initPackingListUpload();

        this.initActionButtons();

        this.initSectionAnimations();

        this.initTransportV20();

    }

    

    /**

     * Cache DOM elements for performance

     */

    cacheDOMElements() {

        this.sections = document.querySelectorAll('.rc-section');

        this.progressBar = document.getElementById('rc-top-progress-bar');

        this.riskOrb = document.getElementById('rc-risk-orb');

        this.riskNeedle = document.getElementById('rc-risk-needle');

        this.riskScoreLabel = document.getElementById('rc-risk-score-label');

        this.riskBadge = document.getElementById('rc-risk-badge');

        this.riskNarrative = document.getElementById('rc-risk-narrative-text');

        

        // Metric displays

        this.metricTransit = document.getElementById('metric-transit');

        this.metricMode = document.getElementById('metric-mode');

        this.metricModules = document.getElementById('metric-modules');

        this.metricInsurance = document.getElementById('metric-insurance');

    }

    

    /**

     * Initialize custom dropdown components

     */

    initDropdowns() {

        const dropdowns = document.querySelectorAll(".rc-dropdown");

        console.log("🟣 initDropdowns:", dropdowns.length);

        

        dropdowns.forEach(dd => {

            const toggle = dd.querySelector(".rc-dropdown-toggle");

            const menu = dd.querySelector(".rc-dropdown-menu");

            const field = dd.dataset.field;

            

            if (!toggle || !menu || !field) {

                console.warn("⚠️ Dropdown missing parts:", dd);

                return;

            }

            

            // Open

            toggle.addEventListener("click", e => {

                e.stopPropagation();

                dd.classList.toggle("active");

            });

            

            // Select item

            menu.addEventListener("click", e => {

                const li = e.target.closest("li");

                if (!li) return;

                

                const value = li.dataset.value;

                if (!value) return;

                

                // Extract text content, ignoring icon SVG elements

                const clone = li.cloneNode(true);

                clone.querySelectorAll('svg, i').forEach(el => el.remove());

                const label = clone.textContent.trim().replace(/\s+/g, ' ');

                

                toggle.querySelector(".rc-dropdown-label").textContent = label;

                this.formData[field] = value;

                

                dd.classList.remove("active");

                console.log("✅ Dropdown:", field, "→", value);

                

                // Special handling for Transport v20 fields

                if (field === 'serviceRoute') {

                    this.updateAllTransportOutputs();

                } else if (field === 'tradeLane') {

                    this.formData.mode = '';

                    this.formData.serviceRoute = '';

                    this.formData.carrier = '';

                    this.formData.pol = '';

                    this.formData.pod = '';

                    setTimeout(() => {

                        this.loadModes();

                        this.loadPOL();

                        this.loadPOD();

                        this.updateAllTransportOutputs();

                    }, 50);

                } else if (field === 'mode') {

                    this.formData.serviceRoute = '';

                    this.formData.carrier = '';

                    setTimeout(() => {

                        this.loadServiceRoutes();

                        this.updateAllTransportOutputs();

                    }, 50);

                } else if (field === 'pol') {

                    this.formData.originPort = value;

                } else if (field === 'pod') {

                    this.formData.destinationPort = value;

                }

                

                this.onFormDataChange();

            });

        });

        

        // Close on outside click

        document.addEventListener("click", () => {

            dropdowns.forEach(d => d.classList.remove("active"));

        });

    }

    

    /**

     * Load logistics data from window.LOGISTICS_DATA

     */

    loadLogisticsData() {

        if (typeof window !== 'undefined' && window.LOGISTICS_DATA) {

            this.logisticsData = window.LOGISTICS_DATA;

            console.log('✅ LOGISTICS_DATA loaded');

            return true;

        } else {

            console.warn('⚠️ LOGISTICS_DATA not available. Retrying...');

            // Retry after a short delay

            setTimeout(() => {

                if (typeof window !== 'undefined' && window.LOGISTICS_DATA) {

                    this.logisticsData = window.LOGISTICS_DATA;

                    console.log('✅ LOGISTICS_DATA loaded on retry');

                    // Reload trade lanes if already initialized

                    if (document.getElementById('tradeLane-menu')) {

                        this.loadTradeLanes();

                    }

                } else {

                    console.error('❌ LOGISTICS_DATA still not available after retry');

                }

            }, 500);

            return false;

        }

    }

    

    /**

     * Initialize Transport v20 dynamic fields

     */

    initTransportV20() {

        // Wait for logistics data to be available

        let retryCount = 0;

        const maxRetries = 20; // 2 seconds max wait

        

        const checkAndInit = () => {

            if (typeof window !== 'undefined' && window.LOGISTICS_DATA) {

                this.logisticsData = window.LOGISTICS_DATA;

                console.log('✅ LOGISTICS_DATA loaded, initializing Transport v20');

                

                // Load initial trade lanes

                setTimeout(() => {

                    this.loadTradeLanes();

                    // Bind event listeners

                    this.bindTransportV20Events();

                }, 100);

            } else if (retryCount < maxRetries) {

                retryCount++;

                // Retry after 100ms

                setTimeout(checkAndInit, 100);

            } else {

                console.error('❌ LOGISTICS_DATA not available after max retries');

            }

        };

        

        checkAndInit();

    }

    

    /**

     * Load trade lanes from logistics_data.js

     */

    loadTradeLanes() {

        const menu = document.getElementById('tradeLane-menu');

        if (!menu) {

            console.warn('⚠️ tradeLane-menu not found');

            return;

        }

        

        if (!this.logisticsData) {

            console.warn('⚠️ LOGISTICS_DATA not available for loadTradeLanes');

            return;

        }

        

        menu.innerHTML = '';

        

        const routes = this.logisticsData.routes || {};

        const tradeLanes = Object.keys(routes).map(key => {

            const route = routes[key];

            return {

                id: key,

                name: route.name || key,

                name_vi: route.name_vi || route.name || key,

                flag: route.flag || ''

            };

        });

        

        if (tradeLanes.length === 0) {

            console.warn('⚠️ No trade lanes found in LOGISTICS_DATA');

            return;

        }

        

        tradeLanes.forEach(lane => {

            const li = document.createElement('li');

            li.setAttribute('role', 'option');

            li.setAttribute('data-value', lane.id);

            li.textContent = `${lane.flag} ${lane.name_vi || lane.name}`;

            menu.appendChild(li);

        });

        

        console.log(`✅ Loaded ${tradeLanes.length} trade lanes into menu`);

        console.log('Menu element:', menu);

        console.log('Menu items:', menu.querySelectorAll('li').length);

    }

    

    /**

     * Load modes for selected trade lane

     */

    loadModes() {

        const menu = document.getElementById('mode-menu');

        if (!menu || !this.logisticsData || !this.formData.tradeLane) return;

        

        menu.innerHTML = '';

        

        const route = this.logisticsData.getRoute(this.formData.tradeLane);

        if (!route || !route.transport_modes) return;

        

        // Extract unique mode types

        const modeMap = {

            'ocean_fcl': { label: 'Sea Freight', icon: 'ship' },

            'ocean_lcl': { label: 'Sea Freight', icon: 'ship' },

            'ocean_break_bulk': { label: 'Sea Freight', icon: 'ship' },

            'ocean_ro_ro': { label: 'Sea Freight', icon: 'ship' },

            'ocean_bulk': { label: 'Sea Freight', icon: 'ship' },

            'ocean_reefer': { label: 'Sea Freight', icon: 'ship' },

            'air_general': { label: 'Air Freight', icon: 'plane' },

            'air_dg': { label: 'Air Freight', icon: 'plane' },

            'air_perishable': { label: 'Air Freight', icon: 'plane' },

            'air_pharma': { label: 'Air Freight', icon: 'plane' },

            'road_ftl': { label: 'Road Transport', icon: 'truck' },

            'road_ltl': { label: 'Road Transport', icon: 'truck' },

            'road_container': { label: 'Road Transport', icon: 'truck' },

            'road_reefer': { label: 'Road Transport', icon: 'truck' },

            'road_heavy': { label: 'Road Transport', icon: 'truck' },

            'road_tank': { label: 'Road Transport', icon: 'truck' },

            'road_regular': { label: 'Road Transport', icon: 'truck' },

            'road_express': { label: 'Road Transport', icon: 'truck' },

            'rail_container': { label: 'Rail Freight', icon: 'train' },

            'rail_bulk': { label: 'Rail Freight', icon: 'train' },

            'rail_reefer': { label: 'Rail Freight', icon: 'train' },

            'rail_lcl': { label: 'Rail Freight', icon: 'train' },

            'rail_heavy': { label: 'Rail Freight', icon: 'train' },

            'rail_passenger': { label: 'Rail Freight', icon: 'train' },

            'rail_china_europe': { label: 'Rail Freight', icon: 'train' }

        };

        

        const availableModes = new Set();

        route.transport_modes.forEach(mode => {

            const modeType = mode.value.split('_')[0]; // Extract 'ocean', 'air', 'road', 'rail'

            if (modeType === 'ocean') availableModes.add('SEA');

            else if (modeType === 'air') availableModes.add('AIR');

            else if (modeType === 'road') availableModes.add('ROAD');

            else if (modeType === 'rail') availableModes.add('RAIL');

        });

        

        const modeLabels = {

            'SEA': { label: 'Sea Freight', icon: 'ship' },

            'AIR': { label: 'Air Freight', icon: 'plane' },

            'ROAD': { label: 'Road Transport', icon: 'truck' },

            'RAIL': { label: 'Rail Freight', icon: 'train' }

        };

        

        Array.from(availableModes).sort().forEach(mode => {

            const li = document.createElement('li');

            li.setAttribute('role', 'option');

            li.setAttribute('data-value', mode);

            const modeInfo = modeLabels[mode];

            li.innerHTML = `<i data-lucide="${modeInfo.icon}" width="18" height="18"></i> ${modeInfo.label}`;

            menu.appendChild(li);

        });

        

        // Reinitialize Lucide icons

        if (typeof lucide !== 'undefined') {

            lucide.createIcons();

        }

        

        console.log(`✅ Loaded ${availableModes.size} transport modes for trade lane: ${this.formData.tradeLane}`);

    }

    

    /**

     * Load service routes for selected trade lane + mode

     */

    loadServiceRoutes() {

        const menu = document.getElementById('serviceRoute-menu');

        if (!menu || !this.logisticsData || !this.formData.tradeLane || !this.formData.mode) return;

        

        menu.innerHTML = '';

        

        const route = this.logisticsData.getRoute(this.formData.tradeLane);

        if (!route || !route.transport_modes) return;

        

        // Map mode to transport mode value prefix

        const modePrefix = {

            'SEA': 'ocean',

            'AIR': 'air',

            'ROAD': 'road',

            'RAIL': 'rail'

        }[this.formData.mode];

        

        if (!modePrefix) return;

        

        // Find matching transport modes

        const matchingModes = route.transport_modes.filter(mode => 

            mode.value.startsWith(modePrefix)

        );

        

        matchingModes.forEach(mode => {

            if (mode.routes && mode.routes.length > 0) {

                mode.routes.forEach(routeOption => {

                    const li = document.createElement('li');

                    li.setAttribute('role', 'option');

                    // Extract schedule from mode or default based on mode type

                    let schedule = 'Weekly';

                    // Try to infer schedule from mode label or default

                    if (mode.label && mode.label.includes('Weekly')) {

                        schedule = 'Weekly';

                    } else if (mode.label && mode.label.includes('Daily')) {

                        schedule = 'Daily';

                    } else {

                        // Default based on mode type

                        if (modePrefix === 'ocean') schedule = 'Weekly';

                        else if (modePrefix === 'air') schedule = 'Daily';

                        else if (modePrefix === 'road') schedule = 'Daily';

                        else if (modePrefix === 'rail') schedule = 'Weekly';

                    }

                    

                    // Extract transit time (prefer days, fallback to hours)

                    let transit = 0;

                    if (routeOption.days) {

                        // If days is a range like "18-22", take average

                        if (typeof routeOption.days === 'string' && routeOption.days.includes('-')) {

                            const parts = routeOption.days.split('-').map(s => parseInt(s.trim()));

                            transit = Math.round(parts.reduce((a, b) => a + b, 0) / parts.length);

                        } else {

                            transit = parseInt(routeOption.days) || 0;

                        }

                    } else if (routeOption.hours) {

                        // Convert hours to days (round up)

                        transit = Math.ceil(parseInt(routeOption.hours) / 24);

                    }

                    

                    li.setAttribute('data-value', JSON.stringify({

                        code: routeOption.pol_code + '-' + routeOption.pod_code,

                        name: `${routeOption.pol} → ${routeOption.pod}`,

                        carrier: this.extractCarrierFromRoute(routeOption, this.formData.tradeLane),

                        schedule: schedule,

                        transit: transit,

                        pol: routeOption.pol,

                        pol_code: routeOption.pol_code,

                        pod: routeOption.pod,

                        pod_code: routeOption.pod_code

                    }));

                    li.textContent = `${routeOption.pol_code}-${routeOption.pod_code} – ${routeOption.pol} → ${routeOption.pod}`;

                    menu.appendChild(li);

                });

            }

        });

        

        console.log(`✅ Loaded ${matchingModes.reduce((sum, m) => sum + (m.routes ? m.routes.length : 0), 0)} service routes`);

    }

    

    /**

     * Extract carrier from route data

     */

    extractCarrierFromRoute(routeOption, tradeLane) {

        // Try to get carrier from carrierRatings

        const carriers = this.logisticsData.getCarrierRatings(tradeLane);

        if (carriers && carriers.length > 0) {

            // Use first carrier as default, or try to match by route

            return carriers[0].name;

        }

        return 'N/A';

    }

    

    /**

     * Load POL (Port of Loading) based on trade lane origin

     */

    loadPOL() {

        const menu = document.getElementById('pol-menu');

        if (!menu || !this.logisticsData || !this.formData.tradeLane) return;

        

        menu.innerHTML = '';

        

        const route = this.logisticsData.getRoute(this.formData.tradeLane);

        if (!route || !route.transport_modes) return;

        

        // Extract unique POLs from all routes

        const pols = new Set();

        route.transport_modes.forEach(mode => {

            if (mode.routes) {

                mode.routes.forEach(r => {

                    if (r.pol && r.pol_code) {

                        pols.add(JSON.stringify({ pol: r.pol, pol_code: r.pol_code }));

                    }

                });

            }

        });

        

        Array.from(pols).forEach(polStr => {

            const pol = JSON.parse(polStr);

            const li = document.createElement('li');

            li.setAttribute('role', 'option');

            li.setAttribute('data-value', pol.pol_code);

            li.textContent = `${pol.pol} (${pol.pol_code})`;

            menu.appendChild(li);

        });

    }

    

    /**

     * Load POD (Port of Discharge) based on trade lane destination

     */

    loadPOD() {

        const menu = document.getElementById('pod-menu');

        if (!menu || !this.logisticsData || !this.formData.tradeLane) return;

        

        menu.innerHTML = '';

        

        const route = this.logisticsData.getRoute(this.formData.tradeLane);

        if (!route || !route.transport_modes) return;

        

        // Extract unique PODs from all routes

        const pods = new Set();

        route.transport_modes.forEach(mode => {

            if (mode.routes) {

                mode.routes.forEach(r => {

                    if (r.pod && r.pod_code) {

                        pods.add(JSON.stringify({ pod: r.pod, pod_code: r.pod_code }));

                    }

                });

            }

        });

        

        Array.from(pods).forEach(podStr => {

            const pod = JSON.parse(podStr);

            const li = document.createElement('li');

            li.setAttribute('role', 'option');

            li.setAttribute('data-value', pod.pod_code);

            li.textContent = `${pod.pod} (${pod.pod_code})`;

            menu.appendChild(li);

        });

    }

    

    /**

     * Update carrier from selected service route

     */

    updateCarrier() {

        const carrierInput = document.getElementById('carrier');

        if (!carrierInput) return;

        

        if (this.formData.serviceRoute) {

            try {

                const routeData = JSON.parse(this.formData.serviceRoute);

                this.formData.carrier = routeData.carrier || '';

                carrierInput.value = this.formData.carrier;

            } catch (e) {

                console.error('Error parsing service route:', e);

            }

        } else {

            this.formData.carrier = '';

            carrierInput.value = '';

        }

    }

    

    /**

     * Update schedule from service route

     */

    updateSchedule() {

        const scheduleInput = document.getElementById('schedule');

        if (!scheduleInput) return;

        

        if (this.formData.serviceRoute) {

            try {

                const routeData = JSON.parse(this.formData.serviceRoute);

                this.formData.schedule = routeData.schedule || '';

                scheduleInput.value = this.formData.schedule;

            } catch (e) {

                console.error('Error parsing service route:', e);

            }

        } else {

            this.formData.schedule = '';

            scheduleInput.value = '';

        }

    }

    

    /**

     * Update transit days from service route

     */

    updateTransit() {

        const transitInput = document.getElementById('transitDays');

        if (!transitInput) return;

        

        if (this.formData.serviceRoute) {

            try {

                const routeData = JSON.parse(this.formData.serviceRoute);

                // Extract transit days (could be days or hours)

                let transit = routeData.transit || null;

                if (transit) {

                    // If it's a string like "18-22", take the average or first number

                    if (typeof transit === 'string' && transit.includes('-')) {

                        const parts = transit.split('-').map(s => parseInt(s.trim()));

                        transit = Math.round(parts.reduce((a, b) => a + b, 0) / parts.length);

                    } else if (typeof transit === 'string') {

                        transit = parseInt(transit);

                    }

                    this.formData.transitDays = transit;

                    transitInput.value = `${transit} days`;

                } else {

                    this.formData.transitDays = null;

                    transitInput.value = '';

                }

            } catch (e) {

                console.error('Error parsing service route:', e);

                this.formData.transitDays = null;

                transitInput.value = '';

            }

        } else {

            this.formData.transitDays = null;

            transitInput.value = '';

        }

    }

    

    /**

     * Calculate and update seasonality index based on ETD month

     */

    updateSeasonality() {

        const seasonalityInput = document.getElementById('seasonality');

        if (!seasonalityInput) return;

        

        if (!this.formData.etd) {

            this.formData.seasonality = null;

            seasonalityInput.value = '';

            return;

        }

        

        const etdDate = new Date(this.formData.etd);

        const month = etdDate.getMonth() + 1; // 1-12

        

        // Seasonality calculation: Q1 (1-3) = 3, Q3 (7-9) = 5, else = 0

        let seasonality = 0;

        if ([1, 2, 3].includes(month)) {

            seasonality = 3;

        } else if ([7, 8, 9].includes(month)) {

            seasonality = 5;

        }

        

        this.formData.seasonality = seasonality;

        seasonalityInput.value = seasonality.toString();

    }

    

    /**

     * Calculate and update ETA: ETD + Transit + Seasonality

     */

    updateETA() {

        const etaInput = document.getElementById('eta');

        if (!etaInput) return;

        

        if (!this.formData.etd || !this.formData.transitDays) {

            this.formData.eta = '';

            etaInput.value = '';

            return;

        }

        

        const etdDate = new Date(this.formData.etd);

        const transitDays = parseInt(this.formData.transitDays) || 0;

        const seasonality = this.formData.seasonality || 0;

        

        const totalDays = transitDays + seasonality;

        const etaDate = new Date(etdDate);

        etaDate.setDate(etaDate.getDate() + totalDays);

        

        this.formData.eta = etaDate.toISOString().split('T')[0];

        etaInput.value = etaDate.toLocaleDateString('en-US', { 

            year: 'numeric', 

            month: 'short', 

            day: 'numeric' 

        });

    }

    

    /**

     * Calculate and update reliability: Carrier reliability - seasonality

     */

    updateReliability() {

        const reliabilityInput = document.getElementById('reliability');

        if (!reliabilityInput) return;

        

        if (!this.formData.carrier || !this.formData.tradeLane) {

            this.formData.reliability = null;

            reliabilityInput.value = '';

            return;

        }

        

        // Get carrier reliability from carrierRatings

        const carriers = this.logisticsData.getCarrierRatings(this.formData.tradeLane);

        const carrier = carriers.find(c => c.name === this.formData.carrier);

        

        if (!carrier) {

            this.formData.reliability = null;

            reliabilityInput.value = '';

            return;

        }

        

        const baseReliability = carrier.ontime || carrier.rating * 20; // Convert rating to percentage

        const seasonality = this.formData.seasonality || 0;

        const reliability = Math.max(0, Math.min(100, baseReliability - seasonality));

        

        this.formData.reliability = reliability;

        reliabilityInput.value = `${reliability.toFixed(1)}%`;

    }

    

    /**

     * Update all transport outputs when any field changes

     */

    updateAllTransportOutputs() {

        this.updateCarrier();

        this.updateSchedule();

        this.updateTransit();

        this.updateSeasonality();

        this.updateETA();

        this.updateReliability();

    }

    

    /**

     * Bind event listeners for Transport v20 fields

     */

    bindTransportV20Events() {

        // ETD change → update seasonality, ETA, reliability

        const etdInput = document.getElementById('etd');

        if (etdInput) {

            etdInput.addEventListener('change', () => {

                this.formData.etd = etdInput.value;

                this.updateSeasonality();

                this.updateETA();

                this.updateReliability();

                this.onFormDataChange();

            });

        }

    }

    

    /**

     * Initialize pill group selectors

     */

    initPillGroups() {

        const pills = document.querySelectorAll(".rc-pill-option");

        console.log("🟠 initPillGroups:", pills.length);

        

        pills.forEach(pill => {

            pill.addEventListener("click", () => {

                const field = pill.dataset.field;

                const value = pill.dataset.value;

                

                if (!field || !value) return;

                

                pill.parentElement.querySelectorAll(".rc-pill-option")

                    .forEach(p => p.classList.remove("active"));

                

                pill.classList.add("active");

                

                this.formData[field] = value;

                

                console.log("✅ Pill:", field, "→", value);

                this.onFormDataChange();

            });

        });

    }

    

    /**

     * Initialize port auto-suggestions

     */

    initPortSuggestions() {

        this.initPortField('originPort');

        this.initPortField('destinationPort');

    }

    

    initPortField(fieldId) {

        const input = document.getElementById(fieldId);

        const dropdown = document.getElementById(`${fieldId}-suggest`);

        

        if (!input || !dropdown) return;

        

        input.addEventListener("input", () => {

            const q = input.value.trim().toLowerCase();

            if (q.length < 2) {

                dropdown.classList.remove("active");

                return;

            }

            

            const matched = this.portDatabase.filter(p =>

                (p.code + " " + p.name).toLowerCase().includes(q)

            );

            

            if (!matched.length) return dropdown.classList.remove("active");

            

            dropdown.innerHTML = matched.slice(0, 8).map(p =>

                `<div class="rc-suggest-item" data-value="${p.name}">${p.name}</div>`

            ).join("");

            

            dropdown.classList.add("active");

        });

        

        dropdown.addEventListener("mousedown", e => {

            const item = e.target.closest(".rc-suggest-item");

            if (!item) return;

            

            input.value = item.dataset.value;

            this.formData[fieldId] = item.dataset.value;

            

            dropdown.classList.remove("active");

            this.onFormDataChange();

        });

        

        input.addEventListener("blur", () => {

            setTimeout(() => dropdown.classList.remove("active"), 150);

        });

    }

    

    /**

     * Initialize input field handlers

     */

    initInputHandlers() {

        // Text inputs

        const textInputs = ['routeCode', 'cargoDescription', 'sellerName', 'sellerCountry', 

                           'sellerContact', 'buyerName', 'buyerCountry', 'buyerContact'];

        

        textInputs.forEach(id => {

            const input = document.getElementById(id);

            if (input) {

                input.addEventListener('blur', () => {

                    this.formData[id] = input.value.trim();

                    this.onFormDataChange();

                });

            }

        });

        

        // Number inputs

        const numberFields = ["transitDays", "grossWeight", "cargoVolume", "insuranceValue"];

        

        numberFields.forEach(id => {

            const input = document.getElementById(id);

            if (!input) return;

            

            // Skip if readonly (v20 fields)

            if (input.readOnly) return;

            

            input.addEventListener("input", () => {

                const value = parseFloat(input.value);

                this.formData[id] = isNaN(value) ? null : value;

                this.debouncedUpdate();

            });

        });

    }

    

    /**

     * Initialize algorithm modules toggles

     */

    initModules() {

        const toggles = document.querySelectorAll("[data-module]");

        toggles.forEach(t => {

            const name = t.dataset.module;

            if (!name) return;

            

            t.checked = this.formData.modules[name];

            

            t.addEventListener("change", () => {

                this.formData.modules[name] = t.checked;

                console.log("🟢 Module:", name, "=", t.checked);

                this.onFormDataChange();

            });

        });

    }

    

    /**

     * Initialize packing list upload (drag & drop)

     */

    initPackingListUpload() {

        const dropzone = document.getElementById('rc-packing-dropzone');

        const fileInput = document.getElementById('rc-packing-file-input');

        const fileInfo = document.getElementById('rc-packing-file-info');

        

        if (!dropzone || !fileInput) return;

        

        // Click to upload

        dropzone.addEventListener('click', () => {

            fileInput.click();

        });

        

        // File selected

        fileInput.addEventListener('change', (e) => {

            if (e.target.files.length > 0) {

                this.handlePackingFile(e.target.files[0], fileInfo);

            }

        });

        

        // Drag over

        dropzone.addEventListener('dragover', (e) => {

            e.preventDefault();

            dropzone.classList.add('rc-dropzone-hover');

        });

        

        // Drag leave

        dropzone.addEventListener('dragleave', () => {

            dropzone.classList.remove('rc-dropzone-hover');

        });

        

        // Drop

        dropzone.addEventListener('drop', (e) => {

            e.preventDefault();

            dropzone.classList.remove('rc-dropzone-hover');

            

            if (e.dataTransfer.files.length > 0) {

                this.handlePackingFile(e.dataTransfer.files[0], fileInfo);

            }

        });

    }

    

    /**

     * Handle packing list file upload

     */

    handlePackingFile(file, fileInfoElement) {

        if (!fileInfoElement) return;

        

        const maxSize = 10 * 1024 * 1024; // 10MB

        

        if (file.size > maxSize) {

            this.showToast('File too large. Maximum 10MB allowed.');

            return;

        }

        

        const extension = file.name.split('.').pop().toLowerCase();

        

        if (!['csv', 'xls', 'xlsx'].includes(extension)) {

            this.showToast('Invalid file type. Please upload .csv, .xls, or .xlsx');

            return;

        }

        

        // Store metadata

        this.formData.packingFileMeta = {

            name: file.name,

            size: file.size,

            type: file.type,

            extension: extension

        };

        

        // Display file info

        const sizeKB = (file.size / 1024).toFixed(2);

        let infoHTML = `

            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">

                <i data-lucide="file-text" width="24" height="24" style="color: var(--rc-neon-primary);"></i>

                <div style="flex: 1;">

                    <div style="font-weight: 600; color: var(--rc-text-primary);">${file.name}</div>

                    <div style="font-size: 0.875rem; color: var(--rc-text-secondary);">${sizeKB} KB</div>

                </div>

            </div>

        `;

        

        // Parse CSV preview

        if (extension === 'csv') {

            const reader = new FileReader();

            reader.onload = (e) => {

                const text = e.target.result;

                const lines = text.split('\n').filter(line => line.trim());

                const rowCount = lines.length - 1; // Exclude header

                

                // Preview first 3 data rows

                const preview = lines.slice(0, 4).map(line => {

                    const cols = line.split(',').slice(0, 3); // First 3 columns

                    return cols.map(c => c.trim().substring(0, 30)).join(' | ');

                }).join('\n');

                

                this.formData.packingFileMeta.rowCount = rowCount;

                this.formData.packingFileMeta.preview = preview;

                

                infoHTML += `

                    <div style="margin-top: 0.75rem; padding: 0.75rem; background: var(--rc-bg-glass); border-radius: 8px;">

                        <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--rc-text-primary);">

                            CSV Preview (${rowCount} rows detected)

                        </div>

                        <pre style="font-size: 0.75rem; color: var(--rc-text-secondary); overflow-x: auto; margin: 0;">${preview}</pre>

                    </div>

                `;

                

                fileInfoElement.innerHTML = infoHTML;

                fileInfoElement.classList.add('active');

                if (typeof lucide !== 'undefined') {

                    lucide.createIcons();

                }

            };

            reader.readAsText(file);

        } else {

            // Excel file

            infoHTML += `

                <div style="margin-top: 0.75rem; padding: 0.75rem; background: var(--rc-bg-glass); border-radius: 8px; color: var(--rc-text-secondary); font-size: 0.875rem;">

                    Excel file detected. Parsing will be handled by backend.

                </div>

            `;

            fileInfoElement.innerHTML = infoHTML;

            fileInfoElement.classList.add('active');

            if (typeof lucide !== 'undefined') {

                lucide.createIcons();

            }

        }

        

        this.showToast('File uploaded successfully');

    }

    

    /**

     * Initialize action buttons

     */

    initActionButtons() {

        const resetBtn = document.getElementById('rc-btn-reset');

        const analyzeBtn = document.getElementById('rc-btn-analyze');

        

        if (resetBtn) {

            resetBtn.addEventListener('click', () => {

                if (confirm('Are you sure you want to reset all form data?')) {

                    this.resetForm();

                }

            });

        }

        

        if (analyzeBtn) {

            analyzeBtn.addEventListener('click', () => {

                this.analyzeRisk();

            });

        }

    }

    

    /**

     * Initialize section fade-in animations

     */

    initSectionAnimations() {

        // Sections already have rc-fade-in-up class, CSS animation will handle it

        // Just ensure they're visible after a short delay to trigger animation

        setTimeout(() => {

            this.sections.forEach((section, index) => {

                if (section && section.classList.contains('rc-fade-in-up')) {

                    // Force reflow to trigger animation

                    void section.offsetHeight;

                }

            });

        }, 50);

    }

    

    /**

     * Debounced update for number inputs

     */

    debouncedUpdate() {

        clearTimeout(this.summaryUpdateTimeout);

        this.summaryUpdateTimeout = setTimeout(() => {

            this.onFormDataChange();

        }, 300);

    }

    

    /**

     * Called when form data changes

     */

    onFormDataChange() {

        this.calculateRiskScore();

        this.updateRiskVisuals();

        this.updateSummary();

        this.updateProgress();

        // Persist current input state for Summary v100
        this.persistStateForSummary();

    }

    

    /**

     * Calculate risk score (0-100)

     */

    calculateRiskScore() {

        let score = 10; // Base score

        

        // Transit days impact

        if (this.formData.transitDays) {

            score += this.formData.transitDays * 0.7;

        }

        

        // Insurance value impact

        if (this.formData.insuranceValue) {

            score += Math.min(this.formData.insuranceValue / 100000, 20);

        }

        

        // Cargo type impact

        const highRiskCargo = ['electronics', 'pharma', 'chemical'];

        if (highRiskCargo.includes(this.formData.cargoType)) {

            score += 10;

        }

        

        // Cargo sensitivity impact

        if (this.formData.cargoSensitivity === 'fragile') {

            score += 8;

        } else if (this.formData.cargoSensitivity === 'temperature') {

            score += 5;

        }

        

        // Seller experience impact

        if (this.formData.sellerExperience === 'new') {

            score += 5;

        } else if (this.formData.sellerExperience === 'experienced') {

            score -= 2;

        }

        

        // Modules impact

        const modulesOn = Object.values(this.formData.modules).filter(v => v).length;

        score += modulesOn * 5;

        

        // Clamp between 0-100

        this.currentRiskScore = Math.max(0, Math.min(100, Math.round(score)));

        

        return this.currentRiskScore;

    }

    

    /**

     * Update risk visuals (orb and gauge)

     */

    updateRiskVisuals() {

        const score = this.currentRiskScore;

        

        // Update orb

        if (this.riskOrb) {

            this.riskOrb.classList.remove('rc-risk-orb-low', 'rc-risk-orb-medium', 'rc-risk-orb-high');

            

            if (score <= 30) {

                this.riskOrb.classList.add('rc-risk-orb-low');

            } else if (score <= 60) {

                this.riskOrb.classList.add('rc-risk-orb-medium');

            } else {

                this.riskOrb.classList.add('rc-risk-orb-high');

            }

        }

        

        // Update gauge needle (map 0-100 to -90deg to +90deg)

        if (this.riskNeedle) {

            const angle = -90 + (score / 100) * 180;

            this.riskNeedle.setAttribute('transform', `rotate(${angle} 100 100)`);

        }

        

        // Update score label

        if (this.riskScoreLabel) {

            this.riskScoreLabel.textContent = `Risk Score: ${score} / 100`;

        }

        

        // Update badge

        if (this.riskBadge) {

            this.riskBadge.classList.remove('rc-risk-badge-low', 'rc-risk-badge-medium', 'rc-risk-badge-high');

            

            if (score <= 30) {

                this.riskBadge.classList.add('rc-risk-badge-low');

                this.riskBadge.textContent = 'Low Risk';

            } else if (score <= 60) {

                this.riskBadge.classList.add('rc-risk-badge-medium');

                this.riskBadge.textContent = 'Moderate Risk';

            } else {

                this.riskBadge.classList.add('rc-risk-badge-high');

                this.riskBadge.textContent = 'High Risk';

            }

        }

    }

    

    /**

     * Update summary section

     */

    updateSummary() {

        // Update metrics - Use v20 fields if available, fallback to legacy

        if (this.metricTransit) {

            const transit = this.formData.transitDays || (this.formData.transitDays ? this.formData.transitDays : null);

            this.metricTransit.textContent = transit 

                ? `${transit} days` 

                : '—';

        }

        

        if (this.metricMode) {

            // Use v20 mode if available, fallback to legacy transportMode

            let modeText = '—';

            if (this.formData.mode) {

                const modeMap = {

                    'SEA': 'Sea Freight',

                    'AIR': 'Air Freight',

                    'ROAD': 'Road Transport',

                    'RAIL': 'Rail Freight'

                };

                modeText = modeMap[this.formData.mode] || this.formData.mode;

            } else if (this.formData.transportMode) {

                const modeMap = {

                    sea: 'Sea Freight',

                    air: 'Air Freight',

                    road: 'Road Transport',

                    rail: 'Rail Freight',

                    multimodal: 'Multimodal'

                };

                modeText = modeMap[this.formData.transportMode] || '—';

            }

            this.metricMode.textContent = modeText;

        }

        

        if (this.metricModules) {

            const count = Object.values(this.formData.modules).filter(v => v).length;

            this.metricModules.textContent = `${count} / 5`;

        }

        

        if (this.metricInsurance) {

            this.metricInsurance.textContent = this.formData.insuranceValue 

                ? `$${this.formData.insuranceValue.toLocaleString()}` 

                : '—';

        }

        

        // Update narrative

        this.updateRiskNarrative();

    }

    

    /**

     * Generate risk narrative text

     */

    updateRiskNarrative() {

        if (!this.riskNarrative) return;

        

        const score = this.currentRiskScore;

        // Use v20 fields if available, fallback to legacy

        const pol = this.formData.pol || this.formData.originPort || '';

        const pod = this.formData.pod || this.formData.destinationPort || '';

        const mode = this.formData.mode || this.formData.transportMode || '';

        const transitDays = this.formData.transitDays || null;

        const eta = this.formData.eta || '';

        const reliability = this.formData.reliability || null;

        const { cargoType, modules } = this.formData;

        

        let narrative = '';

        

        if (!pol || !pod || !mode) {

            narrative = 'Configure your shipment details above to see a comprehensive risk analysis. The AI will analyze your route, cargo type, timing, and enabled modules to provide actionable insights.';

        } else {

            const modeText = {

                'SEA': 'sea freight',

                'AIR': 'air freight',

                'ROAD': 'road transport',

                'RAIL': 'rail freight',

                sea: 'sea freight',

                air: 'air freight',

                road: 'road transport',

                rail: 'rail freight',

                multimodal: 'multimodal transport'

            }[mode] || 'transport';

            

            const modulesOn = Object.entries(modules).filter(([k, v]) => v).map(([k]) => k);

            

            if (score <= 30) {

                narrative = `Your ${modeText} shipment from ${pol} to ${pod} shows <strong>low risk</strong>. `;

                narrative += transitDays ? `With ${transitDays} days transit time, ` : '';

                if (eta) {

                    narrative += `Expected arrival: ${eta}. `;

                }

                if (reliability) {

                    narrative += `Carrier reliability: ${reliability.toFixed(1)}%. `;

                }

                narrative += 'Standard precautions should be sufficient. ';

                if (modulesOn.length > 0) {

                    narrative += `Active risk modules (${modulesOn.join(', ')}) are monitoring for any changes.`;

                }

            } else if (score <= 60) {

                narrative = `Your ${modeText} shipment from ${pol} to ${pod} shows <strong>moderate risk</strong>. `;

                if (transitDays && transitDays > 20) {

                    narrative += `The ${transitDays}-day transit time increases exposure to delays. `;

                }

                if (eta) {

                    narrative += `Expected arrival: ${eta}. `;

                }

                if (reliability) {

                    narrative += `Carrier reliability: ${reliability.toFixed(1)}%. `;

                }

                if (cargoType === 'electronics' || cargoType === 'pharma') {

                    narrative += 'High-value/sensitive cargo requires extra attention. ';

                }

                narrative += 'Consider additional insurance coverage and tracking. ';

                if (modules.weather && transitDays > 15) {

                    narrative += 'Weather module recommends monitoring seasonal patterns for this route.';

                }

            } else {

                narrative = `Your ${modeText} shipment from ${pol} to ${pod} shows <strong>high risk</strong>. `;

                if (transitDays && transitDays > 30) {

                    narrative += `Extended ${transitDays}-day transit significantly increases risk exposure. `;

                }

                if (eta) {

                    narrative += `Expected arrival: ${eta}. `;

                }

                if (reliability) {

                    narrative += `Carrier reliability: ${reliability.toFixed(1)}%. `;

                }

                if (cargoType === 'pharma' || cargoType === 'chemical') {

                    narrative += 'Specialized cargo requires stringent handling protocols. ';

                }

                narrative += '<strong>Recommendations:</strong> Increase insurance coverage, add real-time tracking, consider expedited routing. ';

                if (modulesOn.length < 3) {

                    narrative += 'Enable more risk modules for comprehensive monitoring.';

                }

            }

        }

        

        this.riskNarrative.innerHTML = narrative;

    }

    

    /**

     * Update progress bar

     */

    updateProgress() {

        if (!this.progressBar) return;

        

        // Calculate completion percentage

        const required = ['originPort', 'destinationPort', 'transportMode', 'transitDays', 

                         'cargoType', 'grossWeight', 'insuranceValue', 'packingType',

                         'sellerName', 'sellerCountry', 'incoterm'];

        

        const filled = required.filter(field => {

            const value = this.formData[field];

            return value !== null && value !== '' && value !== undefined;

        }).length;

        

        const percentage = (filled / required.length) * 100;

        

        this.progressBar.style.width = `${percentage}%`;

    }

    /**
     * Persist current form data into localStorage as RISKCAST_STATE
     * mapped to Summary v100 expected schema.
     */
    persistStateForSummary() {
        try {
            const f = this.formData || {};
            const state = {
                trade_route: {
                    trade_lane: f.tradeLane || f.routeCode || '',
                    mode_of_transport: f.mode || f.transportMode || '',
                    mode: f.mode || f.transportMode || '',
                    service_route: f.serviceRoute || '',
                    carrier: f.carrier || f.vessel || '',
                    pol: f.pol || f.originPort || '',
                    pod: f.pod || f.destinationPort || '',
                    incoterm: f.incoterm || '',
                    container_type: f.containerType || f.container_type || '',
                    etd: f.etd || '',
                    transit_time: f.transitDays || f.transit_time || '',
                    eta: f.eta || '',
                    priority: f.buyerPriority || f.priority || 'Balanced',
                    schedule_frequency: f.schedule || '',
                    reliability_score: f.reliability || ''
                },
                cargo_packing: {
                    cargo_type: f.cargoType || '',
                    hs_code: f.hs_code || '',
                    packing_type: f.packingType || '',
                    number_of_packages: f.packages || f.number_of_packages || '',
                    gross_weight: f.grossWeight || f.gross_weight_kg || '',
                    net_weight: f.net_weight_kg || '',
                    volume_cbm: f.cargoVolume || f.volume_cbm || '',
                    stackability: f.stackability || 'Yes',
                    dangerous_goods: f.dangerous_goods || 'No',
                    insurance_value_usd: f.insuranceValue || '',
                    cargo_sensitivity: f.cargoSensitivity || '',
                    cargo_description: f.cargoDescription || f.cargo_desc || '',
                    special_handling: f.specialHandling || ''
                },
                seller: {
                    company_name: f.sellerName || '',
                    country: f.sellerCountry || '',
                    contact_person: f.sellerContact || '',
                    business_type: f.sellerExperience || '',
                    address: f.sellerAddress || ''
                },
                buyer: {
                    company_name: f.buyerName || '',
                    country: f.buyerCountry || '',
                    contact_person: f.buyerContact || '',
                    business_type: f.buyerSegment || '',
                    address: f.buyerAddress || ''
                },
                risk_modules: {
                    weather_climate: f.modules ? !!f.modules.weather : true,
                    port_congestion: f.modules ? !!f.modules.congestion : true,
                    carrier_performance: f.modules ? !!f.modules.carrier : true,
                    market_scanner: f.modules ? !!f.modules.network : false,
                    esg_risk: false,
                    insurance_optimization: false
                }
            };
            localStorage.setItem('RISKCAST_STATE', JSON.stringify(state));
        } catch (err) {
            console.warn('Failed to persist RISKCAST_STATE', err);
        }
    }

    

    /**

     * Reset form

     */

    resetForm() {

        // Reset form data

        Object.keys(this.formData).forEach(key => {

            if (key === 'modules') {

                this.formData.modules = {

                    weather: true,

                    congestion: true,

                    geo: false,

                    carrier: true,

                    network: false

                };

            } else if (key === 'cargoSensitivity') {

                this.formData[key] = 'standard';

            } else if (key === 'sellerExperience') {

                this.formData[key] = 'growing';

            } else if (key === 'buyerPriority') {

                this.formData[key] = 'normal';

            } else {

                this.formData[key] = typeof this.formData[key] === 'number' ? null : '';

            }

        });

        

        // Reset UI

        document.querySelectorAll('input[type="text"], input[type="number"], textarea').forEach(input => {

            input.value = '';

        });

        

        // Reset dropdown labels

        document.querySelectorAll('.rc-dropdown').forEach(dropdown => {

            const toggle = dropdown.querySelector('.rc-dropdown-toggle');

            const label = toggle ? toggle.querySelector('.rc-dropdown-label') : null;

            if (label) {

                const field = dropdown.dataset.field;

                if (field === 'transportMode') {

                    label.textContent = 'Select transport mode';

                } else if (field === 'cargoType') {

                    label.textContent = 'Select cargo type';

                } else if (field === 'packingType') {

                    label.textContent = 'Select packing type';

                } else if (field === 'incoterm') {

                    label.textContent = 'Select incoterm';

                } else if (field === 'buyerSegment') {

                    label.textContent = 'Select buyer segment';

                } else {

                    label.textContent = 'Select option';

                }

            }

        });

        

        // Reset pills

        document.querySelectorAll('.rc-pill-option').forEach(pill => {

            pill.classList.remove('active');

            if (pill.dataset.value === 'standard' || pill.dataset.value === 'growing' || pill.dataset.value === 'normal') {

                pill.classList.add('active');

            }

        });

        

        // Reset modules

        document.querySelectorAll('input[type="checkbox"][data-module]').forEach(checkbox => {

            const moduleName = checkbox.dataset.module;

            if (moduleName && this.formData.modules[moduleName] !== undefined) {

                checkbox.checked = this.formData.modules[moduleName];

            }

        });

        

        // Reset file info

        const fileInfo = document.getElementById('rc-packing-file-info');

        if (fileInfo) {

            fileInfo.classList.remove('active');

            fileInfo.innerHTML = '';

        }

        

        this.onFormDataChange();

        this.showToast('Form reset successfully');

    }

    

    /**

     * Analyze risk (button action)

     */

    analyzeRisk() {

        // Validate required fields

        const errors = this.validateForm();

        

        if (errors.length > 0) {

            this.showToast(`Please complete: ${errors.join(', ')}`);

            return;

        }

        

        // Calculate and show results

        this.calculateRiskScore();

        this.updateRiskVisuals();

        this.updateSummary();

        

        // Scroll to summary

        const summarySection = document.getElementById('rc-section-summary');

        if (summarySection) {

            summarySection.scrollIntoView({ 

                behavior: 'smooth', 

                block: 'start' 

            });

        }

        

        this.showToast('Risk analysis complete');

    }

    

    /**

     * Validate form

     */

    validateForm() {

        const errors = [];

        

        if (!this.formData.originPort) errors.push('Origin Port');

        if (!this.formData.destinationPort) errors.push('Destination Port');

        if (!this.formData.transportMode) errors.push('Transport Mode');

        if (!this.formData.transitDays) errors.push('Transit Days');

        if (!this.formData.cargoType) errors.push('Cargo Type');

        if (!this.formData.grossWeight) errors.push('Gross Weight');

        if (!this.formData.insuranceValue) errors.push('Insurance Value');

        if (!this.formData.packingType) errors.push('Packing Type');

        if (!this.formData.sellerName) errors.push('Seller Name');

        if (!this.formData.sellerCountry) errors.push('Seller Country');

        if (!this.formData.incoterm) errors.push('Incoterm');

        

        return errors;

    }

    

    /**

     * Show toast notification

     */

    showToast(message) {

        const toast = document.getElementById('rc-toast');

        const toastMessage = document.getElementById('rc-toast-message');

        

        if (toast && toastMessage) {

            toastMessage.textContent = message;

            toast.classList.add('active');

            

            setTimeout(() => {

                toast.classList.remove('active');

            }, 3000);

        }

    }

    

    /**

     * Get current risk context (for AI panel)

     */

    getCurrentRiskContext() {

        return {

            formData: this.formData,

            riskScore: this.currentRiskScore,

            riskLevel: this.currentRiskScore <= 30 ? 'low' : this.currentRiskScore <= 60 ? 'moderate' : 'high'

        };

    }

}



// Export to global scope

window.RiskcastInputController = RiskcastInputController;



/**

 * FILE: app/static/js/pages/input/input_controller_v19.js

 * PURPOSE: Main controller for RISKCAST v19 input page

 * 

 * FEATURES:

 * - Form data management with reactive updates

 * - Custom dropdown components

 * - Pill group selectors

 * - Port auto-suggestions with filtering

 * - Input validation

 * - Risk score calculation (deterministic formula)

 * - Risk visual updates (orb + gauge + metrics)

 * - Packing list drag & drop upload

 * - CSV preview parsing

 * - Progress bar tracking

 * - Toast notifications

 * - Form reset and analysis

 * 

 * ARCHITECTURE:

 * - Class-based structure for state management

 * - Debounced updates for performance

 * - Event-driven UI updates

 * - Separation of concerns (data, UI, validation)

 */
