/**
 * Loading Overlay Component - Full page or section overlay
 */

import React from 'react';
import { Loader2 } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';

interface LoadingOverlayProps {
  message?: string;
  fullPage?: boolean;
  transparent?: boolean;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  message = 'Loading...',
  fullPage = false,
  transparent = false,
}) => {
  return (
    <div
      style={{
        position: fullPage ? 'fixed' : 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: transparent ? 'rgba(5, 7, 13, 0.7)' : designTokens.colors.bg0,
        backdropFilter: 'blur(8px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: designTokens.spacing.lg,
        zIndex: 10000,
      }}
    >
      <Loader2
        size={48}
        style={{
          color: designTokens.colors.primaryNeon,
          animation: 'spin 1s linear infinite',
        }}
      />
      <p
        style={{
          fontSize: '16px',
          color: designTokens.colors.textDefault,
          fontFamily: designTokens.typography.fontFamily,
        }}
      >
        {message}
      </p>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
