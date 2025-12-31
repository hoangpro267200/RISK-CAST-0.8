/**
 * RiskCast V22 - D3 Tree Layout Utility
 * ======================================
 * D3.js tree layout builder for Risk Driver Tree visualization
 */

import * as d3 from 'd3';

export const buildTreeLayout = (driverTreeData, containerWidth = 800, containerHeight = 600) => {
  // Create hierarchical structure from driver tree
  const root = {
    name: 'Overall Risk',
    children: []
  };
  
  // Convert driver tree to D3 hierarchy
  Object.entries(driverTreeData).forEach(([categoryKey, categoryData]) => {
    const categoryNode = {
      name: categoryData.category_display_name || categoryKey,
      score: categoryData.score,
      severity: categoryData.severity,
      children: []
    };
    
    categoryData.drivers.forEach(driver => {
      categoryNode.children.push({
        name: driver.layer_display_name || driver.layer,
        layer: driver.layer,
        score: driver.score,
        severity: driver.severity,
        weight: driver.weight,
        contribution: driver.contribution,
        description: driver.description,
        root_causes: driver.root_causes
      });
    });
    
    root.children.push(categoryNode);
  });
  
  // Create D3 tree layout
  const treeLayout = d3.tree()
    .size([containerHeight - 100, containerWidth - 200])
    .separation((a, b) => (a.parent === b.parent ? 1 : 1.2));
  
  // Create hierarchy
  const hierarchy = d3.hierarchy(root);
  const treeData = treeLayout(hierarchy);
  
  return {
    nodes: treeData.descendants(),
    links: treeData.links(),
    hierarchy: hierarchy
  };
};

export const getNodeColor = (score) => {
  if (score < 40) return '#10B981'; // Green
  if (score < 60) return '#F59E0B'; // Yellow/Amber
  if (score < 75) return '#F97316'; // Orange
  return '#EF4444'; // Red
};

export const createCollapsibleTree = (svg, nodes, links) => {
  // Add links
  const link = svg.selectAll('.link')
    .data(links)
    .enter()
    .append('path')
    .attr('class', 'link')
    .attr('d', d => {
      return `M${d.source.y},${d.source.x}
              C${(d.source.y + d.target.y) / 2},${d.source.x}
               ${(d.source.y + d.target.y) / 2},${d.target.x}
               ${d.target.y},${d.target.x}`;
    })
    .style('fill', 'none')
    .style('stroke', '#4FC3F7')
    .style('stroke-opacity', 0.3)
    .style('stroke-width', 2);
  
  // Add nodes
  const node = svg.selectAll('.node')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'node')
    .attr('transform', d => `translate(${d.y},${d.x})`);
  
  // Add circles
  node.append('circle')
    .attr('r', d => d.depth === 0 ? 8 : 6)
    .style('fill', d => d.data.score ? getNodeColor(d.data.score) : '#4FC3F7')
    .style('stroke', '#fff')
    .style('stroke-width', 2)
    .style('filter', 'drop-shadow(0 0 10px rgba(79, 195, 247, 0.4))');
  
  // Add labels
  node.append('text')
    .attr('dy', '.31em')
    .attr('x', d => d.children || d._children ? -12 : 12)
    .style('text-anchor', d => d.children || d._children ? 'end' : 'start')
    .style('fill', '#fff')
    .style('font-size', '12px')
    .text(d => d.data.name);
  
  return { nodes: node, links: link };
};






