<template>
  <g class="risk-band">
    <path
      v-if="areaPath"
      :d="areaPath"
      :fill="gradientUrl"
      opacity="0.3"
    />
    <path
      v-if="linePath"
      :d="linePath"
      stroke="#4FC3F7"
      stroke-width="2"
      fill="none"
    />
    
    <!-- Gradient definition -->
    <defs>
      <linearGradient id="riskGradient" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#EF4444" />
        <stop offset="50%" stop-color="#F59E0B" />
        <stop offset="100%" stop-color="#10B981" />
      </linearGradient>
    </defs>
  </g>
</template>

<script setup>
import { computed } from 'vue'
import { createRiskAreaPath, createRiskLinePath } from '../../utils/visualization/timelineLayout'

const props = defineProps({
  dataPoints: {
    type: Array,
    required: true
  },
  timeScale: {
    type: Function,
    required: true
  },
  height: {
    type: Number,
    required: true
  }
})

const areaPath = computed(() => {
  if (!props.dataPoints || props.dataPoints.length === 0) return null
  return createRiskAreaPath(props.dataPoints, props.timeScale, props.height - 60)
})

const linePath = computed(() => {
  if (!props.dataPoints || props.dataPoints.length === 0) return null
  return createRiskLinePath(props.dataPoints, props.timeScale, props.height - 60)
})

const gradientUrl = 'url(#riskGradient)'
</script>






