
/**
 * Bind event to element(s)
 * @param {string|Element|NodeList} elements - Selector, element, or node list
 * @param {string} event - Event type
 * @param {Function} handler - Event handler
 * @param {boolean|AddEventListenerOptions} options - Event options
 */
export function on(elements, event, handler, options = false) {
    const els = typeof elements === 'string' 
        ? document.querySelectorAll(elements) 
        : (elements.length ? elements : [elements]);
    
    els.forEach(el => {
        if (el && typeof el.addEventListener === 'function') {
            el.addEventListener(event, handler, options);
        }
    });
}

/**
 * Unbind event from element(s)
 * @param {string|Element|NodeList} elements - Selector, element, or node list
 * @param {string} event - Event type
 * @param {Function} handler - Event handler
 * @param {boolean|EventListenerOptions} options - Event options
 */
export function off(elements, event, handler, options = false) {
    const els = typeof elements === 'string' 
        ? document.querySelectorAll(elements) 
        : (elements.length ? elements : [elements]);
    
    els.forEach(el => {
        if (el && typeof el.removeEventListener === 'function') {
            el.removeEventListener(event, handler, options);
        }
    });
}

/**
 * One-time event binding
 * @param {string|Element|NodeList} elements - Selector, element, or node list
 * @param {string} event - Event type
 * @param {Function} handler - Event handler
 * @param {boolean|AddEventListenerOptions} options - Event options
 */
export function once(elements, event, handler, options = false) {
    const wrappedHandler = function(...args) {
        handler.apply(this, args);
        off(elements, event, wrappedHandler, options);
    };
    on(elements, event, wrappedHandler, options);
}

/**
 * Event delegation
 * @param {string|Element} container - Container selector or element
 * @param {string} selector - Child selector
 * @param {string} event - Event type
 * @param {Function} handler - Event handler
 * @param {boolean|AddEventListenerOptions} options - Event options
 */
export function delegate(container, selector, event, handler, options = false) {
    const containerEl = typeof container === 'string' 
        ? document.querySelector(container) 
        : container;
    
    if (!containerEl) {
        return;
    }
    
    containerEl.addEventListener(event, function(e) {
        const target = e.target.closest(selector);
        if (target && containerEl.contains(target)) {
            handler.call(target, e);
        }
    }, options);
}

/**
 * Trigger event on element
 * @param {string|Element} element - Selector or element
 * @param {string} eventType - Event type
 * @param {object} detail - Custom event detail
 */
export function trigger(element, eventType, detail = {}) {
    const el = typeof element === 'string' ? document.querySelector(element) : element;
    if (!el) {
        return;
    }
    
    const event = new CustomEvent(eventType, {
        detail,
        bubbles: true,
        cancelable: true
    });
    
    el.dispatchEvent(event);
}

/**
 * Wait for DOM ready
 * @returns {Promise<void>}
 */
export function domReady() {
    return new Promise((resolve) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', resolve);
        } else {
            resolve();
        }
    });
}

/**
 * Wait for window load
 * @returns {Promise<void>}
 */
export function windowReady() {
    return new Promise((resolve) => {
        if (document.readyState === 'complete') {
            resolve();
        } else {
            window.addEventListener('load', resolve);
        }
    });
}




















