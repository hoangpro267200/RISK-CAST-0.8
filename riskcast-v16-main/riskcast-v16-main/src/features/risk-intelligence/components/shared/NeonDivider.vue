<template>
  <div 
    :class="['neon-divider', orientationClass, sizeClass]"
    :style="customStyle"
  ></div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  color: {
    type: String,
    default: '#4FC3F7' // Neon blue
  },
  orientation: {
    type: String,
    default: 'horizontal', // 'horizontal' | 'vertical'
    validator: (value) => ['horizontal', 'vertical'].includes(value)
  },
  size: {
    type: String,
    default: 'md', // 'sm' | 'md' | 'lg'
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  glow: {
    type: Boolean,
    default: true
  }
})

const orientationClass = computed(() => {
  return props.orientation === 'horizontal' ? 'w-full' : 'h-full'
})

const sizeClass = computed(() => {
  const sizes = {
    horizontal: {
      sm: 'h-px',
      md: 'h-0.5',
      lg: 'h-1'
    },
    vertical: {
      sm: 'w-px',
      md: 'w-0.5',
      lg: 'w-1'
    }
  }
  
  return sizes[props.orientation][props.size]
})

const customStyle = computed(() => {
  const gradient = props.orientation === 'horizontal'
    ? `linear-gradient(to right, transparent, ${props.color}, transparent)`
    : `linear-gradient(to bottom, transparent, ${props.color}, transparent)`
  
  const boxShadow = props.glow
    ? `0 0 8px ${props.color}80, 0 0 16px ${props.color}40`
    : 'none'
  
  return {
    background: gradient,
    boxShadow
  }
})
</script>

<style scoped>
.neon-divider {
  position: relative;
  transition: opacity 0.3s ease;
}

.neon-divider:hover {
  opacity: 0.8;
}
</style>






