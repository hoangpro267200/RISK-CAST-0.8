<template>
  <div class="metric-display">
    <div class="text-sm text-gray-400 mb-1">{{ label }}</div>
    
    <div class="flex items-baseline gap-2">
      <div :class="['text-2xl font-bold', valueClass]">
        {{ formattedValue }}
      </div>
      
      <div v-if="unit" class="text-sm text-gray-500">
        {{ unit }}
      </div>
    </div>
    
    <!-- Trend Indicator -->
    <div v-if="trend !== null && trend !== undefined" class="flex items-center gap-1 mt-1">
      <span :class="trendColor">{{ trendIcon }}</span>
      <span :class="['text-sm', trendColor]">{{ trendText }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatTrend } from '../../utils/formatters/numberFormatter'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  trend: {
    type: Number,
    default: null // Percentage change (positive = increase, negative = decrease)
  },
  unit: {
    type: String,
    default: ''
  },
  valueColor: {
    type: String,
    default: 'text-white'
  },
  formatter: {
    type: Function,
    default: null
  }
})

const formattedValue = computed(() => {
  if (props.formatter) {
    return props.formatter(props.value)
  }
  
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  
  return props.value
})

const valueClass = computed(() => {
  return props.valueColor
})

const trendData = computed(() => {
  if (props.trend === null || props.trend === undefined) return null
  return formatTrend(props.trend)
})

const trendIcon = computed(() => {
  return trendData.value?.icon || ''
})

const trendText = computed(() => {
  return trendData.value?.text || ''
})

const trendColor = computed(() => {
  return trendData.value?.color || 'text-gray-400'
})
</script>






