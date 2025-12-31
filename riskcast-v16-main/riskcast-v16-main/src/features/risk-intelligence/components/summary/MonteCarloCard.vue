<template>
  <GlassCard padding="p-6">
    <h3 class="text-lg font-semibold text-white mb-4">Risk Distribution</h3>
    
    <!-- Key Metrics -->
    <div class="grid grid-cols-2 gap-4 mb-4">
      <div class="glass-card p-3">
        <div class="text-xs text-gray-400 mb-1">P50 (Median)</div>
        <div class="text-2xl font-bold text-white">{{ distribution.p50 || 0 }}</div>
      </div>
      <div class="glass-card p-3">
        <div class="text-xs text-gray-400 mb-1">P95 (Worst Case)</div>
        <div class="text-2xl font-bold text-red-400">{{ distribution.p95 || 0 }}</div>
      </div>
    </div>

    <!-- Distribution Chart (Simple SVG) -->
    <div v-if="hasDistribution" class="mt-4">
      <svg :width="chartWidth" :height="chartHeight" class="w-full">
        <!-- Distribution curve -->
        <path
          :d="distributionPath"
          fill="rgba(79, 195, 247, 0.2)"
          stroke="#4FC3F7"
          stroke-width="2"
        />
        
        <!-- P50 line -->
        <line
          :x1="p50X"
          y1="0"
          :x2="p50X"
          :y2="chartHeight"
          stroke="#10B981"
          stroke-width="2"
          stroke-dasharray="4"
        />
        
        <!-- P95 line -->
        <line
          :x1="p95X"
          y1="0"
          :x2="p95X"
          :y2="chartHeight"
          stroke="#EF4444"
          stroke-width="2"
          stroke-dasharray="4"
        />
      </svg>
      
      <div class="flex justify-between text-xs text-gray-500 mt-2">
        <span>Low Risk</span>
        <span>High Risk</span>
      </div>
    </div>

    <!-- Confidence Interval -->
    <div class="mt-4 text-center text-sm text-gray-400">
      90% Confidence: {{ distribution.p50 - 10 }} - {{ distribution.p95 }}
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import GlassCard from '../shared/GlassCard.vue'

const props = defineProps({
  distribution: {
    type: Object,
    required: true
  }
})

const chartWidth = 300
const chartHeight = 100

const hasDistribution = computed(() => {
  return props.distribution.distribution && props.distribution.distribution.length > 0
})

const distributionPath = computed(() => {
  if (!hasDistribution.value) return ''
  
  const dist = props.distribution.distribution
  const maxProb = Math.max(...dist.map(d => d.probability))
  
  const points = dist.map((d, i) => {
    const x = (i / (dist.length - 1)) * chartWidth
    const y = chartHeight - (d.probability / maxProb) * chartHeight
    return `${x},${y}`
  })
  
  return `M ${points.join(' L ')} L ${chartWidth},${chartHeight} L 0,${chartHeight} Z`
})

const p50X = computed(() => {
  const p50 = props.distribution.p50 || 50
  return (p50 / 100) * chartWidth
})

const p95X = computed(() => {
  const p95 = props.distribution.p95 || 90
  return (p95 / 100) * chartWidth
})
</script>






