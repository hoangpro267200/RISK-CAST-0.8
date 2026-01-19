<template>
  <div class="explanation-dashboard">
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <h1 class="dashboard-title">
          <span class="title-icon">🚀</span>
          RiskCast V22 - AI Risk Analysis
        </h1>
        <div class="version-badge">v22.0</div>
      </div>
      
      <!-- Risk Summary Cards -->
      <RiskSummaryCards
        :overall-score="riskData.overall_score"
        :risk-level="riskData.risk_level"
        :risk-grade="riskData.risk_grade"
        :delay-p50="monteCarloData.p50"
        :delay-p95="monteCarloData.p95"
        :delay-probability="monteCarloData.delay_probability"
        :base-transit="transportData.transit_time"
        :expected-loss="financialData.expected_loss"
        :var95="financialData.var_95"
        :max-exposure="financialData.max_exposure"
        :esg-score="esgData.overall_score"
        :environmental="esgData.environmental"
        :social="esgData.social"
        :governance="esgData.governance"
      />
      
      <!-- Risk Driver Tree -->
      <RiskDriverTree
        :driver-tree="driverTreeData"
        :layer-scores="riskData.layer_scores"
        class="mb-8"
      />
      
      <!-- Persona Switcher -->
      <PersonaSwitcher
        :persona-views="personaViews"
        class="mb-8"
      />
      
      <!-- AI Explanation Panel -->
      <AIExplanationPanel
        :executive-summary="aiExplanation.executive_summary"
        :key-drivers="aiExplanation.key_drivers"
        :what-if-insights="aiExplanation.what_if_insights"
        :confidence="aiExplanation.confidence_score"
        class="mb-8"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import RiskSummaryCards from '../components/RiskSummaryCards.vue';
import RiskDriverTree from '../components/RiskDriverTree.vue';
import PersonaSwitcher from '../components/PersonaSwitcher.vue';
import AIExplanationPanel from '../components/AIExplanationPanel.vue';

// Mock data - in production this would come from API
const riskData = ref({
  overall_score: 38.3,
  risk_level: 'medium',
  risk_grade: 'B+',
  layer_scores: {}
});

const monteCarloData = ref({
  p50: 33.4,
  p95: 51.0,
  delay_probability: 51.5
});

const transportData = ref({
  transit_time: 22
});

const financialData = ref({
  expected_loss: 2400,
  var_95: 37500,
  max_exposure: 250000
});

const esgData = ref({
  overall_score: 33.8,
  environmental: 32.5,
  social: 38.1,
  governance: 31.2
});

const driverTreeData = ref({});
const personaViews = ref({});
const aiExplanation = ref({
  executive_summary: '',
  key_drivers: [],
  what_if_insights: [],
  confidence_score: 0.92
});

// Load data from API
const loadData = async () => {
  try {
    // In production: const response = await fetch('/api/v22/risk-assessment');
    // const data = await response.json();
    
    // For now, use mock data or data passed via props
    console.log('Dashboard mounted - ready to receive V22 data');
  } catch (error) {
    console.error('Error loading risk data:', error);
  }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.explanation-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  padding: 2rem;
}

.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.dashboard-title {
  font-size: 2rem;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-icon {
  font-size: 2.5rem;
}

.version-badge {
  padding: 0.5rem 1rem;
  background: rgba(79, 195, 247, 0.2);
  border: 1px solid #4FC3F7;
  border-radius: 20px;
  color: #4FC3F7;
  font-weight: 700;
  font-size: 0.875rem;
  box-shadow: 0 0 20px rgba(79, 195, 247, 0.3);
}
</style>






