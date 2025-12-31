
/**
 * Format currency with commas
 * @param {number|string} value - Value to format
 * @param {string} currency - Currency symbol (default: empty)
 * @returns {string}
 */
export function formatCurrency(value, currency = '') {
    const num = typeof value === 'string' ? parseFloat(value.replace(/[^\d.-]/g, '')) : Number(value);
    if (isNaN(num)) {
        return currency + '0';
    }
    const formatted = num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return currency + formatted;
}

/**
 * Format number with commas and decimals
 * @param {number|string} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string}
 */
export function formatNumber(value, decimals = 0) {
    const num = typeof value === 'string' ? parseFloat(value) : Number(value);
    if (isNaN(num)) {
        return '0';
    }
    return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format percentage
 * @param {number|string} value - Value to format (0-100)
 * @param {number} decimals - Number of decimal places
 * @returns {string}
 */
export function formatPercentage(value, decimals = 1) {
    const num = typeof value === 'string' ? parseFloat(value) : Number(value);
    if (isNaN(num)) {
        return '0%';
    }
    return num.toFixed(decimals) + '%';
}

/**
 * Format date to DD/MM/YYYY
 * @param {Date|string} date - Date to format
 * @returns {string}
 */
export function formatDate(date) {
    if (!date) {
        return '';
    }
    
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) {
        return '';
    }
    
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    
    return `${day}/${month}/${year}`;
}

/**
 * Format date to YYYY-MM-DD
 * @param {Date|string} date - Date to format
 * @returns {string}
 */
export function formatDateISO(date) {
    if (!date) {
        return '';
    }
    
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) {
        return '';
    }
    
    return d.toISOString().split('T')[0];
}

/**
 * Format date with time
 * @param {Date|string} date - Date to format
 * @returns {string}
 */
export function formatDateTime(date) {
    if (!date) {
        return '';
    }
    
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) {
        return '';
    }
    
    const dateStr = formatDate(d);
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    
    return `${dateStr} ${hours}:${minutes}`;
}

/**
 * Format file size
 * @param {number} bytes - Size in bytes
 * @returns {string}
 */
export function formatFileSize(bytes) {
    if (bytes === 0) {
        return '0 Bytes';
    }
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format duration (milliseconds to readable)
 * @param {number} ms - Duration in milliseconds
 * @returns {string}
 */
export function formatDuration(ms) {
    if (ms < 1000) {
        return `${ms}ms`;
    }
    
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) {
        return `${seconds}s`;
    }
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes < 60) {
        return `${minutes}m ${remainingSeconds}s`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    
    return `${hours}h ${remainingMinutes}m`;
}




















