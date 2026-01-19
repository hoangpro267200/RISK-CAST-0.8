/**
 * Sticky CTA Bar - Progress + Save Draft + Run Analysis
 */

import React from 'react';
import { ArrowRight, Save } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';

interface StickyCTABarProps {
  completeness: number;
  completedCount: number;
  requiredCount: number;
  isSaving: boolean;
  onSaveDraft: () => void;
  onSubmit: () => void;
  canSubmit: boolean;
}

export const StickyCTABar: React.FC<StickyCTABarProps> = ({
  completeness,
  completedCount,
  requiredCount,
  isSaving,
  onSaveDraft,
  onSubmit,
  canSubmit,
}) => {
  return (
    <div
      style={{
        height: '80px',
        backgroundColor: designTokens.colors.bg1,
        backdropFilter: designTokens.blur.md,
        borderTop: `1px solid rgba(255, 255, 255, 0.08)`,
        padding: `0 ${designTokens.spacing['3xl']}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 -4px 24px rgba(0, 0, 0, 0.1)',
      }}
    >
      {/* Progress Section */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: designTokens.spacing.lg,
          flex: 1,
        }}
      >
        {/* Progress Bar */}
        <div
          style={{
            width: '200px',
            height: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '4px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${completeness}%`,
              height: '100%',
              background: `linear-gradient(90deg, ${designTokens.colors.primaryNeon}, ${designTokens.colors.accent})`,
              transition: 'width 200ms ease-out',
            }}
          />
        </div>
        
        {/* Progress Text */}
        <span
          style={{
            fontSize: '14px',
            color: designTokens.colors.textMuted,
            fontFamily: designTokens.typography.fontFamily,
          }}
        >
          {completedCount} of {requiredCount} required
        </span>
        
        {/* Keyboard Hint */}
        <span
          style={{
            fontSize: '12px',
            color: designTokens.colors.textSoft,
            fontFamily: designTokens.typography.fontFamily,
            marginLeft: designTokens.spacing.lg,
          }}
        >
          ⌨ Tab to navigate • Enter to submit
        </span>
      </div>
      
      {/* Actions */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: designTokens.spacing.lg,
        }}
      >
        {/* Save Draft Button */}
        <button
          onClick={onSaveDraft}
          disabled={isSaving}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: designTokens.spacing.sm,
            padding: `${designTokens.spacing.md} ${designTokens.spacing['2xl']}`,
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            border: `1px solid rgba(255, 255, 255, 0.08)`,
            borderRadius: designTokens.radii.lg,
            color: designTokens.colors.textDefault,
            fontSize: '15px',
            fontFamily: designTokens.typography.fontFamily,
            fontWeight: 600,
            cursor: isSaving ? 'not-allowed' : 'pointer',
            opacity: isSaving ? 0.5 : 1,
            transition: designTokens.transitions.normal,
          }}
          onMouseEnter={(e) => {
            if (!isSaving) {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
              e.currentTarget.style.borderColor = designTokens.colors.primaryNeon;
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
          }}
        >
          <Save size={18} />
          {isSaving ? 'Saving...' : 'Save Draft'}
        </button>
        
        {/* Run Analysis Button */}
        <button
          onClick={onSubmit}
          disabled={!canSubmit}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: designTokens.spacing.sm,
            padding: `${designTokens.spacing.lg} ${designTokens.spacing['3xl']}`,
            background: canSubmit
              ? `linear-gradient(135deg, ${designTokens.colors.primaryNeon}, ${designTokens.colors.accent2})`
              : 'rgba(255, 255, 255, 0.05)',
            border: 'none',
            borderRadius: designTokens.radii.lg,
            color: canSubmit ? designTokens.colors.bg0 : designTokens.colors.textMuted,
            fontSize: '16px',
            fontFamily: designTokens.typography.fontFamily,
            fontWeight: 600,
            cursor: canSubmit ? 'pointer' : 'not-allowed',
            opacity: canSubmit ? 1 : 0.5,
            boxShadow: canSubmit ? designTokens.shadows.neon : 'none',
            transition: designTokens.transitions.normal,
          }}
          onMouseEnter={(e) => {
            if (canSubmit) {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 8px 24px rgba(110, 243, 255, 0.4)';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = canSubmit ? designTokens.shadows.neon : 'none';
          }}
        >
          Run Risk Analysis
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
};
