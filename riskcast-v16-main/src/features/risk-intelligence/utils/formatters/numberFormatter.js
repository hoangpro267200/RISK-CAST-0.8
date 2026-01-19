/**
 * Number formatting utilities
 * Locale-aware formatting for scores, percentages, and large numbers
 */

/**
 * Format risk score with optional decimals
 * @param {number} score
 * @param {number} decimals
 * @returns {string}
 */
export function formatScore(score, decimals = 1) {
  if (score === null || score === undefined) return 'N/A'
  return score.toFixed(decimals)
}

/**
 * Format percentage
 * @param {number} value - Value between 0-1 or 0-100
 * @param {number} decimals
 * @param {boolean} isDecimal - If true, value is 0-1, else 0-100
 * @returns {string}
 */
export function formatPercent(value, decimals = 0, isDecimal = false) {
  if (value === null || value === undefined) return 'N/A'
  const percentage = isDecimal ? value * 100 : value
  return `${percentage.toFixed(decimals)}%`
}

/**
 * Format days
 * @param {number} days
 * @returns {string}
 */
export function formatDays(days) {
  if (days === null || days === undefined) return 'N/A'
  if (days === 0) return 'No delay'
  if (days === 1) return '1 day'
  return `${days} days`
}

/**
 * Format delay range
 * @param {number} min
 * @param {number} max
 * @returns {string}
 */
export function formatDelayRange(min, max) {
  if (min === null || max === null) return 'N/A'
  if (min === max) return formatDays(min)
  return `${min}-${max} days`
}

/**
 * Format large numbers with K/M suffixes
 * @param {number} num
 * @param {number} decimals
 * @returns {string}
 */
export function formatLargeNumber(num, decimals = 1) {
  if (num === null || num === undefined) return 'N/A'
  if (num >= 1e9) return `${(num / 1e9).toFixed(decimals)}B`
  if (num >= 1e6) return `${(num / 1e6).toFixed(decimals)}M`
  if (num >= 1e3) return `${(num / 1e3).toFixed(decimals)}K`
  return num.toString()
}

/**
 * Format currency
 * @param {number} amount
 * @param {string} currency
 * @param {string} locale
 * @returns {string}
 */
export function formatCurrency(amount, currency = 'USD', locale = 'en-US') {
  if (amount === null || amount === undefined) return 'N/A'
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency
  }).format(amount)
}

/**
 * Format number with locale-specific separators
 * @param {number} num
 * @param {number} decimals
 * @param {string} locale
 * @returns {string}
 */
export function formatNumber(num, decimals = 0, locale = 'en-US') {
  if (num === null || num === undefined) return 'N/A'
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(num)
}

/**
 * Format trend value with +/- sign and color
 * @param {number} value - Positive = increase, Negative = decrease
 * @returns {{text: string, color: string, icon: string}}
 */
export function formatTrend(value) {
  if (value === null || value === undefined || value === 0) {
    return {
      text: '0%',
      color: 'text-gray-400',
      icon: '→'
    }
  }
  
  const isPositive = value > 0
  const absValue = Math.abs(value)
  
  return {
    text: `${isPositive ? '+' : ''}${absValue.toFixed(1)}%`,
    color: isPositive ? 'text-red-400' : 'text-green-400',
    icon: isPositive ? '↑' : '↓'
  }
}

/**
 * Clamp number to range
 * @param {number} value
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

/**
 * Round to nearest step
 * @param {number} value
 * @param {number} step
 * @returns {number}
 */
export function roundToStep(value, step) {
  return Math.round(value / step) * step
}






