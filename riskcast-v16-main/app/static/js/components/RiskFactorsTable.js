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
 * RiskFactorsTable Component
 * 
 * Displays atomic risk drivers with impact and probability metrics.
 * Sorted by impact (descending), then probability (descending).
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - Receives factors array from backend (already computed)
 * - Backend MUST provide compositeScore
 * - Sorting is UI-only for display organization
 * 
 * @class RiskFactorsTable
 * @exports RiskFactorsTable
 */
export class RiskFactorsTable {
  /**
   * Initialize the RiskFactorsTable component
   */
  constructor() {
    this.container = null;
    this.tableBody = null;
    this._hasCompositeScore = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Array<Object>} data - Array of risk factor objects
   * @param {string} data[].factor - Factor name
   * @param {number} data[].impact - Impact value (0-1)
   * @param {number} data[].probability - Probability value (0-1)
   * @param {number} [data[].compositeScore] - Optional composite risk score (0-1)
   */
  mount(el, data = []) {
    if (!el) {
      return;
    }

    this.container = el;
    this._injectStyles();
    this._checkCompositeScore(data);
    this._createStructure();
    this._render(data);
  }

  /**
   * Update the table with new data
   * @param {Array<Object>} data - Updated risk factor data
   */
  update(data = []) {
    if (!this.container || !this.tableBody) {
      return;
    }

    const hadComposite = this._hasCompositeScore;
    this._checkCompositeScore(data);
    
    if (hadComposite !== this._hasCompositeScore) {
      this._createStructure();
    }
    
    this._render(data);
  }

  /**
   * Check if data contains composite score
   * @private
   * @param {Array<Object>} data - Risk factor data
   */
  _checkCompositeScore(data) {
    this._hasCompositeScore = Array.isArray(data) && data.some(item => {
      const parsed = parseFloat(item.compositeScore);
      return Number.isFinite(parsed);
    });
  }

  /**
   * Cleanup and destroy component
   */
  destroy() {
    this.container = null;
    this.tableBody = null;
    this._hasCompositeScore = false;
  }

  /**
   * Create table structure
   * @private
   */
  _createStructure() {
    const compositeHeader = this._hasCompositeScore 
      ? '<th class="rf-th-composite">Điểm Rủi Ro</th>' 
      : '';

    this.container.innerHTML = `
      <div class="risk-factors-table-wrapper">
        <table class="risk-factors-table">
          <thead>
            <tr>
              <th class="rf-th-factor">Yếu Tố</th>
              <th class="rf-th-impact">Tác Động</th>
              <th class="rf-th-probability">Xác Suất</th>
              ${compositeHeader}
            </tr>
          </thead>
          <tbody class="rf-tbody"></tbody>
        </table>
      </div>
    `;

    this.tableBody = this.container.querySelector('.rf-tbody');
  }

  /**
   * Render table rows
   * @private
   * @param {Array<Object>} data - Risk factor data
   */
  _render(data) {
    if (!Array.isArray(data) || data.length === 0) {
      this._renderEmpty();
      return;
    }

    // Sort by impact DESC, then probability DESC
    const sorted = [...data].sort((a, b) => {
      const impactA = parseFloat(a.impact) || 0;
      const impactB = parseFloat(b.impact) || 0;
      if (impactB !== impactA) {
        return impactB - impactA;
      }
      const probA = parseFloat(a.probability) || 0;
      const probB = parseFloat(b.probability) || 0;
      return probB - probA;
    });

    const rows = sorted.map((factor, index) => this._createRow(factor, index)).join('');
    this.tableBody.innerHTML = rows;
  }

  /**
   * Create single table row HTML
   * @private
   * @param {Object} factor - Risk factor data
   * @param {number} index - Row index
   * @returns {string} HTML string
   */
  _createRow(factor, index) {
    const factorName = this._escapeHtml(factor.factor || 'Unknown');
    const impact = this._clampValue(factor.impact);
    const probability = this._clampValue(factor.probability);
    
    const impactLabel = this._getImpactLabel(impact);
    const probabilityPercent = this._formatProbability(probability);
    const rowClass = this._getRowClass(impact);

    let compositeCell = '';
    if (this._hasCompositeScore) {
      const parsed = parseFloat(factor.compositeScore);
      if (Number.isFinite(parsed)) {
        const clamped = Math.max(0, Math.min(1, parsed));
        compositeCell = `<td class="rf-td-composite">
           <span class="rf-composite-score">${(clamped * 100).toFixed(1)}%</span>
         </td>`;
      } else {
        compositeCell = '<td class="rf-td-composite">—</td>';
      }
    }

    return `
      <tr class="rf-row ${rowClass}">
        <td class="rf-td-factor">${factorName}</td>
        <td class="rf-td-impact">
          <span class="rf-impact-badge">${impactLabel}</span>
        </td>
        <td class="rf-td-probability">${probabilityPercent}</td>
        ${compositeCell}
      </tr>
    `;
  }

  /**
   * Render empty state
   * @private
   */
  _renderEmpty() {
    const colspan = this._hasCompositeScore ? 4 : 3;
    this.tableBody.innerHTML = `
      <tr class="rf-empty-row">
        <td colspan="${colspan}" class="rf-empty-cell">
          Không phát hiện yếu tố rủi ro
        </td>
      </tr>
    `;
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
   * Get impact label from value
   * @private
   * @param {number} impact - Impact value (0-1)
   * @returns {string} Impact label
   */
  _getImpactLabel(impact) {
    if (impact >= 0.7) return 'Cao';
    if (impact >= 0.4) return 'Trung Bình';
    return 'Thấp';
  }

  /**
   * Format probability as percentage
   * @private
   * @param {number} probability - Probability value (0-1)
   * @returns {string} Formatted percentage
   */
  _formatProbability(probability) {
    return `${(probability * 100).toFixed(1)}%`;
  }

  /**
   * Get row highlight class based on impact
   * @private
   * @param {number} impact - Impact value (0-1)
   * @returns {string} CSS class name
   */
  _getRowClass(impact) {
    if (impact >= 0.7) return 'rf-row-high';
    if (impact >= 0.4) return 'rf-row-medium';
    return '';
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
    if (document.getElementById('risk-factors-table-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'risk-factors-table-styles';
    style.textContent = `
      /* RiskFactorsTable Component Styles */
      .risk-factors-table-wrapper {
        background: rgba(15, 15, 20, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 20px;
        overflow-x: auto;
      }

      .risk-factors-table {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        font-size: 13px;
        color: rgba(255, 255, 255, 0.85);
      }

      .risk-factors-table thead {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }

      .risk-factors-table th {
        text-align: left;
        padding: 12px 16px;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: rgba(255, 255, 255, 0.5);
      }

      .rf-th-factor {
        width: 50%;
      }

      .rf-th-impact {
        width: 25%;
      }

      .rf-th-probability {
        width: 25%;
      }

      .rf-th-composite {
        width: 20%;
      }

      .rf-tbody tr {
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        transition: background-color 0.15s ease;
      }

      .rf-tbody tr:last-child {
        border-bottom: none;
      }

      .rf-row:hover {
        background-color: rgba(255, 255, 255, 0.02);
      }

      .rf-row-high {
        background-color: rgba(255, 68, 102, 0.06);
      }

      .rf-row-high:hover {
        background-color: rgba(255, 68, 102, 0.09);
      }

      .rf-row-medium {
        background-color: rgba(255, 204, 0, 0.05);
      }

      .rf-row-medium:hover {
        background-color: rgba(255, 204, 0, 0.08);
      }

      .risk-factors-table td {
        padding: 14px 16px;
        vertical-align: middle;
      }

      .rf-td-factor {
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
      }

      .rf-td-impact {
        font-weight: 600;
      }

      .rf-td-probability {
        font-weight: 600;
        color: rgba(255, 255, 255, 0.75);
        font-variant-numeric: tabular-nums;
      }

      .rf-td-composite {
        font-weight: 600;
        color: rgba(255, 255, 255, 0.65);
        font-variant-numeric: tabular-nums;
        font-size: 12px;
      }

      .rf-composite-score {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.03);
        color: rgba(255, 255, 255, 0.7);
      }

      .rf-impact-badge {
        display: inline-block;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 4px;
        padding: 2px 6px;
      }

      .rf-row-high .rf-impact-badge {
        color: var(--risk-high);
      }

      .rf-row-medium .rf-impact-badge {
        color: var(--risk-medium);
      }

      .rf-impact-badge {
        color: var(--risk-low);
      }

      .rf-empty-row {
        border-bottom: none !important;
      }

      .rf-empty-cell {
        text-align: center;
        padding: 60px 20px !important;
        color: rgba(255, 255, 255, 0.4);
        font-size: 13px;
        font-weight: 500;
      }

      @media (max-width: 768px) {
        .risk-factors-table-wrapper {
          padding: 16px;
        }

        .risk-factors-table th,
        .risk-factors-table td {
          padding: 10px 12px;
          font-size: 12px;
        }

        .rf-th-factor {
          width: 45%;
        }

        .rf-th-impact {
          width: 20%;
        }

        .rf-th-probability {
          width: 20%;
        }

        .rf-th-composite {
          width: 15%;
        }
      }
    `;

    document.head.appendChild(style);
  }
}
