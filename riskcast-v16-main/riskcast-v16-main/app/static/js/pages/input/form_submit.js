
import { $id, on } from '../../core/dom.js';
import { domReady } from '../../core/events.js';

function handleSubmit(e) {
    e.preventDefault();
    e.stopPropagation();
    
    
    // Call global runAnalysis if available
    if (typeof window.runAnalysis === "function") {
        window.runAnalysis();
    } else {
        console.error("✗ ERROR: runAnalysis() missing");
        alert("Không tìm thấy hàm runAnalysis.");
    }
}

export async function initFormSubmit() {
    await domReady();
    
    const form = $id('risk_form');
    if (!form) {
        // Retry after delay
        setTimeout(initFormSubmit, 200);
        return;
    }
    
    // Remove existing listener if any
    form.removeEventListener("submit", handleSubmit);
    // Add new listener
    on(form, 'submit', handleSubmit);
    
}

