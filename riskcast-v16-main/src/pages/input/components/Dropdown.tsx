/**
 * Dropdown Component - Searchable select with keyboard navigation
 */

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Search, Check } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';

interface DropdownOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface DropdownProps {
  label?: string;
  placeholder?: string;
  value?: string;
  options: DropdownOption[];
  searchable?: boolean;
  required?: boolean;
  error?: string;
  helperText?: string;
  onChange?: (value: string) => void;
  icon?: React.ReactNode;
}

export const Dropdown: React.FC<DropdownProps> = ({
  label,
  placeholder = 'Select...',
  value,
  options,
  searchable = false,
  required = false,
  error,
  helperText,
  onChange,
  icon,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const selectedOption = options.find(opt => opt.value === value);
  const filteredOptions = searchable && searchQuery
    ? options.filter(opt => 
        opt.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;
  
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);
  
  const handleSelect = (optionValue: string) => {
    onChange?.(optionValue);
    setIsOpen(false);
    setSearchQuery('');
  };
  
  return (
    <div
      ref={dropdownRef}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: designTokens.spacing.sm,
        position: 'relative',
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
      
      <div style={{ position: 'relative' }}>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          style={{
            width: '100%',
            height: '48px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: designTokens.spacing.sm,
            padding: `0 ${designTokens.spacing.lg}`,
            backgroundColor: 'rgba(255, 255, 255, 0.04)',
            border: `1.5px solid ${error ? designTokens.colors.danger : isOpen ? designTokens.colors.primaryNeon : 'rgba(255, 255, 255, 0.08)'}`,
            borderRadius: designTokens.radii.lg,
            color: selectedOption ? designTokens.colors.textStrong : designTokens.colors.textMuted,
            fontSize: '15px',
            fontFamily: designTokens.typography.fontFamily,
            textAlign: 'left',
            cursor: 'pointer',
            transition: designTokens.transitions.normal,
            boxShadow: isOpen ? `0 0 0 3px rgba(110, 243, 255, 0.15)` : 'none',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: designTokens.spacing.sm, flex: 1 }}>
            {icon}
            <span>{selectedOption?.label || placeholder}</span>
          </div>
          <ChevronDown
            size={18}
            style={{
              transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: designTokens.transitions.normal,
            }}
          />
        </button>
        
        {isOpen && (
          <div
            style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              left: 0,
              right: 0,
              backgroundColor: designTokens.colors.bg1,
              backdropFilter: designTokens.blur.md,
              border: `1px solid rgba(255, 255, 255, 0.08)`,
              borderRadius: designTokens.radii.xl,
              boxShadow: designTokens.shadows.lg,
              zIndex: 1000,
              maxHeight: '320px',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {searchable && (
              <div
                style={{
                  padding: designTokens.spacing.md,
                  borderBottom: `1px solid rgba(255, 255, 255, 0.08)`,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: designTokens.spacing.sm,
                    padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: `1px solid rgba(255, 255, 255, 0.08)`,
                    borderRadius: designTokens.radii.md,
                  }}
                >
                  <Search size={16} style={{ color: designTokens.colors.textMuted }} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search..."
                    style={{
                      flex: 1,
                      background: 'transparent',
                      border: 'none',
                      outline: 'none',
                      fontSize: '14px',
                      color: designTokens.colors.textStrong,
                      fontFamily: designTokens.typography.fontFamily,
                    }}
                    autoFocus
                  />
                </div>
              </div>
            )}
            
            <div
              style={{
                overflowY: 'auto',
                padding: designTokens.spacing.sm,
              }}
            >
              {filteredOptions.length === 0 ? (
                <div
                  style={{
                    padding: designTokens.spacing.lg,
                    textAlign: 'center',
                    color: designTokens.colors.textMuted,
                    fontSize: '14px',
                    fontFamily: designTokens.typography.fontFamily,
                  }}
                >
                  No results found
                </div>
              ) : (
                filteredOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => !option.disabled && handleSelect(option.value)}
                    disabled={option.disabled}
                    style={{
                      width: '100%',
                      padding: `${designTokens.spacing.sm} ${designTokens.spacing.md}`,
                      backgroundColor: option.value === value ? 'rgba(110, 243, 255, 0.15)' : 'transparent',
                      border: 'none',
                      borderRadius: designTokens.radii.md,
                      color: option.value === value ? designTokens.colors.primaryNeon : designTokens.colors.textDefault,
                      fontSize: '15px',
                      fontFamily: designTokens.typography.fontFamily,
                      textAlign: 'left',
                      cursor: option.disabled ? 'not-allowed' : 'pointer',
                      opacity: option.disabled ? 0.5 : 1,
                      display: 'flex',
                      alignItems: 'center',
                      gap: designTokens.spacing.sm,
                      transition: designTokens.transitions.fast,
                    }}
                    onMouseEnter={(e) => {
                      if (!option.disabled && option.value !== value) {
                        e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (option.value !== value) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    {option.value === value && <Check size={16} />}
                    <span>{option.label}</span>
                  </button>
                ))
              )}
            </div>
          </div>
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
