import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import type { ScenarioDataPoint } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';

interface RiskScenarioFanChartProps {
  data: ScenarioDataPoint[];
  etd: string;
  eta: string;
}

export const RiskScenarioFanChart: React.FC<RiskScenarioFanChartProps> = ({ data, etd, eta }) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Defensive guard: handle empty or invalid data
  if (!data || data.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <p className="text-sm">No scenario projection data available</p>
          <p className="text-xs text-white/30 mt-1">Scenario projection data is required for this chart</p>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-white">Risk Scenario Projections</h3>
        <p className="text-sm text-white/60">ETD: {etd || 'N/A'} → ETA: {eta || 'N/A'}</p>
      </div>
      <div 
        ref={containerRef}
        style={{ height: '400px', minHeight: '400px', minWidth: '300px', width: '100%', position: 'relative' }}
      >
        {containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <AreaChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={data}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="date" tick={{ fill: 'rgba(255,255,255,0.6)' }} />
            <YAxis tick={{ fill: 'rgba(255,255,255,0.6)' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0,0,0,0.9)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
              }}
            />
            <Area
              type="monotone"
              dataKey="p90"
              stackId="1"
              stroke="none"
              fill="rgba(59,130,246,0.1)"
              name="90th Percentile"
            />
            <Area
              type="monotone"
              dataKey="p10"
              stackId="1"
              stroke="none"
              fill="rgba(59,130,246,0.1)"
              name="10th Percentile"
            />
            <Area
              type="monotone"
              dataKey="p50"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="none"
              name="Median"
            />
            {data.some((d) => d.expected !== undefined) && (
              <Area
                type="monotone"
                dataKey="expected"
                stroke="#F59E0B"
                strokeWidth={2}
                strokeDasharray="5 5"
                fill="none"
                name="Expected"
              />
            )}
          </AreaChart>
        ) : (
          <ChartSkeleton height={400} />
        )}
      </div>
    </GlassCard>
  );
};




