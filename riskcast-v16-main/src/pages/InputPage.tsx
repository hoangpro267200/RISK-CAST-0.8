/**
 * RISKCAST Input Page - Design Spec v1.0 Implementation
 * "Command Center" - Enterprise Form Experience
 * 
 * Architecture:
 * - 12-column grid with 2-column split (Form 8 cols + Preview 4 cols)
 * - Progressive disclosure (Basic/Advanced mode)
 * - Live preview panel with completeness meter
 * - Autosave with debounce
 * - Real-time validation
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { designTokens } from '@/ui/design-tokens';
import type { DomainCase } from '@/domain/case.schema';
import { mapInputFormToDomainCase } from '@/domain/case.mapper';
import { validateDomainCase } from '@/domain/case.validation';

// Components
import { InputPageLayout } from './input/InputPageLayout';
import { InputFormPanel } from './input/InputFormPanel';
import { PreviewPanel } from './input/PreviewPanel';
import { StickyCTABar } from './input/StickyCTABar';
import { InputSidebar } from './input/InputSidebar';

// Hooks
import { useAutosave } from './input/hooks/useAutosave';
import { useFormState } from './input/hooks/useFormState';
import { useCompleteness } from './input/hooks/useCompleteness';

export default function InputPage() {
  // Form state management
  const {
    formState,
    updateField,
    updateSection,
    resetForm,
    loadDraft,
  } = useFormState();
  
  // Completeness calculation
  const {
    completeness,
    completedFields,
    missingFields,
    requiredFieldsCount,
  } = useCompleteness(formState);
  
  // Autosave
  const { 
    isSaving, 
    lastSaved, 
    saveDraft 
  } = useAutosave(formState);
  
  // Mode toggle (Basic/Advanced)
  const [mode, setMode] = useState<'basic' | 'advanced'>('basic');
  
  // Active section for navigation
  const [activeSection, setActiveSection] = useState<string>('route');
  
  // Preview state (memoized for performance)
  const previewData = useMemo(() => {
    return {
      route: {
        pol: formState.route?.pol || '',
        pod: formState.route?.pod || '',
        mode: formState.route?.mode || '',
        carrier: formState.route?.carrier || '',
        transitDays: formState.schedule?.transitDays || 0,
      },
      cargo: {
        type: formState.cargo?.type || '',
        weight: formState.cargo?.grossWeight || 0,
        volume: formState.cargo?.volume || 0,
        packages: formState.cargo?.packages || 0,
        sensitivity: formState.cargo?.sensitivity || 'standard',
      },
      value: {
        insuranceValue: formState.value?.insuranceValue || 0,
        currency: formState.value?.currency || 'USD',
        incoterm: formState.value?.incoterm || '',
      },
      parties: {
        seller: formState.parties?.seller || null,
        buyer: formState.parties?.buyer || null,
      },
    };
  }, [formState]);
  
  // Handle form submission
  const handleSubmit = useCallback(async () => {
    // Validate form
    const validation = validateDomainCase(formState);
    
    if (!validation.valid) {
      // Show validation errors
      console.error('Validation errors:', validation.issues);
      return;
    }
    
    // Map to DomainCase
    const domainCase = mapInputFormToDomainCase(formState);
    
    // Save to session/localStorage
    localStorage.setItem('RISKCAST_STATE', JSON.stringify(domainCase));
    
    // Submit to backend
    try {
      const response = await fetch('/input_v20/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(domainCase),
      });
      
      if (response.ok || response.redirected) {
        // Redirect to overview/summary
        window.location.href = '/overview';
      } else {
        throw new Error('Submission failed');
      }
    } catch (error) {
      console.error('Submit error:', error);
      // Show error toast
    }
  }, [formState]);
  
  // Load draft on mount
  useEffect(() => {
    const draft = localStorage.getItem('RISKCAST_DRAFT');
    if (draft) {
      try {
        const parsed = JSON.parse(draft);
        loadDraft(parsed);
      } catch (e) {
        console.error('Failed to load draft:', e);
      }
    }
  }, [loadDraft]);
  
  return (
    <InputPageLayout
      sidebar={
        <InputSidebar
          mode={mode}
          onModeChange={setMode}
          activeSection={activeSection}
          onSectionChange={setActiveSection}
          lastSaved={lastSaved}
          onDiscard={resetForm}
        />
      }
      formPanel={
        <InputFormPanel
          formState={formState}
          onFieldChange={updateField}
          onSectionChange={updateSection}
          mode={mode}
          activeSection={activeSection}
        />
      }
      previewPanel={
        <PreviewPanel
          data={previewData}
          completeness={completeness}
          completedFields={completedFields}
          missingFields={missingFields}
        />
      }
      ctaBar={
        <StickyCTABar
          completeness={completeness}
          completedCount={completedFields.length}
          requiredCount={requiredFieldsCount}
          isSaving={isSaving}
          onSaveDraft={saveDraft}
          onSubmit={handleSubmit}
          canSubmit={completeness === 100}
        />
      }
    />
  );
}
