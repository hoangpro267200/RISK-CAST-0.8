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
 * InsuranceDecisionPanel Component
 * 
 * Operational Recommendations / Insurance & Timing Hub
 * Displays insurance recommendations, safe shipping windows, provider fit, and traceability.
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - Receives complete recommendations object from backend (MANDATORY)
 * - All recommendations (insurance, timing, providers, trace) MUST come from backend
 * - Only formats/clamps values for display
 * 
 * @class InsuranceDecisionPanel
 * @exports InsuranceDecisionPanel
 */
export class InsuranceDecisionPanel {
  /**
   * Initialize the InsuranceDecisionPanel component
   */
  constructor() {
    this.container = null;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Recommendations data object
   * @param {Object} data.insurance - Insurance recommendation
   * @param {Object} data.timing - Shipping window recommendation
   * @param {Array} data.providers - Provider fit list
   * @param {Object} data.trace - Decision traceability
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
   * Update the panel with new data
   * @param {Object} data - Updated recommendations data
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
   * Create panel structure
   * @private
   */
  _createStructure() {
    const uniqueId = `insurance-decision-${Date.now()}`;
    this.container.innerHTML = `
      <div class="insurance-decision-wrapper">
        <div class="insurance-decision-header">
          <h2 class="insurance-decision-title">Khuyến Nghị Điều Hành</h2>
          <p class="insurance-decision-subtitle">Bảo Hiểm & Thời Gian Vận Chuyển</p>
        </div>
        
        <div class="insurance-decision-content">
          <!-- Insurance Decision Section -->
          <div class="insurance-decision-section" id="insurance-section"></div>
          
          <!-- Safe Shipping Window Section -->
          <div class="insurance-decision-section" id="timing-section"></div>
          
          <!-- Provider Fit Section -->
          <div class="insurance-decision-section" id="providers-section"></div>
          
          <!-- Traceability Section (Collapsible) -->
          <details class="insurance-decision-traceability" id="${uniqueId}">
            <summary class="insurance-decision-traceability-summary">
              <span class="insurance-decision-traceability-text">Truy Vết Quyết Định</span>
              <span class="insurance-decision-traceability-icon">▼</span>
            </summary>
            <div class="insurance-decision-traceability-content" id="traceability-content"></div>
          </details>
        </div>
      </div>
    `;

    // Add toggle icon animation
    const detailsEl = this.container.querySelector(`#${uniqueId}`);
    if (detailsEl) {
      detailsEl.addEventListener('toggle', function() {
        const icon = this.querySelector('.insurance-decision-traceability-icon');
        if (icon) {
          icon.textContent = this.open ? '▲' : '▼';
        }
      });
    }
  }

  /**
   * Render all sections
   * @private
   * @param {Object} data - Recommendations data
   */
  _render(data) {
    const insurance = data.insurance || {};
    const timing = data.timing || {};
    const providers = Array.isArray(data.providers) ? data.providers : [];
    const trace = data.trace || {};

    // Render insurance section
    const insuranceEl = this.container.querySelector('#insurance-section');
    if (insuranceEl) {
      insuranceEl.innerHTML = this._renderInsurance(insurance);
    }

    // Render timing section
    const timingEl = this.container.querySelector('#timing-section');
    if (timingEl) {
      timingEl.innerHTML = this._renderTiming(timing);
    }

    // Render providers section
    const providersEl = this.container.querySelector('#providers-section');
    if (providersEl) {
      providersEl.innerHTML = this._renderProviders(providers);
    }

    // Render traceability section
    const traceabilityEl = this.container.querySelector('#traceability-content');
    if (traceabilityEl) {
      traceabilityEl.innerHTML = this._renderTraceability(trace);
    }
  }

  /**
   * Render insurance recommendation section
   * @private
   * @param {Object} insurance - Insurance recommendation
   * @returns {string} HTML string
   */
  _renderInsurance(insurance) {
    if (!insurance || Object.keys(insurance).length === 0) {
      return `
        <div class="insurance-decision-empty">
          <p>Dữ liệu khuyến nghị bảo hiểm không có sẵn.</p>
        </div>
      `;
    }

    const required = insurance.required !== undefined ? insurance.required : false;
    const level = insurance.level || 'LOW';
    const packageType = insurance.package || 'Không xác định';
    const confidence = insurance.confidence != null ? insurance.confidence : 0;
    const reasons = Array.isArray(insurance.reasons) ? insurance.reasons : [];
    const checklist = Array.isArray(insurance.coverageChecklist) ? insurance.coverageChecklist : [];
    const disclaimers = Array.isArray(insurance.disclaimers) ? insurance.disclaimers : [];

    // Badge text and color
    let badgeText = 'SKIP';
    let badgeClass = 'insurance-badge-skip';
    if (required) {
      if (level === 'HIGH') {
        badgeText = 'BUY';
        badgeClass = 'insurance-badge-buy';
      } else {
        badgeText = 'OPTIONAL';
        badgeClass = 'insurance-badge-optional';
      }
    }

    return `
      <div class="insurance-decision-insurance">
        <h3 class="insurance-decision-section-title">Quyết Định Bảo Hiểm</h3>
        
        <div class="insurance-decision-badge-container">
          <span class="insurance-decision-badge ${badgeClass}">${badgeText}</span>
          <span class="insurance-decision-confidence">Độ tin cậy: ${confidence}%</span>
        </div>
        
        <div class="insurance-decision-package">
          <h4 class="insurance-decision-package-title">Gói Bảo Hiểm Đề Xuất</h4>
          <p class="insurance-decision-package-name">${this._escapeHtml(packageType)}</p>
        </div>
        
        ${checklist.length > 0 ? `
        <div class="insurance-decision-checklist">
          <h4 class="insurance-decision-checklist-title">Danh Sách Kiểm Tra Bảo Hiểm</h4>
          <ul class="insurance-decision-checklist-list">
            ${checklist.map(item => `<li>${this._escapeHtml(item)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
        
        ${reasons.length > 0 ? `
        <div class="insurance-decision-reasons">
          <h4 class="insurance-decision-reasons-title">Lý Do</h4>
          <ul class="insurance-decision-reasons-list">
            ${reasons.map(reason => `<li>${this._escapeHtml(reason)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
        
        ${disclaimers.length > 0 ? `
        <div class="insurance-decision-disclaimers">
          ${disclaimers.map(disclaimer => `<p class="insurance-decision-disclaimer">${this._escapeHtml(disclaimer)}</p>`).join('')}
        </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * Render safe shipping window section
   * @private
   * @param {Object} timing - Timing recommendation
   * @returns {string} HTML string
   */
  _renderTiming(timing) {
    if (!timing || Object.keys(timing).length === 0) {
      return `
        <div class="insurance-decision-empty">
          <p>Dữ liệu cửa sổ vận chuyển an toàn không có sẵn.</p>
        </div>
      `;
    }

    const recommendedWindow = timing.recommendedWindow || 'Không xác định';
    const avoidWindow = timing.avoidWindow || 'Không có';
    const riskReduction = timing.riskReduction != null ? timing.riskReduction : 0;
    const rationale = Array.isArray(timing.rationale) ? timing.rationale : [];
    const assumptions = Array.isArray(timing.assumptions) ? timing.assumptions : [];

    return `
      <div class="insurance-decision-timing">
        <h3 class="insurance-decision-section-title">Cửa Sổ Vận Chuyển An Toàn</h3>
        
        <div class="insurance-decision-windows">
          <div class="insurance-decision-window recommended">
            <div class="insurance-decision-window-label">Khuyến Nghị</div>
            <div class="insurance-decision-window-value">${this._escapeHtml(recommendedWindow)}</div>
          </div>
          
          <div class="insurance-decision-window avoid">
            <div class="insurance-decision-window-label">Nên Tránh</div>
            <div class="insurance-decision-window-value">${this._escapeHtml(avoidWindow)}</div>
          </div>
        </div>
        
        <div class="insurance-decision-reduction">
          <div class="insurance-decision-reduction-label">Giảm Rủi Ro</div>
          <div class="insurance-decision-reduction-value">${riskReduction.toFixed(1)}%</div>
        </div>
        
        ${rationale.length > 0 ? `
        <div class="insurance-decision-rationale">
          <h4 class="insurance-decision-rationale-title">Lý Do</h4>
          <ul class="insurance-decision-rationale-list">
            ${rationale.map(item => `<li>${this._escapeHtml(item)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
        
        ${assumptions.length > 0 ? `
        <div class="insurance-decision-assumptions">
          <h4 class="insurance-decision-assumptions-title">Giả Định</h4>
          <ul class="insurance-decision-assumptions-list">
            ${assumptions.map(item => `<li>${this._escapeHtml(item)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * Render provider fit section
   * @private
   * @param {Array} providers - Provider fit list
   * @returns {string} HTML string
   */
  _renderProviders(providers) {
    if (!Array.isArray(providers) || providers.length === 0) {
      return `
        <div class="insurance-decision-empty">
          <p>Dữ liệu xếp hạng nhà cung cấp không có sẵn.</p>
        </div>
      `;
    }

    // Show top 2-3 providers
    const topProviders = providers.slice(0, 3);

    return `
      <div class="insurance-decision-providers">
        <h3 class="insurance-decision-section-title">Xếp Hạng Phù Hợp Nhà Cung Cấp</h3>
        
        <div class="insurance-decision-providers-list">
          ${topProviders.map((provider, index) => this._renderProvider(provider, index)).join('')}
        </div>
      </div>
    `;
  }

  /**
   * Render single provider card
   * @private
   * @param {Object} provider - Provider data
   * @param {number} index - Provider index
   * @returns {string} HTML string
   */
  _renderProvider(provider, index) {
    const name = provider.name || `Nhà Cung Cấp ${index + 1}`;
    const fit = provider.fit != null ? provider.fit : 0;
    const strengths = Array.isArray(provider.strengths) ? provider.strengths : [];
    const tradeoffs = Array.isArray(provider.tradeoffs) ? provider.tradeoffs : [];
    const suggestedClauses = Array.isArray(provider.suggestedClauses) ? provider.suggestedClauses : [];

    // Fit bar color
    let fitBarClass = 'insurance-provider-fit-low';
    if (fit >= 80) {
      fitBarClass = 'insurance-provider-fit-high';
    } else if (fit >= 60) {
      fitBarClass = 'insurance-provider-fit-medium';
    }

    return `
      <div class="insurance-decision-provider">
        <div class="insurance-decision-provider-header">
          <h4 class="insurance-decision-provider-name">${this._escapeHtml(name)}</h4>
          <div class="insurance-decision-provider-fit">
            <span class="insurance-decision-provider-fit-label">Độ Phù Hợp</span>
            <span class="insurance-decision-provider-fit-value">${fit}%</span>
          </div>
        </div>
        
        <div class="insurance-decision-provider-fit-bar">
          <div class="insurance-decision-provider-fit-bar-fill ${fitBarClass}" style="width: ${fit}%"></div>
        </div>
        
        ${strengths.length > 0 ? `
        <div class="insurance-decision-provider-strengths">
          <div class="insurance-decision-provider-strengths-label">Điểm Mạnh</div>
          <ul class="insurance-decision-provider-strengths-list">
            ${strengths.map(strength => `<li>${this._escapeHtml(strength)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
        
        ${tradeoffs.length > 0 ? `
        <div class="insurance-decision-provider-tradeoffs">
          <div class="insurance-decision-provider-tradeoffs-label">Đánh Đổi</div>
          <ul class="insurance-decision-provider-tradeoffs-list">
            ${tradeoffs.map(tradeoff => `<li>${this._escapeHtml(tradeoff)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
        
        ${suggestedClauses.length > 0 ? `
        <div class="insurance-decision-provider-clauses">
          <div class="insurance-decision-provider-clauses-label">Điều Khoản Đề Xuất</div>
          <ul class="insurance-decision-provider-clauses-list">
            ${suggestedClauses.map(clause => `<li>${this._escapeHtml(clause)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * Render traceability section
   * @private
   * @param {Object} trace - Trace data
   * @returns {string} HTML string
   */
  _renderTraceability(trace) {
    if (!trace || Object.keys(trace).length === 0) {
      return `
        <div class="insurance-decision-empty">
          <p>Dữ liệu truy vết quyết định không có sẵn.</p>
        </div>
      `;
    }

    const triggers = Array.isArray(trace.triggers) ? trace.triggers : [];
    const dominantSignals = Array.isArray(trace.dominantSignals) ? trace.dominantSignals : [];
    const version = trace.version || 'unknown';

    return `
      <div class="insurance-decision-traceability-details">
        <div class="insurance-decision-traceability-meta">
          <span class="insurance-decision-traceability-version">Phiên bản: ${this._escapeHtml(version)}</span>
        </div>
        
        ${dominantSignals.length > 0 ? `
        <div class="insurance-decision-traceability-dominant">
          <h4 class="insurance-decision-traceability-dominant-title">Tín Hiệu Chủ Đạo</h4>
          <div class="insurance-decision-traceability-dominant-list">
            ${dominantSignals.map(signal => `<span class="insurance-decision-traceability-dominant-tag">${this._escapeHtml(signal)}</span>`).join('')}
          </div>
        </div>
        ` : ''}
        
        ${triggers.length > 0 ? `
        <div class="insurance-decision-traceability-triggers">
          <h4 class="insurance-decision-traceability-triggers-title">Các Kích Hoạt</h4>
          <div class="insurance-decision-traceability-triggers-list">
            ${triggers.map(trigger => `
              <div class="insurance-decision-traceability-trigger">
                <div class="insurance-decision-traceability-trigger-header">
                  <span class="insurance-decision-traceability-trigger-signal">${this._escapeHtml(trigger.signal || 'Unknown')}</span>
                  <span class="insurance-decision-traceability-trigger-impact insurance-decision-traceability-trigger-impact-${(trigger.impact || 'LOW').toLowerCase()}">${this._escapeHtml(trigger.impact || 'LOW')}</span>
                </div>
                <div class="insurance-decision-traceability-trigger-details">
                  <span class="insurance-decision-traceability-trigger-value">Giá trị: ${this._escapeHtml(trigger.value || 'N/A')}</span>
                  <span class="insurance-decision-traceability-trigger-threshold">Ngưỡng: ${this._escapeHtml(trigger.threshold || 'N/A')}</span>
                </div>
                <div class="insurance-decision-traceability-trigger-note">${this._escapeHtml(trigger.note || '')}</div>
              </div>
            `).join('')}
          </div>
        </div>
        ` : ''}
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

    if (document.getElementById('insurance-decision-panel-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'insurance-decision-panel-styles';
    style.textContent = `
      /* InsuranceDecisionPanel Component Styles */
      .insurance-decision-wrapper {
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        padding: 32px;
      }

      .insurance-decision-header {
        margin-bottom: 32px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding-bottom: 24px;
      }

      .insurance-decision-title {
        font-size: 24px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin: 0 0 8px 0;
        letter-spacing: -0.3px;
      }

      .insurance-decision-subtitle {
        font-size: 15px;
        color: rgba(255, 255, 255, 0.6);
        margin: 0;
      }

      .insurance-decision-content {
        display: flex;
        flex-direction: column;
        gap: 32px;
      }

      .insurance-decision-section {
        padding-bottom: 32px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      }

      .insurance-decision-section:last-of-type {
        border-bottom: none;
        padding-bottom: 0;
      }

      .insurance-decision-section-title {
        font-size: 18px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin: 0 0 20px 0;
        letter-spacing: -0.2px;
      }

      .insurance-decision-empty {
        padding: 24px;
        text-align: center;
        color: rgba(255, 255, 255, 0.5);
        font-size: 14px;
      }

      /* Insurance Section */
      .insurance-decision-badge-container {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 24px;
      }

      .insurance-decision-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
      }

      .insurance-badge-buy {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.3);
      }

      .insurance-badge-optional {
        background: rgba(251, 191, 36, 0.2);
        color: #fcd34d;
        border: 1px solid rgba(251, 191, 36, 0.3);
      }

      .insurance-badge-skip {
        background: rgba(107, 114, 128, 0.2);
        color: #9ca3af;
        border: 1px solid rgba(107, 114, 128, 0.3);
      }

      .insurance-decision-confidence {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.6);
      }

      .insurance-decision-package {
        margin-bottom: 24px;
      }

      .insurance-decision-package-title {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        margin: 0 0 8px 0;
      }

      .insurance-decision-package-name {
        font-size: 16px;
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
        font-weight: 500;
      }

      .insurance-decision-checklist,
      .insurance-decision-reasons {
        margin-bottom: 20px;
      }

      .insurance-decision-checklist-title,
      .insurance-decision-reasons-title {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        margin: 0 0 12px 0;
      }

      .insurance-decision-checklist-list,
      .insurance-decision-reasons-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }

      .insurance-decision-checklist-list li,
      .insurance-decision-reasons-list li {
        font-size: 14px;
        line-height: 1.6;
        color: rgba(255, 255, 255, 0.75);
        margin-bottom: 8px;
        padding-left: 20px;
        position: relative;
      }

      .insurance-decision-checklist-list li::before {
        content: '✓';
        position: absolute;
        left: 0;
        color: rgba(34, 197, 94, 0.8);
      }

      .insurance-decision-reasons-list li::before {
        content: '•';
        position: absolute;
        left: 0;
        color: rgba(255, 255, 255, 0.4);
      }

      .insurance-decision-disclaimers {
        margin-top: 24px;
        padding-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
      }

      .insurance-decision-disclaimer {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        margin: 0 0 8px 0;
        line-height: 1.5;
      }

      /* Timing Section */
      .insurance-decision-windows {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 24px;
      }

      .insurance-decision-window {
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
      }

      .insurance-decision-window.recommended {
        background: rgba(34, 197, 94, 0.1);
        border-color: rgba(34, 197, 94, 0.2);
      }

      .insurance-decision-window.avoid {
        background: rgba(239, 68, 68, 0.1);
        border-color: rgba(239, 68, 68, 0.2);
      }

      .insurance-decision-window-label {
        font-size: 12px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.6);
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .insurance-decision-window-value {
        font-size: 16px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
      }

      .insurance-decision-reduction {
        text-align: center;
        padding: 20px;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        margin-bottom: 24px;
      }

      .insurance-decision-reduction-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
        margin-bottom: 8px;
      }

      .insurance-decision-reduction-value {
        font-size: 32px;
        font-weight: 700;
        color: #60a5fa;
      }

      .insurance-decision-rationale,
      .insurance-decision-assumptions {
        margin-bottom: 20px;
      }

      .insurance-decision-rationale-title,
      .insurance-decision-assumptions-title {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        margin: 0 0 12px 0;
      }

      .insurance-decision-rationale-list,
      .insurance-decision-assumptions-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }

      .insurance-decision-rationale-list li,
      .insurance-decision-assumptions-list li {
        font-size: 14px;
        line-height: 1.6;
        color: rgba(255, 255, 255, 0.75);
        margin-bottom: 8px;
        padding-left: 20px;
        position: relative;
      }

      .insurance-decision-rationale-list li::before {
        content: '•';
        position: absolute;
        left: 0;
        color: rgba(255, 255, 255, 0.4);
      }

      .insurance-decision-assumptions-list li::before {
        content: 'ℹ';
        position: absolute;
        left: 0;
        color: rgba(59, 130, 246, 0.6);
      }

      /* Providers Section */
      .insurance-decision-providers-list {
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      .insurance-decision-provider {
        padding: 20px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
      }

      .insurance-decision-provider-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }

      .insurance-decision-provider-name {
        font-size: 16px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
      }

      .insurance-decision-provider-fit {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .insurance-decision-provider-fit-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
      }

      .insurance-decision-provider-fit-value {
        font-size: 18px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.9);
      }

      .insurance-decision-provider-fit-bar {
        height: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 20px;
      }

      .insurance-decision-provider-fit-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
      }

      .insurance-provider-fit-high {
        background: linear-gradient(90deg, #22c55e, #16a34a);
      }

      .insurance-provider-fit-medium {
        background: linear-gradient(90deg, #fbbf24, #f59e0b);
      }

      .insurance-provider-fit-low {
        background: linear-gradient(90deg, #ef4444, #dc2626);
      }

      .insurance-decision-provider-strengths,
      .insurance-decision-provider-tradeoffs,
      .insurance-decision-provider-clauses {
        margin-bottom: 16px;
      }

      .insurance-decision-provider-strengths:last-child,
      .insurance-decision-provider-tradeoffs:last-child,
      .insurance-decision-provider-clauses:last-child {
        margin-bottom: 0;
      }

      .insurance-decision-provider-strengths-label,
      .insurance-decision-provider-tradeoffs-label,
      .insurance-decision-provider-clauses-label {
        font-size: 13px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 8px;
      }

      .insurance-decision-provider-strengths-list,
      .insurance-decision-provider-tradeoffs-list,
      .insurance-decision-provider-clauses-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }

      .insurance-decision-provider-strengths-list li,
      .insurance-decision-provider-tradeoffs-list li,
      .insurance-decision-provider-clauses-list li {
        font-size: 13px;
        line-height: 1.5;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 6px;
        padding-left: 18px;
        position: relative;
      }

      .insurance-decision-provider-strengths-list li::before {
        content: '+';
        position: absolute;
        left: 0;
        color: rgba(34, 197, 94, 0.8);
        font-weight: 700;
      }

      .insurance-decision-provider-tradeoffs-list li::before {
        content: '−';
        position: absolute;
        left: 0;
        color: rgba(239, 68, 68, 0.8);
        font-weight: 700;
      }

      .insurance-decision-provider-clauses-list li::before {
        content: '◉';
        position: absolute;
        left: 0;
        color: rgba(59, 130, 246, 0.8);
        font-size: 10px;
      }

      /* Traceability Section */
      .insurance-decision-traceability {
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        margin-top: 32px;
        padding-top: 24px;
      }

      .insurance-decision-traceability-summary {
        padding: 16px;
        cursor: pointer;
        list-style: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
        user-select: none;
        transition: background-color 0.2s ease;
        border-radius: 8px;
      }

      .insurance-decision-traceability-summary::-webkit-details-marker {
        display: none;
      }

      .insurance-decision-traceability-summary:hover {
        background-color: rgba(255, 255, 255, 0.03);
      }

      .insurance-decision-traceability-text {
        font-size: 15px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8);
      }

      .insurance-decision-traceability-icon {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
      }

      .insurance-decision-traceability-content {
        padding: 24px 0 0 0;
      }

      .insurance-decision-traceability-meta {
        margin-bottom: 20px;
      }

      .insurance-decision-traceability-version {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
      }

      .insurance-decision-traceability-dominant {
        margin-bottom: 24px;
      }

      .insurance-decision-traceability-dominant-title {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8);
        margin: 0 0 12px 0;
      }

      .insurance-decision-traceability-dominant-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .insurance-decision-traceability-dominant-tag {
        display: inline-block;
        padding: 6px 12px;
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 6px;
        font-size: 12px;
        color: #93c5fd;
        font-weight: 500;
      }

      .insurance-decision-traceability-triggers {
        margin-top: 24px;
      }

      .insurance-decision-traceability-triggers-title {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8);
        margin: 0 0 16px 0;
      }

      .insurance-decision-traceability-triggers-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .insurance-decision-traceability-trigger {
        padding: 16px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
      }

      .insurance-decision-traceability-trigger-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }

      .insurance-decision-traceability-trigger-signal {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
      }

      .insurance-decision-traceability-trigger-impact {
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .insurance-decision-traceability-trigger-impact-high {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
      }

      .insurance-decision-traceability-trigger-impact-medium {
        background: rgba(251, 191, 36, 0.2);
        color: #fcd34d;
      }

      .insurance-decision-traceability-trigger-impact-low {
        background: rgba(107, 114, 128, 0.2);
        color: #9ca3af;
      }

      .insurance-decision-traceability-trigger-details {
        display: flex;
        gap: 16px;
        margin-bottom: 8px;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
      }

      .insurance-decision-traceability-trigger-note {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.7);
        line-height: 1.5;
      }

      @media (max-width: 768px) {
        .insurance-decision-wrapper {
          padding: 24px 20px;
        }

        .insurance-decision-title {
          font-size: 20px;
        }

        .insurance-decision-windows {
          grid-template-columns: 1fr;
        }

        .insurance-decision-provider-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 8px;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}
