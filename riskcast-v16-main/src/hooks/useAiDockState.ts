import { useState, useEffect } from 'react';

const STORAGE_KEY = 'riskcast_ai_dock_state';

interface AiDockState {
  isOpen: boolean;
  isMinimized: boolean;
}

/**
 * Hook to manage AI Advisor dock state with localStorage persistence
 * 
 * Features:
 * - Persists open/closed state across sessions
 * - Handles responsive breakpoints (desktop: dock, mobile: bottom sheet)
 * - Provides smooth state transitions
 */
export function useAiDockState(initialOpen = false) {
  const [state, setState] = useState<AiDockState>(() => {
    // Load from localStorage on mount
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          return {
            isOpen: parsed.isOpen ?? initialOpen,
            isMinimized: parsed.isMinimized ?? false,
          };
        }
      } catch (e) {
        console.warn('[useAiDockState] Failed to load saved state:', e);
      }
    }
    return {
      isOpen: initialOpen,
      isMinimized: false,
    };
  });

  // Save to localStorage whenever state changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      } catch (e) {
        console.warn('[useAiDockState] Failed to save state:', e);
      }
    }
  }, [state]);

  const open = () => {
    setState(prev => ({ ...prev, isOpen: true, isMinimized: false }));
  };

  const close = () => {
    setState(prev => ({ ...prev, isOpen: false, isMinimized: false }));
  };

  const toggle = () => {
    setState(prev => ({
      ...prev,
      isOpen: !prev.isOpen,
      isMinimized: prev.isOpen ? false : prev.isMinimized,
    }));
  };

  const minimize = () => {
    setState(prev => ({ ...prev, isMinimized: true }));
  };

  const maximize = () => {
    setState(prev => ({ ...prev, isMinimized: false }));
  };

  return {
    isOpen: state.isOpen,
    isMinimized: state.isMinimized,
    open,
    close,
    toggle,
    minimize,
    maximize,
  };
}
