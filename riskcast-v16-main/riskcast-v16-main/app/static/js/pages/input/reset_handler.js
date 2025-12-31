
import { $id, on } from '../../core/dom.js';
import { resetForm } from './utils_input.js';
import { domReady } from '../../core/events.js';

export async function initResetHandler() {
    await domReady();
    
    const resetBtn = $id('reset-form-btn');
    
    if (resetBtn) {
        on(resetBtn, 'click', resetForm);
    }
}




















