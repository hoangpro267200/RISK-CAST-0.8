/**
 * ENGINE-FIRST ARCHITECTURE LOCK
 *
 * This component is a PURE PRESENTATION LAYER.
 *
 * It MUST NOT:
 * - compute risk
 * - derive decisions
 * - infer thresholds
 * - normalize business data
 *
 * Backend is the SINGLE SOURCE OF TRUTH.
 */

/**
 * RadarChart Component
 * 
 * Renders a radar chart using Chart.js with dark, minimalist styling.
 * Features subtle neon accents and smooth animations.
 * Supports single or multiple datasets with risk-based coloring.
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - Receives chart data from backend (labels, values)
 * - Only formats/clamps values for display
 * - _calculateOverallRisk() is UI-only for visual coloring (not business logic)
 * 
 * @class RadarChart
 * @exports RadarChart
 * @requires Chart.js (must be loaded globally or via CDN)
 */
export class RadarChart {
  /**
   * Initialize the RadarChart component
   * @param {Object} [options] - Component options
   * @param {Function} [options.onRiskLevelChange] - Callback when risk level changes (level, avgScore)
   * @param {Function} [options.onPointHover] - Callback on point hover (label, value)
   */
  constructor(options = {}) {
    this.container = null;
    this.canvas = null;
    this.chartInstance = null;
    this.chartId = `radar-chart-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this._stylesInjected = false;
    this._riskColorCache = {};
    this._hooks = {
      onRiskLevelChange: options.onRiskLevelChange || null,
      onPointHover: options.onPointHover || null,
    };
    this._previousData = null;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Chart data object
   * @param {Array<string>} data.labels - Array of axis labels
   * @param {Array<number>} [data.values] - Array of data values (0-100) - single dataset mode
   * @param {string} [data.label] - Dataset label (optional, single dataset mode)
   * @param {Array<Object>} [data.datasets] - Array of dataset objects (multi-dataset mode)
   * @param {Array<number>} data.datasets[].values - Array of data values (0-100)
   * @param {string} [data.datasets[].label] - Dataset label
   */
  mount(el, data = {}) {
    if (!el) {
      return;
    }

    this.container = el;
    this._injectStyles();

    // Check if Chart.js is available (support both global Chart and window.Chart)
    const ChartLib = typeof Chart !== 'undefined' ? Chart : (typeof window !== 'undefined' && typeof window.Chart !== 'undefined' ? window.Chart : null);
    if (!ChartLib) {
      this._renderError('Chart visualization unavailable');
      return;
    }

    this._createCanvas();
    this._initChart(data);
  }

  /**
   * Update the chart with new data
   * @param {Object} data - New chart data
   */
  update(data = {}) {
    if (!this.container) {
      return;
    }

    if (!this.chartInstance) {
      return;
    }

    // Shallow comparison to skip unnecessary updates
    // BUT: Allow force updates if _forceUpdate flag is set (for ResultsOS/demo mode)
    if (!this._forceUpdate && this._isDataEqual(data, this._previousData)) {
      return;
    }

    const normalized = this._normalizeInputData(data);
    
    // Update chart data
    this.chartInstance.data.labels = normalized.labels;
    this.chartInstance.data.datasets = normalized.datasets;

    // Trigger risk level change hook if applicable
    this._triggerRiskLevelHooks(normalized.datasets);

    // Update chart
    try {
      this.chartInstance.update('none');
    } catch (e) {
      this.chartInstance.update();
    }

    this._previousData = this._deepClone(data);
  }

  /**
   * Normalize input data to support both single and multi-dataset modes
   * @private
   * @param {Object} data - Input data
   * @returns {Object} Normalized data with labels and datasets array
   */
  _normalizeInputData(data) {
    const labels = Array.isArray(data.labels) ? data.labels : [];
    
    // Multi-dataset mode
    if (Array.isArray(data.datasets) && data.datasets.length > 0) {
      const datasets = data.datasets.map((ds, index) => {
        const values = this._normalizeValues(ds.values || [], labels.length);
        const riskLevel = this._calculateOverallRisk(values);
        const colorString = this._getRiskColorFromCSS(riskLevel);
        
        return {
          label: ds.label || `Dataset ${index + 1}`,
          data: values,
          backgroundColor: this._toRgba(colorString, 0.15),
          borderColor: colorString,
          borderWidth: 2,
          pointBackgroundColor: colorString,
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: colorString,
          pointHoverBorderColor: '#ffffff',
          pointHoverBorderWidth: 2,
        };
      });
      
      return { labels, datasets };
    }
    
    // Single dataset mode (backward compatibility)
    const values = this._normalizeValues(data.values || [], labels.length);
    const label = data.label || 'Risk Factors';
    const riskLevel = this._calculateOverallRisk(values);
    const colorString = this._getRiskColorFromCSS(riskLevel);
    
    const dataset = {
      label: label,
      data: values,
      backgroundColor: this._toRgba(colorString, 0.15),
      borderColor: colorString,
      borderWidth: 2,
      pointBackgroundColor: colorString,
      pointBorderColor: '#ffffff',
      pointBorderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 5,
      pointHoverBackgroundColor: colorString,
      pointHoverBorderColor: '#ffffff',
      pointHoverBorderWidth: 2,
    };
    
    return { labels, datasets: [dataset] };
  }

  /**
   * Trigger risk level change hooks for all datasets
   * @private
   * @param {Array<Object>} datasets - Chart datasets
   */
  _triggerRiskLevelHooks(datasets) {
    if (!this._hooks.onRiskLevelChange) {
      return;
    }

    datasets.forEach(dataset => {
      const values = dataset.data;
      if (Array.isArray(values) && values.length > 0) {
        const riskLevel = this._calculateOverallRisk(values);
        const avgScore = values.reduce((sum, val) => sum + val, 0) / values.length;
        this._hooks.onRiskLevelChange(riskLevel, avgScore);
      }
    });
  }

  /**
   * Shallow comparison of data objects
   * @private
   * @param {Object} a - First data object
   * @param {Object} b - Second data object
   * @returns {boolean} True if data is equal
   */
  _isDataEqual(a, b) {
    if (!a && !b) return true;
    if (!a || !b) return false;

    // Compare labels
    if (JSON.stringify(a.labels) !== JSON.stringify(b.labels)) {
      return false;
    }

    // Single dataset mode
    if (a.values && b.values) {
      return JSON.stringify(a.values) === JSON.stringify(b.values) &&
             a.label === b.label;
    }

    // Multi-dataset mode
    if (a.datasets && b.datasets) {
      if (a.datasets.length !== b.datasets.length) {
        return false;
      }
      for (let i = 0; i < a.datasets.length; i++) {
        if (JSON.stringify(a.datasets[i].values) !== JSON.stringify(b.datasets[i].values) ||
            a.datasets[i].label !== b.datasets[i].label) {
          return false;
        }
      }
      return true;
    }

    return false;
  }

  /**
   * Deep clone data object for comparison
   * @private
   * @param {Object} obj - Object to clone
   * @returns {Object} Cloned object
   */
  _deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
      return obj;
    }
    if (obj instanceof Array) {
      return obj.map(item => this._deepClone(item));
    }
    const cloned = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = this._deepClone(obj[key]);
      }
    }
    return cloned;
  }

  /**
   * Normalize and clamp values array
   * @private
   * @param {Array<number>} values - Input values
   * @param {number} expectedLength - Expected array length
   * @returns {Array<number>} Normalized values
   */
  _normalizeValues(values, expectedLength) {
    const length = expectedLength == null ? 0 : Math.max(0, Math.floor(expectedLength));
    const result = new Array(length).fill(0);

    if (!Array.isArray(values)) {
      return result;
    }

    for (let i = 0; i < length && i < values.length; i++) {
      const num = parseFloat(values[i]);
      if (!isNaN(num)) {
        result[i] = Math.max(0, Math.min(100, num));
      }
    }

    return result;
  }

  /**
   * Get overall risk level string from average score
   * @private
   * @param {Array<number>} values - Data values
   * @returns {string} Risk level string: 'low', 'medium', or 'high'
   */
  _calculateOverallRisk(values) {
    if (!Array.isArray(values) || values.length === 0) {
      return 'low';
    }

    const sum = values.reduce((acc, val) => acc + val, 0);
    const average = sum / values.length;

    if (average < 40) {
      return 'low';
    } else if (average < 70) {
      return 'medium';
    } else {
      return 'high';
    }
  }

  /**
   * Get color from CSS variable for risk level
   * @private
   * @param {string} riskLevel - Risk level: 'low', 'medium', or 'high'
   * @returns {string} Resolved color string
   */
  _getRiskColorFromCSS(riskLevel) {
    if (this._riskColorCache[riskLevel]) {
      return this._riskColorCache[riskLevel];
    }

    const varName = riskLevel === 'medium' ? '--risk-medium' : riskLevel === 'high' ? '--risk-high' : '--risk-low';
    const fallback = riskLevel === 'medium' ? '#ffcc00' : riskLevel === 'high' ? '#ff4466' : '#00ff88';

    // Create a temporary element to read CSS variable
    const tempEl = document.createElement('div');
    tempEl.style.setProperty('color', `var(${varName}, ${fallback})`);
    document.body.appendChild(tempEl);
    
    const computedColor = window.getComputedStyle(tempEl).color;
    document.body.removeChild(tempEl);

    let resolvedColor;
    // If computed color is in rgb format, convert to hex
    if (computedColor && computedColor.startsWith('rgb')) {
      resolvedColor = this._rgbToHex(computedColor) || fallback;
    } else {
      resolvedColor = computedColor || fallback;
    }

    this._riskColorCache[riskLevel] = resolvedColor;
    return resolvedColor;
  }

  /**
   * Convert RGB/RGBA string to hex
   * @private
   * @param {string} rgb - RGB/RGBA string (e.g., "rgb(0, 255, 136)" or "rgba(0, 255, 136, 0.5)")
   * @returns {string|null} Hex color string or null if parsing fails
   */
  _rgbToHex(rgb) {
    const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!match) return null;

    const r = parseInt(match[1], 10);
    const g = parseInt(match[2], 10);
    const b = parseInt(match[3], 10);

    return '#' + [r, g, b].map(x => {
      const hex = x.toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    }).join('');
  }

  /**
   * Convert color string to rgba with alpha
   * @private
   * @param {string} colorString - Color string (hex, rgb, or rgba)
   * @param {number} alpha - Alpha value (0-1)
   * @returns {string} RGBA string
   */
  _toRgba(colorString, alpha) {
    if (!colorString) {
      return 'rgba(0, 217, 255, 0.15)';
    }

    // Handle hex colors (#RRGGBB or #RGB)
    if (colorString.startsWith('#')) {
      let hex = colorString.replace('#', '');
      if (hex.length === 3) {
        hex = hex.split('').map(char => char + char).join('');
      }
      const bigint = parseInt(hex, 16);
      if (isNaN(bigint)) {
        return 'rgba(0, 217, 255, 0.15)';
      }
      const r = (bigint >> 16) & 255;
      const g = (bigint >> 8) & 255;
      const b = bigint & 255;
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    // Handle rgb() or rgba()
    const rgbMatch = colorString.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
    if (rgbMatch) {
      const r = parseInt(rgbMatch[1], 10);
      const g = parseInt(rgbMatch[2], 10);
      const b = parseInt(rgbMatch[3], 10);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    // Fallback
    return 'rgba(0, 217, 255, 0.15)';
  }

  /**
   * Get reusable Chart.js options configuration
   * @private
   * @returns {Object} Chart.js options object
   */
  static _getChartOptions() {
    return {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 1.2,
      layout: {
        padding: {
          top: 10,
          bottom: 10,
          left: 10,
          right: 10,
        }
      },
      scales: {
        r: {
          min: 0,
          max: 100,
          beginAtZero: true,
          ticks: {
            stepSize: 25,
            display: true,
            backdropColor: 'transparent',
            color: 'rgba(255, 255, 255, 0.3)',
            font: {
              size: 10,
              family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
            }
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.08)',
            lineWidth: 1,
          },
          angleLines: {
            color: 'rgba(255, 255, 255, 0.08)',
            lineWidth: 1,
          },
          pointLabels: {
            color: 'rgba(255, 255, 255, 0.7)',
            font: {
              size: 12,
              weight: '600',
              family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
            },
            padding: 12,
          }
        }
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: true,
          backgroundColor: 'rgba(15, 15, 20, 0.95)',
          titleColor: 'rgba(255, 255, 255, 0.9)',
          bodyColor: 'rgba(255, 255, 255, 0.8)',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          displayColors: true,
          titleFont: {
            size: 13,
            weight: '600',
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
          },
          bodyFont: {
            size: 12,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
          },
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.parsed.r}`;
            }
          }
        }
      },
      animation: {
        duration: 400,
        easing: 'easeOutCubic',
      },
      interaction: {
        mode: 'nearest',
        intersect: false,
      }
    };
  }

  /**
   * Render error state
   * @private
   * @param {string} message - Error message
   */
  _renderError(message) {
    this.container.innerHTML = `
      <div class="radar-chart-error">
        <div class="radar-chart-error-text">${this._escapeHtml(message)}</div>
        <div class="radar-chart-error-hint">Dữ liệu rủi ro có sẵn trong các bảng bên dưới</div>
      </div>
    `;
  }

  /**
   * Render empty state
   * @private
   */
  _renderEmptyState() {
    this.container.innerHTML = `
      <div class="radar-chart-empty">
        <div class="radar-chart-empty-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <div class="radar-chart-empty-text">Không có dữ liệu radar</div>
      </div>
    `;
  }

  /**
   * Escape HTML to prevent XSS
   * @private
   * @param {string} str - String to escape
   * @returns {string} Escaped string
   */
  _escapeHtml(str) {
    if (str == null) return '';
    if (typeof str !== 'string') return String(str);
    
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /**
   * Create canvas element for the chart
   * @private
   */
  _createCanvas() {
    this.container.innerHTML = `
      <div class="radar-chart-wrapper">
        <canvas id="${this.chartId}" class="radar-chart-canvas"></canvas>
      </div>
    `;
    
    this.canvas = document.getElementById(this.chartId);
  }

  /**
   * Initialize the Chart.js radar chart
   * @private
   * @param {Object} data - Chart data
   */
  _initChart(data) {
    const normalized = this._normalizeInputData(data);

    // Validate data
    if (!Array.isArray(normalized.labels) || normalized.labels.length === 0) {
      this._renderEmptyState();
      return;
    }

    const ctx = this.canvas.getContext('2d');
    
    // Get base options
    const options = RadarChart._getChartOptions();
    
    // Add point hover hook if provided
    if (this._hooks.onPointHover) {
      options.onHover = (event, activeElements) => {
        if (activeElements && activeElements.length > 0) {
          const element = activeElements[0];
          const datasetIndex = element.datasetIndex;
          const index = element.index;
          const dataset = this.chartInstance.data.datasets[datasetIndex];
          const label = normalized.labels[index];
          const value = dataset.data[index];
          this._hooks.onPointHover(label, value);
        }
      };
    }
    
    const ChartLib = typeof Chart !== 'undefined' ? Chart : (typeof window !== 'undefined' && typeof window.Chart !== 'undefined' ? window.Chart : null);
    if (!ChartLib) {
      this._renderError('Chart visualization unavailable');
      return;
    }
    this.chartInstance = new ChartLib(ctx, {
      type: 'radar',
      data: {
        labels: normalized.labels,
        datasets: normalized.datasets,
      },
      options: options,
    });

    // Trigger initial risk level hooks
    this._triggerRiskLevelHooks(normalized.datasets);
    
    // Store initial data for comparison
    this._previousData = this._deepClone(data);
  }

  /**
   * Destroy the chart instance safely
   * @private
   */
  _destroyChart() {
    if (this.chartInstance) {
      try {
        this.chartInstance.destroy();
      } catch (e) {
        // Silent cleanup
      }
      this.chartInstance = null;
    }
  }

  /**
   * Inject component styles into the document head
   * @private
   */
  _injectStyles() {
    if (this._stylesInjected) {
      return;
    }

    if (document.getElementById('radar-chart-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'radar-chart-styles';
    style.textContent = `
      /* RadarChart Component Styles */
      .radar-chart-wrapper {
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 300px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      }

      .radar-chart-canvas {
        max-width: 100%;
        height: auto !important;
      }

      /* Empty state */
      .radar-chart-empty {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 12px;
        padding: 60px 20px;
        background: rgba(20, 20, 25, 0.4);
        border: 1px dashed rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        min-height: 300px;
      }

      .radar-chart-empty-icon {
        color: rgba(255, 255, 255, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .radar-chart-empty-text {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
      }

      /* Error state */
      .radar-chart-error {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 8px;
        padding: 60px 20px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        min-height: 300px;
      }

      .radar-chart-error-text {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.6);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
      }

      .radar-chart-error-hint {
        font-size: 12px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.4);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
        margin-top: 4px;
      }

      /* Responsive adjustments */
      @media (max-width: 640px) {
        .radar-chart-wrapper {
          padding: 16px;
          min-height: 250px;
        }

        .radar-chart-empty,
        .radar-chart-error {
          padding: 40px 16px;
          min-height: 250px;
        }
      }

      /* Accessibility: Reduced motion preference */
      @media (prefers-reduced-motion: reduce) {
        .radar-chart-wrapper {
          /* Chart.js handles animation internally */
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }

  /**
   * Cleanup method to destroy chart and remove references
   * Call this before destroying the component
   */
  destroy() {
    this._destroyChart();
    this.container = null;
    this.canvas = null;
    this._previousData = null;
  }
}
