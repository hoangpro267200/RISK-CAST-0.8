import { useState, useCallback, createContext, useContext, ReactNode } from 'react';

const STORAGE_KEY = 'riskcast_ai_dock_state';

interface AiDockState {
  isOpen: boolean;
  isMinimized: boolean;
}

interface AiDockContextValue {
  isOpen: boolean;
  isMinimized: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  minimize: () => void;
  maximize: () => void;
}

function getStoredState(): AiDockState {
  if (typeof window === 'undefined') {
    return { isOpen: false, isMinimized: false };
  }
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    // ignore
  }
  return { isOpen: false, isMinimized: false };
}

function saveState(state: AiDockState) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

// Create context with default value
const defaultValue: AiDockContextValue = {
  isOpen: false,
  isMinimized: false,
  open: () => {},
  close: () => {},
  toggle: () => {},
  minimize: () => {},
  maximize: () => {},
};

const AiDockContext = createContext<AiDockContextValue>(defaultValue);

/**
 * Provider component - wrap around components that need AI dock state
 */
export function AiDockProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AiDockState>(() => getStoredState());

  const open = useCallback(() => {
    const newState = { isOpen: true, isMinimized: false };
    saveState(newState);
    setState(newState);
  }, []);

  const close = useCallback(() => {
    const newState = { isOpen: false, isMinimized: false };
    saveState(newState);
    setState(newState);
  }, []);

  const toggle = useCallback(() => {
    setState(prev => {
      const newState = { isOpen: !prev.isOpen, isMinimized: false };
      saveState(newState);
      return newState;
    });
  }, []);

  const minimize = useCallback(() => {
    setState(prev => {
      const newState = { ...prev, isMinimized: true };
      saveState(newState);
      return newState;
    });
  }, []);

  const maximize = useCallback(() => {
    setState(prev => {
      const newState = { ...prev, isMinimized: false };
      saveState(newState);
      return newState;
    });
  }, []);

  const value: AiDockContextValue = {
    isOpen: state.isOpen,
    isMinimized: state.isMinimized,
    open,
    close,
    toggle,
    minimize,
    maximize,
  };

  return (
    <AiDockContext.Provider value={value}>
      {children}
    </AiDockContext.Provider>
  );
}

/**
 * Hook to access AI dock state
 */
export function useAiDockState(_initialOpen = false) {
  return useContext(AiDockContext);
}
