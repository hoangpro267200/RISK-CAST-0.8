
/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean}
 */
export function isValidEmail(email) {
    if (!email || typeof email !== 'string') {
        return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email.trim());
}

/**
 * Validate URL format
 * @param {string} url - URL to validate
 * @returns {boolean}
 */
export function isValidURL(url) {
    if (!url || typeof url !== 'string') {
        return false;
    }
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

/**
 * Validate phone number (basic)
 * @param {string} phone - Phone number to validate
 * @returns {boolean}
 */
export function isValidPhone(phone) {
    if (!phone || typeof phone !== 'string') {
        return false;
    }
    const phoneRegex = /^[\d\s\-\+\(\)]+$/;
    return phoneRegex.test(phone.trim()) && phone.replace(/\D/g, '').length >= 10;
}

/**
 * Validate number range
 * @param {number} value - Value to validate
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {boolean}
 */
export function isInRange(value, min, max) {
    const num = Number(value);
    if (isNaN(num)) {
        return false;
    }
    return num >= min && num <= max;
}

/**
 * Validate required field
 * @param {*} value - Value to validate
 * @returns {boolean}
 */
export function isRequired(value) {
    if (value === null || value === undefined) {
        return false;
    }
    if (typeof value === 'string') {
        return value.trim().length > 0;
    }
    if (Array.isArray(value)) {
        return value.length > 0;
    }
    return true;
}

/**
 * Validate date format
 * @param {string} date - Date string to validate
 * @param {string} format - Expected format (optional)
 * @returns {boolean}
 */
export function isValidDate(date) {
    if (!date || typeof date !== 'string') {
        return false;
    }
    const d = new Date(date);
    return d instanceof Date && !isNaN(d.getTime());
}

/**
 * Validate positive number
 * @param {*} value - Value to validate
 * @returns {boolean}
 */
export function isPositive(value) {
    const num = Number(value);
    return !isNaN(num) && num > 0;
}

/**
 * Validate non-negative number
 * @param {*} value - Value to validate
 * @returns {boolean}
 */
export function isNonNegative(value) {
    const num = Number(value);
    return !isNaN(num) && num >= 0;
}

/**
 * Validate input has value (for form validation)
 * @param {HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement} element - Form element
 * @returns {boolean}
 */
export function hasValue(element) {
    if (!element) {
        return false;
    }
    
    const value = element.value;
    if (value === null || value === undefined) {
        return false;
    }
    
    if (typeof value === 'string') {
        return value.trim() !== '' && value !== '0';
    }
    
    return value !== '';
}




















