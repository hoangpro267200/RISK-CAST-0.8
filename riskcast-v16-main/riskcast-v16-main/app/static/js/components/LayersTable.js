/**
 * LayersTable Component
 * 
 * Displays risk layers overview in a clean enterprise table format.
 * Sorted by score (descending), color-coded by risk level.
 * 
 * @class LayersTable
 * @exports LayersTable
 */
export class LayersTable {
  /**
   * Initialize the LayersTable component
   */
  constructor() {
    this.container = null;
    this.tableBody = null;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Array<Object>} data - Array of layer objects
   * @param {string} data[].name - Layer name
   * @param {number} data[].score - Risk score (0-100)
   * @param {string} data[].note - Description note
   */
  mount(el, data = []) {
    if (!el) {
      return;
    }

    this.container = el;
    this._injectStyles();
    this._createStructure();
    this._render(data);
  }

  /**
   * Update the table with new data
   * @param {Array<Object>} data - Updated layer data
   */
  update(data = []) {
    if (!this.container || !this.tableBody) {
      return;
    }

    this._render(data);
  }

  /**
   * Cleanup and destroy component
   */
  destroy() {
    this.container = null;
    this.tableBody = null;
  }

  /**
   * Create table structure
   * @private
   */
  _createStructure() {
    this.container.innerHTML = `
      <div class="layers-table-wrapper">
        <table class="layers-table">
          <thead>
            <tr>
              <th class="layers-th-name">Tên</th>
              <th class="layers-th-score">Điểm</th>
              <th class="layers-th-note">Note</th>
            </tr>
          </thead>
          <tbody class="layers-tbody"></tbody>
        </table>
      </div>
    `;

    this.tableBody = this.container.querySelector('.layers-tbody');
  }

  /**
   * Render table rows
   * @private
   * @param {Array<Object>} data - Layer data
   */
  _render(data) {
    if (!Array.isArray(data) || data.length === 0) {
      this._renderEmpty();
      return;
    }

    // Sort by score DESC
    const sorted = [...data].sort((a, b) => {
      const scoreA = parseFloat(a.score) || 0;
      const scoreB = parseFloat(b.score) || 0;
      return scoreB - scoreA;
    });

    const rows = sorted.map((layer, index) => this._createRow(layer, index)).join('');
    this.tableBody.innerHTML = rows;
  }

  /**
   * Create single table row HTML
   * @private
   * @param {Object} layer - Layer data
   * @param {number} index - Row index
   * @returns {string} HTML string
   */
  _createRow(layer, index) {
    const name = this._escapeHtml(layer.name || 'Unknown');
    const score = this._clampScore(layer.score);
    const note = this._escapeHtml(layer.note || '—');
    const riskClass = this._getRiskClass(score);

    return `
      <tr class="layers-row">
        <td class="layers-td-name">${name}</td>
        <td class="layers-td-score">
          <span class="layers-score-badge ${riskClass}">${score}</span>
        </td>
        <td class="layers-td-note">${note}</td>
      </tr>
    `;
  }

  /**
   * Render empty state
   * @private
   */
  _renderEmpty() {
    this.tableBody.innerHTML = `
      <tr class="layers-empty-row">
        <td colspan="3" class="layers-empty-cell">
          Không có dữ liệu lớp rủi ro
        </td>
      </tr>
    `;
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
   * Map score to risk class for CSS coloring (UI-only)
   * ARCHITECTURE: ENGINE-FIRST
   * This is used ONLY for visual styling (color mapping), NOT business logic
   * Backend MUST provide the authoritative risk level - this is just for CSS classes
   * @private
   * @param {number} score - Risk score
   * @returns {string} CSS class name (for visual styling only)
   */
  _getRiskClass(score) {
    // UI-only visual threshold mapping for CSS classes
    // Backend's risk levels should always be used for business decisions
    if (score >= 70) return 'risk-high';
    if (score >= 40) return 'risk-medium';
    return 'risk-low';
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
    if (document.getElementById('layers-table-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'layers-table-styles';
    style.textContent = `
      /* LayersTable Component Styles */
      .layers-table-wrapper {
        background: rgba(15, 15, 20, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 20px;
        overflow-x: auto;
      }

      .layers-table {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
        font-size: 13px;
        color: rgba(255, 255, 255, 0.85);
      }

      .layers-table thead {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }

      .layers-table th {
        text-align: left;
        padding: 12px 16px;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: rgba(255, 255, 255, 0.5);
      }

      .layers-th-name {
        width: 30%;
      }

      .layers-th-score {
        width: 15%;
      }

      .layers-th-note {
        width: 55%;
      }

      .layers-tbody tr {
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        transition: background-color 0.15s ease;
      }

      .layers-tbody tr:last-child {
        border-bottom: none;
      }

      .layers-row:hover {
        background-color: rgba(255, 255, 255, 0.03);
      }

      .layers-table td {
        padding: 14px 16px;
        vertical-align: middle;
      }

      .layers-td-name {
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
      }

      .layers-td-score {
        font-weight: 600;
      }

      .layers-td-note {
        color: rgba(255, 255, 255, 0.6);
        font-size: 12px;
      }

      .layers-score-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: -0.2px;
      }

      .layers-score-badge.risk-low {
        background: rgba(0, 255, 136, 0.12);
        color: var(--risk-low);
      }

      .layers-score-badge.risk-medium {
        background: rgba(255, 204, 0, 0.12);
        color: var(--risk-medium);
      }

      .layers-score-badge.risk-high {
        background: rgba(255, 68, 102, 0.12);
        color: var(--risk-high);
      }

      .layers-empty-row {
        border-bottom: none !important;
      }

      .layers-empty-cell {
        text-align: center;
        padding: 60px 20px !important;
        color: rgba(255, 255, 255, 0.4);
        font-size: 13px;
        font-weight: 500;
      }

      @media (max-width: 768px) {
        .layers-table-wrapper {
          padding: 16px;
        }

        .layers-table th,
        .layers-table td {
          padding: 10px 12px;
          font-size: 12px;
        }

        .layers-th-name {
          width: 35%;
        }

        .layers-th-score {
          width: 20%;
        }

        .layers-th-note {
          width: 45%;
        }
      }
    `;

    document.head.appendChild(style);
  }
}
