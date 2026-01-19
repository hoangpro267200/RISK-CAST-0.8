/**
 * Design Tokens
 * 
 * Centralized design system for RISKCAST.
 * - Risk severity colors
 * - Accent colors
 * - Typography scale
 * - Spacing scale
 * - Animation presets
 */

// =============================================================================
// COLOR TOKENS
// =============================================================================

/**
 * Risk severity colors (for visual risk indicators)
 */
export const riskColors = {
  critical: {
    bg: 'bg-red-500',
    bgSubtle: 'bg-red-500/10',
    text: 'text-red-400',
    border: 'border-red-500/30',
    gradient: 'from-red-600 to-red-500',
    hex: '#ef4444'
  },
  high: {
    bg: 'bg-orange-500',
    bgSubtle: 'bg-orange-500/10',
    text: 'text-orange-400',
    border: 'border-orange-500/30',
    gradient: 'from-orange-600 to-orange-500',
    hex: '#f97316'
  },
  medium: {
    bg: 'bg-amber-500',
    bgSubtle: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
    gradient: 'from-amber-600 to-amber-500',
    hex: '#f59e0b'
  },
  low: {
    bg: 'bg-emerald-500',
    bgSubtle: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
    gradient: 'from-emerald-600 to-emerald-500',
    hex: '#10b981'
  },
  unknown: {
    bg: 'bg-gray-500',
    bgSubtle: 'bg-gray-500/10',
    text: 'text-gray-400',
    border: 'border-gray-500/30',
    gradient: 'from-gray-600 to-gray-500',
    hex: '#6b7280'
  }
} as const;

/**
 * Get risk color tokens by level
 */
export function getRiskColorTokens(level: string) {
  const normalizedLevel = level?.toLowerCase() || 'unknown';
  
  if (normalizedLevel === 'critical' || normalizedLevel.includes('critical')) {
    return riskColors.critical;
  }
  if (normalizedLevel === 'high' || normalizedLevel.includes('high')) {
    return riskColors.high;
  }
  if (normalizedLevel === 'medium' || normalizedLevel.includes('medium') || normalizedLevel.includes('moderate')) {
    return riskColors.medium;
  }
  if (normalizedLevel === 'low' || normalizedLevel.includes('low')) {
    return riskColors.low;
  }
  
  return riskColors.unknown;
}

/**
 * Accent/UI colors
 */
export const accentColors = {
  primary: {
    bg: 'bg-blue-500',
    bgSubtle: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    gradient: 'from-blue-600 to-blue-500',
    hex: '#3b82f6'
  },
  secondary: {
    bg: 'bg-purple-500',
    bgSubtle: 'bg-purple-500/10',
    text: 'text-purple-400',
    border: 'border-purple-500/30',
    gradient: 'from-purple-600 to-purple-500',
    hex: '#a855f7'
  },
  success: {
    bg: 'bg-emerald-500',
    bgSubtle: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
    gradient: 'from-emerald-600 to-emerald-500',
    hex: '#10b981'
  },
  warning: {
    bg: 'bg-amber-500',
    bgSubtle: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
    gradient: 'from-amber-600 to-amber-500',
    hex: '#f59e0b'
  },
  danger: {
    bg: 'bg-red-500',
    bgSubtle: 'bg-red-500/10',
    text: 'text-red-400',
    border: 'border-red-500/30',
    gradient: 'from-red-600 to-red-500',
    hex: '#ef4444'
  },
  info: {
    bg: 'bg-cyan-500',
    bgSubtle: 'bg-cyan-500/10',
    text: 'text-cyan-400',
    border: 'border-cyan-500/30',
    gradient: 'from-cyan-600 to-cyan-500',
    hex: '#06b6d4'
  }
} as const;

// =============================================================================
// TYPOGRAPHY TOKENS
// =============================================================================

/**
 * Typography scale with Tailwind classes
 */
export const typography = {
  display: {
    className: 'text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight',
    size: '3rem',
    weight: '700',
    lineHeight: '1.1'
  },
  h1: {
    className: 'text-3xl sm:text-4xl font-bold tracking-tight',
    size: '2.25rem',
    weight: '700',
    lineHeight: '1.2'
  },
  h2: {
    className: 'text-2xl sm:text-3xl font-semibold',
    size: '1.875rem',
    weight: '600',
    lineHeight: '1.25'
  },
  h3: {
    className: 'text-xl sm:text-2xl font-semibold',
    size: '1.5rem',
    weight: '600',
    lineHeight: '1.3'
  },
  h4: {
    className: 'text-lg font-semibold',
    size: '1.125rem',
    weight: '600',
    lineHeight: '1.4'
  },
  body: {
    className: 'text-base font-normal',
    size: '1rem',
    weight: '400',
    lineHeight: '1.5'
  },
  bodySmall: {
    className: 'text-sm font-normal',
    size: '0.875rem',
    weight: '400',
    lineHeight: '1.5'
  },
  caption: {
    className: 'text-xs font-normal',
    size: '0.75rem',
    weight: '400',
    lineHeight: '1.4'
  },
  micro: {
    className: 'text-[10px] font-medium uppercase tracking-wider',
    size: '0.625rem',
    weight: '500',
    lineHeight: '1.2'
  },
  mono: {
    className: 'font-mono text-sm',
    size: '0.875rem',
    weight: '400',
    lineHeight: '1.5'
  }
} as const;

/**
 * Text color variants for dark theme
 */
export const textColors = {
  primary: 'text-white',
  secondary: 'text-white/80',
  tertiary: 'text-white/60',
  muted: 'text-white/40',
  disabled: 'text-white/30'
} as const;

// =============================================================================
// SPACING TOKENS
// =============================================================================

/**
 * Spacing scale (matching Tailwind)
 */
export const spacing = {
  xs: '0.25rem',   // 1
  sm: '0.5rem',    // 2
  md: '1rem',      // 4
  lg: '1.5rem',    // 6
  xl: '2rem',      // 8
  '2xl': '3rem',   // 12
  '3xl': '4rem',   // 16
  '4xl': '6rem',   // 24
} as const;

// =============================================================================
// ANIMATION TOKENS
// =============================================================================

/**
 * Animation timing presets
 */
export const animations = {
  fast: '150ms',
  normal: '200ms',
  slow: '300ms',
  verySlow: '500ms',
  
  easeOut: 'cubic-bezier(0.33, 1, 0.68, 1)',
  easeIn: 'cubic-bezier(0.32, 0, 0.67, 0)',
  easeInOut: 'cubic-bezier(0.65, 0, 0.35, 1)',
  spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)'
} as const;

// =============================================================================
// GLASSMORPHISM TOKENS
// =============================================================================

/**
 * Glass effect presets
 */
export const glassEffects = {
  light: {
    className: 'bg-white/5 backdrop-blur-lg border border-white/10',
    background: 'rgba(255, 255, 255, 0.05)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    blur: '16px'
  },
  medium: {
    className: 'bg-white/8 backdrop-blur-xl border border-white/15',
    background: 'rgba(255, 255, 255, 0.08)',
    borderColor: 'rgba(255, 255, 255, 0.15)',
    blur: '24px'
  },
  heavy: {
    className: 'bg-white/10 backdrop-blur-2xl border border-white/20',
    background: 'rgba(255, 255, 255, 0.1)',
    borderColor: 'rgba(255, 255, 255, 0.2)',
    blur: '40px'
  }
} as const;

// =============================================================================
// SHADOW TOKENS
// =============================================================================

/**
 * Shadow presets for dark theme
 */
export const shadows = {
  sm: 'shadow-lg shadow-black/20',
  md: 'shadow-xl shadow-black/25',
  lg: 'shadow-2xl shadow-black/30',
  glow: (color: string) => `shadow-lg shadow-${color}/25`
} as const;

export default {
  riskColors,
  getRiskColorTokens,
  accentColors,
  typography,
  textColors,
  spacing,
  animations,
  glassEffects,
  shadows
};
