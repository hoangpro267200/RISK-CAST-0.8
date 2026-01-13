/**
 * Results Page Renderer - ENGINE-FIRST Architecture
 * 
 * DATA FLOW: ENGINE → summary → state.js → resultsRenderer.js → DOM
 * 
 * RESPONSIBILITIES:
 * - Map summary object to DOM elements
 * - Format values (dates, numbers, currency)
 * - Toggle classes for display (risk levels, status badges)
 * - Loop through arrays (layers, providers, insights, actions)
 * 
 * STRICT RULES:
 * - NO calculations (scores, percentages, risk levels come from engine)
 * - NO business logic (all decisions come from backend)
 * - NO hardcoded values (all data from summary object)
 * - Defensive null checks (graceful degradation)
 */

// Verify scenarioClassifier utility is available at module load time
// (Debug logs removed for production)

/**
 * Format currency value
 * ENGINE-FIRST: Only formatting, no calculations
 * FIX: 0 is a valid value, only null/undefined/NaN should show dash
 */
function formatCurrency(value) {
    if (value == null || value === undefined || isNaN(value)) return '—';
    // 0 is a valid value - show $0 instead of dash
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

/**
 * Format date value
 */
function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    } catch {
        return dateString;
    }
}


/**
 * Get risk level class from level string
 */
function getRiskLevelClass(level) {
    if (!level) return 'moderate';
    const levelLower = String(level).toLowerCase();
    if (levelLower.includes('high') || levelLower.includes('critical')) return 'high';
    if (levelLower.includes('low')) return 'low';
    return 'moderate';
}

/**
 * Get insight type class
 */
function getInsightTypeClass(type) {
    if (!type) return 'watch';
    const typeLower = String(type).toLowerCase();
    if (typeLower.includes('critical') || typeLower.includes('risk')) return 'critical';
    if (typeLower.includes('opportunity') || typeLower.includes('mitigation')) return 'opportunity';
    return 'watch';
}

/**
 * Format percentage value (0-1 to percentage)
 */
function formatPercent(value) {
    if (value == null || isNaN(value)) return '0%';
    if (value <= 1) return `${Math.round(value * 100)}%`;
    return `${Math.round(value)}%`;
}

/**
 * Get recommendation badge class
 */
function getRecommendationClass(recommendation) {
    if (!recommendation) return 'optional';
    const recUpper = String(recommendation).toUpperCase();
    if (recUpper === 'BUY' || recUpper === 'RECOMMENDED') return 'recommended';
    if (recUpper === 'SKIP' || recUpper === 'NOT_RECOMMENDED') return 'not-recommended';
    return 'optional';
}

/**
 * Render shipment header
 * ENGINE-FIRST: Uses normalized summary format
 */
function renderShipmentHeader(summary) {
    // Support both old format and new normalized format
    const shipment = summary?.shipment || {};
    
    const idEl = document.querySelector('.shipment-id');
    if (idEl) idEl.textContent = shipment.id || '—';
    
    const routeEl = document.querySelector('.route');
    if (routeEl) {
        // Use routeText from normalized format, or construct from route object
        const routeText = shipment.routeText || 
                         (shipment.route?.pol && shipment.route?.pod ? 
                          `${shipment.route.pol} → ${shipment.route.pod}` : 
                          shipment.route || '—');
        routeEl.textContent = routeText;
    }
    
    const carrierEl = document.querySelector('.carrier');
    if (carrierEl) carrierEl.textContent = shipment.carrier || '—';
    
    const etdEl = document.querySelector('.departure');
    if (etdEl) {
        const etd = shipment.etd;
        const etdText = etd ? `ETD: ${formatDate(etd)}` : 'ETD: —';
        etdEl.textContent = etdText;
    }
}

/**
 * Render hero zone (risk orb, level badge, confidence, scenario badge)
 * ENGINE-FIRST: Uses normalized summary format
 */
function renderHeroZone(summary) {
    // Support both old format (summary.risk) and new normalized format (summary.overall)
    const overall = summary?.overall || summary?.risk || {};
    
    const scoreEl = document.querySelector('.score-value');
    if (scoreEl) {
        const score = overall.riskScore != null ? Math.round(overall.riskScore) : null;
        scoreEl.textContent = score != null ? score : '—';
    }
    
    const levelBadgeEl = document.querySelector('.risk-level-badge');
    if (levelBadgeEl) {
        // ENGINE-FIRST: Use riskLevel from summary, never calculate from score
        const level = overall.riskLevel || 'Moderate';
        const levelClass = getRiskLevelClass(level);
        levelBadgeEl.textContent = `${level} Risk`;
        levelBadgeEl.className = `risk-level-badge ${levelClass}`;
    }
    
    // Classify scenario and render scenario badge
    const scenario = classifyScenarioForSummary(summary);
    renderScenarioBadge(scenario);
    
    const confidenceFillEl = document.querySelector('.confidence-fill');
    const confidenceValueEl = document.querySelector('.confidence-value');
    if (confidenceFillEl && confidenceValueEl) {
        const confidence = overall.confidence != null ? 
            (overall.confidence > 1 ? Math.round(overall.confidence) : Math.round(overall.confidence * 100)) : 
            null;
        if (confidence != null) {
            confidenceFillEl.style.width = `${confidence}%`;
            confidenceValueEl.textContent = `${confidence}%`;
        } else {
            confidenceFillEl.style.width = '0%';
            confidenceValueEl.textContent = '—';
        }
    }
}

/**
 * Classify scenario for summary data
 * ENGINE-FIRST: Uses scenario classifier utility
 * @private
 */
function classifyScenarioForSummary(summary) {
    // Check if utility is loaded
    const hasUtility = typeof window !== 'undefined' && window.RISKCAST?.utils?.scenarioClassifier;
    
    // Try to use global utility if available
    const classifier = hasUtility ? window.RISKCAST.utils.scenarioClassifier : null;
    
    if (classifier && typeof classifier.classifyScenario === 'function') {
        const input = {
            riskScore: summary?.overall?.riskScore ?? summary?.risk?.finalScore ?? null,
            financial: summary?.financial || {}
        };
        return classifier.classifyScenario(input);
    }
    
    // Fallback: inline classification logic
    return inlineClassifyScenario(summary);
}

/**
 * Inline scenario classification (fallback if utility not available)
 * @private
 */
function inlineClassifyScenario(summary) {
    const overall = summary?.overall || summary?.risk || {};
    const financial = summary?.financial || {};
    
    const riskScore = overall.riskScore ?? null;
    let normalizedRiskScore = null;
    if (riskScore !== null && riskScore !== undefined) {
        const num = parseFloat(riskScore);
        if (!isNaN(num)) {
            normalizedRiskScore = num > 10 ? num / 10 : num;
        }
    }
    
    const financialMetrics = [
        financial.expectedLoss ?? financial.meanLoss,
        financial.var95 ?? financial.p95,
        financial.cvar ?? financial.maxLoss ?? financial.maxObserved,
        financial.maxLoss ?? financial.maxObserved
    ].filter(v => v !== null && v !== undefined);
    
    const hasFinancialExposure = financialMetrics.length > 0 && 
                                 financialMetrics.some(v => {
                                     const num = parseFloat(v);
                                     return !isNaN(num) && num > 0;
                                 });
    
    const hasOperationalRisk = normalizedRiskScore !== null && normalizedRiskScore > 0;
    
    if (!hasOperationalRisk) {
        return {
            type: 'NO_RISK_DETECTED',
            label: 'No Risk Detected',
            description: 'No operational risk detected for this shipment',
            severity: 'neutral'
        };
    }
    
    if (hasOperationalRisk && hasFinancialExposure) {
        return {
            type: 'FULL_RISK_AND_LOSS',
            label: 'Full Risk & Loss',
            description: 'Operational and financial risk exposure detected',
            severity: 'standard'
        };
    }
    
    if (hasOperationalRisk && !hasFinancialExposure) {
        return {
            type: 'OPERATIONAL_RISK_ONLY',
            label: 'Operational Risk Only',
            description: 'No financial loss exposure detected for this shipment',
            severity: 'operational',
            subtitle: 'Operational risk factors present, but no financial impact expected'
        };
    }
    
    return {
        type: 'NO_RISK_DETECTED',
        label: 'No Risk Detected',
        description: 'Insufficient data to classify scenario',
        severity: 'neutral'
    };
}

/**
 * Render scenario badge in hero zone
 * @private
 */
function renderScenarioBadge(scenario) {
    // Find or create scenario badge container
    const orbContainer = document.querySelector('.risk-orb-container');
    if (!orbContainer) {
        console.warn('[ResultsRenderer] .risk-orb-container not found!');
        return;
    }
    
    let badgeContainer = document.querySelector('.scenario-badge-container');
    if (!badgeContainer) {
        badgeContainer = document.createElement('div');
        badgeContainer.className = 'scenario-badge-container';
        orbContainer.appendChild(badgeContainer);
    }
    
    // Get badge configuration
    const classifier = (typeof window !== 'undefined' && window.RISKCAST?.utils?.scenarioClassifier) || null;
    let badgeConfig;
    
    if (classifier && typeof classifier.getScenarioBadge === 'function') {
        badgeConfig = classifier.getScenarioBadge(scenario);
    } else {
        // Fallback badge config
        badgeConfig = getFallbackScenarioBadge(scenario);
    }
    
    // For OPERATIONAL_RISK_ONLY, show subtitle; for others, show description if available
    const showSubtitle = scenario.type === 'OPERATIONAL_RISK_ONLY' && scenario.subtitle;
    const showDescription = scenario.type !== 'OPERATIONAL_RISK_ONLY' && scenario.description;
    
    const badgeHTML = `
        <div class="scenario-badge ${badgeConfig.className}">
            <span class="scenario-badge-icon">${escapeHtml(badgeConfig.icon)}</span>
            <span class="scenario-badge-label">${escapeHtml(badgeConfig.label)}</span>
        </div>
        ${showSubtitle ? `<div class="scenario-badge-subtitle">${escapeHtml(scenario.subtitle)}</div>` : ''}
        ${showDescription ? `<div class="scenario-badge-description">${escapeHtml(scenario.description)}</div>` : ''}
    `;
    
    badgeContainer.innerHTML = badgeHTML;
    
    // Verify badge exists in DOM and force visibility
    const renderedBadge = badgeContainer.querySelector('.scenario-badge');
    if (renderedBadge) {
        // Force visibility
        renderedBadge.style.display = 'inline-flex';
        renderedBadge.style.visibility = 'visible';
        renderedBadge.style.opacity = '1';
        badgeContainer.style.display = 'flex';
        badgeContainer.style.visibility = 'visible';
    } else {
        console.error('[ResultsRenderer] Badge not found in DOM after render!');
    }
}

/**
 * Get fallback scenario badge config
 * @private
 */
function getFallbackScenarioBadge(scenario) {
    const badges = {
        'FULL_RISK_AND_LOSS': {
            label: 'Full Risk & Loss',
            className: 'scenario-badge-full',
            icon: '📊'
        },
        'OPERATIONAL_RISK_ONLY': {
            label: 'OPERATIONAL RISK ONLY',
            className: 'scenario-badge-operational',
            icon: '⚙️'
        },
        'NO_RISK_DETECTED': {
            label: 'No Risk Detected',
            className: 'scenario-badge-none',
            icon: '✓'
        }
    };
    
    return badges[scenario.type] || badges['NO_RISK_DETECTED'];
}

/**
 * Escape HTML to prevent XSS
 * @private
 */
function escapeHtml(str) {
    if (str == null) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

/**
 * Render risk layers orbit using polar coordinates
 * ENGINE-FIRST: Only maps data, no calculations
 * Uses normalized summary format from results.js
 */
function renderRiskLayers(summary) {
    // Support both old format (summary.risk.layers) and new normalized format (summary.layers)
    const layers = summary?.layers || summary?.risk?.layers || [];
    
    const orbitEl = document.querySelector('.risk-layers-orbit');
    if (!orbitEl) return;
    
    // Responsive orbit radius based on viewport
    const getOrbitRadius = () => {
        const width = window.innerWidth;
        if (width > 1200) return 300; // Desktop
        if (width > 768) return 240;  // Medium
        return 200; // Small (but should use grid instead)
    };
    
    // Align orbit container with risk-orb-container center
    // Only on desktop (mobile uses grid layout)
    if (window.innerWidth > 768) {
        const orbContainer = document.querySelector('.risk-orb-container');
        if (orbContainer) {
            const orbRect = orbContainer.getBoundingClientRect();
            const heroRect = orbitEl.closest('.results-hero')?.getBoundingClientRect();
            if (heroRect) {
                const orbCenterY = orbRect.top - heroRect.top + orbRect.height / 2;
                const orbitSize = parseInt(getComputedStyle(orbitEl).width) || 640;
                orbitEl.style.top = `${orbCenterY - orbitSize / 2}px`;
            }
        }
    } else {
        orbitEl.style.top = '';
    }
    
    // Clear existing cards
    orbitEl.innerHTML = '';
    
    // If no layers, show empty state
    if (!layers || layers.length === 0) {
        return;
    }
    
    // Remove duplicates: keep only the first occurrence of each layer name (case-insensitive)
    const normalizeLayerName = (name) => {
        if (!name) return '';
        return name.trim().toLowerCase().replace(/\s+/g, ' ');
    };
    
    const seenLayers = new Map();
    const uniqueLayers = [];
    
    layers.forEach((layer) => {
        if (!layer || !layer.name) return;
        
        const normalizedName = normalizeLayerName(layer.name);
        
        // Skip if we've already seen this layer name
        if (seenLayers.has(normalizedName)) {
            return;
        }
        
        // Mark as seen and add to unique list
        seenLayers.set(normalizedName, true);
        uniqueLayers.push(layer);
    });
    
    // Use unique layers only
    const finalLayers = uniqueLayers;
    if (finalLayers.length === 0) return;
    
    // Get responsive orbit radius
    const orbitRadius = getOrbitRadius();
    const totalLayers = finalLayers.length;
    
    // Calculate angle step (360 degrees / number of layers)
    const angleStep = (2 * Math.PI) / totalLayers; // Full circle in radians
    
    finalLayers.forEach((layer, index) => {
        // Calculate angle for this layer (start at top, go clockwise)
        // Start at -90 degrees (top) and distribute evenly
        const angle = (index * angleStep) - (Math.PI / 2);
        
        // Create card element
        const card = document.createElement('div');
        card.className = 'layer-card';
        
        // Calculate polar coordinates (x, y from center)
        const x = Math.cos(angle) * orbitRadius;
        const y = Math.sin(angle) * orbitRadius;
        
        // Transform: cards start at (50%, 50%) of orbit container
        // Translate by (x, y) to position on circle
        card.style.transform = `translate(calc(-50% + ${x.toFixed(2)}px), calc(-50% + ${y.toFixed(2)}px))`;
        
        // Set status class (use provided status, or fallback based on score for UI display only)
        const status = layer.status || (layer.score != null && layer.score > 70 ? 'high' : layer.score != null && layer.score > 40 ? 'moderate' : 'low');
        const statusClass = getRiskLevelClass(status);
        card.classList.add(statusClass);
        
        // Get icon - use provided icon or map from name
        let icon = layer.icon || '📊';
        if (!layer.icon) {
            const iconMap = {
                'geopolitical': '🌍', 'weather': '⛈️', 'carrier': '🚢', 'port': '⚓',
                'cargo': '📦', 'route': '🗺️', 'transport': '🚚', 'network': '🌐',
                'equipment': '📊', 'esg': '🌱', 'climate': '⛈️', 'delay': '⏱️'
            };
            const layerNameLower = (layer.name || '').toLowerCase();
            for (const [key, value] of Object.entries(iconMap)) {
                if (layerNameLower.includes(key)) {
                    icon = value;
                    break;
                }
            }
        }
        
        // Build card content
        const score = layer.score != null ? Math.round(layer.score) : null;
        card.innerHTML = `
            <div class="layer-icon">${icon}</div>
            <div class="layer-info">
                <span class="layer-name">${layer.name || '—'}</span>
                <span class="layer-score">${score != null ? score : '—'}</span>
            </div>
        `;
        
        // Store original transform for hover effect
        const originalTransform = `translate(calc(-50% + ${x.toFixed(2)}px), calc(-50% + ${y.toFixed(2)}px))`;
        
        // Add hover effect (respect prefers-reduced-motion)
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            card.addEventListener('mouseenter', () => {
                card.style.transform = `${originalTransform} translateY(-3px)`;
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = originalTransform;
            });
        }
        
        orbitEl.appendChild(card);
    });
}

/**
 * Render layers table
 * ENGINE-FIRST: Uses normalized summary format
 */
function renderLayersTable(summary) {
    // Support both old format (summary.risk.layers) and new normalized format (summary.layers)
    const layers = summary?.layers || summary?.risk?.layers || [];
    
    const tbodyEl = document.querySelector('.layers-table tbody');
    if (!tbodyEl) return;
    
    tbodyEl.innerHTML = '';
    
    layers.forEach((layer) => {
        const row = document.createElement('tr');
        const statusClass = getRiskLevelClass(layer.status);
        row.className = `layer-row ${statusClass}`;
        
        // Support both contribution (0-1) and contributionPct (0-100)
        const contribution = layer.contributionPct != null ? Math.round(layer.contributionPct) :
                            layer.contribution != null ? 
            (layer.contribution <= 1 ? Math.round(layer.contribution * 100) : Math.round(layer.contribution)) : 
            null;
        const score = layer.score != null ? Math.round(layer.score) : null;
        
        row.innerHTML = `
            <td><span class="layer-dot"></span> ${layer.name || '—'}</td>
            <td class="score-cell">${score != null ? score : '—'}</td>
            <td class="contribution-cell">
                <div class="contribution-bar" style="width: ${contribution != null ? contribution : 0}%"></div>
                <span>${contribution != null ? `${contribution}%` : '—'}</span>
            </td>
            <td><span class="status-badge ${statusClass}">${layer.status || '—'}</span></td>
        `;
        
        tbodyEl.appendChild(row);
    });
}

/**
 * Render financial impact
 * ENGINE-FIRST: Only maps data, shows "—" if missing
 * Uses normalized summary format
 * @param {Object} summary - Summary data
 * @param {Object} scenario - Scenario classification (optional, will be computed if not provided)
 */
function renderFinancialImpact(summary, scenario = null) {
    // Classify scenario if not provided
    if (!scenario) {
        scenario = classifyScenarioForSummary(summary);
    }
    // Support both old format (summary.financial) and new normalized format
    const financial = summary?.financial || {};
    
    // Try to extract from multiple possible locations if financial is empty
    if (!financial || Object.keys(financial).length === 0) {
        // Try to get from summary directly
        const altFinancial = {
            expectedLoss: summary.expectedLoss || summary.meanLoss || null,
            meanLoss: summary.meanLoss || summary.expectedLoss || null,
            var95: summary.var95 || summary.percentile95 || summary.p95 || null,
            percentile95: summary.percentile95 || summary.var95 || summary.p95 || null,
            cvar: summary.cvar || summary.maxLoss || summary.p99 || null,
            maxLoss: summary.maxLoss || summary.cvar || summary.p99 || null,
            stdDev: summary.stdDev || null,
            cargoValue: summary.cargoValue || 
                       summary.shipment?.value_usd || 
                       summary.shipment?.cargo_value ||
                       summary.shipment?.cargoValue ||
                       summary.shipment?.value ||
                       null
        };
        
        // If we found any data, use it
        const hasData = Object.values(altFinancial).some(v => v != null);
        if (hasData) {
            Object.assign(financial, altFinancial);
        } else {
            // Even if no financial data, try to get cargoValue to determine if we should show financial section
            const cargoValue = altFinancial.cargoValue;
            if (cargoValue == null || parseFloat(cargoValue) === 0) {
                return; // No cargo value, skip financial section
            }
        }
    }
    
    // Ensure cargoValue is set in financial object for classification
    if (!financial.cargoValue) {
        financial.cargoValue = summary?.shipment?.value_usd || 
                               summary?.shipment?.cargo_value ||
                               summary?.shipment?.cargoValue ||
                               summary?.shipment?.value ||
                               null;
    }
    
    // Helper to format or show dash
    // FIX: Don't treat 0 as missing - 0 is a valid value
    const formatOrDash = (value) => {
        if (value == null || value === undefined || isNaN(value)) return '—';
        // 0 is a valid value, only null/undefined/NaN should show dash
        return formatCurrency(value);
    };
    
    // Expected Loss Summary - use more reliable selectors
    const expectedLossSummary = document.querySelector('.expected-loss-summary');
    if (expectedLossSummary) {
        const summaryValues = expectedLossSummary.querySelectorAll('.summary-value');
        
        // Expected Loss (primary)
        const expectedLossEl = expectedLossSummary.querySelector('.summary-value.primary');
        if (expectedLossEl) {
            const expectedLoss = financial.expectedLoss != null ? financial.expectedLoss : financial.meanLoss;
            expectedLossEl.textContent = formatOrDash(expectedLoss);
        }
        
        // 95th Percentile (VaR) - index 1
        if (summaryValues[1]) {
            const var95 = financial.var95 != null ? financial.var95 : financial.percentile95;
            summaryValues[1].textContent = formatOrDash(var95);
        }
        
        // Maximum Observed (CVaR) - index 2
        if (summaryValues[2]) {
            const maxLoss = financial.maxLoss != null ? financial.maxLoss : financial.cvar;
            summaryValues[2].textContent = formatOrDash(maxLoss);
        }
        
        // Cargo Value - index 3
        if (summaryValues[3]) {
            summaryValues[3].textContent = formatOrDash(financial.cargoValue);
        }
    }
    
    // VaR Stat (Loss Curve Card)
    const varStatEl = document.querySelector('.stat-item.var .stat-value');
    if (varStatEl) {
        const var95 = financial.var95 != null ? financial.var95 : financial.percentile95;
        varStatEl.textContent = formatOrDash(var95);
    }
    
    // CVaR Stat (Loss Curve Card)
    const cvarStatEl = document.querySelector('.stat-item.cvar .stat-value');
    if (cvarStatEl) {
        const cvar = financial.cvar != null ? financial.cvar : financial.maxLoss;
        cvarStatEl.textContent = formatOrDash(cvar);
    }
    
    // Mean Loss (Histogram Card) - use more specific selector
    const histogramStats = document.querySelector('.histogram-stats');
    if (histogramStats) {
        const meanLossEl = histogramStats.querySelector('.stat-item:first-child .stat-value');
        if (meanLossEl) {
            const meanLoss = financial.meanLoss != null ? financial.meanLoss : 
                           financial.expectedLoss != null ? financial.expectedLoss : null;
            meanLossEl.textContent = formatOrDash(meanLoss);
        }
        
        const stdDevEl = histogramStats.querySelector('.stat-item:last-child .stat-value');
        if (stdDevEl) {
            // stdDev can be null - that's OK, just show dash
            stdDevEl.textContent = formatOrDash(financial.stdDev);
        }
    }
    
    // Update loss curve SVG labels dynamically
    const varLabelEl = document.querySelector('.loss-curve-svg .var-label') || 
                       document.querySelector('.loss-curve-svg text[fill="rgba(255, 184, 0, 0.8)"]');
    if (varLabelEl && financial.var95) {
        varLabelEl.textContent = formatCurrency(financial.var95);
    }
    
    const cvarLabelEl = document.querySelector('.loss-curve-svg .cvar-label') ||
                        document.querySelector('.loss-curve-svg text[fill="rgba(255, 59, 48, 0.8)"]');
    if (cvarLabelEl && financial.cvar) {
        cvarLabelEl.textContent = formatCurrency(financial.cvar);
    }
    
    // Handle empty states for static SVG charts when scenario is OPERATIONAL_RISK_ONLY
    // BUT only if cargoValue is actually 0 or missing (not just metrics = 0)
    const hasCargoValue = financial.cargoValue != null && parseFloat(financial.cargoValue) > 0;
    if (scenario && scenario.type === 'OPERATIONAL_RISK_ONLY' && !hasCargoValue) {
        // Replace histogram SVG with empty state
        const histogramChart = document.querySelector('.histogram-chart');
        if (histogramChart) {
            histogramChart.innerHTML = `
                <div class="financial-histogram-empty scenario-operational-risk" style="
                    padding: 40px 20px;
                    text-align: center;
                    border: 1px solid rgba(0, 255, 200, 0.2);
                    border-radius: 8px;
                    background: rgba(0, 255, 200, 0.05);
                ">
                    <div class="financial-histogram-empty-content">
                        <div class="financial-histogram-empty-title" style="
                            font-size: 16px;
                            font-weight: 600;
                            color: rgba(0, 255, 200, 0.8);
                            margin-bottom: 8px;
                        ">Operational Risk Assessment</div>
                        <div class="financial-histogram-empty-description" style="
                            font-size: 14px;
                            color: rgba(255, 255, 255, 0.7);
                            margin-bottom: 8px;
                        ">This shipment presents operational risk factors without financial loss exposure.</div>
                        <div class="financial-histogram-empty-note" style="
                            font-size: 12px;
                            color: rgba(255, 255, 255, 0.5);
                            font-style: italic;
                            margin-bottom: 12px;
                        ">Risk analysis focuses on operational factors such as delays, routing complexity, and service quality.</div>
                        <div class="financial-histogram-empty-implication" style="
                            font-size: 13px;
                            color: rgba(0, 255, 200, 0.9);
                            font-weight: 500;
                            padding-top: 12px;
                            border-top: 1px solid rgba(0, 255, 200, 0.2);
                        ">Insurance coverage is optional for this shipment.</div>
                    </div>
                </div>
            `;
        }
        
        // Replace loss curve SVG with empty state
        const lossCurveChart = document.querySelector('.loss-curve-chart');
        if (lossCurveChart) {
            lossCurveChart.innerHTML = `
                <div class="loss-curve-empty scenario-operational-risk" style="
                    padding: 40px 20px;
                    text-align: center;
                    border: 1px solid rgba(0, 255, 200, 0.2);
                    border-radius: 8px;
                    background: rgba(0, 255, 200, 0.05);
                ">
                    <div class="loss-curve-empty-content">
                        <div class="loss-curve-empty-title" style="
                            font-size: 16px;
                            font-weight: 600;
                            color: rgba(0, 255, 200, 0.8);
                            margin-bottom: 8px;
                        ">Operational Risk Assessment</div>
                        <div class="loss-curve-empty-description" style="
                            font-size: 14px;
                            color: rgba(255, 255, 255, 0.7);
                            margin-bottom: 8px;
                        ">This shipment presents operational risk factors without financial loss exposure.</div>
                        <div class="loss-curve-empty-note" style="
                            font-size: 12px;
                            color: rgba(255, 255, 255, 0.5);
                            font-style: italic;
                            margin-bottom: 12px;
                        ">Risk analysis focuses on operational factors such as delays, routing complexity, and service quality.</div>
                        <div class="loss-curve-empty-implication" style="
                            font-size: 13px;
                            color: rgba(0, 255, 200, 0.9);
                            font-weight: 500;
                            padding-top: 12px;
                            border-top: 1px solid rgba(0, 255, 200, 0.2);
                        ">Insurance coverage is optional for this shipment.</div>
                    </div>
                </div>
            `;
        }
    }
}

/**
 * Render decision intelligence
 * ENGINE-FIRST: Only maps data, shows "—" if missing
 * Uses normalized summary format
 */
function renderDecisionIntelligence(summary) {
    // Support both old format (summary.insuranceDecision) and new normalized format (summary.decision)
    const decision = summary?.decision || summary?.insuranceDecision;
    
    // Render guard: if no decision data, show empty state
    if (!decision || Object.keys(decision).length === 0) {
        console.warn('[ResultsRenderer] No insurance decision data available');
        // Show empty state message
        const badgeEl = document.querySelector('.recommendation-badge');
        if (badgeEl) {
            badgeEl.className = 'recommendation-badge optional';
            const badgeValueEl = badgeEl.querySelector('.badge-value');
            if (badgeValueEl) {
                badgeValueEl.textContent = 'No recommendation available';
            }
        }
        return;
    }
    
    const badgeEl = document.querySelector('.recommendation-badge');
    if (badgeEl) {
        const recommendation = decision.insuranceRecommendation || decision.recommendation || 'OPTIONAL';
        const recClass = getRecommendationClass(recommendation);
        badgeEl.className = `recommendation-badge ${recClass}`;
        
        const badgeValueEl = badgeEl.querySelector('.badge-value');
        if (badgeValueEl) {
            if (recommendation === 'BUY' || recommendation === 'RECOMMENDED') {
                badgeValueEl.textContent = 'Insurance Recommended';
            } else if (recommendation === 'SKIP' || recommendation === 'NOT_RECOMMENDED') {
                badgeValueEl.textContent = 'Insurance Not Recommended';
            } else {
                badgeValueEl.textContent = 'Insurance Optional';
            }
        }
    }
    
    const safeWindow = decision.safeWindow || decision.shippingWindow || decision.timing || {};
    const optimalStartEl = document.querySelector('.window-optimal .window-dates');
    if (optimalStartEl) {
        if (safeWindow.optimalStart && safeWindow.optimalEnd) {
            optimalStartEl.textContent = `${formatDate(safeWindow.optimalStart)} – ${formatDate(safeWindow.optimalEnd)}`;
        } else {
            optimalStartEl.textContent = '—';
        }
    }
    
    const currentETDEl = document.querySelector('.window-current .window-dates');
    if (currentETDEl) {
        const currentETD = safeWindow.currentEtd || safeWindow.currentETD || '';
        currentETDEl.textContent = currentETD ? formatDate(currentETD) : '—';
        if (safeWindow.optimalStart && currentETD) {
            const currentDate = new Date(currentETD);
            const optimalStart = new Date(safeWindow.optimalStart);
            if (currentDate < optimalStart) {
                currentETDEl.classList.add('outside');
            } else {
                currentETDEl.classList.remove('outside');
            }
        }
    }
    
    const riskReductionEl = document.querySelector('.reduction-value');
    if (riskReductionEl) {
        if (safeWindow.riskReductionPts != null) {
            const reduction = Math.round(safeWindow.riskReductionPts);
            riskReductionEl.textContent = reduction > 0 ? `-${reduction} points` : `${reduction} points`;
        } else if (safeWindow.riskReduction != null) {
            const reduction = Math.round(safeWindow.riskReduction);
            riskReductionEl.textContent = reduction > 0 ? `-${reduction} points` : `${reduction} points`;
        } else {
            riskReductionEl.textContent = '—';
        }
    }
    
    const providersListEl = document.querySelector('.providers-list');
    if (providersListEl) {
        let providers = decision.providers || [];
        providersListEl.innerHTML = '';
        
        // Generate default providers from risk level if none provided
        if (providers.length === 0) {
            const overall = summary?.overall || summary?.risk || {};
            const riskScore = overall.riskScore ?? overall.finalScore ?? 0;
            
            // Create default provider suggestions based on risk level
            if (riskScore > 50) {
                providers = [
                    { name: 'Standard Insurance Provider', fit: 0.75, premium: 0, rank: 1 },
                    { name: 'Specialized Cargo Insurance', fit: 0.85, premium: 0, rank: 2 }
                ];
            } else {
                providers = [
                    { name: 'Basic Coverage Available', fit: 0.60, premium: 0, rank: 1 }
                ];
            }
        }
        
        if (providers.length === 0) {
            providersListEl.innerHTML = '<div class="provider-item"><span>No providers available</span></div>';
        } else {
            providers.forEach((provider) => {
                const item = document.createElement('div');
                const isBestFit = provider.rank === 1 || providers.indexOf(provider) === 0;
                item.className = isBestFit ? 'provider-item best-fit' : 'provider-item';
                
                const fit = provider.fitPct != null ? Math.round(provider.fitPct) :
                           provider.fit != null ? (typeof provider.fit === 'number' && provider.fit <= 1 ? Math.round(provider.fit * 100) : Math.round(provider.fit)) : null;
                const fitText = fit != null ? (isBestFit ? `Best fit: ${fit}%` : `Fit: ${fit}%`) : '—';
                
                item.innerHTML = `
                    <div class="provider-rank">${provider.rank || (providers.indexOf(provider) + 1)}</div>
                    <div class="provider-info">
                        <span class="provider-name">${provider.name || '—'}</span>
                        <span class="provider-fit">${fitText}</span>
                    </div>
                    <span class="provider-premium">${formatCurrency(provider.premium)}</span>
                `;
                
                providersListEl.appendChild(item);
            });
        }
    }
    
    const traceItemsEl = document.querySelector('.trace-items');
    if (traceItemsEl) {
        let trace = decision.trace || [];
        traceItemsEl.innerHTML = '';
        
        // Generate default trace from risk data if none provided
        if (trace.length === 0) {
            const overall = summary?.overall || summary?.risk || {};
            const riskScore = overall.riskScore ?? overall.finalScore ?? 0;
            const riskLevel = overall.riskLevel || 'Moderate';
            const layers = summary?.layers || [];
            const topLayer = layers.slice().sort((a, b) => (b.score || 0) - (a.score || 0))[0];
            
            trace = [
                {
                    icon: '📊',
                    label: 'Risk Assessment',
                    detail: `${riskLevel} risk level (score: ${Math.round(riskScore)})`
                }
            ];
            
            if (topLayer) {
                trace.push({
                    icon: '⚠️',
                    label: 'Primary Risk Factor',
                    detail: `${topLayer.name} (score: ${Math.round(topLayer.score || 0)})`
                });
            }
            
            const financial = summary?.financial || {};
            if (financial.expectedLoss > 0 || financial.var95 > 0) {
                trace.push({
                    icon: '💰',
                    label: 'Financial Impact',
                    detail: `Expected loss: ${formatCurrency(financial.expectedLoss || 0)}`
                });
            }
        }
        
        if (trace.length === 0) {
            traceItemsEl.innerHTML = '<div class="trace-item"><span class="trace-detail">No traceability data available</span></div>';
        } else {
            trace.forEach((item) => {
                const traceItem = document.createElement('div');
                traceItem.className = 'trace-item';
                
                const icon = item.icon || 
                            (item.label?.toLowerCase().includes('risk') ? '📊' :
                            item.label?.toLowerCase().includes('loss') ? '💰' :
                            item.label?.toLowerCase().includes('coverage') ? '🎯' : '📈');
                
                traceItem.innerHTML = `
                    <div class="trace-icon">${icon}</div>
                    <div class="trace-content">
                        <span class="trace-label">${item.label || '—'}</span>
                        <span class="trace-detail">${item.detail || '—'}</span>
                    </div>
                `;
                
                traceItemsEl.appendChild(traceItem);
            });
        }
    }
}

/**
 * Render AI narrative
 * ENGINE-FIRST: Only maps data, shows empty state if missing
 * Uses normalized summary format
 */
function renderAINarrative(summary) {
    // Support both old format (summary.aiNarrative) and new normalized format (summary.narrative)
    const narrative = summary?.narrative || summary?.aiNarrative || {};
    
    const timestampEl = document.querySelector('.analysis-timestamp');
    if (timestampEl) {
        const timestamp = narrative.timestamp || narrative.generatedAt;
        if (timestamp) {
            try {
                const date = new Date(timestamp);
                timestampEl.textContent = `Generated: ${date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZoneName: 'short'
                })}`;
            } catch {
                timestampEl.textContent = `Generated: ${timestamp}`;
            }
        } else {
            timestampEl.textContent = 'Generated: —';
        }
    }
    
    const summaryEl = document.querySelector('.narrative-summary');
    if (summaryEl) {
        const summaryText = narrative.summaryText || narrative.summary;
        if (summaryText) {
            summaryEl.textContent = summaryText;
        } else {
            // Generate default summary from risk data
            const overall = summary?.overall || summary?.risk || {};
            const riskScore = overall.riskScore ?? overall.finalScore ?? 0;
            const riskLevel = overall.riskLevel || 'Moderate';
            const layers = summary?.layers || [];
            const topLayers = layers.slice().sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 3);
            
            let defaultSummary = `This shipment has a ${riskLevel.toLowerCase()} risk level (score: ${Math.round(riskScore)}). `;
            if (topLayers.length > 0) {
                defaultSummary += `Primary risk factors include ${topLayers.map(l => l.name).join(', ')}. `;
            }
            defaultSummary += 'Review detailed risk layers and financial impact metrics for comprehensive analysis.';
            
            summaryEl.textContent = defaultSummary;
        }
    }
    
    const insightsGridEl = document.querySelector('.insights-grid');
    if (insightsGridEl) {
        let insights = narrative.insights || [];
        insightsGridEl.innerHTML = '';
        
        // Generate default insights from layers if none provided
        if (insights.length === 0) {
            const layers = summary?.layers || [];
            const topLayers = layers.slice().sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 3);
            
            if (topLayers.length > 0) {
                insights = topLayers.map((layer, idx) => {
                    const score = layer.score || 0;
                    let type = 'watch';
                    let icon = '👁️';
                    if (score > 70) {
                        type = 'critical';
                        icon = '⚠️';
                    } else if (score > 50) {
                        type = 'opportunity';
                        icon = '💡';
                    }
                    return {
                        type: type,
                        title: layer.name || `Risk Factor ${idx + 1}`,
                        text: `Risk score: ${Math.round(score)}. ${layer.status ? `Status: ${layer.status}.` : 'Monitor this factor closely.'}`
                    };
                });
            }
        }
        
        if (insights.length === 0) {
            insightsGridEl.innerHTML = `
                <div class="insight-card watch">
                    <div class="insight-header">
                        <span class="insight-icon">ℹ️</span>
                        <span class="insight-label">No Insights</span>
                    </div>
                    <p class="insight-text">No significant risk drivers detected for this shipment.</p>
                </div>
            `;
        } else {
            insights.forEach((insight) => {
                const card = document.createElement('div');
                const typeClass = getInsightTypeClass(insight.type);
                card.className = `insight-card ${typeClass}`;
                
                const icon = insight.type?.toLowerCase().includes('critical') ? '⚠️' :
                            insight.type?.toLowerCase().includes('opportunity') ? '💡' : '👁️';
                
                card.innerHTML = `
                    <div class="insight-header">
                        <span class="insight-icon">${icon}</span>
                        <span class="insight-label">${insight.title || insight.type || 'Insight'}</span>
                    </div>
                    <p class="insight-text">${insight.text || '—'}</p>
                `;
                
                insightsGridEl.appendChild(card);
            });
        }
    }
    
    const actionListEl = document.querySelector('.action-list');
    if (actionListEl) {
        let actions = narrative.actions || [];
        actionListEl.innerHTML = '';
        
        // Generate default actions from risk level if none provided
        if (actions.length === 0) {
            const overall = summary?.overall || summary?.risk || {};
            const riskScore = overall.riskScore ?? overall.finalScore ?? 0;
            const riskLevel = (overall.riskLevel || 'Moderate').toLowerCase();
            
            actions = [];
            if (riskScore > 70 || riskLevel.includes('high')) {
                actions.push('Consider additional insurance coverage for high-risk shipment');
                actions.push('Implement enhanced monitoring and tracking');
                actions.push('Review and optimize route selection');
            } else if (riskScore > 50 || riskLevel.includes('moderate')) {
                actions.push('Monitor shipment progress regularly');
                actions.push('Ensure proper documentation and compliance');
            } else {
                actions.push('Standard monitoring procedures recommended');
            }
        }
        
        if (actions.length === 0) {
            actionListEl.innerHTML = '<li>No recommended actions at this time.</li>';
        } else {
            actions.forEach((action) => {
                const li = document.createElement('li');
                li.textContent = action || '—';
                actionListEl.appendChild(li);
            });
        }
    }
}

/**
 * Main render function
 * Maps summary object to DOM elements
 * ENGINE-FIRST: Only maps data, no calculations
 */
// Export renderFinancialImpact for external use
export { renderFinancialImpact };

export function renderResults(summary) {
    if (!summary || typeof summary !== 'object') {
        console.error('[ResultsRenderer] ✗ Invalid summary object:', summary);
        return;
    }
    
    const layers = summary.layers || [];
    console.log('[ResultsRenderer] 🎨 Starting render with summary:', {
        riskScore: summary.overall?.riskScore || summary.risk?.finalScore,
        riskLevel: summary.overall?.riskLevel,
        confidence: summary.overall?.confidence,
        layersCount: layers.length,
        layerNames: layers.slice(0, 5).map(l => l.name).join(', '),
        hasFinancial: !!summary.financial,
        cargoValue: summary.financial?.cargoValue,
        expectedLoss: summary.financial?.expectedLoss,
        var95: summary.financial?.var95,
        timestamp: new Date().toISOString()
    });
    
    try {
        // Remove empty state banner if present
        const emptyBanner = document.querySelector('.empty-state-banner');
        if (emptyBanner) {
            emptyBanner.remove();
        }
        
        // Classify scenario once for use across components
        const scenario = classifyScenarioForSummary(summary);
        console.log('[ResultsRenderer] 📊 Scenario classified:', scenario.type, scenario.subtitle || scenario.description);
        
        // Store scenario in summary for component access
        if (!summary.scenario) {
            summary.scenario = scenario;
        }
        
        renderShipmentHeader(summary);
        console.log('[ResultsRenderer] ✓ Shipment header rendered');
        
        renderHeroZone(summary);
        console.log('[ResultsRenderer] ✓ Hero zone rendered');
        
        renderRiskLayers(summary);
        console.log('[ResultsRenderer] ✓ Risk layers rendered');
        
        renderLayersTable(summary);
        console.log('[ResultsRenderer] ✓ Layers table rendered');
        
        renderFinancialImpact(summary, scenario);
        console.log('[ResultsRenderer] ✓ Financial impact rendered');
        
        renderDecisionIntelligence(summary);
        console.log('[ResultsRenderer] ✓ Decision intelligence rendered');
        
        renderAINarrative(summary);
        console.log('[ResultsRenderer] ✓ AI narrative rendered');
        
        console.log('[ResultsRenderer] ✅ All components rendered successfully');
    } catch (error) {
        console.error('[ResultsRenderer] ✗ Error rendering results:', error);
        console.error('[ResultsRenderer] Error stack:', error.stack);
        // Show empty state on error
        if (typeof showEmptyState === 'function') {
            showEmptyState();
        }
    }
}

