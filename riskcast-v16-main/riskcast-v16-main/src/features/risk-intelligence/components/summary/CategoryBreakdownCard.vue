<template>
  <GlassCard padding="p-6">
    <h3 class="text-lg font-semibold text-white mb-4">Risk by Category</h3>
    
    <div class="space-y-4">
      <div 
        v-for="category in sortedCategories"
        :key="category.id"
        @click="$emit('categoryClick', category)"
        class="cursor-pointer hover:bg-white/5 p-2 rounded-lg transition-smooth"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="text-xl">{{ getCategoryIcon(category.id) }}</span>
            <span class="text-sm font-medium text-gray-300">
              {{ category.name }}
            </span>
          </div>
          <RiskBadge :score="category.score" size="sm" />
        </div>
        
        <!-- Stacked Bar -->
        <div class="h-2 bg-white/10 rounded-full overflow-hidden">
          <div 
            class="h-full transition-all duration-500"
            :style="{
              width: `${category.score}%`,
              background: getCategoryGradient(category.id)
            }"
          ></div>
        </div>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import { CATEGORY_COLORS } from '../../constants/colorPalette'
import GlassCard from '../shared/GlassCard.vue'
import RiskBadge from '../shared/RiskBadge.vue'

const props = defineProps({
  categories: {
    type: Array,
    required: true
  }
})

defineEmits(['categoryClick'])

const sortedCategories = computed(() => {
  return [...props.categories].sort((a, b) => b.score - a.score)
})

function getCategoryIcon(categoryId) {
  return CATEGORY_COLORS[categoryId]?.icon || '📊'
}

function getCategoryGradient(categoryId) {
  const color = CATEGORY_COLORS[categoryId]?.bg || '#4FC3F7'
  return `linear-gradient(90deg, ${color}dd 0%, ${color}88 100%)`
}
</script>






