/**
 * Basis Risk Score Component
 * 
 * Displays basis risk score for parametric insurance triggers.
 * Basis risk = risk that a parametric trigger doesn't match actual loss.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { BasisRiskData } from '../types/insuranceTypes';
import { Shield, CheckCircle2, AlertCircle, XCircle, Info } from 'lucide-react';

interface BasisRiskScoreProps {
  basisRisk: BasisRiskData;
}

// Get interpretation color and icon
const getInterpretationStyle = (interpretation: BasisRiskData['interpretation']) => {
  switch (interpretation) {
    case 'low':
      return {
        color: 'text-emerald-400',
        bgColor: 'bg-emerald-500/20',
        borderColor: 'border-emerald-500/30',
        icon: CheckCircle2,
        label: 'LOW',
      };
    case 'moderate':
      return {
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/20',
        borderColor: 'border-amber-500/30',
        icon: AlertCircle,
        label: 'MODERATE',
      };
    case 'high':
      return {
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-500/30',
        icon: XCircle,
        label: 'HIGH',
      };
  }
};

export const BasisRiskScore: React.FC<BasisRiskScoreProps> = ({ basisRisk }) => {
  // Defensive guard
  if (!basisRisk) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Shield className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Basis risk data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not calculate basis risk. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  const style = getInterpretationStyle(basisRisk.interpretation);
  const Icon = style.icon;

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-400" />
          <span>Basis Risk Score</span>
        </h3>
        <p className="text-sm text-white/60">
          Risk that parametric triggers don't match actual loss exposure
        </p>
      </div>

      {/* Score Display */}
      <div className={`mb-6 p-6 rounded-xl border ${style.bgColor} ${style.borderColor}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-16 h-16 rounded-full ${style.bgColor} border-2 ${style.borderColor} flex items-center justify-center`}>
              <Icon className={`w-8 h-8 ${style.color}`} />
            </div>
            <div>
              <div className="text-sm text-white/60 mb-1">Basis Risk Score</div>
              <div className={`text-3xl font-bold ${style.color}`}>
                {basisRisk.score.toFixed(3)}
              </div>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-full border ${style.bgColor} ${style.borderColor}`}>
            <span className={`text-sm font-semibold ${style.color}`}>
              {style.label}
            </span>
          </div>
        </div>

        <div className="pt-4 border-t border-white/10">
          <p className="text-sm text-white/80">{basisRisk.explanation}</p>
        </div>
      </div>

      {/* Interpretation Guide */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-white mb-3">Basis Risk Interpretation</h4>
        <div className="space-y-2">
          <div className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-emerald-400 mb-1">Low (0.00 - 0.15)</div>
              <div className="text-xs text-white/70">
                Trigger closely matches actual loss exposure. Parametric insurance is reliable.
              </div>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-amber-400 mb-1">Moderate (0.15 - 0.30)</div>
              <div className="text-xs text-white/70">
                Some mismatch possible. Review trigger design. Consider hybrid coverage.
              </div>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
            <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-red-400 mb-1">High (0.30 - 1.00)</div>
              <div className="text-xs text-white/70">
                Significant mismatch. Traditional indemnity insurance may be better.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Methodology Explainer */}
      <details className="mt-6 pt-4 border-t border-white/10">
        <summary className="cursor-pointer text-sm text-white/70 hover:text-white/90 flex items-center gap-2">
          <Info className="w-4 h-4" />
          <span>What is Basis Risk?</span>
        </summary>
        <div className="mt-3 p-4 bg-white/5 rounded-lg text-sm text-white/70 space-y-2">
          <p>
            <strong className="text-white">Basis Risk</strong> measures how well a parametric trigger 
            (e.g., "delay > 7 days") correlates with actual financial loss.
          </p>
          <p>
            Low basis risk means the trigger reliably indicates when losses occur. High basis risk means 
            the trigger may activate when there's no loss, or fail to activate when there is a loss.
          </p>
          <p className="text-xs text-white/50 mt-2">
            For parametric insurance to be effective, basis risk should be low (&lt; 0.15).
          </p>
        </div>
      </details>
    </GlassCard>
  );
};
