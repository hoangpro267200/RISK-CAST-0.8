import React from 'react';
import { GlassCard } from './GlassCard';

export interface SecondaryRecommendationCardProps {
  category: string;
  badge: {
    text: string;
    type: 'consider' | 'evaluate';
  };
  metric: string;
  context: string;
  confidence: number;
}

export const SecondaryRecommendationCard: React.FC<SecondaryRecommendationCardProps> = ({
  category,
  badge,
  metric,
  context,
  confidence,
}) => {
  const badgeColor = badge.type === 'consider' ? 'blue' : 'purple';

  return (
    <GlassCard padding="md">
      <div className="flex items-start justify-between mb-3">
        <div className="text-xs text-white/60">{category}</div>
        <div
          className={`px-2 py-1 rounded text-xs font-medium ${
            badgeColor === 'blue' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
          }`}
        >
          {badge.text}
        </div>
      </div>

      <div className="mb-3">
        <div className="text-lg font-semibold text-white">{metric}</div>
        <div className="text-sm text-white/60 mt-1">{context}</div>
      </div>

      <div className="pt-3 border-t border-white/10">
        <div className="flex items-center justify-between">
          <span className="text-xs text-white/60">Confidence</span>
          <span className="text-sm font-medium text-white">{Math.round(confidence * 100)}%</span>
        </div>
      </div>
    </GlassCard>
  );
};




