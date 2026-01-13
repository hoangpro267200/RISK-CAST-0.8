/**
 * RiskRadar Component
 * 
 * Visually summarizes how the overall risk score is composed from multiple risk layers.
 * This is the ONLY main chart on the Results page.
 * 
 * Answers: "Which risk dimensions are driving the overall risk?"
 * 
 * @class RiskRadar
 */
class RiskRadar {
  /**
   * Initialize the RiskRadar component
   */
  constructor() {
    this.container = null;
    this.canvas = null;
    this.chartInstance = null;
    this.chartId = `risk-radar-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Chart data
   * @param {Array<string>} data.labels - Array of risk layer names
   * @param {Array<number>} data.values - Array of risk scores (0-100)
   */
  mount(el, data = {}) {
    if (!el) {
      console.warn('RiskRadar: No element provided for mounting');
      return;
    }

    this.container = el;
    this._injectStyles();

    // Check if Chart.js is available
    const ChartLib = this._getChartLib();
    if (!ChartLib) {
      this._renderError('Biểu đồ không khả dụng');
      return;
    }

    // Validate data
    const labels = Array.isArray(data.labels) ? data.labels : [];
    const values = Array.isArray(data.values) ? data.values : [];

    if (labels.length === 0 || values.length === 0) {
      this._renderEmptyState();
      return;
    }

    this._createCanvas();
    this._initChart(labels, values);
  }

  /**
   * Update the chart with new data
   * @param {Object} data - New chart data
   */
  update(data = {}) {
    if (!this.container) {
      console.warn('RiskRadar: Component not mounted');
      return;
    }

    if (!this.chartInstance) {
      // Try to reinitialize if chart doesn't exist
      this.mount(this.container, data);
      return;
    }

    const ChartLib = this._getChartLib();
    if (!ChartLib) {
      this._renderError('Biểu đồ không khả dụng');
      return;
    }

    const labels = Array.isArray(data.labels) ? data.labels : [];
    const values = Array.isArray(data.values) ? data.values : [];

    if (labels.length === 0 || values.length === 0) {
      this._renderEmptyState();
      return;
    }

    // Normalize data lengths
    const normalizedValues = this._normalizeValues(values, labels.length);

    // Update chart data
    this.chartInstance.data.labels = labels;
    this.chartInstance.data.datasets[0].data = normalizedValues;

    try {
      this.chartInstance.update('none');
    } catch (e) {
      console.warn('RiskRadar: Chart update failed', e);
    }
  }

  /**
   * Cleanup and destroy component
   */
  destroy() {
    if (this.chartInstance) {
      try {
        this.chartInstance.destroy();
      } catch (e) {
        // Silent cleanup
      }
      this.chartInstance = null;
    }
    this.container = null;
    this.canvas = null;
  }

  /**
   * Get Chart.js library reference
   * @private
   * @returns {Object|null} Chart.js library or null if not available
   */
  _getChartLib() {
    if (typeof Chart !== 'undefined') {
      return Chart;
    }
    if (typeof window !== 'undefined' && typeof window.Chart !== 'undefined') {
      return window.Chart;
    }
    return null;
  }

  /**
   * Normalize and clamp values array
   * @private
   * @param {Array<number>} values - Input values
   * @param {number} expectedLength - Expected array length
   * @returns {Array<number>} Normalized values
   */
  _normalizeValues(values, expectedLength) {
    const length = Math.max(0, Math.floor(expectedLength));
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
   * Create canvas element for the chart
   * @private
   */
  _createCanvas() {
    this.container.innerHTML = `
      <div class="risk-radar-wrapper">
        <canvas id="${this.chartId}" class="risk-radar-canvas"></canvas>
      </div>
    `;
    
    this.canvas = document.getElementById(this.chartId);
  }

  /**
   * Initialize the Chart.js radar chart
   * @private
   * @param {Array<string>} labels - Risk layer names
   * @param {Array<number>} values - Risk scores
   */
  _initChart(labels, values) {
    if (!this.canvas) {
      return;
    }

    const ChartLib = this._getChartLib();
    if (!ChartLib) {
      this._renderError('Biểu đồ không khả dụng');
      return;
    }

    const normalizedValues = this._normalizeValues(values, labels.length);
    const ctx = this.canvas.getContext('2d');

    this.chartInstance = new ChartLib(ctx, {
      type: 'radar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Lớp Rủi Ro',
          data: normalizedValues,
          backgroundColor: 'rgba(255, 204, 0, 0.15)',
          borderColor: '#ffcc00',
          borderWidth: 2,
          pointBackgroundColor: '#ffcc00',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: '#ffcc00',
          pointHoverBorderColor: '#ffffff',
          pointHoverBorderWidth: 2,
        }]
      },
      options: {
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
                return `${context.parsed.r}`;
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
      }
    });
  }

  /**
   * Render error state
   * @private
   * @param {string} message - Error message
   */
  _renderError(message) {
    this.container.innerHTML = `
      <div class="risk-radar-error">
        <div class="risk-radar-error-text">${this._escapeHtml(message)}</div>
      </div>
    `;
  }

  /**
   * Render empty state
   * @private
   */
  _renderEmptyState() {
    this.container.innerHTML = `
      <div class="risk-radar-empty">
        <div class="risk-radar-empty-text">Không có dữ liệu rủi ro</div>
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
   * Inject component styles into the document head
   * @private
   */
  _injectStyles() {
    if (this._stylesInjected) {
      return;
    }

    if (document.getElementById('risk-radar-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'risk-radar-styles';
    style.textContent = `
      /* RiskRadar Component Styles */
      .risk-radar-wrapper {
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 300px;
      }

      .risk-radar-canvas {
        max-width: 100%;
        height: auto !important;
      }

      /* Empty state */
      .risk-radar-empty {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 60px 20px;
        background: rgba(20, 20, 25, 0.4);
        border: 1px dashed rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        min-height: 300px;
      }

      .risk-radar-empty-text {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
      }

      /* Error state */
      .risk-radar-error {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 60px 20px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        min-height: 300px;
      }

      .risk-radar-error-text {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.6);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        text-align: center;
      }

      /* Responsive adjustments */
      @media (max-width: 640px) {
        .risk-radar-wrapper {
          padding: 16px;
          min-height: 250px;
        }

        .risk-radar-empty,
        .risk-radar-error {
          padding: 40px 16px;
          min-height: 250px;
        }
      }

      /* Accessibility: Reduced motion preference */
      @media (prefers-reduced-motion: reduce) {
        .risk-radar-wrapper {
          /* Chart.js handles animation internally */
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}

export default RiskRadar;





