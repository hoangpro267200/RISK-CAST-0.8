<template>
  <GlassCard padding="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-white mb-1">Risk Timeline</h3>
        <p class="text-sm text-gray-400">Sequential risk events and phases</p>
      </div>
      
      <!-- Zoom Controls -->
      <div class="flex items-center gap-2">
        <button
          @click="zoomOut"
          class="px-3 py-1 text-sm bg-white/5 hover:bg-white/10 rounded-lg transition-smooth"
        >
          −
        </button>
        <span class="text-sm text-gray-400">{{ zoomLevel }}x</span>
        <button
          @click="zoomIn"
          class="px-3 py-1 text-sm bg-white/5 hover:bg-white/10 rounded-lg transition-smooth"
        >
          +
        </button>
      </div>
    </div>

    <!-- Timeline Container -->
    <div 
      class="timeline-container relative bg-gray-900/50 rounded-xl overflow-x-auto scrollbar-thin"
      :style="{ height: `${height}px` }"
    >
      <svg
        :width="svgWidth"
        :height="svgHeight"
        class="min-w-full"
      >
        <!-- Phase backgrounds -->
        <g class="phases">
          <TimelinePhase
            v-for="phase in timeline.phases"
            :key="phase.id"
            :phase="phase"
            :timeScale="timeScale"
            :height="svgHeight"
          />
        </g>

        <!-- Risk band area -->
        <TimelineRiskBand
          :dataPoints="riskDataPoints"
          :timeScale="timeScale"
          :height="svgHeight"
        />

        <!-- Timeline axis -->
        <TimelineAxis
          :timeScale="timeScale"
          :height="svgHeight"
        />

        <!-- Events -->
        <g class="events">
          <TimelineEvent
            v-for="event in timeline.events"
            :key="event.id"
            :event="event"
            :position="getEventPosition(event)"
            @click="handleEventClick(event)"
          />
        </g>

        <!-- Current date marker -->
        <line
          v-if="currentDateX"
          :x1="currentDateX"
          :x2="currentDateX"
          y1="0"
          :y2="svgHeight"
          stroke="#4FC3F7"
          stroke-width="2"
          stroke-dasharray="4"
        />
      </svg>
    </div>

    <!-- Legend -->
    <div class="flex flex-wrap items-center gap-4 mt-4 text-xs text-gray-400">
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-green-500"></div>
        <span>Low Risk</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
        <span>Medium Risk</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-orange-500"></div>
        <span>High Risk</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-red-500"></div>
        <span>Critical Risk</span>
      </div>
      <NeonDivider orientation="vertical" class="h-4" />
      <span>📍 Today</span>
    </div>
  </GlassCard>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRiskStore } from '../../stores/riskStore'
import { useUIStore } from '../../stores/uiStore'
import { useResponsive } from '../../composables/useResponsive'
import { createTimeScale, positionEvent } from '../../utils/visualization/timelineLayout'

import GlassCard from '../shared/GlassCard.vue'
import NeonDivider from '../shared/NeonDivider.vue'
import TimelineAxis from './TimelineAxis.vue'
import TimelinePhase from './TimelinePhase.vue'
import TimelineEvent from './TimelineEvent.vue'
import TimelineRiskBand from './TimelineRiskBand.vue'

const riskStore = useRiskStore()
const uiStore = useUIStore()
const { mobile, tablet } = useResponsive()

const height = computed(() => mobile.value ? 300 : tablet.value ? 400 : 500)
const baseWidth = computed(() => mobile.value ? 800 : tablet.value ? 1200 : 1600)
const zoomLevel = computed(() => uiStore.timelineZoom)

const svgWidth = computed(() => baseWidth.value * zoomLevel.value)
const svgHeight = computed(() => height.value)

const timeline = computed(() => riskStore.timeline)

const timeScale = computed(() => {
  return createTimeScale(timeline.value.phases, svgWidth.value)
})

// Mock risk data points for the band
const riskDataPoints = computed(() => {
  if (!timeline.value.phases || timeline.value.phases.length === 0) return []
  
  const points = []
  timeline.value.phases.forEach(phase => {
    const riskScore = { low: 20, medium: 50, high: 70, critical: 90 }[phase.riskLevel] || 50
    points.push({ date: phase.start, score: riskScore })
    points.push({ date: phase.end, score: riskScore })
  })
  return points
})

function getEventPosition(event) {
  return positionEvent(event, timeScale.value)
}

const currentDateX = computed(() => {
  if (!timeScale.value) return null
  return timeScale.value(new Date())
})

function handleEventClick(event) {
  console.log('Event clicked:', event)
}

function zoomIn() {
  uiStore.zoomIn()
}

function zoomOut() {
  uiStore.zoomOut()
}
</script>






