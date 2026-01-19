<template>
  <div class="risk-summary-section">
    <!-- Section Header -->
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-white mb-2">Risk Summary</h2>
      <p class="text-gray-400">Comprehensive risk intelligence overview</p>
    </div>

    <!-- Grid Layout -->
    <div 
      :class="[
        'grid gap-6',
        gridClass
      ]"
    >
      <!-- Hero Card - Overall Risk (spans 2 columns on desktop) -->
      <div :class="heroSpan">
        <OverallRiskCard 
          :score="overallScore"
          :level="riskLevel"
          :trend="trend"
          :history="history"
          :style="fadeInStyle(0)"
        />
      </div>

      <!-- Secondary Cards (ordered by persona preference) -->
      <template v-for="(cardId, index) in visibleCards" :key="cardId">
        <div :style="fadeInStyle(index + 1)">
          <component 
            :is="cardComponents[cardId]" 
            v-bind="cardProps[cardId]"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRiskStore } from '../../stores/riskStore'
import { usePersonaView } from '../../composables/usePersonaView'
import { useAnimations } from '../../composables/useAnimations'
import { useResponsive } from '../../composables/useResponsive'

import OverallRiskCard from './OverallRiskCard.vue'
import LayerScoresCard from './LayerScoresCard.vue'
import CategoryBreakdownCard from './CategoryBreakdownCard.vue'
import ESGScoreCard from './ESGScoreCard.vue'
import MonteCarloCard from './MonteCarloCard.vue'
import DelayPredictionCard from './DelayPredictionCard.vue'
import ShockScenariosCard from './ShockScenariosCard.vue'

// Stores & Composables
const riskStore = useRiskStore()
const { visibleCards } = usePersonaView()
const { fadeInStyle } = useAnimations()
const { mobile, tablet, desktop } = useResponsive()

// Card Components Map
const cardComponents = {
  layers: LayerScoresCard,
  categories: CategoryBreakdownCard,
  esg: ESGScoreCard,
  monteCarlo: MonteCarloCard,
  delay: DelayPredictionCard,
  shockScenarios: ShockScenariosCard
}

// Card Props
const cardProps = computed(() => ({
  layers: {
    layers: riskStore.layers
  },
  categories: {
    categories: riskStore.categories
  },
  esg: {
    esg: riskStore.esg
  },
  monteCarlo: {
    distribution: riskStore.monteCarlo
  },
  delay: {
    prediction: riskStore.delayPrediction
  },
  shockScenarios: {
    scenarios: riskStore.shockScenarios
  }
}))

// Overall Risk Data
const overallScore = computed(() => riskStore.baseline.overallScore)
const riskLevel = computed(() => riskStore.baseline.riskLevel)
const trend = computed(() => riskStore.riskTrend)
const history = computed(() => [
  // Mock history data - would come from API
  { date: new Date('2025-11-01'), score: 65 },
  { date: new Date('2025-11-15'), score: 70 },
  { date: new Date('2025-12-01'), score: 72 }
])

// Responsive Grid
const gridClass = computed(() => {
  if (mobile.value) return 'grid-cols-1'
  if (tablet.value) return 'grid-cols-2'
  return 'grid-cols-3'
})

const heroSpan = computed(() => {
  if (mobile.value) return 'col-span-1'
  if (tablet.value) return 'col-span-2'
  return 'col-span-2'
})
</script>






