/**
 * ========================================================================
 * RISKCAST v20 - Data Loaders
 * ========================================================================
 * Utility functions for loading logistics data
 */

/**
 * Load logistics data from window.LOGISTICS_DATA
 * @param {Function} onSuccess - Callback when data is loaded
 * @param {Function} onRetry - Callback for retry attempts
 * @returns {boolean} True if data is available, false otherwise
 */
export async function loadLogisticsData(onSuccess = null, onRetry = null) {
    if (typeof window !== 'undefined' && window.LOGISTICS_DATA) {
        console.log('✅ LOGISTICS_DATA loaded');
        if (onSuccess) onSuccess(window.LOGISTICS_DATA);
        return true;
    } else {
        console.warn('⚠️ LOGISTICS_DATA not available. Retrying...');
        setTimeout(() => {
            if (typeof window !== 'undefined' && window.LOGISTICS_DATA) {
                console.log('✅ LOGISTICS_DATA loaded on retry');
                if (onSuccess) onSuccess(window.LOGISTICS_DATA);
            } else if (onRetry) {
                onRetry();
            }
        }, 500);
        return false;
    }
}

/**
 * Wait for LOGISTICS_DATA to be available
 * @param {number} maxRetries - Maximum number of retry attempts
 * @param {number} retryDelay - Delay between retries in ms
 * @returns {Promise<Object>} Promise that resolves with LOGISTICS_DATA
 */
export function waitForLogisticsData(maxRetries = 20, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        let retryCount = 0;
        
        const checkData = () => {
            if (typeof window !== 'undefined' && window.LOGISTICS_DATA) {
                resolve(window.LOGISTICS_DATA);
            } else if (retryCount < maxRetries) {
                retryCount++;
                setTimeout(checkData, retryDelay);
            } else {
                reject(new Error('LOGISTICS_DATA not available after max retries'));
            }
        };
        
        checkData();
    });
}



