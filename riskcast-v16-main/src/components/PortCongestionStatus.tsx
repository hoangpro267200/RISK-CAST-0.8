/**
 * Port Congestion Status Component
 * 
 * Displays port congestion data for POL, POD, and transshipment ports.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { PortCongestionData } from '../types/logisticsTypes';
import { MapPin, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

interface PortCongestionStatusProps {
  pol: PortCongestionData;
  pod: PortCongestionData;
  transshipments: PortCongestionData[];
}

// Get status color and icon
const getStatusStyle = (status: string) => {
  const statusLower = status.toLowerCase();
  if (statusLower.includes('high') || statusLower.includes('severe')) {
    return {
      color: 'text-red-400',
      bgColor: 'bg-red-500/20',
      borderColor: 'border-red-500/30',
      icon: AlertCircle,
    };
  }
  if (statusLower.includes('medium') || statusLower.includes('mild')) {
    return {
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/20',
      borderColor: 'border-amber-500/30',
      icon: Clock,
    };
  }
  return {
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/20',
    borderColor: 'border-emerald-500/30',
    icon: CheckCircle2,
  };
};

// Format percentage change
const formatDelta = (current: number, normal: number): string => {
  const delta = ((current - normal) / normal) * 100;
  return `${delta > 0 ? '+' : ''}${delta.toFixed(0)}%`;
};

export const PortCongestionStatus: React.FC<PortCongestionStatusProps> = ({
  pol,
  pod,
  transshipments,
}) => {
  // Defensive guard
  if (!pol || !pod) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <MapPin className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Port congestion data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not retrieve port congestion data. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  const renderPortRow = (port: PortCongestionData, label: string) => {
    const style = getStatusStyle(port.status);
    const Icon = style.icon;
    const delta = formatDelta(port.dwellTime, port.normalDwellTime);
    const isElevated = port.dwellTime > port.normalDwellTime * 1.2;

    return (
      <tr className="border-b border-white/5 hover:bg-white/5 transition-colors">
        <td className="py-4 px-4">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-400" />
            <span className="text-white font-medium">{port.name}</span>
            {label && (
              <span className="text-xs px-2 py-1 bg-white/10 text-white/60 rounded">
                {label}
              </span>
            )}
          </div>
        </td>
        <td className="py-4 px-4 text-right">
          <span className="text-white font-medium">{port.dwellTime.toFixed(1)} days</span>
        </td>
        <td className="py-4 px-4 text-right">
          <span className="text-white/60">{port.normalDwellTime.toFixed(1)}</span>
        </td>
        <td className="py-4 px-4">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${style.bgColor} ${style.borderColor}`}>
            <Icon className={`w-3.5 h-3.5 ${style.color}`} />
            <span className={`text-xs font-medium ${style.color}`}>
              {port.status.toUpperCase()}
            </span>
          </div>
        </td>
        <td className="py-4 px-4 text-right">
          <span className={`text-sm font-semibold ${
            isElevated ? 'text-red-400' : 'text-emerald-400'
          }`}>
            {delta}
          </span>
        </td>
      </tr>
    );
  };

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-blue-400" />
          <span>Port Congestion Status</span>
        </h3>
        <p className="text-sm text-white/60">
          Current port dwell times and congestion levels
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Port</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-white/60">Dwell Time</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-white/60">Normal</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Status</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-white/60">Delta</th>
            </tr>
          </thead>
          <tbody>
            {renderPortRow(pol, 'POL')}
            {transshipments.map((port, idx) => renderPortRow(port, `TSP ${idx + 1}`))}
            {renderPortRow(pod, 'POD')}
          </tbody>
        </table>
      </div>

      {/* Alerts for High Congestion */}
      {transshipments.some(p => p.dwellTime > p.normalDwellTime * 1.5) && (
        <div className="mt-6 p-4 bg-red-500/10 rounded-lg border border-red-500/20">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-red-400 mb-2">High Congestion Alert</h4>
              {transshipments
                .filter(p => p.dwellTime > p.normalDwellTime * 1.5)
                .map((port, idx) => (
                  <p key={idx} className="text-sm text-white/80 mb-1">
                    <strong>{port.name}</strong> transshipment port experiencing HIGH congestion. 
                    Expected additional delay: {(port.dwellTime - port.normalDwellTime).toFixed(1)} days
                  </p>
                ))}
              <p className="text-xs text-white/60 mt-2">
                Alternative: Consider alternative ports or buffer additional transit time.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Data Source Note */}
      <div className="mt-4 text-xs text-white/40">
        Data Source: AIS vessel tracking, updated 2 hours ago
      </div>
    </GlassCard>
  );
};
