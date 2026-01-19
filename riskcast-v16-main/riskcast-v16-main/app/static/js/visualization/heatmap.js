
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
     * Probability and Severity mappings
     */
    const PROBABILITY_MAP = {
        'low': 0,
        'medium': 1,
        'high': 2
    };

    const SEVERITY_MAP = {
        'low': 0,
        'medium': 1,
        'high': 2
    };

    const PROBABILITY_LABELS = ['Low', 'Medium', 'High'];
    const SEVERITY_LABELS = ['Low', 'Medium', 'High'];

    /**
     * Get risk level for cell based on quadrant
     */
    function getRiskLevelForQuadrant(quadrant) {
        // Quadrants: 1-9 (3x3 grid)
        // Row = severity, Col = probability
        // Lower left (1) = low risk, upper right (9) = critical risk
        
        if (quadrant <= 3) return 'low';      // Low severity
        if (quadrant <= 6) return 'medium';   // Medium severity
        return 'high';                        // High severity
    }

    /**
     * Calculate risk intensity for cell (0-1)
     */
    function calculateRiskIntensity(prob, sev) {
        // Combine probability and severity
        return (prob * 0.5 + sev * 0.5) / 2; // Normalize to 0-1
    }

    /**
     * Create heatmap visualization
     */
    function createHeatmap(containerId, matrixData) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Heatmap container not found: ${containerId}`);
            return null;
        }

        // Clear container
        container.innerHTML = '';

        // Create heatmap grid
        const heatmap = document.createElement('div');
        heatmap.className = 'riskcast-heatmap';

        // Add header row (probability labels)
        heatmap.appendChild(createLabel('', 'heatmap-label')); // Empty top-left
        PROBABILITY_LABELS.forEach(label => {
            const labelEl = createLabel(label, 'heatmap-label');
            heatmap.appendChild(labelEl);
        });

        // Create cells (rows = severity, cols = probability)
        SEVERITY_LABELS.forEach((severityLabel, sevIdx) => {
            // Add severity label column
            const sevLabel = createLabel(severityLabel, 'heatmap-label');
            heatmap.appendChild(sevLabel);

            // Add cells for this severity row
            PROBABILITY_LABELS.forEach((probLabel, probIdx) => {
                const quadrant = sevIdx * 3 + probIdx + 1;
                const riskLevel = getRiskLevelForQuadrant(quadrant);
                const riskIntensity = calculateRiskIntensity(probIdx, sevIdx);
                
                const cell = createHeatmapCell(quadrant, riskLevel, riskIntensity, {
                    probability: probLabel.toLowerCase(),
                    severity: severityLabel.toLowerCase()
                });
                
                heatmap.appendChild(cell);
            });
        });

        container.appendChild(heatmap);

        // Highlight active cell based on matrix data
        if (matrixData) {
            highlightActiveCell(heatmap, matrixData);
        }

        return heatmap;
    }

    /**
     * Create label element
     */
    function createLabel(text, className) {
        const label = document.createElement('div');
        label.className = className;
        label.textContent = text;
        return label;
    }

    /**
     * Create heatmap cell
     */
    function createHeatmapCell(quadrant, riskLevel, riskIntensity, labels) {
        const cell = document.createElement('div');
        cell.className = `heatmap-cell risk-${riskLevel}`;
        cell.dataset.quadrant = quadrant;
        cell.dataset.probability = labels.probability;
        cell.dataset.severity = labels.severity;

        // Add quadrant number
        const quadrantLabel = document.createElement('span');
        quadrantLabel.className = 'heatmap-quadrant-label';
        quadrantLabel.textContent = `Q${quadrant}`;
        cell.appendChild(quadrantLabel);

        // Add tooltip
        cell.title = `Quadrant ${quadrant}: ${labels.probability.charAt(0).toUpperCase() + labels.probability.slice(1)} Probability, ${labels.severity.charAt(0).toUpperCase() + labels.severity.slice(1)} Severity`;

        // Add hover effect
        cell.addEventListener('mouseenter', function() {
            showCellTooltip(cell, labels, quadrant, riskLevel);
        });

        cell.addEventListener('mouseleave', function() {
            hideCellTooltip();
        });

        return cell;
    }

    /**
     * Highlight active cell based on matrix data
     */
    function highlightActiveCell(heatmap, matrixData) {
        const probability = matrixData.probability?.toLowerCase();
        const severity = matrixData.severity?.toLowerCase();
        const quadrant = matrixData.quadrant;

        if (!probability || !severity) {
            return;
        }

        const probIdx = PROBABILITY_MAP[probability] ?? 1;
        const sevIdx = SEVERITY_MAP[severity] ?? 1;

        // Find the active cell
        const activeQuadrant = quadrant || (sevIdx * 3 + probIdx + 1);
        const activeCell = heatmap.querySelector(`[data-quadrant="${activeQuadrant}"]`);

        if (activeCell) {
            activeCell.classList.add('active');
            
            // Scroll into view if needed
            setTimeout(() => {
                activeCell.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
            }, 100);
        }
    }

    /**
     * Show cell tooltip
     */
    function showCellTooltip(cell, labels, quadrant, riskLevel) {
        // Tooltip is already in title attribute, but we could enhance it
        // with a custom tooltip element if needed
    }

    /**
     * Hide cell tooltip
     */
    function hideCellTooltip() {
        // Remove custom tooltip if created
    }

    /**
     * Update heatmap with new data
     */
    function updateHeatmap(heatmap, matrixData) {
        if (!heatmap) return;

        // Remove previous active class
        const prevActive = heatmap.querySelector('.heatmap-cell.active');
        if (prevActive) {
            prevActive.classList.remove('active');
        }

        // Highlight new active cell
        highlightActiveCell(heatmap, matrixData);
    }

    // Export API
    window.RISKCAST.visualization.heatmap = {
        create: createHeatmap,
        update: updateHeatmap,
    };

    console.log('✅ RISKCAST Heatmap visualization initialized');

})();





















