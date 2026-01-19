/**
 * MiniGauges Component
 * 
 * Renders a responsive grid of mini gauge cards, each displaying
 * a label, percentage value, and progress bar.
 * Adapts to any number of gauges provided.
 * 
 * @class MiniGauges
 * @exports MiniGauges
 */
export class MiniGauges {
  /**
   * Initialize the MiniGauges component
   */
  constructor() {
    this.container = null;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Array<Object>} gauges - Array of gauge data objects
   * @param {string} gauges[].label - Gauge label/name
   * @param {number} gauges[].value - Gauge value (0-100 percentage)
   */
  mount(el, gauges = []) {
    if (!el) {
      console.warn('MiniGauges: No element provided for mounting');
      return;
    }

    this.container = el;
    this._injectStyles();
    this.render(gauges);
  }

  /**
   * Update the component with new gauge data
   * @param {Array<Object>} gauges - Updated gauge data
   */
  update(gauges = []) {
    if (!this.container) {
      console.warn('MiniGauges: Component not mounted');
      return;
    }
    this.render(gauges);
  }

  /**
   * Clamp value to valid range (0-100)
   * @private
   * @param {number} value - Input value
   * @returns {number} Clamped value
   */
  _clampValue(value) {
    if (value == null || value === undefined) return 0;
    const num = parseFloat(value);
    if (isNaN(num)) return 0;
    return Math.max(0, Math.min(100, num));
  }

  /**
   * Get risk level based on value thresholds (matching GlobalGauge)
   * @private
   * @param {number} value - Gauge value
   * @returns {string} Risk level: 'low', 'medium', or 'high'
   */
  _getRiskLevel(value) {
    if (value < 40) {
      return 'low';
    } else if (value < 70) {
      return 'medium';
    } else {
      return 'high';
    }
  }

  /**
   * Create a single gauge card HTML
   * @private
   * @param {Object} gauge - Gauge data
   * @param {number} index - Gauge index for unique IDs
   * @returns {string} HTML string for gauge card
   */
  _createGaugeCard(gauge, index) {
    const {
      label = 'Untitled',
      value = 0,
    } = gauge;

    const clampedValue = this._clampValue(value);
    const formattedValue = Math.round(clampedValue);
    const riskLevel = this._getRiskLevel(clampedValue);

    return `
      <div class="mini-gauge-card" data-gauge-index="${index}" data-risk-level="${riskLevel}">
        <div class="mini-gauge-header">
          <div class="mini-gauge-label">${this._escapeHtml(label)}</div>
          <div class="mini-gauge-value" data-risk-level="${riskLevel}">${formattedValue}%</div>
        </div>
        <div class="mini-gauge-bar-container">
          <div class="mini-gauge-bar-track"></div>
          <div 
            class="mini-gauge-bar-fill" 
            data-risk-level="${riskLevel}"
            style="width: ${clampedValue}%;"
          ></div>
        </div>
      </div>
    `;
  }

  /**
   * Render the component HTML
   * @private
   * @param {Array<Object>} gauges - Array of gauge data
   */
  render(gauges) {
    // Handle empty array
    if (!Array.isArray(gauges) || gauges.length === 0) {
      this.container.innerHTML = `
        <div class="mini-gauges-empty">
          <div class="mini-gauges-empty-text">Không có dữ liệu gauge</div>
        </div>
      `;
      return;
    }

    // Generate gauge cards HTML
    const gaugeCardsHTML = gauges
      .map((gauge, index) => this._createGaugeCard(gauge, index))
      .join('');

    // Render grid
    this.container.innerHTML = `
      <div class="mini-gauges-grid">
        ${gaugeCardsHTML}
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

    if (document.getElementById('mini-gauges-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'mini-gauges-styles';
    style.textContent = `
      /* MiniGauges Component Styles */
      .mini-gauges-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        padding: 4px;
      }

      /* Responsive grid: 2 columns on tablets, 1 on mobile */
      @media (max-width: 1024px) {
        .mini-gauges-grid {
          grid-template-columns: repeat(2, 1fr);
        }
      }

      @media (max-width: 640px) {
        .mini-gauges-grid {
          grid-template-columns: 1fr;
          gap: 12px;
        }
      }

      /* Individual gauge card */
      .mini-gauge-card {
        background: rgba(20, 20, 25, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        transition: border-color 0.2s ease, background 0.2s ease;
      }

      .mini-gauge-card:hover {
        border-color: rgba(255, 255, 255, 0.12);
        background: rgba(25, 25, 30, 0.7);
      }

      /* Header section */
      .mini-gauge-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 8px;
      }

      .mini-gauge-label {
        font-size: 13px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.75);
        letter-spacing: 0.2px;
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .mini-gauge-value {
        font-size: 18px;
        font-weight: 700;
        letter-spacing: -0.5px;
        white-space: nowrap;
        transition: color 0.3s ease;
        color: var(--risk-low, #00ff88);
      }

      .mini-gauge-value[data-risk-level="low"] {
        color: var(--risk-low, #00ff88);
      }

      .mini-gauge-value[data-risk-level="medium"] {
        color: var(--risk-medium, #ffcc00);
      }

      .mini-gauge-value[data-risk-level="high"] {
        color: var(--risk-high, #ff4466);
      }

      /* Progress bar */
      .mini-gauge-bar-container {
        position: relative;
        height: 6px;
        width: 100%;
        border-radius: 3px;
        overflow: hidden;
      }

      .mini-gauge-bar-track {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 3px;
      }

      .mini-gauge-bar-fill {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        border-radius: 3px;
        transition: width 0.4s ease, background-color 0.3s ease;
        background-color: var(--risk-low, #00ff88);
      }

      .mini-gauge-bar-fill[data-risk-level="low"] {
        background-color: var(--risk-low, #00ff88);
        box-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
      }

      .mini-gauge-bar-fill[data-risk-level="medium"] {
        background-color: var(--risk-medium, #ffcc00);
        box-shadow: 0 0 8px rgba(255, 204, 0, 0.3);
      }

      .mini-gauge-bar-fill[data-risk-level="high"] {
        background-color: var(--risk-high, #ff4466);
        box-shadow: 0 0 8px rgba(255, 68, 102, 0.3);
      }

      /* Empty state */
      .mini-gauges-empty {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 40px 20px;
        background: rgba(20, 20, 25, 0.4);
        border: 1px dashed rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        min-height: 120px;
      }

      .mini-gauges-empty-text {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.4);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
      }

      /* Accessibility: Reduced motion preference */
      @media (prefers-reduced-motion: reduce) {
        .mini-gauge-card,
        .mini-gauge-bar-fill,
        .mini-gauge-value {
          transition: none;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}





