/**
 * Risk scoring thresholds and level definitions
 * Used across the entire V22 UI layer
 */

export const RISK_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
}

export const RISK_THRESHOLDS = {
  LOW: { min: 0, max: 25 },
  MEDIUM: { min: 26, max: 50 },
  HIGH: { min: 51, max: 75 },
  CRITICAL: { min: 76, max: 100 }
}

export const RISK_LABELS = {
  [RISK_LEVELS.LOW]: 'Low Risk',
  [RISK_LEVELS.MEDIUM]: 'Medium Risk',
  [RISK_LEVELS.HIGH]: 'High Risk',
  [RISK_LEVELS.CRITICAL]: 'Critical Risk'
}

export const ESG_THRESHOLDS = {
  POOR: { min: 0, max: 30 },
  FAIR: { min: 31, max: 50 },
  GOOD: { min: 51, max: 70 },
  EXCELLENT: { min: 71, max: 100 }
}

export const DELAY_THRESHOLDS = {
  MINIMAL: { min: 0, max: 2, label: 'Minimal' },
  MODERATE: { min: 3, max: 7, label: 'Moderate' },
  SIGNIFICANT: { min: 8, max: 14, label: 'Significant' },
  SEVERE: { min: 15, max: Infinity, label: 'Severe' }
}

export const CONFIDENCE_LEVELS = {
  LOW: 0.5,
  MEDIUM: 0.7,
  HIGH: 0.85,
  VERY_HIGH: 0.95
}

export const SEVERITY_LEVELS = {
  INFO: 'info',
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
}






