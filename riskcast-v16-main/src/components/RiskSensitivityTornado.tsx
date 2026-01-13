import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, LabelList } from 'recharts';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';

interface SensitivityDriver {
  name: string;
  impact: number;
  impactMagnitude?: number;
}

interface RiskSensitivityTornadoProps {
  drivers: SensitivityDriver[];
}

const formatPercentage = (value: number): string => {
  const absValue = Math.abs(value);
  if (absValue % 1 === 0) {
    return `${absValue}%`;
  }
  return `${absValue.toFixed(1)}%`;
};

const CustomLabel: React.FC<any> = ({ x, y, width, value, viewBox }) => {
  if (value === undefined || value === null || width === undefined || x === undefined || y === undefined) {
    return null;
  }
  
  const formattedValue = formatPercentage(value);
  const barEnd = (x as number) + (width as number);
  const chartWidth = viewBox?.width || 0;
  const marginRight = 60;
  const maxX = chartWidth - marginRight;
  const minBarWidthForInsideLabel = 60;
  
  const hasSpaceInside = (width as number) >= minBarWidthForInsideLabel && barEnd < maxX - 40;
  const labelX = hasSpaceInside ? barEnd - 6 : barEnd + 10;
  const textAnchor = hasSpaceInside ? 'end' : 'start';
  const fillColor = hasSpaceInside ? '#FFFFFF' : '#E5E7EB';
  
  return (
    <text
      x={labelX}
      y={y}
      fill={fillColor}
      textAnchor={textAnchor}
      dominantBaseline="middle"
      fontSize="12"
      fontWeight="600"
      style={{ 
        textShadow: '0 1px 3px rgba(0,0,0,0.9)',
        pointerEvents: 'none',
        userSelect: 'none',
        transition: 'font-size 0.2s ease'
      }}
    >
      {formattedValue}
    </text>
  );
};

export const RiskSensitivityTornado: React.FC<RiskSensitivityTornadoProps> = ({ drivers }) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Process and filter valid drivers
  const data = (drivers || [])
    .filter(d => d != null && d.name)
    .map((d) => ({
      name: d.name || 'Unknown',
      impact: d.impact ?? 0,
      absImpact: Math.abs(d.impact ?? 0),
    }))
    .filter(d => d.absImpact > 0);

  // Defensive guard: handle empty or invalid data
  if (data.length === 0) {
    return (
      <GlassCard>
        <h3 className="text-lg font-medium text-white mb-4">Sensitivity Analysis</h3>
        <div className="text-center py-12 text-white/60">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/10 flex items-center justify-center">
            <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-sm font-medium text-emerald-400">Low Risk - No Significant Drivers</p>
          <p className="text-xs text-white/40 mt-2 max-w-xs mx-auto">
            Risk score is below threshold. No significant risk drivers detected that require attention.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <h3 className="text-lg font-medium text-white mb-4">Sensitivity Analysis</h3>
      <div 
        ref={containerRef}
        style={{ height: '400px', minHeight: '400px', minWidth: '300px', width: '100%', position: 'relative' }}
      >
        {containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <BarChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={data} 
            layout="vertical" 
            margin={{ top: 20, right: 60, left: 100, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              type="number" 
              tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
              domain={[0, 'dataMax']}
            />
            <YAxis dataKey="name" type="category" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }} width={90} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0,0,0,0.95)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
                padding: '12px',
              }}
              formatter={(value: number | undefined) => [
                value !== undefined ? formatPercentage(value) : '0%',
                'Impact'
              ]}
              labelStyle={{
                color: '#FFFFFF',
                fontWeight: '600',
                marginBottom: '4px',
              }}
              itemStyle={{
                color: '#F3F4F6',
                fontSize: '13px',
              }}
            />
            <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.impact >= 0 ? '#EF4444' : '#10B981'}
                />
              ))}
              <LabelList 
                dataKey="impact" 
                content={<CustomLabel />}
                position="right"
              />
            </Bar>
          </BarChart>
        ) : (
          <ChartSkeleton height={400} />
        )}
      </div>
    </GlassCard>
  );
};




