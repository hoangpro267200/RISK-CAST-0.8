<template>
  <GlassCard padding="p-6">
    <h3 class="text-lg font-semibold text-white mb-4">Shock Scenarios</h3>
    
    <!-- Scenarios Table -->
    <div class="space-y-3">
      <div 
        v-for="scenario in sortedScenarios"
        :key="scenario.id"
        @click="$emit('scenarioClick', scenario)"
        class="glass-card p-3 cursor-pointer hover:bg-white/10 transition-smooth"
      >
        <div class="flex items-start justify-between mb-2">
          <div class="flex-1">
            <div class="font-medium text-white text-sm mb-1">
              {{ scenario.name }}
            </div>
            <div class="text-xs text-gray-400">
              Probability: {{ formatProbability(scenario.probability) }}
            </div>
          </div>
          <RiskBadge :score="scenario.impact" size="sm" />
        </div>
        
        <!-- Impact Bar -->
        <div class="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div 
            class="h-full transition-all duration-500"
            :style="{
              width: `${scenario.impact}%`,
              backgroundColor: getImpactColor(scenario.impact)
            }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="scenarios.length === 0" class="text-center py-8 text-gray-500">
      No shock scenarios identified
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import { getRiskColor } from '../../utils/risk/riskColorMap'
import { formatProbability } from '../../utils/formatters/percentFormatter'
import GlassCard from '../shared/GlassCard.vue'
import RiskBadge from '../shared/RiskBadge.vue'

const props = defineProps({
  scenarios: {
    type: Array,
    required: true
  }
})

defineEmits(['scenarioClick'])

const sortedScenarios = computed(() => {
  return [...props.scenarios].sort((a, b) => b.impact - a.impact)
})

function getImpactColor(impact) {
  return getRiskColor(impact).bg
}
</script>






