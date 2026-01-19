/**
 * Value & Terms Section - Section D
 */

import React from 'react';
import { DollarSign, FileText, MapPin } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { Input } from '../components/Input';
import { Dropdown } from '../components/Dropdown';

interface ValueTermsSectionProps {
  data?: {
    insuranceValue?: number;
    insuranceCoverage?: string;
    incoterm?: string;
    incotermLocation?: string;
    currency?: string;
  };
  onChange: (field: string, value: unknown) => void;
  mode: 'basic' | 'advanced';
}

export const ValueTermsSection: React.FC<ValueTermsSectionProps> = ({
  data,
  onChange,
  mode,
}) => {
  return (
    <GlassCard padding="lg" variant="default">
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: designTokens.spacing.lg,
          marginBottom: designTokens.spacing['2xl'],
        }}
      >
        <div
          style={{
            width: '56px',
            height: '56px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: `linear-gradient(135deg, rgba(110, 243, 255, 0.2), rgba(139, 123, 255, 0.2))`,
            border: `2px solid ${designTokens.colors.primaryNeon}`,
            borderRadius: designTokens.radii.lg,
          }}
        >
          <DollarSign size={28} style={{ color: designTokens.colors.primaryNeon }} />
        </div>
        
        <div style={{ flex: 1 }}>
          <h2
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: designTokens.colors.textStrong,
              fontFamily: 'Orbitron, monospace',
              marginBottom: designTokens.spacing.xs,
            }}
          >
            D. Value & Terms
          </h2>
          <p
            style={{
              fontSize: '15px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            What's it worth and who's responsible?
          </p>
        </div>
        
        <span
          style={{
            padding: `${designTokens.spacing.xs} ${designTokens.spacing.md}`,
            backgroundColor: 'rgba(255, 105, 180, 0.2)',
            color: '#ff69b4',
            border: '1px solid rgba(255, 105, 180, 0.3)',
            borderRadius: designTokens.radii.lg,
            fontSize: '12px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Required
        </span>
      </div>
      
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: designTokens.spacing['2xl'],
        }}
      >
        <Input
          label="Insurance Value"
          type="number"
          value={data?.insuranceValue?.toString() || ''}
          icon={DollarSign}
          unit={data?.currency || 'USD'}
          required
          onChange={(e) => onChange('insuranceValue', parseFloat(e.target.value) || 0)}
          helperText="Total insured value"
        />
        
        <Dropdown
          label="Insurance Coverage"
          placeholder="Select coverage type"
          value={data?.insuranceCoverage}
          options={[
            { value: 'all-risk', label: 'All Risk' },
            { value: 'fpa', label: 'Free of Particular Average (FPA)' },
            { value: 'wpa', label: 'With Particular Average (WPA)' },
          ]}
          onChange={(value) => onChange('insuranceCoverage', value)}
        />
        
        {mode === 'advanced' && (
          <>
            <Dropdown
              label="Incoterm® 2020"
              placeholder="Select Incoterm"
              value={data?.incoterm}
              options={[
                { value: 'EXW', label: 'EXW - Ex Works' },
                { value: 'FOB', label: 'FOB - Free On Board' },
                { value: 'CIF', label: 'CIF - Cost, Insurance, Freight' },
                { value: 'DDP', label: 'DDP - Delivered Duty Paid' },
              ]}
              onChange={(value) => onChange('incoterm', value)}
              helperText="Defines cost & risk transfer point"
            />
            
            <Input
              label="Incoterm Location"
              placeholder="e.g., Shanghai, Los Angeles"
              value={data?.incotermLocation || ''}
              icon={MapPin}
              onChange={(e) => onChange('incotermLocation', e.target.value)}
              helperText="Named place of delivery/transfer"
            />
          </>
        )}
      </div>
    </GlassCard>
  );
};
