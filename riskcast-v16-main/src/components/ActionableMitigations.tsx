/**
 * Actionable Mitigations Component
 * 
 * Displays actionable risk mitigation recommendations with cost/benefit analysis.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { ActionableMitigation } from '../types/riskDisclosureTypes';
import { Target, TrendingDown, DollarSign, Clock } from 'lucide-react';

interface ActionableMitigationsProps {
  mitigations: ActionableMitigation[];
}

// Format currency
const formatCurrency = (value: number): string => {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
};

// Get ROI color
const getROIColor = (reduction: number, cost: number) => {
  const roi = reduction / (cost / 1000); // Risk reduction per $1K spent
  if (roi >= 20) return 'text-emerald-400';
  if (roi >= 10) return 'text-amber-400';
  return 'text-blue-400';
};

export const ActionableMitigations: React.FC<ActionableMitigationsProps> = ({ mitigations }) => {
  // Defensive guard
  if (!mitigations || mitigations.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Target className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Mitigation recommendations unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not generate mitigation recommendations. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Sort by risk reduction (highest first)
  const sortedMitigations = [...mitigations].sort((a, b) => b.riskReductionPercent - a.riskReductionPercent);

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Target className="w-5 h-5 text-green-400" />
          <span>Actionable Mitigations</span>
        </h3>
        <p className="text-sm text-white/60">
          Recommended actions to reduce risk with cost/benefit analysis
        </p>
      </div>

      <div className="space-y-4">
        {sortedMitigations.map((mitigation, idx) => {
          const roi = mitigation.riskReductionPercent / (mitigation.cost / 1000);
          const roiColor = getROIColor(mitigation.riskReductionPercent, mitigation.cost);

          return (
            <div
              key={idx}
              className="p-4 bg-white/5 rounded-xl border border-white/10 hover:border-white/20 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="text-sm font-semibold text-white">{mitigation.action}</h4>
                    {idx === 0 && (
                      <span className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                        BEST ROI
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-white/70">{mitigation.action}</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <DollarSign className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs text-white/60">Cost</span>
                  </div>
                  <div className="text-lg font-bold text-white">
                    {formatCurrency(mitigation.cost)}
                  </div>
                </div>
                <div className="p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingDown className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs text-white/60">Risk Reduction</span>
                  </div>
                  <div className="text-lg font-bold text-emerald-400">
                    {mitigation.riskReductionPercent.toFixed(0)}%
                  </div>
                </div>
                <div className="p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-4 h-4 text-blue-400" />
                    <span className="text-xs text-white/60">Payback Period</span>
                  </div>
                  <div className="text-lg font-bold text-blue-400">
                    {mitigation.paybackPeriod}
                  </div>
                </div>
              </div>

              {/* ROI Indicator */}
              <div className="mt-3 pt-3 border-t border-white/10">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-white/60">ROI (Risk Reduction per $1K):</span>
                  <span className={`font-semibold ${roiColor}`}>
                    {roi.toFixed(1)}% per $1K
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-6 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-white/80">
            <p>
              <strong className="text-blue-400">Mitigation Priority:</strong> Actions are sorted by risk reduction impact. 
              Higher ROI (risk reduction per $1K spent) indicates better value.
            </p>
            <p className="text-xs text-white/60 mt-2">
              Consider implementing multiple mitigations for cumulative risk reduction.
            </p>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
