import { ref, computed } from 'vue'
import { useUIStore } from '../stores/uiStore'
import { calculateStagger, createStaggerConfig } from '../utils/animation/staggerTimings'
import { SPRING_PRESETS, getEasing, getDuration } from '../utils/animation/springPresets'

/**
 * Animation utilities composable
 * Provides animation helpers and configurations
 */
export function useAnimations() {
  const uiStore = useUIStore()

  /**
   * Check if animations should be enabled
   */
  const shouldAnimate = computed(() => {
    return uiStore.shouldAnimate
  })

  /**
   * Get stagger delay for index
   * @param {number} index
   * @param {number} baseDelay
   * @returns {number}
   */
  const getStaggerDelay = (index, baseDelay = 50) => {
    if (!shouldAnimate.value) return 0
    return calculateStagger(index, baseDelay)
  }

  /**
   * Create stagger config for array
   * @param {number} count
   * @param {Object} options
   * @returns {Array}
   */
  const createStagger = (count, options = {}) => {
    if (!shouldAnimate.value) {
      return Array(count).fill({ delay: 0, duration: 0 })
    }
    return createStaggerConfig(count, options)
  }

  /**
   * Get spring animation config
   * @param {string} preset
   * @returns {Object}
   */
  const getSpringConfig = (preset = 'gentle') => {
    if (!shouldAnimate.value) {
      return { duration: 0 }
    }
    return SPRING_PRESETS[preset] || SPRING_PRESETS.gentle
  }

  /**
   * Get CSS easing function
   * @param {string} preset
   * @returns {string}
   */
  const getCSSEasing = (preset = 'gentle') => {
    if (!shouldAnimate.value) return 'linear'
    return getEasing(preset)
  }

  /**
   * Get animation duration
   * @param {string} type
   * @returns {number}
   */
  const getAnimationDuration = (type = 'default') => {
    if (!shouldAnimate.value) return 0
    return getDuration(type)
  }

  /**
   * Create fade-in animation style
   * @param {number} index
   * @param {number} baseDelay
   * @returns {Object}
   */
  const fadeInStyle = (index, baseDelay = 50) => {
    if (!shouldAnimate.value) {
      return { opacity: 1 }
    }

    const delay = getStaggerDelay(index, baseDelay)
    return {
      animation: `fade-in 0.3s ease-out ${delay}ms forwards`,
      opacity: 0
    }
  }

  /**
   * Create slide-up animation style
   * @param {number} index
   * @param {number} baseDelay
   * @returns {Object}
   */
  const slideUpStyle = (index, baseDelay = 50) => {
    if (!shouldAnimate.value) {
      return { opacity: 1, transform: 'translateY(0)' }
    }

    const delay = getStaggerDelay(index, baseDelay)
    return {
      animation: `slide-up 0.4s ease-out ${delay}ms forwards`,
      opacity: 0,
      transform: 'translateY(20px)'
    }
  }

  /**
   * Create scale-in animation style
   * @param {number} index
   * @param {number} baseDelay
   * @returns {Object}
   */
  const scaleInStyle = (index, baseDelay = 50) => {
    if (!shouldAnimate.value) {
      return { opacity: 1, transform: 'scale(1)' }
    }

    const delay = getStaggerDelay(index, baseDelay)
    return {
      animation: `scale-in 0.3s ease-out ${delay}ms forwards`,
      opacity: 0,
      transform: 'scale(0.95)'
    }
  }

  /**
   * Create pulse animation class
   * @param {boolean} shouldPulse
   * @returns {string}
   */
  const pulseClass = (shouldPulse) => {
    if (!shouldAnimate.value || !shouldPulse) return ''
    return 'animate-pulse-glow'
  }

  /**
   * Disable animations temporarily
   * Useful for bulk updates
   */
  const disableTemporarily = (callback, duration = 500) => {
    const wasEnabled = uiStore.animations.enableAnimations
    uiStore.setAnimationsEnabled(false)
    
    callback()
    
    setTimeout(() => {
      uiStore.setAnimationsEnabled(wasEnabled)
    }, duration)
  }

  return {
    // State
    shouldAnimate,
    
    // Methods
    getStaggerDelay,
    createStagger,
    getSpringConfig,
    getCSSEasing,
    getAnimationDuration,
    
    // Style helpers
    fadeInStyle,
    slideUpStyle,
    scaleInStyle,
    pulseClass,
    
    // Utilities
    disableTemporarily
  }
}






