<template>
  <div class="comparison-view glass-card p-6">
    <h4 class="font-semibold text-white mb-4">Before vs After</h4>
    
    <div class="space-y-3">
      <div 
        v-for="metric in metrics"
        :key="metric.label"
        class="flex items-center justify-between py-2 border-b border-white/10"
      >
        <span class="text-sm text-gray-400">{{ metric.label }}</span>
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-300">{{ metric.baseline }}</span>
          <span class="text-gray-600">→</span>
          <span 
            class="text-sm font-semibold"
            :class="metric.changeClass"
          >
            {{ metric.simulated }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  baseline: {
    type: Object,
    required: true
  },
  simulated: {
    type: Object,
    required: true
  }
})

const metrics = computed(() => {
  return [
    {
      label: 'Overall Score',
      baseline: props.baseline.overallScore,
      simulated: props.simulated.overallScore ?? props.baseline.overallScore,
      changeClass: getChangeClass(props.simulated.overallScore, props.baseline.overallScore, true)
    },
    {
      label: 'Expected Delay',
      baseline: `${props.baseline.delay}d`,
      simulated: `${props.simulated.delay ?? props.baseline.delay}d`,
      changeClass: getChangeClass(props.simulated.delay, props.baseline.delay, true)
    }
  ]
})

function getChangeClass(simulated, baseline, higherIsBad = true) {
  if (!simulated || simulated === baseline) return 'text-gray-400'
  const increased = simulated > baseline
  if (higherIsBad) {
    return increased ? 'text-red-400' : 'text-green-400'
  } else {
    return increased ? 'text-green-400' : 'text-red-400'
  }
}
</script>






