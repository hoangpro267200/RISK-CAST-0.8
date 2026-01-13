/**
 * Design system color palette
 * VisionOS aesthetic with glassmorphism + neon accents
 */

export const RISK_COLORS = {
  low: {
    bg: '#10B981',
    text: '#ECFDF5',
    glow: '#10B981',
    gradient: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
    range: [0, 25]
  },
  medium: {
    bg: '#F59E0B',
    text: '#FFFBEB',
    glow: '#F59E0B',
    gradient: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
    range: [26, 50]
  },
  high: {
    bg: '#F97316',
    text: '#FFF7ED',
    glow: '#F97316',
    gradient: 'linear-gradient(135deg, #F97316 0%, #EA580C 100%)',
    range: [51, 75]
  },
  critical: {
    bg: '#EF4444',
    text: '#FEF2F2',
    glow: '#EF4444',
    gradient: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
    range: [76, 100]
  }
}

export const NEON_COLORS = {
  blue: '#4FC3F7',
  cyan: '#00BCD4',
  purple: '#9C27B0',
  pink: '#E91E63',
  green: '#00E676',
  yellow: '#FFD600',
  orange: '#FF6D00'
}

export const GLASSMORPHISM = {
  background: {
    default: 'rgba(255, 255, 255, 0.05)',
    hero: 'rgba(255, 255, 255, 0.08)',
    elevated: 'rgba(255, 255, 255, 0.1)'
  },
  border: {
    default: 'rgba(255, 255, 255, 0.1)',
    elevated: 'rgba(255, 255, 255, 0.15)',
    strong: 'rgba(255, 255, 255, 0.2)'
  },
  blur: {
    default: '24px',
    strong: '32px',
    subtle: '16px'
  }
}

export const ESG_COLORS = {
  environmental: {
    bg: '#10B981',
    text: '#ECFDF5',
    icon: '🌍'
  },
  social: {
    bg: '#3B82F6',
    text: '#EFF6FF',
    icon: '👥'
  },
  governance: {
    bg: '#8B5CF6',
    text: '#F5F3FF',
    icon: '⚖️'
  }
}

export const CATEGORY_COLORS = {
  geopolitical: {
    bg: '#EF4444',
    text: '#FEF2F2',
    icon: '🌐'
  },
  environmental: {
    bg: '#10B981',
    text: '#ECFDF5',
    icon: '🌿'
  },
  operational: {
    bg: '#F59E0B',
    text: '#FFFBEB',
    icon: '⚙️'
  },
  financial: {
    bg: '#3B82F6',
    text: '#EFF6FF',
    icon: '💰'
  },
  compliance: {
    bg: '#8B5CF6',
    text: '#F5F3FF',
    icon: '📋'
  }
}

export const SEVERITY_COLORS = {
  info: {
    bg: '#3B82F6',
    text: '#EFF6FF',
    border: '#60A5FA'
  },
  low: {
    bg: '#10B981',
    text: '#ECFDF5',
    border: '#34D399'
  },
  medium: {
    bg: '#F59E0B',
    text: '#FFFBEB',
    border: '#FBBF24'
  },
  high: {
    bg: '#F97316',
    text: '#FFF7ED',
    border: '#FB923C'
  },
  critical: {
    bg: '#EF4444',
    text: '#FEF2F2',
    border: '#F87171'
  }
}

export const CHART_COLORS = {
  primary: ['#4FC3F7', '#00BCD4', '#3B82F6', '#8B5CF6', '#9C27B0'],
  risk: ['#10B981', '#F59E0B', '#F97316', '#EF4444'],
  sequential: ['#1E293B', '#334155', '#475569', '#64748B', '#94A3B8', '#CBD5E1'],
  diverging: ['#10B981', '#34D399', '#F59E0B', '#FBBF24', '#EF4444', '#DC2626']
}

export const GRADIENT_PRESETS = {
  riskLowToHigh: 'linear-gradient(90deg, #10B981 0%, #F59E0B 33%, #F97316 66%, #EF4444 100%)',
  blueToCyan: 'linear-gradient(135deg, #4FC3F7 0%, #00BCD4 100%)',
  purpleToPink: 'linear-gradient(135deg, #9C27B0 0%, #E91E63 100%)',
  glass: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)'
}






