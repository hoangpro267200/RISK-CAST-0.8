<template>
  <div
    class="tree-tooltip absolute pointer-events-none z-50"
    :style="tooltipStyle"
  >
    <div class="glass-card p-4 max-w-xs shadow-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between mb-3">
        <h4 class="font-semibold text-white">{{ node.data.name }}</h4>
        <RiskBadge :score="node.data.score || 0" size="sm" />
      </div>

      <!-- Description -->
      <p v-if="node.data.description" class="text-sm text-gray-400 mb-3">
        {{ node.data.description }}
      </p>

      <NeonDivider size="sm" class="my-3" />

      <!-- Top Factors -->
      <div v-if="hasFactors" class="space-y-2">
        <div class="text-xs text-gray-500 mb-2">Top Contributing Factors:</div>
        <div
          v-for="(factor, index) in topFactors"
          :key="index"
          class="flex items-center justify-between text-sm"
        >
          <span class="text-gray-300">{{ factor.factor }}</span>
          <span class="text-neon-cyan">{{ formatContribution(factor.contribution) }}</span>
        </div>
      </div>

      <!-- Stats -->
      <div v-if="node.children && node.children.length > 0" class="mt-3 pt-3 border-t border-white/10">
        <div class="flex items-center justify-between text-xs">
          <span class="text-gray-500">Child Nodes:</span>
          <span class="text-white font-medium">{{ node.children.length }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatWeight } from '../../utils/formatters/percentFormatter'
import RiskBadge from '../shared/RiskBadge.vue'
import NeonDivider from '../shared/NeonDivider.vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  position: {
    type: Object,
    required: true
  }
})

const tooltipStyle = computed(() => {
  const offset = 40
  return {
    left: `${props.position.x + offset}px`,
    top: `${props.position.y - offset}px`,
    transform: 'translate(0, -50%)'
  }
})

const hasFactors = computed(() => {
  return props.node.data.factors && props.node.data.factors.length > 0
})

const topFactors = computed(() => {
  if (!hasFactors.value) return []
  return props.node.data.factors.slice(0, 3)
})

function formatContribution(value) {
  return formatWeight(value)
}
</script>

<style scoped>
.tree-tooltip {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translate(0, -50%) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translate(0, -50%) scale(1);
  }
}
</style>






