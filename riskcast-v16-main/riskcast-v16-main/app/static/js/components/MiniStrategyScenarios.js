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
 * MiniStrategyScenarios Component
 * 
 * Renders executive strategy scenarios from backend.
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - Receives scenarios array from backend (MANDATORY)
 * - Scenarios MUST include: name, risk, loss, color, posture (all pre-computed)
 * - Only formats/clamps values for display
 * 
 * @class MiniStrategyScenarios
 * @exports MiniStrategyScenarios
 */
export class MiniStrategyScenarios {
  /**
   * Initialize the MiniStrategyScenarios component
   */
  constructor() {
    this.container = null;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Strategy data object
   * @param {number} data.baseRiskScore - Base risk score (0-100)
   * @param {string} data.basePosture - Base posture: 'low', 'medium', or 'high'
   */
  mount(el, data = {}) {
    if (!el) {
      return;
    }

    this.container = el;
    this._injectStyles();
    this._createStructure();
    this._render(data);
  }

  /**
   * Update the component with new data
   * @param {Object} data - Updated strategy data
   */
  update(data = {}) {
    if (!this.container) {
      return;
    }

    this._render(data);
  }

  /**
   * Cleanup and destroy component
   */
  destroy() {
    this.container = null;
  }

  /**
   * Create component structure
   * @private
   */
  _createStructure() {
    this.container.innerHTML = `
      <div class="mini-strategy-wrapper">
        <div class="mini-strategy-cards" id="mini-strategy-cards"></div>
      </div>
    `;
  }

  /**
   * Render all scenarios
   * ARCHITECTURE: ENGINE-FIRST
   * Backend MUST provide scenarios array with all pre-computed data
   * @private
   * @param {Object} data - Strategy data from backend
   */
  _render(data) {
    // Extract scenarios from backend (MANDATORY - backend must provide)
    const scenarios = data.scenarios || data.payloadForMiniScenarios?.scenarios || [];
    
    if (!Array.isArray(scenarios) || scenarios.length === 0) {
      console.warn('[ENGINE-FIRST] MiniStrategyScenarios: No scenarios provided by backend');
      this._renderEmpty();
      return;
    }

    // Take first 2 scenarios from backend (backend should provide them pre-computed)
    const scenarioA = scenarios[0] || null;
    const scenarioB = scenarios[1] || null;

    const cardsEl = this.container.querySelector('#mini-strategy-cards');
    if (cardsEl) {
      let html = '';
      if (scenarioA) {
        html += this._renderScenarioCard('A', this._formatScenarioForDisplay(scenarioA));
      }
      if (scenarioB) {
        html += this._renderScenarioCard('B', this._formatScenarioForDisplay(scenarioB));
      }
      cardsEl.innerHTML = html;
    }
  }
  
  /**
   * Format scenario from backend for UI display
   * ARCHITECTURE: ENGINE-FIRST - Only formatting, no computation
   * @private
   * @param {Object} scenario - Scenario from backend
   * @returns {Object} Formatted scenario for display
   */
  _formatScenarioForDisplay(scenario) {
    return {
      title: scenario.title || scenario.name || 'Scenario',
      projectedRisk: this._clampScore(scenario.risk || scenario.projectedRisk || 0),
      resultingPosture: scenario.posture || scenario.resultingPosture || 'BALANCED',
      strategies: Array.isArray(scenario.strategies) ? scenario.strategies : []
    };
  }
  
  /**
   * Render empty state
   * @private
   */
  _renderEmpty() {
    const cardsEl = this.container.querySelector('#mini-strategy-cards');
    if (cardsEl) {
      cardsEl.innerHTML = `
        <div class="mini-strategy-empty">
          <p>Dữ liệu kịch bản không có sẵn từ backend.</p>
        </div>
      `;
    }
  }


  /**
   * Render single scenario card
   * @private
   * @param {string} label - Scenario label (A or B)
   * @param {Object} scenario - Scenario data
   * @returns {string} HTML string
   */
  _renderScenarioCard(label, scenario) {
    const postureClass = `posture-${scenario.resultingPosture.toLowerCase()}`;
    const postureMap = {
      'DEFENSIVE': 'Phòng Thủ',
      'BALANCED': 'Cân Bằng',
      'OPPORTUNISTIC': 'Cơ Hội'
    };
    const postureText = postureMap[scenario.resultingPosture] || scenario.resultingPosture;
    const strategiesHtml = scenario.strategies
      .map(strategy => `<li class="mini-strategy-bullet">${this._escapeHtml(strategy)}</li>`)
      .join('');

    return `
      <div class="mini-strategy-card">
        <div class="mini-strategy-card-header">
          <h3 class="mini-strategy-card-title">${this._escapeHtml(scenario.title)}</h3>
          <div class="mini-strategy-card-metrics">
            <div class="mini-strategy-metric">
              <span class="mini-strategy-metric-label">Rủi Ro Dự Kiến</span>
              <span class="mini-strategy-metric-value">${scenario.projectedRisk}</span>
            </div>
            <div class="mini-strategy-metric">
              <span class="mini-strategy-metric-label">Tư Thế</span>
              <span class="mini-strategy-posture ${postureClass}">${postureText}</span>
            </div>
          </div>
        </div>
        <div class="mini-strategy-card-body">
          <ul class="mini-strategy-list">
            ${strategiesHtml}
          </ul>
        </div>
      </div>
    `;
  }


  /**
   * Clamp score to valid range
   * @private
   * @param {number} score - Input score
   * @returns {number} Clamped score
   */
  _clampScore(score) {
    if (score == null) return 0;
    const num = parseFloat(score);
    if (isNaN(num)) return 0;
    return Math.max(0, Math.min(100, Math.round(num)));
  }

  /**
   * Escape HTML to prevent XSS
   * @private
   * @param {string} str - String to escape
   * @returns {string} Escaped string
   */
  _escapeHtml(str) {
    if (str == null) return '';
    const strValue = String(str);
    const div = document.createElement('div');
    div.textContent = strValue;
    return div.innerHTML;
  }

  /**
   * Inject component styles
   * @private
   */
  _injectStyles() {
    if (this._stylesInjected) {
      return;
    }

    if (document.getElementById('mini-strategy-scenarios-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'mini-strategy-scenarios-styles';
    style.textContent = `
      /* MiniStrategyScenarios Component Styles */
      .mini-strategy-wrapper {
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 32px;
      }

      .mini-strategy-cards {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
      }

      .mini-strategy-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      .mini-strategy-card-header {
        display: flex;
        flex-direction: column;
        gap: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding-bottom: 16px;
      }

      .mini-strategy-card-title {
        font-size: 16px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        letter-spacing: -0.2px;
      }

      .mini-strategy-card-metrics {
        display: flex;
        gap: 24px;
        flex-wrap: wrap;
      }

      .mini-strategy-metric {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .mini-strategy-metric-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: rgba(255, 255, 255, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .mini-strategy-metric-value {
        font-size: 24px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.9);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        letter-spacing: -0.5px;
      }

      .mini-strategy-posture {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 4px 10px;
        border-radius: 6px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .mini-strategy-posture.posture-defensive {
        background: rgba(255, 68, 102, 0.15);
        color: var(--risk-high, #ff4466);
        border: 1px solid rgba(255, 68, 102, 0.3);
      }

      .mini-strategy-posture.posture-balanced {
        background: rgba(255, 204, 0, 0.15);
        color: var(--risk-medium, #ffcc00);
        border: 1px solid rgba(255, 204, 0, 0.3);
      }

      .mini-strategy-posture.posture-opportunistic {
        background: rgba(0, 255, 136, 0.15);
        color: var(--risk-low, #00ff88);
        border: 1px solid rgba(0, 255, 136, 0.3);
      }

      .mini-strategy-card-body {
        flex: 1;
      }

      .mini-strategy-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .mini-strategy-bullet {
        font-size: 13px;
        line-height: 1.6;
        color: rgba(255, 255, 255, 0.7);
        padding-left: 20px;
        position: relative;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .mini-strategy-bullet::before {
        content: '•';
        position: absolute;
        left: 0;
        color: rgba(255, 255, 255, 0.4);
        font-size: 16px;
        line-height: 1.4;
      }

      @media (max-width: 900px) {
        .mini-strategy-wrapper {
          padding: 24px 20px;
        }

        .mini-strategy-cards {
          grid-template-columns: 1fr;
        }

        .mini-strategy-card-metrics {
          flex-direction: column;
          gap: 16px;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}
