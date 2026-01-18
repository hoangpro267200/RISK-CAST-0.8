/**
 * Factor Contribution Waterfall Component
 * 
 * Shows how each risk layer adds or subtracts from the base score to reach the final score.
 */

import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, ReferenceLine
} from 'recharts';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import type { LayerData } from '../types';
import { TrendingUp, TrendingDown, Info } from 'lucide-react';

interface FactorContributionWaterfallProps {
  baseScore: number;
  layers: LayerData[];
  finalScore: number;
}

// Custom tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const contribution = data.contribution;
    const isPositive = contribution > 0;
    
    return (
      <div className="bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[200px]">
        <div className="font-medium text-white mb-2 pb-2 border-b border-white/10">
          {label}
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-white/60">Contribution:</span>
            <span className={`font-bold ${isPositive ? 'text-red-400' : 'text-emerald-400'}`}>
              {isPositive ? '+' : ''}{contribution.toFixed(1)} pts
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-white/60">Running Total:</span>
            <span className="text-white font-semibold">{data.runningTotal.toFixed(1)}</span>
          </div>
          {data.interpretation && (
            <div className="mt-3 pt-2 border-t border-white/10 text-xs text-white/70">
              {data.interpretation}
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export const FactorContributionWaterfall: React.FC<FactorContributionWaterfallProps> = ({
  baseScore,
  layers,
  finalScore,
}) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Defensive guard
  if (!layers || layers.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Factor contribution data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            Layer data is required for this chart. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Build waterfall data
  // Sort layers by contribution (absolute value, descending)
  const sortedLayers = [...layers]
    .filter(l => l.contribution !== 0)
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));

  // Build waterfall points
  const waterfallData: Array<{
    name: string;
    contribution: number;
    runningTotal: number;
    interpretation: string;
  }> = [];

  // Starting point
  waterfallData.push({
    name: 'Base Risk',
    contribution: 0,
    runningTotal: baseScore,
    interpretation: 'Starting risk score before layer contributions',
  });

  // Layer contributions
  let runningTotal = baseScore;
  sortedLayers.forEach(layer => {
    runningTotal += layer.contribution;
    waterfallData.push({
      name: layer.name.replace(' Risk', ''),
      contribution: layer.contribution,
      runningTotal: runningTotal,
      interpretation: `${layer.contribution > 0 ? 'Increases' : 'Decreases'} risk by ${Math.abs(layer.contribution).toFixed(1)} points`,
    });
  });

  // Final point
  waterfallData.push({
    name: 'Final Score',
    contribution: 0,
    runningTotal: finalScore,
    interpretation: `Final risk score: ${finalScore.toFixed(1)}/100`,
  });

  const chartWidth = containerSize.width > 0 ? containerSize.width : 800;
  const chartHeight = 400;

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-purple-400" />
          <span>Factor Contribution Waterfall</span>
        </h3>
        <p className="text-sm text-white/60">
          How each risk layer contributes to the final score
        </p>
      </div>

      <div ref={containerRef} className="w-full">
        {containerSize.width > 0 ? (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart
              data={waterfallData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="name"
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                label={{ value: 'Risk Score', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.6)' }}
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                domain={[0, 100]}
              />
              <Tooltip content={<CustomTooltip />} />
              
              {/* Base and Final bars (gray) */}
              <Bar dataKey="runningTotal" radius={[4, 4, 0, 0]}>
                {waterfallData.map((entry, index) => {
                  if (entry.name === 'Base Risk' || entry.name === 'Final Score') {
                    return <Cell key={`cell-${index}`} fill="rgba(107, 114, 128, 0.6)" />;
                  }
                  // Contribution bars (red for positive, green for negative)
                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.contribution > 0 
                        ? 'rgba(239, 68, 68, 0.6)' // red-500
                        : 'rgba(34, 197, 94, 0.6)' // emerald-500
                      }
                    />
                  );
                })}
              </Bar>
              
              {/* Reference line at final score */}
              <ReferenceLine 
                y={finalScore} 
                stroke="#3b82f6" 
                strokeDasharray="3 3"
                label={{ value: `Final: ${finalScore.toFixed(0)}`, position: 'right', fill: '#3b82f6', fontSize: 11 }}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ChartSkeleton height={chartHeight} />
        )}
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gray-500/60" />
          <span className="text-white/60">Base/Final</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-500/60" />
          <span className="text-white/60">Increases Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-emerald-500/60" />
          <span className="text-white/60">Decreases Risk</span>
        </div>
      </div>

      {/* Methodology Explainer */}
      <details className="mt-6 pt-4 border-t border-white/10">
        <summary className="cursor-pointer text-sm text-white/70 hover:text-white/90 flex items-center gap-2">
          <Info className="w-4 h-4" />
          <span>How Factor Contribution Works</span>
        </summary>
        <div className="mt-3 p-4 bg-white/5 rounded-lg text-sm text-white/70 space-y-2">
          <p>
            The waterfall chart shows how each risk layer adds or subtracts from the base risk score 
            to reach the final score. Positive contributions (red) increase risk, while negative 
            contributions (green) decrease risk.
          </p>
          <p>
            Layers are sorted by absolute contribution value to show which factors have the greatest 
            impact on your final risk assessment.
          </p>
        </div>
      </details>
    </GlassCard>
  );
};
