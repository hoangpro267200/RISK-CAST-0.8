/**
 * AI Advisor Dock Component
 * 
 * Premium dock pattern for AI chat:
 * - Desktop: Right dock slide-in panel (360-420px width)
 * - Mobile: Bottom sheet (60-80% height)
 * - Trigger button in header (not floating)
 * - No overlap with footer actions
 */

import { useState, useEffect, useRef } from 'react';
import { Send, X, Bot, Sparkles, MessageCircle } from 'lucide-react';
import { useAiDockState } from '../hooks/useAiDockState';
import React from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface AiAdvisorDockProps {
  sessionId?: string;
  context?: {
    page?: string;
    shipmentId?: string;
    riskScore?: number;
    expectedLoss?: number;
  };
  onClose?: () => void;
}

/**
 * AI Advisor Trigger Button (for header)
 */
export function AiAdvisorTrigger() {
  const { isOpen, toggle } = useAiDockState();
  
  return (
    <button
      onClick={toggle}
      className="px-3 py-2 border border-white/20 rounded-lg text-white/70 hover:text-white hover:border-white/40 transition-all flex items-center gap-2 text-sm"
      aria-label="Open AI Advisor"
    >
      <MessageCircle className="w-4 h-4" />
      <span className="hidden sm:inline">AI Advisor</span>
      {isOpen && (
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
      )}
    </button>
  );
}

/**
 * AI Advisor Dock Panel
 */
export function AiAdvisorDock({ sessionId, context, onClose }: AiAdvisorDockProps) {
  const { isOpen, close, isMinimized } = useAiDockState();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEnabled, setIsEnabled] = useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [currentSessionId] = useState(sessionId || `session-${Date.now()}`);

  // Check Claude status
  const checkClaudeStatus = async () => {
    try {
      setIsCheckingStatus(true);
      const response = await fetch('/api/v1/advisor/status');
      const data = await response.json();
      
      if (data.status === 'success' && data.data) {
        setIsEnabled(data.data.llm === true);
      } else {
        setIsEnabled(false);
      }
    } catch (error) {
      console.error('[AiAdvisorDock] Error checking status:', error);
      setIsEnabled(false);
    } finally {
      setIsCheckingStatus(false);
    }
  };

  useEffect(() => {
    checkClaudeStatus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen && isEnabled) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [isOpen, isEnabled]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !isEnabled) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    const newUserMessage: Message = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await fetch('/api/v1/advisor/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: currentSessionId,
          context: context,
          options: { language: 'vi', include_actions: true }
        })
      });

      if (!response.ok) {
        setIsEnabled(false);
        await checkClaudeStatus();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'AI Advisor is in Limited Mode. Configure Claude API key to enable full capabilities.',
          timestamp: new Date().toISOString()
        }]);
        return;
      }

      const data = await response.json();
      if (data.status === 'success' && data.data) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.data.response || data.data.message || 'No response',
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      console.error('[AiAdvisorDock] Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error connecting to AI Advisor. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Don't render if closed
  if (!isOpen) {
    return null;
  }

  // Responsive: Desktop = dock, Mobile = bottom sheet
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < 768;
  });

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <>
      {/* Overlay (mobile only) */}
      {isMobile && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] transition-opacity"
          onClick={close}
        />
      )}

      {/* Dock Panel */}
      <div
        className={`
          fixed z-[101] bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 
          border border-slate-700/50 shadow-2xl flex flex-col backdrop-blur-xl
          transition-all duration-300 ease-out
          ${isMobile
            ? 'bottom-0 left-0 right-0 h-[70vh] max-h-[600px] rounded-t-2xl'
            : 'top-0 right-0 h-full w-[420px] max-w-[90vw] border-l border-slate-700/50'
          }
          ${isOpen ? (isMobile ? 'translate-y-0' : 'translate-x-0') : (isMobile ? 'translate-y-full' : 'translate-x-full')}
        `}
        style={{
          // Ensure it doesn't overlap with header (z-100) or footer status bar
          top: isMobile ? 'auto' : '0',
          bottom: isMobile ? '0' : 'auto',
        }}
      >
        {/* Header */}
        <div className="relative bg-gradient-to-r from-slate-800 via-slate-800/95 to-slate-800 border-b border-slate-700/50 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Bot size={20} className="text-white" />
              </div>
              {isEnabled && (
                <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-green-400 rounded-full border-2 border-slate-800 animate-pulse shadow-lg" />
              )}
            </div>
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
          <button
            onClick={close}
            className="text-slate-400 hover:text-white hover:bg-red-500/20 rounded-lg p-2 transition-all"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Messages */}
        <div className="relative flex-1 overflow-y-auto p-5 space-y-4">
          {messages.length === 0 && isEnabled && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500/20 to-indigo-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4 backdrop-blur-sm border border-blue-500/20">
                <Bot size={32} className="text-blue-400" />
              </div>
              <p className="text-base text-white font-semibold mb-2">👋 Xin chào!</p>
              <p className="text-sm text-slate-400 mb-4">Tôi là AI Risk Advisor của bạn.</p>
              <p className="text-xs text-slate-500">Ask AI to validate fields / suggest risk mitigations...</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {msg.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                  <Bot size={16} className="text-white" />
                </div>
              )}
              <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                  : 'bg-slate-700/80 backdrop-blur-sm text-slate-100 border border-slate-600/50'
              }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              </div>
              {msg.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xs font-semibold">U</span>
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
              <div className="bg-slate-700/80 backdrop-blur-sm border border-slate-600/50 rounded-2xl px-4 py-3">
                <div className="flex gap-1.5 items-center">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-slate-700/50 bg-slate-800/50 backdrop-blur-sm p-4">
          <div className="flex gap-3 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isEnabled ? "Nhập câu hỏi của bạn..." : "Đang tải..."}
              className="flex-1 bg-slate-700/50 backdrop-blur-sm text-white placeholder-slate-400 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 border border-slate-600/50 disabled:opacity-50"
              rows={1}
              style={{ maxHeight: '120px' }}
              disabled={isLoading || !isEnabled || isCheckingStatus}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading || !isEnabled || isCheckingStatus}
              className={`flex-shrink-0 rounded-xl p-3 transition-all ${
                !input.trim() || isLoading || !isEnabled || isCheckingStatus
                  ? 'bg-slate-600/50 text-slate-400 cursor-not-allowed'
                  : 'bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white hover:scale-105'
              }`}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
