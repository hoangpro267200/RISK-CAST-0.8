/**
 * Validation Hook - Real-time field validation
 */

import { useState, useCallback, useEffect } from 'react';
import type { InputFormState } from './useFormState';

export interface ValidationError {
  field: string;
  section: keyof InputFormState;
  message: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

// Validation rules
const validationRules = {
  route: {
    tradeLane: (value: unknown) => {
      if (!value || String(value).trim() === '') {
        return 'Trade lane is required';
      }
      return null;
    },
    mode: (value: unknown) => {
      if (!value || String(value).trim() === '') {
        return 'Mode of transport is required';
      }
      return null;
    },
    pol: (value: unknown) => {
      if (!value || String(value).trim() === '') {
        return 'Origin port (POL) is required';
      }
      if (String(value).length < 3) {
        return 'Port code must be at least 3 characters';
      }
      return null;
    },
    pod: (value: unknown) => {
      if (!value || String(value).trim() === '') {
        return 'Destination port (POD) is required';
      }
      if (String(value).length < 3) {
        return 'Port code must be at least 3 characters';
      }
      return null;
    },
  },
  cargo: {
    type: (value: unknown) => {
      if (!value || String(value).trim() === '') {
        return 'Cargo type is required';
      }
      return null;
    },
    grossWeight: (value: unknown) => {
      if (value === undefined || value === null || value === '') {
        return 'Gross weight is required';
      }
      const num = Number(value);
      if (isNaN(num) || num <= 0) {
        return 'Gross weight must be greater than 0';
      }
      return null;
    },
    packages: (value: unknown) => {
      if (value === undefined || value === null || value === '') {
        return 'Number of packages is required';
      }
      const num = Number(value);
      if (isNaN(num) || num < 1) {
        return 'Number of packages must be at least 1';
      }
      return null;
    },
  },
  value: {
    insuranceValue: (value: unknown) => {
      if (value === undefined || value === null || value === '') {
        return 'Insurance value is required';
      }
      const num = Number(value);
      if (isNaN(num) || num < 0) {
        return 'Insurance value must be 0 or greater';
      }
      return null;
    },
  },
  parties: {
    seller: {
      company: (value: unknown) => {
        if (!value || String(value).trim() === '') {
          return 'Seller company name is required';
        }
        return null;
      },
      country: (value: unknown) => {
        if (!value || String(value).trim() === '') {
          return 'Seller country is required';
        }
        return null;
      },
    },
    buyer: {
      company: (value: unknown) => {
        if (!value || String(value).trim() === '') {
          return 'Buyer company name is required';
        }
        return null;
      },
      country: (value: unknown) => {
        if (!value || String(value).trim() === '') {
          return 'Buyer country is required';
        }
        return null;
      },
    },
  },
};

export function useValidation(formState: InputFormState) {
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [touchedFields, setTouchedFields] = useState<Set<string>>(new Set());
  
  // Validate a single field
  const validateField = useCallback((
    section: keyof InputFormState,
    field: string,
    value: unknown
  ): string | null => {
    const sectionRules = validationRules[section as keyof typeof validationRules];
    if (!sectionRules) return null;
    
    // Handle nested fields (e.g., parties.seller.company)
    if (section === 'parties' && field.includes('.')) {
      const [partyType, partyField] = field.split('.');
    if (!partyType || !partyField) return null;
    const partyRules = (sectionRules as Record<string, Record<string, (v: unknown) => string | null>>)[partyType];
    if (partyRules && partyRules[partyField]) {
      return partyRules[partyField](value);
      }
      return null;
    }
    
    const rule = (sectionRules as Record<string, (value: unknown) => string | null>)[field];
    if (rule) {
      return rule(value);
    }
    
    return null;
  }, []);
  
  // Validate entire form
  const validateForm = useCallback((): ValidationResult => {
    const newErrors: ValidationError[] = [];
    
    // Validate route section
    if (formState.route) {
      Object.entries(formState.route).forEach(([field, value]) => {
        const error = validateField('route', field, value);
        if (error) {
          newErrors.push({ section: 'route', field, message: error });
        }
      });
    }
    
    // Validate cargo section
    if (formState.cargo) {
      Object.entries(formState.cargo).forEach(([field, value]) => {
        const error = validateField('cargo', field, value);
        if (error) {
          newErrors.push({ section: 'cargo', field, message: error });
        }
      });
    }
    
    // Validate value section
    if (formState.value) {
      Object.entries(formState.value).forEach(([field, value]) => {
        const error = validateField('value', field, value);
        if (error) {
          newErrors.push({ section: 'value', field, message: error });
        }
      });
    }
    
    // Validate parties section
    if (formState.parties) {
      if (formState.parties.seller) {
        Object.entries(formState.parties.seller).forEach(([field, value]) => {
          const error = validateField('parties', `seller.${field}`, value);
          if (error) {
            newErrors.push({ section: 'parties', field: `seller.${field}`, message: error });
          }
        });
      }
      
      if (formState.parties.buyer) {
        Object.entries(formState.parties.buyer).forEach(([field, value]) => {
          const error = validateField('parties', `buyer.${field}`, value);
          if (error) {
            newErrors.push({ section: 'parties', field: `buyer.${field}`, message: error });
          }
        });
      }
    }
    
    setErrors(newErrors);
    return {
      isValid: newErrors.length === 0,
      errors: newErrors,
    };
  }, [formState, validateField]);
  
  // Mark field as touched
  const markFieldTouched = useCallback((section: keyof InputFormState, field: string) => {
    setTouchedFields(prev => new Set(prev).add(`${section}.${field}`));
  }, []);
  
  // Get error for a specific field
  const getFieldError = useCallback((
    section: keyof InputFormState,
    field: string
  ): string | null => {
    const fieldKey = `${section}.${field}`;
    const isTouched = touchedFields.has(fieldKey);
    
    if (!isTouched) return null;
    
    const error = errors.find(
      e => e.section === section && e.field === field
    );
    
    return error?.message || null;
  }, [errors, touchedFields]);
  
  // Validate on form state change (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      validateForm();
    }, 300);
    
    return () => clearTimeout(timer);
  }, [formState, validateForm]);
  
  return {
    errors,
    validateForm,
    validateField,
    markFieldTouched,
    getFieldError,
    isValid: errors.length === 0,
  };
}
