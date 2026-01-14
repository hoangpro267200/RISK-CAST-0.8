/**
 * Tooltip Component
 * 
 * Unified tooltip for consistent info display.
 * - Hover/focus triggered
 * - Multiple positions
 * - Rich content support
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Info, HelpCircle } from 'lucide-react';

export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

export interface TooltipProps {
  /** Tooltip content */
  content: React.ReactNode;
  /** Trigger element */
  children: React.ReactNode;
  /** Position relative to trigger */
  position?: TooltipPosition;
  /** Delay before showing (ms) */
  delay?: number;
  /** Max width */
  maxWidth?: number;
  /** Additional classes for tooltip */
  className?: string;
  /** Disable tooltip */
  disabled?: boolean;
}

/**
 * Get position classes based on position prop
 */
function getPositionClasses(position: TooltipPosition): string {
  switch (position) {
    case 'top':
      return 'bottom-full left-1/2 -translate-x-1/2 mb-2';
    case 'bottom':
      return 'top-full left-1/2 -translate-x-1/2 mt-2';
    case 'left':
      return 'right-full top-1/2 -translate-y-1/2 mr-2';
    case 'right':
      return 'left-full top-1/2 -translate-y-1/2 ml-2';
    default:
      return 'bottom-full left-1/2 -translate-x-1/2 mb-2';
  }
}

/**
 * Get arrow classes based on position
 */
function getArrowClasses(position: TooltipPosition): string {
  switch (position) {
    case 'top':
      return 'top-full left-1/2 -translate-x-1/2 border-t-slate-800 border-x-transparent border-b-transparent';
    case 'bottom':
      return 'bottom-full left-1/2 -translate-x-1/2 border-b-slate-800 border-x-transparent border-t-transparent';
    case 'left':
      return 'left-full top-1/2 -translate-y-1/2 border-l-slate-800 border-y-transparent border-r-transparent';
    case 'right':
      return 'right-full top-1/2 -translate-y-1/2 border-r-slate-800 border-y-transparent border-l-transparent';
    default:
      return 'top-full left-1/2 -translate-x-1/2 border-t-slate-800 border-x-transparent border-b-transparent';
  }
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 200,
  maxWidth = 280,
  className = '',
  disabled = false
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  const showTooltip = useCallback(() => {
    if (disabled) return;
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  }, [delay, disabled]);

  const hideTooltip = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  if (disabled) {
    return <>{children}</>;
  }

  return (
    <div
      ref={triggerRef}
      className="relative inline-flex"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      
      {isVisible && (
        <div
          role="tooltip"
          className={`
            absolute z-50 
            ${getPositionClasses(position)}
            animate-in fade-in zoom-in-95 duration-150
            ${className}
          `}
          style={{ maxWidth }}
        >
          <div className="bg-slate-800/95 backdrop-blur-xl border border-white/10 rounded-lg px-3 py-2 shadow-xl shadow-black/50">
            <div className="text-sm text-white/90">
              {content}
            </div>
          </div>
          {/* Arrow */}
          <div 
            className={`absolute w-0 h-0 border-4 ${getArrowClasses(position)}`}
          />
        </div>
      )}
    </div>
  );
};

/**
 * Info Tooltip - Icon with tooltip
 */
export interface InfoTooltipProps {
  content: React.ReactNode;
  position?: TooltipPosition;
  size?: 'sm' | 'md' | 'lg';
  iconType?: 'info' | 'help';
  className?: string;
}

export const InfoTooltip: React.FC<InfoTooltipProps> = ({
  content,
  position = 'top',
  size = 'sm',
  iconType = 'info',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  const Icon = iconType === 'help' ? HelpCircle : Info;

  return (
    <Tooltip content={content} position={position}>
      <button
        type="button"
        className={`text-white/40 hover:text-white/70 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded ${className}`}
        aria-label="More information"
      >
        <Icon className={sizeClasses[size]} />
      </button>
    </Tooltip>
  );
};

/**
 * Term Tooltip - For explaining financial/risk terms
 */
export interface TermTooltipProps {
  term: string;
  definition: string;
  learnMoreUrl?: string;
}

export const TermTooltip: React.FC<TermTooltipProps> = ({
  term,
  definition,
  learnMoreUrl
}) => {
  return (
    <Tooltip
      content={
        <div>
          <p className="font-medium text-white mb-1">{term}</p>
          <p className="text-white/70 text-xs">{definition}</p>
          {learnMoreUrl && (
            <a
              href={learnMoreUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 text-xs hover:underline mt-2 inline-block"
            >
              Learn more →
            </a>
          )}
        </div>
      }
      maxWidth={320}
    >
      <span className="border-b border-dotted border-white/40 cursor-help">
        {term}
      </span>
    </Tooltip>
  );
};

/**
 * Common financial terms definitions
 */
export const TERM_DEFINITIONS: Record<string, { term: string; definition: string }> = {
  var: {
    term: 'Value at Risk (VaR)',
    definition: 'Maximum potential loss at a given confidence level (e.g., 95%). VaR 95% means there\'s a 5% chance the loss will exceed this amount.'
  },
  cvar: {
    term: 'Conditional VaR (CVaR)',
    definition: 'Expected loss in the worst-case scenarios beyond VaR. Also called Expected Shortfall, it measures tail risk.'
  },
  confidence: {
    term: 'Confidence Level',
    definition: 'Statistical certainty of the risk assessment based on data quality and model accuracy. Higher values indicate more reliable predictions.'
  },
  expectedLoss: {
    term: 'Expected Loss',
    definition: 'The average or most likely loss amount based on probability-weighted scenarios.'
  },
  riskScore: {
    term: 'Risk Score',
    definition: 'Composite metric (0-100) aggregating multiple risk factors. Higher scores indicate greater risk exposure.'
  }
};

export default Tooltip;
