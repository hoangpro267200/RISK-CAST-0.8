<template>
  <GlassCard 
    variant="hero" 
    :glowColor="glowColor"
    padding="p-8"
  >
    <div class="flex flex-col md:flex-row items-center gap-8">
      <!-- Left: Progress Ring -->
      <div class="flex-shrink-0">
        <ProgressRing 
          :progress="score"
          :size="160"
          :strokeWidth="12"
          :color="riskColor.bg"
        />
      </div>

      <!-- Right: Details -->
      <div class="flex-1 text-center md:text-left">
        <h3 class="text-lg text-gray-400 mb-2">Overall Risk Score</h3>
        
        <div class="flex items-baseline gap-3 justify-center md:justify-start mb-4">
          <span class="text-6xl font-bold" :style="{ color: riskColor.bg }">
            {{ score }}
          </span>
          <RiskBadge 
            :score="score" 
            :level="level"
            size="lg"
            showLevel
          />
        </div>

        <!-- Trend Indicator -->
        <div v-if="trend !== null" class="flex items-center gap-2 justify-center md:justify-start mb-4">
          <span :class="trendColor">{{ trendIcon }}</span>
          <span :class="['text-sm', trendColor]">
            {{ trendText }} from last calculation
          </span>
        </div>

        <!-- Sparkline History -->
        <div v-if="history && history.length > 1" class="mt-4">
          <div class="text-xs text-gray-500 mb-1">30-day trend</div>
          <SparklineChart 
            :data="historyScores"
            :width="200"
            :height="40"
            :color="riskColor.bg"
          />
        </div>

        <!-- Quick Stats -->
        <div class="grid grid-cols-3 gap-4 mt-6">
          <div class="text-center">
            <div class="text-2xl font-bold text-white">{{ criticalLayers }}</div>
            <div class="text-xs text-gray-500">Critical Layers</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-white">{{ delayDays }}</div>
            <div class="text-xs text-gray-500">Expected Delay</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-white">{{ p95Score }}</div>
            <div class="text-xs text-gray-500">P95 Risk</div>
          </div>
        </div>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import { useRiskStore } from '../../stores/riskStore'
import { getRiskColor } from '../../utils/risk/riskColorMap'
import { formatTrend } from '../../utils/formatters/numberFormatter'
import GlassCard from '../shared/GlassCard.vue'
import ProgressRing from '../shared/ProgressRing.vue'
import RiskBadge from '../shared/RiskBadge.vue'
import SparklineChart from '../shared/SparklineChart.vue'

const props = defineProps({
  score: {
    type: Number,
    required: true
  },
  level: {
    type: String,
    required: true
  },
  trend: {
    type: Number,
    default: null
  },
  history: {
    type: Array,
    default: () => []
  }
})

const riskStore = useRiskStore()

const riskColor = computed(() => getRiskColor(props.score))

const glowColor = computed(() => {
  return props.score >= 76 ? riskColor.value.glow : null
})

const trendData = computed(() => {
  if (props.trend === null) return null
  return formatTrend(props.trend)
})

const trendIcon = computed(() => trendData.value?.icon || '')
const trendText = computed(() => trendData.value?.text || '')
const trendColor = computed(() => trendData.value?.color || 'text-gray-400')

const historyScores = computed(() => {
  return props.history.map(h => h.score)
})

const criticalLayers = computed(() => {
  return riskStore.layers.filter(l => l.score >= 76).length
})

const delayDays = computed(() => {
  return riskStore.delayPrediction.expected || 0
})

const p95Score = computed(() => {
  return riskStore.monteCarlo.p95 || 0
})
</script>






