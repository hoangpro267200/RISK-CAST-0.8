<template>
  <g 
    class="timeline-event cursor-pointer"
    :transform="`translate(${position.x}, ${position.y})`"
    @click="$emit('click')"
  >
    <!-- Event marker -->
    <circle
      :r="radius"
      :fill="eventColor"
      :stroke="strokeColor"
      :stroke-width="2"
      class="transition-all duration-300"
      :class="{ 'animate-pulse': isCritical }"
    />
    
    <!-- Icon -->
    <text
      y="5"
      text-anchor="middle"
      class="text-sm pointer-events-none"
    >
      {{ eventIcon }}
    </text>

    <!-- Label -->
    <text
      y="30"
      text-anchor="middle"
      class="text-xs fill-gray-300 pointer-events-none"
    >
      {{ truncatedDescription }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue'
import { getRiskColor } from '../../utils/risk/riskColorMap'

const props = defineProps({
  event: {
    type: Object,
    required: true
  },
  position: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])

const radius = computed(() => {
  const sizes = { low: 6, medium: 8, high: 10, critical: 12 }
  return sizes[props.event.severity] || 8
})

const isCritical = computed(() => props.event.severity === 'critical')

const eventColor = computed(() => {
  const scores = { low: 20, medium: 50, high: 70, critical: 90 }
  return getRiskColor(scores[props.event.severity] || 50).bg
})

const strokeColor = computed(() => isCritical.value ? '#fff' : 'rgba(255,255,255,0.5)')

const eventIcon = computed(() => {
  const icons = {
    weather: '🌩️',
    geopolitical: '⚠️',
    operational: '⚙️',
    financial: '💰'
  }
  return icons[props.event.type] || '📍'
})

const truncatedDescription = computed(() => {
  const desc = props.event.description || ''
  return desc.length > 20 ? desc.substring(0, 17) + '...' : desc
})
</script>






