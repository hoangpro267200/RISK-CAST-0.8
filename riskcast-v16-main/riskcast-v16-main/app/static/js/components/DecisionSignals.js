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
 * DecisionSignals Component
 * 
 * Executive Decision Signals panel that displays risk intelligence
 * from backend as actionable signals for enterprise leadership.
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - Receives decision data from backend (MANDATORY)
 * - All signals, urgency, confidence MUST come from backend
 * - Only formats/clamps values for display
 * 
 * @class DecisionSignals
 * @exports DecisionSignals
 */
export class DecisionSignals {
  /**
   * Initialize the DecisionSignals component
   * @param {Object} options - Component options
   * @param {Function} [options.onSignalClick] - Optional callback (not used in read-only mode)
   */
  constructor(options = {}) {
    this.container = null;
    this._options = options;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Decision data object
   * @param {Object} data.decision - Decision data
   * @param {string} data.decision.riskLevel - Risk level: 'low', 'medium', or 'high'
   * @param {number} data.decision.overallRiskScore - Overall risk score (0-100)
   * @param {Array<Object>} data.decision.dominantLayers - Top risk layers
   * @param {string} data.decision.dominantLayers[].name - Layer name
   * @param {number} data.decision.dominantLayers[].score - Layer score (0-100)
   * @param {Array<Object>} data.decision.keyDrivers - Key risk drivers
   * @param {string} data.decision.keyDrivers[].factor - Factor name
   * @param {number} data.decision.keyDrivers[].impact - Impact value (0-1)
   * @param {number} data.decision.keyDrivers[].probability - Probability value (0-1)
   * @param {Object} data.decision.loss - Loss metrics
   * @param {number} data.decision.loss.p95 - P95 loss value
   * @param {number} data.decision.loss.p99 - P99 loss value
   * @param {number} data.decision.loss.tailContribution - Tail risk contribution (0-100)
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
   * @param {Object} data - Updated decision data
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
      <div class="decision-signals-wrapper">
        <div class="decision-signals-header">
          <div class="decision-signals-header-left">
            <h2 class="decision-signals-title">Tín Hiệu Quyết Định Điều Hành</h2>
            <p class="decision-signals-subtitle">Derived from current risk intelligence</p>
          </div>
          <div class="decision-signals-header-right" id="decision-signals-badge"></div>
        </div>
        <div class="decision-signals-posture" id="decision-signals-posture"></div>
        <div class="decision-signals-cards" id="decision-signals-cards"></div>
        <div class="decision-signals-warning" id="decision-signals-warning"></div>
      </div>
    `;
  }

  /**
   * Render all sections
   * @private
   * @param {Object} data - Decision data
   */
  _render(data) {
    const decision = data.decision || {};

    if (!decision || Object.keys(decision).length === 0) {
      this._renderEmpty();
      return;
    }

    const normalized = this._normalizeData(decision);

    const badgeEl = this.container.querySelector('#decision-signals-badge');
    const postureEl = this.container.querySelector('#decision-signals-posture');
    const cardsEl = this.container.querySelector('#decision-signals-cards');
    const warningEl = this.container.querySelector('#decision-signals-warning');

    if (badgeEl) {
      badgeEl.innerHTML = this._renderRiskBadge(normalized.riskLevel);
    }
    if (postureEl) {
      postureEl.innerHTML = this._renderPosture(normalized);
    }
    if (cardsEl) {
      cardsEl.innerHTML = this._renderSignals(normalized);
    }
    if (warningEl) {
      warningEl.innerHTML = this._renderWarning(normalized);
    }
  }

  /**
   * Render empty state
   * @private
   */
  _renderEmpty() {
    this.container.innerHTML = `
      <div class="decision-signals-wrapper">
        <div class="decision-signals-empty">
          <p class="decision-signals-empty-text">Không có dữ liệu quyết định</p>
        </div>
      </div>
    `;
  }

  /**
   * Normalize data for UI display (formatting only, no business logic)
   * ARCHITECTURE: ENGINE-FIRST
   * Backend MUST provide all computed values (riskLevel, compositeScore, etc.)
   * This function only formats/clamps values for display, does NOT compute or derive
   * @private
   * @param {Object} decision - Decision data from backend (already computed)
   * @returns {Object} Formatted data for UI
   */
  _normalizeData(decision) {
    const score = this._clampScore(decision.overallRiskScore);
    // ARCHITECTURE: ENGINE-FIRST - Backend MUST provide riskLevel already computed
    // Do NOT derive or compute risk level - only use what backend provides
    const riskLevel = decision.riskLevel || 'medium'; // Fallback to 'medium' if missing, but backend should ALWAYS provide

    // Extract and format dominant layers (backend MUST provide these already sorted/selected)
    const dominantLayers = (Array.isArray(decision.dominantLayers) ? decision.dominantLayers : [])
      .map(l => ({
        name: String(l.name || 'Unknown'),
        score: this._clampScore(l.score)
      }))
      .slice(0, 2); // Take top 2 as provided by backend

    // Extract and format key drivers (backend MUST provide compositeScore)
    const keyDrivers = (Array.isArray(decision.keyDrivers) ? decision.keyDrivers : [])
      .map(d => ({
        factor: String(d.factor || 'Unknown'),
        impact: this._clampValue(d.impact),
        probability: this._clampValue(d.probability),
        // Use compositeScore from backend if available, otherwise use provided score
        score: d.compositeScore != null ? parseFloat(d.compositeScore) : (d.score != null ? parseFloat(d.score) : 0)
      }))
      .slice(0, 3); // Take top 3 as provided by backend

    const loss = decision.loss || {};
    const tailContribution = this._clampValue(loss.tailContribution) * 100;
    const p95 = loss.p95 != null && Number.isFinite(loss.p95) ? parseFloat(loss.p95) : null;
    const p99 = loss.p99 != null && Number.isFinite(loss.p99) ? parseFloat(loss.p99) : null;

    // Extract signals from backend (MANDATORY)
    const signals = decision.signals || [];

    return {
      riskLevel,
      score,
      dominantLayers,
      keyDrivers,
      tailContribution,
      p95,
      p99,
      confidence: decision.confidence, // Backend MUST provide
      signals: decision.signals || [], // Backend MUST provide pre-computed signals array
      warnings: decision.warnings || [] // Backend MUST provide warnings array
    };
  }

  /**
   * Render risk level badge
   * @private
   * @param {string} riskLevel - Risk level
   * @returns {string} HTML string
   */
  _renderRiskBadge(riskLevel) {
    const level = riskLevel.toLowerCase();
    const classMap = {
      'high': 'risk-high',
      'medium': 'risk-medium',
      'low': 'risk-low'
    };
    
    // Translate risk level badge text
    const riskLevelMap = {
      'high': 'CAO',
      'medium': 'TRUNG BÌNH',
      'low': 'THẤP'
    };
    const riskLevelText = riskLevelMap[level] || 'TRUNG BÌNH';
    const className = classMap[level] || 'risk-medium';

    return `
      <span class="decision-signals-badge ${className}">${riskLevelText}</span>
    `;
  }

  /**
   * Render executive posture
   * @private
   * @param {Object} normalized - Normalized data
   * @returns {string} HTML string
   */
  _renderPosture(normalized) {
    const postureMap = {
      'high': 'Defensive',
      'medium': 'Balanced',
      'low': 'Opportunistic'
    };
    const posture = postureMap[normalized.riskLevel] || 'Balanced';

    const confidence = this._extractConfidence(normalized);
    const confidenceText = confidence.charAt(0) + confidence.slice(1).toLowerCase();

    return `
      <div class="decision-signals-posture-content">
        <span class="decision-signals-posture-label">Tư Thế:</span>
        <span class="decision-signals-posture-value">${posture}</span>
        <span class="decision-signals-posture-confidence">Độ Tin Cậy: ${confidenceText}</span>
      </div>
    `;
  }

  /**
   * Extract confidence level from backend data
   * ARCHITECTURE: ENGINE-FIRST
   * Backend MUST provide confidence already computed
   * This function only extracts/formats, does NOT compute
   * @private
   * @param {Object} normalized - Normalized data (should have confidence from backend)
   * @returns {string} Confidence level display string
   */
  _extractConfidence(normalized) {
    // Backend MUST provide confidence - check in normalized data or use default
    // This is a UI formatting function only, NOT business logic
    if (normalized.confidence != null) {
      const conf = parseFloat(normalized.confidence);
      if (conf >= 0.8) return 'HIGH';
      if (conf >= 0.5) return 'MEDIUM';
      return 'LOW';
    }
    
    // If missing, log warning and use neutral
    console.warn('[ENGINE-FIRST] DecisionSignals: confidence missing from backend data. Using neutral fallback.');
    return 'MEDIUM'; // Neutral fallback for display only
  }

  /**
   * Extract and render decision signals from backend
   * ARCHITECTURE: ENGINE-FIRST
   * Backend MUST provide signals array (pre-computed)
   * This function only extracts and renders, does NOT generate or compute
   * @private
   * @param {Object} normalized - Normalized data (should have signals from backend)
   * @returns {string} HTML string
   */
  _renderSignals(normalized) {
    // Backend MUST provide signals array
    const signals = normalized.signals || [];
    
    if (!Array.isArray(signals) || signals.length === 0) {
      console.warn('[ENGINE-FIRST] DecisionSignals: No signals provided by backend');
      return '<p class="decision-signals-empty-text">Không có tín hiệu từ backend</p>';
    }

    // Render top signals (backend should already provide them sorted/selected)
    const topSignals = signals.slice(0, 5); // Take top 5 from backend
    return topSignals.map(signal => this._renderSignalCard(signal)).join('');
  }

  /**
   * ARCHITECTURE: ENGINE-FIRST
   * 
   * REMOVED FUNCTIONS (Business Logic Violations):
   * - _generateSignalCandidates() - Generated signals based on rules (VIOLATION)
   * - _selectTopSignals() - Selected signals based on urgency sorting (VIOLATION)
   * - _getDefaultSignals() - Generated default signals (VIOLATION)
   * 
   * Backend MUST provide signals array in decision.signals with:
   * - type: string ('Contract', 'Network', 'Monitoring', etc.)
   * - signal: string (actionable signal text)
   * - rationale: string (explanation)
   * - urgency: 'HIGH' | 'MEDIUM' | 'LOW' (pre-computed by backend)
   */

  /**
   * Render single signal card
   * @private
   * @param {Object} signal - Signal object
   * @returns {string} HTML string
   */
  _renderSignalCard(signal) {
    const urgencyClass = `urgency-${signal.urgency.toLowerCase()}`;
    const typeClass = `type-${signal.type.toLowerCase().replace(/\//g, '-')}`;
    
    // Translate type and urgency labels
    const typeMap = {
      'Contract': 'Hợp Đồng',
      'Network': 'Mạng Lưới',
      'Monitoring': 'Giám Sát',
      'Inventory': 'Tồn Kho',
      'Carrier/Supplier': 'Nhà Vận Chuyển'
    };
    const urgencyMap = {
      'HIGH': 'CAO',
      'MEDIUM': 'TRUNG BÌNH',
      'LOW': 'THẤP'
    };
    const typeText = typeMap[signal.type] || signal.type;
    const urgencyText = urgencyMap[signal.urgency] || signal.urgency;

    return `
      <div class="decision-signals-card">
        <div class="decision-signals-card-header">
          <span class="decision-signals-card-type ${typeClass}">${this._escapeHtml(typeText)}</span>
          <span class="decision-signals-card-urgency ${urgencyClass}">${urgencyText}</span>
        </div>
        <div class="decision-signals-card-body">
          <p class="decision-signals-card-signal">${this._escapeHtml(signal.signal)}</p>
          <p class="decision-signals-card-rationale">${this._escapeHtml(signal.rationale)}</p>
        </div>
      </div>
    `;
  }

  /**
   * Render warning section
   * ARCHITECTURE: ENGINE-FIRST
   * Backend MUST provide warnings array
   * This function only renders warnings from backend, does NOT compute them
   * @private
   * @param {Object} normalized - Normalized data (should have warnings from backend)
   * @returns {string} HTML string
   */
  _renderWarning(normalized) {
    // Backend MUST provide warnings array
    const warnings = normalized.warnings || [];
    
    if (!Array.isArray(warnings) || warnings.length === 0) {
      // No warnings from backend - return empty (do NOT compute/generate warnings)
      return '';
    }

    // Render first warning from backend
    const warning = warnings[0];

    return `
      <div class="decision-signals-warning-content">
        <span class="decision-signals-warning-label">Không nên tối ưu hóa:</span>
        <span class="decision-signals-warning-text">${this._escapeHtml(warning)}</span>
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
   * Clamp value to 0-1 range
   * @private
   * @param {number} value - Input value
   * @returns {number} Clamped value
   */
  _clampValue(value) {
    if (value == null) return 0;
    const num = parseFloat(value);
    if (isNaN(num)) return 0;
    return Math.max(0, Math.min(1, num));
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

    if (document.getElementById('decision-signals-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'decision-signals-styles';
    style.textContent = `
      /* DecisionSignals Component Styles */
      .decision-signals-wrapper {
        background: rgba(15, 15, 20, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 32px;
        display: flex;
        flex-direction: column;
        gap: 24px;
      }

      .decision-signals-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 20px;
        margin-bottom: 8px;
      }

      .decision-signals-header-left {
        flex: 1;
      }

      .decision-signals-title {
        font-size: 20px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin: 0 0 4px 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        letter-spacing: -0.3px;
      }

      .decision-signals-subtitle {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-badge.risk-high {
        background: rgba(255, 68, 102, 0.15);
        color: var(--risk-high, #ff4466);
        border: 1px solid rgba(255, 68, 102, 0.3);
      }

      .decision-signals-badge.risk-medium {
        background: rgba(255, 204, 0, 0.15);
        color: var(--risk-medium, #ffcc00);
        border: 1px solid rgba(255, 204, 0, 0.3);
      }

      .decision-signals-badge.risk-low {
        background: rgba(0, 255, 136, 0.15);
        color: var(--risk-low, #00ff88);
        border: 1px solid rgba(0, 255, 136, 0.3);
      }

      .decision-signals-posture {
        padding: 16px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      }

      .decision-signals-posture-content {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
      }

      .decision-signals-posture-label {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.6);
        font-weight: 500;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-posture-value {
        font-size: 16px;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 600;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-posture-confidence {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        margin-left: auto;
      }

      .decision-signals-cards {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin: 8px 0;
      }

      .decision-signals-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .decision-signals-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
      }

      .decision-signals-card-type {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: rgba(255, 255, 255, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-card-urgency {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 3px 8px;
        border-radius: 4px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-card-urgency.urgency-high {
        background: rgba(255, 68, 102, 0.2);
        color: var(--risk-high, #ff4466);
      }

      .decision-signals-card-urgency.urgency-medium {
        background: rgba(255, 204, 0, 0.2);
        color: var(--risk-medium, #ffcc00);
      }

      .decision-signals-card-urgency.urgency-low {
        background: rgba(0, 255, 136, 0.2);
        color: var(--risk-low, #00ff88);
      }

      .decision-signals-card-body {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .decision-signals-card-signal {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
        line-height: 1.5;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-card-rationale {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.65);
        margin: 0;
        line-height: 1.6;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-warning {
        padding-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
      }

      .decision-signals-warning-content {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        flex-wrap: wrap;
      }

      .decision-signals-warning-label {
        font-size: 13px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-warning-text {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.6);
        font-style: italic;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .decision-signals-empty {
        padding: 60px 20px;
        text-align: center;
      }

      .decision-signals-empty-text {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.4);
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      @media (max-width: 900px) {
        .decision-signals-wrapper {
          padding: 24px 20px;
        }

        .decision-signals-header {
          flex-direction: column;
          align-items: flex-start;
        }

        .decision-signals-cards {
          grid-template-columns: 1fr;
        }

        .decision-signals-posture-content {
          flex-direction: column;
          align-items: flex-start;
        }

        .decision-signals-posture-confidence {
          margin-left: 0;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}

/*
 * Example Usage:
 * 
 * import { DecisionSignals } from './components/DecisionSignals.js';
 * 
 * const ds = new DecisionSignals();
 * ds.mount(document.querySelector('#decisionSignals'), {
 *   decision: {
 *     riskLevel: 'high',
 *     overallRiskScore: 75,
 *     dominantLayers: [
 *       { name: 'Port Congestion', score: 82 },
 *       { name: 'Weather Volatility', score: 68 }
 *     ],
 *     keyDrivers: [
 *       { factor: 'Geopolitical Tension', impact: 0.8, probability: 0.7 },
 *       { factor: 'Carrier Reliability', impact: 0.6, probability: 0.5 }
 *     ],
 *     loss: {
 *       p95: 500000,
 *       p99: 1200000,
 *       tailContribution: 25
 *     }
 *   }
 * });
 */
