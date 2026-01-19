import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * What-if simulation store
 * Manages parameter adjustments and simulation results
 */
export const useWhatIfStore = defineStore('whatIf', () => {
  // State
  const baselineParams = ref(new Map())
  const adjustedParams = ref(new Map())
  
  const simulatedResults = ref({
    overallScore: null,
    layers: [],
    delay: null,
    esg: null
  })
  
  const isDirty = ref(false)
  const isSimulating = ref(false)

  // Getters
  const hasChanges = computed(() => {
    return isDirty.value
  })

  const parameterChanges = computed(() => {
    const changes = []
    
    adjustedParams.value.forEach((value, key) => {
      const baseline = baselineParams.value.get(key)
      if (baseline !== undefined && value !== baseline) {
        changes.push({
          id: key,
          from: baseline,
          to: value,
          delta: value - baseline
        })
      }
    })
    
    return changes
  })

  const resultsComparison = computed(() => {
    if (!simulatedResults.value.overallScore) return null
    
    return {
      baseline: baselineParams.value,
      adjusted: adjustedParams.value,
      results: simulatedResults.value
    }
  })

  // Actions
  function initializeParameters(params) {
    baselineParams.value = new Map(Object.entries(params))
    adjustedParams.value = new Map(Object.entries(params))
    isDirty.value = false
  }

  function updateParameter(paramId, newValue) {
    adjustedParams.value.set(paramId, newValue)
    isDirty.value = true
  }

  function setSimulatedResults(results) {
    simulatedResults.value = results
  }

  function setSimulating(value) {
    isSimulating.value = value
  }

  function reset() {
    adjustedParams.value = new Map(baselineParams.value)
    simulatedResults.value = {
      overallScore: null,
      layers: [],
      delay: null,
      esg: null
    }
    isDirty.value = false
  }

  function applyAsBaseline() {
    baselineParams.value = new Map(adjustedParams.value)
    isDirty.value = false
  }

  return {
    // State
    baselineParams,
    adjustedParams,
    simulatedResults,
    isDirty,
    isSimulating,
    
    // Getters
    hasChanges,
    parameterChanges,
    resultsComparison,
    
    // Actions
    initializeParameters,
    updateParameter,
    setSimulatedResults,
    setSimulating,
    reset,
    applyAsBaseline
  }
})






