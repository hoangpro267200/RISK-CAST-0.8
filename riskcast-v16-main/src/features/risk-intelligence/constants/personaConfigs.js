/**
 * Persona-based view configurations
 * Each role sees different metrics and detail levels
 */

export const PERSONA_TYPES = {
  LOGISTICS: 'logistics',
  EXECUTIVE: 'executive',
  ANALYST: 'analyst',
  COMPLIANCE: 'compliance'
}

export const PERSONA_CONFIGS = {
  [PERSONA_TYPES.LOGISTICS]: {
    id: PERSONA_TYPES.LOGISTICS,
    name: 'Logistics Manager',
    icon: '📦',
    description: 'Operational focus with all metrics',
    priorityMetrics: ['overall', 'delay', 'layers', 'timeline'],
    hiddenSections: [],
    treeDepth: 3,
    showMonteCarloDetail: true,
    showShockScenarios: true,
    cardOrder: [
      'overall',
      'delay',
      'layers',
      'categories',
      'monteCarlo',
      'shockScenarios',
      'esg'
    ]
  },
  
  [PERSONA_TYPES.EXECUTIVE]: {
    id: PERSONA_TYPES.EXECUTIVE,
    name: 'Executive',
    icon: '👔',
    description: 'High-level overview and strategic metrics',
    priorityMetrics: ['overall', 'esg', 'delay'],
    hiddenSections: ['monteCarlo', 'shockScenarios'],
    treeDepth: 1,
    showMonteCarloDetail: false,
    showShockScenarios: false,
    cardOrder: [
      'overall',
      'esg',
      'delay',
      'categories'
    ]
  },
  
  [PERSONA_TYPES.ANALYST]: {
    id: PERSONA_TYPES.ANALYST,
    name: 'Risk Analyst',
    icon: '📊',
    description: 'Deep dive with all technical details',
    priorityMetrics: ['all'],
    hiddenSections: [],
    treeDepth: 5,
    showMonteCarloDetail: true,
    showShockScenarios: true,
    cardOrder: [
      'overall',
      'layers',
      'categories',
      'monteCarlo',
      'delay',
      'shockScenarios',
      'esg'
    ]
  },
  
  [PERSONA_TYPES.COMPLIANCE]: {
    id: PERSONA_TYPES.COMPLIANCE,
    name: 'Compliance Officer',
    icon: '⚖️',
    description: 'Regulatory and ESG focus',
    priorityMetrics: ['esg', 'compliance_layers', 'overall'],
    hiddenSections: ['monteCarlo'],
    treeDepth: 2,
    showMonteCarloDetail: false,
    showShockScenarios: true,
    highlightedLayers: ['regulatory', 'sanctions', 'aml', 'customs', 'compliance'],
    cardOrder: [
      'esg',
      'overall',
      'layers',
      'categories',
      'delay',
      'shockScenarios'
    ]
  }
}

export const DEFAULT_PERSONA = PERSONA_TYPES.LOGISTICS

export function getPersonaConfig(personaType) {
  return PERSONA_CONFIGS[personaType] || PERSONA_CONFIGS[DEFAULT_PERSONA]
}

export function isMetricVisible(personaType, metricId) {
  const config = getPersonaConfig(personaType)
  if (config.priorityMetrics.includes('all')) return true
  return config.priorityMetrics.includes(metricId)
}

export function shouldShowSection(personaType, sectionId) {
  const config = getPersonaConfig(personaType)
  return !config.hiddenSections.includes(sectionId)
}






