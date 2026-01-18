/**
 * Logistics Realism Panel
 * 
 * Houses all logistics realism components for comprehensive logistics validation.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import { CargoContainerValidation } from './CargoContainerValidation';
import { RouteSeasonalityRisk } from './RouteSeasonalityRisk';
import { PortCongestionStatus } from './PortCongestionStatus';
import { InsuranceAttentionFlags } from './InsuranceAttentionFlags';
import type { LogisticsRealismData } from '../types/logisticsTypes';
import { Package, Info } from 'lucide-react';

interface LogisticsRealismPanelProps {
  logisticsData: LogisticsRealismData;
  cargoType: string;
  containerType: string;
  cargoValue: number;
  transitDays: number;
}

export const LogisticsRealismPanel: React.FC<LogisticsRealismPanelProps> = ({
  logisticsData,
  cargoType,
  containerType,
  cargoValue,
  transitDays,
}) => {
  // Defensive guard
  if (!logisticsData) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Package className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Logistics realism data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not provide logistics realism data. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <GlassCard variant="hero" className="border-2 border-blue-500/20">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Package className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-2">Logistics Realism Analysis</h2>
            <p className="text-white/70 text-sm mb-3">
              Comprehensive logistics validation including cargo-container compatibility, 
              route seasonality, port congestion, and packaging recommendations.
            </p>
            <div className="flex items-center gap-2 text-xs text-white/50">
              <Info className="w-4 h-4" />
              <span>This analysis enables logistics managers to identify issues within 30 seconds.</span>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Cargo-Container Validation */}
      <CargoContainerValidation
        validation={logisticsData.cargoContainerValidation}
        cargoType={cargoType}
        containerType={containerType}
      />

      {/* Insurance Attention Flags */}
      <InsuranceAttentionFlags
        cargoValue={cargoValue}
        transitDays={transitDays}
        cargoType={cargoType}
        routeRiskLevel={logisticsData.routeSeasonality.riskLevel}
        transshipmentCount={logisticsData.portCongestion.transshipments.length}
        cargoContainerMismatch={!logisticsData.cargoContainerValidation.isValid}
      />

      {/* Route Seasonality Risk */}
      <RouteSeasonalityRisk seasonality={logisticsData.routeSeasonality} />

      {/* Port Congestion Status */}
      <PortCongestionStatus
        pol={logisticsData.portCongestion.pol}
        pod={logisticsData.portCongestion.pod}
        transshipments={logisticsData.portCongestion.transshipments}
      />

      {/* Packaging Recommendations */}
      {logisticsData.packagingRecommendations.length > 0 && (
        <GlassCard>
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
              <Package className="w-5 h-5 text-green-400" />
              <span>Packaging Recommendations</span>
            </h3>
            <p className="text-sm text-white/60">
              Recommended packaging improvements to reduce risk
            </p>
          </div>

          <div className="space-y-3">
            {logisticsData.packagingRecommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-4 bg-white/5 rounded-lg border border-white/10"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="text-sm font-semibold text-white">{rec.item}</h4>
                  <div className="text-sm font-semibold text-cyan-400">
                    ${(rec.cost / 1000).toFixed(1)}K
                  </div>
                </div>
                <p className="text-xs text-white/70 mb-2">{rec.rationale}</p>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-white/50">Risk Reduction:</span>
                  <span className="text-xs font-semibold text-emerald-400">
                    {rec.riskReduction}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Delay Probabilities */}
      {logisticsData.delayProbabilities && (
        <GlassCard>
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
              <Info className="w-5 h-5 text-blue-400" />
              <span>Delay Probabilities</span>
            </h3>
            <p className="text-sm text-white/60">
              Probability of delays exceeding threshold days
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-center">
              <div className="text-xs text-white/60 mb-1">P(delay &gt; 7 days)</div>
              <div className="text-2xl font-bold text-amber-400">
                {(logisticsData.delayProbabilities.p7days * 100).toFixed(0)}%
              </div>
            </div>
            <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-center">
              <div className="text-xs text-white/60 mb-1">P(delay &gt; 14 days)</div>
              <div className="text-2xl font-bold text-orange-400">
                {(logisticsData.delayProbabilities.p14days * 100).toFixed(0)}%
              </div>
            </div>
            <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-center">
              <div className="text-xs text-white/60 mb-1">P(delay &gt; 21 days)</div>
              <div className="text-2xl font-bold text-red-400">
                {(logisticsData.delayProbabilities.p21days * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
};
