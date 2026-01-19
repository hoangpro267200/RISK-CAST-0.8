/**
 * UI state type definitions
 */

/**
 * @typedef {Object} TreeUIState
 * @property {Set<string>} expandedNodes - Expanded node IDs
 * @property {string|null} hoveredNode - Currently hovered node
 * @property {string|null} selectedNode - Currently selected node
 */

/**
 * @typedef {Object} TimelineUIState
 * @property {number} zoomLevel - Zoom level (1-5)
 * @property {DateRange} visibleDateRange - Visible date range
 */

/**
 * @typedef {Object} DateRange
 * @property {Date} start
 * @property {Date} end
 */

/**
 * @typedef {Object} LayoutUIState
 * @property {boolean} sidebarCollapsed
 * @property {string} activeTab - Current active tab
 */

/**
 * @typedef {Object} AnimationSettings
 * @property {boolean} enableAnimations
 * @property {boolean} reducedMotion
 */

export {}






