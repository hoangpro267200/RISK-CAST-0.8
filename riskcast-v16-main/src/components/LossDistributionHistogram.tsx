/**
 * Loss Distribution Histogram Component
 * 
 * Displays loss distribution histogram with overlaid CDF line.
 * Shows P50, P95, P99 markers and flags synthetic data.
 */

import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine, Legend
} from 'recharts';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import type { LossDistributionData } from '../types/insuranceTypes';
import { DollarSign, AlertTriangle, Info } from 'lucide-react';

interface LossDistributionHistogramProps {
  lossDistribution: LossDistributionData;
  expectedLoss: number;
  p95: number;
  p99: number;
}

// Custom tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const frequency = payload.find((p: any) => p.dataKey === 'frequency')?.value || 0;
    const cumulative = payload.find((p: any) => p.dataKey === 'cumulative')?.value || 0;
    
    return (
      <div className="bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[200px]">
        <div className="font-medium text-white mb-2 pb-2 border-b border-white/10">
          Loss: {label}
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-white/60">Frequency:</span>
            <span className="text-cyan-400 font-semibold">{(frequency * 100).toFixed(2)}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-white/60">Cumulative:</span>
            <span className="text-blue-400 font-semibold">{(cumulative * 100).toFixed(2)}%</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

// Format currency
const formatCurrency = (value: number): string => {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
};

export const LossDistributionHistogram: React.FC<LossDistributionHistogramProps> = ({
  lossDistribution,
  expectedLoss,
  p95,
  p99,
}) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Defensive guard
  if (!lossDistribution || !lossDistribution.histogram || lossDistribution.histogram.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <DollarSign className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Loss distribution data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not generate loss distribution. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Prepare chart data
  const chartData = lossDistribution.histogram.map(bucket => ({
    bucket: bucket.bucket,
    frequency: bucket.frequency,
    cumulative: bucket.cumulative,
  }));

  // Find bucket for markers
  const findBucketForValue = (value: number): number => {
    const bucket = chartData.find(d => {
      const range = d.bucket.match(/\$?([\d.]+)[KMB]?/g);
      if (range && range.length >= 2) {
        const min = parseFloat(range[0].replace(/[^0-9.]/g, '')) * (range[0].includes('K') ? 1000 : range[0].includes('M') ? 1000000 : 1);
        const max = parseFloat(range[1].replace(/[^0-9.]/g, '')) * (range[1].includes('K') ? 1000 : range[1].includes('M') ? 1000000 : 1);
        return value >= min && value <= max;
      }
      return false;
    });
    return bucket ? chartData.indexOf(bucket) : -1;
  };

  const chartWidth = containerSize.width > 0 ? containerSize.width : 800;
  const chartHeight = 400;

  return (
    <GlassCard>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-emerald-400" />
              <span>Loss Distribution</span>
            </h3>
            <p className="text-sm text-white/60">
              Probability distribution of potential losses
            </p>
          </div>
          {lossDistribution.isSynthetic && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full text-xs font-medium">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>ESTIMATED</span>
            </div>
          )}
        </div>

        {/* Synthetic Data Warning */}
        {lossDistribution.isSynthetic && (
          <div className="mb-4 p-4 bg-amber-500/10 rounded-lg border border-amber-500/20">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-amber-400 mb-1">Estimated Distribution</h4>
                <p className="text-xs text-white/70 mb-2">
                  This loss curve was generated using parametric estimation because insufficient 
                  historical data was available for this exact route/cargo combination.
                </p>
                <div className="text-xs text-white/50 space-y-1">
                  <p><strong>Confidence Level:</strong> MEDIUM</p>
                  <p><strong>Data Points Used:</strong> {lossDistribution.dataPoints} similar shipments</p>
                  <p><strong>Estimation Method:</strong> Log-normal fit with expert adjustment</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div ref={containerRef} className="w-full">
        {containerSize.width > 0 ? (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="bucket"
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                yAxisId="left"
                label={{ value: 'Frequency (%)', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.6)' }}
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                label={{ value: 'Cumulative (%)', angle: 90, position: 'insideRight', fill: 'rgba(255,255,255,0.6)' }}
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                domain={[0, 1]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* Histogram bars */}
              <Bar 
                yAxisId="left"
                dataKey="frequency" 
                fill="rgba(59, 130, 246, 0.6)" 
                name="Frequency"
                radius={[4, 4, 0, 0]}
              />
              
              {/* CDF line */}
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cumulative"
                stroke="rgba(236, 72, 153, 0.8)"
                strokeWidth={2}
                dot={false}
                name="Cumulative"
              />
              
              {/* Percentile markers */}
              <ReferenceLine 
                yAxisId="left"
                x={chartData[Math.floor(chartData.length * 0.5)]?.bucket}
                stroke="#22c55e"
                strokeDasharray="3 3"
                label={{ value: 'P50', position: 'top', fill: '#22c55e', fontSize: 11 }}
              />
              <ReferenceLine 
                yAxisId="left"
                x={chartData[Math.floor(chartData.length * 0.95)]?.bucket}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{ value: 'P95', position: 'top', fill: '#f59e0b', fontSize: 11 }}
              />
              <ReferenceLine 
                yAxisId="left"
                x={chartData[Math.floor(chartData.length * 0.99)]?.bucket}
                stroke="#ef4444"
                strokeDasharray="3 3"
                label={{ value: 'P99', position: 'top', fill: '#ef4444', fontSize: 11 }}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ChartSkeleton height={chartHeight} />
        )}
      </div>

      {/* Percentile Summary */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
          <div className="text-xs text-emerald-400 mb-1">P50 (Median)</div>
          <div className="text-lg font-bold text-white">{formatCurrency(expectedLoss)}</div>
          <div className="text-xs text-white/50 mt-1">Most likely outcome</div>
        </div>
        <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/20">
          <div className="text-xs text-amber-400 mb-1">P95 (Tail Risk)</div>
          <div className="text-lg font-bold text-white">{formatCurrency(p95)}</div>
          <div className="text-xs text-white/50 mt-1">95% of outcomes below</div>
        </div>
        <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/20">
          <div className="text-xs text-red-400 mb-1">P99 (Extreme)</div>
          <div className="text-lg font-bold text-white">{formatCurrency(p99)}</div>
          <div className="text-xs text-white/50 mt-1">99% of outcomes below</div>
        </div>
      </div>
    </GlassCard>
  );
};
