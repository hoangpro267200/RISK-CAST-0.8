<template>
  <div class="persona-switcher glass-card">
    <div class="persona-tabs">
      <button
        v-for="persona in personas"
        :key="persona.id"
        :class="['persona-tab', { active: activePersona === persona.id }]"
        @click="selectPersona(persona.id)"
      >
        <span class="persona-icon">{{ persona.icon }}</span>
        <span class="persona-label">{{ persona.label }}</span>
      </button>
    </div>
    
    <div class="persona-content">
      <h3 class="persona-headline">{{ currentView.headline }}</h3>
      <p class="persona-summary">{{ currentView.summary }}</p>
      <div class="persona-focus">
        <span class="focus-label">Focus Areas:</span>
        <div class="focus-tags">
          <span v-for="item in currentView.focus" :key="item" class="focus-tag">
            {{ item.replace('_', ' ') }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  personaViews: { type: Object, required: true }
});

const activePersona = ref('cfo');

const personas = [
  { id: 'cfo', label: 'CFO', icon: '💼' },
  { id: 'logistics_manager', label: 'Logistics', icon: '📦' },
  { id: 'risk_officer', label: 'Risk Officer', icon: '🛡️' }
];

const currentView = computed(() => {
  return props.personaViews[activePersona.value] || {
    headline: 'View',
    summary: '',
    focus: []
  };
});

const selectPersona = (personaId) => {
  activePersona.value = personaId;
};
</script>

<style scoped>
.glass-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.persona-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(79, 195, 247, 0.2);
  padding-bottom: 0.5rem;
}

.persona-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: transparent;
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 12px;
  color: #94A3B8;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.persona-tab:hover {
  border-color: rgba(79, 195, 247, 0.4);
  background: rgba(79, 195, 247, 0.1);
}

.persona-tab.active {
  background: rgba(79, 195, 247, 0.2);
  border-color: #4FC3F7;
  color: #4FC3F7;
  box-shadow: 0 0 20px rgba(79, 195, 247, 0.3);
}

.persona-icon {
  font-size: 1.25rem;
}

.persona-content {
  padding: 1rem;
}

.persona-headline {
  font-size: 1.25rem;
  font-weight: 700;
  color: #4FC3F7;
  margin-bottom: 1rem;
}

.persona-summary {
  color: #E2E8F0;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.persona-focus {
  margin-top: 1rem;
}

.focus-label {
  font-size: 0.875rem;
  color: #94A3B8;
  margin-bottom: 0.5rem;
  display: block;
}

.focus-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.focus-tag {
  padding: 0.25rem 0.75rem;
  background: rgba(79, 195, 247, 0.1);
  border: 1px solid rgba(79, 195, 247, 0.3);
  border-radius: 12px;
  font-size: 0.75rem;
  color: #4FC3F7;
  text-transform: capitalize;
}
</style>






