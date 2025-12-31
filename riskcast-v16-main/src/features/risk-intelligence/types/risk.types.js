/**
 * Risk data type definitions
 * Using JSDoc for type hints in plain JavaScript
 */

/**
 * @typedef {Object} RiskBaseline
 * @property {number} overallScore - Overall risk score (0-100)
 * @property {'low'|'medium'|'high'|'critical'} riskLevel
 * @property {Date} timestamp - When calculated
 */

/**
 * @typedef {Object} RiskLayer
 * @property {string} id - Layer identifier
 * @property {string} name - Display name
 * @property {number} score - Layer risk score (0-100)
 * @property {string} description - Layer description
 * @property {RiskFactor[]} factors - Contributing factors
 * @property {number} weight - Weight in overall calculation
 */

/**
 * @typedef {Object} RiskFactor
 * @property {string} factor - Factor name
 * @property {number} contribution - Contribution percentage (0-1)
 */

/**
 * @typedef {Object} RiskCategory
 * @property {string} id - Category ID
 * @property {string} name - Category name
 * @property {number} score - Category score
 * @property {number} weight - Weight percentage
 */

/**
 * @typedef {Object} ESGScore
 * @property {number} environmental - E score (0-100)
 * @property {number} social - S score (0-100)
 * @property {number} governance - G score (0-100)
 */

/**
 * @typedef {Object} MonteCarloDistribution
 * @property {number} p50 - Median (50th percentile)
 * @property {number} p95 - 95th percentile
 * @property {DistributionPoint[]} distribution - Full distribution
 */

/**
 * @typedef {Object} DistributionPoint
 * @property {number} value - Risk score value
 * @property {number} probability - Probability (0-1)
 */

/**
 * @typedef {Object} DelayPrediction
 * @property {number} expected - Expected delay in days
 * @property {number} min - Minimum delay
 * @property {number} max - Maximum delay
 * @property {string} unit - Unit ('days')
 * @property {number} confidence - Confidence level (0-1)
 */

/**
 * @typedef {Object} ShockScenario
 * @property {string} id - Scenario ID
 * @property {string} name - Scenario name
 * @property {number} impact - Impact score (0-100)
 * @property {number} probability - Probability (0-1)
 * @property {string} description - Description
 */

/**
 * @typedef {Object} TreeNode
 * @property {string} id - Node ID
 * @property {string} name - Node name
 * @property {number} score - Node risk score
 * @property {number} weight - Weight in parent
 * @property {TreeNode[]} children - Child nodes
 * @property {Object} data - Additional node data
 */

/**
 * @typedef {Object} TimelinePhase
 * @property {string} id - Phase ID
 * @property {string} name - Phase name
 * @property {string} start - Start date (ISO string)
 * @property {string} end - End date (ISO string)
 * @property {'low'|'medium'|'high'|'critical'} riskLevel
 */

/**
 * @typedef {Object} TimelineEvent
 * @property {string} id - Event ID
 * @property {string} date - Event date (ISO string)
 * @property {string} type - Event type
 * @property {'low'|'medium'|'high'|'critical'} severity
 * @property {string} description - Event description
 */

/**
 * @typedef {Object} RiskTimeline
 * @property {TimelinePhase[]} phases
 * @property {TimelineEvent[]} events
 */

/**
 * @typedef {Object} RiskData
 * @property {RiskBaseline} baseline
 * @property {RiskLayer[]} layers
 * @property {RiskCategory[]} categories
 * @property {ESGScore} esg
 * @property {MonteCarloDistribution} monteCarlo
 * @property {DelayPrediction} delayPrediction
 * @property {ShockScenario[]} shockScenarios
 * @property {TreeNode} driverTree
 * @property {RiskTimeline} timeline
 */

export {}






