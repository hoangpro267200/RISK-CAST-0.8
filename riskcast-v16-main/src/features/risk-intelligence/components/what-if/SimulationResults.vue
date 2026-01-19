<template>
  <div class="simulation-results glass-card p-6">
    <h4 class="font-semibold text-white mb-4">Simulated Results</h4>
    
    <div v-if="isSimulating" class="space-y-3">
      <LoadingShimmer shape="rectangle" size="lg" />
      <LoadingShimmer shape="rectangle" size="md" />
    </div>
    
    <div v-else class="space-y-6">
      <!-- Overall Score -->
      <div class="text-center">
        <div class="text-sm text-gray-400 mb-2">Adjusted Risk Score</div>
        <div class="flex items-center justify-center gap-4">
          <div 
            class="text-5xl font-bold transition-all duration-500"
            :class="scoreColor"
          >
            {{ adjustedScore }}
          </div>
          <div 
            v-if="scoreDiff !== 0"
            class="flex items-center gap-1"
            :class="scoreDiff > 0 ? 'text-red-400' : 'text-green-400'"
          >
            <span class="text-2xl">{{ scoreDiff > 0 ? '↑' : '↓' }}</span>
            <span class="text-xl">{{ Math.abs(scoreDiff) }}</span>
          </div>
        </div>
      </div>

      <NeonDivider />

      <!-- Delay -->
      <div class="grid grid-cols-2 gap-4">
        <div class="text-center glass-card p-3">
          <div class="text-xs text-gray-500 mb-1">Delay (days)</div>
          <div class="text-2xl font-bold text-white">{{ adjustedDelay }}</div>
        </div>
        <div class="text-center glass-card p-3">
          <div class="text-xs text-gray-500 mb-1">Change</div>
          <div 
            class="text-2xl font-bold"
            :class="delayDiff > 0 ? 'text-red-400' : delayDiff < 0 ? 'text-green-400' : 'text-gray-400'"
          >
            {{ delayDiff > 0 ? '+' : '' }}{{ delayDiff }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getRiskColor } from '../../utils/risk/riskColorMap'
import LoadingShimmer from '../shared/LoadingShimmer.vue'
import NeonDivider from '../shared/NeonDivider.vue'

const props = defineProps({
  baseline: {
    type: Object,
    required: true
  },
  simulated: {
    type: Object,
    default: null
  },
  isSimulating: {
    type: Boolean,
    default: false
  }
})

const adjustedScore = computed(() => {
  return props.simulated?.overallScore ?? props.baseline.overallScore
})

const adjustedDelay = computed(() => {
  return props.simulated?.delay ?? props.baseline.delay
})

const scoreDiff = computed(() => {
  if (!props.simulated) return 0
  return adjustedScore.value - props.baseline.overallScore
})

const delayDiff = computed(() => {
  if (!props.simulated) return 0
  return adjustedDelay.value - props.baseline.delay
})

const scoreColor = computed(() => {
  const color = getRiskColor(adjustedScore.value).bg
  return `text-[${color}]`
})
</script>






