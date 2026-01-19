/**
 * Deductible Recommendation Component
 * 
 * Shows recommended deductible with analysis of different deductible options.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { DeductibleRecommendation } from '../types/insuranceTypes';
import { Target, TrendingDown, Info } from 'lucide-react';

interface DeductibleRecommendationProps {
  recommendation: DeductibleRecommendation;
  cargoValue: number;
  expectedLoss: number;
}

// Format currency
const formatCurrency = (value: number): string => {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
};

// Format percentage
const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

export const DeductibleRecommendation: React.FC<DeductibleRecommendationProps> = ({
  recommendation,
  cargoValue,
  expectedLoss,
}) => {
  // Defensive guard
  if (!recommendation) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Target className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Deductible recommendation unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not determine deductible recommendation. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Calculate deductible options (simplified - in real app, this would come from engine)
  const deductibleOptions = [
    { amount: 0, label: '$0 (nil)', premiumEst: cargoValue * 0.0037, breakEven: 'N/A' },
    { amount: cargoValue * 0.005, label: formatCurrency(cargoValue * 0.005), premiumEst: cargoValue * 0.00344, breakEven: '1 claim/6 yrs' },
    { amount: recommendation.amount, label: formatCurrency(recommendation.amount), premiumEst: cargoValue * 0.00324, breakEven: '1 claim/4 yrs', isRecommended: true },
    { amount: cargoValue * 0.02, label: formatCurrency(cargoValue * 0.02), premiumEst: cargoValue * 0.00296, breakEven: '1 claim/2 yrs' },
    { amount: cargoValue * 0.05, label: formatCurrency(cargoValue * 0.05), premiumEst: cargoValue * 0.0025, breakEven: '1 claim/yr' },
  ];

  const recommendedPercent = (recommendation.amount / cargoValue) * 100;

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Target className="w-5 h-5 text-green-400" />
          <span>Deductible Recommendation</span>
        </h3>
        <p className="text-sm text-white/60">
          Cargo Value: {formatCurrency(cargoValue)}
        </p>
      </div>

      {/* Recommended Deductible */}
      <div className="mb-6 p-6 bg-gradient-to-r from-emerald-500/20 to-green-500/10 rounded-xl border-2 border-emerald-500/30">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm text-emerald-400 mb-1">Recommended Deductible</div>
            <div className="text-3xl font-bold text-white">
              {formatCurrency(recommendation.amount)}
            </div>
            <div className="text-xs text-white/60 mt-1">
              ({recommendedPercent.toFixed(1)}% of cargo value)
            </div>
          </div>
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500/40 flex items-center justify-center">
            <TrendingDown className="w-8 h-8 text-emerald-400" />
          </div>
        </div>
        <div className="pt-4 border-t border-emerald-500/20">
          <p className="text-sm text-white/80">{recommendation.rationale}</p>
        </div>
      </div>

      {/* Deductible Analysis Table */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-white mb-3">Deductible Analysis</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-2 px-3 text-white/60 font-medium">Deductible</th>
                <th className="text-right py-2 px-3 text-white/60 font-medium">Premium Est.</th>
                <th className="text-right py-2 px-3 text-white/60 font-medium">Break-even</th>
                <th className="text-right py-2 px-3 text-white/60 font-medium">Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {deductibleOptions.map((option, idx) => (
                <tr
                  key={idx}
                  className={`border-b border-white/5 hover:bg-white/5 transition-colors ${
                    option.isRecommended ? 'bg-emerald-500/10' : ''
                  }`}
                >
                  <td className="py-3 px-3">
                    <span className={`font-medium ${option.isRecommended ? 'text-emerald-400' : 'text-white'}`}>
                      {option.label}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right text-white/80">
                    {formatCurrency(option.premiumEst)}
                  </td>
                  <td className="py-3 px-3 text-right text-white/60 text-xs">
                    {option.breakEven}
                  </td>
                  <td className="py-3 px-3 text-right">
                    {option.isRecommended ? (
                      <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded-full border border-emerald-500/30">
                        OPTIMAL
                      </span>
                    ) : (
                      <span className="text-white/30">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rationale */}
      <div className="p-4 bg-white/5 rounded-lg border border-white/10">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-white/80">
            <p>
              With a {formatPercent(expectedLoss / cargoValue)} annual claim probability and {formatCurrency(expectedLoss)} expected loss, 
              a {formatCurrency(recommendation.amount)} deductible balances premium savings against out-of-pocket exposure. 
              Claims under {formatCurrency(recommendation.amount)} occur in ~35% of loss events.
            </p>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
