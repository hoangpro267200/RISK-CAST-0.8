<template>
  <g class="timeline-phase">
    <rect
      :x="position.x"
      :y="0"
      :width="position.width"
      :height="height"
      :fill="phaseFill"
      :opacity="0.15"
    />
    <text
      :x="position.x + position.width / 2"
      :y="30"
      text-anchor="middle"
      class="text-sm fill-white font-medium"
    >
      {{ phase.name }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue'
import { positionPhase } from '../../utils/visualization/timelineLayout'
import { getRiskColor } from '../../utils/risk/riskColorMap'

const props = defineProps({
  phase: {
    type: Object,
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

const position = computed(() => {
  return positionPhase(props.phase, props.timeScale, props.height)
})

const phaseFill = computed(() => {
  const riskScore = { low: 20, medium: 50, high: 70, critical: 90 }[props.phase.riskLevel] || 50
  return getRiskColor(riskScore).bg
})
</script>






