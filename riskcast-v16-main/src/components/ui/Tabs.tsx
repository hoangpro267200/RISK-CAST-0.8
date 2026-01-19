/**
 * Tabs Component
 * 
 * Enterprise tab navigation with URL sync support.
 * - Keyboard accessible (arrow keys, Home/End)
 * - Responsive (scrollable on mobile)
 * - Focus visible states
 */

import React, { useRef, useCallback, KeyboardEvent } from 'react';

export interface Tab<T extends string = string> {
  id: T;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
  disabled?: boolean;
}

export interface TabsProps<T extends string = string> {
  tabs: Tab<T>[];
  activeTab: T;
  onTabChange: (tab: T) => void;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Visual variant */
  variant?: 'default' | 'pills' | 'underline';
  /** Full width tabs */
  fullWidth?: boolean;
  className?: string;
}

export function Tabs<T extends string = string>({
  tabs,
  activeTab,
  onTabChange,
  size = 'md',
  variant = 'default',
  fullWidth = false,
  className = ''
}: TabsProps<T>) {
  const tabsRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLButtonElement>, currentIndex: number) => {
    const enabledTabs = tabs.filter(t => !t.disabled);
    const currentTab = tabs[currentIndex];
    if (!currentTab) return;
    const currentEnabledIndex = enabledTabs.findIndex(t => t.id === currentTab.id);

    let newIndex = -1;

    switch (e.key) {
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        newIndex = currentEnabledIndex > 0 
          ? currentEnabledIndex - 1 
          : enabledTabs.length - 1;
        break;
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault();
        newIndex = currentEnabledIndex < enabledTabs.length - 1 
          ? currentEnabledIndex + 1 
          : 0;
        break;
      case 'Home':
        e.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        newIndex = enabledTabs.length - 1;
        break;
    }

    const targetTab = enabledTabs[newIndex];
    if (newIndex >= 0 && targetTab) {
      onTabChange(targetTab.id);
      // Focus the new tab button
      const buttons = tabsRef.current?.querySelectorAll('[role="tab"]');
      const targetButton = Array.from(buttons || []).find(
        btn => btn.getAttribute('data-tab-id') === targetTab.id
      ) as HTMLButtonElement | undefined;
      targetButton?.focus();
    }
  }, [tabs, onTabChange]);

  const containerClasses = variant === 'default'
    ? 'bg-white/5 rounded-xl p-1 border border-white/10'
    : variant === 'pills'
      ? 'gap-2'
      : 'border-b border-white/10';

  const getTabClasses = (tab: Tab<T>, isActive: boolean) => {
    const base = `${sizeClasses[size]} font-medium transition-all flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900`;
    
    if (tab.disabled) {
      return `${base} text-white/30 cursor-not-allowed`;
    }

    if (variant === 'default') {
      return isActive
        ? `${base} bg-white/10 text-white rounded-lg`
        : `${base} text-white/50 hover:text-white/80 rounded-lg`;
    }

    if (variant === 'pills') {
      return isActive
        ? `${base} bg-blue-500/20 text-blue-400 border border-blue-500/40 rounded-full`
        : `${base} text-white/50 hover:text-white/80 hover:bg-white/5 border border-transparent rounded-full`;
    }

    // underline variant
    return isActive
      ? `${base} text-white border-b-2 border-blue-500 -mb-px`
      : `${base} text-white/50 hover:text-white/80 border-b-2 border-transparent -mb-px`;
  };

  return (
    <div 
      ref={tabsRef}
      role="tablist"
      aria-orientation="horizontal"
      className={`
        flex ${containerClasses}
        ${fullWidth ? 'w-full' : 'w-fit'}
        overflow-x-auto scrollbar-thin
        scroll-x-mobile
        ${className}
      `}
    >
      {tabs.map((tab, index) => (
        <button
          key={tab.id}
          role="tab"
          id={`tab-${tab.id}`}
          aria-selected={activeTab === tab.id}
          aria-controls={`tabpanel-${tab.id}`}
          aria-disabled={tab.disabled}
          tabIndex={activeTab === tab.id ? 0 : -1}
          data-tab-id={tab.id}
          onClick={() => !tab.disabled && onTabChange(tab.id)}
          onKeyDown={(e) => handleKeyDown(e, index)}
          className={`
            ${getTabClasses(tab, activeTab === tab.id)}
            ${fullWidth ? 'flex-1 justify-center' : ''}
            whitespace-nowrap
          `}
        >
          {tab.icon}
          <span>{tab.label}</span>
          {tab.badge !== undefined && (
            <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/10">
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

export default Tabs;
