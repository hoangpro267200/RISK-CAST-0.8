/**
 * Preview Panel - Live preview of form data
 * 
 * Components:
 * - Route Summary Card
 * - Cargo Summary Card
 * - Completeness Meter
 * - What You'll Get Card
 */

import React from 'react';
import { designTokens } from '@/ui/design-tokens';
import { GlassCard } from '@/components/GlassCard';
import { RouteSummaryCard } from './preview/RouteSummaryCard';
import { CargoSummaryCard } from './preview/CargoSummaryCard';
import { CompletenessMeter } from './preview/CompletenessMeter';
import { WhatYoullGetCard } from './preview/WhatYoullGetCard';

interface PreviewPanelProps {
  data: {
    route: {
      pol: string;
      pod: string;
      mode: string;
      carrier: string;
      transitDays: number;
    };
    cargo: {
      type: string;
      weight: number;
      volume: number;
      packages: number;
      sensitivity: string;
    };
    value: {
      insuranceValue: number;
      currency: string;
      incoterm: string;
    };
    parties: {
      seller: any;
      buyer: any;
    };
  };
  completeness: number;
  completedFields: string[];
  missingFields: string[];
  isLoading?: boolean;
}

export const PreviewPanel: React.FC<PreviewPanelProps> = ({
  data,
  completeness,
  completedFields,
  missingFields,
  isLoading = false,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: designTokens.spacing['2xl'],
      }}
    >
      {/* Route Summary */}
      <RouteSummaryCard
        pol={data.route.pol}
        pod={data.route.pod}
        mode={data.route.mode}
        carrier={data.route.carrier}
        transitDays={data.route.transitDays}
        isLoading={isLoading || !data.route.pol || !data.route.pod}
      />
      
      {/* Cargo Summary */}
      <CargoSummaryCard
        type={data.cargo.type}
        weight={data.cargo.weight}
        volume={data.cargo.volume}
        packages={data.cargo.packages}
        sensitivity={data.cargo.sensitivity}
        insuranceValue={data.value.insuranceValue}
        incoterm={data.value.incoterm}
        isLoading={isLoading || !data.cargo.type}
      />
      
      {/* Completeness Meter */}
      <CompletenessMeter
        completeness={completeness}
        completedFields={completedFields}
        missingFields={missingFields}
        isLoading={isLoading}
      />
      
      {/* What You'll Get */}
      <WhatYoullGetCard isLoading={isLoading} />
    </div>
  );
};
