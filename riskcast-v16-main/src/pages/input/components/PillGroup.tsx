/**
 * Pill Group Component - Radio button group with pill styling
 */

import React from 'react';
import { designTokens } from '@/ui/design-tokens';
import type { LucideIcon } from 'lucide-react';

interface PillOption {
  value: string;
  label: string;
  icon?: LucideIcon;
}

interface PillGroupProps {
  label?: string;
  options: PillOption[];
  value?: string;
  required?: boolean;
  error?: string;
  helperText?: string;
  onChange?: (value: string) => void;
}

export const PillGroup: React.FC<PillGroupProps> = ({
  label,
  options,
  value,
  required = false,
  error,
  helperText,
  onChange,
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
          display: 'flex',
          flexWrap: 'wrap',
          gap: designTokens.spacing.sm,
        }}
      >
        {options.map((option) => {
          const Icon = option.icon;
          const isSelected = value === option.value;
          
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onChange?.(option.value)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: designTokens.spacing.sm,
                padding: `${designTokens.spacing.md} ${designTokens.spacing['2xl']}`,
                height: '40px',
                backgroundColor: isSelected
                  ? `linear-gradient(135deg, rgba(110, 243, 255, 0.15), rgba(139, 123, 255, 0.15))`
                  : 'rgba(255, 255, 255, 0.04)',
                border: `1.5px solid ${isSelected ? designTokens.colors.primaryNeon : 'rgba(255, 255, 255, 0.08)'}`,
                borderRadius: designTokens.radii.md,
                color: isSelected ? designTokens.colors.primaryNeon : designTokens.colors.textMuted,
                fontSize: '15px',
                fontFamily: designTokens.typography.fontFamily,
                fontWeight: isSelected ? 600 : 500,
                cursor: 'pointer',
                transition: designTokens.transitions.normal,
                boxShadow: isSelected ? `0 0 20px rgba(110, 243, 255, 0.3)` : 'none',
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)';
                  e.currentTarget.style.borderColor = designTokens.colors.primaryNeon;
                  e.currentTarget.style.color = designTokens.colors.textDefault;
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.04)';
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                  e.currentTarget.style.color = designTokens.colors.textMuted;
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              {Icon && <Icon size={18} />}
              <span>{option.label}</span>
            </button>
          );
        })}
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
