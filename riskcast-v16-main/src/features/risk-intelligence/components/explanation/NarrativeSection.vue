<template>
  <div
    class="narrative-section glass-card p-6 cursor-pointer transition-all duration-300"
    :class="[
      isActive ? 'ring-2 ring-neon-cyan' : '',
      severityGlow
    ]"
    @click="$emit('click')"
  >
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <h4 class="text-lg font-semibold text-white">{{ section.title }}</h4>
      <RiskBadge
        v-if="section.severity"
        :score="severityScore"
        :level="section.severity"
        size="sm"
        showLevel
      />
    </div>

    <!-- Content -->
    <p class="text-gray-300 leading-relaxed mb-4">
      {{ section.content }}
    </p>

    <!-- Insights -->
    <div v-if="section.insights && section.insights.length > 0" class="mb-4">
      <div class="text-xs text-gray-500 mb-2">Key Insights:</div>
      <div class="space-y-2">
        <div
          v-for="(insight, index) in section.insights"
          :key="index"
          class="flex items-start gap-2 text-sm text-gray-300"
        >
          <span class="text-neon-cyan mt-0.5">•</span>
          <span>{{ insight }}</span>
        </div>
      </div>
    </div>

    <!-- Recommendations -->
    <div v-if="section.recommendations && section.recommendations.length > 0">
      <div class="text-xs text-gray-500 mb-2">Recommendations:</div>
      <div class="space-y-2">
        <div
          v-for="(rec, index) in section.recommendations"
          :key="index"
          class="flex items-start gap-2 text-sm"
        >
          <span class="text-green-400 mt-0.5">✓</span>
          <span class="text-gray-300">{{ rec }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import RiskBadge from '../shared/RiskBadge.vue'

const props = defineProps({
  section: {
    type: Object,
    required: true
  },
  isActive: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const severityScore = computed(() => {
  const scores = { info: 20, low: 30, medium: 50, high: 70, critical: 90 }
  return scores[props.section.severity] || 50
})

const severityGlow = computed(() => {
  if (props.section.severity === 'critical' || props.section.severity === 'high') {
    return 'border-l-4 border-red-500'
  }
  return ''
})
</script>






