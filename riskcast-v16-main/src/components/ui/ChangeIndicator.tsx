/**
 * ChangeIndicator Component
 * 
 * Shows toast/banner when data changes after refresh.
 * Highlights what metrics changed.
 */

import React, { useEffect, useState } from 'react';
import { X, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import type { DataChange } from '@/hooks/useChangeDetection';

export interface ChangeIndicatorProps {
  /** Whether changes were detected */
  hasChanges: boolean;
  /** List of changes */
  changes: DataChange[];
  /** Callback to dismiss */
  onDismiss: () => void;
  /** Auto-hide after milliseconds (0 = no auto-hide) */
  autoHideMs?: number;
  /** Position */
  position?: 'top' | 'bottom';
  className?: string;
}

/**
 * Format change amount for display
 */
function formatChange(change: DataChange): string {
  const amount = change.changeAmount ?? 0;
  const sign = amount > 0 ? '+' : '';
  
  if (change.field.includes('Loss') || change.field.includes('var') || change.field.includes('cvar')) {
    // Currency values
    return `${sign}$${Math.abs(amount).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  }
  
  // Numeric values
  return `${sign}${amount.toFixed(1)}`;
}

export const ChangeIndicator: React.FC<ChangeIndicatorProps> = ({
  hasChanges,
  changes,
  onDismiss,
  autoHideMs = 8000,
  position = 'top',
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  // Show when changes detected
  useEffect(() => {
    if (hasChanges && changes.length > 0) {
      setIsVisible(true);
      setIsExiting(false);
    }
  }, [hasChanges, changes]);

  // Auto-hide timer
  useEffect(() => {
    if (!isVisible || autoHideMs === 0) return;

    const timer = setTimeout(() => {
      handleDismiss();
    }, autoHideMs);

    return () => clearTimeout(timer);
  }, [isVisible, autoHideMs]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      setIsExiting(false);
      onDismiss();
    }, 300);
  };

  if (!isVisible) return null;

  const positionClasses = position === 'top'
    ? 'top-4 left-1/2 -translate-x-1/2'
    : 'bottom-4 left-1/2 -translate-x-1/2';

  const animationClasses = isExiting
    ? 'opacity-0 translate-y-[-10px]'
    : 'opacity-100 translate-y-0';

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`
        fixed z-[200] 
        ${positionClasses}
        max-w-lg w-full mx-4
        transition-all duration-300 ease-out
        ${animationClasses}
        ${className}
      `}
    >
      <div className="bg-slate-800/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-blue-500/10">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <RefreshCw className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">Data Updated</p>
              <p className="text-xs text-white/60">
                {changes.length} metric{changes.length > 1 ? 's' : ''} changed
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="p-1.5 text-white/50 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            aria-label="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Changes List */}
        <div className="px-4 py-3 space-y-2 max-h-48 overflow-y-auto">
          {changes.slice(0, 5).map((change, index) => (
            <div
              key={change.field}
              className={`
                flex items-center justify-between py-2 px-3 rounded-lg
                ${change.changeType === 'increase' 
                  ? 'bg-red-500/10 border border-red-500/20' 
                  : 'bg-emerald-500/10 border border-emerald-500/20'}
                animate-in fade-in slide-in-from-right duration-300
              `}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className="flex items-center gap-2">
                {change.changeType === 'increase' ? (
                  <TrendingUp className="w-4 h-4 text-red-400" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-emerald-400" />
                )}
                <span className="text-sm text-white/90">{change.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-medium tabular-nums ${
                  change.changeType === 'increase' ? 'text-red-400' : 'text-emerald-400'
                }`}>
                  {formatChange(change)}
                </span>
                {change.changePercent && Math.abs(change.changePercent) > 0.1 && (
                  <span className="text-xs text-white/40">
                    ({change.changePercent > 0 ? '+' : ''}{change.changePercent.toFixed(1)}%)
                  </span>
                )}
              </div>
            </div>
          ))}
          
          {changes.length > 5 && (
            <p className="text-xs text-white/40 text-center pt-1">
              +{changes.length - 5} more changes
            </p>
          )}
        </div>

        {/* Progress bar for auto-dismiss */}
        {autoHideMs > 0 && (
          <div className="h-1 bg-white/5">
            <div
              className="h-full bg-blue-500/50 transition-all duration-100"
              style={{
                animation: `shrink ${autoHideMs}ms linear forwards`
              }}
            />
          </div>
        )}
      </div>

      <style>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
};

export default ChangeIndicator;
