<template>
  <GlassCard padding="p-6">
    <h3 class="text-lg font-semibold text-white mb-4">Risk Layers</h3>
    
    <!-- Grid of Mini Layer Cards -->
    <div class="grid grid-cols-2 gap-3">
      <div
        v-for="(layer, index) in topLayers"
        :key="layer.id"
        @click="$emit('layerClick', layer)"
        class="glass-card p-3 cursor-pointer hover:bg-white/10 transition-smooth"
        :class="{ 'ring-1 ring-neon-cyan': layer.highlighted }"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-medium text-gray-300 truncate">
            {{ layer.name }}
          </span>
          <RiskBadge :score="layer.score" size="sm" />
        </div>
        
        <!-- Mini Progress Bar -->
        <div class="h-1 bg-white/10 rounded-full overflow-hidden">
          <div 
            class="h-full transition-all duration-500"
            :style="{
              width: `${layer.score}%`,
              backgroundColor: layer.color
            }"
          ></div>
        </div>
      </div>
    </div>

    <!-- View All Link -->
    <button 
      v-if="layers.length > maxDisplay"
      @click="$emit('viewAll')"
      class="mt-4 w-full text-sm text-neon-cyan hover:text-neon-blue transition-smooth"
    >
      View all {{ layers.length }} layers →
    </button>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import GlassCard from '../shared/GlassCard.vue'
import RiskBadge from '../shared/RiskBadge.vue'

const props = defineProps({
  layers: {
    type: Array,
    required: true
  },
  maxDisplay: {
    type: Number,
    default: 8
  }
})

defineEmits(['layerClick', 'viewAll'])

const topLayers = computed(() => {
  return [...props.layers]
    .sort((a, b) => b.score - a.score)
    .slice(0, props.maxDisplay)
})
</script>






