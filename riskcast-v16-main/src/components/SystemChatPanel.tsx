/**
 * System Chat Panel Component
 * AI Advisor chat interface for RISKCAST
 */

import { useState, useEffect, useRef } from 'react';
import { Send, X, Minimize2, Maximize2, Download, FileText, TrendingUp, BarChart3, MessageCircle, Bot, Sparkles } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  actions?: ActionSuggestion[];
  functionCalls?: any[];
}

interface ActionSuggestion {
  type: 'suggestion' | 'required';
  action: string;
  label: string;
  description: string;
  parameters?: Record<string, any>;
}

interface SystemChatPanelProps {
  sessionId?: string;
  context?: {
    page?: string;
    shipmentId?: string;
    riskScore?: number;
    expectedLoss?: number;
  };
  onClose?: () => void;
}

export function SystemChatPanel({ sessionId, context, onClose }: SystemChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(true); // Start minimized to show button
  const [currentSessionId, setCurrentSessionId] = useState(sessionId || `session-${Date.now()}`);
  const [isEnabled, setIsEnabled] = useState(false); // Claude API enabled state
  const [isCheckingStatus, setIsCheckingStatus] = useState(true); // Initial status check
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Check Claude configuration status on mount and after errors
  const checkClaudeStatus = async () => {
    try {
      setIsCheckingStatus(true);
      const response = await fetch('/api/v1/advisor/status');
      const data = await response.json();
      
      if (data.status === 'success' && data.data) {
        const llmAvailable = data.data.llm === true;
        setIsEnabled(llmAvailable);
        
        if (!llmAvailable) {
          console.log('[SystemChatPanel] LLM not available - Limited Mode');
        }
      } else {
        setIsEnabled(false);
      }
    } catch (error) {
      console.error('[SystemChatPanel] Error checking Claude status:', error);
      setIsEnabled(false);
    } finally {
      setIsCheckingStatus(false);
    }
  };

  useEffect(() => {
    checkClaudeStatus();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (!isMinimized && isEnabled) {
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [isMinimized, isEnabled]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !isEnabled) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message
    const newUserMessage: Message = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await fetch('/api/v1/advisor/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: currentSessionId,
          context: context,
          options: {
            language: 'vi',
            include_actions: true
          }
        })
      });

      if (!response.ok) {
        // Handle HTTP errors - switch to Limited Mode
        setIsEnabled(false);
        await checkClaudeStatus(); // Re-check status
        
        const errorMessage: Message = {
          role: 'assistant',
          content: `AI Advisor is in Limited Mode. Configure Claude API key to enable full capabilities.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }

      let data;
      try {
        data = await response.json();
      } catch (parseError) {
        console.error('[SystemChatPanel] Failed to parse response:', parseError);
        
        // Switch to Limited Mode on parse error
        setIsEnabled(false);
        await checkClaudeStatus(); // Re-check status
        
        const errorMessage: Message = {
          role: 'assistant',
          content: `AI Advisor is in Limited Mode. Configure Claude API key to enable full capabilities.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }

      if (data.status === 'success' && data.data) {
        const reply = data.data.reply || '';
        
        // Check if response is empty or indicates model error
        const metadata = data.data.metadata || {};
        const isModelError = metadata.model === 'deterministic' || 
                           metadata.error?.toLowerCase().includes('model') ||
                           metadata.error?.toLowerCase().includes('not_found') ||
                           metadata.error?.toLowerCase().includes('404');
        
        if (isModelError || !reply.trim()) {
          // Model error detected - switch to Limited Mode
          setIsEnabled(false);
          await checkClaudeStatus(); // Re-check status
          
          const errorMessage: Message = {
            role: 'assistant',
            content: `AI Advisor is in Limited Mode. Configure Claude API key to enable full capabilities.`,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMessage]);
          return;
        }
        
        const assistantMessage: Message = {
          role: 'assistant',
          content: reply,
          timestamp: new Date().toISOString(),
          actions: data.data.actions || [],
          functionCalls: data.data.function_calls || []
        };
        setMessages(prev => [...prev, assistantMessage]);

        // Update session ID if returned
        if (data.data.session_id) {
          setCurrentSessionId(data.data.session_id);
        }
      } else if (data.status === 'error') {
        // Error response from API - check if it's LLM unavailable
        const errorCode = data.error?.code || '';
        const isLLMError = errorCode === 'LLM_UNAVAILABLE' || 
                          errorCode === 'INTERNAL_ERROR' ||
                          data.error?.message?.toLowerCase().includes('model') ||
                          data.error?.message?.toLowerCase().includes('not available');
        
        if (isLLMError) {
          // Switch to Limited Mode
          setIsEnabled(false);
          await checkClaudeStatus(); // Re-check status
        }
        
        const errorMessage: Message = {
          role: 'assistant',
          content: `AI Advisor is in Limited Mode. Configure Claude API key to enable full capabilities.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
      } else {
        // Unknown response format - switch to Limited Mode
        setIsEnabled(false);
        await checkClaudeStatus(); // Re-check status
        
        const errorMessage: Message = {
          role: 'assistant',
          content: `AI Advisor is in Limited Mode. Configure Claude API key to enable full capabilities.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('[SystemChatPanel] Error sending message:', error);
      
      // Switch to Limited Mode on error
      setIsEnabled(false);
      await checkClaudeStatus(); // Re-check status
      
      const errorMessage: Message = {
        role: 'assistant',
        content: `AI Advisor is in Limited Mode. Configure Claude API key to enable full capabilities.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAction = async (action: ActionSuggestion) => {
    if (action.action === 'export_pdf') {
      try {
        const response = await fetch('/api/v1/advisor/actions/export_pdf', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: currentSessionId,
            parameters: action.parameters || {}
          })
        });

        const data = await response.json();
        if (data.status === 'success' && data.data?.result?.file_url) {
          // Open download link
          window.open(data.data.result.file_url, '_blank');
          
          // Add message
          const actionMessage: Message = {
            role: 'assistant',
            content: `PDF report generated! Download it from the link above.`,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, actionMessage]);
        }
      } catch (error) {
        console.error('Action execution error:', error);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsMinimized(false)}
          className="group relative bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600 hover:from-blue-400 hover:via-blue-500 hover:to-indigo-500 text-white rounded-2xl p-4 shadow-2xl shadow-blue-500/50 hover:shadow-blue-500/70 transition-all duration-300 hover:scale-110 active:scale-95 flex items-center gap-3 pr-6"
          title="Mở AI Advisor Chat"
        >
          {/* Animated background glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-2xl opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-300"></div>
          
          {/* Chat icon with animation */}
          <div className="relative bg-white/20 backdrop-blur-sm rounded-xl p-2.5 group-hover:bg-white/30 transition-all duration-300">
            <MessageCircle size={24} className="relative z-10" />
            {isEnabled && (
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-blue-600 animate-pulse"></div>
            )}
          </div>
          
          {/* Text label */}
          <div className="relative z-10 text-left">
            <div className="text-sm font-semibold">AI Advisor</div>
            <div className="text-xs opacity-90">Chat với AI</div>
          </div>
          
          {/* Notification badge */}
          {messages.length > 0 && (
            <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-lg">
              {messages.length}
            </div>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-[420px] h-[680px] bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 border border-slate-700/50 rounded-2xl shadow-2xl flex flex-col z-[9999] backdrop-blur-xl overflow-hidden transition-all duration-300 ease-out">
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-indigo-500/5 pointer-events-none"></div>
      
      {/* Header with gradient */}
      <div className="relative bg-gradient-to-r from-slate-800 via-slate-800/95 to-slate-800 border-b border-slate-700/50 px-5 py-4 flex items-center justify-between rounded-t-2xl backdrop-blur-sm">
        <div className="flex items-center gap-3">
          {/* Avatar/Bot icon */}
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Bot size={20} className="text-white" />
            </div>
            {isEnabled && (
              <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-green-400 rounded-full border-2 border-slate-800 animate-pulse shadow-lg"></div>
            )}
            {!isEnabled && !isCheckingStatus && (
              <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-amber-400 rounded-full border-2 border-slate-800 shadow-lg"></div>
            )}
          </div>
          
          {/* Title and status */}
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <h3 className="text-white font-bold text-lg">AI Advisor</h3>
              {isEnabled && <Sparkles size={14} className="text-blue-400 animate-pulse" />}
            </div>
            <p className="text-xs text-slate-400">
              {isEnabled ? 'Online • Sẵn sàng trả lời' : 'Limited Mode • Đang kiểm tra...'}
            </p>
          </div>
        </div>
        
        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(true)}
            className="text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg p-2 transition-all duration-200"
            title="Thu nhỏ"
          >
            <Minimize2 size={18} />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white hover:bg-red-500/20 hover:text-red-400 rounded-lg p-2 transition-all duration-200"
              title="Đóng"
            >
              <X size={18} />
            </button>
          )}
        </div>
      </div>

      {/* Messages area with gradient scroll */}
      <div className="relative flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent">
        {/* Gradient fade at top */}
        <div className="sticky top-0 h-8 bg-gradient-to-b from-slate-800/80 via-slate-800/40 to-transparent pointer-events-none z-10 -mt-5 mb-5"></div>
        
        {/* Limited Mode Banner */}
        {!isEnabled && !isCheckingStatus && (
          <div className="bg-gradient-to-r from-amber-900/40 to-amber-800/30 border border-amber-700/50 rounded-xl px-4 py-3 mb-4 backdrop-blur-sm transition-all duration-300">
            <div className="flex items-start gap-3">
              <div className="w-5 h-5 bg-amber-500/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-amber-400 text-xs">⚠</span>
              </div>
              <div>
                <p className="text-sm text-amber-200 font-semibold mb-1">Chế độ Giới hạn</p>
                <p className="text-xs text-amber-300/80 leading-relaxed">Vui lòng cấu hình Claude API key để kích hoạt đầy đủ tính năng AI.</p>
              </div>
            </div>
          </div>
        )}

        {/* Welcome message */}
        {messages.length === 0 && isEnabled && (
          <div className="text-center py-12 transition-opacity duration-500">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500/20 to-indigo-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4 backdrop-blur-sm border border-blue-500/20">
              <Bot size={32} className="text-blue-400" />
            </div>
            <p className="text-base text-white font-semibold mb-2">👋 Xin chào!</p>
            <p className="text-sm text-slate-400 mb-4">Tôi là AI Risk Advisor của bạn.</p>
            <div className="inline-flex flex-wrap gap-2 justify-center px-4">
              <span className="text-xs bg-slate-700/50 text-slate-300 px-3 py-1.5 rounded-full border border-slate-600/50">
                💡 Hỏi về rủi ro
              </span>
              <span className="text-xs bg-slate-700/50 text-slate-300 px-3 py-1.5 rounded-full border border-slate-600/50">
                📊 Đề xuất giảm thiểu
              </span>
              <span className="text-xs bg-slate-700/50 text-slate-300 px-3 py-1.5 rounded-full border border-slate-600/50">
                📄 Xuất báo cáo
              </span>
            </div>
          </div>
        )}

        {messages.length === 0 && !isEnabled && !isCheckingStatus && (
          <div className="text-center py-12 transition-opacity duration-500">
            <div className="w-16 h-16 bg-gradient-to-br from-amber-500/20 to-amber-600/20 rounded-2xl flex items-center justify-center mx-auto mb-4 backdrop-blur-sm border border-amber-500/20">
              <Bot size={32} className="text-amber-400" />
            </div>
            <p className="text-sm text-slate-400 mb-2">AI Advisor đang ở chế độ giới hạn.</p>
            <p className="text-xs text-slate-500">Vui lòng cấu hình Claude API key.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 transition-all duration-300 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
          >
            {/* Avatar */}
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-md">
                <Bot size={16} className="text-white" />
              </div>
            )}
            
            {/* Message bubble */}
            <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} flex-1 min-w-0`}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-lg ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-tr-sm'
                    : 'bg-slate-700/80 backdrop-blur-sm text-slate-100 border border-slate-600/50 rounded-tl-sm'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                
                {/* Actions */}
                {msg.actions && msg.actions.length > 0 && (
                  <div className="mt-3 space-y-2 pt-3 border-t border-white/10">
                    {msg.actions.map((action, actionIdx) => (
                      <button
                        key={actionIdx}
                        onClick={() => handleAction(action)}
                        className={`text-xs px-3 py-2 rounded-lg w-full text-left transition-all duration-200 ${
                          msg.role === 'user'
                            ? 'bg-white/20 hover:bg-white/30 text-white'
                            : 'bg-slate-600/50 hover:bg-slate-600 text-slate-200 border border-slate-500/50'
                        }`}
                      >
                        <div className="font-medium">{action.label}</div>
                        {action.description && (
                          <div className="text-xs opacity-80 mt-0.5">{action.description}</div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Timestamp */}
              {msg.timestamp && (
                <span className="text-xs text-slate-500 mt-1.5 px-1">
                  {new Date(msg.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>
            
            {/* User avatar placeholder */}
            {msg.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
                <span className="text-white text-xs font-semibold">U</span>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 transition-all duration-300">
            <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-md">
              <Bot size={16} className="text-white" />
            </div>
            <div className="bg-slate-700/80 backdrop-blur-sm border border-slate-600/50 rounded-2xl rounded-tl-sm px-4 py-3 shadow-lg">
              <div className="flex gap-1.5 items-center">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
                <span className="text-xs text-slate-400 ml-2">Đang suy nghĩ...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
        
        {/* Gradient fade at bottom */}
        <div className="sticky bottom-0 h-8 bg-gradient-to-t from-slate-800/80 via-slate-800/40 to-transparent pointer-events-none mt-5 -mb-5"></div>
      </div>

      {/* Input area with gradient border */}
      <div className="relative border-t border-slate-700/50 bg-slate-800/50 backdrop-blur-sm p-4 rounded-b-2xl">
        {/* Top glow effect */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/50 to-transparent"></div>
        
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isEnabled ? "Nhập câu hỏi của bạn..." : "Đang tải..."}
              className="w-full bg-slate-700/50 backdrop-blur-sm text-white placeholder-slate-400 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 border border-slate-600/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              rows={2}
              disabled={isLoading || !isEnabled || isCheckingStatus}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading || !isEnabled || isCheckingStatus}
            className={`relative flex-shrink-0 rounded-xl p-3 transition-all duration-200 shadow-lg ${
              !input.trim() || isLoading || !isEnabled || isCheckingStatus
                ? 'bg-slate-600/50 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white hover:shadow-blue-500/50 hover:scale-105 active:scale-95'
            }`}
            title={!isEnabled ? 'Claude API key chưa được cấu hình' : 'Gửi tin nhắn (Enter)'}
          >
            <Send size={20} className={!input.trim() || isLoading || !isEnabled || isCheckingStatus ? '' : 'relative z-10'} />
            {!input.trim() || isLoading || !isEnabled || isCheckingStatus ? null : (
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-xl opacity-0 hover:opacity-100 blur-xl transition-opacity duration-300"></div>
            )}
          </button>
        </div>
        
        {/* Helper text */}
        {isEnabled && (
          <p className="text-xs text-slate-500 mt-2 px-1">Nhấn Enter để gửi • Shift+Enter để xuống dòng</p>
        )}
      </div>
    </div>
  );
}
