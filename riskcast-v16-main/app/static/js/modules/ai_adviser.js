
class AIAdviserPanel {
    constructor() {
        this.panel = null;
        this.sidebar = null;
        this.isOpen = false;
        this.streamingHandler = null;
        this.currentStreamingMessage = null;
        this.init();
    }

    /**
     * Initialize panel
     */
    init() {
        // Check if sidebar exists (new layout)
        this.sidebar = document.getElementById('results-ai-chat');
        if (!this.sidebar && !document.getElementById('ai-panel')) {
            this.createPanel();
        }

        if (this.sidebar) {
            this.panel = this.sidebar;
            if (typeof StreamingHandler !== 'undefined') {
                this.streamingHandler = new StreamingHandler('ai-adviser-output');
            } else {
                console.warn('StreamingHandler not available. Make sure streaming.js is loaded before ai_adviser.js');
            }
        } else {
            this.panel = document.getElementById('ai-panel');
            if (typeof StreamingHandler !== 'undefined') {
                this.streamingHandler = new StreamingHandler('ai-messages');
            } else {
                console.warn('StreamingHandler not available. Make sure streaming.js is loaded before ai_adviser.js');
            }
        }

        // Bind events
        this.bindEvents();
    }

    /**
     * Create panel HTML structure
     */
    createPanel() {
        const panelHTML = `
            <div id="ai-panel" class="ai-panel">
                <div class="ai-panel-header">
                    <div class="ai-panel-title">AI Adviser</div>
                    <button class="ai-panel-close" id="ai-panel-close">✕</button>
                </div>
                <div class="ai-messages" id="ai-messages"></div>
                <div class="ai-input-area">
                    <div class="ai-input-wrapper">
                        <textarea 
                            id="ai-input" 
                            class="ai-input" 
                            placeholder="Ask RISKCAST AI anything..."
                            rows="1"
                        ></textarea>
                        <button id="ai-send-button" class="ai-send-button">➤</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', panelHTML);
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Toggle button (mobile)
        const toggleBtn = document.getElementById('ai-chat-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.openSidebar());
        }
        const oldToggleBtn = document.getElementById('ai-panel-toggle');
        if (oldToggleBtn) {
            oldToggleBtn.addEventListener('click', () => this.toggle());
        }

        // Close button (for sidebar)
        const closeBtn = document.getElementById('ai-chat-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeSidebar());
        }
        const oldCloseBtn = document.getElementById('ai-panel-close');
        if (oldCloseBtn) {
            oldCloseBtn.addEventListener('click', () => this.close());
        }

        // Send button (sidebar)
        const sendBtn = document.getElementById('ai-chat-send');
        const input = document.getElementById('ai-chat-input');
        const oldSendBtn = document.getElementById('ai-send-button');
        const oldInput = document.getElementById('ai-input');

        const activeSendBtn = sendBtn || oldSendBtn;
        const activeInput = input || oldInput;

        if (activeSendBtn && activeInput) {
            activeSendBtn.addEventListener('click', () => this.sendMessage());
            
            // Enter to send (Shift+Enter for new line)
            activeInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Auto-resize textarea
            activeInput.addEventListener('input', () => {
                activeInput.style.height = 'auto';
                activeInput.style.height = Math.min(activeInput.scrollHeight, 120) + 'px';
            });
        }
    }

    /**
     * Close sidebar (mobile)
     */
    closeSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.remove('active');
        }
    }

    /**
     * Open sidebar (mobile)
     */
    openSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.add('active');
        }
    }

    /**
     * Toggle panel open/close
     */
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    /**
     * Open panel
     */
    open() {
        if (this.panel) {
            this.panel.classList.add('open');
            this.isOpen = true;
            
            // Focus input
            const input = document.getElementById('ai-input');
            if (input) {
                setTimeout(() => input.focus(), 300);
            }
        }
    }

    /**
     * Close panel
     */
    close() {
        if (this.panel) {
            this.panel.classList.remove('open');
            this.isOpen = false;
        }
    }

    /**
     * Append message bubble (ChatGPT style)
     */
    appendMessage(role, text) {
        const output = document.getElementById('ai-adviser-output') || 
                      document.getElementById('ai-messages');
        if (!output) return;

        const box = document.createElement('div');
        box.className = `ai-message ${role}`;
        box.textContent = text;
        output.appendChild(box);
        
        // Auto scroll
        output.scrollTop = output.scrollHeight;
        
        return box;
    }

    /**
     * Send message to AI
     */
    async sendMessage() {
        const input = document.getElementById('ai-chat-input') || 
                     document.getElementById('ai-input');
        const sendBtn = document.getElementById('ai-chat-send') || 
                       document.getElementById('ai-send-button');
        
        if (!input || !sendBtn) return;

        const message = input.value.trim();
        if (!message) return;

        // Clear input
        input.value = '';
        input.style.height = 'auto';

        // Disable send button
        sendBtn.disabled = true;

        // Show user message
        this.appendMessage('user', message);

        // Show loading indicator
        const loadingBox = this.appendMessage('ai', '...');
        loadingBox.innerHTML = '<div class="ai-loading"><div class="ai-loading-dot"></div><div class="ai-loading-dot"></div><div class="ai-loading-dot"></div></div>';

        try {
            // Create streaming message box
            this.currentStreamingMessage = this.appendMessage('ai', '');
            this.currentStreamingMessage.textContent = '';

            // Stream response
            await this.streamFromAPI('/api/ai/stream', {
                prompt: message,
                context: this.getContext()
            });
        } catch (error) {
            console.error('Error sending message:', error);
            if (this.currentStreamingMessage) {
                this.currentStreamingMessage.textContent = 'Sorry, I encountered an error. Please try again.';
            } else {
                this.appendMessage('ai', 'Sorry, I encountered an error. Please try again.');
            }
        } finally {
            // Remove loading
            if (loadingBox && loadingBox.parentNode) {
                loadingBox.remove();
            }
            sendBtn.disabled = false;
            this.currentStreamingMessage = null;
        }
    }

    /**
     * Stream from API and append tokens
     */
    async streamFromAPI(endpoint, payload) {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        const output = document.getElementById('ai-adviser-output') || 
                      document.getElementById('ai-messages');

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    
                    if (data === '[DONE]') {
                        return;
                    }

                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.text && this.currentStreamingMessage) {
                            this.currentStreamingMessage.textContent += parsed.text;
                            // Auto scroll
                            if (output) {
                                output.scrollTop = output.scrollHeight;
                            }
                        }
                    } catch (e) {
                        // Skip invalid JSON
                    }
                }
            }
        }
    }

    /**
     * Get context for AI (current shipment data, etc.)
     */
    getContext() {
        // Try to get current shipment data from page
        const context = {};

        // Check if we're on results page
        const riskData = window.riskData || {};
        if (Object.keys(riskData).length > 0) {
            context.shipment_data = riskData;
        }

        return context;
    }

    /**
     * Ask AI a specific question (programmatic)
     */
    async ask(question, context = {}) {
        if (!this.isOpen) {
            this.open();
        }

        // Wait for panel to open
        await new Promise(resolve => setTimeout(resolve, 400));

        // Set input and send
        const input = document.getElementById('ai-input');
        if (input) {
            input.value = question;
            this.sendMessage();
        }
    }

    /**
     * Analyze current shipment
     */
    async analyzeShipment(shipmentData) {
        if (!this.isOpen) {
            this.open();
        }

        this.streamingHandler.showLoading();

        try {
            const response = await fetch('/api/ai/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    shipment_data: shipmentData
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                // Display insights
                this.displayInsights(data);
            } else {
                throw new Error(data.message || 'Analysis failed');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.streamingHandler.appendText('Error analyzing shipment: ' + error.message);
        } finally {
            this.streamingHandler.hideLoading();
        }
    }

    /**
     * Display analysis insights
     */
    displayInsights(data) {
        const insights = data.insights || {};
        const summary = data.summary || '';

        // Show summary
        if (summary) {
            this.streamingHandler.appendText(`**Executive Summary:**\n\n${summary}`);
        }

        // Show AI analysis
        if (insights.ai_analysis) {
            this.streamingHandler.appendText(`**AI Analysis:**\n\n${insights.ai_analysis}`);
        }

        // Show key metrics
        const metrics = `
**Key Metrics:**
- Overall Risk: ${insights.overall_risk?.toFixed(1)}/100 (${insights.risk_level})
- Expected Loss: $${insights.expected_loss?.toFixed(2)}
- Reliability: ${insights.reliability?.toFixed(1)}%
        `.trim();

        this.streamingHandler.appendText(metrics);
    }
}

// Initialize on page load
let aiAdviser = null;

document.addEventListener('DOMContentLoaded', () => {
    aiAdviser = new AIAdviserPanel();
    
    // Make globally available
    window.aiAdviser = aiAdviser;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIAdviserPanel;
}

// ==================== AI POPUP CHAT (Floating Button) ====================

// Open/Close Popup
document.addEventListener('DOMContentLoaded', () => {
    const botButton = document.getElementById('aiBotButton');
    const popup = document.getElementById('aiChatPopup');
    const closeBtn = document.getElementById('aiPopupClose');
    
    if (botButton && popup) {
        botButton.onclick = () => {
            popup.classList.remove('hidden');
        };
    }
    
    if (closeBtn && popup) {
        closeBtn.onclick = () => {
            popup.classList.add('hidden');
        };
    }
});

// Append message to popup
function appendPopupMessage(role, text) {
    const messagesContainer = document.getElementById('aiPopupMessages');
    if (!messagesContainer) return;
    
    const box = document.createElement('div');
    box.className = 'ai-message ' + role;
    box.innerText = text;
    messagesContainer.appendChild(box);
    box.scrollIntoView({ behavior: 'smooth', block: 'end' });
    
    return box;
}

// Send message from popup
async function sendPopupMessage() {
    const input = document.getElementById('aiPopupInput');
    const sendBtn = document.getElementById('aiPopupSend');
    
    if (!input || !sendBtn) return;
    
    const q = input.value.trim();
    if (!q) return;
    
    // Show user message
    appendPopupMessage('user', q);
    input.value = '';
    
    // Show loading message
    const loadingMsg = appendPopupMessage('ai', 'Đang xử lý...');
    
    // Disable send button
    sendBtn.disabled = true;
    
    try {
        const res = await fetch('/api/ai/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: q })
        });
        
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        
        // Remove loading message
        loadingMsg.remove();
        
        // Create new AI message for streaming
        const aiMsg = appendPopupMessage('ai', '');
        let full = '';
        
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (!line.trim()) continue;
                
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    
                    if (data === '[DONE]') {
                        return;
                    }
                    
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.text) {
                            full += parsed.text;
                            aiMsg.innerText = full;
                            aiMsg.scrollIntoView({ behavior: 'smooth', block: 'end' });
                        }
                    } catch (e) {
                        // If not JSON, treat as plain text
                        full += data;
                        aiMsg.innerText = full;
                        aiMsg.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                } else {
                    // Plain text streaming
                    full += line;
                    aiMsg.innerText = full;
                    aiMsg.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            }
        }
    } catch (e) {
        console.error('Popup chat error:', e);
        loadingMsg.remove();
        appendPopupMessage('ai', 'Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại.');
    } finally {
        sendBtn.disabled = false;
    }
}

// Bind send button and Enter key
document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('aiPopupSend');
    const input = document.getElementById('aiPopupInput');
    
    if (sendBtn) {
        sendBtn.onclick = sendPopupMessage;
    }
    
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendPopupMessage();
            }
        });
    }
});

// ==================== CLIMATE DATA REAL-TIME UPDATER ====================
document.addEventListener("DOMContentLoaded", function () {
    const monthInput = document.getElementById("shipment-month");
    const climateSection = document.getElementById("climate-section");
    
    if (!monthInput || !climateSection) {
        console.log('⚠️ Climate data updater: monthInput or climateSection not found');
        return;
    }

    function updateClimateData() {
        const val = monthInput.value; // "2025-11"
        if (!val) return;

        // Load from local JSON immediately (no API call, no loading)
        if (!window.CLIMATE_DATA_2025) {
            console.warn('⚠️ CLIMATE_DATA_2025 not loaded yet, retrying...');
            setTimeout(updateClimateData, 100);
            return;
        }

        const monthIdx = parseInt(val.split("-")[1]) - 1;
        if (monthIdx < 0 || monthIdx > 11) {
            console.warn('⚠️ Invalid month index:', monthIdx);
            return;
        }

        const data = window.CLIMATE_DATA_2025.climate_data_2025.months[monthIdx];
        if (!data) {
            console.warn('⚠️ No climate data for month index:', monthIdx);
            return;
        }

        console.log('✅ Climate data loaded from local JSON:', data);

        // Cập nhật từng chỉ số - Format chuẩn quốc tế
        const ensoEl = document.getElementById("enso-value");
        if (ensoEl) {
            // Format chuẩn quốc tế: "La Niña Phase (ONI: -0.6°C)" hoặc "El Niño Phase (ONI: +1.2°C)"
            const oniSign = data.oni >= 0 ? '+' : '';
            const ensoPhase = data.enso === 'La Niña' ? 'La Niña Phase' : 
                             data.enso === 'El Niño' ? 'El Niño Phase' : 'Neutral Phase';
            ensoEl.textContent = `${ensoPhase} (ONI: ${oniSign}${data.oni}°C)`;
        }

        const stormEl = document.getElementById("storm-value");
        if (stormEl) {
            stormEl.textContent = `${data.storms} cơn bão dự kiến`;
        }

        const sstEl = document.getElementById("sst-value");
        if (sstEl) {
            sstEl.textContent = `${data.sst > 0 ? "+" : ""}${data.sst}°C`;
        }

        // Điểm áp lực khí hậu - AUTO CALCULATE & LOCK SLIDER
        const stress = data.stress;
        const stressSlider = document.getElementById("climate-stress-slider");
        const stressValue = document.getElementById("climate-stress-value");
        const stressBadge = document.getElementById("climate-stress-badge");

        if (stressSlider) {
            stressSlider.value = stress;
            stressSlider.disabled = true; // Lock slider - auto calculated
            stressSlider.style.opacity = '0.7';
            stressSlider.style.cursor = 'not-allowed';
        }

        if (stressValue) {
            stressValue.textContent = stress.toFixed(1);
        }

        if (stressBadge) {
            stressBadge.className = 
                stress >= 8 ? "badge critical" : 
                stress >= 6 ? "badge warning" : "badge good";
            stressBadge.textContent = 
                stress >= 8 ? "Critical" : stress >= 6 ? "Cao" : "Thấp";
        }

        // AUTO-FILL RELATED CLIMATE SLIDERS (Locked)
        const portClimateStress = document.getElementById("port_climate_stress");
        if (portClimateStress) {
            // Port stress = climate stress * 0.8 (slightly lower than overall)
            const portStress = Math.min(10, stress * 0.8);
            portClimateStress.value = portStress.toFixed(1);
            portClimateStress.disabled = true; // Lock
            portClimateStress.style.opacity = '0.7';
            portClimateStress.style.cursor = 'not-allowed';
            const portStressDisplay = document.getElementById("port_climate_stress_display");
            if (portStressDisplay) {
                portStressDisplay.textContent = `${portStress.toFixed(1)}/10`;
            }
        }

        const climateVolatility = document.getElementById("climate_volatility_index");
        if (climateVolatility) {
            // Volatility = stress * 10 (convert to 0-100 scale)
            const volatility = Math.min(100, stress * 10);
            climateVolatility.value = Math.round(volatility);
            climateVolatility.disabled = true; // Lock
            climateVolatility.style.opacity = '0.7';
            climateVolatility.style.cursor = 'not-allowed';
            const volatilityDisplay = document.getElementById("climate_volatility_index_display");
            if (volatilityDisplay) {
                volatilityDisplay.textContent = `${Math.round(volatility)}/100`;
            }
        }

        const climateResilience = document.getElementById("climate_resilience");
        if (climateResilience) {
            // Resilience = inverse of stress (higher stress = lower resilience)
            const resilience = Math.max(1, 10 - stress * 0.8);
            climateResilience.value = resilience.toFixed(1);
            climateResilience.disabled = true; // Lock
            climateResilience.style.opacity = '0.7';
            climateResilience.style.cursor = 'not-allowed';
            const resilienceDisplay = document.getElementById("climate_resilience_display");
            if (resilienceDisplay) {
                resilienceDisplay.textContent = `${resilience.toFixed(1)}/10`;
            }
        }

        // Update climate preview card with detailed warning
        updateClimatePreviewCard(data);
    }

    function updateClimatePreviewCard(data) {
        const previewCard = document.getElementById("climate-preview");
        const climateSection = document.getElementById("climate-section");
        
        if (!previewCard) return;

        const stress = data.stress;
        const ensoStatus = data.enso;
        const storms = data.storms;
        const oni = data.oni;
        const sst = data.sst;

        // Get month info
        const monthNames = ['Tháng Một', 'Tháng Hai', 'Tháng Ba', 'Tháng Tư', 'Tháng Năm', 'Tháng Sáu', 
                           'Tháng Bảy', 'Tháng Tám', 'Tháng Chín', 'Tháng Mười', 'Tháng Mười Một', 'Tháng Mười Hai'];
        const monthIdx = parseInt(document.getElementById('shipment-month')?.value?.split('-')[1]) - 1;
        const monthName = monthIdx >= 0 ? monthNames[monthIdx] : '';
        const monthNumber = monthIdx + 1;

        // Calculate risk increase for La Niña
        const riskIncrease = ensoStatus === 'La Niña' && stress >= 8 ? Math.round((stress - 5) * 8) : 0;
        const delayRecommendation = stress >= 8 && storms >= 3 ? '3–5 ngày' : stress >= 8 ? '2–3 ngày' : '';

        // Update status badge
        let statusText = '';
        let statusIcon = '🌊';
        let badgeStyle = '';
        
        // Format chuẩn quốc tế với ONI
        const oniSign = oni >= 0 ? '+' : '';
        if (ensoStatus === 'La Niña') {
            const intensity = Math.abs(oni) >= 1.0 ? 'Strong' : Math.abs(oni) >= 0.5 ? 'Moderate' : 'Weak';
            statusIcon = '🌊';
            statusText = `${intensity} La Niña Phase (ONI: ${oniSign}${oni}°C)`;
            badgeStyle = stress >= 8 
                ? 'background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(220, 38, 38, 0.4)); border-color: rgba(239, 68, 68, 0.6);'
                : 'background: linear-gradient(135deg, rgba(251, 191, 36, 0.3), rgba(245, 158, 11, 0.4)); border-color: rgba(251, 191, 36, 0.6);';
        } else if (ensoStatus === 'El Niño') {
            const intensity = Math.abs(oni) >= 1.0 ? 'Strong' : Math.abs(oni) >= 0.5 ? 'Moderate' : 'Weak';
            statusIcon = '🔥';
            statusText = `${intensity} El Niño Phase (ONI: ${oniSign}${oni}°C)`;
            badgeStyle = 'background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(220, 38, 38, 0.4)); border-color: rgba(239, 68, 68, 0.6);';
        } else {
            statusIcon = '✅';
            statusText = `Neutral Phase (ONI: ${oniSign}${oni}°C)`;
            badgeStyle = 'background: linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(5, 150, 105, 0.4)); border-color: rgba(16, 185, 129, 0.6);';
        }

        // Update stress display
        const stressClass = stress >= 8 ? 'critical' : stress >= 6 ? 'warning' : 'good';
        const stressText = stress >= 8 ? 'Critical' : stress >= 6 ? 'Cao' : 'Thấp';
        const stressColor = stressClass === 'critical' ? '#EF4444' : stressClass === 'warning' ? '#FBBF24' : '#10B981';

        // Get best carrier recommendation based on ESG
        let carrierRecommendation = '';
        if (stress >= 8) {
            const routeValue = document.getElementById('route_input')?.value || '';
            if (routeValue && window.LOGISTICS_DATA) {
                const carriers = window.LOGISTICS_DATA.getCarriersByRoute(routeValue);
                if (carriers && carriers.length > 0) {
                    const bestCarrier = carriers.reduce((prev, curr) => 
                        (curr.rating > prev.rating) ? curr : prev
                    );
                    carrierRecommendation = `Chọn ${bestCarrier.name} (${bestCarrier.rating.toFixed(1)}⭐, on-time ${bestCarrier.ontime}%)`;
                } else {
                    carrierRecommendation = 'Chọn hãng tàu có ESG cao (Maersk, MSC)';
                }
            } else {
                carrierRecommendation = 'Chọn hãng tàu có ESG cao (Maersk, MSC)';
            }
        }

        // Month-specific messages
        const monthMessages = {
            1: 'Tháng này thường có mưa lớn và gió mạnh ở khu vực Đông Nam Á',
            2: 'Thời tiết ổn định hơn, nhưng vẫn cần theo dõi ENSO',
            3: 'Bắt đầu mùa mưa, rủi ro bão tăng dần',
            4: 'Mùa mưa chính, rủi ro cao nhất trong năm',
            5: 'Mùa mưa tiếp tục, cần cẩn thận với bão',
            6: 'Chuyển giao mùa, thời tiết biến động',
            7: 'Mùa khô bắt đầu, rủi ro thấp hơn',
            8: 'Mùa khô, điều kiện tốt cho vận chuyển',
            9: 'Thời tiết ổn định, rủi ro thấp',
            10: 'Bắt đầu mùa mưa, cần theo dõi',
            11: 'Mùa mưa, rủi ro bão cao',
            12: 'Cuối năm, thời tiết biến động'
        };

        const monthSpecificMessage = monthMessages[monthNumber] || '';

        // Build warning list - Format chuẩn quốc tế
        const warningList = [];
        if (ensoStatus === 'La Niña' && stress >= 8) {
            const oniSign = oni >= 0 ? '+' : '';
            warningList.push(`Strong La Niña Phase (ONI: ${oniSign}${oni}°C) → ${riskIncrease > 0 ? `+${riskIncrease}%` : 'tăng'} rủi ro bão`);
        }
        if (storms > 0) {
            warningList.push(`${storms} bão dự kiến trong ${monthName}`);
        }
        if (delayRecommendation) {
            warningList.push(`<strong>Khuyên delay ${delayRecommendation}</strong>`);
        }
        if (carrierRecommendation) {
            warningList.push(carrierRecommendation);
        }
        if (monthSpecificMessage) {
            warningList.push(monthSpecificMessage);
        }

        // Update HTML elements
        const statusBadge = previewCard.querySelector('#climate-status-badge');
        const statusTextEl = previewCard.querySelector('#climate-status-text');
        const stressDisplay = previewCard.querySelector('#climate-stress-display');
        const stressBadgeDisplay = previewCard.querySelector('#climate-stress-badge-display');
        const recText = previewCard.querySelector('#climate-rec-text');
        const warningListEl = previewCard.querySelector('#climate-warning-list');
        const warningSection = previewCard.querySelector('#climate-warning-section');

        if (statusBadge) {
            statusBadge.style.cssText = badgeStyle;
        }
        if (statusTextEl) {
            statusTextEl.innerHTML = `<span class="status-icon">${statusIcon}</span> ${statusText}`;
        }
        if (stressDisplay) {
            stressDisplay.textContent = `${stress.toFixed(1)}/10`;
            stressDisplay.style.color = stressColor;
        }
        if (stressBadgeDisplay) {
            stressBadgeDisplay.textContent = stressText;
            stressBadgeDisplay.className = `badge ${stressClass}`;
        }
        if (recText) {
            recText.textContent = carrierRecommendation || 'Điều kiện khí hậu ổn định';
        }
        if (warningListEl) {
            warningListEl.innerHTML = warningList.map(item => `<li>${item}</li>`).join('');
        }
        if (warningSection) {
            warningSection.style.display = warningList.length > 0 ? 'block' : 'none';
        }
        
        // Show preview card and climate section
        previewCard.style.display = 'block';
        if (climateSection) {
            climateSection.style.display = 'block';
        }
    }

    // Lock all climate sliders immediately (before any data is loaded)
    function lockClimateSliders() {
        const sliders = [
            { id: 'climate-stress-slider', style: 'opacity: 0.7; cursor: not-allowed;' },
            { id: 'port_climate_stress', style: 'opacity: 0.7; cursor: not-allowed; background: rgba(0,255,136,0.05);' },
            { id: 'climate_volatility_index', style: 'opacity: 0.7; cursor: not-allowed; background: rgba(0,255,136,0.05);' },
            { id: 'climate_resilience', style: 'opacity: 0.7; cursor: not-allowed;' }
        ];
        
        sliders.forEach(slider => {
            const el = document.getElementById(slider.id);
            if (el) {
                el.disabled = true;
                el.setAttribute('readonly', 'readonly');
                if (slider.style) {
                    el.style.cssText += slider.style;
                }
            }
        });
    }

    // Lock sliders on page load
    lockClimateSliders();

    monthInput.addEventListener('change', () => {
        updateClimateData();
        lockClimateSliders(); // Re-lock after update
    });
    monthInput.addEventListener('input', () => {
        updateClimateData();
        lockClimateSliders(); // Re-lock after update
    });

    // Tự động chạy lần đầu nếu đã có giá trị (load from local JSON immediately)
    if (monthInput.value) {
        // Try immediately, then retry if CLIMATE_DATA_2025 not loaded yet
        updateClimateData();
        if (!window.CLIMATE_DATA_2025) {
            const checkInterval = setInterval(() => {
                if (window.CLIMATE_DATA_2025) {
                    clearInterval(checkInterval);
                    updateClimateData();
                    lockClimateSliders();
                }
            }, 100);
            // Stop checking after 2 seconds
            setTimeout(() => clearInterval(checkInterval), 2000);
        }
    }
});

