/**
 * Cargo Details Section - Section C
 * Basic fields + Advanced fields (collapsed by default)
 */

import React, { useState } from 'react';
import { Package, Hash, Layers, Weight, Box, Thermometer, AlertOctagon } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { Input } from '../components/Input';
import { Dropdown } from '../components/Dropdown';
import { PillGroup } from '../components/PillGroup';
import { ChevronDown } from 'lucide-react';

interface CargoDetailsSectionProps {
  data?: {
    type?: string;
    hsCode?: string;
    packingType?: string;
    packages?: number;
    grossWeight?: number;
    netWeight?: number;
    volume?: number;
    stackable?: boolean;
    sensitivity?: string;
    tempMin?: number;
    tempMax?: number;
    dangerousGoods?: boolean;
    dgUnNumber?: string;
    dgClass?: string;
    dgPackingGroup?: string;
    loadabilityIssues?: boolean;
    description?: string;
    specialHandling?: string;
  };
  onChange: (field: string, value: unknown) => void;
  mode: 'basic' | 'advanced';
}

export const CargoDetailsSection: React.FC<CargoDetailsSectionProps> = ({
  data,
  onChange,
  mode,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(mode === 'advanced');
  
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
          <Package size={28} style={{ color: designTokens.colors.primaryNeon }} />
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
            C. Cargo Details
          </h2>
          <p
            style={{
              fontSize: '15px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            What am I shipping?
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
      
      {/* Basic Fields */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: designTokens.spacing['2xl'],
          marginBottom: designTokens.spacing['2xl'],
        }}
      >
        <Dropdown
          label="Cargo Type"
          placeholder="Select cargo type"
          value={data?.type}
          options={[
            { value: 'electronics', label: 'Electronics' },
            { value: 'textiles', label: 'Textiles' },
            { value: 'machinery', label: 'Machinery' },
            { value: 'perishable', label: 'Perishable' },
          ]}
          required
          onChange={(value) => onChange('type', value)}
        />
        
        <Input
          label="HS Code"
          placeholder="e.g., 8504.40"
          value={data?.hsCode || ''}
          icon={Hash}
          onChange={(e) => onChange('hsCode', e.target.value)}
          helperText="Harmonized System code (recommended)"
        />
        
        <Dropdown
          label="Packing Type"
          placeholder="Select packing"
          value={data?.packingType}
          options={[
            { value: 'pallets', label: 'Pallets' },
            { value: 'boxes', label: 'Boxes' },
            { value: 'crates', label: 'Crates' },
          ]}
          required
          onChange={(value) => onChange('packingType', value)}
        />
        
        <Input
          label="Number of Packages"
          type="number"
          value={data?.packages?.toString() || ''}
          icon={Layers}
          onChange={(e) => onChange('packages', parseInt(e.target.value) || 0)}
          helperText="Total package count"
        />
        
        <Input
          label="Gross Weight"
          type="number"
          value={data?.grossWeight?.toString() || ''}
          icon={Weight}
          unit="kg"
          required
          onChange={(e) => onChange('grossWeight', parseFloat(e.target.value) || 0)}
          helperText="Total weight including packaging"
        />
        
        <Input
          label="Net Weight"
          type="number"
          value={data?.netWeight?.toString() || ''}
          icon={Weight}
          unit="kg"
          onChange={(e) => onChange('netWeight', parseFloat(e.target.value) || 0)}
          helperText="Weight without packaging"
        />
        
        <Input
          label="Volume"
          type="number"
          step="0.01"
          value={data?.volume?.toString() || ''}
          icon={Box}
          unit="m³"
          onChange={(e) => onChange('volume', parseFloat(e.target.value) || 0)}
          helperText="Cubic meters"
        />
        
        <PillGroup
          label="Stackability"
          options={[
            { value: 'true', label: 'Stackable' },
            { value: 'false', label: 'Non-stackable' },
          ]}
          value={data?.stackable?.toString() || 'true'}
          onChange={(value) => onChange('stackable', value === 'true')}
          helperText="Can packages be stacked?"
        />
      </div>
      
      {/* Advanced Fields Toggle */}
      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: designTokens.spacing.sm,
          padding: designTokens.spacing.md,
          backgroundColor: 'transparent',
          border: `1px dashed rgba(255, 255, 255, 0.2)`,
          borderRadius: designTokens.radii.lg,
          color: designTokens.colors.textMuted,
          fontSize: '14px',
          fontFamily: designTokens.typography.fontFamily,
          cursor: 'pointer',
          marginBottom: designTokens.spacing['2xl'],
          transition: designTokens.transitions.normal,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = designTokens.colors.primaryNeon;
          e.currentTarget.style.color = designTokens.colors.primaryNeon;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
          e.currentTarget.style.color = designTokens.colors.textMuted;
        }}
      >
        <span>{showAdvanced ? 'Hide' : 'Show'} Advanced Options</span>
        <ChevronDown
          size={16}
          style={{
            transform: showAdvanced ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: designTokens.transitions.normal,
          }}
        />
      </button>
      
      {/* Advanced Fields */}
      {showAdvanced && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: designTokens.spacing['2xl'],
            paddingTop: designTokens.spacing['2xl'],
            borderTop: `1px solid rgba(255, 255, 255, 0.08)`,
          }}
        >
          <PillGroup
            label="Cargo Sensitivity"
            options={[
              { value: 'standard', label: 'Standard' },
              { value: 'fragile', label: 'Fragile' },
              { value: 'temperature', label: 'Temperature Sensitive' },
              { value: 'high_value', label: 'High Value' },
            ]}
            value={data?.sensitivity || 'standard'}
            onChange={(value) => onChange('sensitivity', value)}
            helperText="Special handling requirements"
          />
          
          {data?.sensitivity === 'temperature' && (
            <>
              <Input
                label="Min Temperature"
                type="number"
                value={data?.tempMin?.toString() || ''}
                icon={Thermometer}
                unit="°C"
                onChange={(e) => onChange('tempMin', parseFloat(e.target.value) || 0)}
              />
              
              <Input
                label="Max Temperature"
                type="number"
                value={data?.tempMax?.toString() || ''}
                icon={Thermometer}
                unit="°C"
                onChange={(e) => onChange('tempMax', parseFloat(e.target.value) || 0)}
              />
            </>
          )}
          
          <PillGroup
            label="Dangerous Goods (DG)"
            options={[
              { value: 'false', label: 'Not DG' },
              { value: 'true', label: 'DG Cargo' },
            ]}
            value={data?.dangerousGoods?.toString() || 'false'}
            onChange={(value) => onChange('dangerousGoods', value === 'true')}
            helperText="Hazardous materials declaration"
          />
          
          {data?.dangerousGoods && (
            <>
              <Input
                label="UN Number"
                placeholder="e.g., UN1234"
                value={data?.dgUnNumber || ''}
                icon={AlertOctagon}
                onChange={(e) => onChange('dgUnNumber', e.target.value)}
              />
              
              <Dropdown
                label="DG Class"
                placeholder="Select class"
                value={data?.dgClass}
                options={[
                  { value: '1', label: 'Class 1: Explosives' },
                  { value: '2', label: 'Class 2: Gases' },
                  { value: '3', label: 'Class 3: Flammable Liquids' },
                ]}
                onChange={(value) => onChange('dgClass', value)}
              />
              
              <Dropdown
                label="Packing Group"
                placeholder="Select group"
                value={data?.dgPackingGroup}
                options={[
                  { value: 'I', label: 'Packing Group I' },
                  { value: 'II', label: 'Packing Group II' },
                  { value: 'III', label: 'Packing Group III' },
                ]}
                onChange={(value) => onChange('dgPackingGroup', value)}
              />
            </>
          )}
        </div>
      )}
    </GlassCard>
  );
};
