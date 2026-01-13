/**
 * Responsive layout breakpoints
 * Matches Tailwind defaults with custom extensions
 */

export const BREAKPOINTS = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536
}

export const GRID_COLUMNS = {
  mobile: 4,
  tablet: 8,
  desktop: 12
}

export const CARD_LAYOUTS = {
  mobile: {
    columns: 1,
    gap: 16,
    padding: 16
  },
  tablet: {
    columns: 2,
    gap: 20,
    padding: 24
  },
  desktop: {
    columns: 3,
    gap: 24,
    padding: 32
  }
}

export const DASHBOARD_SPACING = {
  sectionGap: {
    mobile: 24,
    tablet: 32,
    desktop: 48
  },
  cardPadding: {
    mobile: 16,
    tablet: 20,
    desktop: 24
  },
  headerHeight: {
    mobile: 60,
    tablet: 72,
    desktop: 80
  }
}

export const VISUALIZATION_SIZES = {
  tree: {
    mobile: { width: 350, height: 400 },
    tablet: { width: 700, height: 600 },
    desktop: { width: 1000, height: 800 }
  },
  timeline: {
    mobile: { width: 350, height: 300 },
    tablet: { width: 700, height: 400 },
    desktop: { width: 1200, height: 500 }
  },
  monteCarlo: {
    mobile: { width: 300, height: 200 },
    tablet: { width: 400, height: 250 },
    desktop: { width: 500, height: 300 }
  }
}

export const Z_INDEX = {
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  modal: 1200,
  popover: 1300,
  tooltip: 1400,
  notification: 1500
}

export function getCurrentBreakpoint() {
  const width = window.innerWidth
  if (width >= BREAKPOINTS['2xl']) return '2xl'
  if (width >= BREAKPOINTS.xl) return 'xl'
  if (width >= BREAKPOINTS.lg) return 'lg'
  if (width >= BREAKPOINTS.md) return 'md'
  if (width >= BREAKPOINTS.sm) return 'sm'
  return 'xs'
}

export function isMobile() {
  return window.innerWidth < BREAKPOINTS.md
}

export function isTablet() {
  const width = window.innerWidth
  return width >= BREAKPOINTS.md && width < BREAKPOINTS.lg
}

export function isDesktop() {
  return window.innerWidth >= BREAKPOINTS.lg
}






