import * as d3 from 'd3'

/**
 * Calculate tree layout using D3
 * @param {Object} treeData - Hierarchical tree data
 * @param {number} width - Container width
 * @param {number} height - Container height
 * @param {Object} options - Layout options
 * @returns {Object} Nodes and edges with positions
 */
export function calculateTreeLayout(treeData, width, height, options = {}) {
  const {
    nodeSize = 80,
    levelSeparation = 150,
    orientation = 'vertical' // 'vertical' | 'horizontal'
  } = options

  // Create tree layout
  const treeLayout = d3.tree()
    .size([width, height])
    .separation((a, b) => {
      return a.parent === b.parent ? 1 : 1.5
    })

  // Create hierarchy
  const root = d3.hierarchy(treeData)
  
  // Apply layout
  treeLayout(root)

  // Transform to our format
  const nodes = root.descendants().map(d => ({
    id: d.data.id,
    x: orientation === 'vertical' ? d.x : d.y,
    y: orientation === 'vertical' ? d.y : d.x,
    depth: d.depth,
    data: d.data,
    parent: d.parent?.data.id || null,
    children: d.children?.map(c => c.data.id) || []
  }))

  const edges = root.links().map(l => ({
    source: {
      id: l.source.data.id,
      x: orientation === 'vertical' ? l.source.x : l.source.y,
      y: orientation === 'vertical' ? l.source.y : l.source.x
    },
    target: {
      id: l.target.data.id,
      x: orientation === 'vertical' ? l.target.x : l.target.y,
      y: orientation === 'vertical' ? l.target.y : l.target.x
    },
    weight: l.target.data.weight || 1
  }))

  return { nodes, edges }
}

/**
 * Create curved Bézier path between two points
 * @param {Object} source - {x, y}
 * @param {Object} target - {x, y}
 * @param {string} orientation - 'vertical' | 'horizontal'
 * @returns {string} SVG path string
 */
export function createCurvedPath(source, target, orientation = 'vertical') {
  if (orientation === 'vertical') {
    const midY = (source.y + target.y) / 2
    return `M ${source.x},${source.y} C ${source.x},${midY} ${target.x},${midY} ${target.x},${target.y}`
  } else {
    const midX = (source.x + target.x) / 2
    return `M ${source.x},${source.y} C ${midX},${source.y} ${midX},${target.y} ${target.x},${target.y}`
  }
}

/**
 * Calculate node radius based on score
 * @param {number} score - Risk score (0-100)
 * @param {number} minRadius - Minimum radius
 * @param {number} maxRadius - Maximum radius
 * @returns {number}
 */
export function calculateNodeRadius(score, minRadius = 20, maxRadius = 40) {
  return minRadius + ((score / 100) * (maxRadius - minRadius))
}

/**
 * Get all ancestor IDs for a node
 * @param {string} nodeId - Target node ID
 * @param {Array} nodes - All nodes
 * @returns {Array<string>} Ancestor IDs
 */
export function getAncestors(nodeId, nodes) {
  const ancestors = []
  let current = nodes.find(n => n.id === nodeId)
  
  while (current && current.parent) {
    ancestors.push(current.parent)
    current = nodes.find(n => n.id === current.parent)
  }
  
  return ancestors
}

/**
 * Get all descendant IDs for a node
 * @param {string} nodeId - Target node ID
 * @param {Array} nodes - All nodes
 * @returns {Array<string>} Descendant IDs
 */
export function getDescendants(nodeId, nodes) {
  const descendants = []
  const node = nodes.find(n => n.id === nodeId)
  
  if (!node) return descendants
  
  function traverse(id) {
    const n = nodes.find(n => n.id === id)
    if (!n || !n.children) return
    
    n.children.forEach(childId => {
      descendants.push(childId)
      traverse(childId)
    })
  }
  
  traverse(nodeId)
  return descendants
}

/**
 * Filter tree to max depth
 * @param {Object} treeData - Tree data
 * @param {number} maxDepth - Maximum depth
 * @returns {Object} Filtered tree
 */
export function filterTreeByDepth(treeData, maxDepth) {
  function filter(node, currentDepth = 0) {
    if (currentDepth >= maxDepth) {
      return { ...node, children: [] }
    }
    
    return {
      ...node,
      children: (node.children || []).map(child => filter(child, currentDepth + 1))
    }
  }
  
  return filter(treeData)
}

export default {
  calculateTreeLayout,
  createCurvedPath,
  calculateNodeRadius,
  getAncestors,
  getDescendants,
  filterTreeByDepth
}






