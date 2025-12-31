/**
 * Tailwind transition utility classes
 * Predefined animation classes
 */

export const TRANSITION_CLASSES = {
  // Basic transitions
  smooth: 'transition-all duration-300 ease-out',
  spring: 'transition-spring',
  fast: 'transition-all duration-200 ease-out',
  slow: 'transition-all duration-500 ease-out',
  
  // Transform transitions
  transform: 'transition-transform duration-300 ease-out',
  transformFast: 'transition-transform duration-200 ease-out',
  
  // Opacity transitions
  fade: 'transition-opacity duration-300 ease-out',
  fadeFast: 'transition-opacity duration-200 ease-out',
  fadeSlow: 'transition-opacity duration-500 ease-out',
  
  // Color transitions
  color: 'transition-colors duration-300 ease-out',
  
  // Combined transitions
  all: 'transition-all duration-300 ease-out',
  
  // Hover effects
  hoverScale: 'hover:scale-105 transition-transform duration-200',
  hoverGlow: 'hover:shadow-lg transition-shadow duration-300',
  
  // State transitions
  enter: 'opacity-0 translate-y-4',
  enterActive: 'opacity-100 translate-y-0',
  leave: 'opacity-100',
  leaveActive: 'opacity-0 translate-y-4'
}

export const PULSE_ANIMATION = 'animate-pulse-glow'
export const FADE_IN_ANIMATION = 'animate-fade-in'
export const SLIDE_UP_ANIMATION = 'animate-slide-up'
export const SCALE_IN_ANIMATION = 'animate-scale-in'

/**
 * Get transition class by name
 * @param {string} name
 * @returns {string}
 */
export function getTransitionClass(name) {
  return TRANSITION_CLASSES[name] || TRANSITION_CLASSES.smooth
}

/**
 * Combine multiple transition classes
 * @param {...string} classes
 * @returns {string}
 */
export function combineTransitions(...classes) {
  return classes.join(' ')
}

/**
 * Check if user prefers reduced motion
 * @returns {boolean}
 */
export function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Get appropriate transition class respecting user preferences
 * @param {string} normalClass
 * @param {string} reducedClass
 * @returns {string}
 */
export function getAccessibleTransition(normalClass, reducedClass = '') {
  return prefersReducedMotion() ? reducedClass : normalClass
}

export default {
  TRANSITION_CLASSES,
  PULSE_ANIMATION,
  FADE_IN_ANIMATION,
  SLIDE_UP_ANIMATION,
  SCALE_IN_ANIMATION,
  getTransitionClass,
  combineTransitions,
  prefersReducedMotion,
  getAccessibleTransition
}






