<template>
  <span 
    :class="[
      'risk-badge inline-flex items-center justify-center font-semibold rounded-full',
      sizeClass,
      colorClass,
      pulseClass
    ]"
    :style="customStyle"
  >
    {{ displayText }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getRiskLevel, getRiskColor, shouldPulse } from '../../utils/risk/riskColorMap'
import { formatScore } from '../../utils/formatters/numberFormatter'

const props = defineProps({
  score: {
    type: Number,
    required: true
  },
  level: {
    type: String,
    default: null // Auto-calculate from score if not provided
  },
  size: {
    type: String,
    default: 'md', // 'sm' | 'md' | 'lg'
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  showLevel: {
    type: Boolean,
    default: false // Show level label instead of score
  },
  decimals: {
    type: Number,
    default: 0
  }
})

const riskLevel = computed(() => {
  return props.level || getRiskLevel(props.score)
})

const riskColor = computed(() => {
  return getRiskColor(props.score)
})

const sizeClass = computed(() => {
  const sizes = {
    sm: 'px-2 py-0.5 text-xs min-w-[3rem]',
    md: 'px-3 py-1 text-sm min-w-[4rem]',
    lg: 'px-4 py-1.5 text-base min-w-[5rem]'
  }
  return sizes[props.size] || sizes.md
})

const colorClass = computed(() => {
  // We'll use inline styles for dynamic colors
  return ''
})

const customStyle = computed(() => {
  const color = riskColor.value
  return {
    backgroundColor: color.bg,
    color: color.text,
    border: `1px solid ${color.bg}`
  }
})

const pulseClass = computed(() => {
  return shouldPulse(props.score) ? 'animate-pulse-glow' : ''
})

const displayText = computed(() => {
  if (props.showLevel) {
    const labels = {
      low: 'Low',
      medium: 'Medium',
      high: 'High',
      critical: 'Critical'
    }
    return labels[riskLevel.value] || riskLevel.value
  }
  return formatScore(props.score, props.decimals)
})
</script>

<style scoped>
.risk-badge {
  transition: all 0.3s ease;
}

.risk-badge:hover {
  transform: scale(1.05);
}
</style>






