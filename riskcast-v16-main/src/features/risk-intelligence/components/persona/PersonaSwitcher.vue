<template>
  <div class="persona-switcher relative">
    <button
      @click="isOpen = !isOpen"
      class="flex items-center gap-2 px-4 py-2 glass-card hover:bg-white/10 transition-smooth rounded-lg"
    >
      <span class="text-xl">{{ currentPersona.icon }}</span>
      <span class="text-sm font-medium text-white">{{ currentPersona.name }}</span>
      <span class="text-xs text-gray-400">▼</span>
    </button>

    <!-- Dropdown -->
    <div
      v-if="isOpen"
      class="absolute top-full right-0 mt-2 glass-card p-2 rounded-lg shadow-2xl z-50 min-w-[200px]"
    >
      <button
        v-for="persona in personas"
        :key="persona.id"
        @click="selectPersona(persona.id)"
        class="w-full flex items-center gap-3 px-3 py-2 hover:bg-white/10 rounded-lg transition-smooth text-left"
        :class="{ 'ring-1 ring-neon-cyan': isActive(persona.id) }"
      >
        <span class="text-xl">{{ persona.icon }}</span>
        <div class="flex-1">
          <div class="text-sm font-medium text-white">{{ persona.name }}</div>
          <div class="text-xs text-gray-400">{{ persona.description }}</div>
        </div>
        <span v-if="isActive(persona.id)" class="text-neon-cyan">✓</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usePersonaStore } from '../../stores/personaStore'
import { PERSONA_CONFIGS } from '../../constants/personaConfigs'

const personaStore = usePersonaStore()
const isOpen = ref(false)

const currentPersona = computed(() => personaStore.currentConfig)

const personas = Object.values(PERSONA_CONFIGS)

function selectPersona(personaId) {
  personaStore.setPersona(personaId)
  isOpen.value = false
}

function isActive(personaId) {
  return personaStore.activePersona === personaId
}
</script>






