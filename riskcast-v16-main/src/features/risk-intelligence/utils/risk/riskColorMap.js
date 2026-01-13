import { RISK_COLORS } from '../../constants/colorPalette'
import { RISK_LEVELS, RISK_THRESHOLDS } from '../../constants/riskThresholds'

/**
 * Get risk level from score
 * @param {number} score - Risk score (0-100)
 * @returns {'low'|'medium'|'high'|'critical'}
 */
export function getRiskLevel(score) {
  if (score <= RISK_THRESHOLDS.LOW.max) return RISK_LEVELS.LOW
  if (score <= RISK_THRESHOLDS.MEDIUM.max) return RISK_LEVELS.MEDIUM
  if (score <= RISK_THRESHOLDS.HIGH.max) return RISK_LEVELS.HIGH
  return RISK_LEVELS.CRITICAL
}

/**
 * Get color config for risk score
 * @param {number} score
 * @returns {Object} Color configuration
 */
export function getRiskColor(score) {
  const level = getRiskLevel(score)
  return RISK_COLORS[level]
}

/**
 * Interpolate color between risk levels
 * @param {number} score - Risk score (0-100)
 * @returns {string} Hex color
 */
export function interpolateRiskColor(score) {
  // Clamp score
  const clampedScore = Math.max(0, Math.min(100, score))
  
  // Define color stops
  const stops = [
    { score: 0, color: '#10B981' },    // Green
    { score: 25, color: '#10B981' },
    { score: 26, color: '#F59E0B' },   // Yellow
    { score: 50, color: '#F59E0B' },
    { score: 51, color: '#F97316' },   // Orange
    { score: 75, color: '#F97316' },
    { score: 76, color: '#EF4444' },   // Red
    { score: 100, color: '#EF4444' }
  ]
  
  // Find surrounding stops
  let lowerStop = stops[0]
  let upperStop = stops[stops.length - 1]
  
  for (let i = 0; i < stops.length - 1; i++) {
    if (clampedScore >= stops[i].score && clampedScore <= stops[i + 1].score) {
      lowerStop = stops[i]
      upperStop = stops[i + 1]
      break
    }
  }
  
  // If score is exactly on a threshold, return that color
  if (lowerStop.score === clampedScore) return lowerStop.color
  if (upperStop.score === clampedScore) return upperStop.color
  
  // Interpolate
  const range = upperStop.score - lowerStop.score
  const progress = (clampedScore - lowerStop.score) / range
  
  return lerpColor(lowerStop.color, upperStop.color, progress)
}

/**
 * Linear interpolation between two hex colors
 * @param {string} color1 - Start color (hex)
 * @param {string} color2 - End color (hex)
 * @param {number} factor - Interpolation factor (0-1)
 * @returns {string} Interpolated hex color
 */
function lerpColor(color1, color2, factor) {
  const c1 = hexToRgb(color1)
  const c2 = hexToRgb(color2)
  
  const r = Math.round(c1.r + (c2.r - c1.r) * factor)
  const g = Math.round(c1.g + (c2.g - c1.g) * factor)
  const b = Math.round(c1.b + (c2.b - c1.b) * factor)
  
  return rgbToHex(r, g, b)
}

/**
 * Convert hex color to RGB
 * @param {string} hex
 * @returns {{r: number, g: number, b: number}}
 */
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : { r: 0, g: 0, b: 0 }
}

/**
 * Convert RGB to hex color
 * @param {number} r
 * @param {number} g
 * @param {number} b
 * @returns {string} Hex color
 */
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(x => {
    const hex = x.toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }).join('')
}

/**
 * Get neon glow style for risk level
 * @param {number} score
 * @param {number} intensity - Glow intensity (0-1)
 * @returns {Object} Style object with boxShadow
 */
export function getNeonGlow(score, intensity = 0.5) {
  const color = getRiskColor(score).glow
  const alpha1 = Math.round(intensity * 255).toString(16).padStart(2, '0')
  const alpha2 = Math.round(intensity * 180).toString(16).padStart(2, '0')
  const alpha3 = Math.round(intensity * 100).toString(16).padStart(2, '0')
  
  return {
    boxShadow: `
      0 0 10px ${color}${alpha1},
      0 0 20px ${color}${alpha2},
      0 0 30px ${color}${alpha3}
    `
  }
}

/**
 * Check if score should show pulse animation (critical risk)
 * @param {number} score
 * @returns {boolean}
 */
export function shouldPulse(score) {
  return score >= RISK_THRESHOLDS.CRITICAL.min
}






