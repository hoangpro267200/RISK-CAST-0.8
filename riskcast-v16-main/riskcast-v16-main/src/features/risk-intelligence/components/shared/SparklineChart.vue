<template>
  <div class="sparkline-chart inline-block">
    <svg 
      :width="width" 
      :height="height" 
      :viewBox="`0 0 ${width} ${height}`"
      class="sparkline"
    >
      <!-- Area fill -->
      <path
        v-if="showArea"
        :d="areaPath"
        :fill="fillColor"
        :opacity="0.3"
      />
      
      <!-- Line -->
      <path
        :d="linePath"
        fill="none"
        :stroke="strokeColor"
        :stroke-width="lineWidth"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="transition-all duration-300"
      />
      
      <!-- Data points -->
      <circle
        v-if="showPoints"
        v-for="(point, index) in points"
        :key="index"
        :cx="point.x"
        :cy="point.y"
        :r="pointRadius"
        :fill="strokeColor"
        class="transition-all duration-300"
      />
      
      <!-- Last point highlight -->
      <circle
        v-if="highlightLast && points.length > 0"
        :cx="points[points.length - 1].x"
        :cy="points[points.length - 1].y"
        :r="pointRadius * 1.5"
        :fill="strokeColor"
        class="animate-pulse"
      />
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    validator: (arr) => arr.every(v => typeof v === 'number')
  },
  width: {
    type: Number,
    default: 100
  },
  height: {
    type: Number,
    default: 30
  },
  lineWidth: {
    type: Number,
    default: 2
  },
  color: {
    type: String,
    default: '#4FC3F7'
  },
  showArea: {
    type: Boolean,
    default: true
  },
  showPoints: {
    type: Boolean,
    default: false
  },
  highlightLast: {
    type: Boolean,
    default: true
  },
  smooth: {
    type: Boolean,
    default: true
  }
})

const pointRadius = 3

const min = computed(() => Math.min(...props.data))
const max = computed(() => Math.max(...props.data))
const range = computed(() => max.value - min.value || 1)

const points = computed(() => {
  const padding = props.lineWidth + pointRadius
  const xStep = (props.width - padding * 2) / (props.data.length - 1 || 1)
  const yScale = (props.height - padding * 2) / range.value
  
  return props.data.map((value, index) => ({
    x: padding + index * xStep,
    y: props.height - padding - (value - min.value) * yScale
  }))
})

const linePath = computed(() => {
  if (points.value.length === 0) return ''
  
  if (props.smooth && points.value.length > 2) {
    return smoothPath(points.value)
  }
  
  return linearPath(points.value)
})

const areaPath = computed(() => {
  if (!props.showArea || points.value.length === 0) return ''
  
  const path = linePath.value
  const firstPoint = points.value[0]
  const lastPoint = points.value[points.value.length - 1]
  
  return `${path} L ${lastPoint.x},${props.height} L ${firstPoint.x},${props.height} Z`
})

const strokeColor = computed(() => props.color)
const fillColor = computed(() => props.color)

function linearPath(pts) {
  return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`).join(' ')
}

function smoothPath(pts) {
  if (pts.length < 3) return linearPath(pts)
  
  let path = `M ${pts[0].x},${pts[0].y}`
  
  for (let i = 0; i < pts.length - 1; i++) {
    const current = pts[i]
    const next = pts[i + 1]
    const controlPointX = (current.x + next.x) / 2
    
    path += ` Q ${controlPointX},${current.y} ${controlPointX},${(current.y + next.y) / 2}`
    path += ` Q ${controlPointX},${next.y} ${next.x},${next.y}`
  }
  
  return path
}
</script>

<style scoped>
.sparkline {
  display: block;
}
</style>






