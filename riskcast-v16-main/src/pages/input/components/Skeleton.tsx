/**
 * Skeleton Loading Component
 */

import React from 'react';
import { designTokens } from '@/ui/design-tokens';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '20px',
  borderRadius = designTokens.radii.md,
  className,
  style,
}) => {
  return (
    <div
      className={className}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        borderRadius,
        background: 'linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s ease-in-out infinite',
        ...style,
      }}
    >
      <style>{`
        @keyframes shimmer {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }
      `}</style>
    </div>
  );
};

export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div
      className={className}
      style={{
        padding: designTokens.spacing['2xl'],
        backgroundColor: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: designTokens.radii['2xl'],
        display: 'flex',
        flexDirection: 'column',
        gap: designTokens.spacing.lg,
      }}
    >
      <Skeleton width="60%" height="24px" />
      <Skeleton width="100%" height="16px" />
      <Skeleton width="80%" height="16px" />
      <div style={{ display: 'flex', gap: designTokens.spacing.sm, marginTop: designTokens.spacing.md }}>
        <Skeleton width="100px" height="32px" borderRadius={designTokens.radii.md} />
        <Skeleton width="100px" height="32px" borderRadius={designTokens.radii.md} />
      </div>
    </div>
  );
};
