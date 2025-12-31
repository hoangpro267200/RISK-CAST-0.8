import React from 'react';

interface ChartSkeletonProps {
  height?: number;
  className?: string;
}

/**
 * Lightweight skeleton placeholder for charts while container size is not ready.
 */
export const ChartSkeleton: React.FC<ChartSkeletonProps> = ({ 
  height = 400, 
  className = '' 
}) => {
  return (
    <div 
      className={`flex items-center justify-center ${className}`}
      style={{ height: `${height}px`, minHeight: `${height}px` }}
    >
      <div className="flex flex-col items-center gap-3 text-white/40">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
        <div className="text-xs">Loading chart...</div>
      </div>
    </div>
  );
};

