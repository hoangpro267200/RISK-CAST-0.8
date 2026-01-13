
(function() {
    'use strict';

    const formSections = [
        {
            id: 'shipping-info',
            selector: '#shipping-info',
            fields: ['route', 'transport_mode', 'pol', 'pod', 'distance', 'transit_time', 'carrier', 'cargo_type', 'container', 'incoterm', 'packaging', 'priority'],
            name: 'Shipping Information'
        },
        {
            id: 'cargo-details',
            selector: '#cargo-details',
            fields: ['packages', 'cargo_value', 'etd', 'eta'],
            name: 'Cargo Details'
        },
        {
            id: 'seller-info',
            selector: '#seller-info',
            fields: ['seller_name', 'seller_country', 'seller_email'],
            name: 'Seller Information'
        },
        {
            id: 'buyer-info',
            selector: '#buyer-info',
            fields: ['buyer_name', 'buyer_country', 'buyer_email'],
            name: 'Buyer Information'
        }
    ];

    let confettiInterval = null;

    /**
     * Initialize premium tracker
     */
    function initPremiumTracker() {
        createProgressBar();
        setupSectionTracking();
        setupFieldListeners();
        updateAllProgress();
        
        // Check initial state
        setTimeout(() => {
            checkCompletion();
        }, 500);
    }

    /**
     * Create top progress bar
     * DISABLED: Using smart progress bar in header instead
     */
    function createProgressBar() {
        // Progress bar removed - using smart progress bar in header
        return;
    }

    /**
     * Setup section tracking
     */
    function setupSectionTracking() {
        formSections.forEach(section => {
            const sectionEl = document.querySelector(section.selector);
            if (sectionEl) {
                createSectionProgressRing(sectionEl, section);
                updateSectionProgress(section);
            }
        });
    }

    /**
     * Create progress ring for section
     */
    function createSectionProgressRing(sectionEl, section) {
        const header = sectionEl.querySelector('.section-header');
        if (!header) return;

        const progressRing = document.createElement('div');
        progressRing.className = 'section-progress-ring';
        progressRing.innerHTML = `
            <svg class="section-progress-svg" viewBox="0 0 48 48">
                <defs>
                    <linearGradient id="emeraldGradient${section.id}" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#10B981;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#34D399;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <circle class="section-progress-circle-bg" cx="24" cy="24" r="20"/>
                <circle class="section-progress-circle" cx="24" cy="24" r="20" 
                        stroke-dasharray="125.6" 
                        stroke-dashoffset="125.6"
                        data-section="${section.id}"/>
            </svg>
            <div class="section-progress-text" data-section-text="${section.id}">0/0</div>
        `;

        header.style.position = 'relative';
        header.appendChild(progressRing);
    }

    /**
     * Setup field listeners
     */
    function setupFieldListeners() {
        // Listen to all form inputs
        document.addEventListener('input', handleFieldChange);
        document.addEventListener('change', handleFieldChange);
        
        // Listen to custom dropdowns
        document.addEventListener('click', function(e) {
            if (e.target.closest('.dropdown-option')) {
                setTimeout(handleFieldChange, 100);
            }
        });
    }

    /**
     * Handle field change
     */
    function handleFieldChange() {
        updateAllProgress();
        checkCompletion();
    }

    /**
     * Update all progress
     */
    function updateAllProgress() {
        let totalFilled = 0;
        let totalFields = 0;

        formSections.forEach(section => {
            const progress = updateSectionProgress(section);
            totalFilled += progress.filled;
            totalFields += progress.total;
        });

        // Update top progress bar
        const percentage = totalFields > 0 ? Math.round((totalFilled / totalFields) * 100) : 0;
        updateTopProgress(percentage);

        // Update section classes
        formSections.forEach(section => {
            const sectionEl = document.querySelector(section.selector);
            if (sectionEl) {
                const progress = getSectionProgress(section);
                if (progress.filled === progress.total && progress.total > 0) {
                    sectionEl.classList.remove('incomplete');
                    sectionEl.classList.add('complete');
                } else {
                    sectionEl.classList.remove('complete');
                    sectionEl.classList.add('incomplete');
                }
            }
        });
    }

    /**
     * Update section progress
     */
    function updateSectionProgress(section) {
        const progress = getSectionProgress(section);
        const sectionEl = document.querySelector(section.selector);
        
        if (!sectionEl) return progress;

        // Update progress ring
        const progressCircle = sectionEl.querySelector(`[data-section="${section.id}"]`);
        const progressText = sectionEl.querySelector(`[data-section-text="${section.id}"]`);
        
        if (progressCircle && progressText) {
            const circumference = 2 * Math.PI * 20; // radius = 20
            const offset = circumference - (progress.percentage / 100) * circumference;
            progressCircle.style.strokeDashoffset = offset;
            progressText.textContent = `${progress.filled}/${progress.total}`;
        }

        return progress;
    }

    /**
     * Get section progress
     */
    function getSectionProgress(section) {
        let filled = 0;
        let total = 0;

        section.fields.forEach(fieldName => {
            total++;
            const field = getFieldElement(fieldName);
            if (field && isFieldFilled(field, fieldName)) {
                filled++;
            }
        });

        return {
            filled,
            total,
            percentage: total > 0 ? (filled / total) * 100 : 0
        };
    }

    /**
     * Get field element
     */
    function getFieldElement(fieldName) {
        // Try different selectors
        const selectors = [
            `#${fieldName}`,
            `#${fieldName}_input`,
            `#${fieldName}_dropdown`,
            `[name="${fieldName}"]`,
            `[id*="${fieldName}"]`
        ];

        for (const selector of selectors) {
            const el = document.querySelector(selector);
            if (el) return el;
        }

        return null;
    }

    /**
     * Check if field is filled
     */
    function isFieldFilled(field, fieldName) {
        if (!field) return false;

        // Input fields
        if (field.tagName === 'INPUT') {
            if (field.type === 'checkbox') {
                return field.checked;
            }
            return field.value && field.value.trim() !== '';
        }

        // Select fields
        if (field.tagName === 'SELECT') {
            return field.value && field.value !== '';
        }

        // Custom dropdowns
        if (field.classList.contains('custom-dropdown')) {
            const value = field.querySelector('.dropdown-value');
            return value && !value.classList.contains('placeholder') && value.textContent.trim() !== '';
        }

        // Hidden inputs (for dropdowns)
        const hiddenInput = document.getElementById(`${fieldName}_input`);
        if (hiddenInput) {
            return hiddenInput.value && hiddenInput.value.trim() !== '';
        }

        return false;
    }

    /**
     * Update top progress bar
     * DISABLED: Using smart progress bar in header instead
     */
    function updateTopProgress(percentage) {
        // Progress bar removed - using smart progress bar in header
        return;
    }

    /**
     * Check if form is 100% complete
     */
    function checkCompletion() {
        let totalFilled = 0;
        let totalFields = 0;

        formSections.forEach(section => {
            const progress = getSectionProgress(section);
            totalFilled += progress.filled;
            totalFields += progress.total;
        });

        const percentage = totalFields > 0 ? Math.round((totalFilled / totalFields) * 100) : 0;

        if (percentage === 100 && totalFields > 0) {
            triggerCompletion();
        }
    }

    /**
     * Trigger completion animation
     */
    function triggerCompletion() {
        // Show completion badge
        showCompletionBadge();
        
        // Trigger confetti
        startConfetti();
        
        // Highlight submit button
        highlightSubmitButton();
        
        // Auto-scroll to button - DISABLED: User complained it's annoying
        // Users prefer to stay at their current position when notification appears
        // setTimeout(() => {
        //     const submitBtn = document.getElementById('run_risk') || document.querySelector('.btn-primary');
        //     if (submitBtn) {
        //         submitBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
        //     }
        // }, 2000);
    }

    /**
     * Show completion badge
     */
    function showCompletionBadge() {
        if (document.querySelector('.completion-badge')) return;

        const badge = document.createElement('div');
        badge.className = 'completion-badge';
        badge.innerHTML = `
            <h3>🎉 Sẵn Sàng Chạy RISKCAST Engine</h3>
            <p>Form đã hoàn thành 100%</p>
        `;

        document.body.appendChild(badge);

        // Remove after 3 seconds
        setTimeout(() => {
            badge.style.animation = 'badge-popup 0.4s reverse forwards';
            setTimeout(() => badge.remove(), 400);
        }, 3000);
    }

    /**
     * Start confetti animation
     */
    function startConfetti() {
        if (confettiInterval) return;

        const container = document.createElement('div');
        container.className = 'confetti-container';
        document.body.appendChild(container);

        const colors = ['#10B981', '#34D399', '#059669'];
        
        confettiInterval = setInterval(() => {
            for (let i = 0; i < 20; i++) {
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + '%';
                confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';
                confetti.style.animationDelay = Math.random() * 0.5 + 's';
                container.appendChild(confetti);

                setTimeout(() => confetti.remove(), 5000);
            }
        }, 200);

        // Stop after 5 seconds
        setTimeout(() => {
            clearInterval(confettiInterval);
            confettiInterval = null;
            setTimeout(() => container.remove(), 5000);
        }, 5000);
    }

    /**
     * Highlight submit button
     */
    function highlightSubmitButton() {
        const submitBtn = document.getElementById('run_risk') || document.querySelector('.btn-primary');
        if (submitBtn) {
            submitBtn.classList.add('ready');
        }
    }

    /**
     * Add AI Recommended tags to auto-filled fields
     */
    function addAIRecommendedTags() {
        // This will be called when fields are auto-filled
        // Implementation depends on your auto-fill logic
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPremiumTracker);
    } else {
        initPremiumTracker();
    }

    // Export for external use
    window.PremiumInputTracker = {
        updateProgress: updateAllProgress,
        checkCompletion: checkCompletion
    };

})();

