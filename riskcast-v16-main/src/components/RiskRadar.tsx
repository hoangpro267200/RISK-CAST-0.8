import React from 'react';
import type { LayerData } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';

interface RiskRadarProps {
  layers: LayerData[];
}

export const RiskRadar: React.FC<RiskRadarProps> = ({ layers }) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Defensive guard: handle empty or invalid data
  if (!layers || layers.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <p className="text-sm">No layer data available</p>
          <p className="text-xs text-white/30 mt-1">Layer data is required for this chart</p>
        </div>
      </GlassCard>
    );
  }

  const data = layers
    .filter(layer => layer != null)
    .map((layer) => ({
      name: (layer.name || 'Unknown').replace(' Risk', ''),
      value: layer.score ?? 0,
      fullMark: 100,
    }));

  return (
    <GlassCard>
      <h3 className="text-lg font-medium text-white mb-4">Risk Profile Radar</h3>
      <div 
        ref={containerRef}
        style={{ height: '400px', minHeight: '400px', minWidth: '300px', width: '100%', position: 'relative' }}
      >
        {containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <RadarChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={data}
          >
            <PolarGrid stroke="rgba(255,255,255,0.2)" />
            <PolarAngleAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 10 }} />
            <Radar
              name="Risk Score"
              dataKey="value"
              stroke="#3B82F6"
              fill="#3B82F6"
              fillOpacity={0.3}
              strokeWidth={2}
            />
          </RadarChart>
        ) : (
          <ChartSkeleton height={400} />
        )}
      </div>
    </GlassCard>
  );
};




