import React from 'react';
import type { LayerData } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

interface RiskScoreConfidenceOverlayProps {
  layers: LayerData[];
}

export const RiskScoreConfidenceOverlay: React.FC<RiskScoreConfidenceOverlayProps> = ({ layers }) => {
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
      score: layer.score ?? 0,
      confidence: (layer.confidence ?? 50) / 100,
    }));

  return (
    <GlassCard>
      <h3 className="text-lg font-medium text-white mb-4">Layer Confidence Overlay</h3>
      <div 
        ref={containerRef}
        style={{ height: '400px', minHeight: '400px', minWidth: '300px', width: '100%', position: 'relative' }}
      >
        {containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <BarChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={data} 
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={60}
              tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
            />
            <YAxis tick={{ fill: 'rgba(255,255,255,0.6)' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0,0,0,0.9)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
              }}
            />
            <Bar dataKey="score" fill="#3B82F6" radius={[4, 4, 0, 0]} />
          </BarChart>
        ) : (
          <ChartSkeleton height={400} />
        )}
      </div>
    </GlassCard>
  );
};




