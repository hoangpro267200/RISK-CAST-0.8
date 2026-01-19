/**
 * Color interpolation utilities for gradients
 */

/**
 * Interpolate between two colors
 * @param {string} color1 - Start color (hex)
 * @param {string} color2 - End color (hex)
 * @param {number} factor - 0 to 1
 * @returns {string} Interpolated color (hex)
 */
export function interpolateColor(color1, color2, factor) {
  const c1 = hexToRgb(color1)
  const c2 = hexToRgb(color2)
  
  const r = Math.round(c1.r + (c2.r - c1.r) * factor)
  const g = Math.round(c1.g + (c2.g - c1.g) * factor)
  const b = Math.round(c1.b + (c2.b - c1.b) * factor)
  
  return rgbToHex(r, g, b)
}

/**
 * Create gradient between multiple colors
 * @param {Array<string>} colors - Array of hex colors
 * @param {number} steps - Number of interpolation steps
 * @returns {Array<string>} Array of interpolated colors
 */
export function createGradient(colors, steps) {
  if (colors.length < 2) return colors
  
  const gradient = []
  const segmentSteps = Math.floor(steps / (colors.length - 1))
  
  for (let i = 0; i < colors.length - 1; i++) {
    for (let j = 0; j < segmentSteps; j++) {
      const factor = j / segmentSteps
      gradient.push(interpolateColor(colors[i], colors[i + 1], factor))
    }
  }
  
  gradient.push(colors[colors.length - 1])
  return gradient
}

/**
 * Get color from gradient scale
 * @param {number} value - Value (0-100)
 * @param {Array<{stop: number, color: string}>} colorStops
 * @returns {string} Interpolated color
 */
export function getGradientColor(value, colorStops) {
  // Sort by stop
  const sorted = [...colorStops].sort((a, b) => a.stop - b.stop)
  
  // Find surrounding stops
  let lower = sorted[0]
  let upper = sorted[sorted.length - 1]
  
  for (let i = 0; i < sorted.length - 1; i++) {
    if (value >= sorted[i].stop && value <= sorted[i + 1].stop) {
      lower = sorted[i]
      upper = sorted[i + 1]
      break
    }
  }
  
  // Calculate factor
  const range = upper.stop - lower.stop
  const factor = range === 0 ? 0 : (value - lower.stop) / range
  
  return interpolateColor(lower.color, upper.color, factor)
}

/**
 * Create radial gradient definition for SVG
 * @param {string} id - Gradient ID
 * @param {string} color - Base color
 * @returns {string} SVG gradient element
 */
export function createRadialGradient(id, color) {
  const rgb = hexToRgb(color)
  const darker = rgbToHex(
    Math.round(rgb.r * 0.7),
    Math.round(rgb.g * 0.7),
    Math.round(rgb.b * 0.7)
  )
  
  return `
    <radialGradient id="${id}">
      <stop offset="0%" stop-color="${color}" />
      <stop offset="100%" stop-color="${darker}" />
    </radialGradient>
  `
}

/**
 * Convert hex to RGB
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
 * Convert RGB to hex
 * @param {number} r
 * @param {number} g
 * @param {number} b
 * @returns {string}
 */
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(x => {
    const hex = Math.max(0, Math.min(255, x)).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }).join('')
}

/**
 * Lighten color
 * @param {string} color - Hex color
 * @param {number} amount - 0 to 1
 * @returns {string}
 */
export function lightenColor(color, amount) {
  const rgb = hexToRgb(color)
  return rgbToHex(
    Math.round(rgb.r + (255 - rgb.r) * amount),
    Math.round(rgb.g + (255 - rgb.g) * amount),
    Math.round(rgb.b + (255 - rgb.b) * amount)
  )
}

/**
 * Darken color
 * @param {string} color - Hex color
 * @param {number} amount - 0 to 1
 * @returns {string}
 */
export function darkenColor(color, amount) {
  const rgb = hexToRgb(color)
  return rgbToHex(
    Math.round(rgb.r * (1 - amount)),
    Math.round(rgb.g * (1 - amount)),
    Math.round(rgb.b * (1 - amount))
  )
}

export default {
  interpolateColor,
  createGradient,
  getGradientColor,
  createRadialGradient,
  lightenColor,
  darkenColor
}






