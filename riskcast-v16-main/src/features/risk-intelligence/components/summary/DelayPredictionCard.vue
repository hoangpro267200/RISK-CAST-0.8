<template>
  <GlassCard padding="p-6" :glowColor="delayGlow">
    <h3 class="text-lg font-semibold text-white mb-4">Delay Prediction</h3>
    
    <!-- Main Delay Display -->
    <div class="text-center mb-6">
      <div class="text-6xl font-bold mb-2" :class="delayColor">
        {{ prediction.expected || 0 }}
      </div>
      <div class="text-sm text-gray-400">Expected Delay (days)</div>
    </div>

    <!-- Range -->
    <div class="glass-card p-4 mb-4">
      <div class="flex justify-between items-center">
        <div class="text-center">
          <div class="text-xs text-gray-500 mb-1">Min</div>
          <div class="text-xl font-semibold text-green-400">{{ prediction.min || 0 }}</div>
        </div>
        
        <div class="text-gray-600">↔</div>
        
        <div class="text-center">
          <div class="text-xs text-gray-500 mb-1">Max</div>
          <div class="text-xl font-semibold text-red-400">{{ prediction.max || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- Range Visualization -->
    <div class="relative h-2 bg-white/10 rounded-full overflow-hidden mb-4">
      <div 
        class="absolute h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 opacity-50"
        :style="rangeStyle"
      ></div>
      <div 
        class="absolute h-full w-1 bg-white"
        :style="expectedMarkerStyle"
      ></div>
    </div>

    <!-- Confidence & Severity -->
    <div class="grid grid-cols-2 gap-3">
      <div class="text-center glass-card p-2">
        <div class="text-xs text-gray-500">Confidence</div>
        <div class="text-sm font-semibold text-white">
          {{ formatConfidence(prediction.confidence) }}
        </div>
      </div>
      <div class="text-center glass-card p-2">
        <div class="text-xs text-gray-500">Severity</div>
        <div class="text-sm font-semibold" :class="severityColor">
          {{ delaySeverity }}
        </div>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import { getDelaySeverity } from '../../utils/risk/delayCalculator'
import { formatConfidence } from '../../utils/formatters/percentFormatter'
import GlassCard from '../shared/GlassCard.vue'

const props = defineProps({
  prediction: {
    type: Object,
    required: true
  }
})

const delayColor = computed(() => {
  const days = props.prediction.expected || 0
  if (days <= 2) return 'text-green-400'
  if (days <= 7) return 'text-yellow-400'
  if (days <= 14) return 'text-orange-400'
  return 'text-red-400'
})

const delayGlow = computed(() => {
  const days = props.prediction.expected || 0
  return days >= 15 ? '#EF4444' : null
})

const delaySeverity = computed(() => {
  return getDelaySeverity(props.prediction.expected || 0)
})

const severityColor = computed(() => {
  const severity = delaySeverity.value
  if (severity === 'minimal') return 'text-green-400'
  if (severity === 'moderate') return 'text-yellow-400'
  if (severity === 'significant') return 'text-orange-400'
  return 'text-red-400'
})

const rangeStyle = computed(() => {
  const min = props.prediction.min || 0
  const max = props.prediction.max || 30
  const total = 30 // Assume 30 days max for visualization
  
  return {
    left: `${(min / total) * 100}%`,
    width: `${((max - min) / total) * 100}%`
  }
})

const expectedMarkerStyle = computed(() => {
  const expected = props.prediction.expected || 0
  const total = 30
  
  return {
    left: `${(expected / total) * 100}%`
  }
})
</script>






