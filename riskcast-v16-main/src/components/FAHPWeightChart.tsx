/**
 * FAHP Weight Chart Component
 * 
 * Displays Fuzzy Analytic Hierarchy Process (FAHP) weights for each risk layer.
 * Shows how each layer's weight was determined and its contribution to the final score.
 */

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import type { FAHPData } from '../types/algorithmTypes';
import { AlertCircle, CheckCircle2, Info } from 'lucide-react';

interface FAHPWeightChartProps {
  fahpData: FAHPData;
}

// Custom tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[200px]">
        <div className="font-medium text-white mb-2 pb-2 border-b border-white/10">
          {data.layerName}
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-white/60">FAHP Weight:</span>
            <span className="text-white font-semibold">{(data.weight * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-white/60">Contribution:</span>
            <span className="text-cyan-400 font-semibold">{data.contributionPercent.toFixed(1)}%</span>
          </div>
          <div className="mt-3 pt-2 border-t border-white/10 text-xs text-white/70">
            This layer determines {data.contributionPercent.toFixed(1)}% of your overall risk score.
          </div>
        </div>
      </div>
    );
  }
  return null;
};

// Consistency Ratio Badge
const ConsistencyBadge: React.FC<{ cr: number; status: 'acceptable' | 'review_needed' }> = ({ cr, status }) => {
  const isAcceptable = status === 'acceptable';
  const Icon = isAcceptable ? CheckCircle2 : AlertCircle;
  const colorClass = isAcceptable 
    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    : 'bg-amber-500/20 text-amber-400 border-amber-500/30';
  
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${colorClass} text-xs font-medium`}>
      <Icon className="w-3.5 h-3.5" />
      <span>
        {isAcceptable ? 'Consistent' : 'Review Needed'} (CR: {cr.toFixed(3)})
      </span>
    </div>
  );
};

export const FAHPWeightChart: React.FC<FAHPWeightChartProps> = ({ fahpData }) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Defensive guard
  if (!fahpData || !fahpData.weights || fahpData.weights.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Info className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">FAHP weights unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not determine layer weights. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Prepare chart data (sorted by weight descending)
  const chartData = [...fahpData.weights]
    .sort((a, b) => b.weight - a.weight)
    .map(w => ({
      layerName: w.layerName.replace(' Risk', ''),
      weight: w.weight,
      contributionPercent: w.contributionPercent,
      fullMark: 1.0,
    }));

  // Color gradient function
  const getColor = (weight: number) => {
    if (weight >= 0.3) return '#ef4444'; // red-500
    if (weight >= 0.2) return '#f59e0b'; // amber-500
    if (weight >= 0.1) return '#eab308'; // yellow-500
    return '#22c55e'; // emerald-500
  };

  const chartWidth = containerSize.width > 0 ? containerSize.width : 600;
  const chartHeight = Math.max(300, fahpData.weights.length * 40);

  return (
    <GlassCard>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
              <span>FAHP Weight Distribution</span>
            </h3>
            <p className="text-sm text-white/60">
              Relative importance of each risk layer determined by Fuzzy Analytic Hierarchy Process
            </p>
          </div>
          <ConsistencyBadge cr={fahpData.consistencyRatio} status={fahpData.consistencyStatus} />
        </div>
      </div>

      <div ref={containerRef} className="w-full">
        {containerSize.width > 0 ? (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                type="number" 
                domain={[0, 1]}
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <YAxis 
                type="category" 
                dataKey="layerName"
                tick={{ fill: 'rgba(255,255,255,0.8)', fontSize: 12 }}
                width={90}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="weight" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(entry.weight)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ChartSkeleton height={chartHeight} />
        )}
      </div>

      {/* Methodology Explainer (Collapsible) */}
      <details className="mt-6 pt-4 border-t border-white/10">
        <summary className="cursor-pointer text-sm text-white/70 hover:text-white/90 flex items-center gap-2">
          <Info className="w-4 h-4" />
          <span>How FAHP Works</span>
        </summary>
        <div className="mt-3 p-4 bg-white/5 rounded-lg text-sm text-white/70 space-y-2">
          <p>
            <strong className="text-white">Fuzzy Analytic Hierarchy Process (FAHP)</strong> determines the relative 
            importance of each risk factor using pairwise comparisons with fuzzy numbers to handle uncertainty.
          </p>
          <p>
            A <strong className="text-white">Consistency Ratio (CR) &lt; 0.1</strong> indicates reliable weights. 
            Your weights were calculated from pairwise comparisons across multiple criteria.
          </p>
          <p className="text-xs text-white/50 mt-2">
            Higher weights indicate factors that have greater influence on the final risk score.
          </p>
        </div>
      </details>
    </GlassCard>
  );
};
