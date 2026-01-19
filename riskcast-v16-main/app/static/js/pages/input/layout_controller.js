
import { $id, qs, addClass, removeClass, toggleClass, on } from '../../core/dom.js';
import { domReady } from '../../core/events.js';

export function initLayoutController() {
    const container = qs('.enterprise-input-container');
    const sidebar = qs('.enterprise-sidebar');
    const sidebarToggle = $id('sidebar-toggle');
    const aiPanel = $id('ai-smart-assist-panel');
    const aiPanelToggle = $id('ai-panel-toggle');
    const aiPanelClose = $id('ai-panel-close');
    const aiPanelContent = $id('ai-panel-content');
    
    if (!container) return;
    
    // Sidebar Toggle
    if (sidebarToggle && sidebar) {
        on(sidebarToggle, 'click', () => {
            toggleClass(container, 'sidebar-collapsed');
            toggleClass(sidebar, 'collapsed');
        });
    }
    
    // AI Panel Toggle
    if (aiPanelToggle && aiPanel) {
        on(aiPanelToggle, 'click', () => {
            addClass(container, 'ai-panel-open');
            addClass(aiPanel, 'open');
            
            // Lazy-load AI content
            if (aiPanelContent && !aiPanelContent.classList.contains('loaded')) {
                setTimeout(() => {
                    addClass(aiPanelContent, 'loaded');
                }, 200);
            }
        });
    }
    
    // AI Panel Close
    if (aiPanelClose && aiPanel) {
        on(aiPanelClose, 'click', () => {
            removeClass(container, 'ai-panel-open');
            removeClass(aiPanel, 'open');
        });
    }
    
    // Close AI panel when clicking outside (optional)
    on(document, 'click', (e) => {
        if (aiPanel && aiPanel.classList.contains('open')) {
            if (!aiPanel.contains(e.target) && 
                !aiPanelToggle.contains(e.target) && 
                e.target !== aiPanelToggle) {
                // Keep panel open on outside click for better UX
            }
        }
    });
}

