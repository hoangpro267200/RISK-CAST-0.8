import { computed } from 'vue'
import { usePersonaStore } from '../stores/personaStore'
import { useRiskStore } from '../stores/riskStore'

/**
 * Persona view composable
 * Provides persona-filtered views of data
 */
export function usePersonaView() {
  const personaStore = usePersonaStore()
  const riskStore = useRiskStore()

  /**
   * Get filtered layers based on active persona
   */
  const filteredLayers = computed(() => {
    const layers = riskStore.layers
    const highlighted = personaStore.highlightedLayers

    if (highlighted.length === 0) {
      return layers
    }

    return layers.map(layer => ({
      ...layer,
      highlighted: highlighted.includes(layer.id)
    }))
  })

  /**
   * Get visible cards based on persona
   */
  const visibleCards = computed(() => {
    const order = personaStore.cardOrder
    const shouldShow = personaStore.shouldShowSection

    return order.filter(cardId => shouldShow(cardId))
  })

  /**
   * Get tree max depth for persona
   */
  const maxTreeDepth = computed(() => {
    return personaStore.treeDepth
  })

  /**
   * Check if metric is visible
   */
  const isMetricVisible = (metricId) => {
    return personaStore.isMetricVisible(metricId)
  }

  /**
   * Check if section should be shown
   */
  const shouldShowSection = (sectionId) => {
    return personaStore.shouldShowSection(sectionId)
  }

  /**
   * Switch persona
   */
  const switchPersona = (personaType) => {
    personaStore.setPersona(personaType)
  }

  /**
   * Get persona config
   */
  const currentPersona = computed(() => {
    return personaStore.currentConfig
  })

  /**
   * Get persona name
   */
  const personaName = computed(() => {
    return personaStore.currentConfig.name
  })

  /**
   * Get persona icon
   */
  const personaIcon = computed(() => {
    return personaStore.currentConfig.icon
  })

  return {
    // Data
    filteredLayers,
    visibleCards,
    maxTreeDepth,
    currentPersona,
    personaName,
    personaIcon,
    
    // Methods
    isMetricVisible,
    shouldShowSection,
    switchPersona
  }
}






