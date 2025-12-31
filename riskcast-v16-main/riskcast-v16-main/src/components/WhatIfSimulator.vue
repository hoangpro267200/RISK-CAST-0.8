<template>
  <div class="what-if-simulator glass-card">
    <div class="simulator-header">
      <h2 class="text-xl font-bold text-white mb-2">
        <span class="icon">⚙️</span> What-If Simulator
      </h2>
      <p class="text-sm text-gray-400">Adjust parameters to see impact on risk score</p>
    </div>
    
    <div class="simulator-content">
      <!-- Current vs Simulated Comparison -->
      <div class="comparison-gauges">
        <div class="gauge-item">
          <div class="gauge-label">Current Score</div>
          <div class="gauge-value original">{{ originalScore.toFixed(1) }}</div>
        </div>
        <div class="gauge-arrow">→</div>
        <div class="gauge-item">
          <div class="gauge-label">Simulated Score</div>
          <div class="gauge-value simulated" :style="`color: ${simulatedColor}`">
            {{ simulatedScore.toFixed(1) }}
          </div>
        </div>
        <div class="gauge-delta" :class="deltaClass">
          {{ delta > 0 ? '+' : '' }}{{ delta.toFixed(1) }}
        </div>
      </div>
      
      <!-- Interactive Sliders -->
      <div class="sliders-container">
        <!-- Carrier Reliability -->
        <div class="slider-group">
          <label class="slider-label">
            <span>Carrier Reliability</span>
            <span class="slider-value">{{ carrierReliability }}</span>
          </label>
          <input
            type="range"
            v-model.number="carrierReliability"
            min="0"
            max="100"
            class="custom-slider"
          />
        </div>
        
        <!-- Packing Quality -->
        <div class="slider-group">
          <label class="slider-label">
            <span>Packing Quality (1-5)</span>
            <span class="slider-value">{{ packingQuality }}</span>
          </label>
          <input
            type="range"
            v-model.number="packingQuality"
            min="1"
            max="5"
            class="custom-slider"
          />
        </div>
        
        <!-- Mode Switch -->
        <div class="slider-group">
          <label class="slider-label">Transport Mode</label>
          <select v-model="selectedMode" class="mode-select">
            <option value="sea_freight">Sea Freight</option>
            <option value="air_freight">Air Freight</option>
            <option value="road">Road</option>
            <option value="rail">Rail</option>
          </select>
        </div>
        
        <!-- Priority -->
        <div class="slider-group">
          <label class="slider-label">Priority</label>
          <select v-model="selectedPriority" class="mode-select">
            <option value="balanced">Balanced</option>
            <option value="fastest">Fastest</option>
            <option value="cheapest">Cheapest</option>
          </select>
        </div>
        
        <!-- Insurance -->
        <div class="slider-group">
          <label class="slider-label">Insurance Coverage</label>
          <select v-model="selectedInsurance" class="mode-select">
            <option value="icc_c">ICC C (Basic)</option>
            <option value="icc_b">ICC B (Standard)</option>
            <option value="icc_a">ICC A (Comprehensive)</option>
            <option value="all_risks">All Risks</option>
          </select>
        </div>
      </div>
      
      <!-- Impact Summary -->
      <div class="impact-summary">
        <div class="impact-header">Impact Analysis</div>
        <div class="impact-items">
          <div class="impact-item" v-for="change in changes" :key="change.factor">
            <span class="change-factor">{{ change.factor }}</span>
            <span class="change-impact" :class="change.impact > 0 ? 'negative' : 'positive'">
              {{ change.impact > 0 ? '+' : '' }}{{ change.impact.toFixed(1) }} pts
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { getRiskColor } from '../utils/riskColorMap';

const props = defineProps({
  baseLayerScores: { type: Object, required: true },
  originalScore: { type: Number, required: true }
});

// Slider states
const carrierReliability = ref(88);
const packingQuality = ref(3);
const selectedMode = ref('sea_freight');
const selectedPriority = ref('balanced');
const selectedInsurance = ref('icc_b');

// Calculate simulated score based on changes
const simulatedScore = computed(() => {
  let score = props.originalScore;
  
  // Carrier reliability impact (weight ~0.12)
  const carrierDelta = (100 - carrierReliability.value) - (100 - 88);
  score += carrierDelta * 0.12;
  
  // Packing quality impact (weight ~0.08)
  const packingDelta = (5 - packingQuality.value) * 10 - 20; // Lower number = better packing
  score += packingDelta * 0.08;
  
  // Mode impact
  const modeImpact = {
    'air_freight': -5,
    'sea_freight': 0,
    'road': +3,
    'rail': +2
  };
  score += modeImpact[selectedMode.value] || 0;
  
  // Priority impact
  const priorityImpact = {
    'fastest': -2,
    'balanced': 0,
    'cheapest': +3
  };
  score += priorityImpact[selectedPriority.value] || 0;
  
  // Insurance impact
  const insuranceImpact = {
    'all_risks': -3,
    'icc_a': -2,
    'icc_b': 0,
    'icc_c': +2
  };
  score += insuranceImpact[selectedInsurance.value] || 0;
  
  return Math.max(0, Math.min(100, score));
});

const delta = computed(() => simulatedScore.value - props.originalScore);

const deltaClass = computed(() => delta.value < 0 ? 'delta-positive' : 'delta-negative');

const simulatedColor = computed(() => getRiskColor(simulatedScore.value).primary);

const changes = computed(() => {
  const changeList = [];
  
  if (carrierReliability.value !== 88) {
    changeList.push({
      factor: 'Carrier Reliability',
      impact: (100 - carrierReliability.value) * 0.12 - (100 - 88) * 0.12
    });
  }
  
  if (packingQuality.value !== 3) {
    changeList.push({
      factor: 'Packing Quality',
      impact: ((5 - packingQuality.value) * 10 - 20) * 0.08
    });
  }
  
  if (selectedMode.value !== 'sea_freight') {
    const impact = { 'air_freight': -5, 'road': +3, 'rail': +2 }[selectedMode.value];
    changeList.push({ factor: 'Transport Mode', impact });
  }
  
  return changeList;
});
</script>

<style scoped>
.glass-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.simulator-header {
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(79, 195, 247, 0.2);
  padding-bottom: 1rem;
}

.icon {
  font-size: 1.5rem;
}

.comparison-gauges {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 2rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 12px;
  margin-bottom: 2rem;
}

.gauge-item {
  text-align: center;
}

.gauge-label {
  font-size: 0.75rem;
  color: #94A3B8;
  margin-bottom: 0.5rem;
}

.gauge-value {
  font-size: 3rem;
  font-weight: 700;
}

.gauge-value.original {
  color: #4FC3F7;
}

.gauge-value.simulated {
  text-shadow: 0 0 20px currentColor;
}

.gauge-arrow {
  font-size: 2rem;
  color: #94A3B8;
}

.gauge-delta {
  padding: 0.5rem 1rem;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1.25rem;
}

.delta-positive {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
  border: 1px solid #10B981;
}

.delta-negative {
  background: rgba(239, 68, 68, 0.2);
  color: #EF4444;
  border: 1px solid #EF4444;
}

.sliders-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.slider-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #E2E8F0;
  font-weight: 600;
}

.slider-value {
  color: #4FC3F7;
  font-weight: 700;
}

.custom-slider {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  outline: none;
  -webkit-appearance: none;
}

.custom-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  background: #4FC3F7;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.6);
}

.mode-select {
  padding: 0.75rem;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(79, 195, 247, 0.3);
  border-radius: 8px;
  color: #fff;
  font-size: 0.875rem;
  cursor: pointer;
}

.mode-select:focus {
  outline: none;
  border-color: #4FC3F7;
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.3);
}

.impact-summary {
  padding: 1rem;
  background: rgba(79, 195, 247, 0.05);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 12px;
}

.impact-header {
  font-weight: 700;
  color: #4FC3F7;
  margin-bottom: 0.75rem;
}

.impact-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.impact-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 6px;
}

.change-factor {
  color: #E2E8F0;
  font-size: 0.875rem;
}

.change-impact {
  font-weight: 700;
  font-size: 0.875rem;
}

.change-impact.positive {
  color: #10B981;
}

.change-impact.negative {
  color: #EF4444;
}
</style>






