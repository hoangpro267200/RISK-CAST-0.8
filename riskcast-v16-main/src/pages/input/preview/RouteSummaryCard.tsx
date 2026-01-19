/**
 * Route Summary Card - Preview Panel Component
 */

import React from 'react';
import { Ship, Package, Clock } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';

interface RouteSummaryCardProps {
  pol: string;
  pod: string;
  mode: string;
  carrier?: string;
  transitDays: number;
}

export const RouteSummaryCard: React.FC<RouteSummaryCardProps> = ({
  pol,
  pod,
  mode,
  carrier,
  transitDays,
}) => {
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
        ROUTE SUMMARY
      </h3>
      
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: designTokens.spacing.lg,
        }}
      >
        <div style={{ textAlign: 'center', flex: 1 }}>
          <div
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: designTokens.colors.textStrong,
              fontFamily: 'Orbitron, monospace',
              marginBottom: designTokens.spacing.xs,
            }}
          >
            {pol}
          </div>
          <div
            style={{
              fontSize: '13px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            Origin
          </div>
        </div>
        
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: `0 ${designTokens.spacing.lg}`,
          }}
        >
          <div
            style={{
              width: '100%',
              height: '2px',
              background: `linear-gradient(90deg, ${designTokens.colors.primaryNeon}, ${designTokens.colors.accent})`,
              position: 'relative',
            }}
          >
            <div
              style={{
                position: 'absolute',
                right: '-8px',
                top: '-6px',
                width: '0',
                height: '0',
                borderLeft: `8px solid ${designTokens.colors.primaryNeon}`,
                borderTop: '6px solid transparent',
                borderBottom: '6px solid transparent',
              }}
            />
          </div>
        </div>
        
        <div style={{ textAlign: 'center', flex: 1 }}>
          <div
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: designTokens.colors.textStrong,
              fontFamily: 'Orbitron, monospace',
              marginBottom: designTokens.spacing.xs,
            }}
          >
            {pod}
          </div>
          <div
            style={{
              fontSize: '13px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            Destination
          </div>
        </div>
      </div>
      
      <div
        style={{
          display: 'flex',
          gap: designTokens.spacing.sm,
          marginBottom: designTokens.spacing.md,
        }}
      >
        <div
          style={{
            padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
            backgroundColor: 'rgba(110, 243, 255, 0.1)',
            border: `1px solid ${designTokens.colors.primaryNeon}`,
            borderRadius: designTokens.radii.md,
            fontSize: '13px',
            fontFamily: designTokens.typography.fontFamily,
            color: designTokens.colors.primaryNeon,
            display: 'flex',
            alignItems: 'center',
            gap: designTokens.spacing.xs,
          }}
        >
          <Ship size={14} />
          {mode}
        </div>
        
        <div
          style={{
            padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
            backgroundColor: 'rgba(110, 243, 255, 0.1)',
            border: `1px solid ${designTokens.colors.primaryNeon}`,
            borderRadius: designTokens.radii.md,
            fontSize: '13px',
            fontFamily: designTokens.typography.fontFamily,
            color: designTokens.colors.primaryNeon,
            display: 'flex',
            alignItems: 'center',
            gap: designTokens.spacing.xs,
          }}
        >
          <Package size={14} />
          FCL
        </div>
        
        <div
          style={{
            padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
            backgroundColor: 'rgba(110, 243, 255, 0.1)',
            border: `1px solid ${designTokens.colors.primaryNeon}`,
            borderRadius: designTokens.radii.md,
            fontSize: '13px',
            fontFamily: designTokens.typography.fontFamily,
            color: designTokens.colors.primaryNeon,
            display: 'flex',
            alignItems: 'center',
            gap: designTokens.spacing.xs,
          }}
        >
          <Clock size={14} />
          {transitDays} days
        </div>
      </div>
      
      {carrier && (
        <div
          style={{
            fontSize: '14px',
            color: designTokens.colors.textMuted,
            fontFamily: designTokens.typography.fontFamily,
          }}
        >
          {carrier}
        </div>
      )}
    </GlassCard>
  );
};
