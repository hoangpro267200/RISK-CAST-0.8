/**
 * RiskCast V22 - Risk Color Mapping Utility
 * ==========================================
 * Provides consistent color mapping for risk scores across all UI components
 * 
 * Design System: VisionOS-glass / Neon SaaS 2025
 */

export const getRiskColor = (score) => {
  if (score < 30) return {
    primary: '#10B981', // Emerald green
    secondary: '#059669',
    glow: 'rgba(16, 185, 129, 0.4)',
    level: 'low',
    label: 'LOW RISK'
  };
  
  if (score < 50) return {
    primary: '#F59E0B', // Amber
    secondary: '#D97706',
    glow: 'rgba(245, 158, 11, 0.4)',
    level: 'medium',
    label: 'MEDIUM RISK'
  };
  
  if (score < 70) return {
    primary: '#EF4444', // Red
    secondary: '#DC2626',
    glow: 'rgba(239, 68, 68, 0.4)',
    level: 'high',
    label: 'HIGH RISK'
  };
  
  return {
    primary: '#DC2626', // Deep red
    secondary: '#991B1B',
    glow: 'rgba(220, 38, 38, 0.6)',
    level: 'critical',
    label: 'CRITICAL RISK'
  };
};

export const getGradient = (score) => {
  const colors = getRiskColor(score);
  return `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%)`;
};

export const getNeonGlow = (score) => {
  const colors = getRiskColor(score);
  return `0 0 20px ${colors.glow}, 0 0 40px ${colors.glow}`;
};

export const categoryColors = {
  transport: '#4FC3F7', // Cyan
  cargo: '#FFB74D',     // Orange
  commercial: '#BA68C8', // Purple
  compliance: '#4DB6AC', // Teal
  external: '#E57373'    // Light Red
};

export const esgColors = {
  environmental: '#66BB6A', // Green
  social: '#42A5F5',        // Blue
  governance: '#AB47BC'     // Purple
};






