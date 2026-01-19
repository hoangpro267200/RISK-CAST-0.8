import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * Main risk data store
 * Manages all risk intelligence data
 */
export const useRiskStore = defineStore('risk', () => {
  // State
  const rawData = ref(null)
  const baseline = ref({
    overallScore: 0,
    riskLevel: 'low',
    timestamp: null,
    shipmentId: null
  })
  
  const layers = ref([])
  const categories = ref([])
  const esg = ref({
    environmental: 0,
    social: 0,
    governance: 0
  })
  
  const monteCarlo = ref({
    p50: 0,
    p95: 0,
    distribution: []
  })
  
  const delayPrediction = ref({
    expected: 0,
    min: 0,
    max: 0,
    unit: 'days',
    confidence: 0
  })
  
  const shockScenarios = ref([])
  const driverTree = ref({
    id: 'root',
    name: 'Overall Risk',
    score: 0,
    children: []
  })
  
  const timeline = ref({
    phases: [],
    events: []
  })
  
  // Meta
  const isLoading = ref(false)
  const error = ref(null)
  const lastFetched = ref(null)

  // Getters
  const visibleLayers = computed(() => {
    return (personaFilter) => {
      if (!personaFilter) return layers.value
      
      // Apply persona-specific filtering
      const config = personaFilter
      if (config.highlightedLayers) {
        return layers.value.map(layer => ({
          ...layer,
          highlighted: config.highlightedLayers.includes(layer.id)
        }))
      }
      
      return layers.value
    }
  })

  const topDrivers = computed(() => {
    return (n = 5) => {
      return [...layers.value]
        .sort((a, b) => b.score - a.score)
        .slice(0, n)
    }
  })

  const riskTrend = computed(() => {
    // Calculate trend from history if available
    // For now, return 0 (no change)
    return 0
  })

  const criticalEvents = computed(() => {
    return timeline.value.events.filter(event => 
      event.severity === 'critical' || event.severity === 'high'
    )
  })

  // Actions
  function setData(data) {
    rawData.value = data
    baseline.value = data.baseline || baseline.value
    layers.value = data.layers || []
    categories.value = data.categories || []
    esg.value = data.esg || esg.value
    monteCarlo.value = data.monteCarlo || monteCarlo.value
    delayPrediction.value = data.delayPrediction || delayPrediction.value
    shockScenarios.value = data.shockScenarios || []
    driverTree.value = data.driverTree || driverTree.value
    timeline.value = data.timeline || timeline.value
    lastFetched.value = new Date()
  }

  function setLoading(value) {
    isLoading.value = value
  }

  function setError(err) {
    error.value = err
  }

  function reset() {
    rawData.value = null
    layers.value = []
    categories.value = []
    shockScenarios.value = []
    timeline.value = { phases: [], events: [] }
    error.value = null
    isLoading.value = false
  }

  return {
    // State
    rawData,
    baseline,
    layers,
    categories,
    esg,
    monteCarlo,
    delayPrediction,
    shockScenarios,
    driverTree,
    timeline,
    isLoading,
    error,
    lastFetched,
    
    // Getters
    visibleLayers,
    topDrivers,
    riskTrend,
    criticalEvents,
    
    // Actions
    setData,
    setLoading,
    setError,
    reset
  }
})






