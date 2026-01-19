<template>
  <div class="persona-badge glass-card px-3 py-1 inline-flex items-center gap-2 rounded-full">
    <span class="text-lg">{{ persona.icon }}</span>
    <span class="text-xs font-medium text-white">{{ persona.name }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePersonaStore } from '../../stores/personaStore'

const personaStore = usePersonaStore()
const persona = computed(() => personaStore.currentConfig)
</script>






