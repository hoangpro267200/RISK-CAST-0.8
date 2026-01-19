/* ==========================================================================
   SUMMARY_V400 - INLINE EDITOR
   Smart editor bubble with positioning and validation
   ========================================================================== */

const V400InlineEditor = (() => {
    let currentFieldKey = null;
    let currentElement = null;
    let currentState = null;
    let onSaveCallback = null;
    
    const bubble = document.getElementById('editorBubble');
    const labelEl = document.getElementById('editorLabel');
    const pathEl = document.getElementById('editorPath');
    const bodyEl = document.getElementById('editorBody');
    const statusEl = document.getElementById('editorStatus');
    const closeBtn = document.getElementById('editorClose');
    const cancelBtn = document.getElementById('editorCancel');
    const saveBtn = document.getElementById('editorSave');
    
    /**
     * Initialize editor
     */
    function init(onSave) {
        onSaveCallback = onSave;
        
        if (!bubble || !closeBtn || !cancelBtn || !saveBtn) {
            console.error('Editor elements not found');
            return;
        }
        
        // PORTAL MODE: Move bubble to body to escape stacking contexts
        if (bubble.parentElement !== document.body) {
            document.body.appendChild(bubble);
        }
        
        // Close button
        closeBtn.addEventListener('click', close);
        
        // Cancel button
        cancelBtn.addEventListener('click', close);
        
        // Save button
        saveBtn.addEventListener('click', handleSave);
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (bubble.classList.contains('editor-bubble--visible') &&
                !bubble.contains(e.target) &&
                !e.target.closest('.field-tile, .banner-tile, .mega-tile')) {
                close();
            }
        });
        
        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && bubble.classList.contains('editor-bubble--visible')) {
                close();
            }
        });
        
        // Re-position on scroll/resize when editor is open
        let scrollHandler = null;
        let resizeHandler = null;
        
        scrollHandler = () => {
            if (bubble.classList.contains('editor-bubble--visible') && currentElement) {
                positionBubble(currentElement);
            }
        };
        
        resizeHandler = () => {
            if (bubble.classList.contains('editor-bubble--visible') && currentElement) {
                positionBubble(currentElement);
            }
        };
        
        window.addEventListener('scroll', scrollHandler, true); // Use capture phase
        window.addEventListener('resize', resizeHandler);
    }
    
    /**
     * Open editor for a field
     */
    function open(fieldKey, element, state) {
        currentFieldKey = fieldKey;
        currentElement = element;
        currentState = V400State.deepClone(state);
        
        const fieldConfig = V400Renderer.FIELD_MAP[fieldKey];
        if (!fieldConfig) {
            console.error('Unknown field:', fieldKey);
            return;
        }
        
        // Update header
        labelEl.textContent = fieldConfig.label;
        pathEl.textContent = getSectionLabel(fieldConfig.section);
        
        // Render input
        renderInput(fieldConfig, state);
        
        // Clear status
        statusEl.innerHTML = '';
        statusEl.className = 'editor-bubble__status';
        
        // Position bubble BEFORE showing (to get accurate measurements)
        positionBubble(element);
        
        // Show bubble
        bubble.classList.add('editor-bubble--visible');
        
        // Re-position after showing (in case bubble size changed)
        setTimeout(() => {
            positionBubble(element);
        }, 10);
        
        // Focus first input
        setTimeout(() => {
            const firstInput = bodyEl.querySelector('input, select, textarea');
            if (firstInput) firstInput.focus();
        }, 50);
    }
    
    /**
     * Close editor
     */
    function close() {
        if (bubble) {
            bubble.classList.remove('editor-bubble--visible');
            bubble.classList.remove('editor-bubble--error');
            // Clear inline positioning styles
            bubble.style.top = '';
            bubble.style.left = '';
        }
        currentFieldKey = null;
        currentElement = null;
        currentState = null;
    }
    
    /**
     * Render input based on field type
     */
    function renderInput(fieldConfig, state) {
        const value = V400State.getValueAtPath(state, fieldConfig.path);
        
        let html = '';
        
        switch (fieldConfig.type) {
            case 'select':
                html = `
                    <div class="editor-field-group">
                        <label class="editor-field-label">${fieldConfig.label}</label>
                        <select class="editor-select" id="editorInput">
                            ${fieldConfig.options.map(opt => `
                                <option value="${opt}" ${value === opt ? 'selected' : ''}>
                                    ${opt || '(Not set)'}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                `;
                break;
                
            case 'checkbox':
                html = `
                    <div class="editor-checkbox-group">
                        <input type="checkbox" class="editor-checkbox" id="editorInput" 
                               ${value ? 'checked' : ''}>
                        <label class="editor-checkbox-label" for="editorInput">
                            ${fieldConfig.label}
                        </label>
                    </div>
                `;
                break;
                
            case 'textarea':
                html = `
                    <div class="editor-field-group">
                        <label class="editor-field-label">${fieldConfig.label}</label>
                        <textarea class="editor-textarea" id="editorInput" 
                                  placeholder="${fieldConfig.placeholder || ''}">${value || ''}</textarea>
                    </div>
                `;
                break;
                
            case 'date':
                html = `
                    <div class="editor-field-group">
                        <label class="editor-field-label">${fieldConfig.label}</label>
                        <input type="date" class="editor-date-input" id="editorInput" 
                               value="${value || ''}"
                               ${fieldConfig.disabled ? 'disabled' : ''}>
                    </div>
                `;
                break;
                
            case 'number':
                html = `
                    <div class="editor-field-group">
                        <label class="editor-field-label">${fieldConfig.label}</label>
                        <input type="number" class="editor-input" id="editorInput" 
                               value="${value || ''}" 
                               placeholder="${fieldConfig.placeholder || ''}"
                               step="${fieldConfig.step || '1'}">
                    </div>
                `;
                break;
                
            default: // text, email, tel
                html = `
                    <div class="editor-field-group">
                        <label class="editor-field-label">${fieldConfig.label}</label>
                        <input type="${fieldConfig.type || 'text'}" class="editor-input" id="editorInput" 
                               value="${value || ''}" 
                               placeholder="${fieldConfig.placeholder || ''}">
                    </div>
                `;
        }
        
        // Add suggestions if available
        html += renderSuggestions(fieldConfig);
        
        bodyEl.innerHTML = html;
        
        // Add Enter key handler
        const input = document.getElementById('editorInput');
        if (input && input.type !== 'textarea') {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSave();
                }
            });
        }
    }
    
    /**
     * Render suggestion chips
     */
    function renderSuggestions(fieldConfig) {
        const suggestions = getSuggestionsForField(fieldConfig);
        
        if (suggestions.length === 0) return '';
        
        return `
            <div class="editor-suggestions">
                ${suggestions.map(s => `
                    <button class="editor-suggestion-chip" type="button" 
                            onclick="document.getElementById('editorInput').value = '${s}'; document.getElementById('editorInput').focus();">
                        ${s}
                    </button>
                `).join('')}
            </div>
        `;
    }
    
    /**
     * Get suggestions for field
     */
    function getSuggestionsForField(fieldConfig) {
        const suggestions = {
            'trade.pol': ['CNSHA', 'CNYTN', 'USNYC', 'USLAX', 'DEHAM', 'NLRTM'],
            'trade.pod': ['DEHAM', 'NLRTM', 'USNYC', 'USLAX', 'GBSOU', 'FRLEH'],
            'trade.carrier': ['Maersk', 'MSC', 'CMA CGM', 'COSCO', 'Hapag-Lloyd', 'ONE'],
            'cargo.cargo_category': ['General Cargo', 'Electronics', 'Textiles'],
            'seller.country': ['CN', 'US', 'DE', 'GB', 'FR', 'JP'],
            'buyer.country': ['US', 'DE', 'GB', 'FR', 'NL', 'IT']
        };
        
        return suggestions[currentFieldKey] || [];
    }
    
    /**
     * Handle save
     */
    function handleSave() {
        const fieldConfig = V400Renderer.FIELD_MAP[currentFieldKey];
        const input = document.getElementById('editorInput');
        
        if (!input || !fieldConfig) return;
        
        let newValue;
        
        if (fieldConfig.type === 'checkbox') {
            newValue = input.checked;
        } else if (fieldConfig.type === 'number') {
            newValue = input.value ? parseFloat(input.value) : null;
        } else {
            newValue = input.value.trim();
        }
        
        // Validate
        const validation = validateValue(fieldConfig, newValue);
        
        if (!validation.valid) {
            showError(validation.message);
            return;
        }
        
        // Update state
        V400State.setValueAtPath(currentState, fieldConfig.path, newValue);
        
        // Save and close
        if (onSaveCallback) {
            onSaveCallback(currentState);
        }
        
        close();
    }
    
    /**
     * Validate value
     */
    function validateValue(fieldConfig, value) {
        // Basic validation
        if (fieldConfig.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                return { valid: false, message: 'Invalid email format' };
            }
        }
        
        if (fieldConfig.type === 'number' && value !== null) {
            if (isNaN(value) || value < 0) {
                return { valid: false, message: 'Must be a positive number' };
            }
        }
        
        return { valid: true };
    }
    
    /**
     * Show error message
     */
    function showError(message) {
        statusEl.innerHTML = `
            <span class="editor-bubble__status-icon">⚠️</span>
            <span>${message}</span>
        `;
        statusEl.className = 'editor-bubble__status editor-bubble__status--error';
        
        bubble.classList.add('editor-bubble--error');
        
        setTimeout(() => {
            bubble.classList.remove('editor-bubble--error');
        }, 600);
    }
    
    /**
     * Position bubble near element using fixed positioning and CSS variables
     */
    function positionBubble(element) {
        if (!element || !bubble) return;
        
        const rect = element.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Calculate center X of the field
        const centerX = rect.left + (rect.width / 2);
        
        // Try bottom position first (default)
        let top = rect.bottom + 12;
        let position = 'bottom';
        
        // Check if bubble would overflow bottom
        const estimatedBubbleHeight = 300; // Approximate height
        if (top + estimatedBubbleHeight > viewportHeight - 20) {
            // Try top position
            if (rect.top - estimatedBubbleHeight > 20) {
                top = rect.top - estimatedBubbleHeight - 12;
                position = 'top';
            } else {
                // Center vertically if both positions overflow
                top = Math.max(20, (viewportHeight - estimatedBubbleHeight) / 2);
                position = 'bottom';
            }
        }
        
        // Calculate left position (center align with field, but constrain to viewport)
        let left = centerX;
        const bubbleWidth = 420; // Fixed width from CSS
        const maxWidth = Math.min(480, viewportWidth - 40); // Max width constraint
        
        // Adjust if overflowing right
        if (left + (bubbleWidth / 2) > viewportWidth - 20) {
            left = viewportWidth - (bubbleWidth / 2) - 20;
        }
        // Adjust if overflowing left
        if (left - (bubbleWidth / 2) < 20) {
            left = (bubbleWidth / 2) + 20;
        }
        
        // Set CSS variables for fixed positioning
        document.documentElement.style.setProperty('--editor-x', `${left}px`);
        document.documentElement.style.setProperty('--editor-y', `${top}px`);
        
        // Set position attribute for arrow styling
        bubble.setAttribute('data-position', position);
    }
    
    /**
     * Get section label
     */
    function getSectionLabel(section) {
        const labels = {
            trade: '01 • Trade & Route',
            cargo: '02 • Cargo & Packing',
            seller: '03 • Seller Details',
            buyer: '04 • Buyer Details'
        };
        return labels[section] || section;
    }
    
    // Public API
    return {
        init,
        open,
        close
    };
})();

