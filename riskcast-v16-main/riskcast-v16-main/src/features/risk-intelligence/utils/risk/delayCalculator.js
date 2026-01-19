/**
 * Delay calculation utilities
 * Maps risk scores to expected delays
 */

/**
 * Calculate delay impact from risk score
 * Based on historical correlation
 * @param {number} riskScore - Risk score (0-100)
 * @returns {{expected: number, min: number, max: number}}
 */
export function calculateDelayImpact(riskScore) {
  // Risk score thresholds and corresponding delays
  if (riskScore < 25) {
    return { expected: 0, min: 0, max: 2 }
  }
  if (riskScore < 50) {
    return { expected: 3, min: 1, max: 7 }
  }
  if (riskScore < 75) {
    return { expected: 8, min: 4, max: 14 }
  }
  return { expected: 15, min: 10, max: 30 }
}

/**
 * Format delay range as string
 * @param {number} min
 * @param {number} max
 * @returns {string}
 */
export function formatDelayRange(min, max) {
  if (min === max) return `${min} days`
  return `${min}-${max} days`
}

/**
 * Get delay severity level
 * @param {number} days
 * @returns {'minimal'|'moderate'|'significant'|'severe'}
 */
export function getDelaySeverity(days) {
  if (days <= 2) return 'minimal'
  if (days <= 7) return 'moderate'
  if (days <= 14) return 'significant'
  return 'severe'
}

/**
 * Calculate buffer recommendation
 * Adds safety margin based on confidence
 * @param {number} expectedDelay
 * @param {number} confidence - 0-1
 * @returns {number} Recommended buffer days
 */
export function calculateBufferRecommendation(expectedDelay, confidence = 0.85) {
  const uncertaintyFactor = 1 - confidence
  const buffer = Math.ceil(expectedDelay * uncertaintyFactor * 2)
  return Math.max(1, buffer)
}

export default {
  calculateDelayImpact,
  formatDelayRange,
  getDelaySeverity,
  calculateBufferRecommendation
}






