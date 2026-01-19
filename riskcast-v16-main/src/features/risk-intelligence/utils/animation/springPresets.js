/**
 * Spring animation presets
 * Physics-based motion configurations
 */

export const SPRING_PRESETS = {
  gentle: {
    tension: 120,
    friction: 14,
    mass: 1,
    velocity: 0,
    clamp: false
  },
  
  bouncy: {
    tension: 200,
    friction: 10,
    mass: 1,
    velocity: 0,
    clamp: false
  },
  
  stiff: {
    tension: 300,
    friction: 20,
    mass: 1,
    velocity: 0,
    clamp: false
  },
  
  slow: {
    tension: 80,
    friction: 12,
    mass: 1,
    velocity: 0,
    clamp: false
  },
  
  molasses: {
    tension: 60,
    friction: 18,
    mass: 1,
    velocity: 0,
    clamp: false
  },
  
  wobbly: {
    tension: 180,
    friction: 8,
    mass: 1,
    velocity: 0,
    clamp: false
  }
}

/**
 * Get spring config by name
 * @param {string} presetName
 * @returns {Object}
 */
export function getSpringPreset(presetName) {
  return SPRING_PRESETS[presetName] || SPRING_PRESETS.gentle
}

/**
 * Create cubic-bezier easing string
 * @param {string} presetName
 * @returns {string}
 */
export function getEasing(presetName = 'gentle') {
  const easings = {
    gentle: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    bouncy: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    stiff: 'cubic-bezier(0.4, 0, 0.2, 1)',
    slow: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
    linear: 'linear'
  }
  
  return easings[presetName] || easings.gentle
}

/**
 * Get duration for animation type
 * @param {string} type
 * @returns {number} Duration in milliseconds
 */
export function getDuration(type = 'default') {
  const durations = {
    instant: 0,
    fast: 200,
    default: 300,
    slow: 400,
    slower: 600
  }
  
  return durations[type] || durations.default
}

export default {
  SPRING_PRESETS,
  getSpringPreset,
  getEasing,
  getDuration
}






