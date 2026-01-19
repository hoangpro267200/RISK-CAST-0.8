<template>
  <div class="risk-summary-cards grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <!-- Card 1: Overall Risk -->
    <div class="glass-card" :style="fadeInStagger(0)">
      <div class="card-header">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Overall Risk</h3>
      </div>
      <div class="card-body">
        <!-- Circular Gauge -->
        <div class="gauge-container">
          <svg class="gauge-svg" viewBox="0 0 200 120">
            <!-- Background arc -->
            <path
              :d="arcPath"
              fill="none"
              stroke="rgba(255,255,255,0.1)"
              stroke-width="20"
              stroke-linecap="round"
            />
            <!-- Progress arc -->
            <path
              :d="arcPath"
              fill="none"
              :stroke="riskColors.primary"
              stroke-width="20"
              stroke-linecap="round"
              :stroke-dasharray="`${scoreProgress} ${arcLength}`"
              :style="`filter: drop-shadow(0 0 10px ${riskColors.glow})`"
              class="gauge-progress"
            />
            <!-- Score text -->
            <text x="100" y="80" text-anchor="middle" class="gauge-score">
              {{ overallScore.toFixed(1) }}
            </text>
            <text x="100" y="100" text-anchor="middle" class="gauge-label">
              {{ riskGrade }}
            </text>
          </svg>
        </div>
        <div class="risk-level-badge" :style="`background: ${getGradient(overallScore)}`">
          {{ riskLevel.toUpperCase() }}
        </div>
        <div class="trend-indicator" :class="trendClass">
          <span class="trend-arrow">{{ trendArrow }}</span>
          <span class="trend-text">{{ trendText }}</span>
        </div>
      </div>
    </div>

    <!-- Card 2: Delay Risk -->
    <div class="glass-card" :style="fadeInStagger(1)">
      <div class="card-header">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Delay Risk</h3>
      </div>
      <div class="card-body">
        <div class="stat-row">
          <span class="stat-label">P50 (Median)</span>
          <span class="stat-value neon-text">{{ delayP50 }}d</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">P95 (Worst Case)</span>
          <span class="stat-value neon-text">{{ delayP95 }}d</span>
        </div>
        <div class="delay-band-visual">
          <div class="delay-bar" :style="`width: ${delayProbability}%`"></div>
          <span class="delay-percentage">{{ delayProbability }}%</span>
        </div>
        <div class="mini-chart">
          <!-- Delay band visualization -->
          <div class="band-container">
            <div class="band p50-band" :style="`width: ${(delayP50 / baseTransit * 100)}%`"></div>
            <div class="band p95-band" :style="`width: ${(delayP95 / baseTransit * 100)}%`"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Card 3: Financial Exposure -->
    <div class="glass-card" :style="fadeInStagger(2)">
      <div class="card-header">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Financial Exposure</h3>
      </div>
      <div class="card-body">
        <div class="stat-row">
          <span class="stat-label">Expected Loss</span>
          <span class="stat-value neon-text">${{ formatNumber(expectedLoss) }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">VaR 95%</span>
          <span class="stat-value text-orange-400">${{ formatNumber(var95) }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Max Exposure</span>
          <span class="stat-value text-red-400">${{ formatNumber(maxExposure) }}</span>
        </div>
        <!-- Mini bar chart -->
        <div class="financial-bars">
          <div class="bar-item">
            <div class="bar expected-bar" :style="`width: ${(expectedLoss / maxExposure * 100)}%`"></div>
          </div>
          <div class="bar-item">
            <div class="bar var-bar" :style="`width: ${(var95 / maxExposure * 100)}%`"></div>
          </div>
          <div class="bar-item">
            <div class="bar max-bar" style="width: 100%"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Card 4: ESG Impact -->
    <div class="glass-card" :style="fadeInStagger(3)">
      <div class="card-header">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">ESG Impact</h3>
      </div>
      <div class="card-body">
        <div class="esg-score-large neon-text">{{ esgScore.toFixed(1) }}</div>
        <div class="esg-breakdown">
          <div class="esg-item">
            <span class="esg-label">E</span>
            <div class="esg-bar" :style="`width: ${environmental}%; background: #66BB6A`"></div>
            <span class="esg-value">{{ environmental }}</span>
          </div>
          <div class="esg-item">
            <span class="esg-label">S</span>
            <div class="esg-bar" :style="`width: ${social}%; background: #42A5F5`"></div>
            <span class="esg-value">{{ social }}</span>
          </div>
          <div class="esg-item">
            <span class="esg-label">G</span>
            <div class="esg-bar" :style="`width: ${governance}%; background: #AB47BC`"></div>
            <span class="esg-value">{{ governance }}</span>
          </div>
        </div>
        <div class="esg-indicator" :class="esgIndicatorClass">
          {{ esgIndicatorText }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { getRiskColor, getGradient } from '../utils/riskColorMap';
import { fadeInStagger } from '../utils/animation';

const props = defineProps({
  overallScore: { type: Number, required: true },
  riskLevel: { type: String, required: true },
  riskGrade: { type: String, required: true },
  delayP50: { type: Number, default: 0 },
  delayP95: { type: Number, default: 0 },
  delayProbability: { type: Number, default: 0 },
  baseTransit: { type: Number, default: 22 },
  expectedLoss: { type: Number, default: 0 },
  var95: { type: Number, default: 0 },
  maxExposure: { type: Number, default: 0 },
  esgScore: { type: Number, default: 50 },
  environmental: { type: Number, default: 50 },
  social: { type: Number, default: 50 },
  governance: { type: Number, default: 50 }
});

const riskColors = computed(() => getRiskColor(props.overallScore));

// Circular gauge calculations (60% arc)
const arcPath = 'M 40 100 A 60 60 0 0 1 160 100';
const arcLength = 188.5; // Approximate arc length
const scoreProgress = computed(() => (props.overallScore / 100) * arcLength);

const trendClass = computed(() => {
  if (props.overallScore < 40) return 'trend-down';
  if (props.overallScore > 60) return 'trend-up';
  return 'trend-neutral';
});

const trendArrow = computed(() => {
  if (props.overallScore < 40) return '↓';
  if (props.overallScore > 60) return '↑';
  return '→';
});

const trendText = computed(() => {
  if (props.overallScore < 40) return 'Improving';
  if (props.overallScore > 60) return 'Watch';
  return 'Stable';
});

const esgIndicatorClass = computed(() => {
  if (props.esgScore < 40) return 'esg-good';
  if (props.esgScore < 60) return 'esg-medium';
  return 'esg-poor';
});

const esgIndicatorText = computed(() => {
  if (props.esgScore < 40) return 'GOOD';
  if (props.esgScore < 60) return 'MEDIUM';
  return 'NEEDS IMPROVEMENT';
});

const formatNumber = (num) => {
  return num >= 1000 ? (num / 1000).toFixed(1) + 'k' : num.toFixed(0);
};
</script>

<style scoped>
.glass-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
  border-color: rgba(79, 195, 247, 0.4);
  box-shadow: 0 0 20px rgba(79, 195, 247, 0.3), 0 8px 32px rgba(0, 0, 0, 0.4);
  transform: translateY(-4px);
}

.card-header {
  margin-bottom: 1rem;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.gauge-container {
  display: flex;
  justify-content: center;
  margin: 0.5rem 0;
}

.gauge-svg {
  width: 200px;
  height: 120px;
}

.gauge-progress {
  transition: stroke-dasharray 1s cubic-bezier(.22, 1.2, .36, 1);
}

.gauge-score {
  fill: #4FC3F7;
  font-size: 32px;
  font-weight: 700;
  filter: drop-shadow(0 0 10px rgba(79, 195, 247, 0.6));
}

.gauge-label {
  fill: #94A3B8;
  font-size: 16px;
  font-weight: 600;
}

.risk-level-badge {
  text-align: center;
  padding: 0.5rem 1rem;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.875rem;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.trend-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem;
}

.trend-arrow {
  font-size: 1.5rem;
  font-weight: 700;
}

.trend-down { color: #10B981; }
.trend-up { color: #EF4444; }
.trend-neutral { color: #F59E0B; }

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #94A3B8;
  font-size: 0.875rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff;
}

.neon-text {
  color: #4FC3F7;
  text-shadow: 0 0 10px rgba(79, 195, 247, 0.6);
}

.delay-band-visual {
  position: relative;
  height: 32px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  padding: 0 0.5rem;
}

.delay-bar {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, #4FC3F7, #0288D1);
  transition: width 1s cubic-bezier(.22, 1.2, .36, 1);
  box-shadow: 0 0 20px rgba(79, 195, 247, 0.4);
}

.delay-percentage {
  position: relative;
  z-index: 1;
  margin-left: auto;
  font-weight: 700;
  color: #fff;
}

.band-container {
  display: flex;
  gap: 4px;
  margin-top: 0.5rem;
}

.band {
  height: 8px;
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(.22, 1.2, .36, 1);
}

.p50-band {
  background: rgba(79, 195, 247, 0.4);
}

.p95-band {
  background: rgba(239, 68, 68, 0.6);
}

.financial-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 0.5rem;
}

.bar-item {
  position: relative;
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(.22, 1.2, .36, 1);
}

.expected-bar {
  background: linear-gradient(90deg, #4FC3F7, #0288D1);
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.4);
}

.var-bar {
  background: linear-gradient(90deg, #F59E0B, #D97706);
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.4);
}

.max-bar {
  background: linear-gradient(90deg, #EF4444, #DC2626);
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
}

.esg-score-large {
  font-size: 3rem;
  font-weight: 700;
  text-align: center;
  margin: 0.5rem 0;
}

.esg-breakdown {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.esg-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.esg-label {
  width: 24px;
  font-weight: 700;
  color: #94A3B8;
}

.esg-bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(.22, 1.2, .36, 1);
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
}

.esg-value {
  width: 32px;
  text-align: right;
  font-size: 0.875rem;
  color: #94A3B8;
}

.esg-indicator {
  margin-top: 0.5rem;
  padding: 0.5rem;
  border-radius: 8px;
  text-align: center;
  font-weight: 700;
  font-size: 0.75rem;
}

.esg-good {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.esg-medium {
  background: rgba(245, 158, 11, 0.2);
  color: #F59E0B;
}

.esg-poor {
  background: rgba(239, 68, 68, 0.2);
  color: #EF4444;
}
</style>






