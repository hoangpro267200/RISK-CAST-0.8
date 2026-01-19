/**

 * RISKCAST v19 AI Assist Panel

 * Conversational AI panel with heuristic responses based on shipment configuration

 */



class AiAssistPanel {

    constructor(controller) {

        this.controller = controller;

        this.conversation = [];

        this.isProcessing = false;

    }

    

    /**

     * Initialize AI panel

     */

    init() {

        this.panel = document.getElementById('rc-ai-panel');

        this.toggleBtn = document.getElementById('rc-ai-assist-toggle');

        this.closeBtn = document.getElementById('rc-ai-panel-close');

        this.conversationDiv = document.getElementById('rc-ai-conversation');

        this.input = document.getElementById('rc-ai-input');

        this.sendBtn = document.getElementById('rc-ai-send');

        this.content = document.getElementById('rc-content');

        

        this.attachEventListeners();

    }

    

    /**

     * Attach event listeners

     */

    attachEventListeners() {

        // Toggle panel

        if (this.toggleBtn) {

            this.toggleBtn.addEventListener('click', () => {

                this.togglePanel();

            });

        }

        

        // Close panel

        if (this.closeBtn) {

            this.closeBtn.addEventListener('click', () => {

                this.closePanel();

            });

        }

        

        // Send message

        if (this.sendBtn) {

            this.sendBtn.addEventListener('click', () => {

                this.sendMessage();

            });

        }

        

        // Send on Enter (but Shift+Enter for new line)

        if (this.input) {

            this.input.addEventListener('keydown', (e) => {

                if (e.key === 'Enter' && !e.shiftKey) {

                    e.preventDefault();

                    this.sendMessage();

                }

            });

        }

    }

    

    /**

     * Toggle panel open/close

     */

    togglePanel() {

        if (this.panel.classList.contains('active')) {

            this.closePanel();

        } else {

            this.openPanel();

        }

    }

    

    /**

     * Open panel

     */

    openPanel() {

        this.panel.classList.add('active');

        if (this.content) {

            this.content.classList.add('rc-ai-panel-open');

        }

        

        // Focus input

        setTimeout(() => {

            if (this.input) this.input.focus();

        }, 300);

    }

    

    /**

     * Close panel

     */

    closePanel() {

        this.panel.classList.remove('active');

        if (this.content) {

            this.content.classList.remove('rc-ai-panel-open');

        }

    }

    

    /**

     * Send user message

     */

    sendMessage() {

        if (this.isProcessing) return;

        

        const message = this.input.value.trim();

        if (!message) return;

        

        // Add user message

        this.addMessage(message, 'user');

        

        // Clear input

        this.input.value = '';

        

        // Process and respond

        this.isProcessing = true;

        this.sendBtn.disabled = true;

        

        setTimeout(() => {

            const response = this.generateResponse(message);

            this.addMessage(response, 'ai');

            this.isProcessing = false;

            this.sendBtn.disabled = false;

        }, 400 + Math.random() * 400); // Simulate thinking time

    }

    

    /**

     * Add message to conversation

     */

    addMessage(text, type) {

        const messageDiv = document.createElement('div');

        messageDiv.className = `rc-ai-message rc-ai-message-${type}`;

        

        const avatar = document.createElement('div');

        avatar.className = 'rc-ai-message-avatar';

        avatar.textContent = type === 'user' ? 'U' : 'AI';

        

        const content = document.createElement('div');

        content.className = 'rc-ai-message-content';

        content.innerHTML = text;

        

        messageDiv.appendChild(avatar);

        messageDiv.appendChild(content);

        

        this.conversationDiv.appendChild(messageDiv);

        

        // Scroll to bottom

        this.conversationDiv.scrollTop = this.conversationDiv.scrollHeight;

        

        // Re-init icons

        lucide.createIcons();

    }

    

    /**

     * Generate AI response based on query and context

     */

    generateResponse(query) {

        const lowerQuery = query.toLowerCase();

        const context = this.controller.getCurrentRiskContext();

        const { formData, riskScore, riskLevel } = context;

        

        // Weather-related questions

        if (lowerQuery.includes('weather') || lowerQuery.includes('storm') || lowerQuery.includes('climate')) {

            if (formData.modules.weather) {

                if (formData.transitDays > 20) {

                    return `Weather module is enabled and monitoring your route. With a ${formData.transitDays}-day transit, you're exposed to seasonal weather patterns. ${this.getSeasonalAdvice(formData)}`;

                }

                return `Weather module is enabled. Your transit time of ${formData.transitDays || 'not specified'} days means ${formData.transitDays > 15 ? 'moderate' : 'limited'} weather exposure. I recommend monitoring forecasts during the voyage.`;

            }

            return `Weather module is currently disabled. I recommend enabling it for routes longer than 15 days to monitor storm risks and seasonal patterns.`;

        }

        

        // Risk-related questions

        if (lowerQuery.includes('risk') || lowerQuery.includes('safe') || lowerQuery.includes('dangerous')) {

            let response = `Your current risk score is <strong>${riskScore}/100</strong> (${riskLevel} risk). `;

            

            if (riskLevel === 'low') {

                response += 'This is a relatively safe configuration. Standard precautions should be sufficient.';

            } else if (riskLevel === 'moderate') {

                response += 'This indicates moderate risk. Key concerns:<ul>';

                if (formData.transitDays > 20) response += '<li>Extended transit time increases delay exposure</li>';

                if (['electronics', 'pharma'].includes(formData.cargoType)) response += '<li>High-value cargo requires extra attention</li>';

                if (formData.cargoSensitivity !== 'standard') response += '<li>Sensitive cargo needs special handling</li>';

                response += '</ul>Consider additional insurance and tracking.';

            } else {

                response += 'This is a high-risk shipment. Critical factors:<ul>';

                if (formData.transitDays > 30) response += '<li>Very long transit significantly increases risk</li>';

                if (formData.cargoType === 'chemical') response += '<li>Hazardous cargo requires strict protocols</li>';

                if (formData.insuranceValue > 500000) response += '<li>High insurance value warrants premium coverage</li>';

                response += '</ul><strong>Recommendations:</strong> Increase insurance, add real-time tracking, consider expedited routing.';

            }

            

            return response;

        }

        

        // Route-related questions

        if (lowerQuery.includes('route') || lowerQuery.includes('port') || lowerQuery.includes('transit')) {

            if (formData.originPort && formData.destinationPort) {

                let response = `Your route from <strong>${formData.originPort}</strong> to <strong>${formData.destinationPort}</strong> via ${formData.transportMode || 'unspecified mode'}. `;

                

                if (formData.transitDays) {

                    response += `Estimated transit: ${formData.transitDays} days. `;

                    if (formData.transitDays > 30) {

                        response += 'This is a long-haul route with higher exposure to delays and port congestion.';

                    } else if (formData.transitDays < 10) {

                        response += 'This is a relatively quick route, reducing time-based risks.';

                    }

                }

                

                if (formData.modules.congestion) {

                    response += ' Port congestion module is monitoring for capacity issues at both ends.';

                }

                

                return response;

            }

            return 'Please configure your origin and destination ports first so I can analyze your route.';

        }

        

        // Insurance questions

        if (lowerQuery.includes('insurance') || lowerQuery.includes('coverage') || lowerQuery.includes('value')) {

            if (formData.insuranceValue) {

                let response = `Your declared insurance value is <strong>$${formData.insuranceValue.toLocaleString()}</strong>. `;

                

                if (riskScore > 60) {

                    response += 'Given the high risk score, I recommend comprehensive all-risk coverage with minimal deductibles.';

                } else if (riskScore > 30) {

                    response += 'For moderate risk, consider standard marine cargo insurance with reasonable deductibles.';

                } else {

                    response += 'With low risk, basic cargo insurance should be sufficient, though comprehensive coverage is always safer.';

                }

                

                if (formData.cargoType === 'electronics' || formData.cargoType === 'pharma') {

                    response += ' For high-value/sensitive cargo, ensure your policy covers temperature deviations and theft.';

                }

                

                return response;

            }

            return 'Please specify your insurance value in the Cargo section so I can provide tailored advice.';

        }

        

        // Cargo questions

        if (lowerQuery.includes('cargo') || lowerQuery.includes('goods') || lowerQuery.includes('packing')) {

            if (formData.cargoType) {

                const cargoNames = {

                    general: 'General Cargo',

                    electronics: 'Electronics',

                    pharma: 'Pharmaceuticals',

                    perishable: 'Perishable Goods',

                    chemical: 'Chemicals'

                };

                

                let response = `Your cargo type is <strong>${cargoNames[formData.cargoType]}</strong>. `;

                

                if (formData.cargoType === 'pharma') {

                    response += 'Pharmaceuticals require strict temperature control. Ensure cold chain integrity throughout transit. Consider reefer containers and temperature logging devices.';

                } else if (formData.cargoType === 'electronics') {

                    response += 'Electronics are high-value and moisture-sensitive. Use desiccants, anti-static packaging, and ensure proper container sealing.';

                } else if (formData.cargoType === 'chemical') {

                    response += 'Hazardous cargo requires IMDG compliance, proper labeling, and segregation. Ensure all safety documentation is complete.';

                } else if (formData.cargoType === 'perishable') {

                    response += 'Perishables need rapid transit and often refrigeration. Monitor transit time closely and have contingency plans for delays.';

                }

                

                if (formData.cargoSensitivity === 'fragile') {

                    response += ' Your cargo is marked as fragile—use shock indicators and specify "handle with care" instructions.';

                }

                

                return response;

            }

            return 'Please specify your cargo type in the Cargo section for detailed handling recommendations.';

        }

        

        // Module questions

        if (lowerQuery.includes('module') || lowerQuery.includes('algorithm') || lowerQuery.includes('analysis')) {

            const enabledModules = Object.entries(formData.modules)

                .filter(([k, v]) => v)

                .map(([k]) => k);

            

            if (enabledModules.length === 0) {

                return 'No risk modules are currently enabled. I recommend enabling at least Weather, Port Congestion, and Carrier Reliability for comprehensive risk monitoring.';

            }

            

            let response = `You have <strong>${enabledModules.length}</strong> modules enabled: ${enabledModules.join(', ')}. `;

            

            if (!formData.modules.weather && formData.transitDays > 15) {

                response += 'Consider enabling Weather module for routes longer than 15 days.';

            }

            if (!formData.modules.congestion) {

                response += ' Port Congestion module helps predict delays at major hubs.';

            }

            if (!formData.modules.carrier && formData.transportMode) {

                response += ' Carrier Reliability module tracks on-time performance and service quality.';

            }

            

            return response;

        }

        

        // Timing questions

        if (lowerQuery.includes('delay') || lowerQuery.includes('time') || lowerQuery.includes('schedule')) {

            if (formData.transitDays) {

                let response = `Your estimated transit is <strong>${formData.transitDays} days</strong>. `;

                

                if (formData.modules.congestion) {

                    response += 'Port congestion module is monitoring for potential delays. ';

                }

                

                if (formData.transitDays > 25) {

                    response += 'Long transit routes are more susceptible to cascading delays. I recommend adding a 5-7 day buffer for critical shipments.';

                } else {

                    response += 'This is a reasonable transit time. Standard buffer of 2-3 days should suffice.';

                }

                

                if (formData.buyerPriority === 'critical') {

                    response += ' Given critical priority, consider expedited routing or air freight alternatives.';

                }

                

                return response;

            }

            return 'Please specify transit days in the Transport section for timing analysis.';

        }

        

        // Incoterm questions

        if (lowerQuery.includes('incoterm') || lowerQuery.includes('responsibility') || lowerQuery.includes('seller') || lowerQuery.includes('buyer')) {

            if (formData.incoterm) {

                const incotermInfo = {

                    exw: 'EXW (Ex Works): Seller delivers at their premises. Buyer bears all transport costs and risks.',

                    fob: 'FOB (Free On Board): Seller delivers to vessel. Risk transfers when goods cross ship rail.',

                    cif: 'CIF (Cost, Insurance & Freight): Seller pays freight and insurance to destination port, but risk transfers at origin port.',

                    cfr: 'CFR (Cost & Freight): Similar to CIF but seller not required to provide insurance.',

                    dap: 'DAP (Delivered At Place): Seller delivers to named place, ready for unloading. Buyer handles import clearance.',

                    ddp: 'DDP (Delivered Duty Paid): Seller bears all costs and risks until goods delivered to buyer.'

                };

                

                return `Your incoterm is <strong>${formData.incoterm.toUpperCase()}</strong>. ${incotermInfo[formData.incoterm] || 'Please verify this term with your trade partner.'}`;

            }

            return 'Please specify your incoterm in the Seller section for responsibility breakdown.';

        }

        

        // General help

        if (lowerQuery.includes('help') || lowerQuery.includes('how') || lowerQuery.includes('what can')) {

            return `I can help you with:

                <ul>

                    <li>Risk analysis and mitigation strategies</li>

                    <li>Route and port recommendations</li>

                    <li>Insurance and coverage advice</li>

                    <li>Cargo handling best practices</li>

                    <li>Transit time optimization</li>

                    <li>Module configuration guidance</li>

                    <li>Incoterm explanations</li>

                </ul>

                Just ask me anything about your shipment configuration!`;

        }

        

        // Optimization questions

        if (lowerQuery.includes('optimize') || lowerQuery.includes('improve') || lowerQuery.includes('reduce risk') || lowerQuery.includes('better')) {

            let suggestions = [];

            

            if (riskScore > 60) {

                suggestions.push('Your risk score is high. Consider these improvements:');

                if (formData.transitDays > 30) suggestions.push('Explore faster routing options');

                if (formData.sellerExperience === 'new') suggestions.push('Request additional documentation from seller');

                if (Object.values(formData.modules).filter(v => v).length < 3) suggestions.push('Enable more risk monitoring modules');

                if (formData.insuranceValue > 100000 && riskScore > 70) suggestions.push('Consider premium insurance with lower deductibles');

            } else if (riskScore > 30) {

                suggestions.push('Your risk is moderate. Some optimization ideas:');

                if (!formData.modules.weather) suggestions.push('Enable weather monitoring for seasonal risk');

                if (!formData.modules.carrier) suggestions.push('Track carrier performance metrics');

                suggestions.push('Add 3-5 day buffer for schedule flexibility');

            } else {

                suggestions.push('Your risk is already low! To optimize further:');

                suggestions.push('Consider cargo consolidation for cost savings');

                suggestions.push('Negotiate better rates with proven carriers');

                if (formData.transitDays > 15) suggestions.push('Explore faster service options');

            }

            

            return suggestions.join('<br>• ');

        }

        

        // Default response

        return `I understand you're asking about "${query}". Based on your current configuration (risk score: ${riskScore}), I'm here to help. Could you be more specific? You can ask about risk factors, route details, insurance, cargo handling, or optimization strategies.`;

    }

    

    /**

     * Get seasonal advice

     */

    getSeasonalAdvice(formData) {

        const month = new Date().getMonth() + 1;

        

        // Simple seasonal heuristics

        if (month >= 6 && month <= 11) {

            // Hurricane/typhoon season

            if (formData.originPort?.includes('US') || formData.destinationPort?.includes('US')) {

                return 'Note: Hurricane season in Atlantic/Gulf (June-November). Monitor tropical storm forecasts.';

            }

            if (formData.originPort?.includes('VN') || formData.originPort?.includes('CN')) {

                return 'Note: Typhoon season in Western Pacific (June-November). Expect possible route deviations.';

            }

        }

        

        if (month >= 12 || month <= 2) {

            return 'Winter season: Watch for ice in northern routes and potential port closures.';

        }

        

        return 'Monitor seasonal weather patterns for your specific route.';

    }

}



// Export to global scope

window.AiAssistPanel = AiAssistPanel;



/**

 * FILE: app/static/js/pages/input/ai_panel_v19.js

 * PURPOSE: AI Assist Panel for RISKCAST v19

 * 

 * FEATURES:

 * - Conversational interface with message bubbles

 * - Heuristic response generation based on:

 *   - Risk score and level

 *   - Form data (route, cargo, modules, etc.)

 *   - Specific query keywords

 * - Context-aware recommendations

 * - Seasonal weather advice

 * - Incoterm explanations

 * - Optimization suggestions

 * - Smooth animations and typing effect simulation

 * 

 * RESPONSE CATEGORIES:

 * - Weather & climate

 * - Risk analysis

 * - Route & ports

 * - Insurance & coverage

 * - Cargo handling

 * - Module recommendations

 * - Timing & delays

 * - Incoterm guidance

 * - General help

 * - Optimization strategies

 * 

 * ARCHITECTURE:

 * - No real API calls - all responses are frontend heuristics

 * - Reads from controller.getCurrentRiskContext()

 * - Maintains conversation history

 * - Keyword-based intent matching

 */

