<template>
  <GlassCard padding="p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-white mb-1">What-If Simulator</h3>
        <p class="text-sm text-gray-400">Adjust parameters to see impact on risk</p>
      </div>
      
      <div class="flex gap-2">
        <button
          @click="handleReset"
          :disabled="!isDirty"
          class="px-4 py-2 text-sm bg-white/5 hover:bg-white/10 rounded-lg transition-smooth disabled:opacity-50"
        >
          Reset
        </button>
        <button
          @click="handleApply"
          :disabled="!isDirty"
          class="px-4 py-2 text-sm bg-neon-blue hover:bg-neon-cyan rounded-lg transition-smooth disabled:opacity-50"
        >
          Apply
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left: Controls -->
      <div class="space-y-6">
        <ParameterGroup
          v-for="group in parameterGroups"
          :key="group.name"
          :group="group"
          @change="handleParameterChange"
        />
      </div>

      <!-- Right: Results -->
      <div class="space-y-6">
        <SimulationResults
          :baseline="baseline"
          :simulated="simulatedResults"
          :isSimulating="isSimulating"
        />
        
        <ComparisonView
          v-if="isDirty"
          :baseline="baseline"
          :simulated="simulatedResults"
        />
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRiskStore } from '../../stores/riskStore'
import { useWhatIfStore } from '../../stores/whatIfStore'
import { useWhatIfEngine } from '../../composables/useWhatIfEngine'

import GlassCard from '../shared/GlassCard.vue'
import ParameterGroup from './ParameterGroup.vue'
import SimulationResults from './SimulationResults.vue'
import ComparisonView from './ComparisonView.vue'

const riskStore = useRiskStore()
const whatIfStore = useWhatIfStore()
const { recalculate, simulatedResults } = useWhatIfEngine()

const baseline = computed(() => ({
  overallScore: riskStore.baseline.overallScore,
  delay: riskStore.delayPrediction.expected,
  layers: riskStore.layers
}))

const isDirty = computed(() => whatIfStore.isDirty)
const isSimulating = computed(() => whatIfStore.isSimulating)

const parameterGroups = [
  {
    name: 'Weather Factors',
    icon: '🌩️',
    parameters: [
      { id: 'weather_severity', name: 'Weather Severity', type: 'slider', value: 50, min: 0, max: 100, unit: '%' }
    ]
  },
  {
    name: 'Operational Factors',
    icon: '⚙️',
    parameters: [
      { id: 'port_congestion', name: 'Port Congestion', type: 'slider', value: 60, min: 0, max: 100, unit: '%' },
      { id: 'carrier_reliability', name: 'Carrier Reliability', type: 'slider', value: 70, min: 0, max: 100, unit: '%' }
    ]
  },
  {
    name: 'Geopolitical Factors',
    icon: '🌐',
    parameters: [
      { id: 'sanctions_exposure', name: 'Sanctions Exposure', type: 'slider', value: 40, min: 0, max: 100, unit: '%' }
    ]
  }
]

function handleParameterChange({ id, value }) {
  whatIfStore.updateParameter(id, value)
  recalculate()
}

function handleReset() {
  whatIfStore.reset()
}

function handleApply() {
  console.log('Apply simulation as new baseline')
  // Would trigger API call in production
}

// Initialize parameters
whatIfStore.initializeParameters({
  weather_severity: 50,
  port_congestion: 60,
  carrier_reliability: 70,
  sanctions_exposure: 40
})
</script>






