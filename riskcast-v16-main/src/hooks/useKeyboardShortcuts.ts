/**
 * useKeyboardShortcuts Hook
 * 
 * Global keyboard shortcuts for power users.
 * - Tab switching: 1, 2, 3
 * - Refresh: R
 * - Command palette: / or Cmd+K
 * - Escape: Close modals/panels
 */

import { useEffect, useCallback, useRef } from 'react';

export interface KeyboardShortcut {
  /** Key(s) to trigger - can be single key or with modifier */
  key: string;
  /** Modifier keys required */
  modifiers?: {
    ctrl?: boolean;
    alt?: boolean;
    shift?: boolean;
    meta?: boolean;
  };
  /** Handler function */
  handler: () => void;
  /** Description for help menu */
  description?: string;
  /** Prevent default browser behavior */
  preventDefault?: boolean;
  /** Only trigger when no input is focused */
  ignoreInputs?: boolean;
}

export interface UseKeyboardShortcutsOptions {
  /** Enable or disable all shortcuts */
  enabled?: boolean;
  /** Shortcuts configuration */
  shortcuts: KeyboardShortcut[];
}

/**
 * Check if an element is an input type
 */
function isInputElement(element: Element | null): boolean {
  if (!element) return false;
  const tagName = element.tagName.toLowerCase();
  return (
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'select' ||
    (element as HTMLElement).isContentEditable
  );
}

/**
 * Hook for keyboard shortcuts
 */
export function useKeyboardShortcuts(options: UseKeyboardShortcutsOptions) {
  const { enabled = true, shortcuts } = options;
  const shortcutsRef = useRef(shortcuts);
  
  // Update ref when shortcuts change
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return;

    const activeElement = document.activeElement;
    
    for (const shortcut of shortcutsRef.current) {
      // Check modifiers
      const modifiers = shortcut.modifiers || {};
      const ctrlMatch = !!modifiers.ctrl === (event.ctrlKey || event.metaKey);
      const altMatch = !!modifiers.alt === event.altKey;
      const shiftMatch = !!modifiers.shift === event.shiftKey;
      const metaMatch = !!modifiers.meta === event.metaKey;

      // Check key
      const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();

      if (keyMatch && ctrlMatch && altMatch && shiftMatch && metaMatch) {
        // Check if should ignore when input is focused
        if (shortcut.ignoreInputs !== false && isInputElement(activeElement)) {
          continue;
        }

        if (shortcut.preventDefault !== false) {
          event.preventDefault();
        }
        
        shortcut.handler();
        return;
      }
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enabled, handleKeyDown]);
}

/**
 * Pre-built shortcuts for Results page
 */
export interface ResultsShortcutsHandlers {
  onTabOverview: () => void;
  onTabAnalytics: () => void;
  onTabDecisions: () => void;
  onRefresh: () => void;
  onToggleCommandPalette: () => void;
  onExport?: () => void;
  onEscape?: () => void;
}

export function useResultsKeyboardShortcuts(
  handlers: ResultsShortcutsHandlers,
  enabled = true
) {
  const shortcuts: KeyboardShortcut[] = [
    {
      key: '1',
      handler: handlers.onTabOverview,
      description: 'Go to Overview tab',
      ignoreInputs: true
    },
    {
      key: '2',
      handler: handlers.onTabAnalytics,
      description: 'Go to Analytics tab',
      ignoreInputs: true
    },
    {
      key: '3',
      handler: handlers.onTabDecisions,
      description: 'Go to Decisions tab',
      ignoreInputs: true
    },
    {
      key: 'r',
      handler: handlers.onRefresh,
      description: 'Refresh data',
      ignoreInputs: true
    },
    {
      key: '/',
      handler: handlers.onToggleCommandPalette,
      description: 'Open command palette / AI Advisor',
      ignoreInputs: true
    },
    {
      key: 'k',
      modifiers: { ctrl: true },
      handler: handlers.onToggleCommandPalette,
      description: 'Open command palette / AI Advisor',
      ignoreInputs: false
    }
  ];

  if (handlers.onExport) {
    shortcuts.push({
      key: 'e',
      modifiers: { ctrl: true },
      handler: handlers.onExport,
      description: 'Export results',
      ignoreInputs: false
    });
  }

  if (handlers.onEscape) {
    shortcuts.push({
      key: 'Escape',
      handler: handlers.onEscape,
      description: 'Close panel/modal',
      ignoreInputs: false,
      preventDefault: false
    });
  }

  useKeyboardShortcuts({ enabled, shortcuts });

  return shortcuts;
}

export default useKeyboardShortcuts;
