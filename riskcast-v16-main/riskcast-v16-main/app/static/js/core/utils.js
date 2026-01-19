
/**
 * Debounce function - delays execution until function stops being called
 * @param {Function} func - Function to debounce
 * @param {number} wait - Delay in milliseconds
 * @param {boolean} immediate - Execute immediately on first call
 * @returns {Function} Debounced function
 */
function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const context = this;
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Throttle function - limits execution rate
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Deep clone an object
 * @param {*} obj - Object to clone
 * @returns {*} Cloned object
 */
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    
    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }
    
    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }
    
    if (typeof obj === 'object') {
        const cloned = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                cloned[key] = deepClone(obj[key]);
            }
        }
        return cloned;
    }
    
    return obj;
}

/**
 * Check if value is empty
 * @param {*} value - Value to check
 * @returns {boolean}
 */
function isEmpty(value) {
    if (value === null || value === undefined) {
        return true;
    }
    if (typeof value === 'string') {
        return value.trim() === '';
    }
    if (Array.isArray(value)) {
        return value.length === 0;
    }
    if (typeof value === 'object') {
        return Object.keys(value).length === 0;
    }
    return false;
}

/**
 * Generate unique ID
 * @returns {string}
 */
function generateId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Sleep/delay function
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry function with exponential backoff
 * @param {Function} fn - Function to retry
 * @param {number} maxRetries - Maximum retry attempts
 * @param {number} delay - Initial delay in ms
 * @returns {Promise<any>}
 */
async function retry(fn, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await sleep(delay * Math.pow(2, i));
        }
    }
}

/**
 * Format number with commas
 * @param {number} num - Number to format
 * @returns {string}
 */
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) {
        return '0';
    }
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Parse number from string (removes commas, etc.)
 * @param {string} str - String to parse
 * @returns {number}
 */
function parseNumber(str) {
    if (typeof str !== 'string') {
        return Number(str) || 0;
    }
    return Number(str.replace(/[^\d.-]/g, '')) || 0;
}

/**
 * Clamp number between min and max
 * @param {number} value - Value to clamp
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number}
 */
function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

/**
 * Batch DOM updates using requestAnimationFrame
 * @param {Function} callback - Function to batch
 * @returns {Function} Batched function
 */
function batchDOMUpdates(callback) {
    let scheduled = false;
    return function(...args) {
        if (!scheduled) {
            scheduled = true;
            requestAnimationFrame(() => {
                callback.apply(this, args);
                scheduled = false;
            });
        }
    };
}

// Make functions available globally
if (typeof window !== 'undefined') {
    window.RCUtils = {
        debounce,
        throttle,
        deepClone,
        isEmpty,
        generateId,
        sleep,
        retry,
        formatNumber,
        parseNumber,
        clamp,
        batchDOMUpdates
    };
}
