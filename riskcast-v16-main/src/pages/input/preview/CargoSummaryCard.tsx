/**
 * Cargo Summary Card - Preview Panel Component
 */

import React from 'react';
import { Package, AlertTriangle, Thermometer } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { Skeleton } from '../components/Skeleton';

interface CargoSummaryCardProps {
  type: string;
  weight: number;
  volume: number;
  packages: number;
  sensitivity: string;
  insuranceValue: number;
  incoterm?: string;
  isLoading?: boolean;
}

export const CargoSummaryCard: React.FC<CargoSummaryCardProps> = ({
  type,
  weight,
  volume,
  packages,
  sensitivity,
  insuranceValue,
  incoterm,
  isLoading = false,
}) => {
  if (isLoading || !type) {
    return (
      <GlassCard padding="lg" variant="default">
        <Skeleton width="40%" height="20px" style={{ marginBottom: designTokens.spacing.lg }} />
        <Skeleton width="60%" height="24px" style={{ marginBottom: designTokens.spacing.md }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: designTokens.spacing.md, marginBottom: designTokens.spacing.lg }}>
          <Skeleton width="100%" height="40px" />
          <Skeleton width="100%" height="40px" />
          <Skeleton width="100%" height="40px" />
        </div>
        <Skeleton width="80%" height="16px" />
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
        CARGO SUMMARY
      </h3>
      
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: designTokens.spacing.sm,
          marginBottom: designTokens.spacing.lg,
        }}
      >
        <Package size={20} style={{ color: designTokens.colors.primaryNeon }} />
        <span
          style={{
            fontSize: '16px',
            fontWeight: 600,
            color: designTokens.colors.textStrong,
            fontFamily: designTokens.typography.fontFamily,
          }}
        >
          {type}
        </span>
      </div>
      
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: designTokens.spacing.md,
          marginBottom: designTokens.spacing.lg,
        }}
      >
        <div>
          <div
            style={{
              fontSize: '12px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
              marginBottom: designTokens.spacing.xs,
            }}
          >
            Weight
          </div>
          <div
            style={{
              fontSize: '16px',
              fontWeight: 600,
              color: designTokens.colors.textStrong,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            {weight.toLocaleString()} kg
          </div>
        </div>
        
        <div>
          <div
            style={{
              fontSize: '12px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
              marginBottom: designTokens.spacing.xs,
            }}
          >
            Volume
          </div>
          <div
            style={{
              fontSize: '16px',
              fontWeight: 600,
              color: designTokens.colors.textStrong,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            {volume.toFixed(1)} m³
          </div>
        </div>
        
        <div>
          <div
            style={{
              fontSize: '12px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
              marginBottom: designTokens.spacing.xs,
            }}
          >
            Packages
          </div>
          <div
            style={{
              fontSize: '16px',
              fontWeight: 600,
              color: designTokens.colors.textStrong,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            {packages} units
          </div>
        </div>
      </div>
      
      {sensitivity !== 'standard' && (
        <div
          style={{
            display: 'flex',
            gap: designTokens.spacing.sm,
            marginBottom: designTokens.spacing.md,
          }}
        >
          {sensitivity === 'fragile' && (
            <div
              style={{
                padding: `${designTokens.spacing.xs} ${designTokens.spacing.md}`,
                backgroundColor: 'rgba(247, 201, 72, 0.2)',
                border: `1px solid ${designTokens.colors.warning}`,
                borderRadius: designTokens.radii.md,
                fontSize: '12px',
                fontFamily: designTokens.typography.fontFamily,
                color: designTokens.colors.warning,
                display: 'flex',
                alignItems: 'center',
                gap: designTokens.spacing.xs,
              }}
            >
              <AlertTriangle size={14} />
              Fragile
            </div>
          )}
          
          {sensitivity === 'temperature' && (
            <div
              style={{
                padding: `${designTokens.spacing.xs} ${designTokens.spacing.md}`,
                backgroundColor: 'rgba(110, 243, 255, 0.2)',
                border: `1px solid ${designTokens.colors.primaryNeon}`,
                borderRadius: designTokens.radii.md,
                fontSize: '12px',
                fontFamily: designTokens.typography.fontFamily,
                color: designTokens.colors.primaryNeon,
                display: 'flex',
                alignItems: 'center',
                gap: designTokens.spacing.xs,
              }}
            >
              <Thermometer size={14} />
              Temp Sensitive
            </div>
          )}
        </div>
      )}
      
      <div
        style={{
          fontSize: '14px',
          color: designTokens.colors.textMuted,
          fontFamily: designTokens.typography.fontFamily,
        }}
      >
        Insured: ${insuranceValue.toLocaleString()} USD
        {incoterm && ` • ${incoterm}`}
      </div>
    </GlassCard>
  );
};
