import React from 'react';
import { GlassCard } from './GlassCard';

export interface PrimaryRecommendationCardProps {
  title: string;
  badge: string;
  riskReduction: number;
  costImpact: string;
  confidence: number;
  rationale: string;
  currentRisk: number;
  newRisk?: number;
}

export const PrimaryRecommendationCard: React.FC<PrimaryRecommendationCardProps> = ({
  title,
  badge,
  riskReduction,
  costImpact,
  confidence,
  rationale,
  currentRisk,
  newRisk,
}) => {
  return (
    <GlassCard padding="lg" className="border-2 border-blue-500/30">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-xs text-blue-400 font-medium mb-1">{badge}</div>
          <h3 className="text-2xl font-bold text-white">{title}</h3>
        </div>
        <div className="text-right">
          <div className="text-sm text-white/60">Confidence</div>
          <div className="text-lg font-semibold text-white">{Math.round(confidence * 100)}%</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-sm text-white/60">Risk Reduction</div>
          <div className={`text-2xl font-bold ${riskReduction > 0 ? 'text-green-400' : 'text-emerald-400/70'}`}>
            {riskReduction > 0 ? `-${riskReduction} pts` : '—'}
          </div>
          {riskReduction === 0 && currentRisk < 30 && (
            <div className="text-xs text-emerald-400/60 mt-1">Already optimal</div>
          )}
        </div>
        <div>
          <div className="text-sm text-white/60">Cost Impact</div>
          <div className="text-xl font-semibold text-white">{costImpact}</div>
        </div>
      </div>

      {newRisk !== undefined && (
        <div className="mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
          <div className="text-xs text-white/60 mb-1">Projected Risk Score</div>
          <div className="flex items-center gap-3">
            <span className="text-white/60">{currentRisk}</span>
            <span className="text-white/40">→</span>
            <span className="text-xl font-bold text-white">{newRisk}</span>
          </div>
        </div>
      )}

      <div className="pt-4 border-t border-white/10">
        <div className="text-sm font-medium text-white/80 mb-2">Rationale</div>
        <p className="text-sm text-white/60">{rationale}</p>
      </div>
    </GlassCard>
  );
};




