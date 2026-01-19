/**
 * LossCurve Component
 * 
 * Visualizes tail risk using Chart.js line chart.
 * Shows probability of exceeding a given loss.
 * 
 * @class LossCurve
 * @exports LossCurve
 * @requires Chart.js (must be loaded globally or via CDN)
 */
export class LossCurve {
  /**
   * Initialize the LossCurve component
   */
  constructor() {
    this.container = null;
    this.canvas = null;
    this.chartInstance = null;
    this.chartId = `loss-curve-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Chart data object
   * @param {Array<number>} data.losses - Loss values (USD)
   * @param {Array<number>} data.probabilities - Probability of exceeding loss (0-1)
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
    const { losses = [], probabilities = [] } = data;
    
    // Build financial data object for state analysis
    const financialDataForCheck = {
      distribution: losses.length > 0 ? losses : null,
      expectedLoss: financialData.expectedLoss ?? financialData.meanLoss ?? null,
      var95: financialData.var95 ?? financialData.p95 ?? null,
      cvar: financialData.cvar ?? financialData.maxLoss ?? null,
      cargoValue: financialData.cargoValue ?? null
    };

    // Check if this is a zero-impact scenario
    const isZeroImpact = this._isZeroImpactScenario(financialDataForCheck, losses, probabilities);
    
    if (isZeroImpact) {
      this._renderZeroImpactState(scenario);
      return;
    }

    // Check if Chart.js is available (support both global Chart and window.Chart)
    const ChartLib = typeof Chart !== 'undefined' ? Chart : (typeof window !== 'undefined' && typeof window.Chart !== 'undefined' ? window.Chart : null);
    if (!ChartLib) {
      el.innerHTML = `
        <div class="loss-curve-error">
          <div class="loss-curve-error-text">Biểu đồ không khả dụng</div>
          <div class="loss-curve-error-hint">Dữ liệu rủi ro đuôi có sẵn trong biểu đồ tần suất tài chính phía trên</div>
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
    console.log('[DEBUG LossCurve.update] Starting update', {
      hasContainer: !!this.container,
      hasLosses: Array.isArray(data.losses) && data.losses.length > 0,
      hasProbabilities: Array.isArray(data.probabilities) && data.probabilities.length > 0,
      hasFinancialData: !!data.financialData,
      hasScenario: !!data.scenario,
      scenarioType: data.scenario?.type
    });

    if (!this.container) {
      console.warn('[DEBUG LossCurve.update] No container!');
      return;
    }

    const { losses = [], probabilities = [], financialData = {}, scenario = null } = data;
    console.log('[DEBUG LossCurve.update] Extracted data:', {
      lossesLength: losses.length,
      probabilitiesLength: probabilities.length,
      financialDataKeys: Object.keys(financialData),
      scenario: scenario
    });

    // ENGINE-FIRST: Re-check zero-impact scenario on update
    const financialDataForCheck = {
      distribution: losses.length > 0 ? losses : null,
      expectedLoss: financialData.expectedLoss ?? financialData.meanLoss ?? null,
      var95: financialData.var95 ?? financialData.p95 ?? null,
      cvar: financialData.cvar ?? financialData.maxLoss ?? null,
      cargoValue: financialData.cargoValue ?? null
    };

    const isZeroImpact = this._isZeroImpactScenario(financialDataForCheck, losses, probabilities);
    console.log('[DEBUG LossCurve.update] Zero-impact check:', {
      isZeroImpact,
      financialDataForCheck
    });

    // If zero-impact and chart exists, destroy it and show empty state
    if (isZeroImpact) {
      console.log('[DEBUG LossCurve.update] Zero-impact detected, rendering empty state with scenario:', scenario);
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

    // Prepare data
    const prepared = this._prepareData(losses, probabilities);

    if (!prepared || !prepared.points || prepared.points.length === 0) {
      this.chartInstance.data.labels = [];
      this.chartInstance.data.datasets[0].data = [];
      const highColor = this._getCSSColor('--risk-high', '#ff4466');
      this.chartInstance.data.datasets[0].backgroundColor = this._toRgba(highColor, 0.15);
      this.chartInstance.data.datasets[0].borderColor = highColor;
    } else {
      // Update chart data
      this.chartInstance.data.labels = prepared.labels;
      this.chartInstance.data.datasets[0].data = prepared.points;
      this.chartInstance.data.datasets[0].backgroundColor = prepared.fillColor;
      this.chartInstance.data.datasets[0].borderColor = prepared.lineColor;
    }

    // Update annotations if P95/P99 found
    if (prepared && (prepared.p95Index !== null || prepared.p99Index !== null)) {
      this._updateAnnotations(prepared);
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
   * @param {Array<number>} losses - Loss values
   * @param {Array<number>} probabilities - Probabilities
   * @returns {boolean} True if all values are zero/null
   */
  _isZeroImpactScenario(financialData, losses, probabilities) {
    // Check loss values array if available
    const hasLosses = Array.isArray(losses) && losses.length > 0;
    const lossesHaveNonZero = hasLosses && losses.some(loss => {
      const lossVal = parseFloat(loss);
      return !isNaN(lossVal) && lossVal > 0;
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

    // Zero-impact if losses have no non-zero values AND all metrics are zero
    return !lossesHaveNonZero && allMetricsZero;
  }

  /**
   * Render zero-impact empty state
   * @private
   * @param {Object} scenario - Optional scenario classification
   */
  _renderZeroImpactState(scenario = null) {
    console.log('[DEBUG LossCurve._renderZeroImpactState] Starting', { scenario });
    
    if (!this.container) {
      console.warn('[DEBUG LossCurve._renderZeroImpactState] No container!');
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
    console.log('[DEBUG LossCurve._renderZeroImpactState] Classifier check:', {
      hasClassifier: !!classifier,
      hasGetFinancialEmptyState: classifier && typeof classifier.getFinancialEmptyState === 'function'
    });
    
    if (scenario && classifier && typeof classifier.getFinancialEmptyState === 'function') {
      emptyState = classifier.getFinancialEmptyState(scenario);
      console.log('[DEBUG LossCurve._renderZeroImpactState] Using classifier empty state:', emptyState);
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
      <div class="loss-curve-empty ${scenario?.type === 'OPERATIONAL_RISK_ONLY' ? 'scenario-operational-risk' : ''}">
        <div class="loss-curve-empty-content">
          <div class="loss-curve-empty-title">${this._escapeHtml(emptyState.title)}</div>
          <div class="loss-curve-empty-description">${this._escapeHtml(emptyState.description)}</div>
          <div class="loss-curve-empty-note">${this._escapeHtml(emptyState.note)}</div>
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
   * @param {Array<number>} losses - Loss values
   * @param {Array<number>} probabilities - Probabilities
   * @returns {Object|null} Prepared data or null if invalid
   */
  _prepareData(losses, probabilities) {
    if (!Array.isArray(losses) || !Array.isArray(probabilities) || losses.length === 0) {
      return null;
    }

    // Pair losses with probabilities and sort by loss
    const pairs = losses.map((loss, idx) => ({
      loss: Math.max(0, parseFloat(loss) || 0),
      probability: Math.max(0, Math.min(1, parseFloat(probabilities[idx] || 0))),
      originalIndex: idx
    })).sort((a, b) => a.loss - b.loss);

    // Enforce monotonic tail probability (loss ↑ ⇒ probability ↓)
    for (let i = 1; i < pairs.length; i++) {
      pairs[i].probability = Math.min(
        pairs[i - 1].probability,
        pairs[i].probability
      );
    }

    // Get colors from CSS variables
    const highColor = this._getCSSColor('--risk-high', '#ff4466');
    const fillColor = this._toRgba(highColor, 0.15);

    // Build chart data
    const labels = [];
    const points = [];
    let p95Index = null;
    let p99Index = null;
    let closestP95 = Infinity;
    let closestP99 = Infinity;

    pairs.forEach((pair, idx) => {
      labels.push(this._formatUSD(pair.loss));
      points.push({
        x: pair.loss,
        y: pair.probability
      });

      // Find P95 (probability closest to 0.05)
      const dist95 = Math.abs(pair.probability - 0.05);
      if (dist95 < closestP95) {
        closestP95 = dist95;
        p95Index = idx;
      }

      // Find P99 (probability closest to 0.01)
      const dist99 = Math.abs(pair.probability - 0.01);
      if (dist99 < closestP99) {
        closestP99 = dist99;
        p99Index = idx;
      }
    });

    return {
      labels,
      points,
      pairs,
      lineColor: highColor,
      fillColor: fillColor,
      p95Index,
      p99Index
    };
  }

  /**
   * Update chart annotations for P95/P99
   * @private
   * @param {Object} prepared - Prepared data
   */
  _updateAnnotations(prepared) {
    const plugins = this.chartInstance.options.plugins;
    if (!plugins || !plugins.annotation || !plugins.annotation.annotations) {
      return;
    }

    const annotations = {};

    if (prepared.p95Index !== null) {
      const p95Point = prepared.points[prepared.p95Index];
      annotations.p95 = {
        type: 'line',
        xMin: p95Point.x,
        xMax: p95Point.x,
        borderColor: prepared.lineColor,
        borderWidth: 2,
        borderDash: [5, 5],
        label: {
          display: true,
          content: 'Tổn Thất P95',
          position: 'start',
          backgroundColor: 'rgba(15, 15, 20, 0.9)',
          color: 'rgba(255, 255, 255, 0.9)',
          font: {
            size: 11,
            weight: '600',
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
          },
          padding: 6,
          cornerRadius: 4,
        }
      };
    }

    if (prepared.p99Index !== null) {
      const p99Point = prepared.points[prepared.p99Index];
      annotations.p99 = {
        type: 'line',
        xMin: p99Point.x,
        xMax: p99Point.x,
        borderColor: prepared.lineColor,
        borderWidth: 2,
        borderDash: [5, 5],
        label: {
          display: true,
          content: 'Tổn Thất P99',
          position: 'start',
          backgroundColor: 'rgba(15, 15, 20, 0.9)',
          color: 'rgba(255, 255, 255, 0.9)',
          font: {
            size: 11,
            weight: '600',
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif',
          },
          padding: 6,
          cornerRadius: 4,
        }
      };
    }

    this.chartInstance.options.plugins.annotation.annotations = annotations;
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
   * Convert color string to rgba with alpha
   * @private
   * @param {string} colorString - Color string (hex, rgb, or rgba)
   * @param {number} alpha - Alpha value (0-1)
   * @returns {string} RGBA string
   */
  _toRgba(colorString, alpha) {
    if (!colorString) {
      return 'rgba(255, 68, 102, 0.15)';
    }

    // Handle hex colors (#RRGGBB or #RGB)
    if (colorString.startsWith('#')) {
      let hex = colorString.replace('#', '');
      if (hex.length === 3) {
        hex = hex.split('').map(char => char + char).join('');
      }
      const bigint = parseInt(hex, 16);
      if (isNaN(bigint)) {
        return 'rgba(255, 68, 102, 0.15)';
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
    return 'rgba(255, 68, 102, 0.15)';
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
   * Format probability as percentage
   * @private
   * @param {number} value - Probability (0-1)
   * @returns {string} Formatted percentage string
   */
  _formatProbability(value) {
    const num = parseFloat(value);
    if (isNaN(num)) return '0%';
    return `${(num * 100).toFixed(1)}%`;
  }

  /**
   * Create canvas element for the chart
   * @private
   */
  _createCanvas() {
    this.container.innerHTML = `
      <div class="loss-curve-wrapper">
        <canvas id="${this.chartId}" class="loss-curve-canvas"></canvas>
      </div>
    `;
    
    this.canvas = document.getElementById(this.chartId);
  }

  /**
   * Initialize the Chart.js line chart
   * @private
   * @param {Object} data - Chart data
   */
  _initChart(data) {
    const {
      losses = [],
      probabilities = [],
    } = data;

    // Prepare data
    const prepared = this._prepareData(losses, probabilities);

    const highColor = this._getCSSColor('--risk-high', '#ff4466');
    const fillColor = this._toRgba(highColor, 0.15);

    const ctx = this.canvas.getContext('2d');
    
    const ChartLib = typeof Chart !== 'undefined' ? Chart : (typeof window !== 'undefined' && typeof window.Chart !== 'undefined' ? window.Chart : null);
    if (!ChartLib) {
      this._renderError('Biểu đồ không khả dụng');
      return;
    }
    this.chartInstance = new ChartLib(ctx, {
      type: 'line',
      data: {
        labels: prepared ? prepared.labels : [],
        datasets: [{
          label: 'Xác Suất Vượt Quá',
          data: prepared ? prepared.points : [],
          backgroundColor: prepared ? prepared.fillColor : fillColor,
          borderColor: prepared ? prepared.lineColor : highColor,
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: prepared ? prepared.lineColor : highColor,
          pointHoverBorderColor: '#ffffff',
          pointHoverBorderWidth: 2,
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
            type: 'linear',
            position: 'bottom',
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
              },
              callback: (value) => {
                return this._formatUSD(value);
              }
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.08)',
              lineWidth: 1,
            }
          },
          y: {
            min: 0,
            max: 1,
            title: {
              display: true,
              text: 'Probability of Exceedance',
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
              },
              callback: (value) => {
                return this._formatProbability(value);
              }
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.08)',
              lineWidth: 1,
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
              title: (context) => {
                const point = context[0];
                return `Tổn Thất: ${this._formatUSD(point.parsed.x)}`;
              },
              label: (context) => {
                const probability = context.parsed.y;
                return `Xác Suất: ${this._formatProbability(probability)}`;
              }
            }
          },
          annotation: prepared && (prepared.p95Index !== null || prepared.p99Index !== null) ? {
            annotations: {}
          } : undefined
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

    // Set up annotations after chart creation
    if (prepared && (prepared.p95Index !== null || prepared.p99Index !== null)) {
      this._updateAnnotations(prepared);
    }
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

    if (document.getElementById('loss-curve-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'loss-curve-styles';
    style.textContent = `
      /* LossCurve Component Styles */
      .loss-curve-wrapper {
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

      .loss-curve-canvas {
        max-width: 100%;
        height: auto !important;
      }

      /* Empty state */
      .loss-curve-empty {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 60px 20px;
        background: rgba(20, 20, 25, 0.4);
        border: 1px dashed rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        min-height: 300px;
      }

      .loss-curve-empty-content {
        text-align: center;
        max-width: 400px;
      }

      .loss-curve-empty-title {
        font-size: 16px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        margin-bottom: 8px;
      }

      .loss-curve-empty-description {
        font-size: 14px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        margin-bottom: 4px;
      }

      .loss-curve-empty-note {
        font-size: 12px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.4);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        margin-top: 8px;
        font-style: italic;
      }

      /* Error state */
      .loss-curve-error {
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

      .loss-curve-error-text {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.6);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
      }

      .loss-curve-error-hint {
        font-size: 12px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.4);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
        margin-top: 4px;
      }

      /* Responsive adjustments */
      @media (max-width: 640px) {
        .loss-curve-wrapper {
          padding: 16px;
          min-height: 250px;
        }
      }

      /* Accessibility: Reduced motion preference */
      @media (prefers-reduced-motion: reduce) {
        .loss-curve-wrapper {
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