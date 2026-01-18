/**
 * Latent Risks Table Component
 * 
 * Displays potential hidden risks that may not be immediately apparent.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { LatentRisk } from '../types/riskDisclosureTypes';
import { AlertTriangle, TrendingUp, Info } from 'lucide-react';

interface LatentRisksTableProps {
  latentRisks: LatentRisk[];
}

// Get severity color and icon
const getSeverityStyle = (severity: LatentRisk['severity']) => {
  switch (severity) {
    case 'HIGH':
      return {
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-500/30',
        icon: AlertTriangle,
      };
    case 'MEDIUM':
      return {
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/20',
        borderColor: 'border-amber-500/30',
        icon: TrendingUp,
      };
    case 'LOW':
      return {
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/20',
        borderColor: 'border-blue-500/30',
        icon: Info,
      };
  }
};

// Format probability
const formatProbability = (prob: number): string => {
  if (prob >= 0.1) return `${(prob * 100).toFixed(0)}%`;
  if (prob >= 0.01) return `${(prob * 100).toFixed(1)}%`;
  return `${(prob * 100).toFixed(2)}%`;
};

export const LatentRisksTable: React.FC<LatentRisksTableProps> = ({ latentRisks }) => {
  // Defensive guard
  if (!latentRisks || latentRisks.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Latent risks data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not identify latent risks. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Sort by severity (HIGH first) then probability
  const sortedRisks = [...latentRisks].sort((a, b) => {
    const severityOrder = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    if (severityOrder[a.severity] !== severityOrder[b.severity]) {
      return severityOrder[b.severity] - severityOrder[a.severity];
    }
    return b.probability - a.probability;
  });

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <span>Potential Hidden Risks</span>
        </h3>
        <p className="text-sm text-white/60">
          Risks that may not be immediately apparent but could impact your shipment
        </p>
      </div>

      <div className="space-y-4">
        {sortedRisks.map((risk, idx) => {
          const style = getSeverityStyle(risk.severity);
          const Icon = style.icon;

          return (
            <div
              key={risk.id || idx}
              className={`p-4 rounded-xl border ${style.bgColor} ${style.borderColor}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3 flex-1">
                  <div className={`w-10 h-10 rounded-lg ${style.bgColor} border ${style.borderColor} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-5 h-5 ${style.color}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-semibold text-white">{risk.name}</h4>
                      <span className={`text-xs px-2 py-1 rounded-full border ${style.bgColor} ${style.borderColor} ${style.color}`}>
                        {risk.severity}
                      </span>
                      <span className="text-xs text-white/50">
                        {risk.category}
                      </span>
                    </div>
                    <p className="text-sm text-white/80 mb-2">{risk.impact}</p>
                  </div>
                </div>
                <div className="text-right ml-4">
                  <div className="text-xs text-white/60 mb-1">Probability</div>
                  <div className={`text-lg font-bold ${style.color}`}>
                    {formatProbability(risk.probability)}
                  </div>
                </div>
              </div>
              
              <div className="pt-3 border-t border-white/10">
                <div className="flex items-start gap-2">
                  <span className="text-xs text-white/60">Mitigation:</span>
                  <span className="text-xs text-white/80 flex-1">{risk.mitigation}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
};
