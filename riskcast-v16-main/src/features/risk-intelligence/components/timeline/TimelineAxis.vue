<template>
  <g class="timeline-axis">
    <!-- Axis line -->
    <line
      :x1="0"
      :x2="width"
      :y1="axisY"
      :y2="axisY"
      stroke="rgba(255,255,255,0.2)"
      stroke-width="1"
    />

    <!-- Ticks and labels -->
    <g
      v-for="(tick, index) in ticks"
      :key="index"
      class="tick"
    >
      <line
        :x1="tick.x"
        :x2="tick.x"
        :y1="axisY"
        :y2="axisY + 6"
        stroke="rgba(255,255,255,0.3)"
        stroke-width="1"
      />
      <text
        :x="tick.x"
        :y="axisY + 20"
        text-anchor="middle"
        class="text-xs fill-gray-400"
      >
        {{ tick.label }}
      </text>
    </g>
  </g>
</template>

<script setup>
import { computed } from 'vue'
import { getTimeTicks, formatTimelineDate } from '../../utils/visualization/timelineLayout'

const props = defineProps({
  timeScale: {
    type: Function,
    required: true
  },
  height: {
    type: Number,
    required: true
  }
})

const axisY = computed(() => props.height - 40)
const width = computed(() => props.timeScale.range()[1])

const ticks = computed(() => {
  const tickDates = getTimeTicks(props.timeScale, 8)
  return tickDates.map(date => ({
    x: props.timeScale(date),
    label: formatTimelineDate(date, 'day')
  }))
})
</script>






