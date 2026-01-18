/**
 * Shared State Components - Unified Empty/Loading/Error States
 * 
 * These components use design tokens for consistent styling across Input/Summary/Results pages.
 * Replaces scattered state components with unified design system.
 */

import React from 'react';
import { Package, RefreshCw, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { GlassCard } from '../GlassCard';
import { designTokens } from '@/ui/design-tokens';

export interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  actionOnClick?: () => void;
  icon?: React.ReactNode;
  className?: string;
}

/**
 * Empty State Component (consistent across all pages)
 * Uses design tokens for typography and spacing
 */
export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  actionOnClick,
  icon,
  className = '',
}: EmptyStateProps) {
  const defaultIcon = icon || <Package className="w-10 h-10" style={{ color: designTokens.colors.textSoft }} />;
  
  const actionButton = actionLabel && (
    actionHref ? (
      <a
        href={actionHref}
        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25 hover:from-blue-600 hover:to-purple-600"
        style={{ 
          borderRadius: designTokens.radii.lg,
          padding: `${designTokens.spacing.md} ${designTokens.spacing.xl}`,
        }}
      >
        {actionLabel}
        <ArrowRight className="w-5 h-5" />
      </a>
    ) : actionOnClick ? (
      <button
        onClick={actionOnClick}
        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25 hover:from-blue-600 hover:to-purple-600"
        style={{ 
          borderRadius: designTokens.radii.lg,
          padding: `${designTokens.spacing.md} ${designTokens.spacing.xl}`,
        }}
      >
        {actionLabel}
        <ArrowRight className="w-5 h-5" />
      </button>
    ) : null
  );
  
  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center ${className}`}>
      <GlassCard className="max-w-md text-center">
        <div 
          className="w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center"
          style={{ 
            backgroundColor: `${designTokens.colors.info}10`,
          }}
        >
          {defaultIcon}
        </div>
        <h2 
          className="text-2xl font-bold mb-2"
          style={{ 
            color: designTokens.colors.textStrong,
            fontSize: designTokens.typography.h2.split('/')[0],
          }}
        >
          {title}
        </h2>
        <p 
          className="mb-6"
          style={{ 
            color: designTokens.colors.textMuted,
            fontSize: designTokens.typography.body.split('/')[0],
          }}
        >
          {description}
        </p>
        {actionButton}
      </GlassCard>
    </div>
  );
}

export interface LoadingStateProps {
  message?: string;
  className?: string;
}

/**
 * Loading State Component (consistent across all pages)
 */
export function LoadingState({ message = 'Loading...', className = '' }: LoadingStateProps) {
  return (
    <div className={`flex items-center justify-center p-8 ${className}`}>
      <div className="text-center">
        <Loader2 
          className="w-12 h-12 mx-auto mb-3 animate-spin"
          style={{ color: designTokens.colors.primaryNeon }}
        />
        <p 
          className="text-sm"
          style={{ 
            color: designTokens.colors.textMuted,
            fontSize: designTokens.typography.caption.split('/')[0],
          }}
        >
          {message}
        </p>
      </div>
    </div>
  );
}

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

/**
 * Error State Component (consistent across all pages)
 */
export function ErrorState({
  title = 'Error',
  message,
  onRetry,
  retryLabel = 'Retry',
  className = '',
}: ErrorStateProps) {
  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center ${className}`}>
      <GlassCard className="max-w-md text-center">
        <div 
          className="w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center"
          style={{ 
            backgroundColor: `${designTokens.colors.danger}10`,
          }}
        >
          <AlertCircle 
            className="w-10 h-10"
            style={{ color: designTokens.colors.danger }}
          />
        </div>
        <h2 
          className="text-2xl font-bold mb-2"
          style={{ 
            color: designTokens.colors.textStrong,
            fontSize: designTokens.typography.h2.split('/')[0],
          }}
        >
          {title}
        </h2>
        <p 
          className="mb-6"
          style={{ 
            color: designTokens.colors.textMuted,
            fontSize: designTokens.typography.body.split('/')[0],
          }}
        >
          {message}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25"
            style={{ 
              borderRadius: designTokens.radii.lg,
              padding: `${designTokens.spacing.md} ${designTokens.spacing.xl}`,
            }}
          >
            <RefreshCw className="w-5 h-5" />
            {retryLabel}
          </button>
        )}
      </GlassCard>
    </div>
  );
}
