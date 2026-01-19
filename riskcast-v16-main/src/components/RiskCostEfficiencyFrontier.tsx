import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';
import { Award, TrendingUp, Zap } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import type { Scenario } from '../types';

interface RiskCostEfficiencyFrontierProps {
  scenarios: Scenario[];
  baselineRisk: number;
  highlightedScenario: string | null;
}

export function RiskCostEfficiencyFrontier({ 
  scenarios, 
  baselineRisk, 
  highlightedScenario 
}: RiskCostEfficiencyFrontierProps) {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  // Defensive guard: handle empty or invalid data
  if (!scenarios || scenarios.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <p className="text-sm">No scenario data available</p>
          <p className="text-xs text-white/30 mt-1">Scenario data is required for this chart</p>
        </div>
      </GlassCard>
    );
  }

  // Identify Pareto optimal points
  const isParetoOptimal = (point: Scenario, allPoints: Scenario[]) => {
    if (!allPoints || allPoints.length === 0) return false;
    return !allPoints.some(other => 
      other !== point && 
      (other.riskReduction ?? 0) >= (point.riskReduction ?? 0) && 
      (other.costImpact ?? 0) <= (point.costImpact ?? 0) &&
      ((other.riskReduction ?? 0) > (point.riskReduction ?? 0) || (other.costImpact ?? 0) < (point.costImpact ?? 0))
    );
  };

  type FrontierPoint = {
    name: string;
    x: number;
    y: number;
    z: number;
    description?: string;
    isPareto: boolean;
  };

  const chartData: FrontierPoint[] = scenarios
    .filter(s => s != null)
    .map(scenario => ({
      name: scenario.title || 'Unknown',
      x: scenario.costImpact ?? 0, // cost
      y: scenario.riskReduction ?? 0, // risk reduction
      z: (scenario.feasibility ?? 0) * 100, // feasibility as size
      description: scenario.description,
      isPareto: isParetoOptimal(scenario, scenarios)
    }));

  // Defensive calculations with fallbacks
  const riskReductions = scenarios.map(s => s.riskReduction ?? 0).filter(v => !isNaN(v));
  const costImpacts = scenarios.map(s => s.costImpact ?? 0).filter(v => !isNaN(v));
  
  const maxRiskReduction = riskReductions.length > 0 ? Math.max(...riskReductions) : 0;
  const maxCost = costImpacts.length > 0 ? Math.max(...costImpacts) : 1; // Use 1 to avoid division by zero
  const efficiencyThreshold = maxCost > 0 ? (maxRiskReduction / maxCost) * 0.7 : 0;

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-black/90 border border-white/20 rounded-lg p-4 shadow-xl">
          <div className="text-white font-medium mb-2">{data.name}</div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-white/60">Cost Impact:</span>
              <span className="text-white">{data.x.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-white/60">Risk Reduction:</span>
              <span className="text-white">{data.y.toFixed(0)} pts</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-white/60">Feasibility:</span>
              <span className="text-white">{data.z.toFixed(0)}%</span>
            </div>
            {data.isPareto && (
              <div className="mt-2 px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-medium">
                Pareto Optimal
              </div>
            )}
          </div>
          {data.description && (
            <div className="mt-3 pt-3 border-t border-white/10 text-xs text-white/60">
              {data.description}
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  const getPointColor = (point: FrontierPoint) => {
    if (point.name === highlightedScenario) return '#8B5CF6'; // purple for highlighted
    if (point.isPareto) return '#10B981'; // green for pareto optimal
    if (point.y / Math.max(point.x, 0.1) > efficiencyThreshold) return '#3B82F6'; // blue for efficient
    return '#6B7280'; // gray for others
  };

  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-medium text-white">Cost-Efficiency Frontier</h2>
          <p className="text-sm text-white/40 mt-1">
            Risk reduction vs cost impact for mitigation strategies
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-white/60">Pareto Optimal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-white/60">Efficient</span>
          </div>
        </div>
      </div>

      {/* Efficiency insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Award className="w-4 h-4 text-green-400" />
            <span className="text-sm font-medium text-white">Best Value</span>
          </div>
          <div className="text-xs text-white/60">
            {chartData.filter(d => d.isPareto).length} strategies on optimal frontier
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-white">Max Impact</span>
          </div>
          <div className="text-xs text-white/60">
            {maxRiskReduction > 0 
              ? `Up to ${maxRiskReduction.toFixed(0)} points risk reduction available`
              : baselineRisk < 30 
                ? 'Risk already optimal - no further reduction needed'
                : 'Maintain current plan - stable risk profile'}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-medium text-white">Efficiency</span>
          </div>
          <div className="text-xs text-white/60">
            Baseline risk: {baselineRisk} points
          </div>
        </div>
      </div>

      <div 
        ref={containerRef}
        style={{ height: '400px', minHeight: '400px', minWidth: '300px', width: '100%', position: 'relative' }}
      >
        {containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <ScatterChart 
            width={containerSize.width} 
            height={containerSize.height}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            
            <XAxis 
              type="number" 
              dataKey="x" 
              name="Cost Impact"
              unit="%"
              tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
              tickLine={{ stroke: 'rgba(255,255,255,0.2)' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
              label={{ 
                value: 'Cost Impact (%)', 
                position: 'insideBottom', 
                offset: -10,
                style: { fill: 'rgba(255,255,255,0.6)' }
              }}
            />
            
            <YAxis 
              type="number" 
              dataKey="y" 
              name="Risk Reduction"
              unit="pts"
              tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
              tickLine={{ stroke: 'rgba(255,255,255,0.2)' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
              label={{ 
                value: 'Risk Reduction (points)', 
                angle: -90, 
                position: 'insideLeft',
                style: { fill: 'rgba(255,255,255,0.6)' }
              }}
            />

            <Tooltip content={<CustomTooltip />} />

            <Scatter 
              data={chartData} 
              fill="#3B82F6"
              shape="circle"
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`}
                  fill={getPointColor(entry)}
                  stroke={entry.name === highlightedScenario ? '#FFFFFF' : 'none'}
                  strokeWidth={entry.name === highlightedScenario ? 2 : 0}
                />
              ))}
            </Scatter>
          </ScatterChart>
        ) : (
          <ChartSkeleton height={400} />
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 text-xs text-white/40 text-center">
        Point size represents feasibility • Colors indicate efficiency classification
      </div>
    </GlassCard>
  );
}




