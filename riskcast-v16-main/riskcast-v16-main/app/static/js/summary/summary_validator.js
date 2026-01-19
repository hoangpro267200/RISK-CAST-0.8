/**
 * =====================================================
 * SUMMARY_VALIDATOR.JS – Real-time Validation Engine
 * RISKCAST FutureOS v100
 * =====================================================
 * 
 * Manages real-time validation using ExpertRules
 * Updates validation panel dynamically
 */

const Validator = (function() {
    'use strict';

    let validationPanel = null;
    let currentIssues = [];
    let validationEnabled = true;

    /**
     * Initialize validator
     */
    function init() {
        console.log('[Validator] Initializing validation engine...');
        validationPanel = document.getElementById('validationContent');
        
        if (!validationPanel) {
            console.error('[Validator] Validation panel not found');
            return false;
        }
        
        // Listen to state changes
        StateSync.addListener(onStateChange);
        
        return true;
    }

    /**
     * Handle state changes
     */
    function onStateChange(eventType, data, state) {
        if (!validationEnabled) return;
        
        // Run validation on state updates
        if (eventType === 'update' || eventType === 'batch-update' || eventType === 'load') {
            validateState(state);
        }
    }

    /**
     * Validate current state
     */
    function validateState(state) {
        if (!state) {
            state = StateSync.getState();
        }
        
        if (!state) {
            console.warn('[Validator] No state available for validation');
            return;
        }
        
        console.log('[Validator] Running validation...');
        
        // Run all expert rules
        currentIssues = ExpertRules.validateAll(state);
        
        // Update UI
        renderValidationPanel();
        updateStatusIndicator();
        
        console.log(`[Validator] Found ${currentIssues.length} issues`);
    }

    /**
     * Render validation panel
     */
    function renderValidationPanel() {
        if (!validationPanel) return;
        
        if (currentIssues.length === 0) {
            validationPanel.innerHTML = `
                <div class="validation-success">
                    <span class="success-icon">✅</span>
                    <h4>All Clear!</h4>
                    <p>No validation issues detected.</p>
                </div>
            `;
            return;
        }
        
        // Group issues by type
        const warnings = currentIssues.filter(issue => issue.type === 'warning');
        const suggestions = currentIssues.filter(issue => issue.type === 'suggestion');
        
        let html = '';
        
        // Render warnings
        if (warnings.length > 0) {
            html += '<div class="validation-section">';
            html += '<h4 class="validation-section-title">⚠️ Warnings</h4>';
            warnings.forEach(warning => {
                html += renderIssue(warning);
            });
            html += '</div>';
        }
        
        // Render suggestions
        if (suggestions.length > 0) {
            html += '<div class="validation-section">';
            html += '<h4 class="validation-section-title">💡 Suggestions</h4>';
            suggestions.forEach(suggestion => {
                html += renderIssue(suggestion);
            });
            html += '</div>';
        }
        
        validationPanel.innerHTML = html;
        
        // Attach event listeners for action buttons
        attachIssueListeners();
    }

    /**
     * Render individual issue
     */
    function renderIssue(issue) {
        const cssClass = issue.type === 'warning' ? 'warning-bubble' : 'suggestion-chip';
        
        let html = `
            <div class="${cssClass}" data-field="${issue.field}">
                <span class="${issue.type === 'warning' ? 'warning-icon' : 'suggestion-icon'}">
                    ${issue.icon}
                </span>
                <div class="${issue.type === 'warning' ? 'warning-content' : 'suggestion-content'}">
                    <div class="${issue.type === 'warning' ? 'warning-title' : 'suggestion-title'}">
                        ${issue.title}
                    </div>
                    <div class="${issue.type === 'warning' ? 'warning-message' : 'suggestion-message'}">
                        ${issue.message}
                    </div>
        `;
        
        // Add action buttons if suggested value exists
        if (issue.suggestedValue) {
            html += `
                <div class="issue-actions">
                    <button class="action-apply-btn" data-field="${issue.field}" data-value="${issue.suggestedValue}">
                        Apply Suggestion
                    </button>
                    <button class="action-dismiss-btn" data-field="${issue.field}">
                        Dismiss
                    </button>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
        
        return html;
    }

    /**
     * Attach event listeners to issue action buttons
     */
    function attachIssueListeners() {
        // Apply suggestion buttons
        document.querySelectorAll('.action-apply-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const field = this.getAttribute('data-field');
                const value = this.getAttribute('data-value');
                applySuggestion(field, value);
            });
        });
        
        // Dismiss buttons
        document.querySelectorAll('.action-dismiss-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const field = this.getAttribute('data-field');
                dismissIssue(field);
            });
        });
    }

    /**
     * Apply suggested value
     */
    function applySuggestion(field, value) {
        console.log(`[Validator] Applying suggestion: ${field} = ${value}`);
        
        // Parse field (format: "section.field")
        const [section, fieldName] = field.split('.');
        
        if (section && fieldName) {
            StateSync.updateField(section, fieldName, value);
            
            // Show success feedback
            showToast(`Applied: ${fieldName} = ${value}`, 'success');
            
            // Re-validate after short delay
            setTimeout(() => validateState(), 500);
        }
    }

    /**
     * Dismiss issue
     */
    function dismissIssue(field) {
        console.log(`[Validator] Dismissing issue for: ${field}`);
        
        // Remove issue from current list
        currentIssues = currentIssues.filter(issue => issue.field !== field);
        
        // Re-render
        renderValidationPanel();
        updateStatusIndicator();
        
        showToast('Issue dismissed', 'info');
    }

    /**
     * Update status indicator
     */
    function updateStatusIndicator() {
        const statusIndicator = document.getElementById('validationStatus');
        
        if (!statusIndicator) return;
        
        const warningCount = currentIssues.filter(i => i.type === 'warning').length;
        
        if (warningCount > 0) {
            statusIndicator.style.color = '#ff5588';
            statusIndicator.title = `${warningCount} warning(s)`;
        } else if (currentIssues.length > 0) {
            statusIndicator.style.color = '#ffaa00';
            statusIndicator.title = `${currentIssues.length} suggestion(s)`;
        } else {
            statusIndicator.style.color = '#00ff88';
            statusIndicator.title = 'All clear';
        }
    }

    /**
     * Show toast notification
     */
    function showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // Add to body
        document.body.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Get current issues
     */
    function getIssues() {
        return currentIssues;
    }

    /**
     * Get issues count
     */
    function getIssuesCount() {
        return {
            total: currentIssues.length,
            warnings: currentIssues.filter(i => i.type === 'warning').length,
            suggestions: currentIssues.filter(i => i.type === 'suggestion').length
        };
    }

    /**
     * Enable/disable validation
     */
    function setEnabled(enabled) {
        validationEnabled = enabled;
        console.log(`[Validator] Validation ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Check if validation passes (no high-severity warnings)
     */
    function canProceed() {
        const highSeverityIssues = currentIssues.filter(issue => 
            issue.type === 'warning' && issue.severity === 'high'
        );
        
        return highSeverityIssues.length === 0;
    }

    /**
     * Force validation run
     */
    function forceValidation() {
        const state = StateSync.getState();
        validateState(state);
    }

    // Public API
    return {
        init,
        validateState,
        getIssues,
        getIssuesCount,
        setEnabled,
        canProceed,
        forceValidation,
        applySuggestion,
        dismissIssue
    };

})();

// Make Validator available globally
window.Validator = Validator;

// Add toast CSS dynamically
const toastStyles = document.createElement('style');
toastStyles.textContent = `
.toast {
    position: fixed;
    bottom: 120px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    padding: 14px 24px;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(0, 255, 255, 0.3);
    border-radius: 12px;
    color: #ffffff;
    font-size: 14px;
    font-weight: 500;
    z-index: 10000;
    opacity: 0;
    transition: all 300ms ease-out;
    pointer-events: none;
}
.toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}
.toast-success {
    border-color: rgba(0, 255, 136, 0.5);
    box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
}
.toast-info {
    border-color: rgba(0, 255, 255, 0.5);
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
}
.validation-success {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: var(--space-xl);
    text-align: center;
}
.success-icon {
    font-size: 64px;
    margin-bottom: var(--space-md);
}
.validation-success h4 {
    font-size: 20px;
    color: #00ff88;
    margin-bottom: var(--space-sm);
}
.validation-success p {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
}
.validation-section {
    margin-bottom: var(--space-lg);
}
.validation-section-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: var(--space-sm);
    color: rgba(255, 255, 255, 0.8);
}
.issue-actions {
    display: flex;
    gap: var(--space-sm);
    margin-top: var(--space-sm);
}
.action-apply-btn,
.action-dismiss-btn {
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: all var(--transition-fast);
}
.action-apply-btn {
    background: linear-gradient(135deg, #00ffff 0%, #0088ff 100%);
    color: #000000;
}
.action-apply-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 255, 255, 0.4);
}
.action-dismiss-btn {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.2);
}
.action-dismiss-btn:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #ffffff;
}
`;
document.head.appendChild(toastStyles);

console.log('[Validator] Module loaded successfully');
