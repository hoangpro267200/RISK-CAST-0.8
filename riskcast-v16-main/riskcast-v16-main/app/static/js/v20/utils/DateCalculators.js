/**
 * ========================================================================
 * RISKCAST v20 - Date Calculators
 * ========================================================================
 * Utility functions for date calculations (ETA, transit days, etc.)
 */

/**
 * Calculate ETA from ETD and transit days
 * @param {string} etd - Estimated Time of Departure (YYYY-MM-DD)
 * @param {number} transitDays - Transit days
 * @returns {string} ETA in YYYY-MM-DD format
 */
export function calculateETA(etd, transitDays) {
    if (!etd || !transitDays) return '';
    
    const etdDate = new Date(etd);
    if (isNaN(etdDate.getTime())) return '';
    
    const transit = parseInt(transitDays);
    if (isNaN(transit)) return '';
    
    const etaDate = new Date(etdDate);
    etaDate.setDate(etaDate.getDate() + transit);
    
    return etaDate.toISOString().split('T')[0];
}

/**
 * Calculate difference in days between two dates
 * @param {string} start - Start date (YYYY-MM-DD)
 * @param {string} end - End date (YYYY-MM-DD)
 * @returns {number} Number of days difference
 */
export function diffDays(start, end) {
    const s = new Date(start);
    const e = new Date(end);
    if (isNaN(s.getTime()) || isNaN(e.getTime())) return 0;
    const diffMs = e.getTime() - s.getTime();
    return Math.max(0, Math.round(diffMs / (1000 * 60 * 60 * 24)));
}

/**
 * Generate realistic date with offset
 * @param {number} minOffset - Minimum days offset from today
 * @param {number} maxOffset - Maximum days offset from today
 * @returns {string} Date in YYYY-MM-DD format
 */
export function generateRealisticDate(minOffset, maxOffset) {
    const today = new Date();
    const offset = minOffset + Math.floor(Math.random() * (maxOffset - minOffset + 1));
    const date = new Date(today);
    date.setDate(date.getDate() + offset);
    return date.toISOString().split('T')[0];
}



