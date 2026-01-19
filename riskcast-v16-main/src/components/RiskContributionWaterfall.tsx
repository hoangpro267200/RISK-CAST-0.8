import React, { useState } from 'react';
import type { LayerData } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Cell, Tooltip } from 'recharts';
import { Layers, BarChart3 } from 'lucide-react';

interface WaterfallDatum {
  name: string;
  value: number;
  cumulative: number;
  contribution: number;
  score: number;
  layerName: string;
  category: string;
}

interface RiskContributionWaterfallProps {
  layers: LayerData[];
  overallScore: number;
  onBarClick?: (layerName: string) => void;
}

// Category colors
const CATEGORY_COLORS: Record<string, { primary: string; gradient: string }> = {
  'TRANSPORT': { primary: '#3B82F6', gradient: 'from-blue-500 to-blue-600' },
  'CARGO': { primary: '#8B5CF6', gradient: 'from-violet-500 to-purple-600' },
  'COMMERCIAL': { primary: '#10B981', gradient: 'from-emerald-500 to-green-600' },
  'COMPLIANCE': { primary: '#F59E0B', gradient: 'from-amber-500 to-orange-600' },
  'EXTERNAL': { primary: '#EC4899', gradient: 'from-pink-500 to-rose-600' },
};

// Custom tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const categoryColor = CATEGORY_COLORS[data.category]?.primary || '#6B7280';
    
    return (
      <div className="bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[200px]">
        <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/10">
          <div 
            className="w-3 h-3 rounded-full" 
            style={{ backgroundColor: categoryColor }}
          />
          <span className="font-medium text-white">{data.name}</span>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-white/60 text-sm">Contribution</span>
            <span className="font-bold text-cyan-400">{data.contribution}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/60 text-sm">Layer Score</span>
            <span className={`font-semibold ${
              data.score >= 70 ? 'text-red-400' : data.score >= 40 ? 'text-amber-400' : 'text-emerald-400'
            }`}>{data.score}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/60 text-sm">Category</span>
            <span className="text-white/80 text-sm">{data.category}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/60 text-sm">Cumulative</span>
            <span className="text-white/80 text-sm">{data.cumulative.toFixed(1)}%</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export function RiskContributionWaterfall({ layers, overallScore, onBarClick }: RiskContributionWaterfallProps) {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();
  const [hoveredBar, setHoveredBar] = useState<string | null>(null);

  const sortedLayers = React.useMemo(() => {
    if (!layers || layers.length === 0) return [];
    return layers.slice().sort((a, b) => (b.contribution ?? 0) - (a.contribution ?? 0));
  }, [layers]);

  // Build waterfall data with categories
  const waterfallData: WaterfallDatum[] = React.useMemo(() => {
    if (sortedLayers.length === 0) return [];
    return sortedLayers.reduce<WaterfallDatum[]>((acc, layer, idx) => {
      const prevValue = idx === 0 ? 0 : acc[idx - 1]?.cumulative ?? 0;
      const contribution = layer.contribution ?? 0;

      acc.push({
        name: (layer.name || '').replace(' Risk', ''),
        value: contribution,
        cumulative: prevValue + contribution,
        contribution: contribution,
        score: layer.score ?? 0,
        layerName: layer.name || '',
        category: layer.category || 'UNKNOWN',
      });
      return acc;
    }, []);
  }, [sortedLayers]);

  // Group by category for legend
  const categoryStats = React.useMemo(() => {
    const stats: Record<string, { count: number; total: number }> = {};
    waterfallData.forEach(d => {
      if (!stats[d.category]) stats[d.category] = { count: 0, total: 0 };
      stats[d.category].count++;
      stats[d.category].total += d.contribution;
    });
    return stats;
  }, [waterfallData]);

  const getBarColor = (category: string, score: number) => {
    // Use category color with score-based intensity
    const baseColor = CATEGORY_COLORS[category]?.primary || '#6B7280';
    return baseColor;
  };

  return (
    <GlassCard className="overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Risk Layer Distribution</h2>
            <p className="text-xs text-white/50">{waterfallData.length} layers analyzed</p>
          </div>
        </div>
      </div>

      {/* Category Legend */}
      <div className="flex flex-wrap gap-3 mb-4">
        {Object.entries(categoryStats).map(([cat, stats]) => (
          <div 
            key={cat}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10"
          >
            <div 
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: CATEGORY_COLORS[cat]?.primary || '#6B7280' }}
            />
            <span className="text-xs text-white/70">{cat}</span>
            <span className="text-xs font-semibold text-white/90">{stats.total.toFixed(0)}%</span>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div 
        ref={containerRef}
        className="relative"
        style={{ height: '400px', minHeight: '400px', minWidth: '300px', width: '100%' }}
      >
        {waterfallData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-white/40">
            <div className="text-center">
              <Layers className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p className="text-sm">No layer data available</p>
            </div>
          </div>
        ) : containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <BarChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={waterfallData} 
            margin={{ top: 30, right: 20, left: 20, bottom: 100 }}
          >
            <defs>
              {Object.entries(CATEGORY_COLORS).map(([cat, colors]) => (
                <linearGradient key={cat} id={`gradient-${cat}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colors.primary} stopOpacity={1} />
                  <stop offset="100%" stopColor={colors.primary} stopOpacity={0.6} />
                </linearGradient>
              ))}
            </defs>
            
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="rgba(255,255,255,0.08)" 
              vertical={false}
            />
            
            <XAxis
              dataKey="name"
              angle={-55}
              textAnchor="end"
              height={100}
              tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.15)' }}
              interval={0}
            />
            
            <YAxis
              tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.15)' }}
              tickFormatter={(v) => `${v}%`}
              domain={[0, 15]}
              ticks={[0, 5, 10, 15]}
            />
            
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            
            <Bar 
              dataKey="value" 
              radius={[4, 4, 0, 0]}
              animationDuration={1200}
              animationEasing="ease-out"
              maxBarSize={45}
            >
              {waterfallData.map((entry) => (
                <Cell
                  key={entry.layerName}
                  fill={`url(#gradient-${entry.category})`}
                  style={{ cursor: onBarClick ? 'pointer' : 'default' }}
                  onClick={() => onBarClick?.(entry.layerName)}
                  onMouseEnter={() => setHoveredBar(entry.layerName)}
                  onMouseLeave={() => setHoveredBar(null)}
                />
              ))}
            </Bar>
          </BarChart>
        ) : (
          <ChartSkeleton height={400} />
        )}
      </div>

      {/* Footer - Legend only */}
      <div className="flex items-center justify-center gap-2 mt-2 pt-3 border-t border-white/10">
        <span className="text-xs text-white/40">Hover for details</span>
        <span className="text-white/20">•</span>
        <span className="text-xs text-white/40">Sorted by contribution</span>
      </div>
    </GlassCard>
  );
}




