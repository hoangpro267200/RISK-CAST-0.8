/**
 * EmptyState Component
 * 
 * Richer empty states for better UX.
 * - Illustration/icon
 * - Title + description
 * - Primary + secondary actions
 * - Help link
 */

import React from 'react';
import { 
  Package, 
  Search, 
  FileQuestion, 
  BarChart3, 
  GitCompare, 
  History,
  ArrowRight,
  ExternalLink
} from 'lucide-react';
import { GlassCard } from '../GlassCard';

export type EmptyStateType = 
  | 'no-data' 
  | 'no-results' 
  | 'no-analysis' 
  | 'no-comparison' 
  | 'no-history' 
  | 'error'
  | 'custom';

export interface EmptyStateAction {
  label: string;
  onClick?: () => void;
  href?: string;
  variant?: 'primary' | 'secondary';
  icon?: React.ReactNode;
}

export interface EmptyStateProps {
  /** Type preset */
  type?: EmptyStateType;
  /** Custom icon (overrides type icon) */
  icon?: React.ReactNode;
  /** Title */
  title?: string;
  /** Description text */
  description?: string;
  /** Primary action */
  primaryAction?: EmptyStateAction;
  /** Secondary action */
  secondaryAction?: EmptyStateAction;
  /** Help link */
  helpLink?: {
    label: string;
    url: string;
  };
  /** Container variant */
  variant?: 'card' | 'inline';
  /** Additional classes */
  className?: string;
}

/**
 * Default configurations by type
 */
const typeDefaults: Record<EmptyStateType, { 
  icon: React.ReactNode; 
  title: string; 
  description: string;
}> = {
  'no-data': {
    icon: <Package className="w-12 h-12" />,
    title: 'No Data Available',
    description: 'There\'s no data to display. Please check back later or try a different selection.'
  },
  'no-results': {
    icon: <Search className="w-12 h-12" />,
    title: 'No Results Found',
    description: 'We couldn\'t find any results matching your criteria. Try adjusting your filters.'
  },
  'no-analysis': {
    icon: <BarChart3 className="w-12 h-12" />,
    title: 'No Analysis Yet',
    description: 'Run a risk analysis from the Input page to see detailed results and recommendations.'
  },
  'no-comparison': {
    icon: <GitCompare className="w-12 h-12" />,
    title: 'No Comparison Selected',
    description: 'Select shipments or time periods to compare risk profiles side by side.'
  },
  'no-history': {
    icon: <History className="w-12 h-12" />,
    title: 'No Historical Data',
    description: 'Historical trends will appear here once more data points are available.'
  },
  'error': {
    icon: <FileQuestion className="w-12 h-12" />,
    title: 'Something Went Wrong',
    description: 'We encountered an error loading this content. Please try again.'
  },
  'custom': {
    icon: <Package className="w-12 h-12" />,
    title: 'No Content',
    description: 'Content will appear here.'
  }
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  type = 'no-data',
  icon,
  title,
  description,
  primaryAction,
  secondaryAction,
  helpLink,
  variant = 'card',
  className = ''
}) => {
  const defaults = typeDefaults[type];
  
  const displayIcon = icon || defaults.icon;
  const displayTitle = title || defaults.title;
  const displayDescription = description || defaults.description;

  const content = (
    <div className="flex flex-col items-center justify-center py-12 text-center max-w-md mx-auto">
      {/* Icon */}
      <div className="w-20 h-20 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-6 text-white/30">
        {displayIcon}
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold text-white mb-2">
        {displayTitle}
      </h3>

      {/* Description */}
      <p className="text-white/60 text-sm mb-6 leading-relaxed">
        {displayDescription}
      </p>

      {/* Actions */}
      {(primaryAction || secondaryAction) && (
        <div className="flex flex-col sm:flex-row items-center gap-3">
          {primaryAction && (
            primaryAction.href ? (
              <a
                href={primaryAction.href}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25"
              >
                {primaryAction.icon || <ArrowRight className="w-4 h-4" />}
                {primaryAction.label}
              </a>
            ) : (
              <button
                onClick={primaryAction.onClick}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25"
              >
                {primaryAction.icon || <ArrowRight className="w-4 h-4" />}
                {primaryAction.label}
              </button>
            )
          )}

          {secondaryAction && (
            secondaryAction.href ? (
              <a
                href={secondaryAction.href}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white rounded-xl font-medium transition-all"
              >
                {secondaryAction.icon}
                {secondaryAction.label}
              </a>
            ) : (
              <button
                onClick={secondaryAction.onClick}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white rounded-xl font-medium transition-all"
              >
                {secondaryAction.icon}
                {secondaryAction.label}
              </button>
            )
          )}
        </div>
      )}

      {/* Help Link */}
      {helpLink && (
        <a
          href={helpLink.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-6 inline-flex items-center gap-1.5 text-sm text-blue-400 hover:text-blue-300 transition-colors"
        >
          {helpLink.label}
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      )}
    </div>
  );

  if (variant === 'inline') {
    return <div className={className}>{content}</div>;
  }

  return (
    <GlassCard className={className}>
      {content}
    </GlassCard>
  );
};

/**
 * Pre-built empty states for common scenarios
 */
export const NoAnalysisState: React.FC<{ className?: string }> = ({ className }) => (
  <EmptyState
    type="no-analysis"
    primaryAction={{
      label: 'Start Analysis',
      href: '/input_v20'
    }}
    secondaryAction={{
      label: 'View Demo',
      href: '/demo'
    }}
    helpLink={{
      label: 'Learn about risk analysis',
      url: '/docs/risk-analysis'
    }}
    className={className}
  />
);

export const NoComparisonState: React.FC<{ onSelectShipments?: () => void; className?: string }> = ({ 
  onSelectShipments,
  className 
}) => (
  <EmptyState
    type="no-comparison"
    primaryAction={{
      label: 'Select Shipments',
      onClick: onSelectShipments
    }}
    className={className}
  />
);

export const NoHistoryState: React.FC<{ className?: string }> = ({ className }) => (
  <EmptyState
    type="no-history"
    description="Historical trend data will be available after multiple analyses are performed on this route or carrier."
    className={className}
  />
);

export default EmptyState;
