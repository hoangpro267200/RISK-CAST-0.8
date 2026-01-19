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
 * RiskScoreOrb Component
 * 
 * Displays the overall shipment risk score as a dominant visual element.
 * This component represents the single most important insight of the Results page.
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - Receives riskLevel from backend (MANDATORY)
 * - Only formats/clamps values for display
 * - _getRiskLevelCategory() is UI-only for CSS coloring (not business logic)
 * 
 * @class RiskScoreOrb
 */
class RiskScoreOrb {
  /**
   * Initialize the RiskScoreOrb component
   */
  constructor() {
    this.container = null;
    this._stylesInjected = false;
    this.pulseInterval = null;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object|number} data - Risk score data
   * @param {number} [data.overallRiskScore] - Overall risk score (0-100) if data is object
   * @param {string} [data.riskLevel] - Risk level: 'LOW', 'MEDIUM', or 'HIGH' if data is object
   * @param {number} [data] - Direct risk score (0-100) if data is number
   */
  mount(el, data = {}) {
    if (!el) {
      console.warn('RiskScoreOrb: No element provided for mounting');
      return;
    }

    this.container = el;
    this._injectStyles();
    
    // ARCHITECTURE: ENGINE-FIRST - Backend MUST provide riskLevel
    let overallRiskScore, riskLevel;
    if (typeof data === 'number') {
      overallRiskScore = data;
      // Backend MUST provide riskLevel - log warning if missing
      console.warn('[ENGINE-FIRST] RiskScoreOrb: riskLevel not provided for number input. Backend should provide complete data object.');
      riskLevel = 'MEDIUM'; // Neutral fallback for display only
    } else {
      overallRiskScore = data.overallRiskScore || data.score || 0;
      // Backend MUST provide riskLevel already computed
      riskLevel = data.riskLevel;
      if (!riskLevel) {
        console.warn('[ENGINE-FIRST] RiskScoreOrb: riskLevel missing from backend data. Using neutral fallback for display only.');
        riskLevel = 'MEDIUM'; // Neutral fallback for display only, NOT business logic
      }
    }

    this._createStructure(overallRiskScore, riskLevel);
    this._startPulseAnimation();
  }

  /**
   * Update the component with new data
   * @param {Object|number} data - Updated risk score data
   */
  update(data = {}) {
    if (!this.container) {
      console.warn('RiskScoreOrb: Component not mounted');
      return;
    }

    // ARCHITECTURE: ENGINE-FIRST - Backend MUST provide riskLevel
    let overallRiskScore, riskLevel;
    if (typeof data === 'number') {
      overallRiskScore = data;
      console.warn('[ENGINE-FIRST] RiskScoreOrb.update: riskLevel not provided for number input. Backend should provide complete data object.');
      riskLevel = 'MEDIUM'; // Neutral fallback for display only
    } else {
      overallRiskScore = data.overallRiskScore || data.score || 0;
      // Backend MUST provide riskLevel already computed
      riskLevel = data.riskLevel;
      if (!riskLevel) {
        console.warn('[ENGINE-FIRST] RiskScoreOrb.update: riskLevel missing from backend data. Using neutral fallback for display only.');
        riskLevel = 'MEDIUM'; // Neutral fallback for display only, NOT business logic
      }
    }

    const clampedScore = this._clampScore(overallRiskScore);
    const normalizedLevel = this._normalizeRiskLevel(riskLevel);
    
    // Update score display
    const scoreEl = this.container.querySelector('.risk-score-orb-value');
    if (scoreEl) {
      scoreEl.textContent = Math.round(clampedScore);
      scoreEl.setAttribute('data-risk-level', this._getRiskLevelCategory(clampedScore));
    }

    // Update risk level label
    const levelEl = this.container.querySelector('.risk-score-orb-level');
    if (levelEl) {
      levelEl.textContent = this._formatRiskLevel(normalizedLevel);
      levelEl.setAttribute('data-risk-level', this._getRiskLevelCategory(clampedScore));
    }

    // Update orb color
    const orbEl = this.container.querySelector('.risk-score-orb-circle');
    if (orbEl) {
      orbEl.setAttribute('data-risk-level', this._getRiskLevelCategory(clampedScore));
    }
  }

  /**
   * Cleanup and destroy component
   */
  destroy() {
    if (this.pulseInterval) {
      clearInterval(this.pulseInterval);
      this.pulseInterval = null;
    }
    this.container = null;
  }

  /**
   * Create the HTML structure for the orb
   * @private
   * @param {number} score - Risk score (0-100)
   * @param {string} riskLevel - Risk level
   */
  _createStructure(score, riskLevel) {
    const clampedScore = this._clampScore(score);
    const normalizedLevel = this._normalizeRiskLevel(riskLevel);
    const riskCategory = this._getRiskLevelCategory(clampedScore);

    this.container.innerHTML = `
      <div class="risk-score-orb-wrapper">
        <div class="risk-score-orb-circle" data-risk-level="${riskCategory}">
          <div class="risk-score-orb-content">
            <div class="risk-score-orb-value" data-risk-level="${riskCategory}">${Math.round(clampedScore)}</div>
            <div class="risk-score-orb-level" data-risk-level="${riskCategory}">${this._formatRiskLevel(normalizedLevel)}</div>
            <div class="risk-score-orb-subtitle">Rủi Ro Tổng Thể Lô Hàng</div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Start the pulse animation
   * @private
   */
  _startPulseAnimation() {
    if (this.pulseInterval) {
      clearInterval(this.pulseInterval);
    }

    // Random interval between 4-6 seconds for organic feel
    const baseInterval = 4000;
    const randomOffset = Math.random() * 2000; // 0-2000ms
    const interval = baseInterval + randomOffset;

    this.pulseInterval = setInterval(() => {
      const orbEl = this.container?.querySelector('.risk-score-orb-circle');
      if (orbEl) {
        orbEl.classList.add('risk-score-orb-pulse');
        setTimeout(() => {
          orbEl.classList.remove('risk-score-orb-pulse');
        }, 1000); // Pulse duration
      }
    }, interval);
  }

  /**
   * Clamp score to valid range (0-100)
   * @private
   * @param {number} score - Input score
   * @returns {number} Clamped score
   */
  _clampScore(score) {
    if (score == null || score === undefined) return 0;
    const num = parseFloat(score);
    if (isNaN(num)) return 0;
    return Math.max(0, Math.min(100, num));
  }

  /**
   * Get risk level category from score (for UI formatting/coloring only)
   * ARCHITECTURE: ENGINE-FIRST
   * This is used ONLY for visual styling (color mapping), NOT for business logic
   * Backend MUST provide the authoritative riskLevel - this is just for CSS classes
   * @private
   * @param {number} score - Risk score (0-100)
   * @returns {string} Risk level category: 'low', 'medium', or 'high' (for CSS only)
   */
  _getRiskLevelCategory(score) {
    // UI-only visual threshold mapping for CSS classes
    // Backend's riskLevel should always be used for business decisions
    if (score < 40) return 'low';
    if (score <= 65) return 'medium';
    return 'high';
  }

  /**
   * Normalize risk level string to standard format
   * @private
   * @param {string} level - Risk level string
   * @returns {string} Normalized risk level: 'LOW', 'MEDIUM', or 'HIGH'
   */
  _normalizeRiskLevel(level) {
    if (!level) return 'LOW';
    const upper = String(level).toUpperCase();
    if (upper.includes('LOW')) return 'LOW';
    if (upper.includes('MEDIUM') || upper.includes('MODERATE')) return 'MEDIUM';
    if (upper.includes('HIGH')) return 'HIGH';
    return 'LOW';
  }

  /**
   * Format risk level for display
   * @private
   * @param {string} level - Risk level
   * @returns {string} Formatted risk level text
   */
  _formatRiskLevel(level) {
    const normalized = this._normalizeRiskLevel(level);
    return normalized;
  }


  /**
   * Inject component styles into the document head
   * @private
   */
  _injectStyles() {
    if (this._stylesInjected) {
      return;
    }

    if (document.getElementById('risk-score-orb-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'risk-score-orb-styles';
    style.textContent = `
      /* RiskScoreOrb Component Styles */
      .risk-score-orb-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 40px 20px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', system-ui, sans-serif;
      }

      .risk-score-orb-circle {
        position: relative;
        width: 280px;
        height: 280px;
        border-radius: 50%;
        background: rgba(15, 15, 20, 0.95);
        border: 2px solid rgba(255, 255, 255, 0.08);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 
          0 8px 32px rgba(0, 0, 0, 0.4),
          inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      }

      /* Subtle neon glow effects based on risk level */
      .risk-score-orb-circle[data-risk-level="low"] {
        box-shadow: 
          0 8px 32px rgba(0, 0, 0, 0.4),
          inset 0 1px 0 rgba(255, 255, 255, 0.05),
          0 0 40px rgba(0, 255, 136, 0.12),
          inset 0 0 60px rgba(0, 255, 136, 0.03);
      }

      .risk-score-orb-circle[data-risk-level="medium"] {
        box-shadow: 
          0 8px 32px rgba(0, 0, 0, 0.4),
          inset 0 1px 0 rgba(255, 255, 255, 0.05),
          0 0 40px rgba(255, 204, 0, 0.12),
          inset 0 0 60px rgba(255, 204, 0, 0.03);
      }

      .risk-score-orb-circle[data-risk-level="high"] {
        box-shadow: 
          0 8px 32px rgba(0, 0, 0, 0.4),
          inset 0 1px 0 rgba(255, 255, 255, 0.05),
          0 0 40px rgba(255, 68, 102, 0.12),
          inset 0 0 60px rgba(255, 68, 102, 0.03);
      }

      /* Pulse animation (slow, calm) */
      .risk-score-orb-pulse {
        animation: risk-score-orb-pulse 1s ease-in-out;
      }

      @keyframes risk-score-orb-pulse {
        0% {
          transform: scale(1);
          opacity: 1;
        }
        50% {
          transform: scale(1.02);
          opacity: 0.98;
        }
        100% {
          transform: scale(1);
          opacity: 1;
        }
      }

      .risk-score-orb-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        gap: 8px;
        z-index: 1;
      }

      .risk-score-orb-value {
        font-size: 96px;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -4px;
        transition: color 0.4s ease, text-shadow 0.4s ease;
        margin: 0;
        padding: 0;
      }

      /* Color rules: <40 green, 40-65 yellow, >65 red */
      .risk-score-orb-value[data-risk-level="low"] {
        color: #00ff88;
        text-shadow: 0 0 30px rgba(0, 255, 136, 0.25);
      }

      .risk-score-orb-value[data-risk-level="medium"] {
        color: #ffcc00;
        text-shadow: 0 0 30px rgba(255, 204, 0, 0.25);
      }

      .risk-score-orb-value[data-risk-level="high"] {
        color: #ff4466;
        text-shadow: 0 0 30px rgba(255, 68, 102, 0.25);
      }

      .risk-score-orb-level {
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: color 0.4s ease;
        margin-top: 4px;
      }

      .risk-score-orb-level[data-risk-level="low"] {
        color: #00ff88;
        opacity: 0.85;
      }

      .risk-score-orb-level[data-risk-level="medium"] {
        color: #ffcc00;
        opacity: 0.85;
      }

      .risk-score-orb-level[data-risk-level="high"] {
        color: #ff4466;
        opacity: 0.85;
      }

      .risk-score-orb-subtitle {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 8px;
      }

      /* Responsive adjustments */
      @media (max-width: 768px) {
        .risk-score-orb-wrapper {
          padding: 32px 16px;
        }

        .risk-score-orb-circle {
          width: 240px;
          height: 240px;
        }

        .risk-score-orb-value {
          font-size: 80px;
          letter-spacing: -3px;
        }

        .risk-score-orb-level {
          font-size: 12px;
          letter-spacing: 1.5px;
        }

        .risk-score-orb-subtitle {
          font-size: 10px;
          letter-spacing: 1.2px;
        }
      }

      @media (max-width: 480px) {
        .risk-score-orb-circle {
          width: 200px;
          height: 200px;
        }

        .risk-score-orb-value {
          font-size: 64px;
          letter-spacing: -2px;
        }

        .risk-score-orb-level {
          font-size: 11px;
          letter-spacing: 1px;
        }
      }

      /* Accessibility: Reduced motion preference */
      @media (prefers-reduced-motion: reduce) {
        .risk-score-orb-circle {
          transition: none;
        }

        .risk-score-orb-pulse {
          animation: none;
        }

        .risk-score-orb-value,
        .risk-score-orb-level {
          transition: none;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}

export default RiskScoreOrb;



