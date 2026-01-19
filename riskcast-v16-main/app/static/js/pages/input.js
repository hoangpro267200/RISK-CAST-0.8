// ==================== INPUT FORM HANDLER ====================

function handleSubmit(e) {
    e.preventDefault();
    e.stopPropagation();

    console.log("✓ FORM SUBMITTED — calling runAnalysis()");

    if (typeof window.runAnalysis === "function") {
        window.runAnalysis();
    } else {
        console.error("✗ ERROR: runAnalysis() missing");
        alert("Không tìm thấy hàm runAnalysis.");
    }
}

function attachFormSubmitHandler() {
    const form = document.getElementById("risk_form");

    if (!form) {
        console.error("✗ Form #risk_form NOT FOUND");
        return false;
    }

    // Remove existing listener if any
    form.removeEventListener("submit", handleSubmit);
    // Add new listener
    form.addEventListener("submit", handleSubmit);

    console.log("✓ Handler attached to #risk_form");
    return true;
}

// Attach after DOM ready with retry mechanism
function initializeFormHandler() {
    if (attachFormSubmitHandler()) {
        console.log("✓ Form handler initialized successfully");
    } else {
        // Retry after a short delay if form not found yet
        console.log("⚠ Form not found, retrying...");
        setTimeout(() => {
            if (attachFormSubmitHandler()) {
                console.log("✓ Form handler initialized on retry");
            } else {
                console.error("✗ Failed to initialize form handler after retry");
            }
        }, 200);
    }
}

// Attach after DOM ready
if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", initializeFormHandler);
} else {
    // DOM already loaded
    initializeFormHandler();
}

// Export globally
window.handleSubmit = handleSubmit;
window.attachFormSubmitHandler = attachFormSubmitHandler;

// ==================== PERFORMANCE OPTIMIZATION ENGINE ====================
(function() {
    'use strict';

    // ==================== TYPING MODE ENGINE ====================
    let typingTimeout = null;
    const TYPING_DELAY = 150;

    function enableTypingMode() {
        const body = document.body;
        if (!body.classList.contains('typing')) {
            body.classList.add('typing');
        }
        
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }
        
        typingTimeout = setTimeout(() => {
            body.classList.remove('typing');
            typingTimeout = null;
        }, TYPING_DELAY);
    }

    function initTypingMode() {
        const inputs = document.querySelectorAll('input[type="text"], input[type="number"], input[type="email"], input[type="tel"], textarea, .form-input');
        
        inputs.forEach(input => {
            input.removeEventListener('input', enableTypingMode);
            input.removeEventListener('keydown', enableTypingMode);
            input.addEventListener('input', enableTypingMode, { passive: true });
            input.addEventListener('keydown', enableTypingMode, { passive: true });
        });
    }

    // ==================== VALIDATION ENGINE ====================
    function validateInput(input) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;

        const value = input.value.trim();
        const isValid = value !== '' && input.checkValidity();

        formGroup.classList.remove('validated', 'error');

        if (isValid) {
            formGroup.classList.add('validated');
        } else if (value !== '' && !input.checkValidity()) {
            formGroup.classList.add('error');
        }
    }

    function initValidationEngine() {
        const inputs = document.querySelectorAll('.form-input, input[type="text"], input[type="number"], input[type="email"], input[type="tel"], textarea');
        
        inputs.forEach(input => {
            validateInput(input);
            
            let validationTimeout;
            const debouncedValidate = () => {
                clearTimeout(validationTimeout);
                validationTimeout = setTimeout(() => validateInput(input), 100);
            };
            
            input.addEventListener('input', debouncedValidate, { passive: true });
            input.addEventListener('blur', () => validateInput(input), { passive: true });
            input.addEventListener('change', () => validateInput(input), { passive: true });
        });
    }

    // ==================== AI PANEL COLLAPSE OPTIMIZER ====================
    function optimizeAIPanelCollapse() {
        const aiPanel = document.getElementById('aiSmartPanel');
        const mainContent = document.querySelector('.main-content');
        
        if (!aiPanel || !mainContent) return;

        const resizeObserver = new ResizeObserver(() => {
            requestAnimationFrame(() => {
                mainContent.style.willChange = 'flex';
            });
        });

        resizeObserver.observe(aiPanel);
    }

    // ==================== INITIALIZATION ====================
    function initPerformanceEngine() {
        initTypingMode();
        initValidationEngine();
        optimizeAIPanelCollapse();

        const observer = new MutationObserver(mutations => {
            let shouldReinit = false;
            mutations.forEach(mutation => {
                if (mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1 && (node.matches('input, textarea') || node.querySelector('input, textarea'))) {
                            shouldReinit = true;
                        }
                    });
                }
            });
            
            if (shouldReinit) {
                initTypingMode();
                initValidationEngine();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPerformanceEngine);
    } else {
        initPerformanceEngine();
    }

    setTimeout(initPerformanceEngine, 500);

    window.enableTypingMode = enableTypingMode;
    window.validateInput = validateInput;
})();
