# RISKCAST v12 Performance Optimization Patches

## BLOCK 1 — OPTIMIZED input.css KEY CHANGES

### Critical Performance Fixes to Apply:

```css
/* ==================== TYPING MODE - DISABLE ANIMATIONS ==================== */
body.typing * {
    transition: none !important;
    animation: none !important;
}

body.typing .form-input,
body.typing .dropdown-trigger {
    transition: none !important;
}

/* ==================== OPTIMIZED TRANSITIONS (NO 'all') ==================== */
/* Replace ALL instances of transition: all with specific properties */

/* Navigation */
.nav-link {
    transition: color 0.2s ease;
}

.nav-link-cta {
    transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

/* Buttons */
.btn-primary {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    will-change: transform;
    transform: translateZ(0);
}

.btn-secondary {
    transition: background 0.2s ease, border-color 0.2s ease;
}

/* Cards */
.value-card {
    transition: border-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;
    will-change: transform;
    transform: translateZ(0);
}

.feature-card {
    transition: border-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;
    will-change: transform;
    transform: translateZ(0);
}

.customer-card {
    transition: border-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;
    will-change: transform;
    transform: translateZ(0);
}

/* ==================== REDUCED BLUR VALUES ==================== */
/* Change all blur(12px-20px) to blur(4px-6px) */

.nav-container {
    backdrop-filter: blur(4px); /* was blur(6px) - keep */
}

.visual-glow {
    filter: blur(20px); /* was blur(40px) */
}

.visual-card {
    backdrop-filter: blur(4px); /* was blur(6px) */
}

.tooltip-content {
    backdrop-filter: blur(4px); /* was blur(6px) */
}

.notification {
    backdrop-filter: blur(4px); /* was blur(6px) */
}

.keyboard-hint {
    backdrop-filter: blur(4px); /* was blur(6px) */
}

/* Form inputs - already optimized at blur(6px), keep */

/* ==================== LIGHTER BOX-SHADOWS ==================== */
/* Replace multiple nested shadows with single optimized shadow */

/* Before: box-shadow: 0 0 12px rgba(0, 255, 195, 0.6), 0 0 30px rgba(0, 255, 195, 0.3); */
/* After: Single shadow with combined effect */

.nav-link-cta:hover {
    box-shadow: 0 0 10px rgba(0, 255, 195, 0.35); /* Combined effect */
}

.btn-primary {
    box-shadow: 0 3px 12px rgba(0, 255, 195, 0.2); /* Lighter */
}

.btn-primary:hover {
    box-shadow: 0 4px 16px rgba(0, 255, 195, 0.3); /* Lighter */
}

.value-card:hover {
    box-shadow: 0 8px 24px rgba(0, 255, 195, 0.1); /* Reduced from 36px */
}

.feature-card:hover {
    box-shadow: 0 6px 20px rgba(0, 255, 195, 0.08); /* Reduced from 32px */
}

.customer-card:hover {
    box-shadow: 0 8px 24px rgba(0, 255, 195, 0.1); /* Reduced from 36px */
}

/* Slider thumb - optimized */
.range-slider::-webkit-slider-thumb {
    box-shadow: 0 0 6px rgba(0, 255, 136, 0.5); /* Reduced from 12px */
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.range-slider::-webkit-slider-thumb:hover {
    box-shadow: 0 0 10px rgba(0, 255, 136, 0.65); /* Reduced from 20px */
}

/* Form input focus - optimized */
.form-input:focus,
.dropdown-trigger:focus {
    box-shadow: 
        0 0 0 2px rgba(0, 255, 136, 0.15),
        0 2px 8px rgba(0, 255, 136, 0.1); /* Reduced from 12px */
}

/* ==================== GPU-FRIENDLY TRANSFORMS ==================== */
/* All transforms use translateZ(0) for GPU acceleration */

.value-card,
.feature-card,
.customer-card,
.btn-primary,
.preset-btn {
    will-change: transform;
    transform: translateZ(0);
}

/* ==================== VALIDATION - JS-BASED (NO :has()) ==================== */
/* Already using .validated class - keep existing */

.form-group.validated .form-input {
    border-color: rgba(16, 185, 129, 0.5) !important;
    background: rgba(16, 185, 129, 0.05) !important;
}

.form-group.validated::after {
    content: '✓';
    position: absolute;
    right: 12px;
    top: 38px;
    color: #10b981;
    font-size: 16px;
    font-weight: 700;
    opacity: 0;
    animation: checkmarkFadeIn 0.3s ease forwards;
    pointer-events: none;
}

/* ==================== AI PANEL COLLAPSE OPTIMIZATION ==================== */
/* Already in riskcast_v12_layout.css - ensure smooth transitions */

.layout-wrapper {
    transition: gap 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.main-content {
    transition: flex 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    will-change: flex;
}

#aiSmartPanel {
    transition: 
        width 0.4s cubic-bezier(0.16, 1, 0.3, 1),
        opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1),
        transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    will-change: width, opacity, transform;
}

/* ==================== PERFORMANCE PRESETS ==================== */
/* Disable expensive operations during typing */

body.typing .value-card:hover,
body.typing .feature-card:hover,
body.typing .customer-card:hover {
    transform: none;
    box-shadow: none;
}

body.typing .range-slider::-webkit-slider-thumb:hover {
    transform: scale(1);
    box-shadow: 0 0 6px rgba(0, 255, 136, 0.5);
}

/* ==================== RESPONSIVE OPTIMIZATIONS ==================== */
@media (prefers-reduced-motion: reduce) {
    * {
        transition: none !important;
        animation: none !important;
    }
}

/* ==================== CONTENT EXPANSION SMOOTH ==================== */
.content-expand-wrapper {
    transition: flex 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    will-change: flex;
    flex: 1;
    min-width: 0;
}
```



























