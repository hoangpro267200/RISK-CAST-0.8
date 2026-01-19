<template>
  <path
    :d="pathData"
    :stroke="strokeColor"
    :stroke-width="strokeWidth"
    :opacity="opacity"
    fill="none"
    stroke-linecap="round"
    class="tree-edge transition-all duration-300"
    :class="edgeClass"
  />
</template>

<script setup>
import { computed } from 'vue'
import { createCurvedPath } from '../../utils/visualization/treeLayout'
import { interpolateColor } from '../../utils/visualization/colorInterpolation'
import { getRiskColor } from '../../utils/risk/riskColorMap'

const props = defineProps({
  source: {
    type: Object,
    required: true
  },
  target: {
    type: Object,
    required: true
  },
  weight: {
    type: Number,
    default: 1
  },
  highlighted: {
    type: Boolean,
    default: false
  }
})

const pathData = computed(() => {
  return createCurvedPath(props.source, props.target, 'vertical')
})

const strokeWidth = computed(() => {
  // Width based on weight
  const baseWidth = 1
  const maxWidth = 4
  return baseWidth + (props.weight * (maxWidth - baseWidth))
})

const strokeColor = computed(() => {
  if (props.highlighted) {
    return '#4FC3F7'
  }
  
  // Gradient from source to target color (simplified)
  const sourceScore = props.source.score || 0
  const targetScore = props.target.score || 0
  const avgScore = (sourceScore + targetScore) / 2
  
  return getRiskColor(avgScore).bg
})

const opacity = computed(() => {
  return props.highlighted ? 1 : 0.4
})

const edgeClass = computed(() => {
  return {
    'animate-pulse': props.highlighted
  }
})
</script>

<style scoped>
.tree-edge {
  pointer-events: none;
}

.tree-edge.animate-pulse {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}
</style>






