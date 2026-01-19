/**
 * Route & Service Section - Section A
 */

import React from 'react';
import { Ship, MapPin } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { Dropdown } from '../components/Dropdown';
import { Input } from '../components/Input';
import { PillGroup } from '../components/PillGroup';
import { Zap, Activity, DollarSign, ShieldCheck } from 'lucide-react';

interface RouteServiceSectionProps {
  data?: {
    tradeLane?: string;
    mode?: string;
    shipmentType?: string;
    serviceRoute?: string;
    carrier?: string;
    containerType?: string;
    priority?: string;
    pol?: string;
    pod?: string;
  };
  onChange: (field: string, value: unknown) => void;
  mode: 'basic' | 'advanced';
}

// Mock data - should come from API or data file
const TRADE_LANES = [
  { value: 'asia-europe', label: 'Asia - Europe' },
  { value: 'asia-america', label: 'Asia - America' },
  { value: 'europe-america', label: 'Europe - America' },
];

const MODES = [
  { value: 'ocean', label: 'Ocean' },
  { value: 'air', label: 'Air' },
  { value: 'road', label: 'Road' },
  { value: 'rail', label: 'Rail' },
];

const PRIORITY_OPTIONS = [
  { value: 'fastest', label: 'Fastest', icon: Zap },
  { value: 'balanced', label: 'Balanced', icon: Activity },
  { value: 'cheapest', label: 'Cheapest', icon: DollarSign },
  { value: 'reliable', label: 'Most Reliable', icon: ShieldCheck },
];

export const RouteServiceSection: React.FC<RouteServiceSectionProps> = ({
  data,
  onChange,
  mode,
}) => {
  return (
    <GlassCard padding="lg" variant="default">
      {/* Section Header */}
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
            boxShadow: `0 0 30px rgba(110, 243, 255, 0.3)`,
          }}
        >
          <Ship size={28} style={{ color: designTokens.colors.primaryNeon }} />
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
            A. Route & Service
          </h2>
          <p
            style={{
              fontSize: '15px',
              color: designTokens.colors.textMuted,
              fontFamily: designTokens.typography.fontFamily,
            }}
          >
            Where is your shipment going and how?
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
      
      {/* Form Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: designTokens.spacing['2xl'],
        }}
      >
        <Dropdown
          label="Trade Lane"
          placeholder="Select trade lane"
          value={data?.tradeLane}
          options={TRADE_LANES}
          searchable
          required
          onChange={(value) => onChange('tradeLane', value)}
        />
        
        <Dropdown
          label="Mode of Transport"
          placeholder="Select mode"
          value={data?.mode}
          options={MODES}
          required
          onChange={(value) => onChange('mode', value)}
        />
        
        <Dropdown
          label="Shipment Type"
          placeholder="Select shipment type"
          value={data?.shipmentType}
          options={[
            { value: 'fcl', label: 'FCL (Full Container Load)' },
            { value: 'lcl', label: 'LCL (Less than Container Load)' },
            { value: 'breakbulk', label: 'Break Bulk' },
          ]}
          required
          onChange={(value) => onChange('shipmentType', value)}
        />
        
        <Dropdown
          label="Service Route"
          placeholder="Select service route"
          value={data?.serviceRoute}
          options={[
            { value: 'route1', label: 'ONE Alliance - Asia-Europe Express' },
            { value: 'route2', label: 'CSCL Saturn - Transpacific' },
          ]}
          searchable
          required
          onChange={(value) => onChange('serviceRoute', value)}
        />
        
        <Dropdown
          label="Carrier"
          placeholder="Select carrier"
          value={data?.carrier}
          options={[
            { value: 'one', label: 'ONE Alliance' },
            { value: 'csc', label: 'CSCL Saturn' },
          ]}
          onChange={(value) => onChange('carrier', value)}
        />
        
        <Dropdown
          label="Container Type"
          placeholder="Select container"
          value={data?.containerType}
          options={[
            { value: '20ft', label: '20ft Standard' },
            { value: '40ft', label: '40ft Standard' },
            { value: '40hc', label: '40ft High Cube' },
            { value: 'reefer', label: 'Reefer' },
          ]}
          onChange={(value) => onChange('containerType', value)}
        />
        
        <PillGroup
          label="Priority Selection"
          options={PRIORITY_OPTIONS}
          value={data?.priority || 'balanced'}
          onChange={(value) => onChange('priority', value)}
          helperText="Filter service routes by priority"
        />
        
        <Input
          label="Origin Port (POL)"
          placeholder="e.g., LAX, SGN, SHA"
          value={data?.pol || ''}
          icon={MapPin}
          required
          onChange={(e) => onChange('pol', e.target.value)}
          helperText="Port where cargo is loaded"
        />
        
        <Input
          label="Destination Port (POD)"
          placeholder="e.g., Rotterdam, Dubai"
          value={data?.pod || ''}
          icon={MapPin}
          required
          onChange={(e) => onChange('pod', e.target.value)}
          helperText="Port where cargo is unloaded"
        />
      </div>
    </GlassCard>
  );
};
