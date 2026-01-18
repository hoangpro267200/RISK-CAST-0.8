/**
 * Case Stepper Component - Navigation Progress Indicator
 * 
 * Shows progress through Input → Summary → Results flow.
 * Provides visual feedback on current step and completion status.
 * Uses design tokens for consistent styling.
 */

import React from 'react';
import { Check, Circle, ArrowRight } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import type { WizardStep } from '@/hooks/useCaseWizard';

export interface CaseStepperProps {
  currentStep: WizardStep;
  completedSteps?: WizardStep[];
  onStepClick?: (step: WizardStep) => void;
  className?: string;
  showLabels?: boolean;
}

export interface StepperStep {
  id: WizardStep;
  label: string;
  number: number;
  path: string;
}

const STEPS: StepperStep[] = [
  { id: 'input', label: 'Input', number: 1, path: '/input_v20' },
  { id: 'summary', label: 'Summary', number: 2, path: '/summary' },
  { id: 'results', label: 'Results', number: 3, path: '/results' },
];

/**
 * Case Stepper Component
 */
export function CaseStepper({
  currentStep,
  completedSteps = [],
  onStepClick,
  className = '',
  showLabels = true,
}: CaseStepperProps) {
  const getStepStatus = (step: StepperStep): 'completed' | 'current' | 'pending' => {
    if (completedSteps.includes(step.id)) return 'completed';
    if (currentStep === step.id) return 'current';
    return 'pending';
  };

  const handleStepClick = (step: StepperStep) => {
    if (onStepClick) {
      onStepClick(step.id);
    } else {
      // Default navigation
      window.location.href = step.path;
    }
  };

  return (
    <nav
      aria-label="Case workflow steps"
      className={`flex items-center justify-center gap-2 sm:gap-4 ${className}`}
      style={{
        padding: `${designTokens.spacing.md} ${designTokens.spacing.xl}`,
      }}
    >
      {STEPS.map((step, index) => {
        const status = getStepStatus(step);
        const isLast = index === STEPS.length - 1;

        return (
          <React.Fragment key={step.id}>
            {/* Step Circle */}
            <div className="flex flex-col items-center gap-2">
              <button
                onClick={() => handleStepClick(step)}
                disabled={status === 'pending' && !completedSteps.includes(step.id)}
                className={`
                  flex items-center justify-center w-10 h-10 rounded-full font-semibold
                  transition-all focus-visible:outline-none focus-visible:ring-2
                  focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900
                  disabled:cursor-not-allowed disabled:opacity-50
                  ${
                    status === 'completed'
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/25'
                      : status === 'current'
                      ? 'bg-blue-500/20 border-2 border-blue-500 text-blue-400 ring-2 ring-blue-500/30'
                      : 'bg-white/5 border border-white/10 text-white/40 hover:bg-white/10'
                  }
                `}
                style={{
                  borderRadius: designTokens.radii.lg,
                  transition: designTokens.transitions.normal,
                }}
                aria-current={status === 'current' ? 'step' : undefined}
                aria-label={`Step ${step.number}: ${step.label}${status === 'completed' ? ' (completed)' : status === 'current' ? ' (current)' : ''}`}
              >
                {status === 'completed' ? (
                  <Check className="w-5 h-5" />
                ) : (
                  <span style={{ fontSize: designTokens.typography.body.split('/')[0] }}>
                    {step.number}
                  </span>
                )}
              </button>

              {/* Step Label */}
              {showLabels && (
                <span
                  className={`
                    text-xs font-medium transition-colors
                    ${
                      status === 'current'
                        ? 'text-white'
                        : status === 'completed'
                        ? 'text-white/80'
                        : 'text-white/40'
                    }
                  `}
                  style={{
                    fontSize: designTokens.typography.caption.split('/')[0],
                  }}
                >
                  {step.label}
                </span>
              )}
            </div>

            {/* Connector Line */}
            {!isLast && (
              <div
                className={`
                  flex-1 h-0.5 transition-colors
                  ${
                    completedSteps.includes(STEPS[index + 1]?.id) || status === 'completed'
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500'
                      : 'bg-white/10'
                  }
                `}
                style={{
                  minWidth: '40px',
                  transition: designTokens.transitions.normal,
                }}
                aria-hidden="true"
              />
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}

/**
 * Compact Stepper (for header/navbar)
 */
export interface CompactStepperProps {
  currentStep: WizardStep;
  className?: string;
}

export function CompactCaseStepper({ currentStep, className = '' }: CompactStepperProps) {
  const currentStepIndex = STEPS.findIndex(s => s.id === currentStep);
  const progress = ((currentStepIndex + 1) / STEPS.length) * 100;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex items-center gap-1">
        {STEPS.map((step, index) => {
          const isCompleted = index < currentStepIndex;
          const isCurrent = index === currentStepIndex;

          return (
            <div
              key={step.id}
              className={`
                w-2 h-2 rounded-full transition-all
                ${
                  isCompleted
                    ? 'bg-blue-500'
                    : isCurrent
                    ? 'bg-blue-400 ring-2 ring-blue-500/30'
                    : 'bg-white/20'
                }
              `}
              style={{
                transition: designTokens.transitions.fast,
              }}
              aria-label={`Step ${step.number}: ${step.label}`}
            />
          );
        })}
      </div>
      <span
        className="text-xs text-white/60"
        style={{
          fontSize: designTokens.typography.caption.split('/')[0],
        }}
      >
        {currentStepIndex + 1}/{STEPS.length}
      </span>
    </div>
  );
}
