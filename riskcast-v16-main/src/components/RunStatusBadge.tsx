/**
 * Run Status Badge Component
 * Color-coded status badge for risk runs
 */
import React from 'react';

export type RunStatus = 'PENDING' | 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED';

interface RunStatusBadgeProps {
  status: RunStatus;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const RunStatusBadge: React.FC<RunStatusBadgeProps> = ({ 
  status, 
  size = 'md',
  className = '' 
}) => {
  const colorMap: Record<RunStatus, { bg: string; text: string; glow?: string }> = {
    PENDING: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', glow: 'shadow-yellow-500/50' },
    QUEUED: { bg: 'bg-blue-500/20', text: 'text-blue-400', glow: 'shadow-blue-500/50' },
    RUNNING: { bg: 'bg-blue-500/20', text: 'text-blue-400', glow: 'shadow-blue-500/50' },
    SUCCEEDED: { bg: 'bg-green-500/20', text: 'text-green-400', glow: 'shadow-green-500/50' },
    FAILED: { bg: 'bg-red-500/20', text: 'text-red-400', glow: 'shadow-red-500/50' },
    CANCELLED: { bg: 'bg-gray-500/20', text: 'text-gray-400', glow: 'shadow-gray-500/50' },
  };

  const sizeMap = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };

  const colors = colorMap[status];
  const sizeClass = sizeMap[size];

  return (
    <span 
      className={`inline-flex items-center rounded-full font-medium ${colors.bg} ${colors.text} ${sizeClass} ${className}`}
    >
      {status === 'RUNNING' && (
        <span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-current" />
      )}
      {status}
    </span>
  );
};
