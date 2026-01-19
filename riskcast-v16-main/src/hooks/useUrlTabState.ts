/**
 * useUrlTabState Hook
 * 
 * Syncs tab state with URL query parameters.
 * - Reads initial tab from URL on mount
 * - Updates URL on tab change (using replaceState, no reload)
 * - Supports default fallback tab
 */

import { useState, useCallback, useEffect } from 'react';

export interface UseUrlTabStateOptions<T extends string> {
  /** URL query parameter name (default: 'tab') */
  paramName?: string;
  /** Default tab if URL param missing */
  defaultTab: T;
  /** Valid tab values */
  validTabs: readonly T[];
}

export interface UseUrlTabStateReturn<T extends string> {
  /** Current active tab */
  activeTab: T;
  /** Set active tab (also updates URL) */
  setActiveTab: (tab: T) => void;
  /** Check if a tab is active */
  isActive: (tab: T) => boolean;
}

/**
 * Hook to sync tab state with URL
 * 
 * @example
 * ```tsx
 * const { activeTab, setActiveTab } = useUrlTabState({
 *   defaultTab: 'overview',
 *   validTabs: ['overview', 'analytics', 'decisions'] as const
 * });
 * ```
 */
export function useUrlTabState<T extends string>(
  options: UseUrlTabStateOptions<T>
): UseUrlTabStateReturn<T> {
  const { paramName = 'tab', defaultTab, validTabs } = options;

  // Read initial tab from URL
  const getTabFromUrl = useCallback((): T => {
    if (typeof window === 'undefined') return defaultTab;
    
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get(paramName);
    
    if (tabParam && validTabs.includes(tabParam as T)) {
      return tabParam as T;
    }
    
    return defaultTab;
  }, [paramName, defaultTab, validTabs]);

  const [activeTab, setActiveTabState] = useState<T>(getTabFromUrl);

  // Update URL when tab changes
  const setActiveTab = useCallback((tab: T) => {
    if (!validTabs.includes(tab)) {
      console.warn(`[useUrlTabState] Invalid tab: ${tab}`);
      return;
    }

    setActiveTabState(tab);

    // Update URL without reload
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set(paramName, tab);
      window.history.replaceState({}, '', url.toString());
    }
  }, [paramName, validTabs]);

  // Check if tab is active
  const isActive = useCallback((tab: T): boolean => {
    return activeTab === tab;
  }, [activeTab]);

  // Listen for popstate (browser back/forward)
  useEffect(() => {
    const handlePopState = () => {
      const newTab = getTabFromUrl();
      setActiveTabState(newTab);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [getTabFromUrl]);

  // Set initial URL if tab param missing
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const params = new URLSearchParams(window.location.search);
    if (!params.has(paramName)) {
      const url = new URL(window.location.href);
      url.searchParams.set(paramName, activeTab);
      window.history.replaceState({}, '', url.toString());
    }
  }, [paramName, activeTab]);

  return {
    activeTab,
    setActiveTab,
    isActive
  };
}

export default useUrlTabState;
