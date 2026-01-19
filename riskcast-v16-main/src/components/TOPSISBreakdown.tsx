/**
 * TOPSIS Breakdown Component
 * 
 * Shows how alternatives (scenarios) were ranked using TOPSIS methodology.
 * Displays D+ (distance to best), D- (distance to worst), and C* (closeness coefficient).
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import type { TOPSISData } from '../types/algorithmTypes';
import { Info, TrendingUp } from 'lucide-react';

interface TOPSISBreakdownProps {
  topsisData: TOPSISData;
}

// Bar visualization component
const DistanceBar: React.FC<{ value: number; max: number; label: string; color: string }> = ({ 
  value, 
  max, 
  label, 
  color 
}) => {
  const percentage = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="w-16 text-xs text-white/60 text-right">{label}</div>
      <div className="flex-1 h-6 bg-white/10 rounded-full overflow-hidden relative">
        <div 
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${percentage}%` }}
        />
        <div className="absolute inset-0 flex items-center justify-center text-xs text-white font-medium">
          {value.toFixed(3)}
        </div>
      </div>
    </div>
  );
};

export const TOPSISBreakdown: React.FC<TOPSISBreakdownProps> = ({ topsisData }) => {
  // Defensive guard
  if (!topsisData || !topsisData.alternatives || topsisData.alternatives.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Info className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">TOPSIS breakdown unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not determine TOPSIS rankings. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Sort by rank
  const sortedAlternatives = [...topsisData.alternatives].sort((a, b) => a.rank - b.rank);
  const maxDistance = Math.max(
    ...sortedAlternatives.flatMap(a => [a.positiveIdealDistance, a.negativeIdealDistance])
  );

  // Get color for C* value
  const getCStarColor = (cStar: number) => {
    if (cStar >= 0.7) return 'text-emerald-400';
    if (cStar >= 0.5) return 'text-amber-400';
    return 'text-red-400';
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-400" />
          <span>TOPSIS Score Breakdown</span>
        </h3>
        <p className="text-sm text-white/60">
          Ranking of alternatives by distance from ideal solutions
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Rank</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Scenario</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-white/60">D+ (to Best)</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-white/60">D- (to Worst)</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-white/60">C* (Closeness)</th>
            </tr>
          </thead>
          <tbody>
            {sortedAlternatives.map((alt, idx) => (
              <tr 
                key={alt.id} 
                className="border-b border-white/5 hover:bg-white/5 transition-colors"
              >
                <td className="py-4 px-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                    alt.rank === 1 
                      ? 'bg-emerald-500/20 text-emerald-400 border-2 border-emerald-500/40'
                      : 'bg-white/10 text-white/70'
                  }`}>
                    {alt.rank}
                  </div>
                </td>
                <td className="py-4 px-4">
                  <span className="text-white font-medium">{alt.name}</span>
                </td>
                <td className="py-4 px-4">
                  <DistanceBar 
                    value={alt.positiveIdealDistance} 
                    max={maxDistance} 
                    label="D+"
                    color="bg-red-500/30"
                  />
                </td>
                <td className="py-4 px-4">
                  <DistanceBar 
                    value={alt.negativeIdealDistance} 
                    max={maxDistance} 
                    label="D-"
                    color="bg-emerald-500/30"
                  />
                </td>
                <td className="py-4 px-4">
                  <span className={`text-lg font-bold ${getCStarColor(alt.closenessCoefficient)}`}>
                    {alt.closenessCoefficient.toFixed(3)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Methodology Explainer */}
      <details className="mt-6 pt-4 border-t border-white/10">
        <summary className="cursor-pointer text-sm text-white/70 hover:text-white/90 flex items-center gap-2">
          <Info className="w-4 h-4" />
          <span>How TOPSIS Works</span>
        </summary>
        <div className="mt-3 p-4 bg-white/5 rounded-lg text-sm text-white/70 space-y-2">
          <p>
            <strong className="text-white">TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)</strong> 
            ranks alternatives by their distance from the best (positive ideal) and worst (negative ideal) solutions.
          </p>
          <p>
            <strong className="text-white">Closeness Coefficient (C*) = D- / (D+ + D-)</strong>
          </p>
          <ul className="list-disc list-inside space-y-1 text-xs text-white/60 ml-2">
            <li><strong className="text-white">D+</strong> = Distance to positive ideal (best case scenario)</li>
            <li><strong className="text-white">D-</strong> = Distance to negative ideal (worst case scenario)</li>
            <li><strong className="text-white">C*</strong> ranges from 0 (worst) to 1 (best)</li>
            <li>Higher C* = Better scenario (closer to ideal, farther from worst)</li>
          </ul>
        </div>
      </details>
    </GlassCard>
  );
};
