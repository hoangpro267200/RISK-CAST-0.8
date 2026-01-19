/**
 * Unified Loader Component
 * 
 * Consistent loading states across the application.
 * - Spinner variant
 * - Dots variant
 * - Pulse variant
 * - Skeleton variant
 */

import React from 'react';

export type LoaderVariant = 'spinner' | 'dots' | 'pulse' | 'skeleton';
export type LoaderSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface LoaderProps {
  /** Visual variant */
  variant?: LoaderVariant;
  /** Size preset */
  size?: LoaderSize;
  /** Loading label (for accessibility and display) */
  label?: string;
  /** Show label visually */
  showLabel?: boolean;
  /** Custom color class */
  color?: string;
  /** Additional classes */
  className?: string;
}

// Size configurations
const sizeConfig: Record<LoaderSize, { spinner: number; dots: number; pulse: number; text: string }> = {
  xs: { spinner: 12, dots: 4, pulse: 16, text: 'text-[10px]' },
  sm: { spinner: 16, dots: 6, pulse: 24, text: 'text-xs' },
  md: { spinner: 24, dots: 8, pulse: 32, text: 'text-sm' },
  lg: { spinner: 32, dots: 10, pulse: 48, text: 'text-base' },
  xl: { spinner: 48, dots: 12, pulse: 64, text: 'text-lg' }
};

/**
 * Spinner Loader
 */
const SpinnerLoader: React.FC<{ size: LoaderSize; color: string }> = ({ size, color }) => {
  const dim = sizeConfig[size].spinner;
  
  return (
    <div
      className={`border-2 border-current border-t-transparent rounded-full animate-spin ${color}`}
      style={{ width: dim, height: dim }}
      role="presentation"
    />
  );
};

/**
 * Dots Loader
 */
const DotsLoader: React.FC<{ size: LoaderSize; color: string }> = ({ size, color }) => {
  const dim = sizeConfig[size].dots;
  
  return (
    <div className="flex items-center gap-1" role="presentation">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={`rounded-full animate-bounce ${color}`}
          style={{
            width: dim,
            height: dim,
            animationDelay: `${i * 150}ms`
          }}
        />
      ))}
    </div>
  );
};

/**
 * Pulse Loader
 */
const PulseLoader: React.FC<{ size: LoaderSize; color: string }> = ({ size, color }) => {
  const dim = sizeConfig[size].pulse;
  
  return (
    <div
      className={`rounded-full animate-pulse ${color}`}
      style={{ width: dim, height: dim }}
      role="presentation"
    />
  );
};

/**
 * Unified Loader Component
 */
export const Loader: React.FC<LoaderProps> = ({
  variant = 'spinner',
  size = 'md',
  label = 'Loading...',
  showLabel = false,
  color = 'text-blue-400',
  className = ''
}) => {
  const bgColor = color.replace('text-', 'bg-');

  return (
    <div
      role="status"
      aria-label={label}
      className={`inline-flex flex-col items-center justify-center gap-2 ${className}`}
    >
      {variant === 'spinner' && <SpinnerLoader size={size} color={color} />}
      {variant === 'dots' && <DotsLoader size={size} color={bgColor} />}
      {variant === 'pulse' && <PulseLoader size={size} color={bgColor} />}
      
      {showLabel && (
        <span className={`${sizeConfig[size].text} text-white/60`}>
          {label}
        </span>
      )}
      
      {/* Screen reader only label */}
      {!showLabel && (
        <span className="sr-only">{label}</span>
      )}
    </div>
  );
};

/**
 * Full Page Loader
 */
export interface PageLoaderProps {
  label?: string;
  sublabel?: string;
}

export const PageLoader: React.FC<PageLoaderProps> = ({
  label = 'Loading',
  sublabel = 'Please wait...'
}) => {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <div className="relative w-24 h-24 mx-auto mb-6">
          <div className="absolute inset-0 rounded-full border-4 border-blue-500/20"></div>
          <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-500 animate-spin"></div>
          <div 
            className="absolute inset-3 rounded-full border-4 border-transparent border-t-purple-500 animate-spin" 
            style={{ animationDuration: '1.5s', animationDirection: 'reverse' }}
          ></div>
          <div 
            className="absolute inset-6 rounded-full border-4 border-transparent border-t-cyan-500 animate-spin" 
            style={{ animationDuration: '2s' }}
          ></div>
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">{label}</h2>
        <p className="text-white/50 text-sm">{sublabel}</p>
      </div>
    </div>
  );
};

/**
 * Button Loader (inline)
 */
export interface ButtonLoaderProps {
  size?: 'sm' | 'md';
  color?: string;
}

export const ButtonLoader: React.FC<ButtonLoaderProps> = ({
  size = 'md',
  color = 'text-current'
}) => {
  const dim = size === 'sm' ? 14 : 18;
  
  return (
    <div
      className={`border-2 border-current border-t-transparent rounded-full animate-spin ${color}`}
      style={{ width: dim, height: dim }}
      aria-hidden="true"
    />
  );
};

/**
 * Chart Loader
 */
export interface ChartLoaderProps {
  height?: number;
  label?: string;
}

export const ChartLoader: React.FC<ChartLoaderProps> = ({
  height = 300,
  label = 'Loading chart...'
}) => {
  return (
    <div 
      className="flex items-center justify-center bg-white/5 rounded-xl border border-white/10"
      style={{ minHeight: height }}
    >
      <div className="text-center">
        <Loader variant="spinner" size="lg" color="text-blue-400" />
        <p className="text-white/50 text-sm mt-3">{label}</p>
      </div>
    </div>
  );
};

export default Loader;
