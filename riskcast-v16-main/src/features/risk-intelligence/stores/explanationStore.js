import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * AI explanation store
 * Manages AI-generated narratives and insights
 */
export const useExplanationStore = defineStore('explanation', () => {
  // State
  const narrative = ref({
    sections: []
  })
  
  const activeSection = ref(null)
  const isLoading = ref(false)

  // Getters
  const sections = computed(() => {
    return narrative.value.sections || []
  })

  const activeSectionData = computed(() => {
    if (!activeSection.value) return null
    return sections.value.find(s => s.id === activeSection.value)
  })

  const highlightedDrivers = computed(() => {
    if (!activeSectionData.value) return []
    return activeSectionData.value.linkedDriverIds || []
  })

  const allInsights = computed(() => {
    return sections.value.flatMap(s => s.insights || [])
  })

  const allRecommendations = computed(() => {
    return sections.value.flatMap(s => s.recommendations || [])
  })

  const criticalSections = computed(() => {
    return sections.value.filter(s => s.severity === 'critical' || s.severity === 'high')
  })

  // Actions
  function setNarrative(data) {
    narrative.value = data
  }

  function scrollToSection(sectionId) {
    activeSection.value = sectionId
    
    // Emit event for smooth scroll
    const event = new CustomEvent('scrollToSection', { 
      detail: { sectionId } 
    })
    window.dispatchEvent(event)
  }

  function clearActiveSection() {
    activeSection.value = null
  }

  function setLoading(value) {
    isLoading.value = value
  }

  function reset() {
    narrative.value = { sections: [] }
    activeSection.value = null
    isLoading.value = false
  }

  return {
    // State
    narrative,
    activeSection,
    isLoading,
    
    // Getters
    sections,
    activeSectionData,
    highlightedDrivers,
    allInsights,
    allRecommendations,
    criticalSections,
    
    // Actions
    setNarrative,
    scrollToSection,
    clearActiveSection,
    setLoading,
    reset
  }
})






