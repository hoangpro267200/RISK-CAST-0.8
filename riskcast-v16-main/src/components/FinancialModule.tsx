import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ReferenceLine
} from 'recharts';
import { DollarSign, TrendingDown, AlertTriangle, Shield } from 'lucide-react';
import type { FinancialMetrics } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';

interface FinancialModuleProps {
  financial: FinancialMetrics;
}

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl">
        <div className="flex items-center gap-2 mb-2">
          <DollarSign className="w-4 h-4 text-emerald-400" />
          <span className="text-white font-medium">Loss: ${Number(label).toLocaleString()}</span>
        </div>
        <div className="text-sm">
          <span className="text-white/60">Probability Density: </span>
          <span className="text-cyan-400 font-semibold">{(payload[0].value * 100).toFixed(2)}%</span>
        </div>
      </div>
    );
  }
  return null;
};

// Metric card component
const MetricCard = ({ 
  icon: Icon, 
  label, 
  value, 
  color, 
  description 
}: { 
  icon: React.ElementType; 
  label: string; 
  value: string; 
  color: string; 
  description: string;
}) => (
  <div className={`relative overflow-hidden rounded-xl p-4 border ${color} bg-gradient-to-br from-white/5 to-transparent`}>
    <div className="absolute top-0 right-0 w-20 h-20 opacity-10">
      <Icon className="w-full h-full" />
    </div>
    <div className="relative z-10">
      <div className="flex items-center gap-2 mb-1">
        <Icon className={`w-4 h-4 ${color.includes('emerald') ? 'text-emerald-400' : color.includes('amber') ? 'text-amber-400' : 'text-red-400'}`} />
        <span className="text-xs text-white/50 uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${color.includes('emerald') ? 'text-emerald-400' : color.includes('amber') ? 'text-amber-400' : 'text-red-400'}`}>
        {value}
      </div>
      <div className="text-xs text-white/40 mt-1">{description}</div>
    </div>
  </div>
);

export const FinancialModule: React.FC<FinancialModuleProps> = ({ financial }) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  if (!financial.lossCurve || financial.lossCurve.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <DollarSign className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm">No loss distribution data available</p>
        </div>
      </GlassCard>
    );
  }

  // Find max probability for domain
  const maxProbability = Math.max(...financial.lossCurve.map(d => d.probability || 0));
  
  // Calculate risk severity indicator
  const riskSeverity = financial.expectedLoss > 10000 ? 'high' : financial.expectedLoss > 5000 ? 'medium' : 'low';

  return (
    <GlassCard className="overflow-hidden">
      {/* Header with gradient accent */}
      <div className="relative mb-6">
        <div className="absolute inset-0 bg-gradient-to-r from-red-500/10 via-amber-500/10 to-emerald-500/10 blur-xl" />
        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-red-500/20 to-amber-500/20 border border-red-500/30">
                <TrendingDown className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Financial Loss Distribution</h3>
                <p className="text-xs text-white/50">Probability density function of potential losses</p>
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              riskSeverity === 'high' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
              riskSeverity === 'medium' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
              'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
            }`}>
              {riskSeverity === 'high' ? '⚠️ High Exposure' : riskSeverity === 'medium' ? '⚡ Moderate' : '✓ Low Risk'}
            </div>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard 
          icon={DollarSign}
          label="Expected Loss"
          value={`$${(financial.expectedLoss / 1000).toFixed(1)}K`}
          color="border-emerald-500/30"
          description="Most likely outcome"
        />
        <MetricCard 
          icon={AlertTriangle}
          label="VaR 95%"
          value={`$${(financial.var95 / 1000).toFixed(1)}K`}
          color="border-amber-500/30"
          description="Severe but plausible"
        />
        <MetricCard 
          icon={Shield}
          label="CVaR 95%"
          value={`$${(financial.cvar95 / 1000).toFixed(1)}K`}
          color="border-red-500/30"
          description="Tail risk average"
        />
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
            data={financial.lossCurve}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <defs>
              <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#EF4444" stopOpacity={0.6} />
                <stop offset="50%" stopColor="#F59E0B" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#10B981" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="strokeGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#10B981" />
                <stop offset="50%" stopColor="#F59E0B" />
                <stop offset="100%" stopColor="#EF4444" />
              </linearGradient>
              <filter id="glow">
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
              dataKey="loss" 
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickFormatter={(value) => `$${(value/1000).toFixed(0)}K`}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            />
            
            <YAxis 
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              domain={[0, maxProbability * 1.1]}
            />
            
            <Tooltip content={<CustomTooltip />} />
            
            {/* Reference lines for key values */}
            <ReferenceLine 
              x={financial.expectedLoss} 
              stroke="#10B981" 
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ 
                value: 'E[L]', 
                fill: '#10B981', 
                fontSize: 10,
                position: 'top'
              }}
            />
            <ReferenceLine 
              x={financial.var95} 
              stroke="#F59E0B" 
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ 
                value: 'VaR', 
                fill: '#F59E0B', 
                fontSize: 10,
                position: 'top'
              }}
            />
            <ReferenceLine 
              x={financial.cvar95} 
              stroke="#EF4444" 
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ 
                value: 'CVaR', 
                fill: '#EF4444', 
                fontSize: 10,
                position: 'top'
              }}
            />
            
            {/* Main area chart */}
            <Area 
              type="monotone" 
              dataKey="probability" 
              stroke="url(#strokeGradient)"
              strokeWidth={3}
              fill="url(#lossGradient)"
              filter="url(#glow)"
              animationDuration={1500}
              animationEasing="ease-out"
            />
          </AreaChart>
        ) : (
          <ChartSkeleton height={350} />
        )}
      </div>

      {/* Footer legend */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-emerald-400" />
          <span className="text-xs text-white/50">Expected Loss</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-amber-400" />
          <span className="text-xs text-white/50">Value at Risk (95%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-red-400" />
          <span className="text-xs text-white/50">Conditional VaR (95%)</span>
        </div>
      </div>
    </GlassCard>
  );
};




