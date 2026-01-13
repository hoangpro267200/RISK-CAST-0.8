import { computed } from 'vue'
import { useRiskStore } from '../stores/riskStore'
import { useWhatIfStore } from '../stores/whatIfStore'
import { calculateDelayImpact } from '../utils/risk/delayCalculator'
import { clamp } from '../utils/formatters/numberFormatter'

/**
 * What-if simulation engine composable
 * Performs local score recalculations without backend calls
 */
export function useWhatIfEngine() {
  const riskStore = useRiskStore()
  const whatIfStore = useWhatIfStore()

  /**
   * Parameter sensitivity configurations
   * Maps parameter IDs to their impact factors
   */
  const parameterSensitivity = {
    weather_severity: {
      affectedLayers: ['weather', 'environmental'],
      sensitivity: 0.5,
      maxImpact: 20
    },
    port_congestion: {
      affectedLayers: ['port_congestion', 'operational'],
      sensitivity: 0.6,
      maxImpact: 15
    },
    sanctions_exposure: {
      affectedLayers: ['sanctions', 'geopolitical'],
      sensitivity: 0.8,
      maxImpact: 25
    },
    carrier_reliability: {
      affectedLayers: ['carrier_reliability', 'operational'],
      sensitivity: -0.4, // Negative: higher reliability = lower risk
      maxImpact: 10
    },
    insurance_coverage: {
      affectedLayers: ['financial'],
      sensitivity: -0.3,
      maxImpact: 8
    }
  }

  /**
   * Compute adjusted overall score
   * @returns {number}
   */
  function computeAdjustedScore() {
    const baseline = riskStore.baseline.overallScore
    const changes = whatIfStore.parameterChanges

    let totalDelta = 0

    changes.forEach(change => {
      const config = parameterSensitivity[change.id]
      if (!config) return

      // Calculate impact based on delta and sensitivity
      const impact = change.delta * config.sensitivity
      const clampedImpact = clamp(impact, -config.maxImpact, config.maxImpact)
      
      totalDelta += clampedImpact
    })

    const adjusted = baseline + totalDelta
    return Math.round(clamp(adjusted, 0, 100))
  }

  /**
   * Compute adjusted layer scores
   * @returns {Array}
   */
  function computeLayerScores() {
    const baseLayers = riskStore.layers
    const changes = whatIfStore.parameterChanges

    return baseLayers.map(layer => {
      let layerDelta = 0

      changes.forEach(change => {
        const config = parameterSensitivity[change.id]
        if (!config) return

        // Check if this parameter affects this layer
        if (config.affectedLayers.includes(layer.id)) {
          const impact = change.delta * config.sensitivity
          layerDelta += impact
        }
      })

      const adjustedScore = layer.score + layerDelta
      return {
        id: layer.id,
        name: layer.name,
        score: Math.round(clamp(adjustedScore, 0, 100))
      }
    })
  }

  /**
   * Compute delay impact from adjusted score
   * @param {number} adjustedScore
   * @returns {Object}
   */
  function computeDelayImpact(adjustedScore) {
    return calculateDelayImpact(adjustedScore)
  }

  /**
   * Compute adjusted ESG scores
   * @returns {Object}
   */
  function computeESGScores() {
    // For now, return baseline ESG
    // In full implementation, map parameters to ESG impacts
    return riskStore.esg
  }

  /**
   * Recalculate all simulation results
   */
  function recalculate() {
    whatIfStore.setSimulating(true)

    try {
      const overallScore = computeAdjustedScore()
      const layers = computeLayerScores()
      const delay = computeDelayImpact(overallScore)
      const esg = computeESGScores()

      whatIfStore.setSimulatedResults({
        overallScore,
        layers,
        delay: delay.expected,
        esg
      })
    } finally {
      whatIfStore.setSimulating(false)
    }
  }

  /**
   * Get parameter configuration
   * @param {string} paramId
   * @returns {Object|null}
   */
  function getParameterConfig(paramId) {
    return parameterSensitivity[paramId] || null
  }

  /**
   * Computed: Current simulated results
   */
  const simulatedResults = computed(() => {
    return whatIfStore.simulatedResults
  })

  /**
   * Computed: Score difference
   */
  const scoreDifference = computed(() => {
    if (!whatIfStore.simulatedResults.overallScore) return 0
    return whatIfStore.simulatedResults.overallScore - riskStore.baseline.overallScore
  })

  /**
   * Computed: Delay difference
   */
  const delayDifference = computed(() => {
    if (!whatIfStore.simulatedResults.delay) return 0
    return whatIfStore.simulatedResults.delay - riskStore.delayPrediction.expected
  })

  return {
    // Methods
    computeAdjustedScore,
    computeLayerScores,
    computeDelayImpact,
    computeESGScores,
    recalculate,
    getParameterConfig,
    
    // Computed
    simulatedResults,
    scoreDifference,
    delayDifference
  }
}






