/**
 * Form Submit Hook - Handles form submission logic
 * Separated to avoid temporal dead zone issues
 */

import { useRef, useCallback } from 'react';
import type { InputFormState } from './useFormState';
import { mapInputFormToDomainCase } from '@/domain/case.mapper';
import { validateDomainCase } from '@/domain/case.validation';
import { saveDomainCaseToStorage } from '@/domain/case.migrate';

interface UseFormSubmitOptions {
  formState: InputFormState;
  validateForm: () => { isValid: boolean; errors: unknown[] };
  showError: (message: string) => void;
  success: (message: string) => void;
  setIsSubmitting: (value: boolean) => void;
}

export function useFormSubmit({
  formState,
  validateForm,
  showError,
  success,
  setIsSubmitting,
}: UseFormSubmitOptions) {
  // Refs to store latest values - initialize ALL refs first
  const formStateRef = useRef(formState);
  const validateFormRef = useRef(validateForm);
  const showErrorRef = useRef(showError);
  const successRef = useRef(success);
  const setIsSubmittingRef = useRef(setIsSubmitting);
  const handleSubmitRef = useRef<(() => Promise<void>) | null>(null);

  // Update refs - MUST be called on every render to get latest values
  formStateRef.current = formState;
  validateFormRef.current = validateForm;
  showErrorRef.current = showError;
  successRef.current = success;
  setIsSubmittingRef.current = setIsSubmitting;

  // Handle form submission - create function directly in ref to avoid TDZ
  // NEVER create a const named handleSubmit - only store in ref
  if (!handleSubmitRef.current) {
    handleSubmitRef.current = async () => {
      // Validate form
      const validationResult = validateFormRef.current();
      
      if (!validationResult.isValid) {
        // Show validation errors
        showErrorRef.current(`Please fix ${validationResult.errors.length} error(s) before submitting`);
        return;
      }
      
      // Map to DomainCase first (this handles the type conversion)
      const domainCase = mapInputFormToDomainCase(formStateRef.current as Record<string, unknown>);
      
      // Then validate with domain schema
      const domainValidation = validateDomainCase(domainCase);
      
      if (!domainValidation.valid) {
        showErrorRef.current('Form validation failed. Please check all required fields.');
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
          successRef.current('Analysis submitted successfully! Redirecting...');
          setTimeout(() => {
            window.location.href = '/overview';
          }, 1500);
        } else {
          throw new Error('Submission failed');
        }
      } catch (err) {
        console.error('Submit error:', err);
        showErrorRef.current('Unable to submit. Please try again.');
      }
    };
  }

  // Enhanced submit handler with loading state
  // Use ref to access handleSubmit to completely avoid TDZ
  const handleSubmitWithLoading = useCallback(async () => {
    setIsSubmittingRef.current(true);
    try {
      // Access handleSubmit via ref to avoid TDZ
      const submitFn = handleSubmitRef.current;
      if (submitFn) {
        await submitFn();
      }
    } finally {
      // Keep loading state for redirect delay
      setTimeout(() => {
        setIsSubmittingRef.current(false);
      }, 2000);
    }
  }, []); // Empty deps - using ref instead of direct dependency

  // Return only handleSubmitWithLoading to avoid TDZ
  // handleSubmit is internal and not needed outside the hook
  return {
    handleSubmitWithLoading,
  };
}
