/**
 * ActivityFeed Component
 * 
 * Enterprise audit trail UI for tracking analysis events.
 * - Shows events like "Analysis run", "Threshold changed"
 * - Supports filtering by event type
 * - Ready for backend integration
 */

import React from 'react';
import { 
  Activity, 
  BarChart3, 
  Settings, 
  Download, 
  Eye,
  User,
  ChevronRight
} from 'lucide-react';
import { GlassCard } from '../GlassCard';

export type ActivityEventType = 
  | 'analysis_run'
  | 'threshold_changed'
  | 'export_generated'
  | 'view_changed'
  | 'comment_added'
  | 'alert_triggered'
  | 'custom';

export interface ActivityEvent {
  id: string;
  type: ActivityEventType;
  title: string;
  description?: string;
  timestamp: string;
  user?: {
    name: string;
    email?: string;
    avatar?: string;
  };
  metadata?: Record<string, unknown>;
}

export interface ActivityFeedProps {
  /** List of activity events */
  events: ActivityEvent[];
  /** Show loading state */
  isLoading?: boolean;
  /** Max events to display */
  maxEvents?: number;
  /** Callback when event is clicked */
  onEventClick?: (event: ActivityEvent) => void;
  /** Callback to load more events */
  onLoadMore?: () => void;
  /** Whether there are more events to load */
  hasMore?: boolean;
  /** Empty state message */
  emptyMessage?: string;
  /** Additional classes */
  className?: string;
}

/**
 * Get icon for event type
 */
function getEventIcon(type: ActivityEventType) {
  switch (type) {
    case 'analysis_run':
      return <BarChart3 className="w-4 h-4" />;
    case 'threshold_changed':
      return <Settings className="w-4 h-4" />;
    case 'export_generated':
      return <Download className="w-4 h-4" />;
    case 'view_changed':
      return <Eye className="w-4 h-4" />;
    case 'comment_added':
      return <User className="w-4 h-4" />;
    case 'alert_triggered':
      return <Activity className="w-4 h-4" />;
    default:
      return <Activity className="w-4 h-4" />;
  }
}

/**
 * Get color for event type
 */
function getEventColor(type: ActivityEventType) {
  switch (type) {
    case 'analysis_run':
      return 'bg-blue-500/20 text-blue-400';
    case 'threshold_changed':
      return 'bg-amber-500/20 text-amber-400';
    case 'export_generated':
      return 'bg-green-500/20 text-green-400';
    case 'view_changed':
      return 'bg-purple-500/20 text-purple-400';
    case 'comment_added':
      return 'bg-cyan-500/20 text-cyan-400';
    case 'alert_triggered':
      return 'bg-red-500/20 text-red-400';
    default:
      return 'bg-white/20 text-white/60';
  }
}

/**
 * Format relative time
 */
function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  events,
  isLoading = false,
  maxEvents = 10,
  onEventClick,
  onLoadMore,
  hasMore = false,
  emptyMessage = 'No activity yet',
  className = ''
}) => {
  const displayEvents = events.slice(0, maxEvents);

  return (
    <GlassCard className={className}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-400" />
          Activity
        </h3>
        {events.length > 0 && (
          <span className="text-xs text-white/50">
            {events.length} event{events.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start gap-3 p-3 bg-white/5 rounded-lg animate-pulse">
              <div className="w-8 h-8 rounded-lg bg-white/10" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-32 bg-white/10 rounded" />
                <div className="h-3 w-48 bg-white/10 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mx-auto mb-3">
            <Activity className="w-6 h-6 text-white/30" />
          </div>
          <p className="text-white/50 text-sm">{emptyMessage}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {displayEvents.map((event) => (
            <button
              key={event.id}
              onClick={() => onEventClick?.(event)}
              className="w-full flex items-start gap-3 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors text-left group"
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${getEventColor(event.type)}`}>
                {getEventIcon(event.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-white truncate">{event.title}</p>
                  <span className="text-xs text-white/40 flex-shrink-0">
                    {formatRelativeTime(event.timestamp)}
                  </span>
                </div>
                {event.description && (
                  <p className="text-xs text-white/50 truncate mt-0.5">{event.description}</p>
                )}
                {event.user && (
                  <div className="flex items-center gap-1 mt-1">
                    <User className="w-3 h-3 text-white/40" />
                    <span className="text-xs text-white/40">{event.user.name}</span>
                  </div>
                )}
              </div>
              <ChevronRight className="w-4 h-4 text-white/30 group-hover:text-white/60 transition-colors flex-shrink-0" />
            </button>
          ))}

          {hasMore && onLoadMore && (
            <button
              onClick={onLoadMore}
              className="w-full py-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              Load more activity
            </button>
          )}
        </div>
      )}
    </GlassCard>
  );
};

export default ActivityFeed;
