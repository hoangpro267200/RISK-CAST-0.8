/**
 * Form State Hook - Manages form state with autosave support
 */

import { useState, useCallback } from 'react';

export interface InputFormState {
  route?: {
    tradeLane?: string;
    mode?: string;
    shipmentType?: string;
    serviceRoute?: string;
    carrier?: string;
    containerType?: string;
    priority?: string;
    pol?: string;
    pod?: string;
  };
  schedule?: {
    etd?: string;
    transitDays?: number;
    eta?: string;
    scheduleFrequency?: string;
    reliabilityScore?: number;
  };
  cargo?: {
    type?: string;
    hsCode?: string;
    packingType?: string;
    packages?: number;
    grossWeight?: number;
    netWeight?: number;
    volume?: number;
    stackable?: boolean;
    sensitivity?: string;
    tempMin?: number;
    tempMax?: number;
    dangerousGoods?: boolean;
    dgUnNumber?: string;
    dgClass?: string;
    dgPackingGroup?: string;
    loadabilityIssues?: boolean;
    description?: string;
    specialHandling?: string;
  };
  value?: {
    insuranceValue?: number;
    insuranceCoverage?: string;
    incoterm?: string;
    incotermLocation?: string;
    currency?: string;
  };
  parties?: {
    seller?: {
      company?: string;
      country?: string;
      city?: string;
      address?: string;
      contact?: string;
      contactRole?: string;
      email?: string;
      phone?: string;
      businessType?: string;
      taxId?: string;
    };
    buyer?: {
      company?: string;
      country?: string;
      city?: string;
      address?: string;
      contact?: string;
      contactRole?: string;
      email?: string;
      phone?: string;
      businessType?: string;
      taxId?: string;
    };
  };
  modules?: {
    esg?: boolean;
    weather?: boolean;
    portCongestion?: boolean;
    carrier?: boolean;
    market?: boolean;
    insurance?: boolean;
  };
  upload?: {
    file?: File | null;
  };
}

const defaultFormState: InputFormState = {
  route: {
    priority: 'balanced',
  },
  cargo: {
    stackable: true,
    sensitivity: 'standard',
    dangerousGoods: false,
  },
  modules: {
    esg: true,
    weather: true,
    portCongestion: true,
    carrier: true,
    market: true,
    insurance: true,
  },
};

export function useFormState() {
  const [formState, setFormState] = useState<InputFormState>(defaultFormState);
  
  const updateField = useCallback((
    section: keyof InputFormState,
    field: string,
    value: unknown
  ) => {
    setFormState(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }));
  }, []);
  
  const updateSection = useCallback((
    section: keyof InputFormState,
    data: Partial<InputFormState[keyof InputFormState]>
  ) => {
    setFormState(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        ...data,
      },
    }));
  }, []);
  
  const resetForm = useCallback(() => {
    setFormState(defaultFormState);
  }, []);
  
  const loadDraft = useCallback((draft: InputFormState) => {
    setFormState(draft);
  }, []);
  
  return {
    formState,
    updateField,
    updateSection,
    resetForm,
    loadDraft,
  };
}
