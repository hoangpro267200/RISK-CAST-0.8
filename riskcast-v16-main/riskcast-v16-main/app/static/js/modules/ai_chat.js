// ========================================
// AI CHAT WIDGET - JAVASCRIPT LOGIC
// ========================================

(function() {
    'use strict';

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[AI Chat] DOM loaded, initializing...');
        
        // ========================================
        // NEW PREMIUM DESIGN - Run First
        // ========================================
        const aiToggle = document.getElementById('ai-toggle');
        const aiPanel = document.getElementById('ai-panel');
        const aiMinimize = document.getElementById('ai-minimize');
        const aiInput = document.getElementById('ai-input');
        const aiSend = document.getElementById('ai-send');
        const aiMessages = document.getElementById('ai-messages');

        console.log('[AI Chat Premium] Elements found:', {
            toggle: !!aiToggle,
            panel: !!aiPanel,
            minimize: !!aiMinimize,
            input: !!aiInput,
            send: !!aiSend,
            messages: !!aiMessages
        });

        if (aiToggle && aiPanel) {
            console.log('[AI Chat Premium] Initializing premium chat widget...');
            
            // Ensure toggle is visible
            aiToggle.style.display = 'flex';
            aiToggle.style.visibility = 'visible';
            aiToggle.style.opacity = '1';
            
            // Ensure panel is hidden initially
            aiPanel.style.display = 'none';
            
            // Open panel when clicking toggle
            aiToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('[AI Chat Premium] Toggle clicked, opening panel...');
                aiPanel.style.display = 'flex';
                aiPanel.style.visibility = 'visible';
                aiToggle.style.display = 'none';
                setTimeout(() => {
                    if (aiInput) {
                        aiInput.focus();
                        console.log('[AI Chat Premium] Input focused');
                    }
                }, 100);
            });

            // Minimize panel
            if (aiMinimize) {
                aiMinimize.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('[AI Chat Premium] Minimize clicked, closing panel...');
                    aiPanel.style.display = 'none';
                    aiPanel.style.visibility = 'hidden';
                    aiToggle.style.display = 'flex';
                });
            } else {
                console.warn('[AI Chat Premium] Minimize button not found!');
            }

            // Send message from new panel
            if (aiSend && aiInput && aiMessages) {
                const sendMessageNew = async function() {
                    const messageText = aiInput.value.trim();
                    if (!messageText) return;

                    // Performance: Use DocumentFragment for batch DOM updates
                    const fragment = document.createDocumentFragment();
                    
                    // Add user message
                    const userBubble = document.createElement('div');
                    userBubble.className = 'ai-bubble user';
                    userBubble.textContent = messageText;
                    fragment.appendChild(userBubble);
                    
                    // Show typing indicator
                    const typingBubble = document.createElement('div');
                    typingBubble.className = 'ai-bubble';
                    typingBubble.innerHTML = '<div style="display: flex; gap: 4px;"><div style="width: 6px; height: 6px; background: #00d4aa; border-radius: 50%; animation: typingBounce 1.4s infinite;"></div><div style="width: 6px; height: 6px; background: #00d4aa; border-radius: 50%; animation: typingBounce 1.4s infinite 0.2s;"></div><div style="width: 6px; height: 6px; background: #00d4aa; border-radius: 50%; animation: typingBounce 1.4s infinite 0.4s;"></div></div>';
                    fragment.appendChild(typingBubble);
                    
                    // Batch append and scroll (single DOM operation)
                    aiMessages.appendChild(fragment);
                    aiInput.value = '';
                    aiMessages.scrollTop = aiMessages.scrollHeight;

                    try {
                        const response = await fetch('/api/ai/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                message: messageText,
                                context: {
                                    route: document.getElementById('summary-route')?.textContent || 'N/A',
                                    cargo: document.getElementById('summary-cargo')?.textContent || 'N/A',
                                    container: document.getElementById('summary-container')?.textContent || 'N/A',
                                    carrier: document.getElementById('summary-carrier')?.textContent || 'N/A'
                                }
                            })
                        });

                        if (!response.ok) {
                            let errorMsg = `API Error: ${response.status} ${response.statusText}`;
                            try {
                                const errorData = await response.json();
                                errorMsg = errorData.detail || errorData.message || errorMsg;
                                console.error('[AI Chat Premium] API Error Response:', errorData);
                            } catch (e) {
                                const errorText = await response.text().catch(() => '');
                                console.error('[AI Chat Premium] API Error Text:', errorText);
                                errorMsg = errorText || errorMsg;
                            }
                            throw new Error(errorMsg);
                        }
                        const data = await response.json();
                        console.log('[AI Chat Premium] Response data:', data);

                        // Remove typing indicator
                        typingBubble.remove();

                        // Add AI response - support both 'reply' and 'response' fields
                        const aiBubble = document.createElement('div');
                        aiBubble.className = 'ai-bubble';
                        const aiResponse = data.reply || data.response || data.message || 'Xin lỗi, tôi chưa hiểu câu hỏi của bạn.';
                        aiBubble.textContent = aiResponse;
                        aiMessages.appendChild(aiBubble);
                        aiMessages.scrollTop = aiMessages.scrollHeight;

                    } catch (error) {
                        console.error('[AI Chat Premium] Error:', error);
                        console.error('[AI Chat Premium] Error message:', error.message);
                        console.error('[AI Chat Premium] Error stack:', error.stack);
                        typingBubble.remove();
                        const errorBubble = document.createElement('div');
                        errorBubble.className = 'ai-bubble';
                        // Provide more specific error message based on error type
                        let errorMessage = 'Xin lỗi, đã xảy ra lỗi khi kết nối với AI. Vui lòng thử lại sau.';
                        let useHTML = false;
                        const errorMsg = (error.message || '').toLowerCase();
                        if (errorMsg.includes('anthropic_api_key not configured') || errorMsg.includes('api key') || errorMsg.includes('anthropic_api_key') || errorMsg.includes('authentication') || errorMsg.includes('not configured')) {
                            errorMessage = '⚠️ <strong>API Key chưa được cấu hình!</strong><br><br>Vui lòng:<br>1. Tạo file <code>.env</code> trong thư mục gốc<br>2. Thêm dòng: <code>ANTHROPIC_API_KEY=your_api_key_here</code><br>3. Lấy API key tại: <a href="https://console.anthropic.com/" target="_blank">https://console.anthropic.com/</a><br>4. Restart server sau khi thêm API key';
                            useHTML = true;
                        } else if (errorMsg.includes('401') || errorMsg.includes('Unauthorized')) {
                            errorMessage = '❌ Lỗi xác thực. Vui lòng kiểm tra API key trong file .env';
                        } else if (errorMsg.includes('500') || errorMsg.includes('Internal Server')) {
                            errorMessage = '⚠️ Lỗi máy chủ. Vui lòng thử lại sau.';
                        } else if (errorMsg.includes('Network') || errorMsg.includes('Failed to fetch')) {
                            errorMessage = '🌐 Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet.';
                        } else if (errorMsg.includes('API Error')) {
                            errorMessage = `❌ Lỗi API: ${errorMsg}`;
                        }
                        if (useHTML) {
                            errorBubble.innerHTML = errorMessage;
                            errorBubble.style.whiteSpace = 'normal';
                            errorBubble.style.lineHeight = '1.6';
                        } else {
                            errorBubble.textContent = errorMessage;
                        }
                        aiMessages.appendChild(errorBubble);
                        aiMessages.scrollTop = aiMessages.scrollHeight;
                    }
                };

                aiSend.addEventListener('click', sendMessageNew);
                aiInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessageNew();
                    }
                });
                
                console.log('[AI Chat Premium] Send message handlers attached');
            }
        } else {
            // Only warn if we're on a page that should have AI chat
            if (window.location.pathname.includes('/results') || window.location.pathname.includes('/input')) {
                // Silently fall back to legacy - this is expected behavior
            }
        }
        
        // ========================================
        // ========================================
        const chatButton = document.getElementById('chatButton') || document.getElementById('aiChatButton');
        const chatPopup = document.getElementById('chatPopup') || document.getElementById('aiChatPopup');
        const chatClose = document.getElementById('chatClose') || document.getElementById('chatCloseBtn');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton') || document.getElementById('chatSendBtn');
        const chatMessages = document.getElementById('chatMessages');
        const notificationBadge = document.getElementById('notificationBadge');
        if (!aiToggle || !aiPanel) {
            // Check if required elements exist
            if (!chatPopup || !chatInput || !sendButton || !chatMessages) {
                console.warn('[AI Chat] Missing required DOM elements, widget not initialized.');
                console.warn('[AI Chat] chatPopup:', chatPopup, 'chatInput:', chatInput, 'sendButton:', sendButton, 'chatMessages:', chatMessages);
                return;
            }

            console.log('[AI Chat] Initializing legacy widget...');
            console.log('[AI Chat] chatButton:', chatButton, 'chatPopup:', chatPopup);

        // Create backdrop overlay if it doesn't exist
        let backdrop = document.getElementById('aiChatBackdrop');
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.id = 'aiChatBackdrop';
            backdrop.className = 'ai-chat-backdrop';
            document.body.appendChild(backdrop);
        }

        // Store scroll position
        let savedScrollPosition = 0;
        let isChatOpen = false;

        // OPEN/CLOSE CHAT POPUP
        function openChat(e) {
            // Prevent any default behavior that might cause scrolling
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            // Prevent multiple opens
            if (isChatOpen) {
                return;
            }
            
            console.log('[AI Chat] Opening chat popup...');
            if (!chatPopup) {
                console.error('[AI Chat] chatPopup is null!');
                return;
            }
            
            isChatOpen = true;
            
            // Save current scroll position BEFORE any DOM changes
            savedScrollPosition = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
            
            // Prevent body scroll when modal is open (but keep scroll position)
            // Use a more reliable method to prevent scroll
            const scrollY = window.scrollY;
            document.body.style.overflow = 'hidden';
            document.body.style.position = 'fixed';
            document.body.style.top = `-${scrollY}px`;
            document.body.style.width = '100%';
            document.documentElement.style.scrollBehavior = 'auto';
            
            // Show backdrop first
            if (backdrop) {
                backdrop.classList.add('active');
            }
            
            // Force display and visibility with centered transform
            // Set all styles explicitly to ensure visibility
            chatPopup.style.display = 'flex';
            chatPopup.style.visibility = 'visible';
            chatPopup.style.opacity = '0';
            chatPopup.style.zIndex = '99999';
            chatPopup.style.position = 'fixed';
            chatPopup.style.top = '50%';
            chatPopup.style.left = '50%';
            chatPopup.style.transform = 'translate(-50%, -50%) scale(0.85)';
            chatPopup.classList.add('active');
            
            // Force reflow to ensure styles are applied
            void chatPopup.offsetHeight;
            
            // Small delay to ensure CSS transitions work, then animate to full opacity
            setTimeout(() => {
                chatPopup.style.opacity = '1';
                chatPopup.style.transform = 'translate(-50%, -50%) scale(1)';
                chatPopup.style.visibility = 'visible';
            }, 10);
            
            // Focus input without causing scroll
            if (chatInput) {
                setTimeout(() => {
                    // Prevent scroll when focusing - use preventScroll option
                    try {
                        chatInput.focus({ preventScroll: true });
                    } catch (e) {
                        chatInput.focus();
                    }
                    // Ensure we're still at the saved position
                    if (document.body.style.position === 'fixed') {
                        // Position is already locked, no need to scroll
                    }
                }, 200);
            }
            if (notificationBadge) {
                notificationBadge.style.display = 'none';
            }
            
            console.log('[AI Chat] Chat popup opened successfully');
        }

        function closeChat() {
            console.log('[AI Chat] Closing chat popup...');
            
            isChatOpen = false;
            
            // Get the scroll position from body top style before removing it
            const bodyTop = document.body.style.top;
            const scrollY = bodyTop ? parseInt(bodyTop.replace('-', '')) : savedScrollPosition;
            
            // Restore body scroll and position
            document.body.style.overflow = '';
            document.body.style.position = '';
            document.body.style.top = '';
            document.body.style.width = '';
            document.documentElement.style.scrollBehavior = '';
            
            // Restore scroll position after a brief delay to ensure styles are applied
            setTimeout(() => {
                window.scrollTo({
                    top: scrollY || savedScrollPosition,
                    behavior: 'auto'
                });
            }, 10);
            
            if (chatPopup) {
                chatPopup.classList.remove('active');
                // Delay hiding to allow animation
                setTimeout(() => {
                    chatPopup.style.display = 'none';
                }, 300);
            }
            
            // Hide backdrop
            if (backdrop) {
                backdrop.classList.remove('active');
            }
        }

        // Premium code already initialized above, skip duplicate
        // Support both chat button and 3D bot
        if (chatButton) {
            console.log('[AI Chat] Adding click listener to chatButton');
            chatButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                openChat(e);
            });
        } else {
            // chatButton not found - this is OK if AI chat is not used on this page
            // Only log if we're on a page that should have it
            if (window.location.pathname.includes('/results')) {
                // Silently handle - chat button is optional
            }
        }
        
        // Make 3D bot clickable to open chat
        const aiBot = document.getElementById('aiBot');
        if (aiBot) {
            console.log('[AI Chat] Adding click listener to 3D bot');
            aiBot.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                openChat(e);
            });
            // Make sure cursor shows it's clickable
            aiBot.style.cursor = 'pointer';
        } else {
            console.warn('[AI Chat] 3D bot (aiBot) not found!');
        }
        
        if (chatClose) {
            chatClose.addEventListener('click', function(e) {
                e.stopPropagation();
                closeChat();
            });
        }

        // Close on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && chatPopup && chatPopup.classList.contains('active')) {
                closeChat();
            }
        });
        
        // Close when clicking on backdrop
        if (backdrop) {
            backdrop.addEventListener('click', function(e) {
                e.stopPropagation();
                closeChat();
            });
        }
        } // Close if (!aiToggle || !aiPanel) block

        // SEND MESSAGE FUNCTION
        async function sendMessage() {
            const messageText = chatInput.value.trim();
            
            if (!messageText) return;

            addMessage(messageText, 'user');
            chatInput.value = '';
            sendButton.disabled = true;
            showTypingIndicator();

            try {
                // Extract context from page
                const context = {
                    overall_risk: document.getElementById('overall-risk-index')?.textContent || 'N/A',
                    expected_loss: document.getElementById('expected-loss')?.textContent || 'N/A',
                    reliability: document.getElementById('reliability-score')?.textContent || 'N/A',
                    route: document.getElementById('routeChip')?.textContent || 'N/A',
                    esg_score: document.getElementById('esg-score')?.textContent || 'N/A',
                    climate_hazard_index: document.getElementById('chi-hero-value')?.textContent || 'N/A'
                };

                const response = await fetch('/api/ai/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: messageText,
                        context: context
                    })
                });

                if (!response.ok) {
                    let errorMsg = `API Error: ${response.status} ${response.statusText}`;
                    try {
                        const errorData = await response.json();
                        errorMsg = errorData.detail || errorData.message || errorMsg;
                        console.error('[AI Chat Legacy] API Error Response:', errorData);
                    } catch (e) {
                        const errorText = await response.text().catch(() => '');
                        console.error('[AI Chat Legacy] API Error Text:', errorText);
                        errorMsg = errorText || errorMsg;
                    }
                    console.error('[AI Chat Legacy] API Error:', errorMsg);
                    throw new Error(errorMsg);
                }

                const data = await response.json();

                hideTypingIndicator();
                // Support both 'reply' and 'response' fields from API
                const aiResponse = data.reply || data.response || data.message || 'Xin lỗi, tôi chưa hiểu câu hỏi của bạn.';
                addMessage(aiResponse, 'ai');

            } catch (error) {
                console.error('[AI Chat Legacy] Error:', error);
                console.error('[AI Chat Legacy] Error message:', error.message);
                console.error('[AI Chat Legacy] Error stack:', error.stack);
                hideTypingIndicator();
                // Provide more specific error message based on error type
                let errorMessage = 'Xin lỗi, đã xảy ra lỗi khi kết nối với AI. Vui lòng thử lại sau.';
                const errorMsg = error.message || '';
                if (errorMsg.includes('ANTHROPIC_API_KEY not configured') || errorMsg.includes('API key') || errorMsg.includes('ANTHROPIC_API_KEY') || errorMsg.includes('authentication')) {
                    errorMessage = '⚠️ API Key chưa được cấu hình!\n\nVui lòng:\n1. Tạo file .env trong thư mục gốc\n2. Thêm dòng: ANTHROPIC_API_KEY=your_api_key_here\n3. Lấy API key tại: https://console.anthropic.com/\n4. Restart server sau khi thêm API key';
                } else if (errorMsg.includes('401') || errorMsg.includes('Unauthorized')) {
                    errorMessage = '❌ Lỗi xác thực. Vui lòng kiểm tra API key trong file .env';
                } else if (errorMsg.includes('500') || errorMsg.includes('Internal Server')) {
                    errorMessage = '⚠️ Lỗi máy chủ. Vui lòng thử lại sau.';
                } else if (errorMsg.includes('Network') || errorMsg.includes('Failed to fetch')) {
                    errorMessage = '🌐 Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet.';
                } else if (errorMsg.includes('API Error')) {
                    errorMessage = `❌ Lỗi API: ${errorMsg}`;
                }
                addMessage(errorMessage, 'ai');
            } finally {
                sendButton.disabled = false;
            }
        }

        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = sender === 'ai' ? '🤖' : '👤';
            
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            bubble.textContent = text;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(bubble);
            chatMessages.appendChild(messageDiv);
            scrollToBottom();
        }

        function showTypingIndicator() {
            const indicator = document.createElement('div');
            indicator.className = 'message ai';
            indicator.id = 'typingIndicator';
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = '🤖';
            
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message-bubble typing-indicator active';
            typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
            
            indicator.appendChild(avatar);
            indicator.appendChild(typingDiv);
            chatMessages.appendChild(indicator);
            scrollToBottom();
        }

        function hideTypingIndicator() {
            const indicator = document.getElementById('typingIndicator');
            if (indicator) indicator.remove();
        }

        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Event listeners
        if (sendButton) sendButton.addEventListener('click', sendMessage);
        if (chatInput) {
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        }

        // Prevent popup from closing when clicking inside
        if (chatPopup) {
            chatPopup.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    });
})();
