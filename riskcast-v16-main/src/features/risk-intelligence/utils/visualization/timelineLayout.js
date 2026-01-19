import * as d3 from 'd3'

/**
 * Create time scale for timeline
 * @param {Array} phases - Timeline phases
 * @param {number} width - Container width
 * @returns {Function} D3 time scale
 */
export function createTimeScale(phases, width) {
  if (!phases || phases.length === 0) {
    return d3.scaleTime().domain([new Date(), new Date()]).range([50, width - 50])
  }

  const dates = phases.flatMap(p => [new Date(p.start), new Date(p.end)])
  const extent = d3.extent(dates)

  return d3.scaleTime()
    .domain(extent)
    .range([50, width - 50])
}

/**
 * Position event on timeline
 * @param {Object} event - Timeline event
 * @param {Function} timeScale - D3 time scale
 * @returns {{x: number, y: number}}
 */
export function positionEvent(event, timeScale) {
  return {
    x: timeScale(new Date(event.date)),
    y: 50 // Fixed Y or based on severity
  }
}

/**
 * Position phase segment
 * @param {Object} phase - Timeline phase
 * @param {Function} timeScale - D3 time scale
 * @param {number} height - Container height
 * @returns {{x: number, width: number, height: number}}
 */
export function positionPhase(phase, timeScale, height) {
  const startX = timeScale(new Date(phase.start))
  const endX = timeScale(new Date(phase.end))

  return {
    x: startX,
    y: 0,
    width: Math.max(endX - startX, 5), // Minimum width
    height: height
  }
}

/**
 * Create risk area path for timeline
 * @param {Array} dataPoints - [{date, score}]
 * @param {Function} timeScale - D3 time scale
 * @param {number} height - Container height
 * @returns {string} SVG path
 */
export function createRiskAreaPath(dataPoints, timeScale, height) {
  if (!dataPoints || dataPoints.length === 0) return ''

  const area = d3.area()
    .x(d => timeScale(new Date(d.date)))
    .y0(height)
    .y1(d => height - (d.score / 100) * height * 0.8)
    .curve(d3.curveMonotoneX)

  return area(dataPoints)
}

/**
 * Create risk line path
 * @param {Array} dataPoints - [{date, score}]
 * @param {Function} timeScale - D3 time scale
 * @param {number} height - Container height
 * @returns {string} SVG path
 */
export function createRiskLinePath(dataPoints, timeScale, height) {
  if (!dataPoints || dataPoints.length === 0) return ''

  const line = d3.line()
    .x(d => timeScale(new Date(d.date)))
    .y(d => height - (d.score / 100) * height * 0.8)
    .curve(d3.curveMonotoneX)

  return line(dataPoints)
}

/**
 * Get time ticks for axis
 * @param {Function} timeScale - D3 time scale
 * @param {number} count - Approximate number of ticks
 * @returns {Array<Date>}
 */
export function getTimeTicks(timeScale, count = 10) {
  return timeScale.ticks(count)
}

/**
 * Format date for timeline axis
 * @param {Date} date
 * @param {string} granularity - 'day' | 'week' | 'month'
 * @returns {string}
 */
export function formatTimelineDate(date, granularity = 'day') {
  const formatters = {
    day: d3.timeFormat('%b %d'),
    week: d3.timeFormat('%b %d'),
    month: d3.timeFormat('%B')
  }

  return formatters[granularity](date)
}

/**
 * Calculate zoom transform
 * @param {number} zoomLevel - 1 to 5
 * @returns {{k: number, x: number, y: number}}
 */
export function calculateZoomTransform(zoomLevel) {
  const k = Math.max(1, Math.min(5, zoomLevel))
  return { k, x: 0, y: 0 }
}

export default {
  createTimeScale,
  positionEvent,
  positionPhase,
  createRiskAreaPath,
  createRiskLinePath,
  getTimeTicks,
  formatTimelineDate,
  calculateZoomTransform
}






