/**
 * Autosuggest Component - POL/POD port search with debounce
 */

import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2, MapPin } from 'lucide-react';
import { designTokens } from '@/ui/design-tokens';

interface PortOption {
  code: string;
  name: string;
  city?: string;
  country?: string;
}

interface AutosuggestProps {
  label?: string;
  placeholder?: string;
  value?: string;
  required?: boolean;
  error?: string;
  helperText?: string;
  onChange?: (value: string) => void;
  onSelect?: (option: PortOption) => void;
  searchFunction?: (query: string) => Promise<PortOption[]>;
  debounceMs?: number;
  minChars?: number;
  maxSuggestions?: number;
}

// Mock port search function - should be replaced with actual API
const mockPortSearch = async (query: string): Promise<PortOption[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 300));
  
  const ports: PortOption[] = [
    { code: 'SGN', name: 'Ho Chi Minh', city: 'Ho Chi Minh', country: 'Vietnam' },
    { code: 'VNSGN', name: 'Ho Chi Minh (Full)', city: 'Ho Chi Minh', country: 'Vietnam' },
    { code: 'SHA', name: 'Shanghai', city: 'Shanghai', country: 'China' },
    { code: 'CNSHA', name: 'Shanghai (Full)', city: 'Shanghai', country: 'China' },
    { code: 'LAX', name: 'Los Angeles', city: 'Los Angeles', country: 'USA' },
    { code: 'USLAX', name: 'Los Angeles (Full)', city: 'Los Angeles', country: 'USA' },
    { code: 'ROT', name: 'Rotterdam', city: 'Rotterdam', country: 'Netherlands' },
    { code: 'NLROT', name: 'Rotterdam (Full)', city: 'Rotterdam', country: 'Netherlands' },
  ];
  
  const lowerQuery = query.toLowerCase();
  return ports.filter(port => 
    port.code.toLowerCase().includes(lowerQuery) ||
    port.name.toLowerCase().includes(lowerQuery) ||
    port.city?.toLowerCase().includes(lowerQuery)
  ).slice(0, 8);
};

export const Autosuggest: React.FC<AutosuggestProps> = ({
  label,
  placeholder = 'Type to search...',
  value,
  required = false,
  error,
  helperText,
  onChange,
  onSelect,
  searchFunction = mockPortSearch,
  debounceMs = 300,
  minChars = 2,
  maxSuggestions = 8,
}) => {
  const [query, setQuery] = useState(value || '');
  const [suggestions, setSuggestions] = useState<PortOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [selectedOption, setSelectedOption] = useState<PortOption | null>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Search function with debounce
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    
    if (query.length < minChars) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true);
    
    debounceTimer.current = setTimeout(async () => {
      try {
        const results = await searchFunction(query);
        setSuggestions(results.slice(0, maxSuggestions));
      } catch (err) {
        console.error('Autosuggest search error:', err);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }, debounceMs);
    
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query, searchFunction, debounceMs, minChars, maxSuggestions]);
  
  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setQuery(newValue);
    setIsOpen(true);
    setSelectedIndex(-1);
    onChange?.(newValue);
  };
  
  // Handle option select
  const handleSelect = (option: PortOption) => {
    setQuery(option.code);
    setSelectedOption(option);
    setIsOpen(false);
    onChange?.(option.code);
    onSelect?.(option);
  };
  
  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || suggestions.length === 0) return;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && suggestions[selectedIndex]) {
          handleSelect(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };
  
  // Highlight matching text
  const highlightText = (text: string, query: string) => {
    if (!query) return text;
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, i) => 
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i} style={{ backgroundColor: 'rgba(110, 243, 255, 0.3)', color: designTokens.colors.primaryNeon }}>
          {part}
        </mark>
      ) : part
    );
  };
  
  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    };
    
    const handleCloseAutosuggest = () => {
      setIsOpen(false);
      setSelectedIndex(-1);
    };
    
    if (isOpen) {
      dropdownRef.current?.setAttribute('data-autosuggest-open', 'true');
      document.addEventListener('mousedown', handleClickOutside);
      dropdownRef.current?.addEventListener('closeAutosuggest', handleCloseAutosuggest);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        dropdownRef.current?.removeEventListener('closeAutosuggest', handleCloseAutosuggest);
        dropdownRef.current?.setAttribute('data-autosuggest-open', 'false');
      };
    }
  }, [isOpen]);
  
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
        <div
          style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            height: '48px',
            backgroundColor: 'rgba(255, 255, 255, 0.04)',
            border: `1.5px solid ${error ? designTokens.colors.danger : isOpen ? designTokens.colors.primaryNeon : 'rgba(255, 255, 255, 0.08)'}`,
            borderRadius: designTokens.radii.lg,
            padding: `0 ${designTokens.spacing.lg}`,
            transition: designTokens.transitions.normal,
            boxShadow: isOpen ? `0 0 0 3px rgba(110, 243, 255, 0.15)` : 'none',
          }}
        >
          <Search
            size={20}
            style={{
              color: designTokens.colors.textMuted,
              marginRight: designTokens.spacing.sm,
              flexShrink: 0,
            }}
          />
          
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsOpen(true)}
            placeholder={placeholder}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              padding: `${designTokens.spacing.md} 0`,
              fontFamily: designTokens.typography.fontFamily,
              fontSize: '15px',
              color: designTokens.colors.textStrong,
            }}
          />
          
          {isLoading && (
            <Loader2
              size={18}
              style={{
                color: designTokens.colors.primaryNeon,
                animation: 'spin 1s linear infinite',
                marginLeft: designTokens.spacing.sm,
              }}
            />
          )}
        </div>
        
        {/* Dropdown */}
        {isOpen && (suggestions.length > 0 || isLoading) && (
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
              overflowY: 'auto',
            }}
          >
            {isLoading ? (
              <div
                style={{
                  padding: designTokens.spacing.lg,
                  textAlign: 'center',
                  color: designTokens.colors.textMuted,
                  fontSize: '14px',
                  fontFamily: designTokens.typography.fontFamily,
                }}
              >
                Searching...
              </div>
            ) : suggestions.length === 0 ? (
              <div
                style={{
                  padding: designTokens.spacing.lg,
                  textAlign: 'center',
                  color: designTokens.colors.textMuted,
                  fontSize: '14px',
                  fontFamily: designTokens.typography.fontFamily,
                }}
              >
                No ports found. Try a different search.
              </div>
            ) : (
              <div ref={suggestionsRef}>
                {suggestions.map((option, index) => {
                  const isKeyboardSelected = index === selectedIndex;
                  
                  return (
                    <button
                      key={`${option.code}-${index}`}
                      type="button"
                      onClick={() => handleSelect(option)}
                      style={{
                        width: '100%',
                        padding: `${designTokens.spacing.md} ${designTokens.spacing.lg}`,
                        backgroundColor: isKeyboardSelected ? 'rgba(110, 243, 255, 0.15)' : 'transparent',
                        border: 'none',
                        borderRadius: designTokens.radii.md,
                        color: isKeyboardSelected ? designTokens.colors.primaryNeon : designTokens.colors.textDefault,
                        fontSize: '15px',
                        fontFamily: designTokens.typography.fontFamily,
                        textAlign: 'left',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: designTokens.spacing.md,
                        transition: designTokens.transitions.fast,
                      }}
                      onMouseEnter={() => setSelectedIndex(index)}
                    >
                      <MapPin size={16} style={{ color: designTokens.colors.textMuted, flexShrink: 0 }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, marginBottom: designTokens.spacing.xs }}>
                          {highlightText(option.code, query)}
                        </div>
                        <div style={{ fontSize: '13px', color: designTokens.colors.textMuted }}>
                          {option.name}
                          {option.city && `, ${option.city}`}
                          {option.country && ` • ${option.country}`}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
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
      
      {selectedOption && (
        <div
          style={{
            fontSize: '12px',
            color: designTokens.colors.textMuted,
            fontFamily: designTokens.typography.fontFamily,
            display: 'flex',
            alignItems: 'center',
            gap: designTokens.spacing.xs,
          }}
        >
          <MapPin size={14} />
          Selected: {selectedOption.name} ({selectedOption.code})
        </div>
      )}
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
