<template>
  <div 
    :class="[
      'glass-card',
      variantClass,
      glowClass,
      paddingClass,
      'relative overflow-hidden'
    ]"
    :style="customStyles"
  >
    <!-- Glow effect for critical items -->
    <div 
      v-if="glowColor" 
      class="absolute inset-0 opacity-20 pointer-events-none"
      :style="glowStyle"
    ></div>
    
    <!-- Content -->
    <slot></slot>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'default', // 'default' | 'hero' | 'compact'
    validator: (value) => ['default', 'hero', 'compact'].includes(value)
  },
  glowColor: {
    type: String,
    default: null // Hex color for neon glow
  },
  padding: {
    type: String,
    default: 'p-6' // Tailwind padding class
  },
  interactive: {
    type: Boolean,
    default: false
  }
})

const variantClass = computed(() => {
  const variants = {
    default: 'backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl shadow-2xl',
    hero: 'backdrop-blur-3xl bg-white/8 border border-white/15 rounded-3xl shadow-2xl',
    compact: 'backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl shadow-xl'
  }
  
  const base = variants[props.variant] || variants.default
  const interactive = props.interactive ? 'cursor-pointer hover:bg-white/10 hover:border-white/20 transition-smooth' : ''
  
  return `${base} ${interactive}`
})

const glowClass = computed(() => {
  if (!props.glowColor) return ''
  return 'ring-1 ring-opacity-50'
})

const paddingClass = computed(() => {
  return props.padding
})

const customStyles = computed(() => {
  if (!props.glowColor) return {}
  
  return {
    '--glow-color': props.glowColor
  }
})

const glowStyle = computed(() => {
  if (!props.glowColor) return {}
  
  return {
    boxShadow: `
      0 0 20px ${props.glowColor},
      0 0 40px ${props.glowColor}80,
      0 0 60px ${props.glowColor}40
    `
  }
})
</script>

<style scoped>
.glass-card {
  position: relative;
}

.ring-1 {
  --tw-ring-color: var(--glow-color, transparent);
}
</style>






