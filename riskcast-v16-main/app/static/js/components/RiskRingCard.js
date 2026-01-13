/**
 * RiskRingCard Component
 * 
 * Displays individual risk drivers as compact orbit-style cards.
 * Designed to be positioned around the main RiskScoreOrb in a radial layout.
 * 
 * @class RiskRingCard
 */
class RiskRingCard {
  /**
   * Initialize the RiskRingCard component
   */
  constructor() {
    this.container = null;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Risk driver data
   * @param {string} data.riskName - Risk driver name
   * @param {number} data.riskValue - Risk value (0-100)
   * @param {string} [data.iconName] - Optional icon name
   */
  mount(el, data = {}) {
    if (!el) {
      console.warn('RiskRingCard: No element provided for mounting');
      return;
    }

    this.container = el;
    this._injectStyles();
    
    const riskName = data.riskName || data.name || 'Rủi Ro';
    const riskValue = this._clampValue(data.riskValue || data.value || 0);
    const iconName = data.iconName || data.icon || null;

    this._createStructure(riskName, riskValue, iconName);
  }

  /**
   * Update the component with new data
   * @param {Object} data - Updated risk driver data
   */
  update(data = {}) {
    if (!this.container) {
      console.warn('RiskRingCard: Component not mounted');
      return;
    }

    const riskName = data.riskName || data.name || 'Rủi Ro';
    const riskValue = this._clampValue(data.riskValue || data.value || 0);
    const iconName = data.iconName || data.icon || null;

    // Update value display
    const valueEl = this.container.querySelector('.risk-ring-card-value');
    if (valueEl) {
      valueEl.textContent = Math.round(riskValue);
      valueEl.setAttribute('data-risk-level', this._getRiskLevelCategory(riskValue));
    }

    // Update label
    const labelEl = this.container.querySelector('.risk-ring-card-label');
    if (labelEl) {
      labelEl.textContent = riskName;
    }

    // Update progress bar
    const progressEl = this.container.querySelector('.risk-ring-card-progress-fill');
    if (progressEl) {
      progressEl.style.width = `${riskValue}%`;
      progressEl.setAttribute('data-risk-level', this._getRiskLevelCategory(riskValue));
    }

    // Update card glow
    const cardEl = this.container.querySelector('.risk-ring-card');
    if (cardEl) {
      cardEl.setAttribute('data-risk-level', this._getRiskLevelCategory(riskValue));
    }

    // Update icon if provided
    const iconEl = this.container.querySelector('.risk-ring-card-icon');
    if (iconEl && iconName) {
      iconEl.innerHTML = this._getIconSVG(iconName);
    }
  }

  /**
   * Cleanup and destroy component
   */
  destroy() {
    this.container = null;
  }

  /**
   * Create the HTML structure for the card
   * @private
   * @param {string} riskName - Risk driver name
   * @param {number} riskValue - Risk value (0-100)
   * @param {string|null} iconName - Optional icon name
   */
  _createStructure(riskName, riskValue, iconName) {
    const riskCategory = this._getRiskLevelCategory(riskValue);
    const iconHTML = iconName ? this._getIconSVG(iconName) : '';

    this.container.innerHTML = `
      <div class="risk-ring-card" data-risk-level="${riskCategory}">
        ${iconName ? `<div class="risk-ring-card-icon">${iconHTML}</div>` : ''}
        <div class="risk-ring-card-content">
          <div class="risk-ring-card-value" data-risk-level="${riskCategory}">${Math.round(riskValue)}</div>
          <div class="risk-ring-card-progress">
            <div class="risk-ring-card-progress-track"></div>
            <div class="risk-ring-card-progress-fill" data-risk-level="${riskCategory}" style="width: ${riskValue}%"></div>
          </div>
          <div class="risk-ring-card-label">${this._escapeHtml(riskName)}</div>
        </div>
      </div>
    `;
  }

  /**
   * Get icon SVG based on icon name
   * @private
   * @param {string} iconName - Icon name
   * @returns {string} SVG HTML string
   */
  _getIconSVG(iconName) {
    const icons = {
      weather: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/><circle cx="12" cy="12" r="4"/></svg>',
      congestion: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6v6H9z"/></svg>',
      carrier: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 18H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h2"/><path d="M19 18h2a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-2"/><path d="M3 8h18"/><path d="M8 8v10"/><path d="M16 8v10"/></svg>',
      market: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
      insurance: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
      esg: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
      delay: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
      default: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>'
    };

    return icons[iconName.toLowerCase()] || icons.default;
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
   * Determine risk level category from value
   * @private
   * @param {number} value - Risk value (0-100)
   * @returns {string} Risk level category: 'low', 'medium', or 'high'
   */
  _getRiskLevelCategory(value) {
    if (value < 40) return 'low';
    if (value <= 65) return 'medium';
    return 'high';
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
   * Inject component styles into the document head
   * @private
   */
  _injectStyles() {
    if (this._stylesInjected) {
      return;
    }

    if (document.getElementById('risk-ring-card-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'risk-ring-card-styles';
    style.textContent = `
      /* RiskRingCard Component Styles */
      .risk-ring-card {
        position: relative;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 16px;
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        min-width: 160px;
        max-width: 200px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
          0 4px 16px rgba(0, 0, 0, 0.3),
          inset 0 1px 0 rgba(255, 255, 255, 0.05);
      }

      /* Subtle glow effects based on risk level */
      .risk-ring-card[data-risk-level="low"] {
        box-shadow: 
          0 4px 16px rgba(0, 0, 0, 0.3),
          inset 0 1px 0 rgba(255, 255, 255, 0.05),
          0 0 20px rgba(0, 255, 136, 0.08);
      }

      .risk-ring-card[data-risk-level="medium"] {
        box-shadow: 
          0 4px 16px rgba(0, 0, 0, 0.3),
          inset 0 1px 0 rgba(255, 255, 255, 0.05),
          0 0 20px rgba(255, 204, 0, 0.08);
      }

      .risk-ring-card[data-risk-level="high"] {
        box-shadow: 
          0 4px 16px rgba(0, 0, 0, 0.3),
          inset 0 1px 0 rgba(255, 255, 255, 0.05),
          0 0 20px rgba(255, 68, 102, 0.08);
      }

      .risk-ring-card-icon {
        flex-shrink: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.4;
        margin-top: 2px;
      }

      .risk-ring-card-icon svg {
        width: 100%;
        height: 100%;
        stroke: currentColor;
        color: rgba(255, 255, 255, 0.5);
      }

      .risk-ring-card-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 8px;
        min-width: 0;
      }

      .risk-ring-card-value {
        font-size: 32px;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -1px;
        transition: color 0.3s ease, text-shadow 0.3s ease;
        margin: 0;
        padding: 0;
      }

      /* Color rules: <40 green, 40-65 yellow, >65 red */
      .risk-ring-card-value[data-risk-level="low"] {
        color: #00ff88;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
      }

      .risk-ring-card-value[data-risk-level="medium"] {
        color: #ffcc00;
        text-shadow: 0 0 20px rgba(255, 204, 0, 0.2);
      }

      .risk-ring-card-value[data-risk-level="high"] {
        color: #ff4466;
        text-shadow: 0 0 20px rgba(255, 68, 102, 0.2);
      }

      .risk-ring-card-progress {
        position: relative;
        width: 100%;
        height: 4px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 2px;
        overflow: hidden;
      }

      .risk-ring-card-progress-track {
        position: absolute;
        inset: 0;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 2px;
      }

      .risk-ring-card-progress-fill {
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        border-radius: 2px;
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s ease;
      }

      .risk-ring-card-progress-fill[data-risk-level="low"] {
        background: linear-gradient(90deg, #00ff88, rgba(0, 255, 136, 0.6));
        box-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
      }

      .risk-ring-card-progress-fill[data-risk-level="medium"] {
        background: linear-gradient(90deg, #ffcc00, rgba(255, 204, 0, 0.6));
        box-shadow: 0 0 8px rgba(255, 204, 0, 0.3);
      }

      .risk-ring-card-progress-fill[data-risk-level="high"] {
        background: linear-gradient(90deg, #ff4466, rgba(255, 68, 102, 0.6));
        box-shadow: 0 0 8px rgba(255, 68, 102, 0.3);
      }

      .risk-ring-card-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: rgba(255, 255, 255, 0.5);
        margin: 0;
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      /* Responsive adjustments */
      @media (max-width: 768px) {
        .risk-ring-card {
          padding: 14px;
          min-width: 140px;
          max-width: 180px;
          gap: 10px;
        }

        .risk-ring-card-value {
          font-size: 28px;
          letter-spacing: -0.8px;
        }

        .risk-ring-card-label {
          font-size: 10px;
          letter-spacing: 0.6px;
        }

        .risk-ring-card-icon {
          width: 18px;
          height: 18px;
        }
      }

      @media (max-width: 480px) {
        .risk-ring-card {
          padding: 12px;
          min-width: 120px;
          max-width: 160px;
        }

        .risk-ring-card-value {
          font-size: 24px;
        }

        .risk-ring-card-label {
          font-size: 9px;
        }
      }

      /* Accessibility: Reduced motion preference */
      @media (prefers-reduced-motion: reduce) {
        .risk-ring-card {
          transition: none;
        }

        .risk-ring-card-progress-fill {
          transition: none;
        }

        .risk-ring-card-value {
          transition: none;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}

export default RiskRingCard;





