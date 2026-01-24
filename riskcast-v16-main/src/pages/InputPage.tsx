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

import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { designTokens } from '@/ui/design-tokens';
import type { DomainCase } from '@/domain/case.schema';
import { mapInputFormToDomainCase } from '@/domain/case.mapper';
import { validateDomainCase } from '@/domain/case.validation';
import { saveDomainCaseToStorage } from '@/domain/case.migrate';

// Components
import { InputPageLayout } from './input/InputPageLayout';
import { InputFormPanel } from './input/InputFormPanel';
import { PreviewPanel } from './input/PreviewPanel';
import { StickyCTABar } from './input/StickyCTABar';
import { InputSidebar } from './input/InputSidebar';
import { Toast, ToastContainer } from './input/components/Toast';
import { KeyboardShortcutsHelp } from './input/components/KeyboardShortcutsHelp';
import { LoadingOverlay } from './input/components/LoadingOverlay';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { shouldProtectRoute } from '../config/auth';

// Hooks
import { useAutosave } from './input/hooks/useAutosave';
import { useFormState } from './input/hooks/useFormState';
import { useCompleteness } from './input/hooks/useCompleteness';
import { useValidation } from './input/hooks/useValidation';
import { useToast } from './input/hooks/useToast';
import { useKeyboardNavigation } from './input/hooks/useKeyboardNavigation';

function InputPageContent() {
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
  
  // Validation
  const {
    errors,
    validateForm,
    getFieldError,
    markFieldTouched,
    isValid,
  } = useValidation(formState);
  
  // Toast notifications
  const { toasts, success, error: showError, removeToast } = useToast();
  
  // Mode toggle (Basic/Advanced)
  const [mode, setMode] = useState<'basic' | 'advanced'>('basic');
  
  // Active section for navigation
  const [activeSection, setActiveSection] = useState<string>('route');
  
  // Loading state (for initial data fetch and submission)
  const [isInitialLoading, setIsInitialLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
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
  
  // Form submission handler - create function directly without any hooks to avoid TDZ
  // This function is recreated on every render but that's fine for event handlers
  async function handleSubmitWithLoading() {
    setIsSubmitting(true);
    try {
      // Validate form
      const validationResult = validateForm();
      
      if (!validationResult.isValid) {
        showError(`Please fix ${validationResult.errors.length} error(s) before submitting`);
        setIsSubmitting(false);
        return;
      }
      
      // Map to DomainCase
      const domainCase = mapInputFormToDomainCase(formState as Record<string, unknown>);
      
      // Validate with domain schema
      const domainValidation = validateDomainCase(domainCase);
      
      if (!domainValidation.valid) {
        showError('Form validation failed. Please check all required fields.');
        setIsSubmitting(false);
        return;
      }
      
      // Save to canonical storage (single source of truth)
      // Also save to legacy key for backward compatibility during transition
      saveDomainCaseToStorage(domainCase);
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
          success('Analysis submitted successfully! Redirecting...');
          setTimeout(() => {
            window.location.href = '/overview';
          }, 1500);
        } else {
          throw new Error('Submission failed');
        }
      } catch (err) {
        console.error('Submit error:', err);
        showError('Unable to submit. Please try again.');
        setIsSubmitting(false);
      }
    } catch (err) {
      console.error('Submit error:', err);
      showError('Unable to submit. Please try again.');
      setIsSubmitting(false);
    } finally {
      // Keep loading state for redirect delay
      setTimeout(() => {
        setIsSubmitting(false);
      }, 2000);
    }
  }
  
  // Stable callbacks for keyboard navigation - defined AFTER all handlers
  const handleKeyboardSubmit = useCallback(() => {
    handleSubmitWithLoading();
  }, [handleSubmitWithLoading]);
  
  const handleKeyboardSaveDraft = useCallback(() => {
    saveDraft();
    success('Draft saved');
  }, [saveDraft, success]);
  
  const handleKeyboardSectionJump = useCallback((sectionId: string) => {
    setActiveSection(sectionId);
  }, []);
  
  // Stable callback for CTA bar submit
  const handleCTASubmit = useCallback(() => {
    handleSubmitWithLoading();
  }, [handleSubmitWithLoading]);
  
  // Keyboard navigation - use stable callbacks (called AFTER all handlers are defined)
  const { focusSection } = useKeyboardNavigation({
    onSaveDraft: handleKeyboardSaveDraft,
    onSubmit: handleKeyboardSubmit,
    onSectionJump: handleKeyboardSectionJump,
    canSubmit: completeness === 100,
  });
  
  // Handle save draft keyboard shortcut
  useEffect(() => {
    const handleSaveDraft = () => {
      saveDraft();
      success('Draft saved');
    };
    
    window.addEventListener('saveDraft', handleSaveDraft as EventListener);
    return () => window.removeEventListener('saveDraft', handleSaveDraft as EventListener);
  }, [saveDraft, success]);
  
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
    <>
    {isSubmitting && (
      <LoadingOverlay
        fullPage
        message="Submitting analysis..."
        transparent
      />
    )}
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
          getFieldError={getFieldError}
          markFieldTouched={markFieldTouched}
        />
      }
      previewPanel={
        <PreviewPanel
          data={previewData}
          completeness={completeness}
          completedFields={completedFields}
          missingFields={missingFields}
          isLoading={isInitialLoading}
        />
      }
      ctaBar={
        <StickyCTABar
          completeness={completeness}
          completedCount={completedFields.length}
          requiredCount={requiredFieldsCount}
          isSaving={isSaving}
          onSaveDraft={saveDraft}
          onSubmit={handleCTASubmit}
          canSubmit={completeness === 100 && !isSubmitting}
          isSubmitting={isSubmitting}
        />
      }
    />
    <ToastContainer>
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          id={toast.id}
          type={toast.type}
          message={toast.message}
          duration={toast.duration}
          onClose={removeToast}
        />
      ))}
    </ToastContainer>
    <KeyboardShortcutsHelp />
  </>
  );
}

export default function InputPage() {
  const needsProtection = shouldProtectRoute('/input_react');
  
  if (needsProtection) {
    return (
      <ProtectedRoute>
        <InputPageContent />
      </ProtectedRoute>
    );
  }
  
  return <InputPageContent />;
}
