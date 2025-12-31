/**
 * FinancialHistogram Component
 * 
 * Visualizes loss distribution using Chart.js bar chart.
 * Shows most likely loss range vs extreme tail risk.
 * 
 * @class FinancialHistogram
 * @exports FinancialHistogram
 * @requires Chart.js (must be loaded globally or via CDN)
 */
export class FinancialHistogram {
  /**
   * Initialize the FinancialHistogram component
   */
  constructor() {
    this.container = null;
    this.canvas = null;
    this.chartInstance = null;
    this.chartId = `financial-histogram-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Chart data object
   * @param {Array<number>} data.bins - Loss buckets (USD)
   * @param {Array<number>} data.counts - Frequency per bucket
   * @param {Object} data.financialData - Optional: Full financial data for zero-impact detection
   * @param {Object} data.scenario - Optional: Scenario classification
   */
  mount(el, data = {}) {
    if (!el) {
      return;
    }

    this.container = el;
    this._injectStyles();

    // ENGINE-FIRST: Check for zero-impact scenario BEFORE attempting to render
    const financialData = data.financialData || {};
    const scenario = data.scenario || null;
    const { bins = [], counts = [] } = data;
    
    // Build financial data object for state analysis
    const financialDataForCheck = {
      distribution: bins.length > 0 ? bins : null,
      expectedLoss: financialData.expectedLoss ?? financialData.meanLoss ?? null,
      var95: financialData.var95 ?? financialData.p95 ?? null,
      cvar: financialData.cvar ?? financialData.maxLoss ?? null,
      cargoValue: financialData.cargoValue ?? null
    };

    // Check if this is a zero-impact scenario
    const isZeroImpact = this._isZeroImpactScenario(financialDataForCheck, bins, counts);
    
    if (isZeroImpact) {
      this._renderZeroImpactState(scenario);
      return;
    }

    // Check if Chart.js is available (support both global Chart and window.Chart)
    const ChartLib = typeof Chart !== 'undefined' ? Chart : (typeof window !== 'undefined' && typeof window.Chart !== 'undefined' ? window.Chart : null);
    if (!ChartLib) {
      el.innerHTML = `
        <div class="financial-histogram-error">
          <div class="financial-histogram-error-text">Biểu đồ không khả dụng</div>
          <div class="financial-histogram-error-hint">Dữ liệu tổn thất có sẵn trong đường cong tổn thất bên dưới</div>
        </div>
      `;
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
    console.log('[DEBUG FinancialHistogram.update] Starting update', {
      hasContainer: !!this.container,
      hasBins: Array.isArray(data.bins) && data.bins.length > 0,
      hasCounts: Array.isArray(data.counts) && data.counts.length > 0,
      hasFinancialData: !!data.financialData,
      hasScenario: !!data.scenario,
      scenarioType: data.scenario?.type
    });

    if (!this.container) {
      console.warn('[DEBUG FinancialHistogram.update] No container!');
      return;
    }

    const { bins = [], counts = [], financialData = {}, scenario = null } = data;
    console.log('[DEBUG FinancialHistogram.update] Extracted data:', {
      binsLength: bins.length,
      countsLength: counts.length,
      financialDataKeys: Object.keys(financialData),
      scenario: scenario
    });

    // ENGINE-FIRST: Re-check zero-impact scenario on update
    const financialDataForCheck = {
      distribution: bins.length > 0 ? bins : null,
      expectedLoss: financialData.expectedLoss ?? financialData.meanLoss ?? null,
      var95: financialData.var95 ?? financialData.p95 ?? null,
      cvar: financialData.cvar ?? financialData.maxLoss ?? null,
      cargoValue: financialData.cargoValue ?? null
    };

    const isZeroImpact = this._isZeroImpactScenario(financialDataForCheck, bins, counts);
    console.log('[DEBUG FinancialHistogram.update] Zero-impact check:', {
      isZeroImpact,
      financialDataForCheck
    });

    // If zero-impact and chart exists, destroy it and show empty state
    if (isZeroImpact) {
      console.log('[DEBUG FinancialHistogram.update] Zero-impact detected, rendering empty state with scenario:', scenario);
      if (this.chartInstance) {
        this._destroyChart();
      }
      this._renderZeroImpactState(scenario);
      return;
    }

    // If no chart instance but we have valid data, create it
    if (!this.chartInstance) {
      const ChartLib = typeof Chart !== 'undefined' ? Chart : (typeof window !== 'undefined' && typeof window.Chart !== 'undefined' ? window.Chart : null);
      if (ChartLib) {
        this._createCanvas();
        this._initChart(data);
        return;
      }
    }

    if (!this.chartInstance) {
      return;
    }

    // Normalize and prepare data
    const prepared = this._prepareData(bins, counts);

    if (!prepared || prepared.labels.length === 0) {
      this.chartInstance.data.labels = [];
      this.chartInstance.data.datasets[0].data = [];
      this.chartInstance.data.datasets[0].backgroundColor = [];
      this.chartInstance.data.datasets[0].borderColor = [];
    } else {
      // Update chart data
      this.chartInstance.data.labels = prepared.labels;
      this.chartInstance.data.datasets[0].data = prepared.values;
      this.chartInstance.data.datasets[0].backgroundColor = prepared.colors;
      this.chartInstance.data.datasets[0].borderColor = prepared.borderColors;
    }

    // Update chart
    try {
      this.chartInstance.update('none');
    } catch (e) {
      this.chartInstance.update();
    }
  }

  /**
   * Check if financial data represents zero-impact scenario
   * ENGINE-FIRST: Only analyzes provided data, never recomputes
   * @private
   * @param {Object} financialData - Financial data object
   * @param {Array<number>} bins - Loss buckets
   * @param {Array<number>} counts - Frequencies
   * @returns {boolean} True if all values are zero/null
   */
  _isZeroImpactScenario(financialData, bins, counts) {
    // Check distribution array if available
    const hasDistribution = Array.isArray(bins) && bins.length > 0 && 
                           Array.isArray(counts) && counts.length > 0;
    const distributionHasNonZero = hasDistribution && bins.some((bin, idx) => {
      const binVal = parseFloat(bin);
      const countVal = parseFloat(counts[idx]);
      // Check if either bin or count has a meaningful non-zero value
      return (!isNaN(binVal) && binVal > 0) || (!isNaN(countVal) && countVal > 0);
    });

    // Check numeric metrics
    const metrics = [
      financialData.expectedLoss,
      financialData.var95,
      financialData.cvar,
      financialData.maxLoss
    ].filter(v => v !== null && v !== undefined && !isNaN(parseFloat(v)));

    const allMetricsZero = metrics.length === 0 || 
                          metrics.every(v => {
                              const num = parseFloat(v);
                              return isNaN(num) || num === 0;
                          });

    // Zero-impact if distribution has no non-zero values AND all metrics are zero
    return !distributionHasNonZero && allMetricsZero;
  }

  /**
   * Render zero-impact empty state
   * @private
   * @param {Object} scenario - Optional scenario classification
   */
  _renderZeroImpactState(scenario = null) {
    console.log('[DEBUG FinancialHistogram._renderZeroImpactState] Starting', { scenario });
    
    if (!this.container) {
      console.warn('[DEBUG FinancialHistogram._renderZeroImpactState] No container!');
      return;
    }

    // Destroy chart if it exists
    if (this.chartInstance) {
      this._destroyChart();
    }

    // Get scenario-aware empty state
    let emptyState;
    
    // Try to use scenario classifier if available
    const classifier = (typeof window !== 'undefined' && window.RISKCAST?.utils?.scenarioClassifier) || null;
    console.log('[DEBUG FinancialHistogram._renderZeroImpactState] Classifier check:', {
      hasClassifier: !!classifier,
      hasGetFinancialEmptyState: classifier && typeof classifier.getFinancialEmptyState === 'function'
    });
    
    if (scenario && classifier && typeof classifier.getFinancialEmptyState === 'function') {
      emptyState = classifier.getFinancialEmptyState(scenario);
      console.log('[DEBUG FinancialHistogram._renderZeroImpactState] Using classifier empty state:', emptyState);
    } else if (scenario && scenario.type === 'OPERATIONAL_RISK_ONLY') {
      // Scenario-aware message for operational risk only
      emptyState = {
        title: 'Financial loss simulation not applicable',
        description: 'This scenario involves operational risk factors only',
        note: 'No financial loss exposure detected. Risk analysis focuses on operational factors such as delays, routing complexity, and service quality.',
        scenarioAware: true
      };
    } else {
      // Fallback empty state
      emptyState = {
        title: 'No financial loss simulated',
        description: 'Cargo value not provided or equal to zero',
        note: 'Risk analysis based on operational factors only',
        scenarioAware: false
      };
    }

    this.container.innerHTML = `
      <div class="financial-histogram-empty ${scenario?.type === 'OPERATIONAL_RISK_ONLY' ? 'scenario-operational-risk' : ''}">
        <div class="financial-histogram-empty-content">
          <div class="financial-histogram-empty-title">${this._escapeHtml(emptyState.title)}</div>
          <div class="financial-histogram-empty-description">${this._escapeHtml(emptyState.description)}</div>
          <div class="financial-histogram-empty-note">${this._escapeHtml(emptyState.note)}</div>
        </div>
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
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  }

  /**
   * Prepare and normalize data for chart
   * @private
   * @param {Array<number>} bins - Loss buckets
   * @param {Array<number>} counts - Frequencies
   * @returns {Object|null} Prepared data or null if invalid
   */
  _prepareData(bins, counts) {
    if (!Array.isArray(bins) || !Array.isArray(counts) || bins.length === 0) {
      return null;
    }

    // Pair bins with counts and sort by bin value
    const pairs = bins.map((bin, idx) => ({
      bin: Math.max(0, parseFloat(bin) || 0),
      count: parseFloat(counts[idx] || 0),
      originalIndex: idx
    })).sort((a, b) => a.bin - b.bin);

    // Identify top 10% highest-loss bins
    const sortedByLoss = [...pairs].sort((a, b) => b.bin - a.bin);
    const top10PercentCount = Math.max(1, Math.ceil(sortedByLoss.length * 0.1));
    const top10PercentBins = new Set(
      sortedByLoss.slice(0, top10PercentCount).map(p => p.originalIndex)
    );

    // Get colors from CSS variables
    const mediumColor = this._getCSSColor('--risk-medium', '#ffcc00');
    const highColor = this._getCSSColor('--risk-high', '#ff4466');

    // Calculate total for normalization
    const totalCount = pairs.reduce((sum, pair) => sum + pair.count, 0);

    // Build chart data
    const labels = [];
    const values = [];
    const colors = [];
    const borderColors = [];

    pairs.forEach((pair, idx) => {
      const isHighRisk = top10PercentBins.has(pair.originalIndex);
      labels.push(this._formatUSD(pair.bin));
      const normalizedValue = totalCount > 0 ? pair.count / totalCount : 0;
      values.push(normalizedValue);
      colors.push(isHighRisk ? highColor : mediumColor);
      borderColors.push(isHighRisk ? highColor : mediumColor);
    });

    return {
      labels,
      values,
      colors,
      borderColors,
      pairs
    };
  }

  /**
   * Get color from CSS variable
   * @private
   * @param {string} varName - CSS variable name
   * @param {string} fallback - Fallback hex color
   * @returns {string} Resolved color string
   */
  _getCSSColor(varName, fallback) {
    try {
      const tempEl = document.createElement('div');
      tempEl.style.setProperty('color', `var(${varName}, ${fallback})`);
      document.body.appendChild(tempEl);
      
      const computedColor = window.getComputedStyle(tempEl).color;
      document.body.removeChild(tempEl);

      // Convert rgb to hex if needed
      if (computedColor && computedColor.startsWith('rgb')) {
        return this._rgbToHex(computedColor) || fallback;
      }

      return computedColor || fallback;
    } catch (e) {
      return fallback;
    }
  }

  /**
   * Convert RGB/RGBA string to hex
   * @private
   * @param {string} rgb - RGB/RGBA string
   * @returns {string|null} Hex color string or null
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
   * Format number as USD
   * @private
   * @param {number} value - Numeric value
   * @returns {string} Formatted USD string
   */
  _formatUSD(value) {
    const num = parseFloat(value);
    if (isNaN(num)) return '$0';

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  }

  /**
   * Create canvas element for the chart
   * @private
   */
  _createCanvas() {
    this.container.innerHTML = `
      <div class="financial-histogram-wrapper">
        <canvas id="${this.chartId}" class="financial-histogram-canvas"></canvas>
      </div>
    `;
    
    this.canvas = document.getElementById(this.chartId);
  }

  /**
   * Initialize the Chart.js bar chart
   * @private
   * @param {Object} data - Chart data
   */
  _initChart(data) {
    const {
      bins = [],
      counts = [],
    } = data;

    // Prepare data
    const prepared = this._prepareData(bins, counts);

    const mediumColor = this._getCSSColor('--risk-medium', '#ffcc00');
    const highColor = this._getCSSColor('--risk-high', '#ff4466');

    const ctx = this.canvas.getContext('2d');
    
    const ChartLib = typeof Chart !== 'undefined' ? Chart : (typeof window !== 'undefined' && typeof window.Chart !== 'undefined' ? window.Chart : null);
    if (!ChartLib) {
      this._renderError('Biểu đồ không khả dụng');
      return;
    }
    this.chartInstance = new ChartLib(ctx, {
      type: 'bar',
      data: {
        labels: prepared ? prepared.labels : [],
        datasets: [{
          label: 'Tần Suất Tương Đối',
          data: prepared ? prepared.values : [],
          backgroundColor: prepared ? prepared.colors : [],
          borderColor: prepared ? prepared.borderColors : [],
          borderWidth: 1,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2,
        layout: {
          padding: {
            top: 10,
            bottom: 10,
            left: 10,
            right: 10,
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Tổn Thất (USD)',
              color: 'rgba(255, 255, 255, 0.7)',
              font: {
                size: 12,
                weight: '600',
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
              }
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.5)',
              font: {
                size: 10,
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
              }
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.08)',
              lineWidth: 1,
            }
          },
          y: {
            title: {
              display: true,
              text: 'Tần Suất Tương Đối',
              color: 'rgba(255, 255, 255, 0.7)',
              font: {
                size: 12,
                weight: '600',
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
              }
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.5)',
              font: {
                size: 10,
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
              }
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.08)',
              lineWidth: 1,
            },
            beginAtZero: true,
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
              title: (context) => {
                return `Tổn Thất: ${context[0].label}`;
              },
              label: (context) => {
                const value = context.parsed.y;
                const percentage = (value * 100).toFixed(1);
                return `Tần Suất Tương Đối: ${value.toFixed(4)} (${percentage}%)`;
              }
            }
          }
        },
        animation: {
          duration: 600,
          easing: 'easeInOutQuart',
        },
        interaction: {
          mode: 'index',
          intersect: false,
        }
      }
    });
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

    if (document.getElementById('financial-histogram-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'financial-histogram-styles';
    style.textContent = `
      /* FinancialHistogram Component Styles */
      .financial-histogram-wrapper {
        background: rgba(15, 15, 20, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 300px;
      }

      .financial-histogram-canvas {
        max-width: 100%;
        height: auto !important;
      }

      /* Empty state */
      .financial-histogram-empty {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 60px 20px;
        background: rgba(20, 20, 25, 0.4);
        border: 1px dashed rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        min-height: 300px;
      }

      .financial-histogram-empty-content {
        text-align: center;
        max-width: 400px;
      }

      .financial-histogram-empty-title {
        font-size: 16px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        margin-bottom: 8px;
      }

      .financial-histogram-empty-description {
        font-size: 14px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        margin-bottom: 4px;
      }

      .financial-histogram-empty-note {
        font-size: 12px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.4);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        margin-top: 8px;
        font-style: italic;
      }

      /* Error state */
      .financial-histogram-error {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 8px;
        padding: 60px 20px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        min-height: 300px;
      }

      .financial-histogram-error-text {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.6);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
      }

      .financial-histogram-error-hint {
        font-size: 12px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.4);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
        margin-top: 4px;
      }

      /* Responsive adjustments */
      @media (max-width: 640px) {
        .financial-histogram-wrapper {
          padding: 16px;
          min-height: 250px;
        }
      }

      /* Accessibility: Reduced motion preference */
      @media (prefers-reduced-motion: reduce) {
        .financial-histogram-wrapper {
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
  }
}