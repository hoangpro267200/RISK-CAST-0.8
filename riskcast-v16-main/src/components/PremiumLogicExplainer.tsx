/**
 * Premium Logic Explainer Component
 * 
 * Explains how insurance premium was calculated with step-by-step breakdown.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { PremiumLogicData } from '../types/insuranceTypes';
import { Calculator, TrendingDown, Info } from 'lucide-react';

interface PremiumLogicExplainerProps {
  premiumLogic: PremiumLogicData;
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

export const PremiumLogicExplainer: React.FC<PremiumLogicExplainerProps> = ({ premiumLogic }) => {
  // Defensive guard
  if (!premiumLogic) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Calculator className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Premium calculation data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not calculate premium logic. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  const savings = premiumLogic.marketRate - premiumLogic.riskcastRate;
  const savingsPercent = premiumLogic.marketRate > 0 
    ? ((savings / premiumLogic.marketRate) * 100).toFixed(1)
    : '0';

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Calculator className="w-5 h-5 text-purple-400" />
          <span>Premium Calculation Logic</span>
        </h3>
        <p className="text-sm text-white/60">
          Step-by-step breakdown of insurance premium calculation
        </p>
      </div>

      {/* Step-by-Step Calculation */}
      <div className="space-y-4 mb-6">
        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold flex items-center justify-center">1</span>
            <span className="text-sm font-semibold text-white">Expected Loss Calculation</span>
          </div>
          <div className="ml-8 space-y-1">
            <div className="text-sm text-white/70">
              Monte Carlo P50 (median loss): <span className="text-white font-medium">{formatCurrency(premiumLogic.expectedLoss)}</span>
            </div>
            <div className="text-xs text-white/50">
              Weighted by probability distribution
            </div>
          </div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold flex items-center justify-center">2</span>
            <span className="text-sm font-semibold text-white">Load Factor Application</span>
          </div>
          <div className="ml-8 space-y-1">
            <div className="text-sm text-white/70">
              Administrative costs: <span className="text-white font-medium">10%</span>
            </div>
            <div className="text-sm text-white/70">
              Profit margin: <span className="text-white font-medium">8%</span>
            </div>
            <div className="text-sm text-white/70">
              Reinsurance cost: <span className="text-white font-medium">7%</span>
            </div>
            <div className="text-sm text-white/70 mt-2">
              Total Load Factor: <span className="text-white font-medium">{premiumLogic.loadFactor.toFixed(2)}x</span>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold flex items-center justify-center">3</span>
            <span className="text-sm font-semibold text-white">Premium Calculation</span>
          </div>
          <div className="ml-8 space-y-1">
            <div className="text-sm text-white/70">
              Base Premium = {formatCurrency(premiumLogic.expectedLoss)} × {premiumLogic.loadFactor.toFixed(2)} = <span className="text-white font-medium">{formatCurrency(premiumLogic.expectedLoss * premiumLogic.loadFactor)}</span>
            </div>
            <div className="text-xs text-white/50">
              Risk adjustment applied based on risk score
            </div>
            <div className="text-lg font-bold text-cyan-400 mt-2">
              Calculated Premium: {formatCurrency(premiumLogic.calculatedPremium)}
            </div>
          </div>
        </div>
      </div>

      {/* Market Comparison */}
      <div className="mb-6 p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg border border-blue-500/20">
        <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingDown className="w-4 h-4 text-blue-400" />
          Market Comparison
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-2 px-3 text-white/60 font-medium">Metric</th>
                <th className="text-right py-2 px-3 text-white/60 font-medium">Market</th>
                <th className="text-right py-2 px-3 text-white/60 font-medium">RISKCAST</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-white/5">
                <td className="py-2 px-3 text-white/80">Rate</td>
                <td className="py-2 px-3 text-right text-white/80">{formatPercent(premiumLogic.marketRate)}</td>
                <td className="py-2 px-3 text-right text-cyan-400 font-semibold">{formatPercent(premiumLogic.riskcastRate)}</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-2 px-3 text-white/80">Premium</td>
                <td className="py-2 px-3 text-right text-white/80">{formatCurrency(premiumLogic.marketRate * premiumLogic.expectedLoss / 100)}</td>
                <td className="py-2 px-3 text-right text-cyan-400 font-semibold">{formatCurrency(premiumLogic.calculatedPremium)}</td>
              </tr>
              <tr>
                <td className="py-2 px-3 text-white/80 font-medium">Savings</td>
                <td className="py-2 px-3 text-right">—</td>
                <td className="py-2 px-3 text-right text-emerald-400 font-semibold">
                  {formatCurrency(savings)} ({savingsPercent}%)
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Explanation */}
      <div className="p-4 bg-white/5 rounded-lg border border-white/10">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-white/80">
            <p className="mb-2">
              <strong className="text-white">Why RISKCAST rate is lower:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1 text-xs text-white/70 ml-2">
              <li>More granular risk assessment (not broad category averages)</li>
              <li>Route-specific data (not generic route patterns)</li>
              <li>Real-time port congestion data</li>
              <li>Algorithm-optimized pricing based on actual risk factors</li>
            </ul>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
