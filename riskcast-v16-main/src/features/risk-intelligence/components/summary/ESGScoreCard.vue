<template>
  <GlassCard padding="p-6">
    <h3 class="text-lg font-semibold text-white mb-4">ESG Score</h3>
    
    <div class="grid grid-cols-3 gap-4">
      <!-- Environmental -->
      <div class="text-center">
        <div class="glass-card p-4 mb-2">
          <div class="text-3xl mb-2">{{ esg.environmental || 0 }}</div>
          <div class="text-xs text-gray-500">Environmental</div>
        </div>
        <div class="h-1 bg-white/10 rounded-full overflow-hidden">
          <div 
            class="h-full bg-green-500 transition-all duration-500"
            :style="{ width: `${esg.environmental}%` }"
          ></div>
        </div>
      </div>

      <!-- Social -->
      <div class="text-center">
        <div class="glass-card p-4 mb-2">
          <div class="text-3xl mb-2">{{ esg.social || 0 }}</div>
          <div class="text-xs text-gray-500">Social</div>
        </div>
        <div class="h-1 bg-white/10 rounded-full overflow-hidden">
          <div 
            class="h-full bg-blue-500 transition-all duration-500"
            :style="{ width: `${esg.social}%` }"
          ></div>
        </div>
      </div>

      <!-- Governance -->
      <div class="text-center">
        <div class="glass-card p-4 mb-2">
          <div class="text-3xl mb-2">{{ esg.governance || 0 }}</div>
          <div class="text-xs text-gray-500">Governance</div>
        </div>
        <div class="h-1 bg-white/10 rounded-full overflow-hidden">
          <div 
            class="h-full bg-purple-500 transition-all duration-500"
            :style="{ width: `${esg.governance}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Average -->
    <NeonDivider class="my-4" />
    
    <div class="text-center">
      <div class="text-sm text-gray-400 mb-1">Overall ESG</div>
      <div class="text-3xl font-bold text-white">{{ overallESG }}</div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import GlassCard from '../shared/GlassCard.vue'
import NeonDivider from '../shared/NeonDivider.vue'

const props = defineProps({
  esg: {
    type: Object,
    required: true
  }
})

const overallESG = computed(() => {
  const e = props.esg.environmental || 0
  const s = props.esg.social || 0
  const g = props.esg.governance || 0
  return Math.round((e + s + g) / 3)
})
</script>






