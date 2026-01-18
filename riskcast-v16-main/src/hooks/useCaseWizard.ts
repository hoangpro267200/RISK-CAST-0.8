/**
 * Case Wizard Hook - Unified Navigation State Management
 * 
 * Manages navigation between Input → Summary → Results with preserved case data.
 * Provides stepper state, navigation handlers, and draft persistence.
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { DomainCase } from '@/domain';

export type WizardStep = 'input' | 'summary' | 'results';

export interface CaseWizardState {
  currentStep: WizardStep;
  caseData: DomainCase | null;
  canNavigateForward: boolean;
  canNavigateBack: boolean;
}

/**
 * Hook for managing case wizard state and navigation
 */
export function useCaseWizard(initialStep: WizardStep = 'input') {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<WizardStep>(initialStep);
  const [caseData, setCaseData] = useState<DomainCase | null>(null);
  
  // Load case data from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('RISKCAST_STATE');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        // Check if it's DomainCase format (has caseId or transportMode)
        if (parsed.caseId || parsed.transportMode) {
          setCaseData(parsed as DomainCase);
        }
      } catch (e) {
        console.warn('[useCaseWizard] Failed to parse saved case data:', e);
      }
    }
  }, []);
  
  // Save case data to localStorage whenever it changes
  useEffect(() => {
    if (caseData) {
      localStorage.setItem('RISKCAST_STATE', JSON.stringify(caseData));
    }
  }, [caseData]);
  
  const canNavigateForward = useCallback((): boolean => {
    switch (currentStep) {
      case 'input':
        // Can go to summary if case data exists (at least basic fields)
        return caseData !== null && !!caseData.pol && !!caseData.pod;
      case 'summary':
        // Can go to results if analysis has been run
        return localStorage.getItem('RISKCAST_RESULTS_V2') !== null;
      case 'results':
        return false; // No forward from results
      default:
        return false;
    }
  }, [currentStep, caseData]);
  
  const canNavigateBack = useCallback((): boolean => {
    switch (currentStep) {
      case 'input':
        return false; // No back from input
      case 'summary':
        return true; // Can go back to input
      case 'results':
        return true; // Can go back to summary
      default:
        return false;
    }
  }, [currentStep]);
  
  const handleNext = useCallback(() => {
    if (!canNavigateForward()) return;
    
    switch (currentStep) {
      case 'input':
        navigate('/summary');
        setCurrentStep('summary');
        break;
      case 'summary':
        navigate('/results');
        setCurrentStep('results');
        break;
      case 'results':
        // No next from results
        break;
    }
  }, [currentStep, canNavigateForward, navigate]);
  
  const handleBack = useCallback(() => {
    if (!canNavigateBack()) return;
    
    switch (currentStep) {
      case 'summary':
        navigate('/input');
        setCurrentStep('input');
        break;
      case 'results':
        navigate('/summary');
        setCurrentStep('summary');
        break;
      case 'input':
        // No back from input
        break;
    }
  }, [currentStep, canNavigateBack, navigate]);
  
  const handleSaveDraft = useCallback(() => {
    if (caseData) {
      // Already saved via useEffect, just update lastModified
      const updated = {
        ...caseData,
        lastModified: new Date().toISOString(),
      };
      setCaseData(updated);
      localStorage.setItem('RISKCAST_STATE', JSON.stringify(updated));
      
      // Optionally: Save to backend draft endpoint
      // fetch('/api/v1/cases/draft', { method: 'POST', body: JSON.stringify(updated) });
    }
  }, [caseData]);
  
  const getStepNumber = useCallback((): number => {
    switch (currentStep) {
      case 'input': return 1;
      case 'summary': return 2;
      case 'results': return 3;
      default: return 1;
    }
  }, [currentStep]);
  
  const getStepLabel = useCallback((): string => {
    switch (currentStep) {
      case 'input': return 'Input';
      case 'summary': return 'Summary';
      case 'results': return 'Results';
      default: return '';
    }
  }, [currentStep]);
  
  return {
    currentStep,
    caseData,
    setCaseData,
    canNavigateForward: canNavigateForward(),
    canNavigateBack: canNavigateBack(),
    handleNext,
    handleBack,
    handleSaveDraft,
    getStepNumber,
    getStepLabel,
  };
}
