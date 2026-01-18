/**
 * Trigger Probability Table Component
 * 
 * Displays parametric trigger probabilities with expected payouts and premium estimates.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { TriggerProbability } from '../types/insuranceTypes';
import { Zap, Info } from 'lucide-react';

interface TriggerProbabilityTableProps {
  triggers: TriggerProbability[];
}

// Format currency
const formatCurrency = (value: number): string => {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
};

// Format percentage
const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(0)}%`;
};

export const TriggerProbabilityTable: React.FC<TriggerProbabilityTableProps> = ({ triggers }) => {
  // Defensive guard
  if (!triggers || triggers.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Zap className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Trigger probability data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not calculate trigger probabilities. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Calculate premium estimate (Probability × Expected Loss × Load Factor 1.0x)
  const calculatePremium = (trigger: TriggerProbability): number => {
    return trigger.probability * trigger.expectedPayout * 1.0;
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" />
          <span>Parametric Trigger Probabilities</span>
        </h3>
        <p className="text-sm text-white/60">
          Probability of trigger events and estimated payouts
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Trigger Event</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-white/60">Probability</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-white/60">Expected Loss</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-white/60">Premium Est.</th>
            </tr>
          </thead>
          <tbody>
            {triggers.map((trigger, idx) => {
              const premium = calculatePremium(trigger);
              const probabilityPercent = trigger.probability * 100;
              
              // Color code by probability
              const getProbabilityColor = (prob: number) => {
                if (prob >= 0.2) return 'text-red-400';
                if (prob >= 0.1) return 'text-amber-400';
                return 'text-emerald-400';
              };

              return (
                <tr 
                  key={idx}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        trigger.probability >= 0.2 ? 'bg-red-400' :
                        trigger.probability >= 0.1 ? 'bg-amber-400' :
                        'bg-emerald-400'
                      }`} />
                      <span className="text-white font-medium">{trigger.trigger}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${
                            trigger.probability >= 0.2 ? 'bg-red-500' :
                            trigger.probability >= 0.1 ? 'bg-amber-500' :
                            'bg-emerald-500'
                          }`}
                          style={{ width: `${probabilityPercent}%` }}
                        />
                      </div>
                      <span className={`text-sm font-semibold min-w-[50px] ${getProbabilityColor(trigger.probability)}`}>
                        {formatPercent(trigger.probability)}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <span className="text-white font-medium">{formatCurrency(trigger.expectedPayout)}</span>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <span className="text-cyan-400 font-medium">{formatCurrency(premium)}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Note */}
      <div className="mt-6 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-white/80">
            <p className="mb-2">
              <strong className="text-blue-400">Calculation:</strong> Premium = Probability × Expected Loss × Load Factor (1.0x)
            </p>
            <p className="text-xs text-white/60">
              <strong>Note:</strong> Multiple triggers can occur simultaneously. Combined probability of ANY trigger: {
                formatPercent(Math.min(1, triggers.reduce((sum, t) => sum + t.probability, 0)))
              }. This does not mean {formatPercent(Math.min(1, triggers.reduce((sum, t) => sum + t.probability, 0)))} chance of loss.
            </p>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
