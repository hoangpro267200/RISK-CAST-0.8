/**
 * What You'll Get Card - Preview Panel Component
 */

import React from 'react';
import { Target, Map, Lightbulb, Shield } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { Skeleton } from '../components/Skeleton';

const BENEFITS = [
  {
    icon: Target,
    title: 'Risk Score (0-10)',
    desc: 'Overall shipment risk rating',
  },
  {
    icon: Map,
    title: 'Route Analysis',
    desc: 'Port delays, weather, etc.',
  },
  {
    icon: Lightbulb,
    title: 'Recommendations',
    desc: 'Actionable risk mitigations',
  },
  {
    icon: Shield,
    title: 'Insurance Options',
    desc: 'Optimized coverage plans',
  },
];

interface WhatYoullGetCardProps {
  isLoading?: boolean;
}

export const WhatYoullGetCard: React.FC<WhatYoullGetCardProps> = ({ isLoading = false }) => {
  if (isLoading) {
    return (
      <GlassCard padding="lg" variant="default">
        <Skeleton width="40%" height="20px" style={{ marginBottom: designTokens.spacing.md }} />
        <Skeleton width="80%" height="16px" style={{ marginBottom: designTokens.spacing.lg }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: designTokens.spacing.md }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} style={{ padding: designTokens.spacing.md, backgroundColor: 'rgba(255, 255, 255, 0.03)', borderRadius: designTokens.radii.lg }}>
              <Skeleton width="60%" height="20px" style={{ marginBottom: designTokens.spacing.xs }} />
              <Skeleton width="100%" height="16px" />
            </div>
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
          marginBottom: designTokens.spacing.md,
        }}
      >
        WHAT YOU'LL GET
      </h3>
      
      <p
        style={{
          fontSize: '14px',
          color: designTokens.colors.textMuted,
          fontFamily: designTokens.typography.fontFamily,
          marginBottom: designTokens.spacing.lg,
        }}
      >
        After analysis, you'll receive:
      </p>
      
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: designTokens.spacing.md,
        }}
      >
        {BENEFITS.map((benefit) => {
          const Icon = benefit.icon;
          
          return (
            <div
              key={benefit.title}
              style={{
                padding: designTokens.spacing.md,
                backgroundColor: 'rgba(255, 255, 255, 0.03)',
                border: `1px solid rgba(255, 255, 255, 0.08)`,
                borderRadius: designTokens.radii.lg,
                display: 'flex',
                alignItems: 'start',
                gap: designTokens.spacing.md,
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'rgba(110, 243, 255, 0.1)',
                  borderRadius: designTokens.radii.md,
                  flexShrink: 0,
                }}
              >
                <Icon size={18} style={{ color: designTokens.colors.primaryNeon }} />
              </div>
              
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontSize: '15px',
                    fontWeight: 600,
                    color: designTokens.colors.textStrong,
                    fontFamily: designTokens.typography.fontFamily,
                    marginBottom: designTokens.spacing.xs,
                  }}
                >
                  {benefit.title}
                </div>
                <div
                  style={{
                    fontSize: '13px',
                    color: designTokens.colors.textMuted,
                    fontFamily: designTokens.typography.fontFamily,
                  }}
                >
                  {benefit.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
};
