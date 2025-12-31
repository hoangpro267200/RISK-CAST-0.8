<template>
  <div class="parameter-control">
    <div class="flex items-center justify-between mb-2">
      <label class="text-sm text-gray-300">{{ parameter.name }}</label>
      <span class="text-sm font-semibold text-neon-cyan">
        {{ currentValue }}{{ parameter.unit }}
      </span>
    </div>
    
    <input
      v-if="parameter.type === 'slider'"
      type="range"
      :min="parameter.min"
      :max="parameter.max"
      :step="parameter.step || 1"
      :value="currentValue"
      @input="handleChange"
      class="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  parameter: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['change'])

const currentValue = ref(props.parameter.value)

function handleChange(event) {
  currentValue.value = Number(event.target.value)
  emit('change', {
    id: props.parameter.id,
    value: currentValue.value
  })
}
</script>

<style scoped>
.slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: #4FC3F7;
  cursor: pointer;
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.5);
}

.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: #4FC3F7;
  cursor: pointer;
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.5);
  border: none;
}
</style>






