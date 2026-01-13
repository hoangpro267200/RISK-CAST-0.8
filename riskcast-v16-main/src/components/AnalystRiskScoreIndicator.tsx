import React from 'react';

interface AnalystRiskScoreIndicatorProps {
  score: number;
  verdict: string;
  confidence: number;
}

export const AnalystRiskScoreIndicator: React.FC<AnalystRiskScoreIndicatorProps> = ({ score, verdict, confidence }) => {
  return (
    <div className="flex items-center justify-between p-6 bg-black/20 rounded-2xl border border-white/10">
      <div>
        <div className="text-sm text-white/60 mb-1">Analyst View</div>
        <div className="text-3xl font-bold text-white">{Math.round(score)}</div>
        <div className="text-sm text-white/60 mt-1">{verdict}</div>
      </div>
      <div className="text-right">
        <div className="text-sm text-white/60">Confidence</div>
        <div className="text-2xl font-semibold text-white">{Math.round(confidence * 100)}%</div>
      </div>
    </div>
  );
};




