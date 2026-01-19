<template>
  <GlassCard padding="p-6">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-white mb-1">AI Risk Explanation</h3>
      <p class="text-sm text-gray-400">Intelligent insights and recommendations</p>
    </div>

    <div class="space-y-6 max-h-[600px] overflow-y-auto scrollbar-thin pr-2">
      <NarrativeSection
        v-for="section in sections"
        :key="section.id"
        :section="section"
        :isActive="activeSection === section.id"
        @click="scrollToSection(section.id)"
      />

      <!-- Empty State -->
      <div v-if="sections.length === 0" class="text-center py-12">
        <div class="text-5xl mb-4">🤖</div>
        <p class="text-gray-400">No AI explanations available yet</p>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import { useExplanationStore } from '../../stores/explanationStore'
import GlassCard from '../shared/GlassCard.vue'
import NarrativeSection from './NarrativeSection.vue'

const explanationStore = useExplanationStore()

const sections = computed(() => explanationStore.sections)
const activeSection = computed(() => explanationStore.activeSection)

function scrollToSection(sectionId) {
  explanationStore.scrollToSection(sectionId)
}

// Mock data for demo
const mockSections = [
  {
    id: 'overview',
    title: 'Risk Summary',
    content: 'Your shipment faces elevated risk (72/100) primarily due to geopolitical instability in transit regions and adverse weather patterns. The combination of sanctions exposure and port congestion creates a compound risk scenario.',
    insights: [
      'Geopolitical risk score: 85/100 - Critical level',
      'Weather risk increasing due to typhoon season',
      'Port congestion at 70% capacity'
    ],
    severity: 'high',
    recommendations: [
      'Consider alternate routes avoiding high-risk zones',
      'Add buffer time of 5-7 days to expected delivery',
      'Increase insurance coverage by 20%'
    ]
  },
  {
    id: 'drivers',
    title: 'Key Risk Drivers',
    content: 'Three main factors contribute to the elevated risk: sanctions exposure (90 impact), weather disruptions (65 impact), and operational constraints (70 impact). These factors have shown strong correlation in historical data.',
    insights: [
      'Sanctions risk affects 40% of transit route',
      'Storm forecast with 75% probability',
      'Carrier reliability below historical average'
    ],
    severity: 'medium'
  }
]

// Set mock data
explanationStore.setNarrative({ sections: mockSections })
</script>






