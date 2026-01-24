/**
 * Keyboard Navigation Hook - Full keyboard support
 * 
 * Features:
 * - Tab navigation between fields
 * - Arrow keys in dropdowns/pill groups
 * - Enter to submit form
 * - Escape to close dropdowns/modals
 * - Ctrl+S to save draft
 * - Number keys (1-7) to jump to sections
 * - Focus management
 */

import { useEffect, useCallback, useRef } from 'react';

interface UseKeyboardNavigationOptions {
  onSaveDraft?: () => void;
  onSubmit?: () => void;
  onSectionJump?: (sectionId: string) => void;
  canSubmit?: boolean;
}

export function useKeyboardNavigation({
  onSaveDraft,
  onSubmit,
  onSectionJump,
  canSubmit = false,
}: UseKeyboardNavigationOptions = {}) {
  const activeDropdownRef = useRef<HTMLElement | null>(null);
  
  // Handle global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle if user is typing in input/textarea
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        // Allow Escape to close dropdowns even when typing
        if (e.key === 'Escape') {
          closeAllDropdowns();
        }
        return;
      }
      
      // Ctrl/Cmd + S: Save draft
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        onSaveDraft?.();
        return;
      }
      
      // Enter: Submit form (only if not in input/textarea)
      if (e.key === 'Enter' && canSubmit) {
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.tagName === 'BUTTON' || activeElement.getAttribute('role') === 'button')) {
          // Let button handle it
          return;
        }
        // If focus is on CTA bar or form, submit
        if (activeElement?.closest('[data-cta-bar]') || activeElement?.closest('form')) {
          e.preventDefault();
          onSubmit?.();
          return;
        }
      }
      
      // Number keys 1-7: Jump to sections
      if (e.key >= '1' && e.key <= '7' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const sectionMap: Record<string, string> = {
          '1': 'route',
          '2': 'schedule',
          '3': 'cargo',
          '4': 'value',
          '5': 'parties',
          '6': 'modules',
          '7': 'upload',
        };
        const sectionId = sectionMap[e.key];
        if (sectionId) {
          e.preventDefault();
          onSectionJump?.(sectionId);
        }
      }
      
      // Escape: Close dropdowns/modals
      if (e.key === 'Escape') {
        closeAllDropdowns();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSaveDraft, onSubmit, onSectionJump, canSubmit]);
  
  // Close all open dropdowns
  const closeAllDropdowns = useCallback(() => {
    // Close dropdowns marked with data-dropdown-open
    const dropdowns = document.querySelectorAll('[data-dropdown-open="true"]');
    dropdowns.forEach(dropdown => {
      dropdown.setAttribute('data-dropdown-open', 'false');
      const event = new CustomEvent('closeDropdown');
      dropdown.dispatchEvent(event);
    });
    
    // Close autosuggest dropdowns
    const autosuggests = document.querySelectorAll('[data-autosuggest-open="true"]');
    autosuggests.forEach(autosuggest => {
      autosuggest.setAttribute('data-autosuggest-open', 'false');
      const event = new CustomEvent('closeAutosuggest');
      autosuggest.dispatchEvent(event);
    });
  }, []);
  
  // Focus management for sections
  const focusSection = useCallback((sectionId: string) => {
    const section = document.getElementById(`section-${sectionId}`);
    if (section) {
      // Find first focusable element
      const focusableSelectors = [
        'input:not([disabled]):not([readonly])',
        'select:not([disabled])',
        'textarea:not([disabled]):not([readonly])',
        'button:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
      ].join(', ');
      
      const firstFocusable = section.querySelector<HTMLElement>(focusableSelectors);
      if (firstFocusable) {
        firstFocusable.focus();
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else {
        // Fallback: just scroll to section
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, []);
  
  // Focus next field in form
  const focusNextField = useCallback(() => {
    const focusableSelectors = [
      'input:not([disabled]):not([readonly])',
      'select:not([disabled])',
      'textarea:not([disabled]):not([readonly])',
      'button:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');
    
    const allFocusable = Array.from(document.querySelectorAll<HTMLElement>(focusableSelectors));
    const currentIndex = allFocusable.findIndex(el => el === document.activeElement);
    
    const nextEl = allFocusable[currentIndex + 1];
    if (currentIndex >= 0 && nextEl) {
      nextEl.focus();
    }
  }, []);
  
  // Focus previous field in form
  const focusPreviousField = useCallback(() => {
    const focusableSelectors = [
      'input:not([disabled]):not([readonly])',
      'select:not([disabled])',
      'textarea:not([disabled]):not([readonly])',
      'button:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');
    
    const allFocusable = Array.from(document.querySelectorAll<HTMLElement>(focusableSelectors));
    const currentIndex = allFocusable.findIndex(el => el === document.activeElement);
    
    const prevEl = allFocusable[currentIndex - 1];
    if (currentIndex > 0 && prevEl) {
      prevEl.focus();
    }
  }, []);
  
  return {
    focusSection,
    focusNextField,
    focusPreviousField,
    closeAllDropdowns,
  };
}
