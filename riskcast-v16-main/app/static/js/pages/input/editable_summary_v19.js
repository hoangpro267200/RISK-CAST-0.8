/**
 * RISKCAST v19 - Editable Summary Panel Extension
 * Safe, non-breaking upgrade to enable inline editing from Summary page
 * Author: RISKCAST Team
 * Version: 19.1.0
 */

// =====================================
// 1. GLOBAL STATE INITIALIZATION
// =====================================
if (typeof window.RC_STATE === 'undefined') {
  window.RC_STATE = {
    transport: {},
    cargo: {},
    seller: {},
    buyer: {},
    modules: {},
    riskScore: 0
  };
}

/**
 * Get current snapshot of key summary fields
 * @returns {Object} Summary data snapshot
 */
function getSummarySnapshot() {
  return {
    origin: RC_STATE.transport.origin || '',
    destination: RC_STATE.transport.destination || '',
    mode: RC_STATE.transport.mode || '',
    containerType: RC_STATE.transport.containerType || '',
    transitType: RC_STATE.transport.transitType || '',
    cargoType: RC_STATE.cargo.type || '',
    packing: RC_STATE.cargo.packing || '',
    grossWeight: RC_STATE.cargo.weight || '',
    insuranceValue: RC_STATE.cargo.insuranceValue || '',
    incoterm: RC_STATE.seller.incoterm || '',
    sellerCountry: RC_STATE.seller.country || ''
  };
}

// =====================================
// 2. FIELD EDITOR CONFIGURATION
// =====================================
const SUMMARY_EDITORS = {
  "transport.mode": {
    type: "dropdown",
    label: "Phương thức vận chuyển",
    options: window.logistics_data?.TRANSPORT_MODES || [
      { value: "sea", label: "Đường biển" },
      { value: "air", label: "Đường hàng không" },
      { value: "road", label: "Đường bộ" },
      { value: "rail", label: "Đường sắt" }
    ]
  },
  "transport.containerType": {
    type: "dropdown",
    label: "Loại container",
    optionsSource: "CONTAINER_TYPES_BY_MODE"
  },
  "transport.origin": {
    type: "dropdown",
    label: "Điểm xuất phát",
    optionsSource: "ORIGIN_PORTS_BY_MODE"
  },
  "transport.destination": {
    type: "dropdown",
    label: "Điểm đến",
    optionsSource: "DESTINATION_PORTS_BY_MODE"
  },
  "cargo.type": {
    type: "dropdown",
    label: "Loại hàng hóa",
    options: window.logistics_data?.CARGO_TYPES || [
      { value: "general", label: "Hàng hóa thông thường" },
      { value: "perishable", label: "Hàng dễ hỏng" },
      { value: "hazardous", label: "Hàng nguy hiểm" },
      { value: "fragile", label: "Hàng dễ vỡ" }
    ]
  },
  "cargo.packing": {
    type: "dropdown",
    label: "Phương thức đóng gói",
    options: window.logistics_data?.PACKING_TYPES || [
      { value: "standard", label: "Tiêu chuẩn" },
      { value: "reinforced", label: "Gia cố" },
      { value: "custom", label: "Tùy chỉnh" }
    ]
  },
  "cargo.weight": {
    type: "number",
    label: "Trọng lượng (kg)",
    min: 0,
    step: 0.01
  },
  "cargo.insuranceValue": {
    type: "number",
    label: "Giá trị bảo hiểm (USD)",
    min: 0,
    step: 0.01
  },
  "seller.country": {
    type: "dropdown",
    label: "Quốc gia người bán",
    options: window.logistics_data?.SELLER_COUNTRIES || [
      { value: "CN", label: "Trung Quốc" },
      { value: "VN", label: "Việt Nam" },
      { value: "US", label: "Hoa Kỳ" },
      { value: "JP", label: "Nhật Bản" }
    ]
  },
  "seller.incoterm": {
    type: "dropdown",
    label: "Điều kiện Incoterm",
    options: window.logistics_data?.INCOTERMS_2020 || [
      { value: "EXW", label: "EXW - Ex Works" },
      { value: "FOB", label: "FOB - Free on Board" },
      { value: "CIF", label: "CIF - Cost Insurance Freight" },
      { value: "DDP", label: "DDP - Delivered Duty Paid" }
    ]
  }
};

/**
 * Get dynamic options based on current state
 * @param {string} sourceKey - Options source identifier
 * @returns {Array} Array of option objects
 */
function getDynamicOptions(sourceKey) {
  const mode = RC_STATE.transport.mode;
  
  switch(sourceKey) {
    case "CONTAINER_TYPES_BY_MODE":
      if (mode === "sea") {
        return window.logistics_data?.CONTAINER_TYPES?.sea || [
          { value: "20ft", label: "20ft Standard" },
          { value: "40ft", label: "40ft Standard" },
          { value: "40ft-hc", label: "40ft High Cube" },
          { value: "reefer", label: "Reefer Container" }
        ];
      } else if (mode === "air") {
        return window.logistics_data?.CONTAINER_TYPES?.air || [
          { value: "uld", label: "ULD Container" },
          { value: "pallet", label: "Pallet" }
        ];
      }
      return [{ value: "standard", label: "Standard" }];
      
    case "ORIGIN_PORTS_BY_MODE":
      if (mode === "sea") {
        return window.logistics_data?.LOCATIONS?.VN?.sea || [
          { value: "CNSHA", label: "Shanghai, China" },
          { value: "SGSIN", label: "Singapore" },
          { value: "VNSGN", label: "Ho Chi Minh, Vietnam" }
        ];
      } else if (mode === "air") {
        return window.logistics_data?.LOCATIONS?.VN?.air || [
          { value: "PVG", label: "Shanghai Pudong" },
          { value: "SIN", label: "Singapore Changi" },
          { value: "SGN", label: "Tan Son Nhat" }
        ];
      }
      return [];
      
    case "DESTINATION_PORTS_BY_MODE":
      // Same logic as origin
      return getDynamicOptions("ORIGIN_PORTS_BY_MODE");
      
    default:
      return [];
  }
}

// =====================================
// 3. FIELD EDITOR MODAL
// =====================================
let currentEditField = null;

/**
 * Open field editor modal
 * @param {string} fieldKey - Field identifier (e.g., "transport.mode")
 */
function openFieldEditor(fieldKey) {
  const config = SUMMARY_EDITORS[fieldKey];
  if (!config) {
    console.error(`No editor config for field: ${fieldKey}`);
    return;
  }
  
  currentEditField = fieldKey;
  
  // Get current value
  const keys = fieldKey.split('.');
  const currentValue = RC_STATE[keys[0]]?.[keys[1]] || '';
  
  // Get options
  let options = config.options;
  if (config.optionsSource) {
    options = getDynamicOptions(config.optionsSource);
  }
  
  // Create modal HTML
  const modalHTML = `
    <div class="rc-modal-overlay" id="rcFieldEditorModal">
      <div class="rc-modal-container">
        <div class="rc-modal-header">
          <h3>Chỉnh sửa ${config.label}</h3>
          <button class="rc-modal-close" onclick="closeFieldEditor()">&times;</button>
        </div>
        <div class="rc-modal-body">
          ${renderEditorInput(config, currentValue, options)}
          <div class="rc-ai-suggest-wrapper" style="margin-top: 12px;">
            <button class="rc-ai-suggest" onclick="handleAISuggest('${fieldKey}')">
              <span>✨</span> Ask AI to suggest
            </button>
          </div>
        </div>
        <div class="rc-modal-footer">
          <button class="rc-btn-secondary" onclick="closeFieldEditor()">Cancel</button>
          <button class="rc-btn-primary" onclick="saveFieldChanges()">Save Changes</button>
        </div>
      </div>
    </div>
  `;
  
  // Remove existing modal if any
  const existingModal = document.getElementById('rcFieldEditorModal');
  if (existingModal) {
    existingModal.remove();
  }
  
  // Append to body
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  
  // Focus on input
  setTimeout(() => {
    const input = document.querySelector('#rcFieldEditorModal input, #rcFieldEditorModal select');
    if (input) input.focus();
  }, 100);
}

/**
 * Render appropriate input element based on config
 * @param {Object} config - Field configuration
 * @param {string} currentValue - Current field value
 * @param {Array} options - Dropdown options (if applicable)
 * @returns {string} HTML string
 */
function renderEditorInput(config, currentValue, options) {
  if (config.type === "dropdown") {
    const optionsHTML = options.map(opt => 
      `<option value="${opt.value}" ${opt.value === currentValue ? 'selected' : ''}>
        ${opt.label || opt.name || opt}
      </option>`
    ).join('');
    
    return `
      <select id="rcFieldEditorInput" class="rc-field-input">
        <option value="">-- Chọn --</option>
        ${optionsHTML}
      </select>
    `;
  } else if (config.type === "number") {
    return `
      <input 
        type="number" 
        id="rcFieldEditorInput" 
        class="rc-field-input"
        value="${currentValue}"
        min="${config.min || 0}"
        step="${config.step || 1}"
        placeholder="Nhập giá trị..."
      />
    `;
  } else {
    // Text input fallback
    return `
      <input 
        type="text" 
        id="rcFieldEditorInput" 
        class="rc-field-input"
        value="${currentValue}"
        placeholder="Nhập giá trị..."
      />
    `;
  }
}

/**
 * Close field editor modal
 */
function closeFieldEditor() {
  const modal = document.getElementById('rcFieldEditorModal');
  if (modal) {
    modal.classList.add('rc-modal-closing');
    setTimeout(() => modal.remove(), 150);
  }
  currentEditField = null;
}

/**
 * Save changes from field editor
 */
function saveFieldChanges() {
  if (!currentEditField) return;
  
  const input = document.getElementById('rcFieldEditorInput');
  if (!input) return;
  
  const newValue = input.value;
  const keys = currentEditField.split('.');
  
  // 1. Update RC_STATE
  if (!RC_STATE[keys[0]]) {
    RC_STATE[keys[0]] = {};
  }
  RC_STATE[keys[0]][keys[1]] = newValue;
  
  // 2. Update corresponding DOM input element
  updateDOMInput(currentEditField, newValue);
  
  // 3. Recalculate risk
  if (typeof window.calculateRisk === 'function') {
    window.calculateRisk();
  }
  
  // 4. Re-render summary
  renderSummaryFromState();
  
  // Close modal
  closeFieldEditor();
  
  // Show success feedback
  showNotification('Đã cập nhật thành công!');
}

/**
 * Update original form input element
 * @param {string} fieldKey - Field identifier
 * @param {string} newValue - New value to set
 */
function updateDOMInput(fieldKey, newValue) {
  const keys = fieldKey.split('.');
  const possibleIds = [
    `${keys[0]}_${keys[1]}`,
    `${keys[0]}${keys[1].charAt(0).toUpperCase() + keys[1].slice(1)}`,
    keys[1],
    `input_${keys[1]}`
  ];
  
  // Try to find the input element
  for (const id of possibleIds) {
    const input = document.getElementById(id) || document.querySelector(`[name="${id}"]`);
    if (input) {
      input.value = newValue;
      
      // Trigger change event
      const event = new Event('change', { bubbles: true });
      input.dispatchEvent(event);
      
      return;
    }
  }
  
  console.warn(`Could not find DOM input for: ${fieldKey}`);
}

// =====================================
// 4. SUMMARY RERENDER FUNCTION
// =====================================
/**
 * Sync RC_STATE from input controller formData
 */
function syncRCStateFromInputController() {
  // Try to get formData from input controller
  const inputController = window.rcController || window.riskcastInputController;
  if (inputController && inputController.formData) {
    const fd = inputController.formData;
    
    // Sync transport data
    RC_STATE.transport = {
      origin: fd.pol || fd.originPort || '',
      destination: fd.pod || fd.destinationPort || '',
      mode: fd.mode || fd.transportMode || '',
      containerType: fd.containerType || '',
      transitType: fd.serviceRoute || '',
      carrier: fd.carrier || '',
      transitDays: fd.transitDays || null
    };
    
    // Sync cargo data
    RC_STATE.cargo = {
      type: fd.cargoType || '',
      packing: fd.packingType || '',
      weight: fd.grossWeight || '',
      insuranceValue: fd.insuranceValue || '',
      volume: fd.cargoVolume || ''
    };
    
    // Sync seller data
    RC_STATE.seller = {
      country: fd.sellerCountry || '',
      incoterm: fd.incoterm || ''
    };
    
    // Sync buyer data
    RC_STATE.buyer = {
      country: fd.buyerCountry || ''
    };
    
    // Sync risk score
    if (inputController.currentRiskScore !== undefined) {
      RC_STATE.riskScore = inputController.currentRiskScore;
    }
    
    console.log('[Editable Summary] RC_STATE synced from input controller:', RC_STATE);
    return true;
  }
  return false;
}

/**
 * Update editable buttons with current recap values
 */
function updateEditableButtonsFromRecap() {
  // Get values from recap elements
  const recapMode = document.getElementById('rc-recap-mode');
  const recapContainer = document.getElementById('rc-recap-container');
  const recapOrigin = document.getElementById('rc-recap-origin');
  const recapDestination = document.getElementById('rc-recap-destination');
  const recapCargo = document.getElementById('rc-recap-cargo');
  const recapPacking = document.getElementById('rc-recap-packing');
  const recapWeight = document.getElementById('rc-recap-weight');
  const recapInsurance = document.getElementById('rc-recap-insurance');
  const recapSellerCountry = document.getElementById('rc-recap-seller-country');
  const recapIncoterm = document.getElementById('rc-recap-incoterm');
  
  // Helper to extract text value from element (handles editable buttons)
  const getValueFromRecap = (el) => {
    if (!el) return '';
    const editableBtn = el.querySelector('.rc-editable-field');
    if (editableBtn) {
      const textSpan = editableBtn.querySelector('.rc-editable-field-text');
      if (textSpan) return textSpan.textContent.trim();
    }
    return el.textContent.trim() || '';
  };
  
  // Update editable buttons
  if (recapMode) {
    const modeValue = getValueFromRecap(recapMode);
    const modeBtn = recapMode.querySelector('[data-field="transport.mode"]');
    if (modeBtn) {
      let textSpan = modeBtn.querySelector('.rc-editable-field-text');
      if (!textSpan) {
        textSpan = document.createElement('span');
        textSpan.className = 'rc-editable-field-text';
        modeBtn.insertBefore(textSpan, modeBtn.querySelector('.rc-edit-pill'));
      }
      textSpan.textContent = modeValue || '—';
    }
  }
  
  // Repeat for other fields...
  [{
    el: recapContainer,
    field: 'transport.containerType'
  }, {
    el: recapOrigin,
    field: 'transport.origin'
  }, {
    el: recapDestination,
    field: 'transport.destination'
  }, {
    el: recapCargo,
    field: 'cargo.type'
  }, {
    el: recapPacking,
    field: 'cargo.packing'
  }, {
    el: recapWeight,
    field: 'cargo.weight'
  }, {
    el: recapInsurance,
    field: 'cargo.insuranceValue'
  }, {
    el: recapSellerCountry,
    field: 'seller.country'
  }, {
    el: recapIncoterm,
    field: 'seller.incoterm'
  }].forEach(({el, field}) => {
    if (el) {
      const value = getValueFromRecap(el);
      const btn = el.querySelector(`[data-field="${field}"]`);
      if (btn) {
        let textSpan = btn.querySelector('.rc-editable-field-text');
        if (!textSpan) {
          textSpan = document.createElement('span');
          textSpan.className = 'rc-editable-field-text';
          btn.insertBefore(textSpan, btn.querySelector('.rc-edit-pill'));
        }
        textSpan.textContent = value || '—';
      }
    }
  });
}

/**
 * Re-render summary page from current RC_STATE
 */
function renderSummaryFromState() {
  // First, try to sync from input controller
  syncRCStateFromInputController();
  
  const snap = getSummarySnapshot();
  
  // Update recap rows
  updateRecapField('origin', snap.origin);
  updateRecapField('destination', snap.destination);
  updateRecapField('mode', snap.mode);
  updateRecapField('containerType', snap.containerType);
  updateRecapField('cargoType', snap.cargoType);
  updateRecapField('packing', snap.packing);
  updateRecapField('grossWeight', snap.grossWeight);
  updateRecapField('insuranceValue', snap.insuranceValue);
  updateRecapField('incoterm', snap.incoterm);
  updateRecapField('sellerCountry', snap.sellerCountry);
  
  // Update risk gauge
  if (RC_STATE.riskScore !== undefined) {
    updateRiskGauge(RC_STATE.riskScore);
  }
  
  // Update AI summary if function exists
  if (typeof window.updateAISummary === 'function') {
    window.updateAISummary(snap);
  }
  
  // Update benchmark cards if function exists
  if (typeof window.updateBenchmarks === 'function') {
    window.updateBenchmarks(snap);
  }
  
  // Trigger Summary v19 Ultra update if exists
  if (window.summaryV19Ultra && typeof window.summaryV19Ultra.loadFormData === 'function') {
    window.summaryV19Ultra.loadFormData();
    window.summaryV19Ultra.renderSmartRecap();
    
    // After recap renders, update editable buttons
    setTimeout(() => {
      updateEditableButtonsFromRecap();
    }, 100);
  } else {
    // If summary v19 ultra doesn't exist, still try to update buttons after a delay
    setTimeout(() => {
      updateEditableButtonsFromRecap();
    }, 500);
  }
}

/**
 * Update individual recap field display
 * @param {string} field - Field name
 * @param {string} value - New value
 */
function updateRecapField(field, value) {
  const elements = document.querySelectorAll(`[data-recap-field="${field}"]`);
  elements.forEach(el => {
    el.textContent = value || '—';
  });
  
  // Also update editable buttons
  const fieldKey = getFieldKeyFromRecap(field);
  if (fieldKey) {
    const buttons = document.querySelectorAll(`[data-field="${fieldKey}"]`);
    buttons.forEach(btn => {
      const span = btn.querySelector('.rc-editable-field-text');
      if (span) {
        span.textContent = value || '—';
      } else {
        // If no span, create one
        const textSpan = document.createElement('span');
        textSpan.className = 'rc-editable-field-text';
        textSpan.textContent = value || '—';
        btn.insertBefore(textSpan, btn.querySelector('.rc-edit-pill'));
      }
    });
  }
  
  // Update summary v19 recap rows (both the span and editable button)
  const recapValueEl = document.getElementById(`rc-recap-${field}`);
  if (recapValueEl) {
    // Update editable button text if exists
    const editableBtn = recapValueEl.querySelector('.rc-editable-field');
    if (editableBtn) {
      const textSpan = editableBtn.querySelector('.rc-editable-field-text');
      if (textSpan) {
        textSpan.textContent = value || '—';
      }
    } else {
      // Fallback: update text directly
      recapValueEl.textContent = value || '—';
    }
  }
}

/**
 * Map recap field to full field key
 * @param {string} recapField - Short field name
 * @returns {string|null} Full field key
 */
function getFieldKeyFromRecap(recapField) {
  const mapping = {
    'origin': 'transport.origin',
    'destination': 'transport.destination',
    'mode': 'transport.mode',
    'containerType': 'transport.containerType',
    'cargoType': 'cargo.type',
    'packing': 'cargo.packing',
    'grossWeight': 'cargo.weight',
    'insuranceValue': 'cargo.insuranceValue',
    'incoterm': 'seller.incoterm',
    'sellerCountry': 'seller.country'
  };
  return mapping[recapField] || null;
}

/**
 * Update risk gauge display
 * @param {number} score - Risk score (0-100)
 */
function updateRiskGauge(score) {
  const gaugeValue = document.querySelector('.rc-gauge-value, #rc-risk-meter-score');
  if (gaugeValue) {
    gaugeValue.textContent = Math.round(score);
  }
  
  const gaugeBar = document.querySelector('.rc-gauge-bar-fill');
  if (gaugeBar) {
    gaugeBar.style.width = `${score}%`;
  }
  
  // Update risk level text
  const levelText = document.querySelector('.rc-risk-level, #rc-risk-meter-level');
  if (levelText) {
    if (score < 30) levelText.textContent = 'Thấp';
    else if (score < 60) levelText.textContent = 'Trung bình';
    else levelText.textContent = 'Cao';
  }
}

// =====================================
// 5. EVENT LISTENERS
// =====================================
/**
 * Initialize editable field listeners
 */
function initEditableFields() {
  document.addEventListener('click', function(e) {
    const editableBtn = e.target.closest('.rc-editable-field');
    if (editableBtn) {
      const fieldKey = editableBtn.getAttribute('data-field');
      if (fieldKey) {
        e.stopPropagation();
        openFieldEditor(fieldKey);
      }
    }
    
    // Close modal on overlay click
    const overlay = e.target.closest('.rc-modal-overlay');
    if (overlay && e.target === overlay) {
      closeFieldEditor();
    }
  });
  
  // ESC to close modal
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeFieldEditor();
    }
  });
}

// =====================================
// 6. AI SUGGEST PLACEHOLDER
// =====================================
/**
 * Handle AI suggestion request
 * @param {string} fieldKey - Field to get suggestion for
 */
function handleAISuggest(fieldKey) {
  if (typeof window.RC_AI_SUGGEST === 'function') {
    window.RC_AI_SUGGEST(fieldKey, RC_STATE);
  } else {
    showNotification('Tính năng AI đang được phát triển', 'info');
  }
}

// Make function available globally for onclick
window.RC_AI_SUGGEST = function(fieldKey, state) {
  console.log('AI Suggest called for:', fieldKey, state);
  showNotification('Chức năng AI sẽ sớm ra mắt!', 'info');
};

// =====================================
// 7. UTILITY FUNCTIONS
// =====================================
/**
 * Show notification toast
 * @param {string} message - Message to display
 * @param {string} type - Notification type (success|error|info)
 */
function showNotification(message, type = 'success') {
  const notification = document.createElement('div');
  notification.className = `rc-notification rc-notification-${type}`;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  setTimeout(() => notification.classList.add('rc-notification-show'), 10);
  setTimeout(() => {
    notification.classList.remove('rc-notification-show');
    setTimeout(() => notification.remove(), 300);
  }, 2500);
}

// =====================================
// 8. INITIALIZATION
// =====================================
// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initEditableFields);
} else {
  initEditableFields();
}

// Auto-render summary on page load if on summary page
window.addEventListener('load', function() {
  // Wait a bit for summary to render first
  setTimeout(() => {
    if (window.location.hash === '#summary' || 
        document.querySelector('.rc-summary-page, #rc-section-summary')) {
      renderSummaryFromState();
    } else {
      // Even if not on summary page, sync RC_STATE from input controller
      syncRCStateFromInputController();
    }
  }, 1000);
  
  // Also listen for summary updates
  document.addEventListener('rc-summary-updated', () => {
    setTimeout(() => {
      syncRCStateFromInputController();
      updateEditableButtonsFromRecap();
    }, 100);
  });
});

// Export functions for global access
window.openFieldEditor = openFieldEditor;
window.closeFieldEditor = closeFieldEditor;
window.saveFieldChanges = saveFieldChanges;
window.handleAISuggest = handleAISuggest;
window.renderSummaryFromState = renderSummaryFromState;
window.getSummarySnapshot = getSummarySnapshot;
window.initEditableFields = initEditableFields;
window.syncRCStateFromInputController = syncRCStateFromInputController;
window.updateEditableButtonsFromRecap = updateEditableButtonsFromRecap;

