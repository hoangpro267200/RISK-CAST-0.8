/**
 * Algorithm Explainability Panel
 * 
 * Houses all algorithm explanation components: FAHP, TOPSIS, and Monte Carlo.
 * Provides a unified view of how the risk score was calculated.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import { FAHPWeightChart } from './FAHPWeightChart';
import { TOPSISBreakdown } from './TOPSISBreakdown';
import { MonteCarloExplainer } from './MonteCarloExplainer';
import type { AlgorithmExplainabilityData } from '../types/algorithmTypes';
import { Brain, Info } from 'lucide-react';

interface AlgorithmExplainabilityPanelProps {
  algorithmData: AlgorithmExplainabilityData;
}

export const AlgorithmExplainabilityPanel: React.FC<AlgorithmExplainabilityPanelProps> = ({ 
  algorithmData 
}) => {
  // Defensive guard
  if (!algorithmData) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Brain className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Algorithm explainability data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not provide algorithm transparency data. Please re-run analysis with complete data.
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
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-2">Algorithm Explainability</h2>
            <p className="text-white/70 text-sm mb-3">
              Understand how your risk score was calculated using FAHP (weights), TOPSIS (ranking), 
              and Monte Carlo simulation (uncertainty modeling).
            </p>
            <div className="flex items-center gap-2 text-xs text-white/50">
              <Info className="w-4 h-4" />
              <span>This transparency enables insurance underwriters and risk managers to trust and verify the assessment.</span>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* FAHP Weights */}
      <FAHPWeightChart fahpData={algorithmData.fahp} />

      {/* TOPSIS Breakdown */}
      {algorithmData.topsis.alternatives.length > 0 && (
        <TOPSISBreakdown topsisData={algorithmData.topsis} />
      )}

      {/* Monte Carlo Explainer */}
      {algorithmData.monteCarlo.nSamples > 0 && (
        <MonteCarloExplainer monteCarloData={algorithmData.monteCarlo} />
      )}
    </div>
  );
};
