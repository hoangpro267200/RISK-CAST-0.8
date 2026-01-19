/**
 * Autosave Hook - Debounced autosave with localStorage
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { InputFormState } from './useFormState';

export function useAutosave(formState: InputFormState) {
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  
  const saveDraft = useCallback(async () => {
    setIsSaving(true);
    
    try {
      // Save to localStorage
      localStorage.setItem('RISKCAST_DRAFT', JSON.stringify(formState));
      localStorage.setItem('RISKCAST_DRAFT_TIMESTAMP', new Date().toISOString());
      
      // Optionally save to backend
      // await fetch('/api/drafts', { method: 'POST', body: JSON.stringify(formState) });
      
      setLastSaved(new Date());
    } catch (error) {
      console.error('Autosave failed:', error);
    } finally {
      setIsSaving(false);
    }
  }, [formState]);
  
  // Debounced autosave on form state change
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    
    debounceTimer.current = setTimeout(() => {
      saveDraft();
    }, 1000); // 1 second debounce
    
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [formState, saveDraft]);
  
  // Load last saved timestamp on mount
  useEffect(() => {
    const timestamp = localStorage.getItem('RISKCAST_DRAFT_TIMESTAMP');
    if (timestamp) {
      setLastSaved(new Date(timestamp));
    }
  }, []);
  
  return {
    isSaving,
    lastSaved,
    saveDraft,
  };
}
