/**
 * Input Component - Text input with icon and unit support
 */

import React from 'react';
import { designTokens } from '@/ui/design-tokens';
import type { LucideIcon } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  icon?: LucideIcon;
  unit?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  icon: Icon,
  unit,
  error,
  helperText,
  required,
  className,
  style,
  ...props
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: designTokens.spacing.sm,
      }}
    >
      {label && (
        <label
          style={{
            fontSize: '13px',
            fontWeight: 600,
            color: error ? designTokens.colors.danger : designTokens.colors.textStrong,
            fontFamily: designTokens.typography.fontFamily,
          }}
        >
          {label}
          {required && (
            <span style={{ color: designTokens.colors.danger, marginLeft: '4px' }}>*</span>
          )}
        </label>
      )}
      
      <div
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          height: '48px',
          backgroundColor: 'rgba(255, 255, 255, 0.04)',
          border: `1.5px solid ${error ? designTokens.colors.danger : 'rgba(255, 255, 255, 0.08)'}`,
          borderRadius: designTokens.radii.lg,
          padding: `0 ${designTokens.spacing.lg}`,
          transition: designTokens.transitions.normal,
          ...(props.disabled && {
            opacity: 0.5,
            cursor: 'not-allowed',
          }),
        }}
        className={className}
      >
        {Icon && (
          <Icon
            size={20}
            style={{
              color: designTokens.colors.textMuted,
              marginRight: designTokens.spacing.sm,
              flexShrink: 0,
            }}
          />
        )}
        
        <input
          {...props}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            padding: `${designTokens.spacing.md} 0`,
            fontFamily: designTokens.typography.fontFamily,
            fontSize: '15px',
            color: designTokens.colors.textStrong,
            ...style,
          }}
        />
        
        {unit && (
          <span
            style={{
              fontSize: '13px',
              color: designTokens.colors.textMuted,
              marginLeft: designTokens.spacing.sm,
            }}
          >
            {unit}
          </span>
        )}
      </div>
      
      {(error || helperText) && (
        <span
          style={{
            fontSize: '13px',
            color: error ? designTokens.colors.danger : designTokens.colors.textMuted,
            fontFamily: designTokens.typography.fontFamily,
          }}
        >
          {error || helperText}
        </span>
      )}
    </div>
  );
};
