/**
 * DatePicker Component - Custom date picker (not browser default)
 */

import React, { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';

interface DatePickerProps {
  label?: string;
  value?: string; // ISO format: YYYY-MM-DD
  required?: boolean;
  error?: string;
  helperText?: string;
  minDate?: string; // ISO format
  maxDate?: string; // ISO format
  onChange?: (value: string) => void;
  formatDisplay?: (date: Date) => string;
}

const formatDateDisplay = (date: Date): string => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const day = date.getDate();
  const month = months[date.getMonth()];
  const year = date.getFullYear();
  return `${day} ${month} ${year}`;
};

export const DatePicker: React.FC<DatePickerProps> = ({
  label,
  value,
  required = false,
  error,
  helperText,
  minDate,
  maxDate,
  onChange,
  formatDisplay = formatDateDisplay,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(
    value ? new Date(value) : null
  );
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Parse dates
  const min = minDate ? new Date(minDate) : null;
  const max = maxDate ? new Date(maxDate) : null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  // Get days in month
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    const days: (Date | null)[] = [];
    
    // Empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    
    // Days in month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }
    
    return days;
  };
  
  const days = getDaysInMonth(currentMonth);
  
  // Navigate months
  const goToPreviousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };
  
  const goToNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };
  
  // Handle date select
  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
    const isoString = date.toISOString().split('T')[0] ?? '';
    onChange?.(isoString);
    setIsOpen(false);
  };
  
  // Check if date is disabled
  const isDateDisabled = (date: Date | null): boolean => {
    if (!date) return true;
    if (min && date < min) return true;
    if (max && date > max) return true;
    return false;
  };
  
  // Check if date is today
  const isToday = (date: Date | null): boolean => {
    if (!date) return false;
    return date.toDateString() === today.toDateString();
  };
  
  // Check if date is selected
  const isSelected = (date: Date | null): boolean => {
    if (!date || !selectedDate) return false;
    return date.toDateString() === selectedDate.toDateString();
  };
  
  // Close on outside click
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
  
  // Update selected date when value prop changes
  useEffect(() => {
    if (value) {
      setSelectedDate(new Date(value));
    }
  }, [value]);
  
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  
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
            color: selectedDate ? designTokens.colors.textStrong : designTokens.colors.textMuted,
            fontSize: '15px',
            fontFamily: designTokens.typography.fontFamily,
            textAlign: 'left',
            cursor: 'pointer',
            transition: designTokens.transitions.normal,
            boxShadow: isOpen ? `0 0 0 3px rgba(110, 243, 255, 0.15)` : 'none',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: designTokens.spacing.sm, flex: 1 }}>
            <Calendar size={20} style={{ color: designTokens.colors.textMuted }} />
            <span>{selectedDate ? formatDisplay(selectedDate) : 'Select date'}</span>
          </div>
        </button>
        
        {isOpen && (
          <div
            style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              left: 0,
              width: '320px',
              backgroundColor: designTokens.colors.bg1,
              backdropFilter: designTokens.blur.md,
              border: `1px solid rgba(255, 255, 255, 0.08)`,
              borderRadius: designTokens.radii.xl,
              boxShadow: designTokens.shadows.lg,
              zIndex: 1000,
              padding: designTokens.spacing.lg,
            }}
          >
            {/* Month Navigation */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: designTokens.spacing.lg,
              }}
            >
              <button
                type="button"
                onClick={goToPreviousMonth}
                style={{
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: designTokens.colors.textDefault,
                  cursor: 'pointer',
                  borderRadius: designTokens.radii.md,
                  transition: designTokens.transitions.fast,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <ChevronLeft size={18} />
              </button>
              
              <div
                style={{
                  fontSize: '16px',
                  fontWeight: 600,
                  color: designTokens.colors.textStrong,
                  fontFamily: designTokens.typography.fontFamily,
                }}
              >
                {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
              </div>
              
              <button
                type="button"
                onClick={goToNextMonth}
                style={{
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: designTokens.colors.textDefault,
                  cursor: 'pointer',
                  borderRadius: designTokens.radii.md,
                  transition: designTokens.transitions.fast,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <ChevronRight size={18} />
              </button>
            </div>
            
            {/* Day Names Header */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(7, 1fr)',
                gap: designTokens.spacing.xs,
                marginBottom: designTokens.spacing.sm,
              }}
            >
              {dayNames.map(day => (
                <div
                  key={day}
                  style={{
                    textAlign: 'center',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: designTokens.colors.textMuted,
                    fontFamily: designTokens.typography.fontFamily,
                    padding: designTokens.spacing.xs,
                  }}
                >
                  {day}
                </div>
              ))}
            </div>
            
            {/* Calendar Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(7, 1fr)',
                gap: designTokens.spacing.xs,
              }}
            >
              {days.map((date, index) => {
                const disabled = isDateDisabled(date);
                const isTodayDate = isToday(date);
                const isSelectedDate = isSelected(date);
                
                if (!date) {
                  return <div key={`empty-${index}`} />;
                }
                
                return (
                  <button
                    key={date.toISOString()}
                    type="button"
                    onClick={() => !disabled && handleDateSelect(date)}
                    disabled={disabled}
                    style={{
                      width: '36px',
                      height: '36px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: isSelectedDate
                        ? designTokens.colors.primaryNeon
                        : isTodayDate
                        ? 'rgba(110, 243, 255, 0.1)'
                        : 'transparent',
                      border: isTodayDate && !isSelectedDate
                        ? `2px solid ${designTokens.colors.primaryNeon}`
                        : 'none',
                      borderRadius: designTokens.radii.md,
                      color: disabled
                        ? designTokens.colors.textDisabled
                        : isSelectedDate
                        ? designTokens.colors.bg0
                        : designTokens.colors.textDefault,
                      fontSize: '14px',
                      fontFamily: designTokens.typography.fontFamily,
                      fontWeight: isSelectedDate ? 600 : 400,
                      cursor: disabled ? 'not-allowed' : 'pointer',
                      opacity: disabled ? 0.4 : 1,
                      transition: designTokens.transitions.fast,
                    }}
                    onMouseEnter={(e) => {
                      if (!disabled && !isSelectedDate) {
                        e.currentTarget.style.backgroundColor = 'rgba(110, 243, 255, 0.15)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelectedDate) {
                        e.currentTarget.style.backgroundColor = isTodayDate ? 'rgba(110, 243, 255, 0.1)' : 'transparent';
                      }
                    }}
                  >
                    {date.getDate()}
                  </button>
                );
              })}
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
