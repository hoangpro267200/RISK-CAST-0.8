import React, { useMemo } from 'react';
import { safeNumber, clampNumber } from '../utils/safeData';

export interface RiskOrbPremiumProps {
  score: number;
  riskLevel?: 'LOW' | 'MEDIUM' | 'HIGH';
  className?: string;
}

function getRiskColor(level: string): string {
  switch (level) {
    case 'HIGH':
      return '#ef4444'; // red-500
    case 'MEDIUM':
      return '#f59e0b'; // amber-500
    case 'LOW':
      return '#10b981'; // emerald-500
    default:
      return '#6b7280'; // gray-500
  }
}

function getRiskGradient(level: string): [string, string] {
  switch (level) {
    case 'HIGH':
      return ['#dc2626', '#ef4444']; // red-600 to red-500
    case 'MEDIUM':
      return ['#d97706', '#f59e0b']; // amber-600 to amber-500
    case 'LOW':
      return ['#059669', '#10b981']; // emerald-600 to emerald-500
    default:
      return ['#4b5563', '#6b7280']; // gray-600 to gray-500
  }
}

export const RiskOrbPremium: React.FC<RiskOrbPremiumProps> = ({
  score,
  riskLevel = 'MEDIUM',
  className = '',
}) => {
  const normalizedScore = useMemo(() => clampNumber(safeNumber(score, 0), 0, 100), [score]);
  const color = useMemo(() => getRiskColor(riskLevel), [riskLevel]);
  const [gradientStart, gradientEnd] = useMemo(() => getRiskGradient(riskLevel), [riskLevel]);

  // Pulse animation intensity based on risk level
  const pulseIntensity = useMemo(() => {
    if (riskLevel === 'HIGH') return 1.15;
    if (riskLevel === 'MEDIUM') return 1.08;
    return 1.05;
  }, [riskLevel]);

  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      {/* Outer glow rings */}
      <div
        className="absolute inset-0 rounded-full opacity-20 blur-3xl"
        style={{
          background: `radial-gradient(circle, ${color}, transparent 70%)`,
          animation: 'pulse 3s ease-in-out infinite',
        }}
      />

      {/* Middle ring */}
      <div
        className="absolute inset-4 rounded-full opacity-30 blur-2xl"
        style={{
          background: `radial-gradient(circle, ${gradientEnd}, transparent 60%)`,
          animation: 'pulse 2s ease-in-out infinite',
        }}
      />

      {/* Main orb container */}
      <svg
        width="280"
        height="280"
        viewBox="0 0 280 280"
        className="relative"
        role="img"
        aria-label={`Risk score: ${normalizedScore} out of 100, ${riskLevel.toLowerCase()} risk`}
      >
        <defs>
          {/* Gradient for orb */}
          <radialGradient id="orbGradient" cx="40%" cy="40%">
            <stop offset="0%" stopColor={gradientEnd} stopOpacity="0.9" />
            <stop offset="50%" stopColor={color} stopOpacity="0.7" />
            <stop offset="100%" stopColor={gradientStart} stopOpacity="0.5" />
          </radialGradient>

          {/* Shine effect */}
          <radialGradient id="shineGradient" cx="35%" cy="35%">
            <stop offset="0%" stopColor="white" stopOpacity="0.4" />
            <stop offset="50%" stopColor="white" stopOpacity="0.1" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>

          {/* Shadow */}
          <filter id="orbShadow">
            <feDropShadow dx="0" dy="8" stdDeviation="12" floodColor={color} floodOpacity="0.3" />
          </filter>
        </defs>

        {/* Main orb circle */}
        <circle
          cx="140"
          cy="140"
          r="120"
          fill="url(#orbGradient)"
          filter="url(#orbShadow)"
          style={{
            animation: `orbPulse 3s ease-in-out infinite`,
            transformOrigin: 'center',
          }}
        />

        {/* Shine overlay */}
        <circle cx="140" cy="140" r="120" fill="url(#shineGradient)" opacity="0.6" />

        {/* Inner glow */}
        <circle cx="140" cy="140" r="100" fill={color} opacity="0.1" />

        {/* Score text */}
        <text
          x="140"
          y="150"
          textAnchor="middle"
          fontSize="56"
          fontWeight="700"
          fill="white"
          style={{ userSelect: 'none' }}
        >
          {normalizedScore}
        </text>

        {/* Risk level label */}
        <text
          x="140"
          y="190"
          textAnchor="middle"
          fontSize="16"
          fontWeight="500"
          fill="white"
          opacity="0.8"
          style={{ userSelect: 'none', letterSpacing: '0.1em' }}
        >
          {riskLevel}
        </text>
      </svg>

      <style>{`
        @keyframes orbPulse {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(${pulseIntensity});
            opacity: 0.9;
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 0.2;
            transform: scale(1);
          }
          50% {
            opacity: 0.3;
            transform: scale(1.05);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          @keyframes orbPulse {
            0%, 100% {
              transform: scale(1);
              opacity: 1;
            }
          }
          @keyframes pulse {
            0%, 100% {
              opacity: 0.2;
              transform: scale(1);
            }
          }
        }
      `}</style>
    </div>
  );
};
