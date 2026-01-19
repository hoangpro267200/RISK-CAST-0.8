<template>
  <div class="risk-driver-tree" ref="containerRef">
    <GlassCard padding="p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h3 class="text-lg font-semibold text-white mb-1">Risk Driver Tree</h3>
          <p class="text-sm text-gray-400">Hierarchical risk factor analysis</p>
        </div>
        
        <!-- Controls -->
        <div class="flex items-center gap-2">
          <button
            @click="expandAll"
            class="px-3 py-1 text-sm bg-white/5 hover:bg-white/10 rounded-lg transition-smooth"
          >
            Expand All
          </button>
          <button
            @click="collapseAll"
            class="px-3 py-1 text-sm bg-white/5 hover:bg-white/10 rounded-lg transition-smooth"
          >
            Collapse All
          </button>
          <button
            @click="resetZoom"
            class="px-3 py-1 text-sm bg-white/5 hover:bg-white/10 rounded-lg transition-smooth"
          >
            Reset Zoom
          </button>
        </div>
      </div>

      <!-- Tree Visualization -->
      <div 
        class="tree-container relative bg-gray-900/50 rounded-xl overflow-hidden"
        :style="{ height: `${height}px` }"
      >
        <svg
          ref="svgRef"
          :width="svgWidth"
          :height="svgHeight"
          class="w-full h-full"
        >
          <!-- Gradients -->
          <defs>
            <radialGradient 
              v-for="node in visibleNodes" 
              :key="`grad-${node.id}`"
              :id="`gradient-${node.id}`"
            >
              <stop offset="0%" :stop-color="getNodeColor(node)" />
              <stop offset="100%" :stop-color="darkenColor(getNodeColor(node), 0.3)" />
            </radialGradient>
          </defs>

          <!-- Edges -->
          <g class="edges">
            <TreeEdge
              v-for="edge in visibleEdges"
              :key="`edge-${edge.source.id}-${edge.target.id}`"
              :source="edge.source"
              :target="edge.target"
              :weight="edge.weight"
              :highlighted="isEdgeHighlighted(edge)"
            />
          </g>

          <!-- Nodes -->
          <g class="nodes">
            <TreeNode
              v-for="node in visibleNodes"
              :key="node.id"
              :node="node"
              :position="{ x: node.x, y: node.y }"
              :isExpanded="isExpanded(node.id)"
              :isHovered="hoveredNode === node.id"
              :isSelected="selectedNode === node.id"
              :isHighlighted="highlightedNodes.includes(node.id)"
              @click="handleNodeClick(node)"
              @mouseenter="hoveredNode = node.id"
              @mouseleave="hoveredNode = null"
            />
          </g>
        </svg>

        <!-- Tooltip -->
        <TreeTooltip
          v-if="hoveredNode && tooltipData"
          :node="tooltipData"
          :position="tooltipPosition"
        />
      </div>

      <!-- Legend -->
      <TreeLegend class="mt-4" />
    </GlassCard>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRiskStore } from '../../stores/riskStore'
import { useUIStore } from '../../stores/uiStore'
import { usePersonaView } from '../../composables/usePersonaView'
import { useResponsive } from '../../composables/useResponsive'
import { calculateTreeLayout, filterTreeByDepth, getAncestors, getDescendants } from '../../utils/visualization/treeLayout'
import { getRiskColor } from '../../utils/risk/riskColorMap'
import { darkenColor } from '../../utils/visualization/colorInterpolation'

import GlassCard from '../shared/GlassCard.vue'
import TreeNode from './TreeNode.vue'
import TreeEdge from './TreeEdge.vue'
import TreeTooltip from './TreeTooltip.vue'
import TreeLegend from './TreeLegend.vue'

const props = defineProps({
  treeData: {
    type: Object,
    default: null
  },
  maxDepth: {
    type: Number,
    default: null
  },
  highlightedPath: {
    type: Array,
    default: () => []
  }
})

// Stores
const riskStore = useRiskStore()
const uiStore = useUIStore()
const { maxTreeDepth } = usePersonaView()
const { mobile, tablet } = useResponsive()

// Refs
const containerRef = ref(null)
const svgRef = ref(null)
const hoveredNode = ref(null)
const selectedNode = ref(null)

// Dimensions
const height = computed(() => mobile.value ? 400 : tablet.value ? 600 : 800)
const svgWidth = computed(() => mobile.value ? 350 : tablet.value ? 700 : 1000)
const svgHeight = computed(() => height.value)

// Tree data
const effectiveTreeData = computed(() => {
  return props.treeData || riskStore.driverTree
})

const effectiveMaxDepth = computed(() => {
  return props.maxDepth || maxTreeDepth.value || 3
})

const filteredTreeData = computed(() => {
  return filterTreeByDepth(effectiveTreeData.value, effectiveMaxDepth.value)
})

// Layout calculation
const layout = computed(() => {
  if (!filteredTreeData.value) return { nodes: [], edges: [] }
  
  return calculateTreeLayout(
    filteredTreeData.value,
    svgWidth.value,
    svgHeight.value,
    {
      nodeSize: 80,
      levelSeparation: 150,
      orientation: 'vertical'
    }
  )
})

const visibleNodes = computed(() => layout.value.nodes)
const visibleEdges = computed(() => layout.value.edges)

// Expanded nodes
const expandedNodes = computed(() => uiStore.tree.expandedNodes)

function isExpanded(nodeId) {
  return expandedNodes.value.has(nodeId)
}

function handleNodeClick(node) {
  uiStore.toggleNode(node.id)
  selectedNode.value = node.id
}

function expandAll() {
  const allIds = visibleNodes.value.map(n => n.id)
  uiStore.expandAll(allIds)
}

function collapseAll() {
  uiStore.collapseAll()
}

function resetZoom() {
  // Reset any zoom/pan transformations
  selectedNode.value = null
  hoveredNode.value = null
}

// Node coloring
function getNodeColor(node) {
  return getRiskColor(node.data.score || 0).bg
}

// Highlighting
const highlightedNodes = computed(() => {
  if (props.highlightedPath.length > 0) {
    return props.highlightedPath
  }
  
  if (selectedNode.value) {
    const ancestors = getAncestors(selectedNode.value, visibleNodes.value)
    const descendants = getDescendants(selectedNode.value, visibleNodes.value)
    return [selectedNode.value, ...ancestors, ...descendants]
  }
  
  return []
})

function isEdgeHighlighted(edge) {
  if (highlightedNodes.value.length === 0) return false
  return highlightedNodes.value.includes(edge.source.id) && 
         highlightedNodes.value.includes(edge.target.id)
}

// Tooltip
const tooltipData = computed(() => {
  if (!hoveredNode.value) return null
  return visibleNodes.value.find(n => n.id === hoveredNode.value)
})

const tooltipPosition = computed(() => {
  if (!tooltipData.value) return { x: 0, y: 0 }
  return {
    x: tooltipData.value.x,
    y: tooltipData.value.y
  }
})

// Lifecycle
onMounted(() => {
  // Initialize with root expanded
  if (visibleNodes.value.length > 0) {
    uiStore.expandNode(visibleNodes.value[0].id)
  }
})
</script>

<style scoped>
.tree-container {
  position: relative;
  user-select: none;
}

.nodes {
  pointer-events: all;
}

.edges {
  pointer-events: none;
}
</style>






