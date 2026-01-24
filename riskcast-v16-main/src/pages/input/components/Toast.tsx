/**
 * Toast Notification Component
 */

import React, { useEffect } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
  onClose: (id: string) => void;
}

const icons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const colors = {
  success: designTokens.colors.success,
  error: designTokens.colors.danger,
  warning: designTokens.colors.warning,
  info: designTokens.colors.info,
};

export const Toast: React.FC<ToastProps> = ({
  id,
  type,
  message,
  duration = 5000,
  onClose,
}) => {
  const Icon = icons[type];
  const color = colors[type];
  
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose(id);
      }, duration);
      
      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);
  
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: designTokens.spacing.md,
        padding: `${designTokens.spacing.md} ${designTokens.spacing.lg}`,
        backgroundColor: designTokens.colors.bg1,
        backdropFilter: designTokens.blur.md,
        border: `1px solid ${color}40`,
        borderRadius: designTokens.radii.lg,
        boxShadow: designTokens.shadows.lg,
        minWidth: '300px',
        maxWidth: '400px',
        animation: 'slideIn 0.3s ease-out',
      }}
    >
      <Icon size={20} style={{ color, flexShrink: 0 }} />
      
      <div
        style={{
          flex: 1,
          fontSize: '14px',
          color: designTokens.colors.textDefault,
          fontFamily: designTokens.typography.fontFamily,
        }}
      >
        {message}
      </div>
      
      <button
        type="button"
        onClick={() => onClose(id)}
        style={{
          width: '24px',
          height: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'transparent',
          border: 'none',
          color: designTokens.colors.textMuted,
          cursor: 'pointer',
          borderRadius: designTokens.radii.sm,
          transition: designTokens.transitions.fast,
          flexShrink: 0,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = designTokens.colors.textDefault;
          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = designTokens.colors.textMuted;
          e.currentTarget.style.backgroundColor = 'transparent';
        }}
      >
        <X size={16} />
      </button>
      
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export const ToastContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div
      style={{
        position: 'fixed',
        top: '80px',
        right: '24px',
        zIndex: 10000,
        display: 'flex',
        flexDirection: 'column',
        gap: designTokens.spacing.md,
        pointerEvents: 'none',
      }}
    >
      <div style={{ pointerEvents: 'auto' }}>
        {children}
      </div>
    </div>
  );
};
