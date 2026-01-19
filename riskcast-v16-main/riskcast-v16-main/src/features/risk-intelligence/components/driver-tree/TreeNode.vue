<template>
  <g 
    class="tree-node cursor-pointer"
    :transform="`translate(${position.x}, ${position.y})`"
    @click="$emit('click')"
    @mouseenter="$emit('mouseenter')"
    @mouseleave="$emit('mouseleave')"
  >
    <!-- Glow effect for highlighted nodes -->
    <circle
      v-if="isHighlighted || isSelected"
      :r="radius + 5"
      :fill="`url(#gradient-${node.id})`"
      :opacity="0.3"
      class="animate-pulse"
    />

    <!-- Main node circle -->
    <circle
      :r="radius"
      :fill="`url(#gradient-${node.id})`"
      :stroke="strokeColor"
      :stroke-width="strokeWidth"
      :class="nodeClass"
      class="transition-all duration-300"
    />

    <!-- Score text -->
    <text
      y="5"
      text-anchor="middle"
      class="text-sm font-bold fill-white pointer-events-none"
    >
      {{ Math.round(node.data.score || 0) }}
    </text>

    <!-- Name label -->
    <text
      y="30"
      text-anchor="middle"
      class="text-xs fill-gray-300 pointer-events-none max-w-[80px]"
    >
      {{ truncatedName }}
    </text>

    <!-- Expand/Collapse indicator -->
    <g v-if="hasChildren" transform="translate(0, -25)">
      <circle
        r="8"
        fill="rgba(255,255,255,0.1)"
        stroke="rgba(255,255,255,0.3)"
        stroke-width="1"
      />
      <text
        y="3"
        text-anchor="middle"
        class="text-xs fill-white pointer-events-none"
      >
        {{ isExpanded ? '−' : '+' }}
      </text>
    </g>
  </g>
</template>

<script setup>
import { computed } from 'vue'
import { getRiskColor } from '../../utils/risk/riskColorMap'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  position: {
    type: Object,
    required: true
  },
  isExpanded: {
    type: Boolean,
    default: false
  },
  isHovered: {
    type: Boolean,
    default: false
  },
  isSelected: {
    type: Boolean,
    default: false
  },
  isHighlighted: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click', 'mouseenter', 'mouseleave'])

const radius = computed(() => {
  const baseRadius = 25
  const score = props.node.data.score || 0
  const bonus = (score / 100) * 10
  return baseRadius + bonus
})

const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

const strokeColor = computed(() => {
  if (props.isSelected) return '#4FC3F7'
  if (props.isHighlighted) return '#00BCD4'
  if (props.isHovered) return '#fff'
  return 'rgba(255,255,255,0.2)'
})

const strokeWidth = computed(() => {
  if (props.isSelected) return 3
  if (props.isHighlighted) return 2
  if (props.isHovered) return 2
  return 1
})

const nodeClass = computed(() => {
  return {
    'opacity-100': !props.isHighlighted && !props.isSelected,
    'opacity-50': props.isHighlighted && !props.isSelected && !props.isHovered
  }
})

const truncatedName = computed(() => {
  const name = props.node.data.name || 'Unknown'
  return name.length > 15 ? name.substring(0, 12) + '...' : name
})
</script>

<style scoped>
.tree-node {
  transition: all 0.3s ease;
}

.tree-node:hover circle {
  filter: brightness(1.2);
}
</style>






