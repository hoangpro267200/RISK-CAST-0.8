/**
 * Toggle Switch Component
 */

import React from 'react';
import { designTokens } from '@/ui/design-tokens';

interface ToggleProps {
  label?: string;
  checked?: boolean;
  disabled?: boolean;
  onChange?: (checked: boolean) => void;
  size?: 'sm' | 'md' | 'lg';
}

export const Toggle: React.FC<ToggleProps> = ({
  label,
  checked = false,
  disabled = false,
  onChange,
  size = 'md',
}) => {
  const sizeMap = {
    sm: { track: '36px', thumb: '16px' },
    md: { track: '48px', thumb: '20px' },
    lg: { track: '56px', thumb: '24px' },
  };
  
  const dimensions = sizeMap[size];
  
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: designTokens.spacing.md,
      }}
    >
      {label && (
        <label
          style={{
            fontSize: '15px',
            color: disabled ? designTokens.colors.textDisabled : designTokens.colors.textDefault,
            fontFamily: designTokens.typography.fontFamily,
            cursor: disabled ? 'not-allowed' : 'pointer',
            userSelect: 'none',
          }}
          onClick={() => !disabled && onChange?.(!checked)}
        >
          {label}
        </label>
      )}
      
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange?.(!checked)}
        style={{
          position: 'relative',
          width: dimensions.track,
          height: `${parseInt(dimensions.thumb) + 8}px`,
          backgroundColor: checked
            ? designTokens.colors.primaryNeon
            : 'rgba(255, 255, 255, 0.1)',
          border: 'none',
          borderRadius: '9999px',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.4 : 1,
          transition: designTokens.transitions.normal,
          padding: '4px',
          display: 'flex',
          alignItems: 'center',
        }}
        onMouseEnter={(e) => {
          if (!disabled) {
            e.currentTarget.style.opacity = '0.8';
          }
        }}
        onMouseLeave={(e) => {
          if (!disabled) {
            e.currentTarget.style.opacity = '1';
          }
        }}
      >
        <div
          style={{
            width: dimensions.thumb,
            height: dimensions.thumb,
            backgroundColor: 'white',
            borderRadius: '50%',
            transform: checked ? `translateX(calc(${dimensions.track} - ${dimensions.thumb} - 8px))` : 'translateX(0)',
            transition: `transform ${designTokens.transitions.normal}`,
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
          }}
        />
      </button>
    </div>
  );
};
