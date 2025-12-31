import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import type { FinancialMetrics } from '../types';
import { GlassCard } from './GlassCard';
import { ChartSkeleton } from './ChartSkeleton';
import { useContainerSize } from '../hooks/useContainerSize';

interface FinancialModuleProps {
  financial: FinancialMetrics;
}

export const FinancialModule: React.FC<FinancialModuleProps> = ({ financial }) => {
  const [containerRef, containerSize] = useContainerSize<HTMLDivElement>();

  if (!financial.lossCurve || financial.lossCurve.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">No loss curve data available</div>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-white">Financial Loss Distribution</h3>
        <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
          <div>
            <div className="text-white/60">Expected Loss</div>
            <div className="text-white font-semibold">${(financial.expectedLoss / 1000).toFixed(1)}K</div>
          </div>
          <div>
            <div className="text-white/60">VaR 95%</div>
            <div className="text-white font-semibold">${(financial.var95 / 1000).toFixed(1)}K</div>
          </div>
          <div>
            <div className="text-white/60">CVaR 95%</div>
            <div className="text-white font-semibold">${(financial.cvar95 / 1000).toFixed(1)}K</div>
          </div>
        </div>
      </div>
      <div 
        ref={containerRef}
        style={{ height: '350px', minHeight: '350px', minWidth: '300px', width: '100%', position: 'relative' }}
      >
        {containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? (
          <LineChart 
            width={containerSize.width} 
            height={containerSize.height}
            data={financial.lossCurve}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="loss" tick={{ fill: 'rgba(255,255,255,0.6)' }} />
            <YAxis tick={{ fill: 'rgba(255,255,255,0.6)' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0,0,0,0.9)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
              }}
            />
            <Line type="monotone" dataKey="probability" stroke="#EF4444" strokeWidth={2} />
          </LineChart>
        ) : (
          <ChartSkeleton height={350} />
        )}
      </div>
    </GlassCard>
  );
};




