/**
 * Skeleton Loading Components
 * 
 * Unified skeleton system for perceived performance.
 * Matches glassmorphism design (rounded, subtle border, blur).
 */

import React from 'react';

// =============================================================================
// BASE SKELETON
// =============================================================================

export interface SkeletonProps {
  className?: string;
  /** Animation variant */
  variant?: 'pulse' | 'shimmer' | 'none';
  /** Border radius preset */
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | 'full';
  /** Custom inline styles */
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'shimmer',
  rounded = 'lg',
  style
}) => {
  const animationClass = 
    variant === 'pulse' ? 'animate-pulse' :
    variant === 'shimmer' ? 'loading-shimmer' :
    '';

  const roundedClass = 
    rounded === 'none' ? '' :
    rounded === 'sm' ? 'rounded-sm' :
    rounded === 'md' ? 'rounded-md' :
    rounded === 'lg' ? 'rounded-lg' :
    rounded === 'xl' ? 'rounded-xl' :
    rounded === '2xl' ? 'rounded-2xl' :
    rounded === '3xl' ? 'rounded-3xl' :
    'rounded-full';

  return (
    <div 
      className={`bg-white/5 border border-white/10 ${roundedClass} ${animationClass} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
};

// =============================================================================
// TEXT SKELETONS
// =============================================================================

export interface SkeletonTextProps extends SkeletonProps {
  /** Number of lines to show */
  lines?: number;
  /** Width pattern: 'full', 'varied', or specific widths per line */
  widths?: 'full' | 'varied' | string[];
}

export const SkeletonText: React.FC<SkeletonTextProps> = ({
  lines = 3,
  widths = 'varied',
  variant = 'shimmer',
  className = ''
}) => {
  const getWidth = (index: number): string => {
    if (widths === 'full') return 'w-full';
    if (Array.isArray(widths)) return widths[index] || 'w-full';
    // Varied pattern
    if (index === lines - 1) return 'w-3/4';
    if (index % 2 === 0) return 'w-full';
    return 'w-5/6';
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton 
          key={i}
          variant={variant}
          rounded="md"
          className={`h-4 ${getWidth(i)}`}
        />
      ))}
    </div>
  );
};

// =============================================================================
// CARD SKELETONS
// =============================================================================

export interface SkeletonCardProps extends SkeletonProps {
  /** Include header */
  showHeader?: boolean;
  /** Include icon */
  showIcon?: boolean;
  /** Content lines */
  contentLines?: number;
  /** Include footer */
  showFooter?: boolean;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({
  showHeader = true,
  showIcon = true,
  contentLines = 3,
  showFooter = false,
  variant = 'shimmer',
  className = ''
}) => {
  return (
    <div 
      className={`backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 ${className}`}
      aria-hidden="true"
    >
      {showHeader && (
        <div className="flex items-center gap-3 mb-4">
          {showIcon && (
            <Skeleton variant={variant} rounded="xl" className="w-10 h-10" />
          )}
          <Skeleton variant={variant} rounded="md" className="h-6 w-32" />
        </div>
      )}
      
      <SkeletonText lines={contentLines} variant={variant} />
      
      {showFooter && (
        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-white/10">
          <Skeleton variant={variant} rounded="md" className="h-4 w-20" />
          <Skeleton variant={variant} rounded="full" className="h-4 w-4" />
          <Skeleton variant={variant} rounded="md" className="h-4 w-16" />
        </div>
      )}
    </div>
  );
};

// =============================================================================
// STAT CARD SKELETON
// =============================================================================

export const SkeletonStatCard: React.FC<SkeletonProps> = ({
  variant = 'shimmer',
  className = ''
}) => {
  return (
    <div 
      className={`backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl p-4 text-center ${className}`}
      aria-hidden="true"
    >
      <Skeleton variant={variant} rounded="lg" className="w-6 h-6 mx-auto mb-2" />
      <Skeleton variant={variant} rounded="md" className="h-8 w-16 mx-auto mb-2" />
      <Skeleton variant={variant} rounded="md" className="h-3 w-20 mx-auto mb-1" />
      <Skeleton variant={variant} rounded="md" className="h-2 w-14 mx-auto" />
    </div>
  );
};

// =============================================================================
// CHART SKELETON
// =============================================================================

export interface SkeletonChartProps extends SkeletonProps {
  /** Chart type for visual representation */
  type?: 'bar' | 'line' | 'radar' | 'pie' | 'generic';
  /** Height in pixels */
  height?: number;
}

export const SkeletonChart: React.FC<SkeletonChartProps> = ({
  type = 'generic',
  height = 300,
  variant = 'shimmer',
  className = ''
}) => {
  return (
    <div 
      className={`backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 ${className}`}
      style={{ minHeight: height }}
      aria-hidden="true"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Skeleton variant={variant} rounded="lg" className="w-8 h-8" />
          <Skeleton variant={variant} rounded="md" className="h-6 w-40" />
        </div>
        <Skeleton variant={variant} rounded="md" className="h-8 w-24" />
      </div>

      {/* Chart area */}
      <div 
        className="relative flex items-end justify-between gap-2"
        style={{ height: height - 120 }}
      >
        {type === 'bar' && (
          <>
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton 
                key={i}
                variant={variant}
                rounded="md"
                className="flex-1"
                style={{ 
                  height: `${30 + Math.sin(i) * 30 + 40}%`,
                  animationDelay: `${i * 100}ms`
                }}
              />
            ))}
          </>
        )}

        {type === 'radar' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="relative w-full h-full max-w-[250px] max-h-[250px]">
              {[0.9, 0.7, 0.5, 0.3].map((scale, i) => (
                <Skeleton
                  key={i}
                  variant={variant}
                  rounded="full"
                  className="absolute inset-0"
                  style={{
                    transform: `scale(${scale})`,
                    opacity: 0.3 + (0.7 - scale)
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {(type === 'line' || type === 'generic') && (
          <div className="absolute inset-0 flex flex-col justify-center">
            <div className="flex items-end justify-between gap-1 h-3/4">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="flex-1 flex flex-col justify-end">
                  <Skeleton 
                    variant={variant}
                    rounded="sm"
                    className="w-full"
                    style={{ 
                      height: `${20 + Math.sin(i * 0.5) * 30 + 30}%`,
                      animationDelay: `${i * 50}ms`
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {type === 'pie' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <Skeleton 
              variant={variant}
              rounded="full"
              className="w-48 h-48"
            />
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <Skeleton variant={variant} rounded="sm" className="w-3 h-3" />
            <Skeleton variant={variant} rounded="md" className="h-3 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
};

// =============================================================================
// RISK ORB SKELETON
// =============================================================================

export const SkeletonRiskOrb: React.FC<SkeletonProps> = ({
  variant = 'pulse',
  className = ''
}) => {
  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      {/* Orb */}
      <div className="relative">
        <Skeleton 
          variant={variant}
          rounded="full"
          className="w-48 h-48 sm:w-56 sm:h-56 lg:w-64 lg:h-64"
        />
        {/* Inner glow effect */}
        <div className="absolute inset-8 rounded-full bg-white/5 animate-pulse" />
      </div>
      
      {/* Badge below orb */}
      <div className="mt-6 text-center space-y-2">
        <Skeleton variant={variant} rounded="full" className="h-6 w-24 mx-auto" />
        <Skeleton variant={variant} rounded="md" className="h-4 w-48 mx-auto" />
      </div>
    </div>
  );
};

// =============================================================================
// EXECUTIVE SUMMARY SKELETON
// =============================================================================

export const SkeletonExecutiveSummary: React.FC<SkeletonProps> = ({
  variant = 'shimmer',
  className = ''
}) => {
  return (
    <div 
      className={`backdrop-blur-3xl bg-white/8 border-2 border-blue-500/20 rounded-3xl p-8 ${className}`}
      aria-hidden="true"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
        {/* Risk Orb area */}
        <SkeletonRiskOrb variant={variant} />

        {/* Takeaways area */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <Skeleton variant={variant} rounded="lg" className="w-6 h-6" />
            <Skeleton variant={variant} rounded="md" className="h-7 w-64" />
          </div>

          {/* Takeaway items */}
          {Array.from({ length: 3 }).map((_, i) => (
            <div 
              key={i}
              className="flex items-start gap-3 p-4 bg-white/5 rounded-xl border border-white/10"
            >
              <Skeleton variant={variant} rounded="full" className="w-8 h-8 flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton variant={variant} rounded="md" className="h-4 w-full" />
                <Skeleton variant={variant} rounded="md" className="h-4 w-3/4" />
              </div>
            </div>
          ))}

          {/* Confidence bar */}
          <div className="flex items-center gap-4 pt-4 border-t border-white/10">
            <Skeleton variant={variant} rounded="md" className="w-5 h-5" />
            <Skeleton variant={variant} rounded="md" className="h-4 w-28" />
            <Skeleton variant={variant} rounded="md" className="h-6 w-12" />
          </div>
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// RESULTS PAGE SKELETON (FULL PAGE)
// =============================================================================

export const SkeletonResultsPage: React.FC = () => {
  return (
    <div className="space-y-8" aria-label="Loading results..." role="status">
      {/* Executive Summary */}
      <SkeletonExecutiveSummary />

      {/* Route & Timeline cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SkeletonCard showHeader contentLines={4} />
        <SkeletonCard showHeader contentLines={3} />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonStatCard key={i} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonChart type="radar" height={350} />
        <SkeletonChart type="bar" height={350} />
      </div>

      {/* Narrative */}
      <SkeletonCard showHeader contentLines={6} showFooter />
    </div>
  );
};

export default Skeleton;
