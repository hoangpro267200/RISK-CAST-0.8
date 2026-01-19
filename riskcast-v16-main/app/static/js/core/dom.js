
/**
 * Quick selector shortcuts
 * @param {string} selector - CSS selector
 * @returns {Element|null}
 */
export function qs(selector) {
    return document.querySelector(selector);
}

/**
 * Query selector all
 * @param {string} selector - CSS selector
 * @returns {NodeList}
 */
export function qsa(selector) {
    return document.querySelectorAll(selector);
}

/**
 * Get element by ID
 * @param {string} id - Element ID
 * @returns {Element|null}
 */
export function $id(id) {
    return document.getElementById(id);
}

/**
 * Wait for element to appear in DOM
 * @param {string} selector - CSS selector
 * @param {number} timeout - Timeout in ms
 * @returns {Promise<Element>}
 */
export function waitForElement(selector, timeout = 5000) {
    return new Promise((resolve, reject) => {
        const element = qs(selector);
        if (element) {
            resolve(element);
            return;
        }

        const observer = new MutationObserver((mutations, obs) => {
            const element = qs(selector);
            if (element) {
                obs.disconnect();
                resolve(element);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        setTimeout(() => {
            observer.disconnect();
            reject(new Error(`Element ${selector} not found within ${timeout}ms`));
        }, timeout);
    });
}

/**
 * Check if element exists
 * @param {string} selector - CSS selector
 * @returns {boolean}
 */
export function exists(selector) {
    return qs(selector) !== null;
}

/**
 * Remove element from DOM
 * @param {string|Element} element - Selector or element
 */
export function remove(element) {
    const el = typeof element === 'string' ? qs(element) : element;
    if (el && el.parentNode) {
        el.parentNode.removeChild(el);
    }
}

/**
 * Clear element content
 * @param {string|Element} element - Selector or element
 */
export function clear(element) {
    const el = typeof element === 'string' ? qs(element) : element;
    if (el) {
        el.innerHTML = '';
    }
}

/**
 * Normalize elements to array (supports Element, NodeList, Array, or selector string)
 * @param {Element|NodeList|Array|string} els - Elements to normalize
 * @returns {Array<Element>} Normalized array of elements
 */
function normalizeElements(els) {
    if (!els) return [];
    if (els instanceof Element) return [els];
    if (NodeList.prototype.isPrototypeOf(els) || Array.isArray(els)) return [...els];
    if (typeof els === "string") return [...document.querySelectorAll(els)];
    return [];
}

/**
 * Add class to element(s)
 * @param {string|Element|NodeList|Array} elements - Selector, element, node list, or array
 * @param {string} className - Class name to add
 */
export function addClass(elements, className) {
    const arr = normalizeElements(elements);
    arr.forEach(el => el && el.classList && el.classList.add(className));
}

/**
 * Remove class from element(s)
 * @param {string|Element|NodeList|Array} elements - Selector, element, node list, or array
 * @param {string} className - Class name to remove
 */
export function removeClass(elements, className) {
    const arr = normalizeElements(elements);
    arr.forEach(el => el && el.classList && el.classList.remove(className));
}

/**
 * Toggle class on element(s)
 * @param {string|Element|NodeList|Array} elements - Selector, element, node list, or array
 * @param {string} className - Class name to toggle
 */
export function toggleClass(elements, className) {
    const arr = normalizeElements(elements);
    arr.forEach(el => el && el.classList && el.classList.toggle(className));
}

/**
 * Check if element has class
 * @param {string|Element} element - Selector or element
 * @param {string} className - Class name
 * @returns {boolean}
 */
export function hasClass(element, className) {
    const el = typeof element === 'string' ? qs(element) : element;
    return el?.classList?.contains(className) ?? false;
}

/**
 * Set attribute on element(s)
 * @param {string|Element|NodeList|Array} elements - Selector, element, node list, or array
 * @param {string} name - Attribute name
 * @param {string} value - Attribute value
 */
export function setAttr(elements, name, value) {
    const arr = normalizeElements(elements);
    arr.forEach(el => el && el.setAttribute && el.setAttribute(name, value));
}

/**
 * Get attribute from element
 * @param {string|Element} element - Selector or element
 * @param {string} name - Attribute name
 * @returns {string|null}
 */
export function getAttr(element, name) {
    const el = typeof element === 'string' ? qs(element) : element;
    return el?.getAttribute?.(name) ?? null;
}

/**
 * Remove attribute from element(s)
 * @param {string|Element|NodeList|Array} elements - Selector, element, node list, or array
 * @param {string} name - Attribute name
 */
export function removeAttr(elements, name) {
    const arr = normalizeElements(elements);
    arr.forEach(el => el && el.removeAttribute && el.removeAttribute(name));
}

/**
 * Set text content of element by ID
 * @param {string} id - Element ID
 * @param {string} text - Text content to set
 */
export function setText(id, text) {
    const el = $id(id);
    if (el) {
        el.textContent = text || '';
    } else {
    }
}

/**
 * Set innerHTML of element by ID
 * @param {string} id - Element ID
 * @param {string} html - HTML content to set
 */
export function setHTML(id, html) {
    const el = $id(id);
    if (el) {
        el.innerHTML = html || '';
    } else {
    }
}

/**
 * Add event listener helper
 * @param {Element|Document|Window|NodeList|Array|string} target - Target element(s) or document/window or selector
 * @param {string} event - Event name
 * @param {Function} handler - Event handler function
 * @param {boolean|Object} options - Event listener options
 */
export function on(target, event, handler, options) {
    if (!target) return;
    
    // Special handling for document and window
    if (target === document || target === window) {
        target.addEventListener(event, handler, options);
        return;
    }
    
    // Use normalizeElements for everything else
    const arr = normalizeElements(target);
    arr.forEach(el => {
        if (el && el.addEventListener) {
            el.addEventListener(event, handler, options);
        }
    });
}

