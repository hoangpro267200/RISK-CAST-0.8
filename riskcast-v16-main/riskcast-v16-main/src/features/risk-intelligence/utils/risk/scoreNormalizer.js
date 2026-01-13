import { getRiskLevel } from './riskColorMap'
import { getRiskColor } from './riskColorMap'

/**
 * Transform backend risk data to UI format
 * Main data normalization layer
 * @param {Object} backendData - Raw backend response
 * @returns {Object} Normalized UI data
 */
export function normalizeRiskData(backendData) {
  if (!backendData) {
    throw new Error('Backend data is required')
  }

  return {
    baseline: normalizeBaseline(backendData),
    layers: normalizeLayers(backendData.layer_scores || []),
    categories: aggregateCategories(backendData.layer_scores || []),
    esg: normalizeESG(backendData.esg || {}),
    monteCarlo: normalizeMonteCarlo(backendData.monte_carlo || {}),
    delayPrediction: normalizeDelayPrediction(backendData.delay_prediction || {}),
    shockScenarios: normalizeShockScenarios(backendData.shock_scenarios || []),
    driverTree: buildDriverTree(backendData.risk_drivers || []),
    timeline: normalizeTimeline(backendData.timeline || {})
  }
}

/**
 * Normalize baseline risk data
 * @param {Object} data
 * @returns {Object}
 */
function normalizeBaseline(data) {
  const score = data.overall_risk_score || 0
  return {
    overallScore: score,
    riskLevel: getRiskLevel(score),
    timestamp: new Date(data.calculated_at || Date.now()),
    shipmentId: data.shipment_id || null
  }
}

/**
 * Normalize layer scores
 * @param {Array} layers
 * @returns {Array}
 */
function normalizeLayers(layers) {
  return layers
    .map(layer => ({
      id: layer.layer_id || generateId(),
      name: formatLayerName(layer.layer_name || 'Unknown Layer'),
      score: layer.score || 0,
      description: layer.description || '',
      factors: layer.top_factors || [],
      weight: layer.weight || 0,
      level: getRiskLevel(layer.score || 0),
      color: getRiskColor(layer.score || 0).bg
    }))
    .sort((a, b) => b.score - a.score) // Sort by score descending
}

/**
 * Aggregate layers into categories
 * @param {Array} layers
 * @returns {Array}
 */
function aggregateCategories(layers) {
  const categoryMap = {
    geopolitical: ['sanctions', 'conflict', 'political_stability', 'geopolitical'],
    environmental: ['weather', 'climate', 'natural_disaster', 'environmental'],
    operational: ['port_congestion', 'carrier_reliability', 'capacity', 'operational'],
    financial: ['currency', 'fuel_price', 'insurance', 'financial'],
    compliance: ['regulatory', 'customs', 'aml', 'compliance']
  }

  const categories = {}

  // Initialize categories
  Object.keys(categoryMap).forEach(cat => {
    categories[cat] = {
      id: cat,
      name: formatCategoryName(cat),
      scores: [],
      weights: []
    }
  })

  // Map layers to categories
  layers.forEach(layer => {
    const layerId = (layer.layer_id || layer.layer_name || '').toLowerCase()
    
    for (const [category, keywords] of Object.entries(categoryMap)) {
      if (keywords.some(keyword => layerId.includes(keyword))) {
        categories[category].scores.push(layer.score || 0)
        categories[category].weights.push(layer.weight || 1)
        break
      }
    }
  })

  // Calculate weighted averages
  return Object.values(categories)
    .map(cat => {
      const totalWeight = cat.weights.reduce((sum, w) => sum + w, 0)
      const weightedSum = cat.scores.reduce((sum, score, i) => {
        return sum + (score * cat.weights[i])
      }, 0)
      
      const score = totalWeight > 0 ? weightedSum / totalWeight : 0
      
      return {
        id: cat.id,
        name: cat.name,
        score: Math.round(score),
        weight: totalWeight,
        count: cat.scores.length
      }
    })
    .filter(cat => cat.count > 0)
    .sort((a, b) => b.score - a.score)
}

/**
 * Normalize ESG scores
 * @param {Object} esg
 * @returns {Object}
 */
function normalizeESG(esg) {
  return {
    environmental: esg.e_score || esg.environmental || 0,
    social: esg.s_score || esg.social || 0,
    governance: esg.g_score || esg.governance || 0
  }
}

/**
 * Normalize Monte Carlo distribution
 * @param {Object} mc
 * @returns {Object}
 */
function normalizeMonteCarlo(mc) {
  return {
    p50: mc.p50 || 0,
    p95: mc.p95 || 0,
    distribution: mc.distribution || []
  }
}

/**
 * Normalize delay prediction
 * @param {Object} delay
 * @returns {Object}
 */
function normalizeDelayPrediction(delay) {
  return {
    expected: delay.expected_days || delay.expected || 0,
    min: delay.min_days || delay.min || 0,
    max: delay.max_days || delay.max || 0,
    unit: 'days',
    confidence: delay.confidence || 0.5
  }
}

/**
 * Normalize shock scenarios
 * @param {Array} scenarios
 * @returns {Array}
 */
function normalizeShockScenarios(scenarios) {
  return scenarios.map(s => ({
    id: s.scenario_id || s.id || generateId(),
    name: s.scenario_name || s.name || 'Unknown Scenario',
    impact: s.impact_score || s.impact || 0,
    probability: s.probability || 0,
    description: s.description || ''
  }))
}

/**
 * Build hierarchical driver tree from flat list
 * @param {Array} drivers
 * @returns {Object}
 */
function buildDriverTree(drivers) {
  if (!drivers || drivers.length === 0) {
    return {
      id: 'root',
      name: 'Overall Risk',
      score: 0,
      children: []
    }
  }

  // If already hierarchical, return as is
  if (drivers[0] && drivers[0].children !== undefined) {
    return drivers[0]
  }

  // Build hierarchy from flat list
  const root = {
    id: 'root',
    name: 'Overall Risk',
    score: 0,
    children: []
  }

  // Group by category
  const categoryGroups = {}
  
  drivers.forEach(driver => {
    const category = driver.category || 'other'
    if (!categoryGroups[category]) {
      categoryGroups[category] = []
    }
    categoryGroups[category].push(driver)
  })

  // Build tree structure
  Object.entries(categoryGroups).forEach(([category, items]) => {
    const categoryNode = {
      id: category,
      name: formatCategoryName(category),
      score: Math.round(items.reduce((sum, item) => sum + (item.score || 0), 0) / items.length),
      children: items.map(item => ({
        id: item.id || generateId(),
        name: item.name || 'Unknown',
        score: item.score || 0,
        weight: item.weight || 1,
        children: []
      }))
    }
    root.children.push(categoryNode)
  })

  return root
}

/**
 * Normalize timeline data
 * @param {Object} timeline
 * @returns {Object}
 */
function normalizeTimeline(timeline) {
  return {
    phases: (timeline.phases || []).map(p => ({
      id: p.phase_id || p.id || generateId(),
      name: p.phase_name || p.name || 'Unknown Phase',
      start: p.start_date || p.start,
      end: p.end_date || p.end,
      riskLevel: p.risk_level || 'low'
    })),
    events: (timeline.events || []).map(e => ({
      id: e.event_id || e.id || generateId(),
      date: e.event_date || e.date,
      type: e.event_type || e.type || 'unknown',
      severity: e.severity || 'low',
      description: e.description || ''
    }))
  }
}

/**
 * Format layer name (snake_case to Title Case)
 * @param {string} name
 * @returns {string}
 */
function formatLayerName(name) {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase())
}

/**
 * Format category name
 * @param {string} name
 * @returns {string}
 */
function formatCategoryName(name) {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase())
}

/**
 * Generate unique ID
 * @returns {string}
 */
function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export default {
  normalizeRiskData,
  normalizeBaseline,
  normalizeLayers,
  aggregateCategories,
  normalizeESG,
  normalizeMonteCarlo,
  normalizeDelayPrediction,
  normalizeShockScenarios,
  buildDriverTree,
  normalizeTimeline
}






