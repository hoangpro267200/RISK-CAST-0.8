/**
 * ========================================================================
 * SUMMARY v19 ULTRA – RISKCAST
 * VisionOS Edition - 3D Hologram + Parallax + AI Risk Engine Controller
 * ========================================================================
 */

class SummaryV19UltraController {
    constructor() {
        this.formData = null;
        this.riskScore = 0;
        this.riskLevel = 'low';
        this.uiSoundEnabled = false;
        this.soundContext = null;
        this.parallaxEnabled = true;
        this.simulationData = null;
        
        // Initialize audio context (optional)
        this.initAudio();
        
        // Bind methods
        this.handleParallax = this.handleParallax.bind(this);
        this.handleSimulate = this.handleSimulate.bind(this);
    }

    /**
     * Initialize Summary v19 Ultra
     */
    initSummaryV19Ultra() {
        console.log('[SUMMARY v19 ULTRA] Initializing...');
        
        // Get form data from input controller
        this.loadFormData();
        
        // Render all components
        this.renderHologram();
        this.renderSmartRecap();
        this.renderRiskMatrix();
        this.renderSimulation();
        this.renderBenchmark();
        this.renderAISummary();
        this.renderAIRecommendations();
        this.renderSmartTags();
        this.updateRiskMeter();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup parallax
        this.setupParallax();
        
        console.log('[SUMMARY v19 ULTRA] Initialized');
    }

    /**
     * Load form data from input controller or localStorage
     */
    loadFormData() {
        // Try to get from global input controller
        const inputController = window.rcController || window.riskcastInputController;
        if (inputController && inputController.formData) {
            this.formData = inputController.formData;
        } else {
            // Fallback: try localStorage
            const savedData = localStorage.getItem('rc-input-state');
            if (savedData) {
                try {
                    this.formData = JSON.parse(savedData);
                } catch (e) {
                    console.warn('[SUMMARY v19 ULTRA] Failed to parse saved data');
                    this.formData = this.getDefaultFormData();
                }
            } else {
                this.formData = this.getDefaultFormData();
            }
        }
        
        // Calculate risk score
        this.calculateRiskScore();
    }

    /**
     * Get default form data structure
     */
    getDefaultFormData() {
        return {
            tradeLane: '',
            mode: '',
            pol: '',
            pod: '',
            cargoType: '',
            grossWeight: null,
            cargoVolume: null,
            insuranceValue: null,
            cargoSensitivity: 'standard',
            packingType: '',
            modules: {
                weather: false,
                congestion: false,
                geo: false,
                carrier: false,
                network: false
            }
        };
    }

    /**
     * Calculate risk score from form data
     */
    calculateRiskScore() {
        const data = this.formData;
        let score = 0;
        
        // Base score from sensitivity
        const sensitivityMap = {
            'fragile': 30,
            'standard': 15,
            'robust': 5
        };
        score += sensitivityMap[data.cargoSensitivity] || 15;
        
        // Insurance value factor (0-20 points)
        if (data.insuranceValue) {
            const insuranceFactor = Math.min(data.insuranceValue / 100000, 1) * 20;
            score += insuranceFactor;
        }
        
        // Weight factor (0-15 points)
        if (data.grossWeight) {
            const weightFactor = Math.min(data.grossWeight / 50000, 1) * 15;
            score += weightFactor;
        }
        
        // Module factors (0-20 points)
        const moduleCount = Object.values(data.modules || {}).filter(Boolean).length;
        score += (moduleCount / 5) * 20;
        
        // Congestion index (mock, 0-15 points)
        const congestionIndex = Math.random() * 15;
        score += congestionIndex;
        
        // Climate risk (mock, 0-20 points)
        const climateRisk = data.modules?.weather ? Math.random() * 20 : 0;
        score += climateRisk;
        
        // Normalize to 0-100
        this.riskScore = Math.min(Math.max(Math.round(score), 0), 100);
        
        // Determine risk level
        if (this.riskScore < 30) {
            this.riskLevel = 'low';
        } else if (this.riskScore < 60) {
            this.riskLevel = 'medium';
        } else {
            this.riskLevel = 'high';
        }
    }

    /**
     * Initialize audio context (optional)
     */
    initAudio() {
        try {
            this.soundContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('[SUMMARY v19 ULTRA] Audio not supported');
        }
    }

    /**
     * Play UI sound (optional)
     */
    playSound(type = 'tap') {
        if (!this.uiSoundEnabled || !this.soundContext) return;
        
        // Try to load sound file
        const soundPath = `/static/sounds/ui_${type}.mp3`;
        // Note: In production, you would load and play the actual sound file
        // For now, we'll just log it
        console.log('[SUMMARY v19 ULTRA] Sound would play:', soundPath);
    }

    /**
     * Render 3D Hologram
     */
    renderHologram() {
        const container = document.getElementById('rc-hologram-container');
        if (!container) return;
        
        // Set risk level attribute for color mapping
        container.closest('.rc-holo-wrapper').setAttribute('data-risk-level', this.riskLevel);
        
        // Update glow pulse based on risk score
        const glow = container.querySelector('.rc-holo-glow');
        if (glow) {
            const pulseIntensity = this.riskScore / 100;
            glow.style.opacity = pulseIntensity * 0.6;
        }
    }

    /**
     * Render Smart Shipment Recap
     */
    renderSmartRecap() {
        const data = this.formData;
        
        // Helper to format values
        const format = (value, fallback = '—') => {
            if (value === null || value === undefined || value === '') return fallback;
            return value;
        };
        
        // Update all recap fields
        this.updateElement('rc-recap-route', 
            data.pol && data.pod ? `${format(data.pol)} → ${format(data.pod)}` : '—');
        this.updateElement('rc-recap-mode', format(data.mode || data.transportMode));
        this.updateElement('rc-recap-container', format(data.containerType));
        this.updateElement('rc-recap-transit', format(data.transitType || 'Standard'));
        this.updateElement('rc-recap-cargo', format(data.cargoType));
        this.updateElement('rc-recap-packing', format(data.packingType));
        this.updateElement('rc-recap-weight', 
            data.grossWeight ? `${this.formatNumber(data.grossWeight)} kg` : '—');
        this.updateElement('rc-recap-volume', 
            data.cargoVolume ? `${this.formatNumber(data.cargoVolume)} m³` : '—');
        this.updateElement('rc-recap-insurance', 
            data.insuranceValue ? `$${this.formatNumber(data.insuranceValue)}` : '—');
        this.updateElement('rc-recap-sensitivity', 
            this.formatSensitivity(data.cargoSensitivity));
        
        // Modules enabled
        const modulesList = Object.entries(data.modules || {})
            .filter(([_, enabled]) => enabled)
            .map(([key, _]) => this.formatModuleName(key))
            .join(', ');
        this.updateElement('rc-recap-modules', modulesList || 'None');
        
        // Climate info (mock)
        const climateInfo = data.modules?.weather ? 'Active monitoring' : 'Not enabled';
        this.updateElement('rc-recap-climate', climateInfo);
        
        // Congestion index (mock)
        const congestionIndex = (Math.random() * 100).toFixed(1);
        this.updateElement('rc-recap-congestion', `${congestionIndex}%`);
        
        // Update editable buttons with current recap values after a short delay
        setTimeout(() => {
            if (typeof window.updateEditableButtonsFromRecap === 'function') {
                window.updateEditableButtonsFromRecap();
            }
            // Also sync RC_STATE
            if (typeof window.syncRCStateFromInputController === 'function') {
                window.syncRCStateFromInputController();
            }
        }, 100);
    }

    /**
     * Render Risk Matrix 5x5
     */
    renderRiskMatrix() {
        const container = document.querySelector('.rc-matrix-grid');
        if (!container) return;
        
        // Clear existing cells
        container.innerHTML = '';
        
        // Create 5x5 grid
        for (let severity = 4; severity >= 0; severity--) {
            for (let probability = 0; probability < 5; probability++) {
                const cell = document.createElement('div');
                cell.className = 'rc-matrix-cell';
                cell.setAttribute('data-severity', severity);
                cell.setAttribute('data-probability', probability);
                
                // Check if this is the active cell
                const activeSeverity = this.getSeverityIndex();
                const activeProbability = this.getProbabilityIndex();
                
                if (severity === activeSeverity && probability === activeProbability) {
                    cell.classList.add('active');
                    cell.setAttribute('title', `Current Risk Position: Severity ${severity + 1}, Probability ${probability + 1}`);
                }
                
                container.appendChild(cell);
            }
        }
    }

    /**
     * Get severity index from risk score
     */
    getSeverityIndex() {
        // Map risk score to severity (0-4)
        if (this.riskScore < 20) return 0; // Minimal
        if (this.riskScore < 40) return 1; // Low
        if (this.riskScore < 60) return 2; // Medium
        if (this.riskScore < 80) return 3; // High
        return 4; // Critical
    }

    /**
     * Get probability index from sensitivity and other factors
     */
    getProbabilityIndex() {
        const data = this.formData;
        let prob = 0;
        
        // Base on sensitivity
        if (data.cargoSensitivity === 'fragile') prob += 2;
        else if (data.cargoSensitivity === 'standard') prob += 1;
        
        // Module count
        const moduleCount = Object.values(data.modules || {}).filter(Boolean).length;
        prob += Math.min(moduleCount, 2);
        
        // Normalize to 0-4
        return Math.min(Math.max(prob, 0), 4);
    }

    /**
     * Render Risk Simulation (7 days)
     */
    renderSimulation() {
        // Initial state - empty
        const line = document.getElementById('rc-simulation-line');
        if (line) {
            line.style.opacity = '0';
        }
    }

    /**
     * Handle simulate button click
     */
    handleSimulate() {
        this.playSound('tap');
        
        // Generate simulation data
        const baseScore = this.riskScore;
        this.simulationData = [];
        
        for (let day = 0; day < 7; day++) {
            // Add some random variation (±10 points)
            const variation = (Math.random() - 0.5) * 20;
            const dayScore = Math.min(Math.max(baseScore + variation, 0), 100);
            this.simulationData.push(dayScore);
        }
        
        // Render chart
        this.renderSimulationChart();
        
        // Update description
        const trend = this.calculateTrend();
        const description = `Nếu điều kiện hiện tại giữ nguyên, risk có xu hướng ${trend} trong 7 ngày tới.`;
        this.updateElement('rc-simulation-description', description);
    }

    /**
     * Render simulation chart
     */
    renderSimulationChart() {
        const line = document.getElementById('rc-simulation-line');
        if (!line || !this.simulationData) return;
        
        // Calculate points (invert Y because SVG Y increases downward)
        const width = 300;
        const height = 150;
        const padding = 20;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        
        const points = this.simulationData.map((score, index) => {
            const x = padding + (index / 6) * chartWidth;
            const y = padding + chartHeight - (score / 100) * chartHeight;
            return `${x},${y}`;
        }).join(' ');
        
        line.setAttribute('points', points);
        
        // Animate
        line.style.opacity = '0';
        line.style.strokeDasharray = '1000';
        line.style.strokeDashoffset = '1000';
        
        requestAnimationFrame(() => {
            line.style.transition = 'opacity 0.5s ease-out, stroke-dashoffset 2s ease-out';
            line.style.opacity = '1';
            line.style.strokeDashoffset = '0';
        });
    }

    /**
     * Calculate trend from simulation data
     */
    calculateTrend() {
        if (!this.simulationData || this.simulationData.length < 2) return 'ổn định';
        
        const first = this.simulationData[0];
        const last = this.simulationData[this.simulationData.length - 1];
        const diff = last - first;
        
        if (diff > 5) return 'tăng';
        if (diff < -5) return 'giảm';
        return 'ổn định';
    }

    /**
     * Render Benchmark vs Industry
     */
    renderBenchmark() {
        const currentScore = this.riskScore;
        const laneAvg = 42; // Mock
        const laneTop10 = 25; // Mock
        
        // Update bars
        this.updateElement('rc-benchmark-current', null, (el) => {
            el.style.width = `${currentScore}%`;
        });
        this.updateElement('rc-benchmark-current-value', currentScore);
        
        // Calculate comparison
        const diff = laneAvg - currentScore;
        let comparison = '';
        
        if (diff > 0) {
            const percent = ((diff / laneAvg) * 100).toFixed(1);
            comparison = `Bạn đang an toàn hơn ${percent}% so với trung bình tuyến này.`;
        } else if (diff < 0) {
            const percent = ((Math.abs(diff) / laneAvg) * 100).toFixed(1);
            comparison = `Risk của bạn cao hơn ${percent}% so với trung bình tuyến này.`;
        } else {
            comparison = 'Risk của bạn bằng với trung bình tuyến này.';
        }
        
        this.updateElement('rc-benchmark-comparison', `<p>${comparison}</p>`);
    }

    /**
     * Render AI Summary
     */
    renderAISummary() {
        const data = this.formData;
        const summary = this.buildAISummaryText(data);
        
        this.updateElement('rc-ai-summary-text', `<p>${summary}</p>`);
    }

    /**
     * Build AI Summary text
     */
    buildAISummaryText(data) {
        const parts = [];
        
        // Transport mode and route
        if (data.mode || data.transportMode) {
            const mode = this.formatTransportMode(data.mode || data.transportMode);
            const route = data.pol && data.pod ? `${data.pol} → ${data.pod}` : 'chưa xác định';
            parts.push(`Shipment sử dụng ${mode} từ ${route}`);
        } else {
            parts.push('Shipment chưa được cấu hình đầy đủ');
        }
        
        // Weight and insurance
        if (data.grossWeight || data.insuranceValue) {
            const weight = data.grossWeight ? `${this.formatNumber(data.grossWeight)} kg` : 'chưa xác định';
            const insurance = data.insuranceValue ? `$${this.formatNumber(data.insuranceValue)}` : 'chưa xác định';
            parts.push(`trọng lượng ${weight}, bảo hiểm ${insurance}`);
        }
        
        // Sensitivity and modules
        const sensitivity = this.formatSensitivity(data.cargoSensitivity);
        const modulesList = Object.entries(data.modules || {})
            .filter(([_, enabled]) => enabled)
            .map(([key, _]) => this.formatModuleName(key))
            .join(', ') || 'không có';
        parts.push(`Hàng hóa ở mức ${sensitivity}, các module kích hoạt: ${modulesList}`);
        
        // Risk level
        const riskLabel = this.getRiskLevelLabel();
        parts.push(`AI đánh giá risk level hiện tại ${this.riskScore}/100 – ${riskLabel}`);
        
        return parts.join('. ') + '.';
    }

    /**
     * Render AI Recommendations
     */
    renderAIRecommendations() {
        const recommendations = this.generateRecommendations();
        const container = document.querySelector('.rc-recommendations-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.className = 'rc-recommendation-item';
            li.textContent = rec;
            container.appendChild(li);
        });
    }

    /**
     * Generate AI Recommendations
     */
    generateRecommendations() {
        const data = this.formData;
        const recommendations = [];
        
        // Weather risk
        if (data.modules?.weather) {
            if (this.riskScore > 60) {
                recommendations.push('Cảnh báo: Rủi ro thời tiết cao. Nên theo dõi sát sao dự báo và có kế hoạch dự phòng.');
            } else {
                recommendations.push('Thời tiết hiện tại ổn định. Tiếp tục theo dõi để đảm bảo an toàn.');
            }
        }
        
        // Congestion risk
        if (this.riskScore > 50) {
            recommendations.push('Chỉ số tắc nghẽn cảng đang ở mức cao. Cân nhắc điều chỉnh lịch trình hoặc chọn cảng thay thế.');
        }
        
        // Sensitivity
        if (data.cargoSensitivity === 'fragile') {
            recommendations.push('Hàng hóa dễ vỡ cần đóng gói chuyên nghiệp và xử lý cẩn thận. Đề xuất sử dụng container có kiểm soát nhiệt độ.');
        }
        
        // Insurance value
        if (data.insuranceValue && data.insuranceValue > 100000) {
            recommendations.push('Giá trị bảo hiểm cao. Đảm bảo tài liệu và chứng từ đầy đủ, xem xét bảo hiểm bổ sung nếu cần.');
        }
        
        // Module optimization
        const moduleCount = Object.values(data.modules || {}).filter(Boolean).length;
        if (moduleCount < 3 && this.riskScore > 40) {
            recommendations.push('Kích hoạt thêm các module phân tích để có đánh giá risk chính xác hơn.');
        }
        
        // Ensure at least 3 recommendations
        while (recommendations.length < 3) {
            recommendations.push('Tiếp tục cập nhật thông tin shipment để nhận được đánh giá risk chính xác nhất.');
        }
        
        return recommendations.slice(0, 4); // Max 4 recommendations
    }

    /**
     * Render Smart Risk Tags
     */
    renderSmartTags() {
        const tags = this.generateSmartTags();
        const container = document.getElementById('rc-smart-risk-tags');
        if (!container) return;
        
        container.innerHTML = '';
        
        tags.forEach(tag => {
            const span = document.createElement('span');
            span.className = 'rc-summary-ultra-tag';
            span.textContent = tag;
            container.appendChild(span);
        });
    }

    /**
     * Generate Smart Risk Tags
     */
    generateSmartTags() {
        const data = this.formData;
        const tags = [];
        
        // Fragile cargo
        if (data.cargoSensitivity === 'fragile') {
            tags.push('Fragile Cargo');
        }
        
        // High value shipment
        if (data.insuranceValue && data.insuranceValue > 100000) {
            tags.push('High Value Shipment');
        }
        
        // Transpacific route
        if (data.pol && data.pod) {
            const pol = (data.pol || '').toUpperCase();
            const pod = (data.pod || '').toUpperCase();
            if ((pol.includes('VN') || pol.includes('CN') || pol.includes('JP')) && 
                (pod.includes('US') || pod.includes('CA'))) {
                tags.push('Transpacific Route');
            }
        }
        
        // Weather sensitive
        if (data.modules?.weather && this.riskScore > 50) {
            tags.push('Weather Sensitive');
        }
        
        // Port congestion
        const congestionIndex = Math.random() * 100;
        if (congestionIndex >= 70) {
            tags.push('Port Congestion Risk');
        }
        
        return tags;
    }

    /**
     * Update Risk Meter
     */
    updateRiskMeter() {
        // Update score
        this.updateElement('rc-risk-meter-score', this.riskScore);
        
        // Update level
        const levelLabel = this.getRiskLevelLabel();
        this.updateElement('rc-risk-meter-level', levelLabel);
        
        // Update needle position
        const needle = document.getElementById('rc-risk-meter-needle');
        if (needle) {
            // 210 degree arc: -105 to 105 degrees
            // Map 0-100 to -105 to 105
            const angle = -105 + (this.riskScore / 100) * 210;
            needle.setAttribute('transform', `rotate(${angle} 150 150)`);
        }
        
        // Update trend sparkline (mock data)
        this.updateTrendSparkline();
    }

    /**
     * Update trend sparkline
     */
    updateTrendSparkline() {
        const line = document.getElementById('rc-trend-line');
        if (!line) return;
        
        // Generate mock trend data (slight variation)
        const points = [];
        const baseY = 20 - (this.riskScore / 100) * 12;
        
        for (let i = 0; i < 6; i++) {
            const x = (i / 5) * 100;
            const variation = (Math.random() - 0.5) * 4;
            const y = baseY + variation;
            points.push(`${x},${y}`);
        }
        
        line.setAttribute('points', points.join(' '));
    }

    /**
     * Setup Parallax Effect
     */
    setupParallax() {
        const deck = document.getElementById('rc-hologram-deck');
        if (!deck) return;
        
        deck.addEventListener('mousemove', this.handleParallax);
        deck.addEventListener('mouseleave', () => {
            deck.style.transform = '';
        });
    }

    /**
     * Handle parallax mouse move
     */
    handleParallax(e) {
        if (!this.parallaxEnabled) return;
        
        const deck = e.currentTarget;
        const rect = deck.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = ((y - centerY) / centerY) * -10; // Max 10 degrees
        const rotateY = ((x - centerX) / centerX) * 10;
        const translateZ = 20;
        
        deck.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(${translateZ}px)`;
    }

    /**
     * Setup Event Listeners
     */
    setupEventListeners() {
        // UI Sound toggle
        const soundToggle = document.getElementById('rc-ui-sound-toggle');
        if (soundToggle) {
            soundToggle.addEventListener('click', () => {
                this.uiSoundEnabled = !this.uiSoundEnabled;
                const icon = soundToggle.querySelector('i');
                const span = soundToggle.querySelector('span');
                
                if (this.uiSoundEnabled) {
                    icon.setAttribute('data-lucide', 'volume-2');
                    span.textContent = 'Sound: On';
                } else {
                    icon.setAttribute('data-lucide', 'volume-x');
                    span.textContent = 'Sound: Off';
                }
                
                // Reinitialize lucide icons
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            });
        }
        
        // Simulate button
        const simulateBtn = document.getElementById('rc-btn-simulate');
        if (simulateBtn) {
            simulateBtn.addEventListener('click', this.handleSimulate);
        }
    }

    /**
     * Helper: Update element text content
     */
    updateElement(id, text, callback = null) {
        const el = document.getElementById(id);
        if (!el) return;
        
        if (callback) {
            callback(el);
        } else if (text !== null) {
            // Check if element contains editable button - preserve it
            const editableBtn = el.querySelector('.rc-editable-field');
            if (editableBtn) {
                // Update text in editable button
                let textSpan = editableBtn.querySelector('.rc-editable-field-text');
                if (textSpan) {
                    textSpan.textContent = text;
                } else {
                    // Create text span if doesn't exist
                    textSpan = document.createElement('span');
                    textSpan.className = 'rc-editable-field-text';
                    textSpan.textContent = text;
                    editableBtn.insertBefore(textSpan, editableBtn.querySelector('.rc-edit-pill'));
                }
            } else {
                // No editable button, update text directly
                el.textContent = text;
            }
        }
    }

    /**
     * Helper: Format number
     */
    formatNumber(num) {
        if (typeof num !== 'number') return num;
        return new Intl.NumberFormat('en-US').format(num);
    }

    /**
     * Helper: Format sensitivity
     */
    formatSensitivity(sensitivity) {
        const map = {
            'fragile': 'Dễ vỡ',
            'standard': 'Tiêu chuẩn',
            'robust': 'Bền chắc'
        };
        return map[sensitivity] || sensitivity;
    }

    /**
     * Helper: Format module name
     */
    formatModuleName(key) {
        const map = {
            'weather': 'Weather',
            'congestion': 'Congestion',
            'geo': 'Geopolitical',
            'carrier': 'Carrier',
            'network': 'Network'
        };
        return map[key] || key;
    }

    /**
     * Helper: Format transport mode
     */
    formatTransportMode(mode) {
        const map = {
            'sea': 'vận tải biển',
            'air': 'vận tải hàng không',
            'road': 'vận tải đường bộ',
            'rail': 'vận tải đường sắt'
        };
        return map[mode] || mode;
    }

    /**
     * Helper: Get risk level label
     */
    getRiskLevelLabel() {
        const map = {
            'low': 'Low Risk',
            'medium': 'Medium Risk',
            'high': 'High Risk'
        };
        return map[this.riskLevel] || 'Unknown';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the summary section
    const summarySection = document.getElementById('rc-section-summary');
    if (summarySection) {
        window.summaryV19Ultra = new SummaryV19UltraController();
        window.summaryV19Ultra.initSummaryV19Ultra();
        
        // Watch for form data changes
        const inputController = window.rcController || window.riskcastInputController;
        if (inputController) {
            // Re-initialize when form data changes (debounced)
            let updateTimeout;
            
            // Function to update summary
            const updateSummary = () => {
                if (window.summaryV19Ultra) {
                    window.summaryV19Ultra.loadFormData();
                    window.summaryV19Ultra.renderSmartRecap();
                    window.summaryV19Ultra.calculateRiskScore();
                    window.summaryV19Ultra.updateRiskMeter();
                    window.summaryV19Ultra.renderHologram();
                    window.summaryV19Ultra.renderRiskMatrix();
                    window.summaryV19Ultra.renderAISummary();
                    window.summaryV19Ultra.renderAIRecommendations();
                    window.summaryV19Ultra.renderBenchmark();
                    window.summaryV19Ultra.renderSmartTags();
                    
                    // Trigger editable summary update
                    if (typeof window.updateEditableButtonsFromRecap === 'function') {
                        setTimeout(() => {
                            window.updateEditableButtonsFromRecap();
                        }, 100);
                    }
                    
                    // Dispatch event for editable summary
                    document.dispatchEvent(new CustomEvent('rc-summary-updated'));
                }
            };
            
            // Listen to form input changes
            const form = document.querySelector('form') || document.querySelector('.rc-content');
            if (form) {
                form.addEventListener('input', () => {
                    clearTimeout(updateTimeout);
                    updateTimeout = setTimeout(updateSummary, 300);
                });
                
                form.addEventListener('change', () => {
                    clearTimeout(updateTimeout);
                    updateTimeout = setTimeout(updateSummary, 300);
                });
            }
            
            // Also listen to custom events if input controller emits them
            document.addEventListener('rc-form-updated', () => {
                clearTimeout(updateTimeout);
                updateTimeout = setTimeout(updateSummary, 300);
            });
        }
    }
});

