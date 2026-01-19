/**
 * Rendering Logic for Shipment Summary (v2)
 * Handles DOM manipulation and template rendering
 * Migrated from React/TSX to Vanilla JS
 */

const SummaryRenderer = {
  // Icon SVG paths (simplified - should use sprite or icon library)
  icons: {
    shield: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>',
    dollarSign: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    clock: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    alertTriangle: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>',
    leaf: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>',
    cloud: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/>',
    anchor: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>',
    trendingUp: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>',
    radar: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>',
    checkCircle: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    database: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/>',
    zap: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>',
    plane: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>',
    truck: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0"/>',
    ship: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>',
    users: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>',
  },

  /**
   * Render shipment header
   */
  renderHeader() {
    const container = document.getElementById('shipment-header-container');
    if (!container) return;

    const template = document.getElementById('shipment-header-template');
    if (!template) {
      console.error('Shipment header template not found');
      return;
    }

    const clone = template.content.cloneNode(true);

    // Populate with data
    const data = SummaryState.shipmentData;
    if (data) {
      this.setFieldValue(clone, 'shipment_id', data.shipment_id || 'N/A');
      this.setFieldValue(clone, 'origin_code', data.origin?.code || 'N/A');
      this.setFieldValue(clone, 'origin_city', data.origin?.city || '');
      this.setFieldValue(clone, 'destination_code', data.destination?.code || 'N/A');
      this.setFieldValue(clone, 'destination_city', data.destination?.city || '');
      this.setFieldValue(clone, 'transport_mode', data.transport_mode || 'N/A');
      this.setFieldValue(clone, 'eta_range', data.eta_range || 'N/A');
      this.setFieldValue(clone, 'eta_duration', data.eta_duration || '');
      this.setFieldValue(clone, 'confidence_percent', (data.confidence || 0) + '%');
      
      // Set confidence bar width
      const confidenceBar = clone.querySelector('[data-confidence-bar]');
      if (confidenceBar) {
        confidenceBar.style.width = (data.confidence || 0) + '%';
      }

      // Set transport icon
      const transportIcon = clone.querySelector('[data-transport-icon]');
      if (transportIcon) {
        const iconMap = {
          'air': 'plane',
          'ocean': 'ship',
          'road': 'truck',
          'rail': 'truck',
        };
        const iconType = iconMap[data.transport_mode?.toLowerCase()] || 'truck';
        transportIcon.innerHTML = this.icons[iconType] || this.icons.truck;
      }
    }

    container.appendChild(clone);
  },

  /**
   * Render risk snapshot strip
   */
  renderRiskSnapshot() {
    const container = document.getElementById('risk-snapshot-container');
    if (!container) return;

    const template = document.getElementById('risk-snapshot-template');
    if (!template) return;

    const clone = template.content.cloneNode(true);
    const metricsGrid = clone.getElementById('risk-metrics-grid');
    if (!metricsGrid) return;

    const data = SummaryState.shipmentData;
    const metrics = [
      {
        id: 'risk_level',
        icon: 'shield',
        label: 'Estimated Risk Level',
        value: data?.risk_level || 'LOW',
        color: 'text-teal-400',
        bgColor: 'bg-teal-500/10',
        borderColor: 'border-teal-500/30',
      },
      {
        id: 'expected_loss',
        icon: 'dollarSign',
        label: 'Expected Loss',
        value: data?.expected_loss || '$0',
        color: 'text-cyan-400',
        bgColor: 'bg-cyan-500/10',
        borderColor: 'border-cyan-500/30',
      },
      {
        id: 'eta_reliability',
        icon: 'clock',
        label: 'ETA Reliability',
        value: data?.eta_reliability || 'N/A',
        color: 'text-violet-400',
        bgColor: 'bg-violet-500/10',
        borderColor: 'border-violet-500/30',
      },
      {
        id: 'active_alerts',
        icon: 'alertTriangle',
        label: 'Active Alerts',
        value: data?.active_alerts || '0',
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/10',
        borderColor: 'border-amber-500/30',
      },
    ];

    metrics.forEach(metric => {
      const metricEl = this.createRiskMetric(metric);
      metricsGrid.appendChild(metricEl);
    });

    container.appendChild(clone);
  },

  /**
   * Create a risk metric element
   */
  createRiskMetric(metric) {
    const template = document.getElementById('risk-metric-item');
    if (!template) {
      // Fallback: create element manually
      const div = document.createElement('div');
      div.className = `flex items-center gap-3 px-4 py-3 rounded-xl border ${metric.bgColor} ${metric.borderColor}`;
      div.dataset.metricId = metric.id;

      const iconSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      iconSvg.setAttribute('class', `w-5 h-5 ${metric.color}`);
      iconSvg.setAttribute('fill', 'none');
      iconSvg.setAttribute('stroke', 'currentColor');
      iconSvg.setAttribute('viewBox', '0 0 24 24');
      iconSvg.innerHTML = this.icons[metric.icon] || '';

      const content = document.createElement('div');
      content.className = 'flex-1';

      const label = document.createElement('div');
      label.className = 'text-white/50 text-xs';
      label.textContent = metric.label;
      label.dataset.metricLabel = '';

      const value = document.createElement('div');
      value.className = `mt-0.5 ${metric.color}`;
      value.textContent = metric.value;
      value.dataset.metricValue = '';

      content.appendChild(label);
      content.appendChild(value);
      div.appendChild(iconSvg);
      div.appendChild(content);
      return div;
    }

    const clone = template.content.cloneNode(true);
    const container = clone.querySelector('[data-metric-id]');

    container.dataset.metricId = metric.id;
    container.classList.add(metric.bgColor, 'border', metric.borderColor);

    const icon = clone.querySelector('[data-metric-icon]');
    if (icon) {
      icon.innerHTML = this.icons[metric.icon] || '';
      icon.classList.add(metric.color);
    }

    const label = clone.querySelector('[data-metric-label]');
    if (label) label.textContent = metric.label;

    const value = clone.querySelector('[data-metric-value]');
    if (value) {
      value.textContent = metric.value;
      value.classList.add(metric.color);
    }

    return clone;
  },

  /**
   * Render information cards
   */
  renderInformationCards() {
    const container = document.getElementById('information-cards-container');
    if (!container) return;

    const template = document.getElementById('information-cards-template');
    if (!template) return;

    const clone = template.content.cloneNode(true);
    const data = SummaryState.shipmentData;

    if (data) {
      // Route & Transit
      if (data.route) {
        this.setFieldValue(clone, 'departure_date', data.route.departure_date || 'N/A');
        this.setFieldValue(clone, 'departure_time', data.route.departure_time || '');
        this.setFieldValue(clone, 'arrival_date', data.route.arrival_date || 'N/A');
        this.setFieldValue(clone, 'transit_duration', data.route.transit_duration || 'N/A');
        this.setFieldValue(clone, 'incoterms', data.route.incoterms || 'N/A');
      }

      // Cargo & Packaging
      if (data.cargo) {
        this.setFieldValue(clone, 'commodity', data.cargo.commodity || 'N/A');
        this.setFieldValue(clone, 'cargo_value', data.cargo.value || 'N/A');
        this.setFieldValue(clone, 'cargo_weight', data.cargo.weight || 'N/A');
        this.setFieldValue(clone, 'packaging', data.cargo.packaging || 'N/A');
        this.setFieldValue(clone, 'hs_code', data.cargo.hs_code || 'N/A');
      }

      // Parties
      if (data.parties) {
        if (data.parties.shipper) {
          this.setFieldValue(clone, 'shipper_name', data.parties.shipper.name || 'N/A');
          this.setFieldValue(clone, 'shipper_location', data.parties.shipper.location || '');
        }
        if (data.parties.consignee) {
          this.setFieldValue(clone, 'consignee_name', data.parties.consignee.name || 'N/A');
          this.setFieldValue(clone, 'consignee_location', data.parties.consignee.location || '');
        }
        if (data.parties.carrier) {
          this.setFieldValue(clone, 'carrier_name', data.parties.carrier.name || 'N/A');
          this.setFieldValue(clone, 'carrier_rating', `Rating: ${data.parties.carrier.rating || 'N/A'}`);
        }
      }
    }

    container.appendChild(clone);
  },

  /**
   * Render intelligence modules
   */
  renderIntelligenceModules() {
    const container = document.getElementById('intelligence-modules-container');
    if (!container) return;

    const template = document.getElementById('intelligence-modules-template');
    if (!template) return;

    const clone = template.content.cloneNode(true);
    const modulesGrid = clone.getElementById('modules-grid');
    if (!modulesGrid) return;

    const modulesList = [
      {
        id: 'esg',
        icon: 'leaf',
        label: 'ESG Compliance',
        description: 'Environmental & sustainability analysis',
        color: 'cyan',
      },
      {
        id: 'weather',
        icon: 'cloud',
        label: 'Weather Patterns',
        description: 'Real-time meteorological data',
        color: 'teal',
      },
      {
        id: 'portCongestion',
        icon: 'anchor',
        label: 'Port Congestion',
        description: 'Terminal capacity & delays',
        color: 'violet',
      },
      {
        id: 'carrierPerformance',
        icon: 'trendingUp',
        label: 'Carrier Performance',
        description: 'Historical reliability metrics',
        color: 'cyan',
      },
      {
        id: 'marketScanner',
        icon: 'radar',
        label: 'Market Scanner',
        description: 'Trade route intelligence',
        color: 'teal',
      },
      {
        id: 'insurance',
        icon: 'shield',
        label: 'Insurance Assessment',
        description: 'Coverage recommendations',
        color: 'violet',
      },
    ];

    modulesList.forEach(module => {
      const moduleEl = this.createModuleButton(module);
      modulesGrid.appendChild(moduleEl);
    });

    // Set active count
    this.updateActiveModulesCount(clone);

    container.appendChild(clone);
  },

  /**
   * Create a module toggle button
   */
  createModuleButton(module) {
    const template = document.getElementById('module-item-template');
    if (!template) {
      // Fallback creation
      return this.createModuleButtonFallback(module);
    }

    const clone = template.content.cloneNode(true);
    const button = clone.querySelector('.module-toggle-btn');
    if (!button) return clone;

    const isActive = SummaryState.modules[module.id];

    button.dataset.moduleId = module.id;
    button.dataset.moduleActive = isActive;

    // Apply color classes
    const colors = this.getModuleColorClasses(module.color, isActive);
    button.classList.add(colors.bg, 'border', colors.border);
    if (colors.glow) button.classList.add(colors.glow);

    // Set icon
    const icon = clone.querySelector('.module-icon');
    if (icon) {
      icon.innerHTML = this.icons[module.icon] || '';
      icon.classList.add(colors.text);
    }

    const iconWrapper = clone.querySelector('.module-icon-wrapper');
    if (iconWrapper) {
      iconWrapper.classList.add(colors.bg, 'border', colors.border);
    }

    // Set labels
    const label = clone.querySelector('[data-module-label]');
    if (label) {
      label.textContent = module.label;
      label.classList.toggle('text-white', isActive);
      label.classList.toggle('text-white/60', !isActive);
    }

    const description = clone.querySelector('[data-module-description]');
    if (description) {
      description.textContent = module.description;
    }

    // Toggle track
    const track = clone.querySelector('.module-toggle-track');
    const thumb = clone.querySelector('.module-toggle-thumb');
    
    if (track && thumb) {
      if (isActive) {
        track.classList.remove('bg-white/10');
        track.classList.add('bg-gradient-to-r', 'from-cyan-500', 'to-teal-500');
        thumb.classList.remove('ml-1');
        thumb.classList.add('ml-5');
      } else {
        track.classList.add('bg-white/10');
        track.classList.remove('bg-gradient-to-r', 'from-cyan-500', 'to-teal-500');
        thumb.classList.add('ml-1');
        thumb.classList.remove('ml-5');
      }
    }

    // Active indicator
    const activeIndicator = clone.querySelector('.module-active-indicator');
    if (activeIndicator) {
      if (isActive) {
        activeIndicator.classList.remove('hidden');
        activeIndicator.classList.add('flex');
      } else {
        activeIndicator.classList.add('hidden');
        activeIndicator.classList.remove('flex');
      }
    }

    return clone;
  },

  /**
   * Fallback module button creation
   */
  createModuleButtonFallback(module) {
    const button = document.createElement('button');
    button.className = 'relative p-5 rounded-2xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] text-left module-toggle-btn';
    button.dataset.moduleId = module.id;
    
    const isActive = SummaryState.modules[module.id];
    const colors = this.getModuleColorClasses(module.color, isActive);
    button.classList.add(colors.bg, 'border', colors.border);
    
    button.innerHTML = `
      <div class="absolute top-4 right-4">
        <div class="module-toggle-track w-10 h-6 rounded-full transition-colors ${isActive ? 'bg-gradient-to-r from-cyan-500 to-teal-500' : 'bg-white/10'}">
          <div class="module-toggle-thumb w-4 h-4 bg-white rounded-full mt-1 transition-transform ${isActive ? 'ml-5' : 'ml-1'}"></div>
        </div>
      </div>
      <div class="flex items-start gap-3 mb-3">
        <div class="module-icon-wrapper p-2 rounded-xl ${colors.bg} border ${colors.border}">
          <svg class="w-5 h-5 module-icon ${colors.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            ${this.icons[module.icon] || ''}
          </svg>
        </div>
        <div class="flex-1 pr-12">
          <div class="module-label transition-colors ${isActive ? 'text-white' : 'text-white/60'}" data-module-label>${module.label}</div>
          <div class="text-white/40 text-sm" data-module-description>${module.description}</div>
        </div>
      </div>
      <div class="module-active-indicator ${isActive ? 'flex' : 'hidden'} items-center gap-1.5 text-xs text-cyan-400">
        <div class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></div>
        <span>Signal active</span>
      </div>
    `;
    
    return button;
  },

  /**
   * Get color classes for module
   */
  getModuleColorClasses(color, isActive) {
    const colorMap = {
      cyan: {
        bg: isActive ? 'bg-cyan-500/10' : 'bg-white/5',
        border: isActive ? 'border-cyan-500/50' : 'border-white/10',
        text: 'text-cyan-400',
        glow: isActive ? 'shadow-[0_0_20px_rgba(6,182,212,0.2)]' : '',
      },
      teal: {
        bg: isActive ? 'bg-teal-500/10' : 'bg-white/5',
        border: isActive ? 'border-teal-500/50' : 'border-white/10',
        text: 'text-teal-400',
        glow: isActive ? 'shadow-[0_0_20px_rgba(20,184,166,0.2)]' : '',
      },
      violet: {
        bg: isActive ? 'bg-violet-500/10' : 'bg-white/5',
        border: isActive ? 'border-violet-500/50' : 'border-white/10',
        text: 'text-violet-400',
        glow: isActive ? 'shadow-[0_0_20px_rgba(139,92,246,0.2)]' : '',
      },
    };
    return colorMap[color] || colorMap.cyan;
  },

  /**
   * Update active modules count display
   */
  updateActiveModulesCount(root = document) {
    const countEl = root.querySelector('#active-modules-count');
    if (countEl) {
      const active = SummaryState.getActiveModuleCount();
      const total = SummaryState.getTotalModuleCount();
      countEl.textContent = `${active} of ${total}`;
    }
  },

  /**
   * Render system confirmation section
   */
  renderSystemConfirmation() {
    const container = document.getElementById('system-confirmation-container');
    if (!container) return;

    const template = document.getElementById('system-confirmation-template');
    if (!template) return;

    const clone = template.content.cloneNode(true);
    const confirmationsGrid = clone.getElementById('confirmations-grid');
    if (!confirmationsGrid) return;

    const confirmations = [
      {
        icon: 'checkCircle',
        text: 'Data validated',
        detail: 'All shipment parameters verified',
      },
      {
        icon: 'database',
        text: 'No critical conflicts detected',
        detail: 'Cross-reference checks passed',
      },
      {
        icon: 'zap',
        text: 'Ready for full risk analysis',
        detail: 'Intelligence modules synchronized',
      },
    ];

    confirmations.forEach(confirmation => {
      const confEl = this.createConfirmationItem(confirmation);
      confirmationsGrid.appendChild(confEl);
    });

    container.appendChild(clone);
  },

  /**
   * Create a confirmation item
   */
  createConfirmationItem(confirmation) {
    const template = document.getElementById('confirmation-item-template');
    if (!template) {
      // Fallback
      const div = document.createElement('div');
      div.className = 'flex items-start gap-3';
      div.innerHTML = `
        <div class="p-2 bg-teal-500/20 border border-teal-500/40 rounded-xl">
          <svg class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            ${this.icons[confirmation.icon] || ''}
          </svg>
        </div>
        <div>
          <div class="text-white/90 mb-0.5">${confirmation.text}</div>
          <div class="text-white/40 text-sm">${confirmation.detail}</div>
        </div>
      `;
      return div;
    }

    const clone = template.content.cloneNode(true);

    const icon = clone.querySelector('[data-confirmation-icon]');
    if (icon) icon.innerHTML = this.icons[confirmation.icon] || '';

    const text = clone.querySelector('[data-confirmation-text]');
    if (text) text.textContent = confirmation.text;

    const detail = clone.querySelector('[data-confirmation-detail]');
    if (detail) detail.textContent = confirmation.detail;

    return clone;
  },

  /**
   * Helper: Set field value by data attribute
   */
  setFieldValue(root, fieldName, value) {
    const field = root.querySelector(`[data-field="${fieldName}"]`);
    if (field) {
      field.textContent = value;
    }
  },

  /**
   * Re-render a specific module button
   */
  reRenderModule(moduleId) {
    const button = document.querySelector(`[data-module-id="${moduleId}"]`);
    if (!button) return;

    const isActive = SummaryState.modules[moduleId];
    button.dataset.moduleActive = isActive;

    // Update classes
    const track = button.querySelector('.module-toggle-track');
    const thumb = button.querySelector('.module-toggle-thumb');
    const label = button.querySelector('[data-module-label]');
    const activeIndicator = button.querySelector('.module-active-indicator');

    if (track && thumb) {
      if (isActive) {
        track.classList.remove('bg-white/10');
        track.classList.add('bg-gradient-to-r', 'from-cyan-500', 'to-teal-500');
        thumb.classList.remove('ml-1');
        thumb.classList.add('ml-5');
      } else {
        track.classList.add('bg-white/10');
        track.classList.remove('bg-gradient-to-r', 'from-cyan-500', 'to-teal-500');
        thumb.classList.add('ml-1');
        thumb.classList.remove('ml-5');
      }
    }

    if (label) {
      label.classList.toggle('text-white', isActive);
      label.classList.toggle('text-white/60', !isActive);
    }

    if (activeIndicator) {
      if (isActive) {
        activeIndicator.classList.remove('hidden');
        activeIndicator.classList.add('flex');
      } else {
        activeIndicator.classList.add('hidden');
        activeIndicator.classList.remove('flex');
      }
    }

    this.updateActiveModulesCount();
  },
};

