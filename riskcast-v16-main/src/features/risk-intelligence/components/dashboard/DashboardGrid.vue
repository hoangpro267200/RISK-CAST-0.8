<template>
  <div class="dashboard-grid">
    <!-- Tab Navigation -->
    <div class="flex items-center gap-2 mb-6 overflow-x-auto scrollbar-thin">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="$emit('tabChange', tab.id)"
        class="px-4 py-2 rounded-lg transition-smooth whitespace-nowrap"
        :class="[
          activeTab === tab.id
            ? 'glass-card-hero ring-2 ring-neon-cyan text-white'
            : 'glass-card hover:bg-white/10 text-gray-400'
        ]"
      >
        <span class="mr-2">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <Transition name="fade" mode="out-in">
        <component :is="currentTabComponent" :key="activeTab" />
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import RiskSummarySection from '../summary/RiskSummarySection.vue'
import RiskDriverTree from '../driver-tree/RiskDriverTree.vue'
import RiskTimeline from '../timeline/RiskTimeline.vue'
import WhatIfSimulator from '../what-if/WhatIfSimulator.vue'
import AIExplanationPanel from '../explanation/AIExplanationPanel.vue'

const props = defineProps({
  activeTab: {
    type: String,
    default: 'summary'
  }
})

defineEmits(['tabChange'])

const tabs = [
  { id: 'summary', label: 'Summary', icon: '📊' },
  { id: 'tree', label: 'Risk Drivers', icon: '🌳' },
  { id: 'timeline', label: 'Timeline', icon: '📅' },
  { id: 'whatif', label: 'What-If', icon: '🎯' },
  { id: 'explanation', label: 'AI Insights', icon: '🤖' }
]

const tabComponents = {
  summary: RiskSummarySection,
  tree: RiskDriverTree,
  timeline: RiskTimeline,
  whatif: WhatIfSimulator,
  explanation: AIExplanationPanel
}

const currentTabComponent = computed(() => {
  return tabComponents[props.activeTab] || tabComponents.summary
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>






