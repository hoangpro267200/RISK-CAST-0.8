/**
 * Completeness Hook - Calculates form completion percentage
 */

import { useMemo } from 'react';
import type { InputFormState } from './useFormState';

interface CompletenessResult {
  completeness: number; // 0-100
  completedFields: string[];
  missingFields: string[];
  requiredFieldsCount: number;
}

const REQUIRED_FIELDS = [
  { section: 'route', field: 'tradeLane', label: 'Trade Lane' },
  { section: 'route', field: 'mode', label: 'Mode of Transport' },
  { section: 'route', field: 'shipmentType', label: 'Shipment Type' },
  { section: 'route', field: 'serviceRoute', label: 'Service Route' },
  { section: 'route', field: 'pol', label: 'Origin Port (POL)' },
  { section: 'route', field: 'pod', label: 'Destination Port (POD)' },
  { section: 'cargo', field: 'type', label: 'Cargo Type' },
  { section: 'cargo', field: 'packingType', label: 'Packing Type' },
  { section: 'cargo', field: 'grossWeight', label: 'Gross Weight' },
  { section: 'value', field: 'insuranceValue', label: 'Insurance Value' },
  { section: 'parties', field: 'seller.company', label: 'Seller Company' },
  { section: 'parties', field: 'seller.country', label: 'Seller Country' },
  { section: 'parties', field: 'buyer.company', label: 'Buyer Company' },
  { section: 'parties', field: 'buyer.country', label: 'Buyer Country' },
];

export function useCompleteness(formState: InputFormState): CompletenessResult {
  return useMemo(() => {
    const completed: string[] = [];
    const missing: string[] = [];
    
    REQUIRED_FIELDS.forEach(({ section, field, label }) => {
      const sectionData = formState[section as keyof InputFormState];
      
      if (!sectionData) {
        missing.push(label);
        return;
      }
      
      // Handle nested fields (e.g., seller.company)
      if (field.includes('.')) {
        const [parent, child] = field.split('.');
        if (!parent || !child) {
          missing.push(label);
          return;
        }
        const parentData = (sectionData as Record<string, unknown>)[parent] as Record<string, unknown> | undefined;
        if (!parentData) {
          missing.push(label);
          return;
        }
        const value = parentData[child];
        
        if (value && String(value).trim() !== '') {
          completed.push(label);
        } else {
          missing.push(label);
        }
      } else {
        const value = (sectionData as Record<string, unknown>)[field];
        
        // Check if value exists and is not empty
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          // Special check for numbers (must be > 0)
          if (typeof value === 'number') {
            if (value > 0) {
              completed.push(label);
            } else {
              missing.push(label);
            }
          } else {
            completed.push(label);
          }
        } else {
          missing.push(label);
        }
      }
    });
    
    const total = REQUIRED_FIELDS.length;
    const completedCount = completed.length;
    const completeness = Math.round((completedCount / total) * 100);
    
    return {
      completeness,
      completedFields: completed,
      missingFields: missing,
      requiredFieldsCount: total,
    };
  }, [formState]);
}
