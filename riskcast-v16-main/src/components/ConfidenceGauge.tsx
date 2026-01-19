import React, { useMemo } from 'react';
import { safeRatio01 } from '../utils/safeData';

export interface ConfidenceGaugeProps {
  confidence: number; // 0-1 or 0-100
  label?: string;
  className?: string;
  showPercentage?: boolean;
}

function normalizeConfidence(value: number): number {
  const safe = safeRatio01(value > 1 ? value / 100 : value);
  return safe;
}

function getConfidenceColor(confidence: number): { main: string; glow: string } {
  if (confidence >= 0.8) return { main: '#10b981', glow: 'rgba(16, 185, 129, 0.4)' }; // emerald
  if (confidence >= 0.6) return { main: '#f59e0b', glow: 'rgba(245, 158, 11, 0.4)' }; // amber
  return { main: '#ef4444', glow: 'rgba(239, 68, 68, 0.4)' }; // red
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return 'High Confidence';
  if (confidence >= 0.6) return 'Medium Confidence';
  return 'Low Confidence';
}

export const ConfidenceGauge: React.FC<ConfidenceGaugeProps> = ({
  confidence,
  label,
  className = '',
  showPercentage = true,
}) => {
  const normalized = useMemo(() => normalizeConfidence(confidence), [confidence]);
  const percentage = useMemo(() => Math.round(normalized * 100), [normalized]);
  const colors = useMemo(() => getConfidenceColor(normalized), [normalized]);
  const confidenceLabel = useMemo(
    () => label || getConfidenceLabel(normalized),
    [label, normalized]
  );

  // Full circle gauge parameters
  const size = 180;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const center = size / 2;
  const circumference = 2 * Math.PI * radius;
  
  // Start from top (-90deg) and go 270 degrees (3/4 circle)
  const arcLength = circumference * 0.75; // 270 degrees
  const progressOffset = arcLength - (normalized * arcLength);

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className="relative" style={{ width: size, height: size }}>
        {/* Glow effect */}
        <div 
          className="absolute inset-4 rounded-full blur-xl opacity-30"
          style={{ backgroundColor: colors.glow }}
        />
        
        <svg width={size} height={size} className="relative z-10">
          <defs>
            {/* Gradient for the active arc */}
            <linearGradient id="confidenceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={colors.main} stopOpacity="0.8" />
              <stop offset="100%" stopColor={colors.main} stopOpacity="1" />
            </linearGradient>
            
            {/* Drop shadow filter */}
            <filter id="dropShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor={colors.main} floodOpacity="0.5" />
            </filter>
          </defs>

          {/* Background track (270 degrees) */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${arcLength} ${circumference}`}
            transform={`rotate(135 ${center} ${center})`}
          />

          {/* Progress arc */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="url(#confidenceGradient)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeDashoffset={progressOffset}
            transform={`rotate(135 ${center} ${center})`}
            filter="url(#dropShadow)"
            style={{
              transition: 'stroke-dashoffset 0.8s ease-out',
            }}
          />

          {/* End cap indicator dot */}
          <circle
            cx={center + radius * Math.cos((135 + normalized * 270) * Math.PI / 180)}
            cy={center + radius * Math.sin((135 + normalized * 270) * Math.PI / 180)}
            r={strokeWidth / 2 + 2}
            fill={colors.main}
            filter="url(#dropShadow)"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showPercentage && (
            <div 
              className="text-5xl font-bold tracking-tight"
              style={{ color: colors.main }}
            >
              {percentage}%
            </div>
          )}
          <div className="text-sm font-medium text-white/80 mt-1">
            {confidenceLabel}
          </div>
          <div className="text-xs text-white/40 mt-0.5">
            Data Confidence
          </div>
        </div>
      </div>
    </div>
  );
};
