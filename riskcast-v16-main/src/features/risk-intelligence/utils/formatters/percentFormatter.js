/**
 * Percentage-specific formatting utilities
 */

/**
 * Format score as percentage (0-100)
 * @param {number} score
 * @param {number} decimals
 * @returns {string}
 */
export function formatScorePercent(score, decimals = 0) {
  if (score === null || score === undefined) return 'N/A'
  return `${score.toFixed(decimals)}%`
}

/**
 * Format probability (0-1) as percentage
 * @param {number} probability
 * @param {number} decimals
 * @returns {string}
 */
export function formatProbability(probability, decimals = 1) {
  if (probability === null || probability === undefined) return 'N/A'
  return `${(probability * 100).toFixed(decimals)}%`
}

/**
 * Format confidence level
 * @param {number} confidence - Value between 0-1
 * @returns {string}
 */
export function formatConfidence(confidence) {
  if (confidence === null || confidence === undefined) return 'Unknown'
  if (confidence >= 0.95) return 'Very High'
  if (confidence >= 0.85) return 'High'
  if (confidence >= 0.70) return 'Medium'
  return 'Low'
}

/**
 * Format weight/contribution percentage
 * @param {number} weight - Value between 0-1
 * @param {number} decimals
 * @returns {string}
 */
export function formatWeight(weight, decimals = 1) {
  if (weight === null || weight === undefined) return 'N/A'
  return `${(weight * 100).toFixed(decimals)}%`
}

export default {
  formatScorePercent,
  formatProbability,
  formatConfidence,
  formatWeight
}






