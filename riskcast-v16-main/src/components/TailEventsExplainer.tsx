/**
 * Tail Events Explainer Component
 * 
 * Explains tail risk events (P95, P99, max loss) with historical context.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { TailEvent, RiskThresholds } from '../types/riskDisclosureTypes';
import { AlertTriangle, TrendingDown, Info } from 'lucide-react';

interface TailEventsExplainerProps {
  tailEvents: TailEvent[];
  thresholds: RiskThresholds;
}

// Format currency
const formatCurrency = (value: number): string => {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
};

// Format probability
const formatProbability = (prob: number): string => {
  if (prob >= 0.1) return `${(prob * 100).toFixed(0)}%`;
  if (prob >= 0.01) return `${(prob * 100).toFixed(1)}%`;
  return `${(prob * 100).toFixed(2)}%`;
};

export const TailEventsExplainer: React.FC<TailEventsExplainerProps> = ({
  tailEvents,
  thresholds,
}) => {
  // Defensive guard
  if (!thresholds || (!tailEvents || tailEvents.length === 0)) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <TrendingDown className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Tail events data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not identify tail events. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <TrendingDown className="w-5 h-5 text-orange-400" />
          <span>Tail Risk Events</span>
        </h3>
        <p className="text-sm text-white/60">
          Extreme scenarios with low probability but high impact
        </p>
      </div>

      {/* Risk Thresholds Summary */}
      <div className="mb-6 grid grid-cols-3 gap-4">
        <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/20">
          <div className="text-xs text-amber-400 mb-1">P95 (Tail Threshold)</div>
          <div className="text-lg font-bold text-white">{formatCurrency(thresholds.p95)}</div>
          <div className="text-xs text-white/50 mt-1">95% of outcomes below</div>
        </div>
        <div className="p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
          <div className="text-xs text-orange-400 mb-1">P99 (Extreme)</div>
          <div className="text-lg font-bold text-white">{formatCurrency(thresholds.p99)}</div>
          <div className="text-xs text-white/50 mt-1">99% of outcomes below</div>
        </div>
        <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/20">
          <div className="text-xs text-red-400 mb-1">Max Loss</div>
          <div className="text-lg font-bold text-white">{formatCurrency(thresholds.maxLoss)}</div>
          <div className="text-xs text-white/50 mt-1">Worst case scenario</div>
        </div>
      </div>

      {/* Tail Events List */}
      {tailEvents.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-white mb-3">Identified Tail Events</h4>
          <div className="space-y-3">
            {tailEvents.map((event, idx) => (
              <div
                key={idx}
                className="p-4 bg-red-500/10 rounded-lg border border-red-500/20"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h5 className="text-sm font-semibold text-red-400 mb-1">{event.event}</h5>
                    <p className="text-xs text-white/70">{event.historicalPrecedent || 'No historical precedent'}</p>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-xs text-white/60 mb-1">Probability</div>
                    <div className="text-lg font-bold text-red-400">
                      {formatProbability(event.probability)}
                    </div>
                  </div>
                </div>
                <div className="pt-2 border-t border-red-500/20">
                  <div className="text-xs text-white/80">
                    Potential Loss: <span className="font-semibold text-red-400">{formatCurrency(event.potentialLoss)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interpretation */}
      <div className="p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-white/80">
            <p className="mb-2">
              <strong className="text-orange-400">Tail Risk Interpretation:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1 text-xs text-white/70 ml-2">
              <li><strong>P95 ({formatCurrency(thresholds.p95)}):</strong> 95% of outcomes are better than this. Tail risk starts here.</li>
              <li><strong>P99 ({formatCurrency(thresholds.p99)}):</strong> Extreme scenario with 1% probability. Requires contingency planning.</li>
              <li><strong>Max Loss ({formatCurrency(thresholds.maxLoss)}):</strong> Theoretical worst case. Consider parametric insurance for tail protection.</li>
            </ul>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
