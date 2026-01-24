import { useState, useEffect, useCallback } from 'react';
import { Header } from './Header';
import { HeroOverview } from './HeroOverview';
import { InfoPanel } from './InfoPanel';
import { AIAdvisor } from './AIAdvisor';
import { IntelligenceModules } from './IntelligenceModules';
import { ActionFooter } from './ActionFooter';
import { SmartInlineEditor } from './SmartInlineEditor';
import { AiAdvisorDock, AiAdvisorTrigger } from '../AiAdvisorDock';
import { AiDockProvider } from '../../hooks/useAiDockState';
import type { ShipmentData, ModulesState, SaveState } from './types';
import { getValidationIssues, type ValidationIssue } from '../../lib/validation';
import { 
  mapInputFormToDomainCase, 
  mapDomainCaseToShipmentData,
  createDefaultDomainCase,
  mapDomainCaseToAnalyzeRequest,
  type DomainCase,
  loadDomainCaseFromStorage,
  saveDomainCaseToStorage,
} from '@/domain';
import { computeInputHash } from '@/engine/inputHash';
import { CaseStepper } from '../ui/CaseStepper';
import { SummaryBreadcrumb } from '../ui/Breadcrumb';

// Smart field types for enhanced editing
type SmartFieldType = 'text' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea' | 'port' | 'cargo_type' | 'incoterm' | 'mode' | 'carrier' | 'container';

// Field configuration for smart inline editor
const FIELD_CONFIG: Record<string, { type: SmartFieldType; label: string; options?: Array<{ value: string; label: string }> }> = {
  'trade.pol': { type: 'port', label: 'Port of Loading' },
  'trade.pod': { type: 'port', label: 'Port of Discharge' },
  'trade.mode': { type: 'mode', label: 'Transport Mode' },
  'trade.container_type': { type: 'container', label: 'Container Type' },
  'trade.etd': { type: 'date', label: 'ETD' },
  'trade.eta': { type: 'date', label: 'ETA' },
  'trade.transit_time_days': { type: 'number', label: 'Transit Days' },
  'trade.incoterm': { type: 'incoterm', label: 'Incoterm' },
  'trade.incoterm_location': { type: 'text', label: 'Incoterm Location' },
  'trade.carrier': { type: 'carrier', label: 'Carrier' },
  'trade.priority': { type: 'select', label: 'Priority', options: [
    { value: 'low', label: 'Low' },
    { value: 'normal', label: 'Normal' },
    { value: 'high', label: 'High' },
    { value: 'urgent', label: 'Urgent' },
  ]},
  'cargo.cargo_type': { type: 'cargo_type', label: 'Cargo Type' },
  'cargo.cargo_category': { type: 'text', label: 'Cargo Category' },
  'cargo.hs_code': { type: 'text', label: 'HS Code' },
  'cargo.packages': { type: 'number', label: 'Packages' },
  'cargo.gross_weight_kg': { type: 'number', label: 'Gross Weight (kg)' },
  'cargo.net_weight_kg': { type: 'number', label: 'Net Weight (kg)' },
  'cargo.volume_cbm': { type: 'number', label: 'Volume (CBM)' },
  'cargo.packing_type': { type: 'text', label: 'Packing Type' },
  'cargo.stackability': { type: 'checkbox', label: 'Stackable' },
  'cargo.temp_control_required': { type: 'checkbox', label: 'Temperature Controlled' },
  'cargo.is_dg': { type: 'checkbox', label: 'Dangerous Goods' },
  // Shipment Value (top-level field)
  'value': { type: 'number', label: 'Shipment Value (USD)' },
  'seller.company': { type: 'text', label: 'Company' },
  'seller.name': { type: 'text', label: 'Contact Name' },
  'seller.email': { type: 'text', label: 'Email' },
  'seller.phone': { type: 'text', label: 'Phone' },
  'seller.country': { type: 'text', label: 'Country' },
  'seller.city': { type: 'text', label: 'City' },
  'seller.address': { type: 'textarea', label: 'Address' },
  'seller.tax_id': { type: 'text', label: 'Tax ID' },
  'buyer.company': { type: 'text', label: 'Company' },
  'buyer.name': { type: 'text', label: 'Contact Name' },
  'buyer.email': { type: 'text', label: 'Email' },
  'buyer.phone': { type: 'text', label: 'Phone' },
  'buyer.country': { type: 'text', label: 'Country' },
  'buyer.city': { type: 'text', label: 'City' },
  'buyer.address': { type: 'textarea', label: 'Address' },
  'buyer.tax_id': { type: 'text', label: 'Tax ID' },
};

// Get nested value from object
function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce((acc, part) => {
    if (acc && typeof acc === 'object' && part in acc) {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, obj as unknown);
}

// Set nested value in object
function setNestedValue(obj: Record<string, unknown>, path: string, value: unknown): void {
  const parts = path.split('.');
  const last = parts.pop()!;
  const target = parts.reduce((acc, part) => {
    if (!(acc as Record<string, unknown>)[part]) {
      (acc as Record<string, unknown>)[part] = {};
    }
    return (acc as Record<string, unknown>)[part] as Record<string, unknown>;
  }, obj);
  target[last] = value;
}

interface RiskcastSummaryProps {
  initialData?: ShipmentData;
}

export function RiskcastSummary({ initialData }: RiskcastSummaryProps) {
  // Default data
  const defaultData: ShipmentData = {
    shipmentId: 'SH-SGN-LAX-' + Date.now().toString().slice(-10),
    trade: {
      pol: 'SGN',
      polName: 'Tan Son Nhat International Airport',
      polCity: 'Ho Chi Minh City',
      polCountry: 'Vietnam',
      pod: 'LAX',
      podName: 'Los Angeles International Airport',
      podCity: 'Los Angeles',
      podCountry: 'United States',
      mode: 'AIR',
      service_route: 'SGN-LAX Direct',
      carrier: 'Cathay Pacific',
      container_type: 'Air Cargo Unit',
      etd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] || '',
      eta: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] || '',
      transit_time_days: 3,
      incoterm: 'CIF',
      incoterm_location: 'Los Angeles',
      priority: 'normal',
    },
    cargo: {
      cargo_type: 'Electronics',
      cargo_category: 'General',
      hs_code: '8471.30',
      hs_chapter: '84',
      packing_type: 'Pallets',
      packages: 24,
      gross_weight_kg: 1200,
      net_weight_kg: 1100,
      volume_cbm: 8.5,
      stackability: false,
      temp_control_required: false,
      is_dg: false,
    },
    seller: {
      name: 'John Nguyen',
      company: 'Vietnam Export Co.',
      email: 'john@vnexport.com',
      phone: '+84 28 3824 5678',
      country: 'Vietnam',
      city: 'Ho Chi Minh City',
      address: '123 Le Loi Street',
      tax_id: 'VN123456789',
    },
    buyer: {
      name: 'Mike Johnson',
      company: 'US Import LLC',
      email: 'mike@usimport.com',
      phone: '+1 213 555 1234',
      country: 'United States',
      city: 'Los Angeles',
      address: '456 Commerce Ave',
      tax_id: 'US987654321',
    },
    value: 125000,
    currency: 'USD',
  };

  // State
  const [data, setData] = useState<ShipmentData>(initialData ?? defaultData);
  const [modules, setModules] = useState<ModulesState>({
    esg: true,
    weather: true,
    portCongestion: true,
    carrierPerformance: true,
    marketScanner: false,
    insurance: true,
  });
  const [saveState, setSaveState] = useState<SaveState>('saved');
  const [lastSaved, setLastSaved] = useState<Date>(new Date());
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [editor, setEditor] = useState<{
    isOpen: boolean;
    field: string;
    value: unknown;
    position: { x: number; y: number };
  }>({
    isOpen: false,
    field: '',
    value: null,
    position: { x: 0, y: 0 },
  });

  // Transform RISKCAST_STATE (Input page format) to ShipmentData format
  // UPDATED: Uses domain mapper for consistent transformation
  const transformInputStateToSummary = (state: Record<string, unknown>): ShipmentData => {
    // Use domain mapper: Input form state → DomainCase → ShipmentData
    const domainCase = mapInputFormToDomainCase(state);
    return mapDomainCaseToShipmentData(domainCase);
  };

  // Load data from canonical storage on mount (migrate legacy if needed)
  useEffect(() => {
    console.log('[RiskcastSummary] Loading canonical DomainCase from storage (migrating legacy if present)...');
    
    // Debug: Check what's in localStorage
    const rawState = localStorage.getItem('RISKCAST_STATE');
    const rawCase = localStorage.getItem('RISKCAST_CASE_V1');
    console.log('[RiskcastSummary] DEBUG - RISKCAST_STATE:', rawState ? JSON.parse(rawState) : 'null');
    console.log('[RiskcastSummary] DEBUG - RISKCAST_CASE_V1:', rawCase ? JSON.parse(rawCase) : 'null');
    
    try {
      const domainCase = loadDomainCaseFromStorage();
      if (domainCase) {
        console.log('[RiskcastSummary] Loaded DomainCase:', domainCase);
        console.log('[RiskcastSummary] DomainCase fields check:', {
          eta: domainCase.eta,
          transitTimeDays: domainCase.transitTimeDays,
          carrier: domainCase.carrier,
          hsCode: domainCase.hsCode,
          packaging: domainCase.packaging,
          cargoValue: domainCase.cargoValue,
        });
        const transformed = mapDomainCaseToShipmentData(domainCase);
        console.log('[RiskcastSummary] Transformed ShipmentData:', transformed);
        console.log('[RiskcastSummary] ShipmentData fields check:', {
          eta: transformed.trade.eta,
          transit_time_days: transformed.trade.transit_time_days,
          carrier: transformed.trade.carrier,
          hs_code: transformed.cargo.hs_code,
          packing_type: transformed.cargo.packing_type,
          value: transformed.value,
        });
        setData(transformed);
        if (domainCase.modules) {
          setModules({
            esg: domainCase.modules.esg,
            weather: domainCase.modules.weather,
            portCongestion: domainCase.modules.portCongestion,
            carrierPerformance: domainCase.modules.carrierPerformance,
            marketScanner: domainCase.modules.marketScanner,
            insurance: domainCase.modules.insurance,
          });
        }
      } else {
        console.log('[RiskcastSummary] No canonical case found, using default data');
      }
    } catch (e) {
      console.error('[RiskcastSummary] Failed to load/migrate DomainCase:', e);
      console.error('[RiskcastSummary] Error stack:', e instanceof Error ? e.stack : String(e));
    }

    const savedModules = localStorage.getItem('summary_modules_state');
    if (savedModules) {
      try {
        setModules(JSON.parse(savedModules));
      } catch (e) {
        console.warn('Failed to parse saved modules:', e);
      }
    }
  }, []);

  // Save modules to localStorage
  useEffect(() => {
    localStorage.setItem('summary_modules_state', JSON.stringify(modules));
  }, [modules]);

  // Validation issues
  const validationIssues = getValidationIssues(data);
  
  // Calculate completeness and canAnalyze (for header actions)
  const requiredFields = [
    { value: data.trade.pol, label: 'POL' },
    { value: data.trade.pod, label: 'POD' },
    { value: data.trade.mode, label: 'Mode' },
    { value: data.trade.container_type, label: 'Container' },
    { value: data.trade.etd, label: 'ETD' },
    { value: data.trade.transit_time_days, label: 'Transit Time' },
    { value: data.cargo.cargo_type, label: 'Cargo Type' },
    { value: data.cargo.hs_code, label: 'HS Code' },
    { value: data.cargo.packages, label: 'Packages' },
    { value: data.cargo.gross_weight_kg, label: 'Gross Weight' },
    { value: data.cargo.volume_cbm, label: 'Volume' },
    { value: data.seller.company, label: 'Seller Company' },
    { value: data.seller.email, label: 'Seller Email' },
    { value: data.seller.phone, label: 'Seller Phone' },
    { value: data.seller.country, label: 'Seller Country' },
    { value: data.buyer.company, label: 'Buyer Company' },
    { value: data.buyer.email, label: 'Buyer Email' },
    { value: data.buyer.phone, label: 'Buyer Phone' },
    { value: data.buyer.country, label: 'Buyer Country' },
  ];
  const filledCount = requiredFields.filter(f => f.value && f.value !== 0).length;
  const completeness = Math.round((filledCount / requiredFields.length) * 100);
  const canAnalyze = completeness >= 20; // Allow analysis with partial data for testing

  // Handlers
  const handleFieldClick = useCallback((path: string, event?: MouseEvent | React.MouseEvent) => {
    const fieldConfig = FIELD_CONFIG[path];
    if (!fieldConfig) return;

    const value = getNestedValue(data as unknown as Record<string, unknown>, path);
    const rect = event?.target instanceof HTMLElement 
      ? event.target.getBoundingClientRect() 
      : { left: window.innerWidth / 2 - 150, top: window.innerHeight / 2 - 100 };

    setEditor({
      isOpen: true,
      field: path,
      value,
      position: { x: rect.left, y: rect.top + 40 },
    });
  }, [data]);

  // Helper: Convert ShipmentData back to DomainCase for saving
  // CRITICAL: Preserve all fields, handle empty strings correctly (empty string → undefined for optional fields)
  const shipmentDataToDomainCase = useCallback((shipmentData: ShipmentData): DomainCase => {
    // Map ShipmentData back to DomainCase (for saving as DomainCase)
    // Normalize empty strings to undefined for optional fields
    const normalizeOptionalString = (val: string | undefined | null): string | undefined => {
      return (val && val.trim() !== '') ? val : undefined;
    };
    
    const formData: Record<string, unknown> = {
      pol_code: shipmentData.trade.pol,
      pod_code: shipmentData.trade.pod,
      transport_mode: shipmentData.trade.mode.toLowerCase(),
      container: shipmentData.trade.container_type,
      service_route: normalizeOptionalString(shipmentData.trade.service_route),
      carrier: normalizeOptionalString(shipmentData.trade.carrier),
      etd: shipmentData.trade.etd,
      // CRITICAL: Empty string '' → undefined for optional eta
      eta: normalizeOptionalString(shipmentData.trade.eta),
      // CRITICAL: Preserve 0 as valid transit_time_days value (0 days is valid)
      transit_time_days: shipmentData.trade.transit_time_days ?? 0,
      cargo_type: shipmentData.cargo.cargo_type,
      cargo_category: normalizeOptionalString(shipmentData.cargo.cargo_category),
      hs_code: normalizeOptionalString(shipmentData.cargo.hs_code),
      packaging: normalizeOptionalString(shipmentData.cargo.packing_type),
      packages: shipmentData.cargo.packages ?? 1,
      // CRITICAL: Preserve 0 as valid weight/volume (0 kg/0 CBM is valid)
      gross_weight_kg: shipmentData.cargo.gross_weight_kg ?? undefined,
      net_weight_kg: shipmentData.cargo.net_weight_kg ?? undefined,
      volume_cbm: shipmentData.cargo.volume_cbm ?? undefined,
      // CRITICAL: Preserve cargoValue even if 0 (0 is valid for free samples, etc.)
      cargo_value: shipmentData.value ?? 0,
      currency: shipmentData.currency || 'USD',
      incoterm: normalizeOptionalString(shipmentData.trade.incoterm),
      incoterm_location: normalizeOptionalString(shipmentData.trade.incoterm_location),
      priority: shipmentData.trade.priority || 'normal',
      seller: {
        name: normalizeOptionalString(shipmentData.seller.name),
        company: shipmentData.seller.company || '',
        email: shipmentData.seller.email || '',
        phone: shipmentData.seller.phone || '',
        country: shipmentData.seller.country || '',
        city: normalizeOptionalString(shipmentData.seller.city),
        address: normalizeOptionalString(shipmentData.seller.address),
        tax_id: normalizeOptionalString(shipmentData.seller.tax_id),
      },
      buyer: {
        name: normalizeOptionalString(shipmentData.buyer.name),
        company: shipmentData.buyer.company || '',
        email: shipmentData.buyer.email || '',
        phone: shipmentData.buyer.phone || '',
        country: shipmentData.buyer.country || '',
        city: normalizeOptionalString(shipmentData.buyer.city),
        address: normalizeOptionalString(shipmentData.buyer.address),
        tax_id: normalizeOptionalString(shipmentData.buyer.tax_id),
      },
      modules,
    };
    
    return mapInputFormToDomainCase(formData);
  }, [modules]);

  const handleEditorSave = useCallback((value: unknown) => {
    setSaveState('saving');
    
    const newData = JSON.parse(JSON.stringify(data)) as Record<string, unknown>;
    setNestedValue(newData, editor.field, value);
    setData(newData as unknown as ShipmentData);

    // Persist canonical DomainCase (single source of truth)
    const domainCase = shipmentDataToDomainCase(newData as unknown as ShipmentData);
    saveDomainCaseToStorage(domainCase);
    
    setTimeout(() => {
      setSaveState('saved');
      setLastSaved(new Date());
    }, 500);
  }, [data, editor.field]);

  const handleEditorClose = useCallback(() => {
    setEditor(prev => ({ ...prev, isOpen: false }));
  }, []);

  const handleModuleToggle = useCallback((key: keyof ModulesState) => {
    setModules(prev => ({ ...prev, [key]: !prev[key] }));
    setSaveState('unsaved');
    setTimeout(() => {
      setSaveState('saved');
      setLastSaved(new Date());
    }, 500);
  }, []);

  const handleSaveDraft = useCallback(() => {
    setSaveState('saving');
    
    // Convert ShipmentData to DomainCase for saving (single source of truth)
    const domainCase = shipmentDataToDomainCase(data);
    saveDomainCaseToStorage(domainCase);
    
    // Also save modules separately (for backward compatibility)
    localStorage.setItem('summary_modules_state', JSON.stringify(modules));
    
    setTimeout(() => {
      setSaveState('saved');
      setLastSaved(new Date());
    }, 500);
  }, [data, modules, shipmentDataToDomainCase]);

  const handleBack = useCallback(() => {
    window.history.back();
  }, []);

  const handleRunAnalysis = useCallback(async () => {
    setIsAnalyzing(true);
    
    try {
      // Save current state first (as canonical DomainCase for single source of truth)
      const domainCase = shipmentDataToDomainCase(data);
      saveDomainCaseToStorage(domainCase);
      localStorage.setItem('summary_modules_state', JSON.stringify(modules));

      // Build analyze payload deterministically from DomainCase
      const payload = {
        ...mapDomainCaseToAnalyzeRequest(domainCase),
        timestamp: new Date().toISOString(),
      };

      // Try to call API, but handle gracefully if it fails
      let results = null;
      try {
        const response = await fetch('/api/v1/risk/v2/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          const responseData = await response.json();
          // Handle standard response format: {success: true, data: {...}}
          // Extract actual result from data.result or use data directly
          if (responseData.success && responseData.data) {
            // If data has a 'result' field, use it; otherwise use data itself
            results = responseData.data.result || responseData.data;
          } else {
            // Legacy format: response is the result directly
            results = responseData;
          }
          console.log('[RiskcastSummary] API response parsed:', results);
        }
      } catch (apiError) {
        console.error('[RiskcastSummary] API request failed:', apiError);
        // CRITICAL: Do NOT generate fake data. Show error instead.
        setIsAnalyzing(false);
        setSaveState('error');
        alert('Risk analysis engine is unavailable. Please ensure the backend server is running and try again.');
        return; // Exit early - do not proceed without real engine data
      }

      // CRITICAL: If no results from engine, show error - NEVER generate fake data
      if (!results) {
        console.error('[RiskcastSummary] No results received from engine');
        setIsAnalyzing(false);
        setSaveState('error');
        alert('No analysis results received from engine. Please check the API connection and try again.');
        return; // Exit early - do not proceed without real engine data
      }

      // Validate that results came from real engine (not mock)
      if (results.engine_version && results.engine_version.includes('mock')) {
        console.error('[RiskcastSummary] CRITICAL: Mock data detected - rejecting');
        throw new Error('Mock data is not allowed in production');
      }

      // Compute input hash for stale result detection
      const inputHash = computeInputHash(domainCase);
      const runId = results.run_id ?? results.runId ?? results.analysis_id ?? `run-${Date.now()}`;
      
      // Store expected context for integrity validation
      const expectedContext = {
        expectedCaseId: domainCase.caseId || undefined,
        expectedRunId: String(runId),
        expectedInputHash: inputHash,
        expectedCargoValue: domainCase.cargoValue || undefined,
        expectedCurrency: domainCase.currency || undefined,
        expectedPol: domainCase.pol || undefined,
        expectedPod: domainCase.pod || undefined,
      };
      
      // Save context for Results page to use
      localStorage.setItem('RISKCAST_EXPECTED_CONTEXT', JSON.stringify(expectedContext));
      
      // Attach input hash to results for backend verification
      if (results && typeof results === 'object') {
        (results as Record<string, unknown>).input_hash = inputHash;
        (results as Record<string, unknown>).run_id = runId;
      }

      // Save ONLY real engine results
      localStorage.setItem('RISKCAST_RESULTS_V2', JSON.stringify(results));
      
      // Short delay for UX
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Redirect to results page
      console.log('[RiskcastSummary] Redirecting to /results...');
      window.location.href = '/results';
    } catch (error) {
      console.error('[RiskcastSummary] Analysis error:', error);
      setSaveState('error');
      alert('Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  }, [data, modules]);

  const handleIssueClick = useCallback((issue: ValidationIssue) => {
    if (issue.affectedFields.length > 0) {
      const firstField = issue.affectedFields[0];
      if (!firstField) return;
      // Find and scroll to the field
      const fieldElement = document.querySelector(`[data-field-path="${firstField}"]`);
      if (fieldElement) {
        fieldElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Trigger click to open editor
        const rect = fieldElement.getBoundingClientRect();
        handleFieldClick(firstField, { target: fieldElement, left: rect.left, top: rect.top } as unknown as MouseEvent);
      }
    }
  }, [handleFieldClick]);

  // Build field arrays for panels
  const tradeFields = [
    { label: 'POL', value: data.trade.pol, path: 'trade.pol' },
    { label: 'POD', value: data.trade.pod, path: 'trade.pod' },
    { label: 'Mode', value: data.trade.mode, path: 'trade.mode' },
    { label: 'Container', value: data.trade.container_type, path: 'trade.container_type' },
    { label: 'ETD', value: data.trade.etd, path: 'trade.etd' },
    { label: 'ETA', value: data.trade.eta, path: 'trade.eta' },
    { label: 'Transit Days', value: data.trade.transit_time_days, path: 'trade.transit_time_days' },
    { label: 'Incoterm', value: data.trade.incoterm, path: 'trade.incoterm' },
    { label: 'Carrier', value: data.trade.carrier, path: 'trade.carrier' },
    { label: 'Priority', value: data.trade.priority, path: 'trade.priority' },
  ];

  // Format money value for display
  const formatMoney = (val: number | null | undefined): string => {
    if (val == null || isNaN(val)) return '—';
    return `$${val.toLocaleString('en-US')} ${data.currency || 'USD'}`;
  };

  const cargoFields = [
    { label: 'Cargo Type', value: data.cargo.cargo_type, path: 'cargo.cargo_type' },
    { label: 'HS Code', value: data.cargo.hs_code, path: 'cargo.hs_code' },
    { label: 'Packages', value: data.cargo.packages, path: 'cargo.packages' },
    { label: 'Gross Weight', value: `${data.cargo.gross_weight_kg} kg`, path: 'cargo.gross_weight_kg' },
    { label: 'Volume', value: `${data.cargo.volume_cbm} CBM`, path: 'cargo.volume_cbm' },
    { label: 'Packing', value: data.cargo.packing_type, path: 'cargo.packing_type' },
    { label: 'Stackable', value: data.cargo.stackability, path: 'cargo.stackability' },
    { label: 'Temp Control', value: data.cargo.temp_control_required, path: 'cargo.temp_control_required' },
    { label: 'Dangerous', value: data.cargo.is_dg, path: 'cargo.is_dg' },
    // SHIPMENT VALUE - editable money field (last tile)
    { label: 'Shipment Value', value: formatMoney(data.value), path: 'value' },
  ];

  const sellerFields = [
    { label: 'Company', value: data.seller.company, path: 'seller.company' },
    { label: 'Contact', value: data.seller.name, path: 'seller.name' },
    { label: 'Email', value: data.seller.email, path: 'seller.email' },
    { label: 'Phone', value: data.seller.phone, path: 'seller.phone' },
    { label: 'Country', value: data.seller.country, path: 'seller.country' },
    { label: 'City', value: data.seller.city, path: 'seller.city' },
  ];

  const buyerFields = [
    { label: 'Company', value: data.buyer.company, path: 'buyer.company' },
    { label: 'Contact', value: data.buyer.name, path: 'buyer.name' },
    { label: 'Email', value: data.buyer.email, path: 'buyer.email' },
    { label: 'Phone', value: data.buyer.phone, path: 'buyer.phone' },
    { label: 'Country', value: data.buyer.country, path: 'buyer.country' },
    { label: 'City', value: data.buyer.city, path: 'buyer.city' },
  ];

  const fieldConfig = FIELD_CONFIG[editor.field] ?? { type: 'text', label: editor.field };

  return (
    <AiDockProvider>
    <div className="min-h-screen bg-gradient-to-br from-[#0a1628] via-[#0d1f35] to-[#0a1628]">
      <Header 
        saveState={saveState} 
        lastSaved={lastSaved}
        actions={{
          onBack: handleBack,
          onSaveDraft: handleSaveDraft,
          onRunAnalysis: handleRunAnalysis,
          canAnalyze,
          isAnalyzing,
        }}
      />

      {/* PR #6: Case Stepper (Navigation Progress) */}
      <div className="px-12 pt-4 pb-2 border-b border-white/10">
        <CaseStepper currentStep="summary" completedSteps={['input']} />
      </div>

      {/* PR #6: Breadcrumb Navigation */}
      <div className="px-12 pt-4">
        <SummaryBreadcrumb />
      </div>

      <main className="px-12 py-8 pb-24">
        {/* Hero Overview */}
        <HeroOverview data={data} />

        {/* Main Content Grid */}
        <div className="mt-8 grid grid-cols-3 gap-6">
          {/* Left Column: Panels */}
          <div className="col-span-2 space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <InfoPanel
                title="Trade Details"
                icon="trade"
                fields={tradeFields}
                validationIssues={validationIssues}
                onFieldClick={handleFieldClick}
              />
              <InfoPanel
                title="Cargo Details"
                icon="cargo"
                fields={cargoFields}
                validationIssues={validationIssues}
                onFieldClick={handleFieldClick}
              />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <InfoPanel
                title="Seller/Shipper"
                icon="seller"
                fields={sellerFields}
                validationIssues={validationIssues}
                onFieldClick={handleFieldClick}
              />
              <InfoPanel
                title="Buyer/Consignee"
                icon="buyer"
                fields={buyerFields}
                validationIssues={validationIssues}
                onFieldClick={handleFieldClick}
              />
            </div>

            {/* Intelligence Modules */}
            <IntelligenceModules modules={modules} onToggle={handleModuleToggle} />
          </div>

          {/* Right Column: AI Advisor */}
          <div className="sticky top-24">
            <AIAdvisor issues={validationIssues} onIssueClick={handleIssueClick} />
          </div>
        </div>
      </main>

      {/* Action Footer - REMOVED: Actions moved to header */}
      {/* Status Footer (optional - can show completion status) */}
      <div className="fixed bottom-0 left-0 right-0 z-40 backdrop-blur-xl bg-[#0a1628]/90 border-t border-white/10">
        <div className="px-12 py-3">
          <div className="flex items-center justify-between">
            {/* Left: Status Pills */}
            <div className="flex items-center gap-4">
              {/* Completeness */}
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all ${
                      completeness === 100 
                        ? 'bg-green-500' 
                        : completeness >= 80 
                          ? 'bg-cyan-500' 
                          : 'bg-orange-500'
                    }`}
                    style={{ width: `${completeness}%` }}
                  />
                </div>
                <span className="text-white/70 text-sm">{completeness}% Complete</span>
              </div>

              {/* Issues */}
              {validationIssues.filter(i => i.severity === 'critical').length > 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-full">
                  <span className="text-red-300 text-xs font-medium">
                    {validationIssues.filter(i => i.severity === 'critical').length} Critical
                  </span>
                </div>
              )}
              {validationIssues.filter(i => i.severity === 'warning').length > 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/20 border border-orange-500/30 rounded-full">
                  <span className="text-orange-300 text-xs font-medium">
                    {validationIssues.filter(i => i.severity === 'warning').length} Warnings
                  </span>
                </div>
              )}
              {validationIssues.filter(i => i.severity === 'critical').length === 0 && 
               validationIssues.filter(i => i.severity === 'warning').length === 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 border border-green-500/30 rounded-full">
                  <span className="text-green-300 text-xs font-medium">✓ All Clear</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Smart Inline Editor */}
      <SmartInlineEditor
        isOpen={editor.isOpen}
        field={editor.field}
        label={fieldConfig.label}
        value={editor.value}
        type={fieldConfig.type}
        options={fieldConfig.options}
        position={editor.position}
        transportMode={data.trade?.mode}
        onSave={handleEditorSave}
        onClose={handleEditorClose}
      />

      {/* AI Advisor Dock - Premium dock pattern (no overlap with footer) */}
      <AiAdvisorDock
        context={{
          page: 'summary',
          shipmentId: data.shipmentId,
        }}
      />
    </div>
    </AiDockProvider>
  );
}

export type { ShipmentData, ModulesState };

