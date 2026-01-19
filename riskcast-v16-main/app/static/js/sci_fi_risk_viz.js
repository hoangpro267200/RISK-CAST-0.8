/**
 * SCI-FI CINEMATIC RISK VISUALIZATION
 * 
 * Creates orbital layout with central Risk Score orb
 * and floating risk factor cards arranged around it.
 */

(function() {
    'use strict';

    // Factor mapping with beautiful SVG-style icons
    const FACTOR_MAP = {
        'equipment': { name: 'Equipment', icon: getIconSVG('equipment') },
        'weather': { name: 'Weather', icon: getIconSVG('weather') },
        'esg': { name: 'ESG', icon: getIconSVG('esg') },
        'port': { name: 'Port', icon: getIconSVG('port') },
        'climate': { name: 'Climate', icon: getIconSVG('climate') },
        'carrier': { name: 'Carrier', icon: getIconSVG('carrier') },
        'geopolitical': { name: 'Geopolitical', icon: getIconSVG('geopolitical') },
        'delay': { name: 'Delay', icon: getIconSVG('delay') },
        'cargo': { name: 'Cargo', icon: getIconSVG('cargo') },
        'route': { name: 'Route', icon: getIconSVG('route') },
        'transport': { name: 'Transport', icon: getIconSVG('transport') }
    };

    /**
     * Get beautiful, modern SVG icons for sci-fi theme
     * All icons are monochromatic, consistent, and visually appealing
     */
    function getIconSVG(type) {
        const icons = {
            // Equipment - Modern gear/cog icon
            'equipment': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/></svg>',
            
            // Weather - Cloud with lightning
            'weather': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/><polyline points="13 10 9 16 13 16 11 20"/></svg>',
            
            // ESG - Leaf/growth icon
            'esg': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/><path d="M12 6v6l4 2"/><path d="M8 12c0-2.21 1.79-4 4-4s4 1.79 4 4"/></svg>',
            
            // Port - Anchor icon (modern, clean)
            'port': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M12 2C9.79 2 8 3.79 8 6s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"/><circle cx="12" cy="6" r="2"/><path d="M8 10c0 2.21 1.79 4 4 4s4-1.79 4-4"/></svg>',
            
            // Climate - Globe with grid lines
            'climate': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M12 2a15.3 15.3 0 0 0-4 10 15.3 15.3 0 0 0 4 10"/></svg>',
            
            // Carrier - Ship/container vessel
            'carrier': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18h18M3 18l2-8h14l2 8M3 18v2M21 18v2"/><rect x="5" y="10" width="14" height="8" rx="1"/><path d="M7 10V8a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2"/><circle cx="9" cy="18" r="1"/><circle cx="15" cy="18" r="1"/></svg>',
            
            // Geopolitical - Globe with network
            'geopolitical': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><circle cx="12" cy="12" r="2"/><path d="M8 8l8 8M16 8l-8 8"/></svg>',
            
            // Delay - Clock with alert
            'delay': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/></svg>',
            
            // Cargo - Container box
            'cargo': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="18" height="14" rx="1"/><path d="M3 7l9-4 9 4M3 7v14M21 7v14"/><line x1="3" y1="12" x2="21" y2="12"/><path d="M8 7v5M16 7v5"/></svg>',
            
            // Route - Navigation/route path
            'route': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M12 7v4M5 17l7-7M19 17l-7-7"/><path d="M12 11l-7 6M12 11l7 6"/></svg>',
            
            // Transport - Modern truck/vehicle
            'transport': '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="14" height="10" rx="1"/><path d="M17 8V6a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v2"/><line x1="3" y1="13" x2="17" y2="13"/><path d="M17 18h1a2 2 0 0 0 2-2v-2"/><circle cx="7" cy="18" r="2"/><circle cx="19" cy="18" r="2"/></svg>'
        };
        return icons[type] || icons['equipment'];
    }

    /**
     * Initialize sci-fi risk visualization
     */
    function initSciFiViz() {
        console.log('[SciFiViz] Initializing...');
        const container = document.getElementById('sci-fi-risk-viz');
        if (!container) {
            console.error('[SciFiViz] Container #sci-fi-risk-viz not found!');
            return;
        }

        // Force visibility with inline styles to override any CSS - compact layout
        container.style.cssText = `
            position: relative !important;
            width: 100% !important;
            min-height: 420px !important;
            padding: 4rem 2rem 1rem 2rem !important;
            margin: 0 auto !important;
            overflow: visible !important;
            background: radial-gradient(ellipse at 50% 40%, rgba(0, 255, 200, 0.05) 0%, transparent 60%), radial-gradient(circle at 50% 50%, rgba(0, 100, 200, 0.03) 0%, transparent 80%), linear-gradient(180deg, #050810 0%, #0a0e1a 30%, #0d1117 70%, #050810 100%) !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 100 !important;
        `;
        
        // Also ensure container is in viewport
        const containerRect = container.getBoundingClientRect();
        console.log('[SciFiViz] Container dimensions:', {
            width: containerRect.width,
            height: containerRect.height,
            top: containerRect.top,
            left: containerRect.left
        });
        
        // Force sci-fi-container visibility and centering - compact layout
        const sciFiContainer = container.querySelector('.sci-fi-container');
        if (sciFiContainer) {
            sciFiContainer.style.cssText = `
                position: relative !important;
                width: 100% !important;
                max-width: 900px !important;
                margin: 0 auto !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: flex-start !important;
                min-height: auto !important;
                padding: 0 !important;
            `;
        }
        
        // Ensure risk-orb-core is centered and smaller - no margin for compact layout
        const orbCore = container.querySelector('.risk-orb-core');
        if (orbCore) {
            orbCore.style.cssText = `
                position: relative !important;
                width: 220px !important;
                height: 220px !important;
                margin: 0 auto !important;
                z-index: 10 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            `;
        }
        
        // Make orb inner smaller
        const orbInner = orbCore?.querySelector('.orb-inner');
        if (orbInner) {
            orbInner.style.cssText = `
                position: relative !important;
                width: 180px !important;
                height: 180px !important;
                border-radius: 50% !important;
                background: radial-gradient(circle at 30% 30%, rgba(0, 255, 200, 0.4), rgba(0, 255, 200, 0.15)), radial-gradient(circle at center, rgba(0, 255, 200, 0.25), transparent 75%) !important;
                border: 4px solid rgba(0, 255, 200, 0.7) !important;
                box-shadow: 0 0 50px rgba(0, 255, 200, 0.5), 0 0 100px rgba(0, 255, 200, 0.3), 0 0 150px rgba(0, 255, 200, 0.1), inset 0 0 50px rgba(0, 255, 200, 0.15) !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                backdrop-filter: blur(15px) !important;
                -webkit-backdrop-filter: blur(15px) !important;
                z-index: 2 !important;
            `;
        }
        
        // Make score text smaller
        const scoreValue = container.querySelector('.orb-score-value');
        if (scoreValue) {
            scoreValue.style.cssText = `
                font-size: 4.5rem !important;
                font-weight: 900 !important;
                color: #ffffff !important;
                text-shadow: 0 0 30px rgba(0, 255, 200, 1), 0 0 60px rgba(0, 255, 200, 0.8), 0 0 90px rgba(0, 255, 200, 0.5), 0 0 120px rgba(0, 255, 200, 0.3) !important;
                line-height: 1 !important;
                margin-bottom: 0.5rem !important;
                letter-spacing: -0.05em !important;
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            `;
        }
        
        // Update orb rings size
        const orbRings = orbCore?.querySelector('.orb-rings');
        if (orbRings) {
            orbRings.style.cssText = `
                position: absolute !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                width: 220px !important;
                height: 220px !important;
                z-index: 0 !important;
            `;
        }

        // Ensure connection lines SVG is visible
        const connectionLines = container.querySelector('#connection-lines');
        if (connectionLines) {
            connectionLines.style.cssText = `
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                pointer-events: none !important;
                z-index: 1 !important;
                opacity: 1 !important;
                display: block !important;
                visibility: visible !important;
            `;
        }
        
        console.log('[SciFiViz] Container found, checking for data...');

        // Try to get data immediately
        let data = getRiskData();
        
        if (data && data.factors && Object.keys(data.factors).length > 0) {
            console.log('[SciFiViz] Data found immediately:', data);
            renderVisualization(data);
        } else {
            // Render with defaults immediately, then update if data arrives
            console.log('[SciFiViz] Rendering with defaults first, will update if data arrives');
            renderVisualization(getDefaultData());
            
            // Continue checking for real data
            let attempts = 0;
            const maxAttempts = 30; // 3 seconds
            
            const checkData = setInterval(() => {
                attempts++;
                data = getRiskData();
                
                if (data && data.factors && Object.keys(data.factors).length > 0) {
                    console.log('[SciFiViz] Real data found after', attempts * 100, 'ms, updating:', data);
                    clearInterval(checkData);
                    renderVisualization(data);
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkData);
                }
            }, 100);
        }
    }

    /**
     * Get risk data from various sources
     */
    function getRiskData() {
        console.log('[SciFiViz] Checking data sources...');
        
        // Source 1: window.__RISKCAST_SUMMARY__
        if (window.__RISKCAST_SUMMARY__) {
            console.log('[SciFiViz] Found window.__RISKCAST_SUMMARY__');
            const summary = window.__RISKCAST_SUMMARY__;
            const data = extractDataFromSummary(summary);
            if (data && data.riskScore) {
                return data;
            }
        }

        // Source 2: window.__RESULTSOS__
        if (window.__RESULTSOS__) {
            console.log('[SciFiViz] Found window.__RESULTSOS__');
            const summary = window.__RESULTSOS__.summary || window.__RESULTSOS__.state;
            if (summary) {
                const data = extractDataFromSummary(summary);
                if (data && data.riskScore) {
                    return data;
                }
            }
        }

        // Source 3: DOM elements (from resultsRenderer or any rendered content)
        console.log('[SciFiViz] Checking DOM elements...');
        const scoreEl = document.querySelector('.score-value') || 
                       document.querySelector('#risk-score-value') ||
                       document.querySelector('[id*="risk-score"]');
        const confidenceEl = document.querySelector('.confidence-value') ||
                            document.querySelector('[id*="confidence"]');
        const layers = Array.from(document.querySelectorAll('.layer-card'));

        // Also try to find factor list in text format
        const factorList = document.querySelectorAll('[class*="factor"], [data-factor]');
        
        if (scoreEl || layers.length > 0 || factorList.length > 0) {
            console.log('[SciFiViz] Found DOM elements:', {
                scoreEl: !!scoreEl,
                confidenceEl: !!confidenceEl,
                layers: layers.length,
                factorList: factorList.length
            });
            return extractDataFromDOM(scoreEl, confidenceEl, layers);
        }

        console.log('[SciFiViz] No data sources found');
        return null;
    }

    /**
     * Extract data from summary object
     */
    function extractDataFromSummary(summary) {
        const overall = summary.overall || summary.risk || {};
        const layers = summary.layers || [];
        const confidence = overall.confidence != null ? 
            (overall.confidence > 1 ? overall.confidence / 100 : overall.confidence) : 
            0.76;

        // Map layers to factors
        const factors = {};
        layers.forEach(layer => {
            if (layer.name) {
                const key = layer.name.toLowerCase().replace(/\s+/g, '_');
                const score = layer.score != null ? 
                    (layer.score > 100 ? layer.score / 10 : layer.score) : 
                    0;
                factors[key] = {
                    name: layer.name,
                    score: Math.round(score),
                    icon: FACTOR_MAP[key]?.icon || getIconSVG('equipment')
                };
            }
        });

        // If no factors from layers, try to get from factors array/object
        if (Object.keys(factors).length === 0 && summary.factors) {
            if (Array.isArray(summary.factors)) {
                summary.factors.forEach(factor => {
                    const key = (factor.name || factor.factor || '').toLowerCase().replace(/\s+/g, '_');
                    if (key) {
                        factors[key] = {
                            name: factor.name || factor.factor,
                            score: Math.round(factor.score || factor.value || 0),
                            icon: FACTOR_MAP[key]?.icon || getIconSVG('equipment')
                        };
                    }
                });
            } else if (typeof summary.factors === 'object') {
                Object.entries(summary.factors).forEach(([key, value]) => {
                    const normalizedKey = key.toLowerCase().replace(/\s+/g, '_');
                    factors[normalizedKey] = {
                        name: FACTOR_MAP[normalizedKey]?.name || key,
                        score: Math.round((typeof value === 'number' ? value : parseFloat(value) || 0) * 100),
                        icon: FACTOR_MAP[normalizedKey]?.icon || getIconSVG('equipment')
                    };
                });
            }
        }

        return {
            riskScore: overall.riskScore != null ? Math.round(overall.riskScore) : 16,
            riskLevel: overall.riskLevel || 'low',
            confidence: Math.round(confidence * 100),
            factors: factors
        };
    }

    /**
     * Extract data from DOM elements
     */
    function extractDataFromDOM(scoreEl, confidenceEl, layers) {
        // Try multiple selectors for risk score
        let riskScore = 16;
        if (scoreEl) {
            riskScore = parseInt(scoreEl.textContent) || 16;
        } else {
            // Try other selectors
            const altScoreEl = document.querySelector('.score-value') || 
                              document.querySelector('#risk-score-value') ||
                              document.querySelector('[class*="risk-score"]');
            if (altScoreEl) {
                riskScore = parseInt(altScoreEl.textContent) || 16;
            }
        }

        // Try multiple selectors for confidence
        let confidence = 76;
        if (confidenceEl) {
            confidence = parseInt(confidenceEl.textContent.replace('%', '')) || 76;
        } else {
            const altConfEl = document.querySelector('.confidence-value') ||
                             document.querySelector('#sci-fi-confidence');
            if (altConfEl) {
                confidence = parseInt(altConfEl.textContent.replace('%', '')) || 76;
            }
        }

        const factors = {};
        
        // Try to get layers from multiple sources
        if (layers && layers.length > 0) {
            layers.forEach((layer, index) => {
                const nameEl = layer.querySelector('.layer-name');
                const scoreEl = layer.querySelector('.layer-score');
                if (nameEl && scoreEl) {
                    const name = nameEl.textContent.trim();
                    const key = name.toLowerCase().replace(/\s+/g, '_');
                    const score = parseInt(scoreEl.textContent) || 0;
                    factors[key] = {
                        name: name,
                        score: score,
                        icon: FACTOR_MAP[key]?.icon || getIconSVG('equipment')
                    };
                }
            });
        }

        // If no factors found, try to extract from text list (fallback)
        if (Object.keys(factors).length === 0) {
            // Try to parse from body text (format: "Icon NameNumber" or "Name Number")
            const bodyText = document.body.textContent || '';
            
            // Pattern: Icon + Name + Number (e.g., "📊 Transport0", "⛈️ Weather25", "Transport0", "Weather25")
            // Note: Some formats have no space between name and number
            const factorPatterns = [
                { pattern: /([📊⛈️⚓🚢⚙️🌍🌱🌐⏱️📦🗺️])\s*(Transport|Weather|Port|Carrier|Delay|Climate|ESG|Equipment|Geopolitical|Cargo|Route)\s*(\d+)/gi, iconIndex: 1, nameIndex: 2, scoreIndex: 3 },
                { pattern: /([📊⛈️⚓🚢⚙️🌍🌱🌐⏱️📦🗺️])\s*(Transport|Weather|Port|Carrier|Delay|Climate|ESG|Equipment|Geopolitical|Cargo|Route)(\d+)/gi, iconIndex: 1, nameIndex: 2, scoreIndex: 3 },
                { pattern: /(Transport|Weather|Port|Carrier|Delay|Climate|ESG|Equipment|Geopolitical|Cargo|Route)\s*(\d+)/gi, iconIndex: 0, nameIndex: 1, scoreIndex: 2 },
                { pattern: /(Transport|Weather|Port|Carrier|Delay|Climate|ESG|Equipment|Geopolitical|Cargo|Route)(\d+)/gi, iconIndex: 0, nameIndex: 1, scoreIndex: 2 }
            ];

            factorPatterns.forEach(({ pattern, iconIndex, nameIndex, scoreIndex }) => {
                let match;
                while ((match = pattern.exec(bodyText)) !== null && Object.keys(factors).length < 6) {
                    const name = match[nameIndex];
                    const score = parseInt(match[scoreIndex]);
                    const icon = iconIndex > 0 ? match[iconIndex] : FACTOR_MAP[name.toLowerCase()]?.icon || getIconSVG('equipment');
                    const key = name.toLowerCase();
                    
                    if (!factors[key] && !isNaN(score)) {
                        factors[key] = { name, score, icon };
                        console.log('[SciFiViz] Extracted factor from text:', key, score);
                    }
                }
            });
        }

        return {
            riskScore: riskScore,
            riskLevel: getRiskLevel(riskScore),
            confidence: confidence,
            factors: factors
        };
    }

    /**
     * Get default data for fallback
     * Uses visible text on page if available
     */
    function getDefaultData() {
        // Try to extract from visible text on page
        const pageText = document.body.textContent || '';
        
        // Try to find risk score in text
        let riskScore = 16;
        const scoreMatch = pageText.match(/(?:risk\s*score|score)[:\s]*(\d+)/i);
        if (scoreMatch) {
            riskScore = parseInt(scoreMatch[1]) || 16;
        }

        // Try to find confidence
        let confidence = 76;
        const confMatch = pageText.match(/(?:confidence|model\s*confidence)[:\s]*(\d+)/i);
        if (confMatch) {
            confidence = parseInt(confMatch[1]) || 76;
        }

        // Default factors (will be replaced if found in DOM)
        // Match the visible data from screenshot - use SVG icons
        const factors = {
            transport: { name: 'Transport', score: 0, icon: getIconSVG('transport') },
            weather: { name: 'Weather', score: 25, icon: getIconSVG('weather') },
            port: { name: 'Port', score: 17, icon: getIconSVG('port') },
            carrier: { name: 'Carrier', score: 17, icon: getIconSVG('carrier') },
            delay: { name: 'Delay', score: 15, icon: getIconSVG('delay') },
            climate: { name: 'Climate', score: 17, icon: getIconSVG('climate') }
        };
        
        // Also try to find "Port52" format (no space)
        const portMatch = pageText.match(/Port(\d+)/i);
        if (portMatch && factors.port) {
            factors.port.score = parseInt(portMatch[1]) || factors.port.score;
        }

        // Try to extract factors from visible text (support both "Name Number" and "NameNumber" formats)
        const factorPatterns = [
            { pattern: /(?:📊\s*)?transport[:\s]*(\d+)/i, key: 'transport' },
            { pattern: /(?:⛈️\s*)?weather[:\s]*(\d+)/i, key: 'weather' },
            { pattern: /(?:⚓\s*)?port[:\s]*(\d+)/i, key: 'port' },
            { pattern: /(?:🚢\s*)?carrier[:\s]*(\d+)/i, key: 'carrier' },
            { pattern: /(?:⚙️\s*)?delay[:\s]*(\d+)/i, key: 'delay' },
            { pattern: /(?:🌍\s*)?climate[:\s]*(\d+)/i, key: 'climate' },
            // Also try without space: "Transport0", "Weather25"
            { pattern: /transport(\d+)/i, key: 'transport' },
            { pattern: /weather(\d+)/i, key: 'weather' },
            { pattern: /port(\d+)/i, key: 'port' },
            { pattern: /carrier(\d+)/i, key: 'carrier' },
            { pattern: /delay(\d+)/i, key: 'delay' },
            { pattern: /climate(\d+)/i, key: 'climate' }
        ];

        factorPatterns.forEach(({ pattern, key }) => {
            const match = pageText.match(pattern);
            if (match && factors[key]) {
                const score = parseInt(match[1]);
                if (!isNaN(score)) {
                    factors[key].score = score;
                    console.log('[SciFiViz] Extracted', key, '=', score);
                }
            }
        });

        return {
            riskScore: riskScore,
            riskLevel: getRiskLevel(riskScore),
            confidence: confidence,
            factors: factors
        };
    }

    /**
     * Determine risk level from score
     */
    function getRiskLevel(score) {
        if (score <= 30) return 'low';
        if (score <= 60) return 'moderate';
        return 'high';
    }

    /**
     * Render the visualization
     */
    function renderVisualization(data) {
        console.log('[SciFiViz] Rendering with data:', data);
        
        if (!data) {
            console.error('[SciFiViz] No data provided!');
            return;
        }

        // Ensure we have at least some factors
        if (!data.factors || Object.keys(data.factors).length === 0) {
            console.warn('[SciFiViz] No factors found, using defaults');
            const defaultData = getDefaultData();
            data.factors = defaultData.factors;
            // Also use default risk score and confidence if missing
            if (!data.riskScore) data.riskScore = defaultData.riskScore;
            if (!data.riskLevel) data.riskLevel = defaultData.riskLevel;
            if (!data.confidence) data.confidence = defaultData.confidence;
        }

        // Update central orb
        updateRiskOrb(data.riskScore || 16, data.riskLevel || 'low');

        // Update factor cards in orbital layout (this will also draw connection lines)
        updateFactorCards(data.factors);

        // Update badge and confidence
        updateBadgeAndConfidence(data.riskLevel || 'low', data.confidence || 76);

        console.log('[SciFiViz] ✅ Visualization rendered successfully with', Object.keys(data.factors).length, 'factors');
    }

    /**
     * Update central risk orb with inline styles
     */
    function updateRiskOrb(score, level) {
        const scoreEl = document.getElementById('sci-fi-risk-score');
        const orbCore = document.querySelector('.risk-orb-core');
        const orbInner = orbCore?.querySelector('.orb-inner');

        if (scoreEl) {
            scoreEl.textContent = score;
            // Force visibility with inline styles - smaller font
            scoreEl.style.cssText = `
                font-size: 4.5rem !important;
                font-weight: 900 !important;
                color: #ffffff !important;
                text-shadow: 0 0 30px rgba(0, 255, 200, 1), 0 0 60px rgba(0, 255, 200, 0.8), 0 0 90px rgba(0, 255, 200, 0.5), 0 0 120px rgba(0, 255, 200, 0.3) !important;
                line-height: 1 !important;
                margin-bottom: 0.5rem !important;
                letter-spacing: -0.05em !important;
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            `;
        }

        if (orbCore) {
            // Remove existing risk level classes
            orbCore.classList.remove('low-risk', 'moderate-risk', 'high-risk');
            // Add new risk level class
            orbCore.classList.add(`${level}-risk`);
            // Force visibility with inline styles
            orbCore.style.cssText = `
                position: relative !important;
                width: 280px !important;
                height: 280px !important;
                margin: 2rem 0 !important;
                z-index: 10 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                visibility: visible !important;
                opacity: 1 !important;
            `;
            
            if (orbInner) {
                orbInner.style.cssText = `
                    position: relative !important;
                    width: 180px !important;
                    height: 180px !important;
                    border-radius: 50% !important;
                    background: radial-gradient(circle at 30% 30%, rgba(0, 255, 200, 0.4), rgba(0, 255, 200, 0.15)), radial-gradient(circle at center, rgba(0, 255, 200, 0.25), transparent 75%) !important;
                    border: 4px solid rgba(0, 255, 200, 0.7) !important;
                    box-shadow: 0 0 50px rgba(0, 255, 200, 0.5), 0 0 100px rgba(0, 255, 200, 0.3), 0 0 150px rgba(0, 255, 200, 0.1), inset 0 0 50px rgba(0, 255, 200, 0.15) !important;
                    display: flex !important;
                    flex-direction: column !important;
                    align-items: center !important;
                    justify-content: center !important;
                    backdrop-filter: blur(15px) !important;
                    -webkit-backdrop-filter: blur(15px) !important;
                    z-index: 2 !important;
                `;
            }
            
            console.log('[SciFiViz] Orb updated:', score, level);
        } else {
            console.error('[SciFiViz] Orb core not found!');
        }
    }

    /**
     * Update factor cards in orbital layout
     */
    function updateFactorCards(factors) {
        const orbit = document.getElementById('factor-orbit');
        if (!orbit) {
            console.error('[SciFiViz] Factor orbit container not found!');
            return;
        }

        console.log('[SciFiViz] Updating factor cards:', factors);

        // Clear existing cards
        const existingCards = orbit.querySelectorAll('.factor-card');
        existingCards.forEach(card => card.remove());

        // Get factor entries (limit to 6 for clean layout)
        const factorEntries = Object.entries(factors).filter(([key, factor]) => {
            return factor && factor.name && factor.score !== undefined;
        }).slice(0, 6);
        
        const count = factorEntries.length;

        if (count === 0) {
            console.warn('[SciFiViz] No valid factors to display');
            return;
        }

        console.log('[SciFiViz] Rendering', count, 'factor cards');

        // Ensure orbit has dimensions (force if needed) with inline styles
        // Make orbit container centered and properly sized - compact layout
        orbit.style.cssText = `
            position: relative !important;
            width: 100% !important;
            max-width: 900px !important;
            height: 380px !important;
            margin: 0 auto !important;
            min-height: 380px !important;
            display: block !important;
            visibility: visible !important;
            overflow: visible !important;
            z-index: 5 !important;
        `;
        
        console.log('[SciFiViz] Orbit dimensions set:', {
            width: orbit.offsetWidth,
            height: orbit.offsetHeight
        });
        
        // Double check after a moment
        setTimeout(() => {
            if (orbit.offsetWidth === 0 || orbit.offsetHeight === 0) {
                console.warn('[SciFiViz] Orbit still has no dimensions, forcing again');
                orbit.style.setProperty('width', '800px', 'important');
                orbit.style.setProperty('height', '600px', 'important');
            }
        }, 100);

        // Position cards after a short delay to ensure layout is ready
        // Use requestAnimationFrame to wait for next paint cycle
        requestAnimationFrame(() => {
            setTimeout(() => {
                if (orbit.offsetWidth > 0 && orbit.offsetHeight > 0) {
                    positionFactorCards(orbit, factorEntries);
                } else {
                    // Retry if dimensions not ready
                    const retry = setInterval(() => {
                        if (orbit.offsetWidth > 0 && orbit.offsetHeight > 0) {
                            clearInterval(retry);
                            positionFactorCards(orbit, factorEntries);
                        }
                    }, 100);
                    
                    // Timeout after 2 seconds
                    setTimeout(() => {
                        clearInterval(retry);
                        positionFactorCards(orbit, factorEntries);
                    }, 2000);
                }
            }, 100);
        });
    }

    /**
     * Position factor cards in orbit around the central orb
     */
    function positionFactorCards(orbit, factorEntries) {
        const count = factorEntries.length;
        
        // Get the central orb position to orbit around it
        const orbCore = document.querySelector('.risk-orb-core');
        let centerX, centerY;
        
        if (orbCore && orbit.offsetWidth > 0 && orbit.offsetHeight > 0) {
            // Get orb's position relative to orbit container
            const orbitRect = orbit.getBoundingClientRect();
            const orbRect = orbCore.getBoundingClientRect();
            
            // Calculate center of orb relative to orbit container
            centerX = orbRect.left - orbitRect.left + orbRect.width / 2;
            centerY = orbRect.top - orbitRect.top + orbRect.height / 2;
            
            // Ensure valid coordinates
            if (isNaN(centerX) || isNaN(centerY) || centerX <= 0 || centerY <= 0) {
                console.warn('[SciFiViz] Invalid orb position, using orbit center');
                centerX = orbit.offsetWidth / 2;
                centerY = orbit.offsetHeight / 2;
            }
        } else {
            // Fallback: use orbit center
            centerX = (orbit.offsetWidth || 900) / 2;
            centerY = (orbit.offsetHeight || 380) / 2;
        }
        
        // Balanced radius - not too close, not too far
        // Use a moderate radius for good visual balance
        const radius = 200; // Distance from orb center to card center (balanced spacing)

        console.log('[SciFiViz] Positioning cards:', { 
            centerX, 
            centerY, 
            radius, 
            count,
            orbitWidth: orbit.offsetWidth,
            orbitHeight: orbit.offsetHeight,
            orbFound: !!orbCore
        });

        // Create and position cards
        factorEntries.forEach(([key, factor], index) => {
            const card = createFactorCard(key, factor, index);
            orbit.appendChild(card);

            // Calculate angle for orbital position (evenly spaced around circle)
            const angle = (index / count) * Math.PI * 2 - (Math.PI / 2); // Start at top (12 o'clock)
            // Position card center at orbital radius, then offset by half card dimensions
            const cardCenterX = centerX + Math.cos(angle) * radius;
            const cardCenterY = centerY + Math.sin(angle) * radius;
            const x = cardCenterX - 70; // 70 = half card width (140/2)
            const y = cardCenterY - 80; // 80 = half card height (160/2)

            // Force visibility and positioning with !important via setProperty
            card.style.setProperty('position', 'absolute', 'important');
            card.style.setProperty('left', `${x}px`, 'important');
            card.style.setProperty('top', `${y}px`, 'important');
            card.style.setProperty('display', 'flex', 'important');
            card.style.setProperty('visibility', 'visible', 'important');
            card.style.setProperty('opacity', '1', 'important');
            card.style.setProperty('z-index', '5', 'important');
            card.style.setProperty('width', '140px', 'important');
            card.style.setProperty('height', '160px', 'important');
            
            // Verify card is in DOM and visible
            setTimeout(() => {
                const rect = card.getBoundingClientRect();
                const computed = window.getComputedStyle(card);
                console.log('[SciFiViz] Card verification:', {
                    name: factor.name,
                    position: { x, y },
                    rect: { 
                        width: rect.width, 
                        height: rect.height, 
                        top: rect.top, 
                        left: rect.left,
                        bottom: rect.bottom,
                        right: rect.right
                    },
                    computed: {
                        display: computed.display,
                        visibility: computed.visibility,
                        opacity: computed.opacity,
                        position: computed.position,
                        zIndex: computed.zIndex
                    },
                    inViewport: rect.width > 0 && rect.height > 0 && rect.top < window.innerHeight && rect.bottom > 0
                });
                
                // If card is not visible, try to fix it
                if (rect.width === 0 || rect.height === 0) {
                    console.warn('[SciFiViz] Card has no dimensions, forcing:', factor.name);
                    card.style.setProperty('width', '140px', 'important');
                    card.style.setProperty('height', '160px', 'important');
                    card.style.setProperty('min-width', '140px', 'important');
                    card.style.setProperty('min-height', '160px', 'important');
                }
            }, 100);
        });

        // Draw connection lines AFTER cards are positioned
        // Use multiple attempts to ensure lines are drawn
        const drawLines = () => {
            if (centerX > 0 && centerY > 0 && count > 0) {
                drawConnectionLines(orbit, centerX, centerY, count, radius);
            } else {
                console.warn('[SciFiViz] Cannot draw lines - invalid coordinates:', { centerX, centerY, count });
            }
        };
        
        // Try immediately
        requestAnimationFrame(() => {
            setTimeout(drawLines, 50);
        });
        
        // Also try after a longer delay to ensure layout is stable
        setTimeout(drawLines, 200);
    }

    /**
     * Create a factor card element (match image 2 layout)
     */
    function createFactorCard(key, factor, index) {
        const card = document.createElement('div');
        card.className = 'factor-card';
        card.setAttribute('data-factor', key);

        // Create badge number (sequential index, 01, 02, 03...)
        const badgeNumber = String((index || 0) + 1).padStart(2, '0');

        // Apply critical inline styles immediately to ensure visibility
        card.style.cssText = `
            position: absolute !important;
            width: 140px !important;
            height: 160px !important;
            background: rgba(5, 8, 16, 0.75) !important;
            backdrop-filter: blur(30px) !important;
            -webkit-backdrop-filter: blur(30px) !important;
            border: 2px solid rgba(0, 255, 200, 0.35) !important;
            border-bottom: 5px solid rgba(0, 255, 200, 0.7) !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            justify-content: flex-start !important;
            gap: 0.75rem !important;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), 0 0 40px rgba(0, 255, 200, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
            cursor: pointer !important;
            z-index: 5 !important;
            overflow: visible !important;
            visibility: visible !important;
            opacity: 1 !important;
            box-sizing: border-box !important;
        `;

        card.innerHTML = `
            <div class="factor-badge" style="position: absolute; top: 0.75rem; right: 0.75rem; width: 32px; height: 32px; border: 2px solid rgba(0, 255, 200, 0.6); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; color: rgba(0, 255, 200, 0.9); background: rgba(0, 255, 200, 0.1); box-shadow: 0 0 10px rgba(0, 255, 200, 0.4); z-index: 1;">${badgeNumber}</div>
            <div class="factor-icon" style="display: flex; align-items: center; justify-content: center; width: 100%; margin-top: 0.5rem; margin-bottom: 0.5rem; color: rgba(0, 255, 200, 0.9); filter: drop-shadow(0 0 12px rgba(0, 255, 200, 0.8));">${factor.icon}</div>
            <div class="factor-name" style="font-size: 0.8125rem; font-weight: 600; color: rgba(255, 255, 255, 0.85); text-transform: none; letter-spacing: 0.05em; text-align: center; width: 100%; line-height: 1.4; margin-bottom: auto; padding-top: 0.5rem;">${factor.name}</div>
            <div class="factor-score" style="font-size: 1.875rem; font-weight: 900; color: #00ffc8; text-shadow: 0 0 15px rgba(0, 255, 200, 0.8), 0 0 30px rgba(0, 255, 200, 0.5); align-self: center !important; text-align: center !important; width: 100% !important; margin-top: auto; line-height: 1;">${factor.score}</div>
        `;
        return card;
    }

    /**
     * Draw connection lines from center to cards (visible)
     */
    function drawConnectionLines(orbit, centerX, centerY, count, radius) {
        // Validate inputs
        if (!orbit || !count || count === 0) {
            console.warn('[SciFiViz] Cannot draw lines - invalid inputs:', { orbit: !!orbit, count });
            return;
        }
        
        if (isNaN(centerX) || isNaN(centerY) || centerX <= 0 || centerY <= 0) {
            console.warn('[SciFiViz] Cannot draw lines - invalid coordinates:', { centerX, centerY });
            // Try to recalculate center
            centerX = orbit.offsetWidth / 2 || 450;
            centerY = orbit.offsetHeight / 2 || 190;
        }
        
        // Try to find SVG in orbit container first, then fallback to global
        let svg = orbit.querySelector('#connection-lines') || document.getElementById('connection-lines');
        
        if (!svg) {
            console.warn('[SciFiViz] Connection lines SVG not found, creating one...');
            // Create SVG if it doesn't exist
            svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.id = 'connection-lines';
            svg.className = 'connection-lines';
            orbit.insertBefore(svg, orbit.firstChild); // Insert at beginning so it's behind cards
        }

        // Set SVG dimensions to match orbit container
        const orbitWidth = orbit.offsetWidth || 900;
        const orbitHeight = orbit.offsetHeight || 380;
        svg.setAttribute('width', String(orbitWidth));
        svg.setAttribute('height', String(orbitHeight));
        svg.setAttribute('viewBox', `0 0 ${orbitWidth} ${orbitHeight}`);
        svg.setAttribute('preserveAspectRatio', 'none');
        svg.style.cssText = `
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            pointer-events: none !important;
            z-index: 1 !important;
            opacity: 1 !important;
            display: block !important;
            visibility: visible !important;
        `;

        // Clear existing lines
        svg.innerHTML = '';
        
        console.log('[SciFiViz] Drawing connection lines:', { 
            centerX: centerX.toFixed(1), 
            centerY: centerY.toFixed(1), 
            count, 
            radius,
            orbitWidth,
            orbitHeight,
            svgFound: !!svg,
            svgParent: svg.parentElement?.id || svg.parentElement?.className
        });

        // Draw lines from orb center to each card center
        let linesDrawn = 0;
        for (let i = 0; i < count; i++) {
            const angle = (i / count) * Math.PI * 2 - (Math.PI / 2);
            // Calculate card center position (same as card positioning logic)
            const cardCenterX = centerX + Math.cos(angle) * radius;
            const cardCenterY = centerY + Math.sin(angle) * radius;

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', String(centerX));
            line.setAttribute('y1', String(centerY));
            line.setAttribute('x2', String(cardCenterX));
            line.setAttribute('y2', String(cardCenterY));
            line.setAttribute('stroke', 'rgba(0, 255, 200, 0.6)');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('stroke-dasharray', '5, 3');
            line.setAttribute('stroke-linecap', 'round');
            line.style.cssText = `
                filter: drop-shadow(0 0 4px rgba(0, 255, 200, 0.8)) !important;
                opacity: 1 !important;
            `;
            svg.appendChild(line);
            linesDrawn++;
        }
        
        if (linesDrawn > 0) {
            console.log('[SciFiViz] ✓ Connection lines drawn:', linesDrawn, 'lines from center (', centerX.toFixed(1), ',', centerY.toFixed(1), ')');
        } else {
            console.warn('[SciFiViz] ⚠ No lines drawn!', { count, centerX, centerY, radius });
        }
    }

    /**
     * Update badge and confidence
     */
    function updateBadgeAndConfidence(level, confidence) {
        const badgeEl = document.getElementById('sci-fi-risk-badge');
        const confidenceEl = document.getElementById('sci-fi-confidence');

        if (badgeEl) {
            const badgeText = badgeEl.querySelector('.badge-text');
            if (badgeText) {
                const levelText = level === 'low' ? 'LOW RISK' :
                                 level === 'moderate' ? 'MODERATE RISK' :
                                 'HIGH RISK';
                badgeText.textContent = levelText;
            }
        }

        if (confidenceEl) {
            confidenceEl.textContent = `${confidence}%`;
        }
    }

    // Initialize when DOM is ready
    function startInit() {
        // Wait a bit for other scripts to populate data
        setTimeout(() => {
            initSciFiViz();
        }, 500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startInit);
    } else {
        startInit();
    }

    // Also try after window load (in case data loads later)
    window.addEventListener('load', () => {
        setTimeout(() => {
            const container = document.getElementById('sci-fi-risk-viz');
            if (container) {
                let data = getRiskData();
                if (!data) {
                    console.log('[SciFiViz] No data found, using defaults');
                    data = getDefaultData();
                }
                console.log('[SciFiViz] Re-rendering after window load');
                renderVisualization(data);
            }
        }, 1000);
    });

    // Force render with defaults if nothing happens after 3 seconds
    setTimeout(() => {
        const container = document.getElementById('sci-fi-risk-viz');
        if (container) {
            const orb = container.querySelector('.risk-orb-core');
            const orbit = container.querySelector('#factor-orbit');
            const allCards = container.querySelectorAll('.factor-card');
            const visibleCards = Array.from(allCards).filter(card => {
                const style = window.getComputedStyle(card);
                return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
            });
            
            console.log('[SciFiViz] Visibility check:', {
                containerExists: !!container,
                orbExists: !!orb,
                orbitExists: !!orbit,
                totalCards: allCards.length,
                visibleCards: visibleCards.length,
                orbitDimensions: orbit ? { width: orbit.offsetWidth, height: orbit.offsetHeight } : null
            });
            
            // If orb exists but no cards are visible, force render
            if (orb && visibleCards.length === 0) {
                console.log('[SciFiViz] No visible cards found, force rendering with defaults');
                const data = getDefaultData();
                renderVisualization(data);
                
                // Also try to manually show any existing cards
                allCards.forEach(card => {
                    card.style.setProperty('display', 'flex', 'important');
                    card.style.setProperty('visibility', 'visible', 'important');
                    card.style.setProperty('opacity', '1', 'important');
                });
            }
        }
    }, 3000);
    
    // Additional check: verify component is actually visible in viewport
    setTimeout(() => {
        const container = document.getElementById('sci-fi-risk-viz');
        if (container) {
            const rect = container.getBoundingClientRect();
            console.log('[SciFiViz] Container viewport check:', {
                exists: !!container,
                dimensions: { width: rect.width, height: rect.height },
                position: { top: rect.top, left: rect.left },
                inViewport: rect.width > 0 && rect.height > 0,
                computedDisplay: window.getComputedStyle(container).display,
                computedVisibility: window.getComputedStyle(container).visibility
            });
            
            // If container has no dimensions, force them
            if (rect.width === 0 || rect.height === 0) {
                console.warn('[SciFiViz] Container has no dimensions, forcing...');
                container.style.setProperty('width', '100%', 'important');
                container.style.setProperty('min-height', '700px', 'important');
                container.style.setProperty('display', 'block', 'important');
            }
        }
    }, 4000);

    // Expose for manual updates and debugging
    window.SciFiRiskViz = {
        init: initSciFiViz,
        update: renderVisualization,
        getData: getRiskData,
        debug: function() {
            const container = document.getElementById('sci-fi-risk-viz');
            const orbit = document.getElementById('factor-orbit');
            const orb = container?.querySelector('.risk-orb-core');
            const cards = container?.querySelectorAll('.factor-card') || [];
            
            console.log('[SciFiViz] DEBUG INFO:', {
                container: {
                    exists: !!container,
                    display: container ? window.getComputedStyle(container).display : null,
                    visibility: container ? window.getComputedStyle(container).visibility : null,
                    dimensions: container ? container.getBoundingClientRect() : null
                },
                orbit: {
                    exists: !!orbit,
                    dimensions: orbit ? { width: orbit.offsetWidth, height: orbit.offsetHeight } : null,
                    display: orbit ? window.getComputedStyle(orbit).display : null
                },
                orb: {
                    exists: !!orb,
                    display: orb ? window.getComputedStyle(orb).display : null
                },
                cards: {
                    total: cards.length,
                    visible: Array.from(cards).filter(c => {
                        const s = window.getComputedStyle(c);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    }).length,
                    positions: Array.from(cards).map(c => ({
                        name: c.querySelector('.factor-name')?.textContent,
                        rect: c.getBoundingClientRect(),
                        styles: {
                            display: window.getComputedStyle(c).display,
                            position: window.getComputedStyle(c).position,
                            left: window.getComputedStyle(c).left,
                            top: window.getComputedStyle(c).top
                        }
                    }))
                }
            });
            
            return { container, orbit, orb, cards: Array.from(cards) };
        },
        forceShow: function() {
            const container = document.getElementById('sci-fi-risk-viz');
            if (container) {
                container.style.setProperty('display', 'block', 'important');
                container.style.setProperty('visibility', 'visible', 'important');
                container.style.setProperty('opacity', '1', 'important');
                
                const cards = container.querySelectorAll('.factor-card');
                cards.forEach(card => {
                    card.style.setProperty('display', 'flex', 'important');
                    card.style.setProperty('visibility', 'visible', 'important');
                    card.style.setProperty('opacity', '1', 'important');
                });
                
                console.log('[SciFiViz] Forced visibility for', cards.length, 'cards');
            }
        }
    };

})();

