import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts';
import type { ScenarioDataPoint } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import { Activity, Calendar, Ship, Plane, ArrowRight } from 'lucide-react';

interface RiskScenarioFanChartProps {
  data: ScenarioDataPoint[];
  etd: string;
  eta: string;
}

// Custom tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const p10 = payload.find((p: any) => p.dataKey === 'p10')?.value || 0;
    const p50 = payload.find((p: any) => p.dataKey === 'p50')?.value || 0;
    const p90 = payload.find((p: any) => p.dataKey === 'p90')?.value || 0;
    const phase = payload[0]?.payload?.phase || 'Transit';
    
    return (
      <div className="bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[200px]">
        <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/10">
          <Calendar className="w-4 h-4 text-cyan-400" />
          <span className="font-medium text-white">{label}</span>
          <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-white/10 text-white/70">{phase}</span>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-white/60 text-sm">Best Case (P10)</span>
            <span className="font-semibold text-emerald-400">{p10.toFixed(1)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-white/60 text-sm">Expected (P50)</span>
            <span className="font-bold text-cyan-400">{p50.toFixed(1)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-white/60 text-sm">Worst Case (P90)</span>
            <span className="font-semibold text-red-400">{p90.toFixed(1)}</span>
          </div>
        </div>
        {/* Confidence interval visual */}
        <div className="mt-3 pt-2 border-t border-white/10">
          <div className="text-xs text-white/40 mb-1">80% Confidence Interval</div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden relative">
            <div 
              className="absolute h-full bg-gradient-to-r from-emerald-500/50 via-cyan-500/50 to-red-500/50"
              style={{ 
                left: `${p10}%`, 
                width: `${p90 - p10}%` 
              }}
            />
            <div 
              className="absolute w-1 h-full bg-cyan-400"
              style={{ left: `${p50}%` }}
            />
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export const RiskScenarioFanChart: React.FC<RiskScenarioFanChartProps> = ({ data, etd, eta }) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Defensive guard: handle empty or invalid data
  if (!data || data.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Activity className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm">No scenario projection data available</p>
          <p className="text-xs text-white/30 mt-1">Scenario projection data is required for this chart</p>
        </div>
      </GlassCard>
    );
  }

  // Calculate statistics
  const currentP50 = data[0]?.p50 || 0;
  const finalP50 = data[data.length - 1]?.p50 || 0;
  const trend = finalP50 - currentP50;
  const maxP90 = Math.max(...data.map(d => d.p90 || 0));
  const minP10 = Math.min(...data.map(d => d.p10 || 0));

  return (
    <GlassCard className="overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30">
            <Activity className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Risk Scenario Projections</h3>
            <p className="text-xs text-white/50">Monte Carlo simulation with 80% confidence bands</p>
          </div>
        </div>
        
        {/* Trend indicator */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
          trend > 5 ? 'bg-red-500/20 border border-red-500/30' :
          trend < -5 ? 'bg-emerald-500/20 border border-emerald-500/30' :
          'bg-white/10 border border-white/20'
        }`}>
          <span className={`text-xs font-medium ${
            trend > 5 ? 'text-red-400' : trend < -5 ? 'text-emerald-400' : 'text-white/60'
          }`}>
            {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend).toFixed(1)} pts
          </span>
        </div>
      </div>

      {/* Journey timeline */}
      <div className="flex items-center gap-2 mb-4 p-3 rounded-xl bg-white/5 border border-white/10">
        <div className="flex items-center gap-2">
          <Ship className="w-4 h-4 text-cyan-400" />
          <div>
            <div className="text-xs text-white/40">ETD</div>
            <div className="text-sm font-medium text-white">{etd || 'N/A'}</div>
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex-1 h-0.5 bg-gradient-to-r from-cyan-500/50 to-violet-500/50" />
          <ArrowRight className="w-4 h-4 text-white/30 mx-2" />
          <div className="flex-1 h-0.5 bg-gradient-to-r from-violet-500/50 to-emerald-500/50" />
        </div>
        <div className="flex items-center gap-2">
          <Plane className="w-4 h-4 text-emerald-400" />
          <div>
            <div className="text-xs text-white/40">ETA</div>
            <div className="text-sm font-medium text-white">{eta || 'N/A'}</div>
          </div>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <div className="text-lg font-bold text-emerald-400">{minP10.toFixed(0)}</div>
          <div className="text-[10px] text-white/40 uppercase">Best Case</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
          <div className="text-lg font-bold text-cyan-400">{currentP50.toFixed(0)}</div>
          <div className="text-[10px] text-white/40 uppercase">Expected</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-red-500/10 border border-red-500/20">
          <div className="text-lg font-bold text-red-400">{maxP90.toFixed(0)}</div>
          <div className="text-[10px] text-white/40 uppercase">Worst Case</div>
        </div>
      </div>

      {/* Chart */}
      <div 
        ref={containerRef}
        className="relative"
        style={{ height: '350px', minHeight: '350px', minWidth: '300px', width: '100%' }}
      >
        {containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <AreaChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={data}
            margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
          >
            <defs>
              <linearGradient id="fanGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8B5CF6" stopOpacity={0.4} />
                <stop offset="50%" stopColor="#06B6D4" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#10B981" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="medianGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#06B6D4" />
                <stop offset="100%" stopColor="#8B5CF6" />
              </linearGradient>
              <filter id="fanGlow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="rgba(255,255,255,0.05)" 
              vertical={false}
            />
            
            <XAxis 
              dataKey="date" 
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            />
            
            <YAxis 
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              domain={[0, 100]}
            />
            
            <Tooltip content={<CustomTooltip />} />
            
            {/* Risk threshold reference line */}
            <ReferenceLine 
              y={70} 
              stroke="#EF4444" 
              strokeDasharray="5 5" 
              strokeWidth={1}
              label={{ 
                value: 'High Risk', 
                fill: '#EF4444', 
                fontSize: 10,
                position: 'right'
              }}
            />
            
            {/* P90 - Upper bound */}
            <Area
              type="monotone"
              dataKey="p90"
              stroke="rgba(239, 68, 68, 0.5)"
              strokeWidth={1}
              fill="url(#fanGradient)"
              name="90th Percentile"
              animationDuration={1500}
            />
            
            {/* P10 - Lower bound (fills the gap) */}
            <Area
              type="monotone"
              dataKey="p10"
              stroke="rgba(16, 185, 129, 0.5)"
              strokeWidth={1}
              fill="#0a1628"
              name="10th Percentile"
              animationDuration={1500}
            />
            
            {/* P50 - Median line */}
            <Area
              type="monotone"
              dataKey="p50"
              stroke="url(#medianGradient)"
              strokeWidth={3}
              fill="none"
              name="Median"
              filter="url(#fanGlow)"
              animationDuration={1500}
              dot={{ fill: '#06B6D4', strokeWidth: 0, r: 3 }}
              activeDot={{ fill: '#06B6D4', stroke: '#fff', strokeWidth: 2, r: 5 }}
            />
          </AreaChart>
        ) : (
          <ChartSkeleton height={350} />
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-2 pt-3 border-t border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-r from-cyan-500 to-violet-500" />
          <span className="text-xs text-white/50">Expected Path</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-3 rounded bg-gradient-to-b from-violet-500/40 to-transparent" />
          <span className="text-xs text-white/50">80% Confidence</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 border-dashed border-t-2 border-red-400" />
          <span className="text-xs text-white/50">High Risk Threshold</span>
        </div>
      </div>
    </GlassCard>
  );
};




