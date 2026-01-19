<template>
  <div class="risk-dashboard min-h-screen bg-gray-950 p-4 md:p-6 lg:p-8">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <div class="loading-shimmer w-32 h-32 rounded-full mx-auto mb-4"></div>
        <p class="text-gray-400">Loading risk intelligence...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center min-h-screen">
      <div class="glass-card p-8 max-w-md text-center">
        <div class="text-red-400 text-6xl mb-4">⚠️</div>
        <h2 class="text-2xl font-bold text-white mb-2">Error Loading Data</h2>
        <p class="text-gray-400 mb-4">{{ error.message }}</p>
        <button 
          @click="retry" 
          class="px-6 py-2 bg-neon-blue text-white rounded-lg hover:bg-opacity-90 transition-smooth"
        >
          Retry
        </button>
      </div>
    </div>

    <!-- Main Dashboard -->
    <div v-else class="container mx-auto max-w-7xl">
      <DashboardHeader
        :shipmentId="props.shipmentId"
        :lastUpdated="lastFetched"
        :isLoading="isLoading"
        @refresh="loadData"
        @export="handleExport"
      />
      
      <DashboardGrid
        :activeTab="activeTab"
        @tabChange="handleTabChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRiskStore } from '../../stores/riskStore'
import { useUIStore } from '../../stores/uiStore'
import { useRiskData } from '../../composables/useRiskData'
import DashboardHeader from './DashboardHeader.vue'
import DashboardGrid from './DashboardGrid.vue'

// Props
const props = defineProps({
  shipmentId: {
    type: String,
    default: 'MOCK-001'
  },
  initialPersona: {
    type: String,
    default: 'logistics'
  }
})

// Stores & Composables
const riskStore = useRiskStore()
const uiStore = useUIStore()
const { loadMockData } = useRiskData()

// State
const isLoading = computed(() => riskStore.isLoading)
const error = computed(() => riskStore.error)
const lastFetched = computed(() => riskStore.lastFetched)
const activeTab = computed(() => uiStore.currentTab)

// Methods
async function retry() {
  await loadData()
}

async function loadData() {
  try {
    riskStore.setLoading(true)
    await loadMockData()
  } catch (err) {
    console.error('Failed to load data:', err)
  } finally {
    riskStore.setLoading(false)
  }
}

function handleTabChange(tab) {
  uiStore.setActiveTab(tab)
}

function handleExport() {
  console.log('Export functionality - would download PDF/CSV')
  alert('Export feature coming soon!')
}

// Lifecycle
onMounted(async () => {
  await loadData()
})
</script>

