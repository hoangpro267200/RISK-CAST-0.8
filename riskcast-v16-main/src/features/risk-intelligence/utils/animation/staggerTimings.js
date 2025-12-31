/**
 * Stagger animation timing calculations
 * For cascade effects
 */

/**
 * Calculate stagger delay for item at index
 * @param {number} index - Item index
 * @param {number} baseDelay - Base delay in ms
 * @param {number} maxDelay - Maximum total delay
 * @returns {number} Delay in milliseconds
 */
export function calculateStagger(index, baseDelay = 50, maxDelay = 1000) {
  return Math.min(index * baseDelay, maxDelay)
}

/**
 * Calculate stagger delay with easing
 * @param {number} index
 * @param {number} total - Total number of items
 * @param {number} duration - Total animation duration
 * @param {Function} easingFn - Easing function
 * @returns {number}
 */
export function calculateStaggerWithEasing(index, total, duration, easingFn = easeOutQuad) {
  const progress = index / (total - 1)
  const easedProgress = easingFn(progress)
  return easedProgress * duration
}

/**
 * Ease out quadratic
 * @param {number} t - Progress (0-1)
 * @returns {number}
 */
export function easeOutQuad(t) {
  return t * (2 - t)
}

/**
 * Ease in quadratic
 * @param {number} t
 * @returns {number}
 */
export function easeInQuad(t) {
  return t * t
}

/**
 * Ease in-out quadratic
 * @param {number} t
 * @returns {number}
 */
export function easeInOutQuad(t) {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
}

/**
 * Ease out cubic
 * @param {number} t
 * @returns {number}
 */
export function easeOutCubic(t) {
  return (--t) * t * t + 1
}

/**
 * Create stagger config for array of items
 * @param {number} count - Number of items
 * @param {Object} options
 * @returns {Array<{delay: number, duration: number}>}
 */
export function createStaggerConfig(count, options = {}) {
  const {
    baseDelay = 50,
    duration = 300,
    easingFn = easeOutQuad,
    reverse = false
  } = options

  const configs = []
  
  for (let i = 0; i < count; i++) {
    const index = reverse ? count - 1 - i : i
    const delay = calculateStagger(index, baseDelay)
    
    configs.push({
      delay,
      duration,
      easing: easingFn
    })
  }
  
  return configs
}

/**
 * Calculate cascade timing for grid layout
 * @param {number} index - Item index
 * @param {number} columns - Grid columns
 * @param {number} rowDelay - Delay per row
 * @param {number} colDelay - Delay per column
 * @returns {number}
 */
export function calculateGridStagger(index, columns, rowDelay = 100, colDelay = 50) {
  const row = Math.floor(index / columns)
  const col = index % columns
  
  return (row * rowDelay) + (col * colDelay)
}

export default {
  calculateStagger,
  calculateStaggerWithEasing,
  easeOutQuad,
  easeInQuad,
  easeInOutQuad,
  easeOutCubic,
  createStaggerConfig,
  calculateGridStagger
}






