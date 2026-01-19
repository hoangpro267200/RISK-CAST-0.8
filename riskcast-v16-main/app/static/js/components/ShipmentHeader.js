/**
 * ShipmentHeader Component
 * 
 * Displays high-level shipment metadata in a glassmorphic card.
 * Shows: ID, route, incoterms, cargo type, value, and ETA.
 * 
 * @class ShipmentHeader
 * @exports ShipmentHeader
 */
export class ShipmentHeader {
  /**
   * Initialize the ShipmentHeader component
   */
  constructor() {
    this.container = null;
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {Object} shipment - Shipment data object (UI DTO)
   * @param {string} shipment.id - Shipment identifier
   * @param {string} shipment.route - Pre-formatted route string
   * @param {string} shipment.incoterms - Incoterms code (e.g., FOB, CIF)
   * @param {string} shipment.cargoType - Type of cargo
   * @param {number} shipment.cargoValue - Cargo value in USD
   * @param {string} shipment.eta - Estimated time of arrival (ISO date or formatted)
   */
  mount(el, shipment = {}) {
    if (!el) {
      console.warn('ShipmentHeader: No element provided for mounting');
      return;
    }

    this.container = el;
    this._injectStyles();
    this.render(shipment);
  }

  /**
   * Update the component with new data
   * @param {Object} shipment - Updated shipment data
   */
  update(shipment = {}) {
    if (!this.container) {
      console.warn('ShipmentHeader: Component not mounted');
      return;
    }
    this.render(shipment);
  }

  /**
   * Normalize shipment data for internal use
   * @private
   * @param {Object} shipment - Raw shipment data
   * @returns {Object} Normalized shipment data
   */
  _normalizeData(shipment) {
    return {
      id: this._normalizeId(shipment.id),
      route: this._normalizeRoute(shipment.route),
      incoterms: this._normalizeString(shipment.incoterms),
      cargoType: this._normalizeString(shipment.cargoType),
      cargoValue: this._normalizeNumber(shipment.cargoValue),
      eta: this._normalizeString(shipment.eta),
    };
  }

  /**
   * Normalize shipment ID
   * @private
   * @param {*} id - Shipment ID
   * @returns {string} Normalized ID
   */
  _normalizeId(id) {
    if (id == null || id === '') {
      return 'N/A';
    }
    return String(id);
  }

  /**
   * Normalize route string
   * @private
   * @param {*} route - Route string (pre-formatted)
   * @returns {string} Normalized route
   */
  _normalizeRoute(route) {
    if (route == null || route === '') {
      return 'Chưa chỉ định tuyến đường';
    }
    return String(route);
  }

  /**
   * Normalize string value
   * @private
   * @param {*} value - String value
   * @returns {string} Normalized string or empty
   */
  _normalizeString(value) {
    if (value == null || value === '') {
      return '';
    }
    return String(value);
  }

  /**
   * Normalize number value
   * @private
   * @param {*} value - Numeric value
   * @returns {number|null} Normalized number or null
   */
  _normalizeNumber(value) {
    if (value == null || value === '') {
      return null;
    }
    const num = Number(value);
    return isNaN(num) ? null : num;
  }

  /**
   * Format currency value to USD string
   * @private
   * @param {number|null} value - Numeric value
   * @returns {string} Formatted currency string
   */
  _formatCurrency(value) {
    if (value == null || typeof value !== 'number' || isNaN(value)) {
      return 'N/A';
    }
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    } catch (e) {
      return 'N/A';
    }
  }

  /**
   * Format date string for ETA display
   * @private
   * @param {string} dateStr - ISO date string or formatted date
   * @returns {string} Formatted date string
   */
  _formatETA(dateStr) {
    if (!dateStr || dateStr === '') {
      return 'TBD';
    }
    
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) {
        return String(dateStr);
      }
      
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (e) {
      return String(dateStr);
    }
  }

  /**
   * Render the component HTML
   * @private
   * @param {Object} shipment - Shipment data
   */
  render(shipment) {
    const data = this._normalizeData(shipment);
    
    const formattedValue = this._formatCurrency(data.cargoValue);
    const formattedETA = this._formatETA(data.eta);

    this.container.innerHTML = `
      <div class="shipment-header-card">
        <!-- Top Row: ID and Route -->
        <div class="sh-top-row">
          <div class="sh-id-section">
            <div class="sh-label">Mã Lô Hàng</div>
            <div class="sh-id">${this._escapeHtml(data.id)}</div>
          </div>
          <div class="sh-route-section">
            <div class="sh-label">Tuyến Đường</div>
            <div class="sh-route">${this._escapeHtml(data.route)}</div>
          </div>
        </div>

        <!-- Middle Row: Chips (Incoterms + Cargo Type) -->
        <div class="sh-chips-row">
          ${data.incoterms ? `<span class="sh-chip sh-chip-incoterms">${this._escapeHtml(data.incoterms)}</span>` : ''}
          ${data.cargoType ? `<span class="sh-chip sh-chip-cargo">${this._escapeHtml(data.cargoType)}</span>` : ''}
        </div>

        <!-- Bottom Row: Value and ETA -->
        <div class="sh-bottom-row">
          <div class="sh-value-section">
            <div class="sh-label">Giá Trị Hàng Hóa</div>
            <div class="sh-value">${this._escapeHtml(formattedValue)}</div>
          </div>
          <div class="sh-eta-section">
            <div class="sh-label">Thời Gian Dự Kiến</div>
            <div class="sh-eta">${this._escapeHtml(formattedETA)}</div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Escape HTML to prevent XSS
   * @private
   * @param {*} str - Value to escape
   * @returns {string} Escaped string
   */
  _escapeHtml(str) {
    if (str == null) {
      return '';
    }
    
    const div = document.createElement('div');
    div.textContent = String(str);
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

    if (document.getElementById('shipment-header-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'shipment-header-styles';
    style.textContent = `
      /* ShipmentHeader Component Styles */
      .shipment-header-card {
        background: rgba(20, 20, 25, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px 28px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        display: flex;
        flex-direction: column;
        gap: 20px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
        color: #e0e0e0;
      }

      /* Top Row */
      .sh-top-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 24px;
        flex-wrap: wrap;
      }

      .sh-id-section,
      .sh-route-section,
      .sh-value-section,
      .sh-eta-section {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .sh-label {
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: rgba(255, 255, 255, 0.45);
      }

      .sh-id {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.3px;
      }

      .sh-route {
        font-size: 14px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.6);
      }

      /* Chips Row */
      .sh-chips-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }

      .sh-chip {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.85);
      }

      .sh-chip-incoterms {
        background: rgba(100, 200, 255, 0.12);
        border-color: rgba(100, 200, 255, 0.25);
        color: #64c8ff;
      }

      .sh-chip-cargo {
        background: rgba(180, 140, 255, 0.12);
        border-color: rgba(180, 140, 255, 0.25);
        color: #b48cff;
      }

      /* Bottom Row */
      .sh-bottom-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 24px;
        flex-wrap: wrap;
        padding-top: 8px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
      }

      .sh-value {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
      }

      .sh-eta {
        font-size: 18px;
        font-weight: 700;
        color: #00ff88;
        text-shadow: 0 0 12px rgba(0, 255, 136, 0.3);
      }

      /* Responsive adjustments */
      @media (max-width: 640px) {
        .shipment-header-card {
          padding: 20px;
          gap: 16px;
        }

        .sh-id {
          font-size: 20px;
        }

        .sh-value {
          font-size: 18px;
        }

        .sh-eta {
          font-size: 16px;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}
