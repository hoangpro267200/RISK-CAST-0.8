import React from 'react';
import type { DataDomain } from '../types';
import { GlassCard } from './GlassCard';

interface DataReliabilityMatrixProps {
  domains: DataDomain[];
}

export const DataReliabilityMatrix: React.FC<DataReliabilityMatrixProps> = ({ domains }) => {
  return (
    <GlassCard>
      <h3 className="text-lg font-medium text-white mb-4">Data Reliability Matrix</h3>
      <div className="space-y-3">
        {domains.map((domain) => (
          <div key={domain.domain} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
            <div>
              <div className="text-sm font-medium text-white">{domain.domain}</div>
              <div className="text-xs text-white/60 mt-1">{domain.notes}</div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-xs text-white/60">Confidence</div>
                <div className="text-sm font-semibold text-white">{Math.round(domain.confidence * 100)}%</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-white/60">Completeness</div>
                <div className="text-sm font-semibold text-white">{Math.round(domain.completeness * 100)}%</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-white/60">Freshness</div>
                <div className="text-sm font-semibold text-white">{Math.round(domain.freshness * 100)}%</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
};




