import React from 'react';
import type { LayerData } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip } from 'recharts';
import { Target, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

interface RiskRadarProps {
  layers: LayerData[];
}

// Custom tooltip for radar (Sprint 3: Enhanced with contribution % and FAHP weight)
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const score = data.value;
    const riskLevel = score >= 70 ? 'High' : score >= 40 ? 'Medium' : 'Low';
    const riskColor = score >= 70 ? 'text-red-400' : score >= 40 ? 'text-amber-400' : 'text-emerald-400';
    
    return (
      <div className="bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[220px]">
        <div className="font-medium text-white mb-2 pb-2 border-b border-white/10">
          {data.name}
        </div>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-white/60 text-sm">Score</span>
            <span className={`font-bold ${riskColor}`}>{score}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-white/60 text-sm">Risk Level</span>
            <span className={`text-sm font-medium ${riskColor}`}>{riskLevel}</span>
          </div>
          {/* Sprint 3: Contribution % */}
          {data.contribution !== undefined && (
            <div className="flex justify-between items-center">
              <span className="text-white/60 text-sm">Contribution</span>
              <span className="text-cyan-400 font-semibold">{data.contribution.toFixed(1)}%</span>
            </div>
          )}
          {/* Sprint 3: FAHP Weight */}
          {data.fahpWeight !== undefined && (
            <div className="flex justify-between items-center">
              <span className="text-white/60 text-sm">FAHP Weight</span>
              <span className="text-purple-400 font-semibold">{(data.fahpWeight * 100).toFixed(1)}%</span>
            </div>
          )}
          {data.category && (
            <div className="flex justify-between items-center">
              <span className="text-white/60 text-sm">Category</span>
              <span className="text-white/80 text-sm">{data.category}</span>
            </div>
          )}
        </div>
        {/* Interpretation */}
        {(data.contribution !== undefined || data.fahpWeight !== undefined) && (
          <div className="mt-3 pt-2 border-t border-white/10 text-xs text-white/70">
            {data.contribution !== undefined && (
              <p>This layer contributes {data.contribution.toFixed(1)}% to your overall risk score.</p>
            )}
            {data.fahpWeight !== undefined && (
              <p className="mt-1">FAHP weight: {(data.fahpWeight * 100).toFixed(1)}% determines this layer's importance.</p>
            )}
          </div>
        )}
        {/* Mini progress bar */}
        <div className="mt-3 pt-2 border-t border-white/10">
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                score >= 70 ? 'bg-gradient-to-r from-red-500 to-red-400' : 
                score >= 40 ? 'bg-gradient-to-r from-amber-500 to-amber-400' : 
                'bg-gradient-to-r from-emerald-500 to-emerald-400'
              }`}
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
      </div>
    );
  }
  return null;
};

// Risk level badge component
const RiskBadge = ({ score, label }: { score: number; label: string }) => {
  const Icon = score >= 70 ? AlertCircle : score >= 40 ? TrendingUp : CheckCircle;
  const colors = score >= 70 
    ? 'bg-red-500/20 text-red-400 border-red-500/30' 
    : score >= 40 
    ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
  
  return (
    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${colors} text-xs font-medium`}>
      <Icon className="w-3 h-3" />
      <span>{label}</span>
    </div>
  );
};

export const RiskRadar: React.FC<RiskRadarProps> = ({ layers }) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Defensive guard: handle empty or invalid data
  if (!layers || layers.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Target className="w-12 h-12 mx-auto mb-4 opacity-30" />
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
      category: (layer as any).category || 'Unknown',
      // Sprint 3: Add contribution and FAHP weight for enhanced tooltip
      contribution: layer.contribution ?? 0,
      fahpWeight: (layer as any).fahpWeight ?? (layer.weight ? layer.weight / 100 : undefined),
    }));

  // Calculate statistics
  const avgScore = Math.round(data.reduce((sum, d) => sum + d.value, 0) / data.length);
  const maxScore = Math.max(...data.map(d => d.value));
  const minScore = Math.min(...data.map(d => d.value));
  const highRiskCount = data.filter(d => d.value >= 70).length;

  return (
    <GlassCard className="overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30">
            <Target className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Risk Profile Radar</h3>
            <p className="text-xs text-white/50">{data.length} risk dimensions analyzed</p>
          </div>
        </div>
        <RiskBadge 
          score={avgScore} 
          label={avgScore >= 70 ? 'High Risk' : avgScore >= 40 ? 'Moderate' : 'Low Risk'} 
        />
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="text-center p-2 rounded-lg bg-white/5 border border-white/10">
          <div className="text-lg font-bold text-white">{avgScore}</div>
          <div className="text-[10px] text-white/40 uppercase">Average</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-white/5 border border-white/10">
          <div className="text-lg font-bold text-red-400">{maxScore}</div>
          <div className="text-[10px] text-white/40 uppercase">Highest</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-white/5 border border-white/10">
          <div className="text-lg font-bold text-emerald-400">{minScore}</div>
          <div className="text-[10px] text-white/40 uppercase">Lowest</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-white/5 border border-white/10">
          <div className="text-lg font-bold text-amber-400">{highRiskCount}</div>
          <div className="text-[10px] text-white/40 uppercase">High Risk</div>
        </div>
      </div>

      {/* Chart */}
      <div 
        ref={containerRef}
        className="relative"
        style={{ height: '350px', minHeight: '350px', minWidth: '300px', width: '100%' }}
      >
        {containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <RadarChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={data}
            margin={{ top: 20, right: 30, bottom: 20, left: 30 }}
          >
            <defs>
              <linearGradient id="radarGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#06B6D4" stopOpacity={0.2} />
              </linearGradient>
              <filter id="radarGlow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            
            <PolarGrid 
              stroke="rgba(255,255,255,0.1)" 
              gridType="polygon"
            />
            
            <PolarAngleAxis 
              dataKey="name" 
              tick={{ 
                fill: 'rgba(255,255,255,0.7)', 
                fontSize: 11,
                fontWeight: 500
              }}
              tickLine={false}
            />
            
            <PolarRadiusAxis 
              angle={90} 
              domain={[0, 100]} 
              tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 9 }}
              tickCount={5}
              axisLine={false}
            />
            
            <Tooltip content={<CustomTooltip />} />
            
            {/* Background reference areas */}
            <Radar
              name="High Risk Zone"
              dataKey="fullMark"
              stroke="none"
              fill="rgba(239, 68, 68, 0.05)"
              fillOpacity={1}
            />
            
            {/* Main radar */}
            <Radar
              name="Risk Score"
              dataKey="value"
              stroke="#3B82F6"
              fill="url(#radarGradient)"
              fillOpacity={0.6}
              strokeWidth={2}
              filter="url(#radarGlow)"
              animationDuration={1500}
              animationEasing="ease-out"
              dot={{
                r: 4,
                fill: '#3B82F6',
                stroke: '#fff',
                strokeWidth: 2,
              }}
              activeDot={{
                r: 6,
                fill: '#3B82F6',
                stroke: '#fff',
                strokeWidth: 2,
              }}
            />
          </RadarChart>
        ) : (
          <ChartSkeleton height={350} />
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-2 pt-3 border-t border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span className="text-xs text-white/50">Low (&lt;40)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500" />
          <span className="text-xs text-white/50">Medium (40-69)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-xs text-white/50">High (≥70)</span>
        </div>
      </div>
    </GlassCard>
  );
};




