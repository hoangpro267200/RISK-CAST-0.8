<template>
  <div class="risk-timeline glass-card">
    <div class="timeline-header">
      <h2 class="text-xl font-bold text-white mb-2">Logistics Timeline</h2>
      <p class="text-sm text-gray-400">Journey milestones with risk overlays</p>
    </div>
    
    <div class="timeline-container">
      <!-- Timeline axis -->
      <div class="timeline-axis">
        <div class="timeline-line"></div>
        
        <!-- Milestones -->
        <div
          v-for="(milestone, index) in milestones"
          :key="milestone.id"
          class="milestone"
          :style="`left: ${milestone.position}%`"
        >
          <div class="milestone-marker" :class="milestone.status">
            <span class="milestone-icon">{{ milestone.icon }}</span>
          </div>
          <div class="milestone-label">
            <div class="milestone-name">{{ milestone.name }}</div>
            <div class="milestone-date">{{ milestone.date }}</div>
          </div>
        </div>
      </div>
      
      <!-- Risk Overlays -->
      <div class="risk-overlays">
        <!-- Delay zone shading -->
        <div v-if="showDelayZone" class="overlay delay-zone" :style="delayZoneStyle">
          <span class="overlay-label">Delay Risk Zone</span>
        </div>
        
        <!-- Weather risk shading -->
        <div v-if="showWeatherRisk" class="overlay weather-zone" :style="weatherZoneStyle">
          <span class="overlay-label">Weather Risk</span>
        </div>
        
        <!-- Shock markers -->
        <div
          v-for="shock in shockMarkers"
          :key="shock.id"
          class="shock-marker"
          :style="`left: ${shock.position}%`"
          :title="shock.description"
        >
          <span class="shock-icon">{{ shock.icon }}</span>
        </div>
      </div>
      
      <!-- Monte Carlo bands -->
      <div v-if="monteCarloData" class="mc-bands">
        <div class="mc-band p50-band" :style="`width: ${p50Width}%`">
          <span class="band-label">P50: {{ p50Days }}d</span>
        </div>
        <div class="mc-band p95-band" :style="`width: ${p95Width}%`">
          <span class="band-label">P95: {{ p95Days }}d</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  etd: { type: String, default: '15/01/2026' },
  transitTime: { type: Number, default: 22 },
  delayP50: { type: Number, default: 33 },
  delayP95: { type: Number, default: 51 },
  weatherRisk: { type: Number, default: 35 },
  shockScenarios: { type: Array, default: () => [] },
  monteCarloData: { type: Object, default: null }
});

const milestones = computed(() => [
  { id: 'etd', name: 'ETD', icon: '🚢', position: 0, status: 'completed', date: props.etd },
  { id: 'pol', name: 'POL Departure', icon: '⚓', position: 10, status: 'completed', date: '+2d' },
  { id: 'transit', name: 'Mid-Transit', icon: '🌊', position: 50, status: 'in-progress', date: '+11d' },
  { id: 'pod', name: 'POD Arrival', icon: '🏭', position: 80, status: 'pending', date: '+20d' },
  { id: 'clearance', name: 'Customs', icon: '📋', position: 90, status: 'pending', date: '+22d' },
  { id: 'delivery', name: 'Delivery', icon: '✅', position: 100, status: 'pending', date: '+24d' }
]);

const showDelayZone = computed(() => props.delayP95 > props.transitTime * 1.2);
const showWeatherRisk = computed(() => props.weatherRisk > 50);

const delayZoneStyle = computed(() => ({
  left: '60%',
  width: '35%',
  background: 'rgba(239, 68, 68, 0.15)'
}));

const weatherZoneStyle = computed(() => ({
  left: '40%',
  width: '40%',
  background: 'rgba(79, 195, 247, 0.15)'
}));

const shockMarkers = computed(() => {
  const markers = [];
  
  if (props.shockScenarios.length > 0) {
    markers.push(
      { id: 'port_strike', icon: '⚡', position: 85, description: 'Port strike risk' },
      { id: 'weather', icon: '🌧️', position: 55, description: 'Storm risk' }
    );
  }
  
  return markers;
});

const p50Days = computed(() => props.delayP50);
const p95Days = computed(() => props.delayP95);
const p50Width = computed(() => (props.delayP50 / props.delayP95 * 100));
const p95Width = computed(() => 100);
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

.timeline-header {
  margin-bottom: 2rem;
}

.timeline-container {
  position: relative;
  padding: 3rem 0;
  min-height: 200px;
}

.timeline-axis {
  position: relative;
  height: 80px;
}

.timeline-line {
  position: absolute;
  top: 40px;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #4FC3F7, #0288D1);
  border-radius: 2px;
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.4);
}

.milestone {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.milestone-marker {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
  transition: all 0.3s ease;
}

.milestone-marker.completed {
  background: rgba(16, 185, 129, 0.3);
  border: 2px solid #10B981;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
}

.milestone-marker.in-progress {
  background: rgba(245, 158, 11, 0.3);
  border: 2px solid #F59E0B;
  box-shadow: 0 0 15px rgba(245, 158, 11, 0.4);
  animation: pulse 2s infinite;
}

.milestone-marker.pending {
  background: rgba(148, 163, 184, 0.2);
  border: 2px solid #64748B;
}

.milestone-icon {
  font-size: 1.25rem;
}

.milestone-label {
  text-align: center;
}

.milestone-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: #E2E8F0;
  margin-bottom: 0.25rem;
}

.milestone-date {
  font-size: 0.625rem;
  color: #94A3B8;
}

.risk-overlays {
  position: absolute;
  top: 50px;
  left: 0;
  right: 0;
  height: 60px;
}

.overlay {
  position: absolute;
  height: 100%;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(255, 255, 255, 0.3);
}

.overlay-label {
  font-size: 0.75rem;
  color: #fff;
  font-weight: 600;
}

.shock-marker {
  position: absolute;
  top: 20px;
  transform: translateX(-50%);
  width: 32px;
  height: 32px;
  background: rgba(239, 68, 68, 0.3);
  border: 2px solid #EF4444;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.shock-marker:hover {
  transform: translateX(-50%) scale(1.2);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
}

.shock-icon {
  font-size: 1rem;
}

.mc-bands {
  position: relative;
  margin-top: 8rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mc-band {
  height: 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  padding: 0 0.75rem;
  transition: width 1s cubic-bezier(.22, 1.2, .36, 1);
}

.p50-band {
  background: rgba(79, 195, 247, 0.3);
  border: 1px solid rgba(79, 195, 247, 0.5);
}

.p95-band {
  background: rgba(239, 68, 68, 0.3);
  border: 1px solid rgba(239, 68, 68, 0.5);
}

.band-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 15px rgba(245, 158, 11, 0.4);
  }
  50% {
    box-shadow: 0 0 25px rgba(245, 158, 11, 0.7);
  }
}
</style>






