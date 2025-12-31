import React from 'react';
import type { LayerData } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Cell, LabelList } from 'recharts';

interface WaterfallDatum {
  name: string;
  value: number;
  cumulative: number;
  contribution: number;
  score: number;
  layerName: string;
}

interface RiskContributionWaterfallProps {
  layers: LayerData[];
  overallScore: number;
  onBarClick?: (layerName: string) => void;
}

export function RiskContributionWaterfall({ layers, overallScore, onBarClick }: RiskContributionWaterfallProps) {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  const sortedLayers = React.useMemo(() => {
    if (!layers || layers.length === 0) return [];
    return layers.slice().sort((a, b) => (b.contribution ?? 0) - (a.contribution ?? 0));
  }, [layers]);

  // Build waterfall data
  const waterfallData: WaterfallDatum[] = React.useMemo(() => {
    if (sortedLayers.length === 0 || overallScore === 0) return [];
    return sortedLayers.reduce<WaterfallDatum[]>((acc, layer, idx) => {
      const prevValue = idx === 0 ? 0 : acc[idx - 1]?.cumulative ?? 0;
      const contribution = layer.contribution ?? 0;
      const current = (overallScore * contribution) / 100;

      acc.push({
        name: (layer.name || '').replace(' Risk', ''),
        value: current,
        cumulative: prevValue + current,
        contribution: contribution,
        score: layer.score ?? 0,
        layerName: layer.name || '',
      });
      return acc;
    }, []);
  }, [sortedLayers, overallScore]);

  const getBarColor = (score: number) => {
    if (score >= 70) return '#EF4444';
    if (score >= 40) return '#F59E0B';
    return '#10B981';
  };

  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-medium text-white">Layer Contribution Waterfall</h2>
          <p className="text-sm text-white/40 mt-1">How each layer contributes to the overall score</p>
        </div>
      </div>

      <div 
        ref={containerRef}
        style={{ height: '400px', minHeight: '400px', minWidth: '300px', width: '100%', position: 'relative' }}
      >
        {waterfallData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-white/40">
            <div className="text-center">
              <p className="text-sm">No layer data available</p>
              <p className="text-xs text-white/30 mt-1">Layer contribution data is required for this chart</p>
            </div>
          </div>
        ) : containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <BarChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={waterfallData} 
            margin={{ top: 20, right: 20, left: 20, bottom: 60 }}
          >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={60}
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                tickLine={{ stroke: 'rgba(255,255,255,0.2)' }}
              />
              <YAxis
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                tickLine={{ stroke: 'rgba(255,255,255,0.2)' }}
                axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                <LabelList
                  dataKey="contribution"
                  position="top"
                  formatter={(v: unknown) => `${Math.round(Number(v))}%`}
                  fill="rgba(255,255,255,0.7)"
                  fontSize={11}
                />
                {waterfallData.map((entry) => (
                  <Cell
                    key={entry.layerName}
                    fill={getBarColor(entry.score)}
                    style={{ cursor: onBarClick ? 'pointer' : 'default' }}
                    onClick={() => onBarClick?.(entry.layerName)}
                  />
                ))}
              </Bar>
            </BarChart>
        ) : (
          <ChartSkeleton height={400} />
        )}
      </div>
    </GlassCard>
  );
}




