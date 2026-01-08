/**
 * Controller for Shipment Summary Page (v2)
 * Handles user interactions and coordinates state/rendering
 * Migrated from React/TSX to Vanilla JS
 */

const SummaryController = {
  /**
   * Initialize controller
   */
  init() {
    // Subscribe to state changes
    SummaryState.subscribe(this.handleStateChange.bind(this));

    // Attach event listeners
    this.attachEventListeners();

    // Initial render
    this.render();
  },

  /**
   * Full page render
   */
  render() {
    SummaryRenderer.renderHeader();
    SummaryRenderer.renderRiskSnapshot();
    SummaryRenderer.renderInformationCards();
    SummaryRenderer.renderIntelligenceModules();
    SummaryRenderer.renderSystemConfirmation();
  },

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Module toggle buttons (event delegation)
    document.addEventListener('click', (e) => {
      const moduleBtn = e.target.closest('.module-toggle-btn');
      if (moduleBtn) {
        const moduleId = moduleBtn.dataset.moduleId;
        if (moduleId) {
          this.handleModuleToggle(moduleId);
        }
      }
    });

    // Run analysis button
    const runAnalysisBtn = document.getElementById('run-analysis-btn');
    if (runAnalysisBtn) {
      runAnalysisBtn.addEventListener('click', this.handleRunAnalysis.bind(this));
    }
  },

  /**
   * Handle module toggle
   */
  handleModuleToggle(moduleId) {
    SummaryState.toggleModule(moduleId);
  },

  /**
   * Handle run analysis button click
   */
  handleRunAnalysis() {
    console.log('Running full risk analysis with modules:', SummaryState.modules);
    
    // Prepare analysis request data
    const analysisData = {
      shipment_id: SummaryState.shipmentData?.shipment_id,
      modules: SummaryState.modules,
      timestamp: new Date().toISOString(),
    };

    // Send to server (existing logic should handle this)
    this.submitAnalysisRequest(analysisData);
  },

  /**
   * Submit analysis request to server
   */
  submitAnalysisRequest(data) {
    // Transform summary data to shipment format for API
    const shipmentData = this.transformSummaryDataToShipment(data);
    
    // Use the existing risk analysis endpoint
    const apiEndpoint = '/api/v1/risk/analyze';
    
    // Show loading state
    const btn = document.getElementById('run-analysis-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="tracking-wide">Analyzing...</span>';
    }
    
    // Submit request
    fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(shipmentData),
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(result => {
        // Handle standard response envelope
        const analysisResult = result.data?.result || result.result || result;
        
        // Store result in memory/state for results page
        if (window.RISKCAST && window.RISKCAST.state) {
          window.RISKCAST.state.setLastResult(analysisResult);
        } else {
          // Fallback: store in localStorage
          try {
            localStorage.setItem('last_risk_analysis', JSON.stringify(analysisResult));
          } catch (e) {
            console.warn('Could not store result in localStorage:', e);
          }
        }
        
        // Navigate to results page
        window.location.href = '/results';
      })
      .catch(error => {
        console.error('Analysis request failed:', error);
        this.showError('Failed to start analysis. Please try again.');
        
        // Restore button
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = `
            <div class="relative flex items-center gap-3 text-white">
              <span class="tracking-wide">Run Full Risk Analysis</span>
              <svg class="w-5 h-5 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </div>
          `;
        }
      });
  },

  /**
   * Transform summary data to shipment format for API
   */
  transformSummaryDataToShipment(data) {
    const shipment = SummaryState.shipmentData;
    if (!shipment) {
      // Fallback: create minimal shipment
      return {
        transport_mode: 'air',
        cargo_type: 'general',
        route: `${shipment?.origin?.code || 'SGN'}_${shipment?.destination?.code || 'LAX'}`,
        incoterm: 'FOB',
        container: 'N/A',
        packaging: 'palletized',
        priority: 'standard',
        packages: 12,
        etd: new Date().toISOString().split('T')[0],
        eta: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        transit_time: 7.0,
        cargo_value: 145000,
        use_fuzzy: data.modules?.esg || false,
        use_forecast: data.modules?.weather || false,
        use_mc: true,
        use_var: true,
      };
    }
    
    // Transform from summary format to shipment format
    const route = shipment.route || {};
    const cargo = shipment.cargo || {};
    
    // Extract cargo value (remove $ and commas)
    let cargoValue = 0;
    if (cargo.value) {
      cargoValue = parseFloat(cargo.value.replace(/[$,]/g, '')) || 0;
    }
    
    // Extract packages
    let packages = 12;
    if (cargo.packaging) {
      const match = cargo.packaging.match(/(\d+)/);
      if (match) packages = parseInt(match[1]);
    }
    
    // Calculate transit time
    let transitTime = 7.0;
    if (route.transit_duration) {
      const match = route.transit_duration.match(/(\d+)/);
      if (match) transitTime = parseFloat(match[1]);
    }
    
    return {
      transport_mode: (shipment.transport_mode || 'air').toLowerCase(),
      cargo_type: (cargo.commodity || 'general').toLowerCase(),
      route: `${shipment.origin?.code || 'SGN'}_${shipment.destination?.code || 'LAX'}`,
      incoterm: route.incoterms || 'FOB',
      container: 'N/A',
      packaging: 'palletized',
      priority: 'standard',
      packages: packages,
      etd: route.departure_date || new Date().toISOString().split('T')[0],
      eta: route.arrival_date || new Date(Date.now() + transitTime * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      transit_time: transitTime,
      cargo_value: cargoValue,
      use_fuzzy: data.modules?.esg || false,
      use_forecast: data.modules?.weather || false,
      use_mc: true,
      use_var: true,
      // Include buyer/seller if available
      buyer: shipment.parties?.consignee ? {
        name: shipment.parties.consignee.name,
        location: shipment.parties.consignee.location,
      } : null,
      seller: shipment.parties?.shipper ? {
        name: shipment.parties.shipper.name,
        location: shipment.parties.shipper.location,
      } : null,
    };
  },

  /**
   * Show error message
   */
  showError(message) {
    // Try to use existing toast/notification system
    if (window.RISKCAST && window.RISKCAST.ui && window.RISKCAST.ui.toast) {
      window.RISKCAST.ui.toast.error(message);
    } else {
      // Fallback: alert
      alert(message);
    }
  },

  /**
   * Handle state changes
   */
  handleStateChange(event, data) {
    switch (event) {
      case 'module_toggle':
        SummaryRenderer.reRenderModule(data.moduleId);
        break;
      case 'init':
        // Initial state loaded
        break;
    }
  },
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSummaryPage);
} else {
  initSummaryPage();
}

function initSummaryPage() {
  // Get shipment data injected by Python template
  // Assuming: <script>window.SHIPMENT_DATA = {{ shipment_data|tojson }};</script>
  if (window.SHIPMENT_DATA) {
    SummaryState.init(window.SHIPMENT_DATA);
    SummaryController.init();
  } else {
    console.warn('SHIPMENT_DATA not found. Summary page may not render correctly.');
    // Try to initialize with empty state for testing
    SummaryState.init({});
    SummaryController.init();
  }
}

