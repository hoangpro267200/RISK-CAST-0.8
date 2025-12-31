
import { removeClass, removeAttr } from '../../core/dom.js';

function unlockForm() {
    // 1. Mở khóa mọi input, dropdown, textarea với FORCE
    removeAttr("input, select, textarea, .custom-dropdown, .dropdown-trigger, .dropdown-menu, .dropdown-option, .dropdown-value, button, [role='button']", "disabled");
    removeAttr("input, select, textarea, .custom-dropdown, .dropdown-trigger, .dropdown-menu, .dropdown-option, .dropdown-value, button, [role='button']", "readonly");
    
    // Remove classes individually
    removeClass("input, select, textarea, .custom-dropdown, .dropdown-trigger, .dropdown-menu, .dropdown-option, .dropdown-value, button, [role='button']", "disabled");
    removeClass("input, select, textarea, .custom-dropdown, .dropdown-trigger, .dropdown-menu, .dropdown-option, .dropdown-value, button, [role='button']", "locked");
    removeClass("input, select, textarea, .custom-dropdown, .dropdown-trigger, .dropdown-menu, .dropdown-option, .dropdown-value, button, [role='button']", "readonly");
    removeClass("input, select, textarea, .custom-dropdown, .dropdown-trigger, .dropdown-menu, .dropdown-option, .dropdown-value, button, [role='button']", "blocked");
    
    // Force unlock styles
    const allElements = document.querySelectorAll('input, select, textarea, .custom-dropdown, .dropdown-trigger, .dropdown-menu, .dropdown-option, .dropdown-value, button, [role="button"]');
    allElements.forEach(el => {
        el.disabled = false;
        el.readOnly = false;
        el.style.setProperty('pointer-events', 'auto', 'important');
        el.style.setProperty('opacity', '1', 'important');
        el.style.setProperty('cursor', el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' ? 'text' : 'pointer', 'important');
        el.style.setProperty('z-index', '10000', 'important');
        el.style.setProperty('position', 'relative', 'important');
    });

    // 2. Force unlock dropdowns đặc biệt
    const dropdowns = document.querySelectorAll('.custom-dropdown');
    dropdowns.forEach(dropdown => {
        removeClass(dropdown, 'disabled');
        removeClass(dropdown, 'locked');
        removeClass(dropdown, 'blocked');
        dropdown.style.setProperty('pointer-events', 'auto', 'important');
        dropdown.style.setProperty('z-index', '10000', 'important');
        
        const trigger = dropdown.querySelector('.dropdown-trigger');
        if (trigger) {
            trigger.style.setProperty('pointer-events', 'auto', 'important');
            trigger.style.setProperty('cursor', 'pointer', 'important');
            trigger.style.setProperty('z-index', '10001', 'important');
            removeAttr(trigger, 'disabled');
            removeClass(trigger, 'disabled');
            removeClass(trigger, 'locked');
        }
        
        const menu = dropdown.querySelector('.dropdown-menu');
        if (menu) {
            menu.style.setProperty('pointer-events', 'auto', 'important');
            menu.style.setProperty('z-index', '10002', 'important');
        }
        
        dropdown.querySelectorAll('.dropdown-option').forEach(option => {
            option.style.setProperty('pointer-events', 'auto', 'important');
            option.style.setProperty('cursor', 'pointer', 'important');
            removeAttr(option, 'disabled');
        });
    });
}

export function initFormUnlock() {
    // Run immediately
    unlockForm();
    
    // Also run after DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', unlockForm);
    } else {
        unlockForm();
    }
    
    // Retry after a delay
    setTimeout(unlockForm, 500);
    
    // Check if SmartInputSystem is available and unlock
    if (window.SmartInputSystem?.init) {
        setTimeout(() => {
            unlockForm();
        }, 1000);
    }
}
