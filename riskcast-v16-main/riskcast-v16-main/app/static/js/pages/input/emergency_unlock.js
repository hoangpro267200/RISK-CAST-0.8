
import { qsa, remove } from '../../core/dom.js';

function forceUnlockInputs() {
    console.log('🔓 Emergency unlock: Starting...');
    
    // 1. Enable inputs
    document.querySelectorAll('input, select, textarea, button, .dropdown-trigger, .dropdown-option').forEach(el => {
        el.disabled = false;
        el.readOnly = false;
        el.removeAttribute('disabled');
        el.removeAttribute('readonly');
        el.style.setProperty('pointer-events', 'auto', 'important');
        el.style.setProperty('opacity', '1', 'important');
        el.style.setProperty('z-index', '10000', 'important');
        el.style.setProperty('cursor', el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' ? 'text' : 'pointer', 'important');
        
        // Force visible borders
        if (el.classList.contains('form-input') || el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') {
            el.style.setProperty('border', '1px solid rgba(255, 255, 255, 0.2)', 'important');
            el.style.setProperty('background', 'rgba(20, 24, 32, 1)', 'important');
        }
    });
    
    // 2. Enable scrolling
    document.body.style.setProperty('overflow', 'auto', 'important');
    document.body.style.setProperty('overflow-y', 'auto', 'important');
    document.documentElement.style.setProperty('overflow', 'auto', 'important');
    document.documentElement.style.setProperty('overflow-y', 'auto', 'important');
    document.documentElement.style.setProperty('height', 'auto', 'important');
    document.body.style.setProperty('height', 'auto', 'important');
    document.body.style.setProperty('position', 'relative', 'important');
    document.body.style.setProperty('top', '', 'important');
    document.body.style.setProperty('left', '', 'important');
    
    // 3. Hide overlays (using the selector pattern from user's code)
    document.querySelectorAll('[id*="overlay"], [class*="backdrop"], .loading-overlay, #loadingOverlay, .modal-backdrop, [class*="overlay"]').forEach(el => {
        if (!el.classList.contains('active')) {
            el.style.setProperty('display', 'none', 'important');
            el.style.setProperty('pointer-events', 'none', 'important');
            el.style.setProperty('opacity', '0', 'important');
            el.style.setProperty('z-index', '-9999', 'important');
        }
    });
    
    // Remove any fixed positioning that blocks scroll
    qsa('body > *').forEach(el => {
        if (el.style.position === 'fixed' && el.id !== 'sticky-progress-bar') {
            el.style.setProperty('position', 'relative', 'important');
        }
    });
    
    // Force enable all dropdowns
    qsa('.custom-dropdown, .dropdown-menu').forEach(dd => {
        dd.style.setProperty('pointer-events', 'auto', 'important');
        dd.style.setProperty('opacity', '1', 'important');
        dd.style.setProperty('z-index', '10001', 'important');
        const trigger = dd.querySelector('.dropdown-trigger');
        if (trigger) {
            trigger.style.setProperty('pointer-events', 'auto', 'important');
            trigger.style.setProperty('cursor', 'pointer', 'important');
        }
    });
    
    // Remove any blocking elements
    qsa('[style*="pointer-events: none"]').forEach(el => {
        if (!el.classList.contains('ph') && !el.classList.contains('icon')) {
            el.style.setProperty('pointer-events', 'auto', 'important');
        }
    });
    
    console.log('✅ Emergency unlock: Form unlocked!');
}

// Export function for console access
window.forceUnlockForm = forceUnlockInputs;

export function initEmergencyUnlock() {
    // Run immediately - don't wait for anything
    forceUnlockInputs();

    // Also run on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', forceUnlockInputs);
    } else {
        forceUnlockInputs();
    }

    // Run on window load
    window.addEventListener('load', forceUnlockInputs);

    // Re-run every 200ms for first 5 seconds (in case other scripts lock it again)
    let unlockCount = 0;
    const unlockInterval = setInterval(() => {
        if (unlockCount++ >= 25) {
            clearInterval(unlockInterval);
            return;
        }
        forceUnlockInputs();
    }, 200);
    
    // Final unlock after 2 seconds
    setTimeout(forceUnlockInputs, 2000);
}
