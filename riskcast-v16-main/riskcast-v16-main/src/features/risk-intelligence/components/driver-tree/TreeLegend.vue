<template>
  <div class="tree-legend glass-card p-4">
    <div class="flex flex-wrap items-center gap-6">
      <!-- Color Legend -->
      <div class="flex items-center gap-4">
        <span class="text-xs text-gray-400">Risk Level:</span>
        <div
          v-for="level in riskLevels"
          :key="level.name"
          class="flex items-center gap-2"
        >
          <div
            class="w-4 h-4 rounded-full"
            :style="{ backgroundColor: level.color }"
          ></div>
          <span class="text-xs text-gray-300">{{ level.label }}</span>
        </div>
      </div>

      <NeonDivider orientation="vertical" size="sm" class="h-6" />

      <!-- Size Legend -->
      <div class="flex items-center gap-4">
        <span class="text-xs text-gray-400">Node Size:</span>
        <span class="text-xs text-gray-300">Score Magnitude</span>
      </div>

      <NeonDivider orientation="vertical" size="sm" class="h-6" />

      <!-- Interaction Hint -->
      <div class="flex items-center gap-2 text-xs text-gray-400">
        <span>💡</span>
        <span>Click nodes to expand/collapse • Hover for details</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { RISK_COLORS } from '../../constants/colorPalette'
import NeonDivider from '../shared/NeonDivider.vue'

const riskLevels = [
  { name: 'low', label: 'Low', color: RISK_COLORS.low.bg },
  { name: 'medium', label: 'Medium', color: RISK_COLORS.medium.bg },
  { name: 'high', label: 'High', color: RISK_COLORS.high.bg },
  { name: 'critical', label: 'Critical', color: RISK_COLORS.critical.bg }
]
</script>






