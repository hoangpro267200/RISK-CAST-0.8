/**
 * ========================================================================
 * RISKCAST v20 - Entry Point
 * ========================================================================
 * Main entry point for RISKCAST v20 modular architecture
 */

// Import sanitize helpers
import { sanitizeGlobalState } from './utils/SanitizeHelpers.js';
import { RiskcastInputController } from './core/RiskcastInputController.js';

document.addEventListener('DOMContentLoaded', () => {
    if (window.__RC_V20_INITIALIZED__) {
        console.warn('⚠️ RISKCAST v20.3 already initialized');
        return;
    }
    
    window.__RC_V20_INITIALIZED__ = true;
    
    console.log('🚀 RISKCAST v20.3 — Initializing...');
    
    // Sanitize existing state
    sanitizeGlobalState();
    
    // Initialize controller
    window.RC_V20 = new RiskcastInputController();
    window.RC_V20.init();
    
    // Expose state globally
    window.RC_STATE = window.RC_V20.stateManager.getState();
    
    console.log('✅ RISKCAST v20.3 — Ready! All features loaded.');
});

