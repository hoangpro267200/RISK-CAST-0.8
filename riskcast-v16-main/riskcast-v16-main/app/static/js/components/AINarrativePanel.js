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
 * AINarrativePanel Component
 * 
 * Executive narrative panel that displays risk intelligence explanations
 * from backend in clear, defensible language for enterprise and academic review.
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - Receives narrative data from backend (MANDATORY)
 * - All explanations, factors, composite scores MUST come from backend
 * - Only formats/clamps values for display
 * 
 * @class AINarrativePanel
 * @exports AINarrativePanel
 */
export class AINarrativePanel {
  /**
   * Initialize the AINarrativePanel component
   */
  constructor() {
    this.container = null;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} data - Narrative data object
   * @param {Object} data.summary - Overall risk summary
   * @param {number} data.summary.overallRiskScore - Overall risk score (0-100)
   * @param {string} data.summary.riskLevel - Risk level: 'low', 'medium', or 'high'
   * @param {Array<Object>} data.layers - Risk layers array
   * @param {string} data.layers[].name - Layer name
   * @param {number} data.layers[].score - Layer score (0-100)
   * @param {string} data.layers[].note - Layer note
   * @param {Array<Object>} data.factors - Risk factors array
   * @param {string} data.factors[].factor - Factor name
   * @param {number} data.factors[].impact - Impact value (0-1)
   * @param {number} data.factors[].probability - Probability value (0-1)
   * @param {number} [data.factors[].compositeScore] - Optional composite score (0-1)
   * @param {Object} data.loss - Loss metrics
   * @param {number} data.loss.p95 - P95 loss value
   * @param {number} data.loss.p99 - P99 loss value
   * @param {number} data.loss.tailContribution - Tail risk contribution (%)
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
   * @param {Object} data - Updated narrative data
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
   * Create panel structure with collapsible sections
   * @private
   */
  _createStructure() {
    const uniqueId = `ai-narrative-${Date.now()}`;
    this.container.innerHTML = `
      <div class="ai-narrative-wrapper">
        <div class="ai-narrative-executive" id="ai-narrative-executive"></div>
        <details class="ai-narrative-details" id="${uniqueId}">
          <summary class="ai-narrative-summary">
            <span class="ai-narrative-summary-text">Xem phân tích chi tiết</span>
            <span class="ai-narrative-summary-icon">▼</span>
          </summary>
          <div class="ai-narrative-sections">
            <div class="ai-narrative-section" id="ai-narrative-overall"></div>
            <div class="ai-narrative-section" id="ai-narrative-layers"></div>
            <div class="ai-narrative-section" id="ai-narrative-factors"></div>
            <div class="ai-narrative-section" id="ai-narrative-loss"></div>
          </div>
        </details>
      </div>
    `;

    // Add toggle icon animation
    const detailsEl = this.container.querySelector(`#${uniqueId}`);
    if (detailsEl) {
      detailsEl.addEventListener('toggle', function() {
        const icon = this.querySelector('.ai-narrative-summary-icon');
        if (icon) {
          icon.textContent = this.open ? '▲' : '▼';
        }
      });
    }
  }

  /**
   * Render all narrative sections
   * @private
   * @param {Object} data - Narrative data
   */
  _render(data) {
    const summary = data.summary || {};
    const layers = Array.isArray(data.layers) ? data.layers : [];
    const factors = Array.isArray(data.factors) ? data.factors : [];
    const loss = data.loss || {};

    // Render executive summary (always visible)
    const executiveEl = this.container.querySelector('#ai-narrative-executive');
    if (executiveEl) {
      executiveEl.innerHTML = this._renderExecutiveSummary(summary, layers, factors, loss);
    }

    // Render detailed sections (collapsible)
    const overallEl = this.container.querySelector('#ai-narrative-overall');
    const layersEl = this.container.querySelector('#ai-narrative-layers');
    const factorsEl = this.container.querySelector('#ai-narrative-factors');
    const lossEl = this.container.querySelector('#ai-narrative-loss');

    if (overallEl) {
      overallEl.innerHTML = this._renderOverallRisk(summary);
    }
    if (layersEl) {
      layersEl.innerHTML = this._renderDominantLayers(layers);
    }
    if (factorsEl) {
      factorsEl.innerHTML = this._renderKeyDrivers(factors);
    }
    if (lossEl) {
      lossEl.innerHTML = this._renderLossInsight(loss);
    }
  }

  /**
   * Render executive summary (3-5 lines, always visible)
   * @private
   * @param {Object} summary - Summary data
   * @param {Array<Object>} layers - Layers data
   * @param {Array<Object>} factors - Factors data
   * @param {Object} loss - Loss data
   * @returns {string} HTML string
   */
  _renderExecutiveSummary(summary, layers, factors, loss) {
    const score = this._clampScore(summary.overallRiskScore);
    const riskLevel = summary.riskLevel || 'low';
    const levelText = this._getRiskLevelText(riskLevel);

    // Get top layer
    const sortedLayers = [...(layers || [])].sort((a, b) => {
      const scoreA = parseFloat(a.score) || 0;
      const scoreB = parseFloat(b.score) || 0;
      return scoreB - scoreA;
    });
    const topLayer = sortedLayers[0];
    const topLayerName = topLayer ? this._escapeHtml(topLayer.name || 'Không xác định') : 'nhiều yếu tố rủi ro';
    const topLayerScore = topLayer ? this._clampScore(topLayer.score) : null;

    // Get tail risk info
    const tailContribution = loss.tailContribution;
    const tailText = tailContribution != null && Number.isFinite(tailContribution) 
      ? ` Tail risk accounts for ${Math.max(0, Math.min(100, tailContribution)).toFixed(1)}% of exposure.`
      : '';

    let summaryText = `Điểm rủi ro tổng thể: ${score} (${levelText}).`;
    if (topLayer && topLayerScore !== null) {
      summaryText += ` Yếu tố chính: ${topLayerName} (${topLayerScore}).`;
    }
    if (tailText) {
      summaryText += tailText.replace('Tail risk accounts for', 'Rủi ro đuôi chiếm').replace('% of exposure.', '% tổng rủi ro.');
    }

    return `
      <div class="ai-narrative-executive-content">
        <h3 class="ai-narrative-executive-title">Tóm Tắt Điều Hành</h3>
        <p class="ai-narrative-executive-text">${summaryText}</p>
      </div>
    `;
  }

  /**
   * Render overall risk assessment section
   * @private
   * @param {Object} summary - Summary data
   * @returns {string} HTML string
   */
  _renderOverallRisk(summary) {
    const score = this._clampScore(summary.overallRiskScore);
    const riskLevel = summary.riskLevel || 'low';
    const levelText = this._getRiskLevelText(riskLevel);
    const explanation = this._getRiskLevelExplanation(riskLevel, score);

    return `
      <h3 class="ai-narrative-title">Đánh Giá Rủi Ro Tổng Thể</h3>
      <p class="ai-narrative-text">
        Điểm rủi ro tổng thể ${score} cho thấy hồ sơ rủi ro ${levelText}. ${explanation}
      </p>
    `;
  }

  /**
   * Render dominant risk layers section
   * @private
   * @param {Array<Object>} layers - Layers data
   * @returns {string} HTML string
   */
  _renderDominantLayers(layers) {
    if (!Array.isArray(layers) || layers.length === 0) {
      return `
        <h3 class="ai-narrative-title">Lớp Rủi Ro Chủ Đạo</h3>
        <p class="ai-narrative-text">
          Dữ liệu lớp rủi ro không có sẵn để phân tích.
        </p>
      `;
    }

    const sorted = [...layers].sort((a, b) => {
      const scoreA = parseFloat(a.score) || 0;
      const scoreB = parseFloat(b.score) || 0;
      return scoreB - scoreA;
    });

    const topLayers = sorted.slice(0, 2);
    const layerNames = topLayers.map(l => this._escapeHtml(l.name || 'Không xác định')).join(' và ');
    const scores = topLayers.map(l => this._clampScore(l.score));
    const scoreTextVi = topLayers.length === 1 
      ? `điểm ${scores[0]}`
      : `điểm ${scores[0]} và ${scores[1]}`;
    
    let narrative = `Rủi ro tổng thể tăng cao chủ yếu do ${layerNames}, với ${scoreTextVi} tương ứng.`;

    if (topLayers.length === 2 && sorted.length > 2) {
      const thirdScore = this._clampScore(sorted[2].score);
      narrative += ` Hai lớp này chiếm phần lớn biến động giảm, với lớp cao tiếp theo ở mức ${thirdScore}.`;
    } else if (topLayers.length === 1 && sorted.length > 1) {
      const secondScore = this._clampScore(sorted[1].score);
      narrative += ` Lớp này đại diện cho yếu tố rủi ro chính, với mức phơi nhiễm thứ cấp ở ${secondScore}.`;
    }

    return `
      <h3 class="ai-narrative-title">Lớp Rủi Ro Chủ Đạo</h3>
      <p class="ai-narrative-text">${narrative}</p>
    `;
  }

  /**
   * Render key risk drivers section
   * @private
   * @param {Array<Object>} factors - Factors data
   * @returns {string} HTML string
   */
  _renderKeyDrivers(factors) {
    if (!Array.isArray(factors) || factors.length === 0) {
      return `
        <h3 class="ai-narrative-title">Yếu Tố Rủi Ro Chính</h3>
        <p class="ai-narrative-text">
          Dữ liệu yếu tố rủi ro không có sẵn để phân tích.
        </p>
      `;
    }

    const sorted = [...factors].sort((a, b) => {
      const scoreA = this._getFactorScore(a);
      const scoreB = this._getFactorScore(b);
      return scoreB - scoreA;
    });

    const topFactors = sorted.slice(0, 3);
    const factorNames = topFactors.map(f => this._escapeHtml(f.factor || 'Không xác định'));
    
    let narrative = '';
    if (topFactors.length === 1) {
      const impact = this._getImpactLabel(topFactors[0].impact);
      const prob = (parseFloat(topFactors[0].probability) * 100).toFixed(1);
      const impactVi = impact === 'High' ? 'cao' : impact === 'Medium' ? 'trung bình' : 'thấp';
      narrative = `Yếu tố rủi ro chính là ${factorNames[0]}, với tác động ${impactVi} và xác suất ${prob}%.`;
    } else if (topFactors.length === 2) {
      narrative = `Các yếu tố rủi ro chính là ${factorNames[0]} và ${factorNames[1]}, cùng đại diện cho các điểm phơi nhiễm quan trọng nhất trong hồ sơ rủi ro.`;
    } else {
      narrative = `Các yếu tố rủi ro chính là ${factorNames[0]}, ${factorNames[1]}, và ${factorNames[2]}, cùng tạo nên phần lớn phơi nhiễm rủi ro.`;
    }

    if (topFactors.length > 1) {
      const impactTexts = topFactors.map(f => {
        const impact = this._getImpactLabel(f.impact);
        const prob = (parseFloat(f.probability) * 100).toFixed(1);
        const impactVi = impact === 'High' ? 'cao' : impact === 'Medium' ? 'trung bình' : 'thấp';
        return `tác động ${impactVi} (${prob}% xác suất)`;
      });
      narrative += ` Các yếu tố này thể hiện ${impactTexts.join(', ')} tương ứng.`;
    }

    return `
      <h3 class="ai-narrative-title">Yếu Tố Rủi Ro Chính</h3>
      <p class="ai-narrative-text">${narrative}</p>
    `;
  }

  /**
   * Render loss and tail risk insight section
   * @private
   * @param {Object} loss - Loss data
   * @returns {string} HTML string
   */
  _renderLossInsight(loss) {
    const p95 = loss.p95;
    const p99 = loss.p99;
    const tailContribution = loss.tailContribution;

    if (p95 == null && p99 == null && tailContribution == null) {
      return `
        <h3 class="ai-narrative-title">Thông Tin Tổn Thất & Rủi Ro Đuôi</h3>
        <p class="ai-narrative-text">
          Dữ liệu phân phối tổn thất không có sẵn để phân tích.
        </p>
      `;
    }

    let narrative = '';

    if (p95 != null && Number.isFinite(p95)) {
      const p95Formatted = this._formatCurrency(p95);
      narrative += `Ở mức độ tin cậy phân vị thứ 95, phơi nhiễm tổn thất tiềm năng được ước tính là ${p95Formatted}.`;
    }

    if (p99 != null && Number.isFinite(p99)) {
      const p99Formatted = this._formatCurrency(p99);
      if (narrative) {
        narrative += ` Ở phân vị thứ 99, phơi nhiễm rủi ro đuôi cực đoan đạt ${p99Formatted}.`;
      } else {
        narrative += `Phơi nhiễm rủi ro đuôi cực đoan ở phân vị thứ 99 được ước tính là ${p99Formatted}.`;
      }
    }

    if (tailContribution != null && Number.isFinite(tailContribution)) {
      const tailPercent = Math.max(0, Math.min(100, tailContribution)).toFixed(1);
      if (narrative) {
        narrative += ` Các sự kiện rủi ro đuôi chiếm khoảng ${tailPercent}% tổng phơi nhiễm rủi ro, cho thấy sự tập trung ${tailContribution > 20 ? 'đáng kể' : 'vừa phải'} trong các kịch bản cực đoan.`;
      } else {
        narrative += `Các sự kiện rủi ro đuôi chiếm khoảng ${tailPercent}% tổng phơi nhiễm rủi ro.`;
      }
    }

    if (!narrative) {
      narrative = 'Các chỉ số phân phối tổn thất không đầy đủ và không thể phân tích đầy đủ tại thời điểm này.';
    }

    return `
      <h3 class="ai-narrative-title">Thông Tin Tổn Thất & Rủi Ro Đuôi</h3>
      <p class="ai-narrative-text">${narrative}</p>
    `;
  }

  /**
   * Extract factor score from backend data for sorting (UI-only)
   * ARCHITECTURE: ENGINE-FIRST
   * Backend MUST provide compositeScore already computed
   * This function only extracts the score for UI sorting, does NOT compute
   * @private
   * @param {Object} factor - Factor data from backend (MUST have compositeScore)
   * @returns {number} Composite score (from backend, or 0 if missing)
   */
  _getFactorScore(factor) {
    // Backend MUST provide compositeScore (authoritative)
    if (factor.compositeScore != null) {
      const parsed = parseFloat(factor.compositeScore);
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
    // Fallback to score if provided
    if (factor.score != null) {
      const parsed = parseFloat(factor.score);
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
    
    // If missing, log warning and return 0 (do NOT compute)
    console.warn('[ENGINE-FIRST] AINarrativePanel: Factor missing compositeScore from backend. Cannot sort. Backend should provide compositeScore.');
    return 0; // Neutral value - do NOT compute impact × probability
  }

  /**
   * Get risk level text
   * @private
   * @param {string} riskLevel - Risk level
   * @returns {string} Formatted text
   */
  _getRiskLevelText(riskLevel) {
    if (riskLevel === 'high') return 'cao';
    if (riskLevel === 'medium') return 'trung bình';
    return 'thấp';
  }

  /**
   * Get risk level explanation
   * @private
   * @param {string} riskLevel - Risk level
   * @param {number} score - Risk score
   * @returns {string} Explanation text
   */
  _getRiskLevelExplanation(riskLevel, score) {
    if (riskLevel === 'high') {
      return `Phân loại này phản ánh phơi nhiễm đáng kể trên nhiều chiều rủi ro, đòi hỏi sự chú ý ngay lập tức và các chiến lược giảm thiểu.`;
    }
    if (riskLevel === 'medium') {
      return `Phân loại này cho thấy phơi nhiễm vừa phải cần được giám sát và các biện pháp quản lý rủi ro chủ động.`;
    }
    return `Phân loại này cho thấy mức phơi nhiễm có thể quản lý được với các biện pháp kiểm soát rủi ro tiêu chuẩn.`;
  }

  /**
   * Get impact label
   * @private
   * @param {number} impact - Impact value (0-1)
   * @returns {string} Impact label
   */
  _getImpactLabel(impact) {
    const clamped = this._clampValue(impact);
    if (clamped >= 0.7) return 'High';
    if (clamped >= 0.4) return 'Medium';
    return 'Low';
  }

  /**
   * Clamp score to valid range
   * @private
   * @param {number} score - Input score
   * @returns {number} Clamped score
   */
  _clampScore(score) {
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
    const num = parseFloat(value);
    if (isNaN(num)) return 0;
    return Math.max(0, Math.min(1, num));
  }

  /**
   * Format currency value
   * @private
   * @param {number} value - Currency value
   * @returns {string} Formatted currency string
   */
  _formatCurrency(value) {
    const num = parseFloat(value);
    if (!Number.isFinite(num)) return '$0';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
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

    if (document.getElementById('ai-narrative-panel-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'ai-narrative-panel-styles';
    style.textContent = `
      /* AINarrativePanel Component Styles */
      .ai-narrative-wrapper {
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .ai-narrative-executive {
        padding: 24px 32px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      }

      .ai-narrative-executive-title {
        font-size: 16px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin: 0 0 12px 0;
        letter-spacing: -0.2px;
      }

      .ai-narrative-executive-text {
        font-size: 15px;
        line-height: 1.6;
        color: rgba(255, 255, 255, 0.85);
        margin: 0;
      }

      .ai-narrative-details {
        border-top: none;
      }

      .ai-narrative-summary {
        padding: 16px 32px;
        cursor: pointer;
        list-style: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
        user-select: none;
        transition: background-color 0.2s ease;
      }

      .ai-narrative-summary::-webkit-details-marker {
        display: none;
      }

      .ai-narrative-summary:hover {
        background-color: rgba(255, 255, 255, 0.03);
      }

      .ai-narrative-summary-text {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        letter-spacing: -0.1px;
      }

      .ai-narrative-summary-icon {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
        transition: transform 0.2s ease;
      }

      .ai-narrative-sections {
        padding: 0 32px 32px 32px;
      }

      .ai-narrative-section {
        margin-bottom: 28px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding-bottom: 28px;
      }

      .ai-narrative-section:last-child {
        border-bottom: none;
        padding-bottom: 0;
        margin-bottom: 0;
      }

      .ai-narrative-title {
        font-size: 16px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.9);
        margin: 0 0 10px 0;
        letter-spacing: -0.2px;
      }

      .ai-narrative-text {
        font-size: 14px;
        line-height: 1.7;
        color: rgba(255, 255, 255, 0.7);
        margin: 0;
        font-weight: 400;
      }

      @media (max-width: 768px) {
        .ai-narrative-executive {
          padding: 20px 24px;
        }

        .ai-narrative-summary {
          padding: 14px 24px;
        }

        .ai-narrative-sections {
          padding: 0 24px 24px 24px;
        }

        .ai-narrative-section {
          padding-bottom: 24px;
          margin-bottom: 24px;
        }

        .ai-narrative-executive-title,
        .ai-narrative-title {
          font-size: 15px;
        }

        .ai-narrative-executive-text,
        .ai-narrative-text {
          font-size: 13px;
          line-height: 1.6;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}
