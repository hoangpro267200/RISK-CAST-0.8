<template>
  <div class="parameter-group glass-card p-4">
    <div class="flex items-center gap-2 mb-4">
      <span class="text-2xl">{{ group.icon }}</span>
      <h4 class="font-semibold text-white">{{ group.name }}</h4>
    </div>
    
    <div class="space-y-4">
      <ParameterControl
        v-for="param in group.parameters"
        :key="param.id"
        :parameter="param"
        @change="$emit('change', $event)"
      />
    </div>
  </div>
</template>

<script setup>
defineProps({
  group: {
    type: Object,
    required: true
  }
})

defineEmits(['change'])
</script>






