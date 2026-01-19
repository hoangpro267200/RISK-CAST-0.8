import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  BREAKPOINTS, 
  getCurrentBreakpoint, 
  isMobile, 
  isTablet, 
  isDesktop 
} from '../constants/layoutBreakpoints'

/**
 * Responsive breakpoint composable
 * Provides reactive breakpoint detection
 */
export function useResponsive() {
  const currentBreakpoint = ref(getCurrentBreakpoint())
  const windowWidth = ref(window.innerWidth)
  const windowHeight = ref(window.innerHeight)

  // Computed breakpoint checks
  const mobile = computed(() => isMobile())
  const tablet = computed(() => isTablet())
  const desktop = computed(() => isDesktop())

  const xs = computed(() => windowWidth.value < BREAKPOINTS.sm)
  const sm = computed(() => windowWidth.value >= BREAKPOINTS.sm && windowWidth.value < BREAKPOINTS.md)
  const md = computed(() => windowWidth.value >= BREAKPOINTS.md && windowWidth.value < BREAKPOINTS.lg)
  const lg = computed(() => windowWidth.value >= BREAKPOINTS.lg && windowWidth.value < BREAKPOINTS.xl)
  const xl = computed(() => windowWidth.value >= BREAKPOINTS.xl && windowWidth.value < BREAKPOINTS['2xl'])
  const xxl = computed(() => windowWidth.value >= BREAKPOINTS['2xl'])

  /**
   * Update dimensions
   */
  function updateDimensions() {
    windowWidth.value = window.innerWidth
    windowHeight.value = window.innerHeight
    currentBreakpoint.value = getCurrentBreakpoint()
  }

  /**
   * Debounced resize handler
   */
  let resizeTimeout = null
  function handleResize() {
    if (resizeTimeout) clearTimeout(resizeTimeout)
    resizeTimeout = setTimeout(() => {
      updateDimensions()
    }, 150)
  }

  /**
   * Get grid columns for current breakpoint
   */
  const gridColumns = computed(() => {
    if (mobile.value) return 1
    if (tablet.value) return 2
    return 3
  })

  /**
   * Get card gap for current breakpoint
   */
  const cardGap = computed(() => {
    if (mobile.value) return 16
    if (tablet.value) return 20
    return 24
  })

  /**
   * Check if breakpoint matches
   * @param {string|Array} breakpoints
   * @returns {boolean}
   */
  function matchesBreakpoint(breakpoints) {
    const bp = Array.isArray(breakpoints) ? breakpoints : [breakpoints]
    return bp.includes(currentBreakpoint.value)
  }

  /**
   * Get value based on breakpoint
   * @param {Object} values - Breakpoint-value pairs
   * @returns {*}
   */
  function getBreakpointValue(values) {
    // Check from largest to smallest
    if (xxl.value && values['2xl']) return values['2xl']
    if (xl.value && values.xl) return values.xl
    if (lg.value && values.lg) return values.lg
    if (md.value && values.md) return values.md
    if (sm.value && values.sm) return values.sm
    if (xs.value && values.xs) return values.xs
    
    // Fallback
    return values.default || null
  }

  /**
   * Check if orientation is portrait
   */
  const isPortrait = computed(() => {
    return windowHeight.value > windowWidth.value
  })

  /**
   * Check if orientation is landscape
   */
  const isLandscape = computed(() => {
    return windowWidth.value > windowHeight.value
  })

  // Lifecycle
  onMounted(() => {
    window.addEventListener('resize', handleResize)
    updateDimensions()
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    if (resizeTimeout) clearTimeout(resizeTimeout)
  })

  return {
    // State
    currentBreakpoint,
    windowWidth,
    windowHeight,
    
    // Breakpoint checks
    mobile,
    tablet,
    desktop,
    xs,
    sm,
    md,
    lg,
    xl,
    xxl,
    
    // Orientation
    isPortrait,
    isLandscape,
    
    // Layout helpers
    gridColumns,
    cardGap,
    
    // Methods
    matchesBreakpoint,
    getBreakpointValue
  }
}






