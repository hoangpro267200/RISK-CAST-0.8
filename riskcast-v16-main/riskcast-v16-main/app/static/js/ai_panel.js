/**
 * AI PANEL - SMART ASSIST
 * AI assistant with 3 skills: Explain, What-if, Optimize
 */

(function() {
    'use strict';

    let isOpen = false;
    let messages = [];

    /**
     * Initialize AI panel
     */
    function init() {
        // Floating button
        const floatBtn = document.getElementById('aiFloatBtn');
        if (floatBtn) {
            floatBtn.addEventListener('click', togglePanel);
        }

        // Close button
        const closeBtn = document.getElementById('aiPanelClose');
        if (closeBtn) {
            closeBtn.addEventListener('click', closePanel);
        }

        // Skill buttons
        const skillBtns = document.querySelectorAll('.ai-skill-btn');
        skillBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const skill = btn.dataset.skill;
                handleSkillClick(skill);
            });
        });

        // Send button
        const sendBtn = document.getElementById('aiSendBtn');
        const input = document.getElementById('aiInput');
        if (sendBtn) {
            sendBtn.addEventListener('click', sendMessage);
        }
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        }

        console.log('[AI Panel] Initialized');
    }

    /**
     * Toggle panel
     */
    function togglePanel() {
        if (isOpen) {
            closePanel();
        } else {
            openPanel();
        }
    }

    /**
     * Open panel
     */
    function openPanel() {
        const panel = document.getElementById('aiPanel');
        if (panel) {
            panel.classList.add('open');
            isOpen = true;
        }
    }

    /**
     * Close panel
     */
    function closePanel() {
        const panel = document.getElementById('aiPanel');
        if (panel) {
            panel.classList.remove('open');
            isOpen = false;
        }
    }

    /**
     * Handle skill button click
     */
    async function handleSkillClick(skill) {
        const shipmentState = window.OverviewV33?.getShipmentState();
        if (!shipmentState) {
            addMessage('assistant', 'No shipment data available.');
            return;
        }

        switch (skill) {
            case 'explain':
                await handleExplain(shipmentState);
                break;
            case 'whatif':
                await handleWhatIf(shipmentState);
                break;
            case 'optimize':
                await handleOptimize(shipmentState);
                break;
        }
    }

    /**
     * AI Explain - Summarize shipment
     */
    async function handleExplain(shipmentState) {
        addMessage('user', 'Explain this shipment');
        showTyping();

        try {
            const response = await fetch('/api/ai/explain', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(shipmentState)
            });

            if (!response.ok) {
                throw new Error('Failed to get explanation');
            }

            const data = await response.json();
            hideTyping();
            addMessage('assistant', data.explanation || data.message || 'Explanation generated successfully.');
        } catch (error) {
            hideTyping();
            addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            console.error('[AI Panel] Explain error:', error);
        }
    }

    /**
     * AI What-if Scenario
     */
    async function handleWhatIf(shipmentState) {
        addMessage('user', 'What if POD changes?');
        showTyping();

        // Prompt user for scenario
        const scenario = prompt('Enter your what-if scenario (e.g., "What if POD becomes USLAX?"):');
        if (!scenario) {
            hideTyping();
            return;
        }

        try {
            const response = await fetch('/api/ai/what_if', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    shipment: shipmentState,
                    scenario: scenario
                })
            });

            if (!response.ok) {
                throw new Error('Failed to process scenario');
            }

            const data = await response.json();
            hideTyping();

            // Update shipment state if new data provided
            if (data.updated_shipment) {
                window.OverviewV33.setShipmentState(data.updated_shipment);
                addMessage('assistant', data.analysis || 'Scenario processed. Shipment data updated.');
            } else {
                addMessage('assistant', data.analysis || data.message || 'Scenario analyzed successfully.');
            }
        } catch (error) {
            hideTyping();
            addMessage('assistant', 'Sorry, I encountered an error processing the scenario.');
            console.error('[AI Panel] What-if error:', error);
        }
    }

    /**
     * AI Optimize Route
     */
    async function handleOptimize(shipmentState) {
        addMessage('user', 'Optimize the route');
        showTyping();

        try {
            const response = await fetch('/api/ai/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(shipmentState)
            });

            if (!response.ok) {
                throw new Error('Failed to optimize route');
            }

            const data = await response.json();
            hideTyping();

            if (data.optimized_route && data.optimized_route.segments) {
                // Draw preview route
                window.OverviewV33.drawPreviewRoute(data.optimized_route.segments);
                addMessage('assistant', data.recommendation || 'Route optimized. Preview shown on globe (cyan dotted line).');
                
                // Ask if user wants to apply
                setTimeout(() => {
                    const apply = confirm('Apply this optimized route?');
                    if (apply && data.optimized_route) {
                        window.OverviewV33.setShipmentState({
                            ...shipmentState,
                            segments: data.optimized_route.segments
                        });
                        window.OverviewV33.clearPreviewRoute();
                        addMessage('assistant', 'Optimized route applied successfully.');
                    } else {
                        window.OverviewV33.clearPreviewRoute();
                    }
                }, 1000);
            } else {
                addMessage('assistant', data.recommendation || data.message || 'Route optimization completed.');
            }
        } catch (error) {
            hideTyping();
            addMessage('assistant', 'Sorry, I encountered an error optimizing the route.');
            console.error('[AI Panel] Optimize error:', error);
        }
    }

    /**
     * Send user message
     */
    async function sendMessage() {
        const input = document.getElementById('aiInput');
        if (!input) return;

        const message = input.value.trim();
        if (!message) return;

        addMessage('user', message);
        input.value = '';
        showTyping();

        try {
            const shipmentState = window.OverviewV33?.getShipmentState();
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    shipment: shipmentState
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();
            hideTyping();
            addMessage('assistant', data.response || data.message || 'I received your message.');
        } catch (error) {
            hideTyping();
            addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            console.error('[AI Panel] Chat error:', error);
        }
    }

    /**
     * Add message to chat
     */
    function addMessage(role, text) {
        const messagesContainer = document.getElementById('aiMessages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = text;

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageDiv.appendChild(bubble);
        messageDiv.appendChild(time);
        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        messages.push({ role, text, time: new Date() });
    }

    /**
     * Show typing indicator
     */
    function showTyping() {
        const messagesContainer = document.getElementById('aiMessages');
        if (!messagesContainer) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'ai-message assistant';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="ai-typing">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Hide typing indicator
     */
    function hideTyping() {
        const typing = document.getElementById('typingIndicator');
        if (typing) {
            typing.remove();
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

