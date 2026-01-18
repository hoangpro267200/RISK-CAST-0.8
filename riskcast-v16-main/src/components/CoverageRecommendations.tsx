/**
 * Coverage Recommendations Component
 * 
 * Displays insurance coverage recommendations with priority levels.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { CoverageRecommendation } from '../types/insuranceTypes';
import { Shield, CheckCircle2, AlertCircle, Info } from 'lucide-react';

interface CoverageRecommendationsProps {
  recommendations: CoverageRecommendation[];
}

// Get priority badge style
const getPriorityStyle = (priority: CoverageRecommendation['priority']) => {
  switch (priority) {
    case 'required':
      return {
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-500/30',
        icon: AlertCircle,
        label: 'REQUIRED',
      };
    case 'recommended':
      return {
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/20',
        borderColor: 'border-amber-500/30',
        icon: CheckCircle2,
        label: 'RECOMMENDED',
      };
    case 'optional':
      return {
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/20',
        borderColor: 'border-blue-500/30',
        icon: Info,
        label: 'OPTIONAL',
      };
  }
};

export const CoverageRecommendations: React.FC<CoverageRecommendationsProps> = ({ recommendations }) => {
  // Defensive guard
  if (!recommendations || recommendations.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Shield className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Coverage recommendations unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not generate coverage recommendations. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Group by priority
  const required = recommendations.filter(r => r.priority === 'required');
  const recommended = recommendations.filter(r => r.priority === 'recommended');
  const optional = recommendations.filter(r => r.priority === 'optional');

  const renderRecommendation = (rec: CoverageRecommendation, idx: number) => {
    const style = getPriorityStyle(rec.priority);
    const Icon = style.icon;

    return (
      <div
        key={idx}
        className={`p-4 rounded-xl border ${style.bgColor} ${style.borderColor} mb-4`}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg ${style.bgColor} border ${style.borderColor} flex items-center justify-center`}>
              <Icon className={`w-5 h-5 ${style.color}`} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-lg font-semibold text-white">{rec.type}</h4>
                <span className={`text-xs px-2 py-1 rounded-full border ${style.bgColor} ${style.borderColor} ${style.color}`}>
                  {style.label}
                </span>
              </div>
              <p className="text-sm text-white/60">{rec.clause}</p>
            </div>
          </div>
        </div>
        <div className="pt-3 border-t border-white/10">
          <p className="text-sm text-white/80">{rec.rationale}</p>
        </div>
      </div>
    );
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-400" />
          <span>Coverage Recommendations</span>
        </h3>
        <p className="text-sm text-white/60">
          Insurance coverage recommendations based on your shipment risk profile
        </p>
      </div>

      <div className="space-y-6">
        {/* Required Coverage */}
        {required.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-red-400 mb-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              REQUIRED
            </h4>
            {required.map((rec, idx) => renderRecommendation(rec, idx))}
          </div>
        )}

        {/* Recommended Coverage */}
        {recommended.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-amber-400 mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              RECOMMENDED
            </h4>
            {recommended.map((rec, idx) => renderRecommendation(rec, idx))}
          </div>
        )}

        {/* Optional Coverage */}
        {optional.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-blue-400 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4" />
              OPTIONAL
            </h4>
            {optional.map((rec, idx) => renderRecommendation(rec, idx))}
          </div>
        )}
      </div>
    </GlassCard>
  );
};
