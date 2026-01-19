
import { qsa, on } from '../../core/dom.js';
import { debounce } from '../../core/utils.js';

export function initInputEvents() {
    // Typing mode - add class to body when user is typing
    let typingTimeout = null;
    const TYPING_DELAY = 150;
    
    const enableTypingMode = debounce(() => {
        document.body.classList.add('typing');
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }
        typingTimeout = setTimeout(() => {
            document.body.classList.remove('typing');
            typingTimeout = null;
        }, TYPING_DELAY);
    }, 50);
    
    const inputs = qsa('input[type="text"], input[type="number"], input[type="email"], input[type="tel"], textarea, .form-input');
    
    inputs.forEach(input => {
        on(input, 'input', enableTypingMode, { passive: true });
        on(input, 'keydown', enableTypingMode, { passive: true });
    });
    
    // Dynamic input monitoring
    const observer = new MutationObserver((mutations) => {
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
            const newInputs = qsa('input[type="text"], input[type="number"], input[type="email"], input[type="tel"], textarea, .form-input');
            newInputs.forEach(input => {
                on(input, 'input', enableTypingMode, { passive: true });
                on(input, 'keydown', enableTypingMode, { passive: true });
            });
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}




















