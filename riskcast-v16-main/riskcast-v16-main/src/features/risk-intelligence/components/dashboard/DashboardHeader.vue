<template>
  <div class="dashboard-header glass-card p-4 mb-6">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <!-- Left: Title & Info -->
      <div class="flex-1">
        <div class="flex items-center gap-3 mb-2">
          <h1 class="text-2xl font-bold text-gradient-blue">
            RiskCast Intelligence
          </h1>
          <PersonaBadge />
        </div>
        
        <div class="flex items-center gap-4 text-sm text-gray-400">
          <span>Shipment: <span class="text-white font-mono">{{ shipmentId }}</span></span>
          <span>•</span>
          <span>Updated: {{ formattedLastUpdated }}</span>
          <span v-if="isLoading" class="text-neon-cyan animate-pulse">● Syncing...</span>
        </div>
      </div>

      <!-- Right: Controls -->
      <div class="flex items-center gap-3">
        <PersonaSwitcher />
        
        <button
          @click="$emit('refresh')"
          :disabled="isLoading"
          class="px-4 py-2 glass-card hover:bg-white/10 rounded-lg transition-smooth disabled:opacity-50"
          title="Refresh data"
        >
          <span :class="{ 'animate-spin': isLoading }">🔄</span>
        </button>
        
        <button
          @click="$emit('export')"
          class="px-4 py-2 glass-card hover:bg-white/10 rounded-lg transition-smooth"
          title="Export report"
        >
          📥 Export
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatRelativeTime } from '../../utils/formatters/dateFormatter'
import PersonaSwitcher from '../persona/PersonaSwitcher.vue'
import PersonaBadge from '../persona/PersonaBadge.vue'

const props = defineProps({
  shipmentId: {
    type: String,
    default: 'MOCK-001'
  },
  lastUpdated: {
    type: Date,
    default: () => new Date()
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['refresh', 'export'])

const formattedLastUpdated = computed(() => {
  return formatRelativeTime(props.lastUpdated)
})
</script>






