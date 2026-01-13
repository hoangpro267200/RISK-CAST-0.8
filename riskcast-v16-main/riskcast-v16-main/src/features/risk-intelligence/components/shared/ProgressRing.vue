<template>
  <div class="progress-ring relative inline-flex items-center justify-center">
    <svg 
      :width="size" 
      :height="size" 
      :viewBox="`0 0 ${size} ${size}`"
      class="transform -rotate-90"
    >
      <!-- Background circle -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        :stroke-width="strokeWidth"
        stroke="currentColor"
        class="text-white/10"
        fill="none"
      />
      
      <!-- Progress circle -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        :stroke-width="strokeWidth"
        :stroke="color"
        fill="none"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
        stroke-linecap="round"
        class="transition-all duration-500 ease-out"
        :class="glowClass"
      />
    </svg>
    
    <!-- Center content (score) -->
    <div class="absolute inset-0 flex items-center justify-center">
      <slot>
        <span class="text-lg font-bold" :style="{ color }">
          {{ displayValue }}
        </span>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getRiskColor } from '../../utils/risk/riskColorMap'

const props = defineProps({
  progress: {
    type: Number,
    required: true,
    validator: (value) => value >= 0 && value <= 100
  },
  size: {
    type: Number,
    default: 120
  },
  strokeWidth: {
    type: Number,
    default: 8
  },
  color: {
    type: String,
    default: null // Auto-calculate from progress if null
  },
  showValue: {
    type: Boolean,
    default: true
  },
  animated: {
    type: Boolean,
    default: true
  }
})

const center = computed(() => props.size / 2)
const radius = computed(() => (props.size - props.strokeWidth) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)

const dashOffset = computed(() => {
  const offset = circumference.value - (props.progress / 100) * circumference.value
  return props.animated ? offset : 0
})

const displayValue = computed(() => {
  return props.showValue ? Math.round(props.progress) : ''
})

const progressColor = computed(() => {
  if (props.color) return props.color
  return getRiskColor(props.progress).bg
})

const glowClass = computed(() => {
  if (props.progress >= 76) {
    return 'drop-shadow-[0_0_8px_rgba(239,68,68,0.6)]'
  }
  return ''
})
</script>

<style scoped>
.progress-ring {
  filter: drop-shadow(0 0 10px rgba(0, 0, 0, 0.3));
}

circle {
  transition: stroke-dashoffset 0.5s ease-out, stroke 0.3s ease;
}
</style>






