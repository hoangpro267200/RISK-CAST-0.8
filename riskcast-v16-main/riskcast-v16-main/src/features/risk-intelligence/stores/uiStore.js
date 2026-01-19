import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * UI state store
 * Manages UI interactions and display states
 */
export const useUIStore = defineStore('ui', () => {
  // State - Tree
  const tree = ref({
    expandedNodes: new Set(),
    hoveredNode: null,
    selectedNode: null
  })

  // State - Timeline
  const timeline = ref({
    zoomLevel: 1,
    visibleDateRange: {
      start: null,
      end: null
    }
  })

  // State - Layout
  const layout = ref({
    sidebarCollapsed: false,
    activeTab: 'summary'
  })

  // State - Animations
  const animations = ref({
    enableAnimations: true,
    reducedMotion: false
  })

  // Getters - Tree
  const isNodeExpanded = computed(() => {
    return (nodeId) => tree.value.expandedNodes.has(nodeId)
  })

  const expandedNodesList = computed(() => {
    return Array.from(tree.value.expandedNodes)
  })

  // Getters - Timeline
  const timelineZoom = computed(() => {
    return timeline.value.zoomLevel
  })

  // Getters - Layout
  const currentTab = computed(() => {
    return layout.value.activeTab
  })

  // Getters - Animations
  const shouldAnimate = computed(() => {
    return animations.value.enableAnimations && !animations.value.reducedMotion
  })

  // Actions - Tree
  function toggleNode(nodeId) {
    if (tree.value.expandedNodes.has(nodeId)) {
      tree.value.expandedNodes.delete(nodeId)
    } else {
      tree.value.expandedNodes.add(nodeId)
    }
  }

  function expandNode(nodeId) {
    tree.value.expandedNodes.add(nodeId)
  }

  function collapseNode(nodeId) {
    tree.value.expandedNodes.delete(nodeId)
  }

  function expandAll(nodeIds) {
    nodeIds.forEach(id => tree.value.expandedNodes.add(id))
  }

  function collapseAll() {
    tree.value.expandedNodes.clear()
  }

  function setHoveredNode(nodeId) {
    tree.value.hoveredNode = nodeId
  }

  function setSelectedNode(nodeId) {
    tree.value.selectedNode = nodeId
  }

  function clearSelection() {
    tree.value.selectedNode = null
  }

  // Actions - Timeline
  function setZoomLevel(level) {
    timeline.value.zoomLevel = Math.max(1, Math.min(5, level))
  }

  function zoomIn() {
    setZoomLevel(timeline.value.zoomLevel + 1)
  }

  function zoomOut() {
    setZoomLevel(timeline.value.zoomLevel - 1)
  }

  function setVisibleDateRange(start, end) {
    timeline.value.visibleDateRange = { start, end }
  }

  // Actions - Layout
  function setActiveTab(tab) {
    layout.value.activeTab = tab
  }

  function toggleSidebar() {
    layout.value.sidebarCollapsed = !layout.value.sidebarCollapsed
  }

  function setSidebarCollapsed(value) {
    layout.value.sidebarCollapsed = value
  }

  // Actions - Animations
  function setAnimationsEnabled(value) {
    animations.value.enableAnimations = value
  }

  function setReducedMotion(value) {
    animations.value.reducedMotion = value
  }

  function detectReducedMotion() {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    animations.value.reducedMotion = mediaQuery.matches
    
    // Listen for changes
    mediaQuery.addEventListener('change', (e) => {
      animations.value.reducedMotion = e.matches
    })
  }

  // Initialize
  detectReducedMotion()

  return {
    // State
    tree,
    timeline,
    layout,
    animations,
    
    // Getters
    isNodeExpanded,
    expandedNodesList,
    timelineZoom,
    currentTab,
    shouldAnimate,
    
    // Actions - Tree
    toggleNode,
    expandNode,
    collapseNode,
    expandAll,
    collapseAll,
    setHoveredNode,
    setSelectedNode,
    clearSelection,
    
    // Actions - Timeline
    setZoomLevel,
    zoomIn,
    zoomOut,
    setVisibleDateRange,
    
    // Actions - Layout
    setActiveTab,
    toggleSidebar,
    setSidebarCollapsed,
    
    // Actions - Animations
    setAnimationsEnabled,
    setReducedMotion,
    detectReducedMotion
  }
})






