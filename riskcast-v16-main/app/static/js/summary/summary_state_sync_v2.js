/**
 * State Management for Shipment Summary (v2)
 * Handles module toggles and data state
 * Migrated from React/TSX to Vanilla JS
 * 
 * DATA FLOW:
 * 1. Try localStorage.RISKCAST_STATE (from Input page) - PRIORITY
 * 2. Fallback to window.SHIPMENT_DATA (from Python template)
 * 3. Fallback to sample data
 */

const SummaryState = {
  // Intelligence modules state
  modules: {
    esg: true,
    weather: true,
    portCongestion: true,
    carrierPerformance: true,
    marketScanner: false,
    insurance: true,
  },

  // Shipment data (from localStorage or Python template)
  shipmentData: null,
  
  // Raw RISKCAST_STATE for reference
  riskcastState: null,

  // Observers/listeners
  observers: [],

  /**
   * Initialize state - prioritize localStorage over Python-injected data
   * @param {Object} serverData - Shipment data from Python template (fallback)
   */
  init(serverData) {
    console.log('[SummaryState] Initializing...');
    
    // 1. Try to load from localStorage (RISKCAST_STATE from Input page)
    const localData = this.loadFromLocalStorage();
    
    if (localData && Object.keys(localData).length > 0) {
      console.log('[SummaryState] ✅ Loaded data from localStorage (RISKCAST_STATE)');
      this.riskcastState = localData;
      this.shipmentData = this.transformRiskcastStateToSummaryData(localData);
    } else if (serverData && Object.keys(serverData).length > 0) {
      console.log('[SummaryState] ✅ Using server-provided data (window.SHIPMENT_DATA)');
      this.shipmentData = serverData;
    } else {
      console.log('[SummaryState] ⚠️ No data available, using defaults');
      this.shipmentData = this.getDefaultData();
    }
    
    // Restore module state from localStorage if available
    const savedModules = localStorage.getItem('summary_modules_state');
    if (savedModules) {
      try {
        this.modules = JSON.parse(savedModules);
      } catch (e) {
        console.warn('Failed to restore module state:', e);
      }
    }
    
    // Also try to restore modules from RISKCAST_STATE.riskModules
    if (this.riskcastState && this.riskcastState.riskModules) {
      this.modules = {
        esg: this.riskcastState.riskModules.use_esg ?? true,
        weather: this.riskcastState.riskModules.use_weather ?? true,
        portCongestion: this.riskcastState.riskModules.use_port ?? true,
        carrierPerformance: this.riskcastState.riskModules.use_carrier ?? true,
        marketScanner: this.riskcastState.riskModules.use_market ?? false,
        insurance: this.riskcastState.riskModules.use_insurance ?? true,
      };
    }
    
    console.log('[SummaryState] Shipment data:', this.shipmentData);
    this.notifyObservers('init');
  },
  
  /**
   * Load RISKCAST_STATE from localStorage
   * @returns {Object|null} RISKCAST_STATE object or null
   */
  loadFromLocalStorage() {
    try {
      const saved = localStorage.getItem('RISKCAST_STATE');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.warn('[SummaryState] Failed to load from localStorage:', e);
    }
    return null;
  },
  
  /**
   * Transform RISKCAST_STATE (Input page format) to Summary data format
   * @param {Object} state - RISKCAST_STATE object
   * @returns {Object} Summary-compatible data
   */
  transformRiskcastStateToSummaryData(state) {
    const transport = state.transport || {};
    const cargo = state.cargo || {};
    const seller = state.seller || {};
    const buyer = state.buyer || {};
    const meta = state.meta || {};
    
    // Extract port codes
    const pol = transport.origin || transport.pol || 'SGN';
    const pod = transport.destination || transport.pod || 'LAX';
    
    // Get port info
    const polInfo = this.getPortInfo(pol);
    const podInfo = this.getPortInfo(pod);
    
    // Calculate dates
    const etd = transport.etd || new Date().toISOString().split('T')[0];
    const transitDays = parseInt(transport.transitDays) || 7;
    const etdDate = new Date(etd);
    const etaDate = new Date(etdDate);
    etaDate.setDate(etaDate.getDate() + transitDays);
    
    // Get cargo value
    const cargoValue = parseFloat(cargo.insuranceValue) || parseFloat(cargo.value) || 0;
    
    return {
      shipment_id: meta.shipment_id || this.generateShipmentId(pol, pod),
      origin: {
        code: pol,
        city: polInfo.city,
        country: polInfo.country
      },
      destination: {
        code: pod,
        city: podInfo.city,
        country: podInfo.country
      },
      transport_mode: this.normalizeTransportMode(transport.mode),
      eta_range: this.formatDateRange(etd, etaDate.toISOString().split('T')[0]),
      eta_duration: `${transitDays} days`,
      confidence: 85,
      risk_level: state.riskLevel || 'LOW',
      expected_loss: `$${Math.round(cargoValue * 0.02).toLocaleString()}`,
      eta_reliability: '92%',
      active_alerts: 0,
      route: {
        departure_date: this.formatDate(etd),
        departure_time: '14:30 UTC+7',
        arrival_date: this.formatDateRange(etd, etaDate.toISOString().split('T')[0]),
        transit_duration: `${transitDays} days`,
        incoterms: seller.incoterm || transport.incoterm || 'FOB'
      },
      cargo: {
        commodity: cargo.type || cargo.cargoType || 'General Cargo',
        value: cargoValue > 0 ? `$${cargoValue.toLocaleString()}` : 'Not specified',
        weight: cargo.weight ? `${parseFloat(cargo.weight).toLocaleString()} kg` : 'Not specified',
        packaging: cargo.packing || 'Standard',
        hs_code: cargo.hsCode || 'N/A'
      },
      parties: {
        shipper: {
          name: seller.companyName || seller.name || 'Seller',
          location: `${seller.city || ''}, ${seller.country?.name || seller.country || ''}`
        },
        consignee: {
          name: buyer.companyName || buyer.name || 'Buyer',
          location: `${buyer.city || ''}, ${buyer.country?.name || buyer.country || ''}`
        },
        carrier: {
          name: transport.carrier || 'Not specified',
          rating: 'N/A'
        }
      }
    };
  },
  
  /**
   * Get port info by code
   * @param {string} code - Port code (e.g., 'SGN', 'LAX')
   * @returns {Object} Port info
   */
  getPortInfo(code) {
    const ports = {
      'SGN': { city: 'Ho Chi Minh City', country: 'Vietnam' },
      'HAN': { city: 'Hanoi', country: 'Vietnam' },
      'LAX': { city: 'Los Angeles', country: 'USA' },
      'JFK': { city: 'New York', country: 'USA' },
      'ORD': { city: 'Chicago', country: 'USA' },
      'SFO': { city: 'San Francisco', country: 'USA' },
      'PVG': { city: 'Shanghai', country: 'China' },
      'HKG': { city: 'Hong Kong', country: 'Hong Kong' },
      'SIN': { city: 'Singapore', country: 'Singapore' },
      'NRT': { city: 'Tokyo', country: 'Japan' },
      'ICN': { city: 'Seoul', country: 'South Korea' },
      'BKK': { city: 'Bangkok', country: 'Thailand' },
      'DXB': { city: 'Dubai', country: 'UAE' },
      'FRA': { city: 'Frankfurt', country: 'Germany' },
      'LHR': { city: 'London', country: 'UK' },
      'AMS': { city: 'Amsterdam', country: 'Netherlands' },
    };
    return ports[code?.toUpperCase()] || { city: code, country: 'Unknown' };
  },
  
  /**
   * Normalize transport mode string
   * @param {string} mode - Raw mode string
   * @returns {string} Normalized mode
   */
  normalizeTransportMode(mode) {
    if (!mode) return 'Air';
    const m = mode.toLowerCase();
    if (m.includes('air')) return 'Air';
    if (m.includes('sea') || m.includes('ocean')) return 'Ocean';
    if (m.includes('road') || m.includes('truck')) return 'Road';
    if (m.includes('rail')) return 'Rail';
    return mode;
  },
  
  /**
   * Format date for display
   * @param {string} dateStr - ISO date string
   * @returns {string} Formatted date
   */
  formatDate(dateStr) {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return dateStr;
    }
  },
  
  /**
   * Format date range for display
   * @param {string} startDate - Start date
   * @param {string} endDate - End date
   * @returns {string} Formatted range
   */
  formatDateRange(startDate, endDate) {
    try {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const startDay = start.getDate();
      const endDay = end.getDate();
      const month = end.toLocaleDateString('en-US', { month: 'short' });
      const year = end.getFullYear();
      return `${month} ${startDay}-${endDay}, ${year}`;
    } catch {
      return `${startDate} - ${endDate}`;
    }
  },
  
  /**
   * Generate shipment ID
   * @param {string} pol - Port of loading
   * @param {string} pod - Port of discharge
   * @returns {string} Generated ID
   */
  generateShipmentId(pol, pod) {
    const timestamp = Date.now();
    return `SH-${pol}-${pod}-${timestamp}`;
  },
  
  /**
   * Get default/sample data when nothing is available
   * @returns {Object} Default summary data
   */
  getDefaultData() {
    return {
      shipment_id: 'SH-SAMPLE-' + Date.now(),
      origin: { code: 'SGN', city: 'Ho Chi Minh City', country: 'Vietnam' },
      destination: { code: 'LAX', city: 'Los Angeles', country: 'USA' },
      transport_mode: 'Air',
      eta_range: 'Jan 8-10, 2026',
      eta_duration: '5-7 days',
      confidence: 85,
      risk_level: 'LOW',
      expected_loss: '$2,400',
      eta_reliability: '92%',
      active_alerts: 2,
      route: {
        departure_date: 'Jan 3, 2026',
        departure_time: '14:30 UTC+7',
        arrival_date: 'Jan 8-10, 2026',
        transit_duration: '5-7 days',
        incoterms: 'FOB'
      },
      cargo: {
        commodity: 'Electronics',
        value: '$145,000',
        weight: '2,450 kg',
        packaging: '12 Pallets',
        hs_code: '8471.30'
      },
      parties: {
        shipper: { name: 'Sample Shipper', location: 'Ho Chi Minh City, Vietnam' },
        consignee: { name: 'Sample Consignee', location: 'Los Angeles, USA' },
        carrier: { name: 'Global Air Freight', rating: '4.7/5.0' }
      }
    };
  },

  /**
   * Toggle a module on/off
   * @param {string} moduleId - Module identifier
   */
  toggleModule(moduleId) {
    if (this.modules.hasOwnProperty(moduleId)) {
      this.modules[moduleId] = !this.modules[moduleId];
      this.persistModuleState();
      this.notifyObservers('module_toggle', { moduleId, active: this.modules[moduleId] });
    }
  },

  /**
   * Get active module count
   * @returns {number}
   */
  getActiveModuleCount() {
    return Object.values(this.modules).filter(Boolean).length;
  },

  /**
   * Get total module count
   * @returns {number}
   */
  getTotalModuleCount() {
    return Object.keys(this.modules).length;
  },

  /**
   * Persist module state to localStorage
   */
  persistModuleState() {
    try {
      localStorage.setItem('summary_modules_state', JSON.stringify(this.modules));
    } catch (e) {
      console.warn('Failed to persist module state:', e);
    }
  },

  /**
   * Subscribe to state changes
   * @param {Function} callback - Observer callback
   */
  subscribe(callback) {
    this.observers.push(callback);
  },

  /**
   * Notify all observers of state change
   * @param {string} event - Event type
   * @param {Object} data - Event data
   */
  notifyObservers(event, data = {}) {
    this.observers.forEach(observer => observer(event, data));
  },
};

