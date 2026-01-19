/**
 * What-if simulation type definitions
 */

/**
 * @typedef {Object} Parameter
 * @property {string} id - Parameter ID
 * @property {string} name - Display name
 * @property {'slider'|'toggle'|'dropdown'} type - Control type
 * @property {number|boolean|string} value - Current value
 * @property {number} [min] - Min value (for slider)
 * @property {number} [max] - Max value (for slider)
 * @property {number} [step] - Step size (for slider)
 * @property {string} [unit] - Display unit
 * @property {number} sensitivity - Impact sensitivity
 * @property {string} category - Parameter category
 * @property {string} description - Help text
 */

/**
 * @typedef {Object} ParameterGroup
 * @property {string} name - Group name
 * @property {string} icon - Group icon
 * @property {Parameter[]} parameters - Parameters in group
 */

/**
 * @typedef {Object} SimulationResults
 * @property {number} overallScore - Adjusted overall score
 * @property {Object[]} layers - Adjusted layer scores
 * @property {number} delay - Adjusted delay prediction
 * @property {Object} esg - Adjusted ESG scores
 */

export {}






