/**
 * useTenant Hook
 * Tenant context hook for RISKCAST V3
 */
import { useState, useEffect, useCallback } from 'react';

interface Tenant {
  id: string;
  name: string;
  slug?: string;
}

export function useTenant() {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load tenant from localStorage on mount
  useEffect(() => {
    const tenantId = localStorage.getItem('tenant_id');
    const tenantStr = localStorage.getItem('tenant');
    
    if (tenantId && tenantStr) {
      try {
        const tenantData = JSON.parse(tenantStr);
        setTenant(tenantData);
      } catch (e) {
        // Invalid tenant data, clear it
        localStorage.removeItem('tenant_id');
        localStorage.removeItem('tenant');
      }
    }
    setIsLoading(false);
  }, []);

  const setCurrentTenant = useCallback((tenantData: Tenant) => {
    localStorage.setItem('tenant_id', tenantData.id);
    localStorage.setItem('tenant', JSON.stringify(tenantData));
    setTenant(tenantData);
  }, []);

  const clearTenant = useCallback(() => {
    localStorage.removeItem('tenant_id');
    localStorage.removeItem('tenant');
    setTenant(null);
  }, []);

  return {
    tenant,
    isLoading,
    setCurrentTenant,
    clearTenant
  };
}
