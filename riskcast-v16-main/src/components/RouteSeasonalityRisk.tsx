/**
 * Route Seasonality Risk Component
 * 
 * Displays route seasonality analysis with climatic indices and risk factors.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { RouteSeasonalityData } from '../types/logisticsTypes';
import { Cloud, TrendingUp, Info } from 'lucide-react';

interface RouteSeasonalityRiskProps {
  seasonality: RouteSeasonalityData;
}

// Get risk level color
const getRiskColor = (riskLevel: RouteSeasonalityData['riskLevel']) => {
  switch (riskLevel) {
    case 'HIGH':
      return 'text-red-400 bg-red-500/20 border-red-500/30';
    case 'MEDIUM':
      return 'text-amber-400 bg-amber-500/20 border-amber-500/30';
    case 'LOW':
      return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30';
  }
};

export const RouteSeasonalityRisk: React.FC<RouteSeasonalityRiskProps> = ({ seasonality }) => {
  // Defensive guard
  if (!seasonality) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Cloud className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Route seasonality data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not determine route seasonality. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  const riskColor = getRiskColor(seasonality.riskLevel);

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Cloud className="w-5 h-5 text-cyan-400" />
          <span>Route Seasonality Risk</span>
        </h3>
        <p className="text-sm text-white/60">
          Seasonal weather patterns and climatic conditions affecting this route
        </p>
      </div>

      {/* Overall Risk */}
      <div className={`mb-6 p-6 rounded-xl border ${riskColor}`}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm text-white/60 mb-1">Season</div>
            <div className="text-2xl font-bold text-white">{seasonality.season}</div>
          </div>
          <div className={`px-4 py-2 rounded-full border ${riskColor}`}>
            <span className="text-sm font-semibold">
              {seasonality.riskLevel} RISK
            </span>
          </div>
        </div>
      </div>

      {/* Risk Factors */}
      {seasonality.factors.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-white mb-3">Seasonal Risk Factors</h4>
          <div className="space-y-2">
            {seasonality.factors.map((factor, idx) => (
              <div key={idx} className="p-3 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-start gap-3">
                  <TrendingUp className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white mb-1">{factor.factor}</div>
                    <div className="text-xs text-white/60">{factor.impact}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Climatic Indices */}
      {seasonality.climaticIndices.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-white mb-3">Climatic Indices</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-2 px-3 text-white/60 font-medium">Index</th>
                  <th className="text-right py-2 px-3 text-white/60 font-medium">Value</th>
                  <th className="text-left py-2 px-3 text-white/60 font-medium">Interpretation</th>
                </tr>
              </thead>
              <tbody>
                {seasonality.climaticIndices.map((index, idx) => (
                  <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-3 px-3 text-white font-medium">{index.name}</td>
                    <td className="py-3 px-3 text-right">
                      <span className={`font-semibold ${
                        Math.abs(index.value) > 1 ? 'text-amber-400' :
                        Math.abs(index.value) > 0.5 ? 'text-blue-400' :
                        'text-emerald-400'
                      }`}>
                        {index.value > 0 ? '+' : ''}{index.value.toFixed(2)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-white/70 text-xs">{index.interpretation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Methodology Explainer */}
      <details className="mt-6 pt-4 border-t border-white/10">
        <summary className="cursor-pointer text-sm text-white/70 hover:text-white/90 flex items-center gap-2">
          <Info className="w-4 h-4" />
          <span>How Seasonality Risk is Calculated</span>
        </summary>
        <div className="mt-3 p-4 bg-white/5 rounded-lg text-sm text-white/70 space-y-2">
          <p>
            Seasonality risk is calculated based on historical weather patterns, climatic indices 
            (ENSO, PDO, MJO), and route-specific seasonal variations.
          </p>
          <p>
            Factors include storm frequency, wave height, temperature extremes, and port congestion 
            patterns that vary by season.
          </p>
        </div>
      </details>
    </GlassCard>
  );
};
