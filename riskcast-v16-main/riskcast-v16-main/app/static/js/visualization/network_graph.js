
(function() {
    'use strict';

    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.visualization === 'undefined') {
        window.RISKCAST.visualization = {};
    }

    const utils = window.RISKCAST.visualization.utils || {};

    /**
     * Create network graph using canvas (simplified implementation)
     */
    function createNetworkGraph(containerId, networkData) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Network graph container not found: ${containerId}`);
            return null;
        }

        // Clear container
        container.innerHTML = '';

        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.style.width = '100%';
        canvas.style.height = '500px';
        container.appendChild(canvas);

        // Resize canvas to container
        function resizeCanvas() {
            const rect = container.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = 500;
        }

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        const ctx = canvas.getContext('2d');
        let animationFrameId = null;
        let hoveredNode = null;
        let selectedNode = null;

        // Prepare nodes and edges
        const nodes = networkData.nodes || [];
        const edges = networkData.edges || [];

        // Calculate positions (force-directed layout simplified)
        const nodePositions = calculateNodePositions(nodes, edges, canvas.width, canvas.height);

        /**
         * Get color for risk level
         */
        function getRiskColor(risk) {
            if (risk < 0.33) return '#00FFC8'; // Green
            if (risk < 0.67) return '#FFD700'; // Yellow
            return '#FF3366'; // Red
        }

        /**
         * Calculate node positions (simplified circular/force-directed)
         */
        function calculateNodePositions(nodes, edges, width, height) {
            const positions = {};
            const centerX = width / 2;
            const centerY = height / 2;
            const radius = Math.min(width, height) * 0.3;

            // Simple circular layout
            nodes.forEach((node, index) => {
                const angle = (index / nodes.length) * Math.PI * 2;
                positions[node.id] = {
                    x: centerX + Math.cos(angle) * radius,
                    y: centerY + Math.sin(angle) * radius,
                    risk: node.risk || 0.5
                };
            });

            return positions;
        }

        /**
         * Draw network graph
         */
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw edges first (so nodes appear on top)
            edges.forEach(edge => {
                // Support both 'source/target' and 'from/to' formats
                const sourceId = edge.source || edge.from;
                const targetId = edge.target || edge.to;
                const sourcePos = nodePositions[sourceId];
                const targetPos = nodePositions[targetId];

                if (!sourcePos || !targetPos) return;

                // Edge width based on volume
                const edgeWidth = 1 + (edge.volume || 1) * 2;
                
                // Edge color based on propagation risk
                const propRisk = edge.propagation || 0;
                const alpha = 0.3 + propRisk * 0.4;
                const edgeColor = `rgba(0, 255, 200, ${alpha})`;

                ctx.beginPath();
                ctx.moveTo(sourcePos.x, sourcePos.y);
                ctx.lineTo(targetPos.x, targetPos.y);
                ctx.strokeStyle = edgeColor;
                ctx.lineWidth = edgeWidth;
                ctx.stroke();

                // Glow effect for high propagation
                if (propRisk > 0.5) {
                    ctx.shadowBlur = 15;
                    ctx.shadowColor = '#00FFC8';
                    ctx.stroke();
                    ctx.shadowBlur = 0;
                }
            });

            // Draw nodes
            nodes.forEach(node => {
                const pos = nodePositions[node.id];
                if (!pos) return;

                const risk = node.risk || 0.5;
                const color = getRiskColor(risk);
                const isHovered = hoveredNode === node.id;
                const isSelected = selectedNode === node.id;

                // Node size based on risk
                const nodeSize = 15 + risk * 20;

                // Outer glow
                if (isHovered || isSelected) {
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, nodeSize + 5, 0, Math.PI * 2);
                    ctx.fillStyle = color;
                    ctx.shadowBlur = 20;
                    ctx.shadowColor = color;
                    ctx.globalAlpha = 0.3;
                    ctx.fill();
                    ctx.globalAlpha = 1.0;
                    ctx.shadowBlur = 0;
                }

                // Node circle
                ctx.beginPath();
                ctx.arc(pos.x, pos.y, nodeSize, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();

                // Node label
                ctx.fillStyle = '#ffffff';
                ctx.font = '12px Inter, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(node.id, pos.x, pos.y - nodeSize - 15);

                // Risk percentage
                ctx.fillStyle = '#8FFFD0';
                ctx.font = '10px Inter, sans-serif';
                ctx.fillText((risk * 100).toFixed(0) + '%', pos.x, pos.y + nodeSize + 12);
            });
        }

        /**
         * Handle mouse events
         */
        function handleMouseMove(event) {
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            // Check if mouse is over a node
            let foundNode = null;
            nodes.forEach(node => {
                const pos = nodePositions[node.id];
                if (!pos) return;

                const nodeSize = 15 + (node.risk || 0.5) * 20;
                const dx = x - pos.x;
                const dy = y - pos.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance <= nodeSize) {
                    foundNode = node.id;
                }
            });

            if (foundNode !== hoveredNode) {
                hoveredNode = foundNode;
                canvas.style.cursor = foundNode ? 'pointer' : 'default';
                draw();
            }
        }

        function handleClick(event) {
            if (hoveredNode) {
                selectedNode = selectedNode === hoveredNode ? null : hoveredNode;
                draw();
                showNodeTooltip(selectedNode);
            }
        }

        /**
         * Show node tooltip
         */
        function showNodeTooltip(nodeId) {
            const node = nodes.find(n => n.id === nodeId);
            if (!node) return;

            // Create or update tooltip
            let tooltip = document.getElementById('network-tooltip');
            if (!tooltip) {
                tooltip = document.createElement('div');
                tooltip.id = 'network-tooltip';
                tooltip.className = 'network-tooltip';
                document.body.appendChild(tooltip);
            }

            tooltip.innerHTML = `
                <div><strong>${nodeId}</strong></div>
                <div>Risk: ${(node.risk * 100).toFixed(1)}%</div>
            `;
            tooltip.style.display = 'block';
        }

        // Add event listeners
        canvas.addEventListener('mousemove', handleMouseMove);
        canvas.addEventListener('click', handleClick);

        // Initial draw
        draw();

        // Animation loop (for glow effects)
        function animate() {
            draw();
            animationFrameId = requestAnimationFrame(animate);
        }
        animate();

        // Cleanup function
        canvas.cleanup = function() {
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
            }
            window.removeEventListener('resize', resizeCanvas);
            canvas.removeEventListener('mousemove', handleMouseMove);
            canvas.removeEventListener('click', handleClick);
        };

        return canvas;
    }

    /**
     * Update network graph
     */
    function updateNetworkGraph(canvas, networkData) {
        if (!canvas) return;
        // Would need to reinitialize with new data
        // For simplicity, just return - caller should recreate
        return createNetworkGraph(canvas.parentElement.id, networkData);
    }

    // Export API
    window.RISKCAST.visualization.networkGraph = {
        create: createNetworkGraph,
        update: updateNetworkGraph,
    };

    console.log('✅ RISKCAST Network graph initialized');

})();





















