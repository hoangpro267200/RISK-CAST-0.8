<template>
  <div 
    :class="[
      'loading-shimmer',
      shapeClass,
      sizeClass
    ]"
    :style="customStyle"
  ></div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  shape: {
    type: String,
    default: 'rectangle', // 'rectangle' | 'circle' | 'text'
    validator: (value) => ['rectangle', 'circle', 'text'].includes(value)
  },
  width: {
    type: String,
    default: null // e.g., '100%', '200px'
  },
  height: {
    type: String,
    default: null // e.g., '20px', '3rem'
  },
  size: {
    type: String,
    default: 'md', // 'sm' | 'md' | 'lg' (predefined sizes)
    validator: (value) => ['sm', 'md', 'lg', 'xl'].includes(value)
  }
})

const shapeClass = computed(() => {
  const shapes = {
    rectangle: 'rounded-lg',
    circle: 'rounded-full',
    text: 'rounded'
  }
  return shapes[props.shape] || shapes.rectangle
})

const sizeClass = computed(() => {
  // Default sizes if width/height not provided
  if (props.width || props.height) return ''
  
  const sizes = {
    rectangle: {
      sm: 'w-24 h-8',
      md: 'w-32 h-12',
      lg: 'w-48 h-16',
      xl: 'w-64 h-20'
    },
    circle: {
      sm: 'w-8 h-8',
      md: 'w-12 h-12',
      lg: 'w-16 h-16',
      xl: 'w-20 h-20'
    },
    text: {
      sm: 'w-full h-4',
      md: 'w-full h-5',
      lg: 'w-full h-6',
      xl: 'w-full h-8'
    }
  }
  
  return sizes[props.shape]?.[props.size] || sizes.rectangle.md
})

const customStyle = computed(() => {
  const style = {}
  
  if (props.width) {
    style.width = props.width
  }
  
  if (props.height) {
    style.height = props.height
  }
  
  return style
})
</script>

<style scoped>
.loading-shimmer {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.05) 0%,
    rgba(255, 255, 255, 0.1) 50%,
    rgba(255, 255, 255, 0.05) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>






