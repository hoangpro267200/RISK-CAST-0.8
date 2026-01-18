/**
 * Monte Carlo Explainer Component
 * 
 * Explains the Monte Carlo simulation methodology and shows distribution parameters.
 * Displays percentiles (P10, P50, P90, P95, P99) with interpretation.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { MonteCarloData } from '../types/algorithmTypes';
import { Info, BarChart3 } from 'lucide-react';

interface MonteCarloExplainerProps {
  monteCarloData: MonteCarloData;
}

// Percentile Ruler Component
const PercentileRuler: React.FC<{ percentiles: MonteCarloData['percentiles'] }> = ({ percentiles }) => {
  const values = [
    { label: 'P10', value: percentiles.p10, color: 'text-emerald-400' },
    { label: 'P50', value: percentiles.p50, color: 'text-blue-400' },
    { label: 'P90', value: percentiles.p90, color: 'text-amber-400' },
    { label: 'P95', value: percentiles.p95, color: 'text-orange-400' },
    { label: 'P99', value: percentiles.p99, color: 'text-red-400' },
  ];

  const minValue = Math.min(...values.map(v => v.value));
  const maxValue = Math.max(...values.map(v => v.value));
  const range = maxValue - minValue;

  const formatValue = (val: number) => {
    if (val >= 1000) return `$${(val / 1000).toFixed(1)}K`;
    return `$${val.toFixed(0)}`;
  };

  return (
    <div className="mt-4">
      <div className="relative h-12 bg-white/5 rounded-lg p-2">
        {values.map((item, idx) => {
          const position = range > 0 ? ((item.value - minValue) / range) * 100 : 50;
          return (
            <div
              key={item.label}
              className="absolute top-0 bottom-0 flex flex-col items-center"
              style={{ left: `${position}%`, transform: 'translateX(-50%)' }}
            >
              <div className={`text-xs font-bold ${item.color} mb-1`}>{item.label}</div>
              <div className="w-0.5 h-4 bg-current" style={{ color: 'inherit' }} />
              <div className={`text-xs font-medium ${item.color} mt-1`}>
                {formatValue(item.value)}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 text-xs text-white/60">
        <div className="flex items-center gap-4 flex-wrap">
          {values.map(item => (
            <div key={item.label} className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full ${item.color.replace('text-', 'bg-')}`} />
              <span>{item.label} = {formatValue(item.value)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export const MonteCarloExplainer: React.FC<MonteCarloExplainerProps> = ({ monteCarloData }) => {
  // Defensive guard
  if (!monteCarloData || monteCarloData.nSamples === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Info className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Monte Carlo simulation data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not run Monte Carlo simulation. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-purple-400" />
          <span>Monte Carlo Simulation</span>
        </h3>
        <p className="text-sm text-white/60">
          Uncertainty modeling through random sampling
        </p>
      </div>

      {/* Simulation Parameters Card */}
      <div className="mb-6 p-4 bg-white/5 rounded-lg border border-white/10">
        <h4 className="text-sm font-semibold text-white mb-3">Simulation Parameters</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-white/50 mb-1">Samples</div>
            <div className="text-lg font-bold text-white">
              {monteCarloData.nSamples.toLocaleString()}
            </div>
            <div className="text-xs text-white/40">iterations</div>
          </div>
          <div>
            <div className="text-xs text-white/50 mb-1">Distribution</div>
            <div className="text-lg font-bold text-white capitalize">
              {monteCarloData.distributionType}
            </div>
          </div>
          {Object.entries(monteCarloData.parameters).slice(0, 2).map(([key, value]) => (
            <div key={key}>
              <div className="text-xs text-white/50 mb-1">{key}</div>
              <div className="text-lg font-bold text-white">{value.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Percentile Ruler */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-white mb-2">Loss Distribution Percentiles</h4>
        <PercentileRuler percentiles={monteCarloData.percentiles} />
      </div>

      {/* Interpretation */}
      <div className="mb-6 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
        <h4 className="text-sm font-semibold text-blue-400 mb-2">Interpretation</h4>
        <ul className="space-y-2 text-sm text-white/80">
          <li>
            <strong className="text-blue-400">P50 (${(monteCarloData.percentiles.p50 / 1000).toFixed(1)}K):</strong> 
            {' '}Your most likely loss scenario (median)
          </li>
          <li>
            <strong className="text-orange-400">P95 (${(monteCarloData.percentiles.p95 / 1000).toFixed(1)}K):</strong> 
            {' '}95% of outcomes are better than this (tail risk threshold)
          </li>
          <li>
            <strong className="text-red-400">P99 (${(monteCarloData.percentiles.p99 / 1000).toFixed(1)}K):</strong> 
            {' '}Extreme scenario (1% probability)
          </li>
        </ul>
      </div>

      {/* Methodology Explainer */}
      <details className="mt-6 pt-4 border-t border-white/10">
        <summary className="cursor-pointer text-sm text-white/70 hover:text-white/90 flex items-center gap-2">
          <Info className="w-4 h-4" />
          <span>How Monte Carlo Simulation Works</span>
        </summary>
        <div className="mt-3 p-4 bg-white/5 rounded-lg text-sm text-white/70 space-y-2">
          <p>
            We ran <strong className="text-white">{monteCarloData.nSamples.toLocaleString()} simulations</strong> of 
            your shipment to model uncertainty. Each simulation randomizes risk factors based on historical data.
          </p>
          <p>
            <strong className="text-white">Distribution Type:</strong> {monteCarloData.distributionType}
          </p>
          <p className="text-xs text-white/50 mt-2">
            This means: There's a 22% chance your actual loss exceeds ${(monteCarloData.percentiles.p90 / 1000).toFixed(1)}K 
            (90th percentile).
          </p>
        </div>
      </details>
    </GlassCard>
  );
};
