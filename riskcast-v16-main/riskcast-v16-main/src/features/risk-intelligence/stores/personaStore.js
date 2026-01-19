import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { PERSONA_TYPES, PERSONA_CONFIGS, DEFAULT_PERSONA } from '../constants/personaConfigs'

/**
 * Persona store
 * Manages active persona and view configurations
 */
export const usePersonaStore = defineStore('persona', () => {
  // State
  const activePersona = ref(DEFAULT_PERSONA)

  // Getters
  const currentConfig = computed(() => {
    return PERSONA_CONFIGS[activePersona.value] || PERSONA_CONFIGS[DEFAULT_PERSONA]
  })

  const isMetricVisible = computed(() => {
    return (metricId) => {
      const config = currentConfig.value
      if (config.priorityMetrics.includes('all')) return true
      return config.priorityMetrics.includes(metricId)
    }
  })

  const shouldShowSection = computed(() => {
    return (sectionId) => {
      const config = currentConfig.value
      return !config.hiddenSections.includes(sectionId)
    }
  })

  const cardOrder = computed(() => {
    return currentConfig.value.cardOrder || []
  })

  const treeDepth = computed(() => {
    return currentConfig.value.treeDepth || 3
  })

  const showMonteCarloDetail = computed(() => {
    return currentConfig.value.showMonteCarloDetail !== false
  })

  const showShockScenarios = computed(() => {
    return currentConfig.value.showShockScenarios !== false
  })

  const highlightedLayers = computed(() => {
    return currentConfig.value.highlightedLayers || []
  })

  // Actions
  function setPersona(personaType) {
    if (PERSONA_CONFIGS[personaType]) {
      activePersona.value = personaType
    }
  }

  function resetToDefault() {
    activePersona.value = DEFAULT_PERSONA
  }

  return {
    // State
    activePersona,
    
    // Getters
    currentConfig,
    isMetricVisible,
    shouldShowSection,
    cardOrder,
    treeDepth,
    showMonteCarloDetail,
    showShockScenarios,
    highlightedLayers,
    
    // Actions
    setPersona,
    resetToDefault
  }
})






