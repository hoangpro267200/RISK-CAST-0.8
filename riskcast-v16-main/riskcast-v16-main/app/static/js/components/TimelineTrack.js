/**
 * TimelineTrack Component
 * 
 * Renders sequential risk assessment points to visualize risk stability
 * and volatility across evaluation iterations.
 * 
 * NOTE:
 * TimelineTrack represents sequential risk assessment points,
 * not real historical or forecasted time-series data.
 * Labels (T-3 → T0) indicate evaluation iterations or simulation steps.
 * 
 * @class TimelineTrack
 * @exports TimelineTrack
 */
export class TimelineTrack {
  /**
   * Initialize the TimelineTrack component
   */
  constructor() {
    this.container = null;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Timeline data object
   * @param {Array<Object>} data.timeline - Timeline points array
   * @param {string} data.timeline[].label - Assessment point label (e.g., 'T-3', 'T-2', 'T-1', 'T0')
   * @param {number} data.timeline[].risk - Risk score (0-100)
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
   * @param {Object} data - Updated timeline data
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
      <div class="timeline-track-wrapper">
        <div class="timeline-track-content" id="timeline-track-content"></div>
      </div>
    `;
  }

  /**
   * Render timeline
   * @private
   * @param {Object} data - Timeline data
   */
  _render(data) {
    const timeline = Array.isArray(data.timeline) ? data.timeline : [];
    const contentEl = this.container.querySelector('#timeline-track-content');

    if (!contentEl) {
      return;
    }

    if (timeline.length === 0) {
      contentEl.innerHTML = `
        <div class="timeline-track-empty">
          <p class="timeline-track-empty-text">Không có dữ liệu đánh giá rủi ro theo thời gian</p>
        </div>
      `;
      return;
    }

    const normalized = this._normalizeTimeline(timeline);
    contentEl.innerHTML = this._renderTimeline(normalized);
    this._attachTooltips(contentEl, normalized);
  }

  /**
   * Normalize timeline data
   * @private
   * @param {Array<Object>} timeline - Raw timeline data
   * @returns {Array<Object>} Normalized timeline
   */
  _normalizeTimeline(timeline) {
    return timeline.map((point, index) => ({
      label: String(point.label || `T${index}`),
      risk: this._clampScore(point.risk),
      riskLevel: this._getRiskLevel(this._clampScore(point.risk))
    }));
  }

  /**
   * Render timeline SVG and points
   * @private
   * @param {Array<Object>} normalized - Normalized timeline data
   * @returns {string} HTML string
   */
  _renderTimeline(normalized) {
    const pointCount = normalized.length;
    if (pointCount === 0) return '';

    // Calculate positions (evenly spaced) - use absolute values for SVG path
    // viewBox is "0 0 100 100", so we use 0-100 range
    const points = normalized.map((point, index) => {
      const xPercent = (index / Math.max(pointCount - 1, 1)) * 100;
      const xAbsolute = xPercent; // For path: absolute value in viewBox coordinates
      return {
        ...point,
        xPercent, // For cx/cy/text (supports percentage)
        xAbsolute, // For path (must be absolute number)
        yPercent: 50, // Center vertically
        yAbsolute: 50 // For path: absolute value
      };
    });

    // Generate SVG path for connecting line (must use absolute numbers, not percentages)
    const pathData = points.map((p, i) => {
      return i === 0 ? `M ${p.xAbsolute} ${p.yAbsolute}` : `L ${p.xAbsolute} ${p.yAbsolute}`;
    }).join(' ');

    // Generate point circles (cx/cy/text can use percentage)
    const pointsHtml = points.map((point, index) => {
      const riskClass = `risk-${point.riskLevel}`;
      return `
        <g class="timeline-point-group" data-index="${index}">
          <circle
            class="timeline-point ${riskClass}"
            cx="${point.xPercent}%"
            cy="${point.yPercent}%"
            r="6"
          />
          <text
            class="timeline-label"
            x="${point.xPercent}%"
            y="${point.yPercent + 12}%"
            text-anchor="middle"
          >${this._escapeHtml(point.label)}</text>
          <text
            class="timeline-risk-value"
            x="${point.xPercent}%"
            y="${point.yPercent - 10}%"
            text-anchor="middle"
          >${point.risk}</text>
        </g>
      `;
    }).join('');

    return `
      <div class="timeline-track-svg-container">
        <svg class="timeline-track-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
          <path
            class="timeline-track-line"
            d="${pathData}"
            fill="none"
            stroke="rgba(255, 255, 255, 0.2)"
            stroke-width="2"
          />
          ${pointsHtml}
        </svg>
      </div>
      <div class="timeline-track-tooltip" id="timeline-track-tooltip"></div>
    `;
  }

  /**
   * Attach hover tooltips to points
   * @private
   * @param {HTMLElement} container - Container element
   * @param {Array<Object>} normalized - Normalized timeline data
   */
  _attachTooltips(container, normalized) {
    const tooltip = container.querySelector('#timeline-track-tooltip');
    if (!tooltip) return;

    const pointGroups = container.querySelectorAll('.timeline-point-group');
    
    pointGroups.forEach((group, index) => {
      const point = normalized[index];
      if (!point) return;

      group.addEventListener('mouseenter', (e) => {
        const rect = group.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        
        tooltip.style.display = 'block';
        tooltip.style.left = `${rect.left - containerRect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.top - containerRect.top - 40}px`;
        tooltip.innerHTML = `
          <div class="timeline-tooltip-content">
            <div class="timeline-tooltip-row">
              <span class="timeline-tooltip-label">Điểm Rủi Ro:</span>
              <span class="timeline-tooltip-value">${point.risk}</span>
            </div>
            <div class="timeline-tooltip-row">
              <span class="timeline-tooltip-label">Mốc Đánh Giá:</span>
              <span class="timeline-tooltip-value">${this._escapeHtml(point.label)}</span>
            </div>
          </div>
        `;
      });

      group.addEventListener('mouseleave', () => {
        tooltip.style.display = 'none';
      });
    });
  }

  /**
   * Get risk level from score
   * @private
   * @param {number} score - Risk score
   * @returns {string} Risk level: 'low', 'medium', or 'high'
   */
  _getRiskLevel(score) {
    const num = parseFloat(score);
    if (isNaN(num)) return 'low';
    const clamped = Math.max(0, Math.min(100, num));
    if (clamped >= 70) return 'high';
    if (clamped >= 40) return 'medium';
    return 'low';
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

    if (document.getElementById('timeline-track-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'timeline-track-styles';
    style.textContent = `
      /* TimelineTrack Component Styles */
      .timeline-track-wrapper {
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 32px;
      }

      .timeline-track-content {
        position: relative;
        min-height: 120px;
      }

      .timeline-track-svg-container {
        width: 100%;
        height: 120px;
        position: relative;
      }

      .timeline-track-svg {
        width: 100%;
        height: 100%;
      }

      .timeline-track-line {
        stroke: rgba(255, 255, 255, 0.2);
        stroke-width: 2;
        transition: stroke 0.2s ease;
      }

      .timeline-point-group {
        cursor: pointer;
        transition: transform 0.2s ease;
      }

      .timeline-point-group:hover {
        transform: scale(1.1);
      }

      .timeline-point {
        stroke-width: 2;
        transition: r 0.2s ease, stroke-width 0.2s ease, fill 0.2s ease, stroke 0.2s ease;
        /* Default color - will be overridden by risk-specific classes */
        fill: var(--risk-medium, #ffcc00);
        stroke: var(--risk-medium, #ffcc00);
      }

      .timeline-point-group:hover .timeline-point {
        r: 8;
        stroke-width: 3;
      }

      /* Risk-specific colors with higher specificity */
      .timeline-point-group .timeline-point.risk-low {
        fill: var(--risk-low, #00ff88) !important;
        stroke: var(--risk-low, #00ff88) !important;
      }

      .timeline-point-group .timeline-point.risk-medium {
        fill: var(--risk-medium, #ffcc00) !important;
        stroke: var(--risk-medium, #ffcc00) !important;
      }

      .timeline-point-group .timeline-point.risk-high {
        fill: var(--risk-high, #ff4466) !important;
        stroke: var(--risk-high, #ff4466) !important;
      }

      .timeline-label {
        font-size: 11px;
        fill: rgba(255, 255, 255, 0.6);
        font-weight: 600;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        text-anchor: middle;
        pointer-events: none;
      }

      .timeline-risk-value {
        font-size: 12px;
        fill: rgba(255, 255, 255, 0.9);
        font-weight: 700;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        text-anchor: middle;
        pointer-events: none;
      }

      .timeline-track-tooltip {
        position: absolute;
        display: none;
        background: rgba(15, 15, 20, 0.95);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 10px 14px;
        pointer-events: none;
        z-index: 1000;
        transform: translateX(-50%);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      }

      .timeline-tooltip-content {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .timeline-tooltip-row {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
      }

      .timeline-tooltip-label {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .timeline-tooltip-value {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 700;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .timeline-track-empty {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 120px;
        padding: 40px 20px;
      }

      .timeline-track-empty-text {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.4);
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        text-align: center;
      }

      @media (max-width: 768px) {
        .timeline-track-wrapper {
          padding: 24px 20px;
        }

        .timeline-track-svg-container {
          height: 100px;
        }

        .timeline-label {
          font-size: 10px;
        }

        .timeline-risk-value {
          font-size: 11px;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}
