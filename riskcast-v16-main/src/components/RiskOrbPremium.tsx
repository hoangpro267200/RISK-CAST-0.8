import React, { useMemo, useState } from 'react';
import { safeNumber, clampNumber } from '../utils/safeData';
import { ChevronDown, ChevronUp } from 'lucide-react';

export type OrbSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'responsive';

export interface RiskOrbPremiumProps {
  score: number;
  riskLevel?: 'LOW' | 'MEDIUM' | 'HIGH';
  /** Size variant - 'responsive' auto-adjusts based on breakpoint */
  size?: OrbSize;
  /** Enable compact mode toggle */
  collapsible?: boolean;
  /** Initial collapsed state (only if collapsible is true) */
  defaultCollapsed?: boolean;
  /** Callback when collapsed state changes */
  onCollapsedChange?: (collapsed: boolean) => void;
  className?: string;
}

// Size configurations in pixels
const SIZE_CONFIG: Record<Exclude<OrbSize, 'responsive'>, { width: number; fontSize: number; labelSize: number }> = {
  xs: { width: 120, fontSize: 28, labelSize: 10 },
  sm: { width: 160, fontSize: 36, labelSize: 12 },
  md: { width: 200, fontSize: 44, labelSize: 14 },
  lg: { width: 240, fontSize: 52, labelSize: 16 },
  xl: { width: 280, fontSize: 56, labelSize: 16 },
};

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
  size = 'responsive',
  collapsible = false,
  defaultCollapsed = false,
  onCollapsedChange,
  className = '',
}) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  
  const normalizedScore = useMemo(() => clampNumber(safeNumber(score, 0), 0, 100), [score]);
  const color = useMemo(() => getRiskColor(riskLevel), [riskLevel]);
  const [gradientStart, gradientEnd] = useMemo(() => getRiskGradient(riskLevel), [riskLevel]);

  // Pulse animation intensity based on risk level
  const pulseIntensity = useMemo(() => {
    if (riskLevel === 'HIGH') return 1.15;
    if (riskLevel === 'MEDIUM') return 1.08;
    return 1.05;
  }, [riskLevel]);

  // Handle collapse toggle
  const handleToggleCollapse = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    onCollapsedChange?.(newState);
  };

  // Unique ID for SVG gradients to avoid conflicts when multiple orbs on page
  const uniqueId = useMemo(() => `orb-${Math.random().toString(36).substr(2, 9)}`, []);

  // Responsive size classes
  const responsiveClasses = size === 'responsive' 
    ? 'w-32 h-32 xs:w-40 xs:h-40 sm:w-48 sm:h-48 md:w-56 md:h-56 lg:w-64 lg:h-64'
    : '';

  // Get fixed size config
  const sizeConfig = size !== 'responsive' ? SIZE_CONFIG[size] : SIZE_CONFIG.lg;
  const orbWidth = size === 'responsive' ? '100%' : sizeConfig.width;
  const fontSize = sizeConfig.fontSize;
  const labelSize = sizeConfig.labelSize;

  // Collapsed (compact) view
  if (collapsible && isCollapsed) {
    return (
      <div className={`flex flex-col items-center ${className}`}>
        <button
          onClick={handleToggleCollapse}
          className="flex items-center gap-3 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all group"
          aria-expanded={false}
          aria-label="Expand risk score display"
        >
          <div 
            className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
            style={{ background: `linear-gradient(135deg, ${gradientStart}, ${gradientEnd})` }}
          >
            {normalizedScore}
          </div>
          <span className="text-white/80 font-medium">{riskLevel} Risk</span>
          <ChevronDown className="w-4 h-4 text-white/50 group-hover:text-white/80 transition-colors" />
        </button>
      </div>
    );
  }

  return (
    <div className={`relative flex flex-col items-center justify-center ${className}`}>
      {/* Collapse button */}
      {collapsible && (
        <button
          onClick={handleToggleCollapse}
          className="absolute -top-2 -right-2 z-10 p-1.5 bg-white/10 hover:bg-white/20 rounded-full border border-white/10 transition-all"
          aria-expanded={true}
          aria-label="Collapse risk score display"
        >
          <ChevronUp className="w-3 h-3 text-white/70" />
        </button>
      )}

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

      {/* Main orb container - Responsive */}
      <div className={size === 'responsive' ? responsiveClasses : ''}>
        <svg
          width={orbWidth}
          height={orbWidth}
          viewBox="0 0 280 280"
          className="relative w-full h-full"
          role="img"
          aria-label={`Risk score: ${normalizedScore} out of 100, ${riskLevel.toLowerCase()} risk`}
          aria-live="polite"
          aria-atomic="true"
        >
          <defs>
            {/* Gradient for orb - unique ID */}
            <radialGradient id={`${uniqueId}-gradient`} cx="40%" cy="40%">
              <stop offset="0%" stopColor={gradientEnd} stopOpacity="0.9" />
              <stop offset="50%" stopColor={color} stopOpacity="0.7" />
              <stop offset="100%" stopColor={gradientStart} stopOpacity="0.5" />
            </radialGradient>

            {/* Shine effect */}
            <radialGradient id={`${uniqueId}-shine`} cx="35%" cy="35%">
              <stop offset="0%" stopColor="white" stopOpacity="0.4" />
              <stop offset="50%" stopColor="white" stopOpacity="0.1" />
              <stop offset="100%" stopColor="white" stopOpacity="0" />
            </radialGradient>

            {/* Shadow */}
            <filter id={`${uniqueId}-shadow`}>
              <feDropShadow dx="0" dy="8" stdDeviation="12" floodColor={color} floodOpacity="0.3" />
            </filter>
          </defs>

          {/* Main orb circle */}
          <circle
            cx="140"
            cy="140"
            r="120"
            fill={`url(#${uniqueId}-gradient)`}
            filter={`url(#${uniqueId}-shadow)`}
            style={{
              animation: `orbPulse 3s ease-in-out infinite`,
              transformOrigin: 'center',
            }}
          />

          {/* Shine overlay */}
          <circle cx="140" cy="140" r="120" fill={`url(#${uniqueId}-shine)`} opacity="0.6" />

          {/* Inner glow */}
          <circle cx="140" cy="140" r="100" fill={color} opacity="0.1" />

          {/* Score text */}
          <text
            x="140"
            y="150"
            textAnchor="middle"
            fontSize={fontSize}
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
            fontSize={labelSize}
            fontWeight="500"
            fill="white"
            opacity="0.8"
            style={{ userSelect: 'none', letterSpacing: '0.1em' }}
          >
            {riskLevel}
          </text>
        </svg>
      </div>

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
