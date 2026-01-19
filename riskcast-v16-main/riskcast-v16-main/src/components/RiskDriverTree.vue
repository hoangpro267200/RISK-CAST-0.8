<template>
  <div class="risk-driver-tree glass-card">
    <div class="card-header">
      <h2 class="text-xl font-bold text-white mb-2">Risk Driver Tree</h2>
      <p class="text-sm text-gray-400">Hierarchical risk factor analysis</p>
    </div>
    <div ref="treeContainer" class="tree-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import * as d3 from 'd3';
import { getNodeColor } from '../utils/treeLayout';

const props = defineProps({
  driverTree: { type: Object, required: true },
  layerScores: { type: Object, required: true }
});

const treeContainer = ref(null);

const renderTree = () => {
  if (!treeContainer.value) return;
  
  // Clear previous
  d3.select(treeContainer.value).selectAll('*').remove();
  
  const width = 800;
  const height = 600;
  
  const svg = d3.select(treeContainer.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .append('g')
    .attr('transform', 'translate(50, 50)');
  
  // Build hierarchy
  const root = {
    name: 'Overall Risk',
    children: []
  };
  
  Object.entries(props.driverTree).forEach(([key, catData]) => {
    const catNode = {
      name: catData.category_display_name || key,
      score: catData.score,
      children: catData.drivers.slice(0, 3).map(d => ({
        name: d.layer_display_name,
        score: d.score,
        layer: d.layer
      }))
    };
    root.children.push(catNode);
  });
  
  const treeLayout = d3.tree().size([height - 100, width - 200]);
  const hierarchy = d3.hierarchy(root);
  const treeData = treeLayout(hierarchy);
  
  // Links
  svg.selectAll('.link')
    .data(treeData.links())
    .enter()
    .append('path')
    .attr('class', 'link')
    .attr('d', d => `M${d.source.y},${d.source.x}C${(d.source.y + d.target.y) / 2},${d.source.x} ${(d.source.y + d.target.y) / 2},${d.target.x} ${d.target.y},${d.target.x}`)
    .style('fill', 'none')
    .style('stroke', '#4FC3F7')
    .style('stroke-opacity', 0.3)
    .style('stroke-width', 2);
  
  // Nodes
  const node = svg.selectAll('.node')
    .data(treeData.descendants())
    .enter()
    .append('g')
    .attr('class', 'node')
    .attr('transform', d => `translate(${d.y},${d.x})`);
  
  node.append('circle')
    .attr('r', d => d.depth === 0 ? 8 : 6)
    .style('fill', d => d.data.score ? getNodeColor(d.data.score) : '#4FC3F7')
    .style('stroke', '#fff')
    .style('stroke-width', 2)
    .style('filter', 'drop-shadow(0 0 8px rgba(79, 195, 247, 0.4))');
  
  node.append('text')
    .attr('dy', '.31em')
    .attr('x', d => d.children ? -12 : 12)
    .style('text-anchor', d => d.children ? 'end' : 'start')
    .style('fill', '#fff')
    .style('font-size', '11px')
    .text(d => d.data.name);
};

onMounted(() => {
  renderTree();
});

watch(() => props.driverTree, () => {
  renderTree();
});
</script>

<style scoped>
.risk-driver-tree {
  min-height: 500px;
  overflow: hidden;
}

.tree-container {
  width: 100%;
  min-height: 500px;
}

.glass-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
</style>






