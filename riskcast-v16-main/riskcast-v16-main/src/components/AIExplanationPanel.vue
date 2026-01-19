<template>
  <div class="ai-explanation-panel glass-card">
    <div class="panel-header">
      <h2 class="text-xl font-bold text-white mb-2">
        <span class="brain-icon">🧠</span> AI Explanation
      </h2>
      <p class="text-sm text-gray-400">Natural language risk insights</p>
    </div>
    
    <div class="explanation-content" ref="contentContainer">
      <!-- Executive Summary Bubble -->
      <div class="explanation-bubble executive" :style="fadeIn(0)">
        <div class="bubble-header">📊 Executive Summary</div>
        <div class="bubble-content">{{ executiveSummary }}</div>
      </div>
      
      <!-- Key Drivers Bubbles -->
      <div
        v-for="(driver, index) in keyDrivers"
        :key="driver.name"
        class="explanation-bubble driver"
        :style="fadeIn(index + 1)"
      >
        <div class="bubble-header">
          🎯 Key Driver: {{ driver.display_name }} ({{ driver.score }}/100)
        </div>
        <div class="bubble-content">
          <p class="driver-reason">→ {{ driver.short_reason }}</p>
          <p class="driver-action"><strong>Action:</strong> {{ driver.suggested_action }}</p>
        </div>
      </div>
      
      <!-- What-If Insights -->
      <div
        v-for="(insight, index) in whatIfInsights"
        :key="insight.change"
        class="explanation-bubble what-if"
        :style="fadeIn(keyDrivers.length + index + 1)"
      >
        <div class="bubble-header">💡 What-If: {{ insight.change }}</div>
        <div class="bubble-content">
          <div class="score-comparison">
            <span class="score-before">{{ insight.original_score }}</span>
            <span class="arrow">→</span>
            <span class="score-after">{{ insight.new_score }}</span>
            <span class="delta" :class="insight.delta < 0 ? 'positive' : 'negative'">
              {{ insight.delta > 0 ? '+' : '' }}{{ insight.delta.toFixed(1) }}
            </span>
          </div>
          <p class="insight-comment">{{ insight.comment }}</p>
        </div>
      </div>
      
      <!-- Confidence Badge -->
      <div class="confidence-badge" :style="fadeIn(keyDrivers.length + whatIfInsights.length + 1)">
        <span class="confidence-label">Confidence:</span>
        <span class="confidence-value">{{ (confidence * 100).toFixed(0) }}%</span>
        <div class="confidence-bar">
          <div class="confidence-fill" :style="`width: ${confidence * 100}%`"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps({
  executiveSummary: { type: String, required: true },
  keyDrivers: { type: Array, default: () => [] },
  whatIfInsights: { type: Array, default: () => [] },
  confidence: { type: Number, default: 0.85 }
});

const contentContainer = ref(null);

const fadeIn = (index) => ({
  animation: `fadeInUp 0.6s cubic-bezier(.22, 1.2, .36, 1) ${index * 0.15}s both`
});

onMounted(() => {
  // Auto-scroll animation could be added here
});
</script>

<style scoped>
.ai-explanation-panel {
  max-height: 800px;
  overflow-y: auto;
}

.glass-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.panel-header {
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(79, 195, 247, 0.2);
  padding-bottom: 1rem;
}

.brain-icon {
  font-size: 1.5rem;
  margin-right: 0.5rem;
}

.explanation-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.explanation-bubble {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(79, 195, 247, 0.3);
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.explanation-bubble:hover {
  border-color: rgba(79, 195, 247, 0.6);
  box-shadow: 0 0 20px rgba(79, 195, 247, 0.2);
  transform: translateX(4px);
}

.explanation-bubble.executive {
  background: rgba(79, 195, 247, 0.1);
  border-width: 2px;
}

.bubble-header {
  font-weight: 700;
  color: #4FC3F7;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.bubble-content {
  color: #E2E8F0;
  line-height: 1.6;
  font-size: 0.875rem;
}

.driver-reason {
  margin-bottom: 0.5rem;
  color: #CBD5E1;
}

.driver-action {
  color: #10B981;
}

.score-comparison {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.score-before, .score-after {
  font-size: 1.25rem;
  color: #4FC3F7;
}

.arrow {
  color: #94A3B8;
}

.delta {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.delta.positive {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.delta.negative {
  background: rgba(239, 68, 68, 0.2);
  color: #EF4444;
}

.insight-comment {
  color: #94A3B8;
  font-size: 0.8125rem;
}

.confidence-badge {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(79, 195, 247, 0.05);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 12px;
}

.confidence-label {
  font-weight: 600;
  color: #94A3B8;
}

.confidence-value {
  font-weight: 700;
  font-size: 1.25rem;
  color: #4FC3F7;
}

.confidence-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #4FC3F7, #0288D1);
  border-radius: 4px;
  transition: width 1s cubic-bezier(.22, 1.2, .36, 1);
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.6);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>






