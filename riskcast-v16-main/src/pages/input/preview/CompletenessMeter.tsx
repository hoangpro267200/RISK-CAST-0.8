/**
 * Completeness Meter - Preview Panel Component
 */

import React from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { Skeleton } from '../components/Skeleton';

interface CompletenessMeterProps {
  completeness: number;
  completedFields: string[];
  missingFields: string[];
  isLoading?: boolean;
}

export const CompletenessMeter: React.FC<CompletenessMeterProps> = ({
  completeness,
  completedFields,
  missingFields,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <GlassCard padding="lg" variant="default">
        <Skeleton width="40%" height="20px" style={{ marginBottom: designTokens.spacing.lg }} />
        <Skeleton width="100%" height="8px" style={{ marginBottom: designTokens.spacing.md }} />
        <Skeleton width="60%" height="16px" style={{ marginBottom: designTokens.spacing.lg }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: designTokens.spacing.sm }}>
          {[1, 2, 3, 4].map(i => (
            <Skeleton key={i} width="80%" height="20px" />
          ))}
        </div>
      </GlassCard>
    );
  }
  
  return (
    <GlassCard padding="lg" variant="default">
      <h3
        style={{
          fontSize: '18px',
          fontWeight: 600,
          color: designTokens.colors.textStrong,
          fontFamily: designTokens.typography.fontFamily,
          marginBottom: designTokens.spacing.lg,
        }}
      >
        COMPLETENESS
      </h3>
      
      {/* Progress Bar */}
      <div
        style={{
          width: '100%',
          height: '8px',
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          borderRadius: '4px',
          overflow: 'hidden',
          marginBottom: designTokens.spacing.md,
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
      
      <div
        style={{
          fontSize: '14px',
          color: designTokens.colors.textMuted,
          fontFamily: designTokens.typography.fontFamily,
          marginBottom: designTokens.spacing.lg,
        }}
      >
        {completedFields.length} of {completedFields.length + missingFields.length} required fields
      </div>
      
      {/* Checklist */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: designTokens.spacing.sm,
        }}
      >
        {completedFields.map((field) => (
          <div
            key={field}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: designTokens.spacing.sm,
              fontSize: '14px',
              fontFamily: designTokens.typography.fontFamily,
              color: designTokens.colors.textDefault,
            }}
          >
            <CheckCircle2 size={16} style={{ color: designTokens.colors.success }} />
            <span>{field}</span>
          </div>
        ))}
        
        {missingFields.map((field) => (
          <div
            key={field}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: designTokens.spacing.sm,
              fontSize: '14px',
              fontFamily: designTokens.typography.fontFamily,
              color: designTokens.colors.textMuted,
            }}
          >
            <XCircle size={16} style={{ color: designTokens.colors.danger }} />
            <span>{field}</span>
          </div>
        ))}
      </div>
      
      {missingFields.length > 0 && (
        <button
          type="button"
          onClick={() => {
            // Scroll to first missing field
            const firstMissing = missingFields[0];
            // Implementation: find field and scroll
          }}
          style={{
            marginTop: designTokens.spacing.lg,
            padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
            backgroundColor: 'transparent',
            border: `1px solid rgba(255, 255, 255, 0.08)`,
            borderRadius: designTokens.radii.md,
            color: designTokens.colors.primaryNeon,
            fontSize: '13px',
            fontFamily: designTokens.typography.fontFamily,
            fontWeight: 500,
            cursor: 'pointer',
            textDecoration: 'underline',
            transition: designTokens.transitions.normal,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = designTokens.colors.primaryNeon;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
          }}
        >
          Jump to missing fields
        </button>
      )}
    </GlassCard>
  );
};
