/**
 * Unified Design Tokens
 * 
 * Exports CSS vars as TypeScript constants for use in React components.
 * This ensures consistent typography, spacing, colors across Input/Summary/Results pages.
 * 
 * Source: /app/static/css/tokens.css
 */

/**
 * Spacing scale (from CSS vars --space-*)
 */
export const spacing = {
  xs: 'var(--space-4)',    // 4px
  sm: 'var(--space-8)',    // 8px
  md: 'var(--space-12)',   // 12px
  lg: 'var(--space-16)',   // 16px
  xl: 'var(--space-20)',   // 20px
  '2xl': 'var(--space-24)', // 24px
  '3xl': 'var(--space-32)', // 32px
  '4xl': 'var(--space-40)', // 40px
  '5xl': 'var(--space-48)', // 48px
} as const;

/**
 * Typography scale (from CSS vars --font-*)
 */
export const typography = {
  fontFamily: 'var(--font-family)',
  display: 'var(--font-display)',   // 48px/1.1
  h1: 'var(--font-h1)',              // 32px/1.15
  h2: 'var(--font-h2)',              // 24px/1.2
  bodyLg: 'var(--font-body-lg)',     // 18px/1.5
  body: 'var(--font-body)',          // 16px/1.55
  caption: 'var(--font-caption)',    // 13px/1.4
  label: 'var(--font-label)',        // 12px/1.35
} as const;

/**
 * Colors (from CSS vars)
 */
export const colors = {
  // Primary palette
  primaryNeon: 'var(--color-primary-neon)',  // #6ef3ff
  accent: 'var(--color-accent)',             // #8b7bff
  accent2: 'var(--color-accent-2)',          // #39c1ff
  
  // Background layers
  bg0: 'var(--color-bg-0)',                  // #05070d
  bg1: 'var(--color-bg-1)',                  // rgba(16, 21, 35, 0.82)
  bg2: 'var(--color-bg-2)',                  // rgba(22, 28, 44, 0.72)
  bg3: 'var(--color-bg-3)',                  // rgba(28, 36, 54, 0.62)
  surface: 'var(--color-surface)',           // rgba(255, 255, 255, 0.04)
  
  // Glass layers
  glass1: 'var(--glass-1)',                  // rgba(255, 255, 255, 0.08)
  glass2: 'var(--glass-2)',                  // rgba(255, 255, 255, 0.12)
  glass3: 'var(--glass-3)',                  // rgba(255, 255, 255, 0.18)
  
  // Text tiers
  textStrong: 'var(--text-strong)',          // #f7fbff
  textMuted: 'var(--text-muted)',            // #c7d2e2
  textSoft: 'var(--text-soft)',              // #9aa6bd
  textDisabled: 'var(--text-disabled)',      // #6c7691
  
  // Status colors
  success: 'var(--status-success)',          // #5be8a9
  warning: 'var(--status-warning)',          // #f7c948
  danger: 'var(--status-danger)',            // #ff6b6b
  info: 'var(--status-info)',                // #61c9ff
  neutral: 'var(--status-neutral)',          // #9da8c3
} as const;

/**
 * Border radius (from CSS vars --radius-*)
 */
export const radii = {
  sm: 'var(--radius-8)',   // 8px
  md: 'var(--radius-12)',  // 12px
  lg: 'var(--radius-16)',  // 16px
  xl: 'var(--radius-20)',  // 20px
  '2xl': 'var(--radius-24)', // 24px
} as const;

/**
 * Transitions (from CSS vars --transition-*)
 */
export const transitions = {
  fast: 'var(--transition-fast)',    // 150ms
  normal: 'var(--transition)',       // 220ms
  slow: 'var(--transition-slow)',    // 400ms
} as const;

/**
 * Shadows (from CSS vars --shadow-*)
 */
export const shadows = {
  layered: 'var(--shadow-layered)',
  neon: 'var(--shadow-neon)',
  soft: 'var(--shadow-soft)',
} as const;

/**
 * Blur presets (from CSS vars --blur-*)
 */
export const blur = {
  sm: 'var(--blur-20)',  // blur(20px)
  md: 'var(--blur-30)',  // blur(30px)
} as const;

/**
 * Design tokens export (for direct use in components)
 */
export const designTokens = {
  spacing,
  typography,
  colors,
  radii,
  transitions,
  shadows,
  blur,
} as const;

export default designTokens;
