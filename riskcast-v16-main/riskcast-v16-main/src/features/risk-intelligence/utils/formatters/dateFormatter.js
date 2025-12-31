/**
 * Date formatting utilities
 * For timeline and timestamp display
 */

/**
 * Format date for timeline axis
 * @param {Date|string} date
 * @param {string} granularity - 'day', 'month', 'year'
 * @returns {string}
 */
export function formatTimelineDate(date, granularity = 'day') {
  const d = new Date(date)
  
  switch (granularity) {
    case 'day':
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric'
      }).format(d)
    
    case 'month':
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        year: 'numeric'
      }).format(d)
    
    case 'year':
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric'
      }).format(d)
    
    default:
      return formatDate(d)
  }
}

/**
 * Format full date
 * @param {Date|string} date
 * @returns {string}
 */
export function formatDate(date) {
  const d = new Date(date)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(d)
}

/**
 * Format date and time
 * @param {Date|string} date
 * @returns {string}
 */
export function formatDateTime(date) {
  const d = new Date(date)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(d)
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param {Date|string} date
 * @returns {string}
 */
export function formatRelativeTime(date) {
  const d = new Date(date)
  const now = new Date()
  const diffMs = now - d
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  
  if (diffSec < 60) return 'just now'
  if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`
  if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`
  if (diffDay < 7) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`
  return formatDate(d)
}

/**
 * Get date range string
 * @param {Date|string} start
 * @param {Date|string} end
 * @returns {string}
 */
export function formatDateRange(start, end) {
  const startDate = new Date(start)
  const endDate = new Date(end)
  
  const startStr = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric'
  }).format(startDate)
  
  const endStr = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(endDate)
  
  return `${startStr} - ${endStr}`
}

/**
 * Calculate duration between dates
 * @param {Date|string} start
 * @param {Date|string} end
 * @returns {{days: number, hours: number, minutes: number}}
 */
export function calculateDuration(start, end) {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const diffMs = endDate - startDate
  
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
  
  return { days, hours, minutes }
}

/**
 * Format duration as human-readable string
 * @param {{days: number, hours: number, minutes: number}} duration
 * @returns {string}
 */
export function formatDuration(duration) {
  const parts = []
  
  if (duration.days > 0) {
    parts.push(`${duration.days} day${duration.days > 1 ? 's' : ''}`)
  }
  if (duration.hours > 0) {
    parts.push(`${duration.hours} hour${duration.hours > 1 ? 's' : ''}`)
  }
  if (duration.minutes > 0 && duration.days === 0) {
    parts.push(`${duration.minutes} minute${duration.minutes > 1 ? 's' : ''}`)
  }
  
  return parts.join(', ') || '0 minutes'
}

/**
 * Check if date is in the past
 * @param {Date|string} date
 * @returns {boolean}
 */
export function isPast(date) {
  return new Date(date) < new Date()
}

/**
 * Check if date is in the future
 * @param {Date|string} date
 * @returns {boolean}
 */
export function isFuture(date) {
  return new Date(date) > new Date()
}

/**
 * Get ISO string for date
 * @param {Date|string} date
 * @returns {string}
 */
export function toISOString(date) {
  return new Date(date).toISOString()
}






