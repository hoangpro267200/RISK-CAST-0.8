
import { $id } from '../../core/dom.js';
import { domReady, windowReady } from '../../core/events.js';

export async function initSummaryOverview() {
    await domReady();
    
    // Try to initialize summary overview if available globally
    if (typeof window.initSummaryOverview === 'function') {
        window.initSummaryOverview();
        return;
    }

    // Fallback: try to find and initialize overview elements
    const summaryOverview = $id('summary-overview');
    const inputGrid = $id('input-grid');
    
    if (!summaryOverview || !inputGrid) {
        // Retry if elements not loaded yet
        setTimeout(initSummaryOverview, 300);
        return;
    }

    // Summary overview is ready - further initialization can be added here
    await windowReady();
    setTimeout(() => {
        if (typeof window.initSummaryOverview === 'function') {
            window.initSummaryOverview();
        }
    }, 500);
}
