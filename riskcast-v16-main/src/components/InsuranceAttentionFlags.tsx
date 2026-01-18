/**
 * Insurance Attention Flags Component
 * 
 * Displays insurance attention flags based on shipment characteristics.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import { AlertTriangle, Shield, DollarSign, Clock, Package, Cloud } from 'lucide-react';

interface InsuranceFlag {
  type: 'HIGH_VALUE' | 'LONG_TRANSIT' | 'FRAGILE' | 'WEATHER_RISK' | 'HANDLING_RISK' | 'CARGO_CONTAINER_MISMATCH';
  message: string;
  recommendation: string;
  icon: React.ElementType;
}

interface InsuranceAttentionFlagsProps {
  cargoValue: number;
  transitDays: number;
  cargoType: string;
  routeRiskLevel?: 'LOW' | 'MEDIUM' | 'HIGH';
  transshipmentCount?: number;
  cargoContainerMismatch?: boolean;
}

export const InsuranceAttentionFlags: React.FC<InsuranceAttentionFlagsProps> = ({
  cargoValue,
  transitDays,
  cargoType,
  routeRiskLevel,
  transshipmentCount = 0,
  cargoContainerMismatch = false,
}) => {
  // Generate flags based on conditions
  const flags: InsuranceFlag[] = [];

  // High value flag
  if (cargoValue > 200000) {
    flags.push({
      type: 'HIGH_VALUE',
      message: `High-value cargo (${cargoValue >= 1000000 ? `$${(cargoValue / 1000000).toFixed(2)}M` : `$${(cargoValue / 1000).toFixed(0)}K`})`,
      recommendation: 'Recommend full ICC(A) coverage + inland transit extension',
      icon: DollarSign,
    });
  }

  // Long transit flag
  if (transitDays > 30) {
    flags.push({
      type: 'LONG_TRANSIT',
      message: `Extended transit (${transitDays} days)`,
      recommendation: 'Condensation risk increases. Recommend humidity indicator cards + inspection clause',
      icon: Clock,
    });
  }

  // Fragile cargo flag
  const fragileTypes = ['electronics', 'pharmaceuticals', 'glass', 'ceramic'];
  if (fragileTypes.some(type => cargoType.toLowerCase().includes(type))) {
    flags.push({
      type: 'FRAGILE',
      message: `${cargoType} (Temperature/Shock Sensitive)`,
      recommendation: 'Moisture exclusion waiver, shock damage rider',
      icon: Package,
    });
  }

  // Weather risk flag
  if (routeRiskLevel === 'HIGH') {
    flags.push({
      type: 'WEATHER_RISK',
      message: 'Winter Pacific Crossing',
      recommendation: 'Consider parametric weather coverage',
      icon: Cloud,
    });
  }

  // Handling risk flag
  if (transshipmentCount > 1) {
    flags.push({
      type: 'HANDLING_RISK',
      message: 'Multiple Port Transfers',
      recommendation: 'Damage risk increases. Consider all-risk coverage',
      icon: Shield,
    });
  }

  // Cargo-container mismatch flag
  if (cargoContainerMismatch) {
    flags.push({
      type: 'CARGO_CONTAINER_MISMATCH',
      message: 'Cargo-Container Mismatch',
      recommendation: 'Container type may not be suitable. Review container selection',
      icon: AlertTriangle,
    });
  }

  // Defensive guard
  if (flags.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-8 text-white/60">
          <Shield className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm font-medium">No special insurance attention flags</p>
          <p className="text-xs text-white/40 mt-1">Standard coverage applies</p>
        </div>
      </GlassCard>
    );
  }

  // Get flag color
  const getFlagColor = (type: InsuranceFlag['type']) => {
    switch (type) {
      case 'HIGH_VALUE':
      case 'CARGO_CONTAINER_MISMATCH':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'LONG_TRANSIT':
      case 'FRAGILE':
      case 'WEATHER_RISK':
      case 'HANDLING_RISK':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-400" />
          <span>Insurance Attention Flags</span>
        </h3>
        <p className="text-sm text-white/60">
          Special considerations for this shipment
        </p>
      </div>

      <div className="space-y-4">
        {flags.map((flag, idx) => {
          const Icon = flag.icon;
          const colorClass = getFlagColor(flag.type);

          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border ${colorClass}`}
            >
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-lg ${colorClass} flex items-center justify-center flex-shrink-0`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold mb-1">{flag.message}</h4>
                  <p className="text-xs text-white/70 mt-2">
                    → {flag.recommendation}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
};
