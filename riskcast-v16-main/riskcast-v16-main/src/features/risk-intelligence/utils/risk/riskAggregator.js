/**
 * Risk aggregation utilities
 * For rolling up scores across layers and categories
 */

/**
 * Calculate weighted average
 * @param {Array<{score: number, weight: number}>} items
 * @returns {number}
 */
export function calculateWeightedAverage(items) {
  if (!items || items.length === 0) return 0

  const totalWeight = items.reduce((sum, item) => sum + (item.weight || 1), 0)
  const weightedSum = items.reduce((sum, item) => {
    return sum + (item.score || 0) * (item.weight || 1)
  }, 0)

  return totalWeight > 0 ? weightedSum / totalWeight : 0
}

/**
 * Aggregate layer scores into overall score
 * @param {Array} layers
 * @returns {number}
 */
export function aggregateOverallScore(layers) {
  return Math.round(calculateWeightedAverage(layers))
}

/**
 * Find top N risk drivers
 * @param {Array} layers
 * @param {number} n
 * @returns {Array}
 */
export function getTopRiskDrivers(layers, n = 5) {
  return [...layers]
    .sort((a, b) => b.score - a.score)
    .slice(0, n)
}

/**
 * Calculate risk distribution
 * @param {Array} layers
 * @returns {{low: number, medium: number, high: number, critical: number}}
 */
export function calculateRiskDistribution(layers) {
  const distribution = {
    low: 0,
    medium: 0,
    high: 0,
    critical: 0
  }

  layers.forEach(layer => {
    const score = layer.score || 0
    if (score <= 25) distribution.low++
    else if (score <= 50) distribution.medium++
    else if (score <= 75) distribution.high++
    else distribution.critical++
  })

  return distribution
}

/**
 * Calculate trend from historical data
 * @param {Array<{date: Date, score: number}>} history
 * @returns {number} Percentage change
 */
export function calculateTrend(history) {
  if (!history || history.length < 2) return 0

  const sorted = [...history].sort((a, b) => new Date(a.date) - new Date(b.date))
  const oldest = sorted[0].score
  const newest = sorted[sorted.length - 1].score

  if (oldest === 0) return 0
  return ((newest - oldest) / oldest) * 100
}

/**
 * Normalize scores to 0-100 range
 * @param {Array<number>} scores
 * @returns {Array<number>}
 */
export function normalizeScores(scores) {
  if (!scores || scores.length === 0) return []

  const min = Math.min(...scores)
  const max = Math.max(...scores)
  const range = max - min

  if (range === 0) return scores.map(() => 50)

  return scores.map(score => ((score - min) / range) * 100)
}

export default {
  calculateWeightedAverage,
  aggregateOverallScore,
  getTopRiskDrivers,
  calculateRiskDistribution,
  calculateTrend,
  normalizeScores
}






