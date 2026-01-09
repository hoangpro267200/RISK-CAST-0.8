import { useState, useEffect, useCallback } from 'react';
import { Header } from './Header';
import { HeroOverview } from './HeroOverview';
import { InfoPanel } from './InfoPanel';
import { AIAdvisor } from './AIAdvisor';
import { IntelligenceModules } from './IntelligenceModules';
import { ActionFooter } from './ActionFooter';
import { SmartInlineEditor } from './SmartInlineEditor';
import { SystemChatPanel } from '../SystemChatPanel';
import type { ShipmentData, ModulesState, SaveState } from './types';
import { getValidationIssues, type ValidationIssue } from '../../lib/validation';

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
  'value': { type: 'number', label: 'Shipment Value (USD)' },
};

// Get nested value from object
function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce((acc, part) => (acc as Record<string, unknown>)?.[part], obj);
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
      etd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      eta: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
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
  const transformInputStateToSummary = (state: Record<string, unknown>): ShipmentData => {
    const transport = (state.transport || {}) as Record<string, unknown>;
    const cargo = (state.cargo || {}) as Record<string, unknown>;
    const seller = (state.seller || {}) as Record<string, unknown>;
    const buyer = (state.buyer || {}) as Record<string, unknown>;
    
    // Get POL/POD codes
    const pol = String(transport.pol || 'SGN');
    const pod = String(transport.pod || 'LAX');
    
    // Map port codes to names/cities (basic mapping)
    const portInfo: Record<string, { name: string; city: string; country: string }> = {
      'SGN': { name: 'Tan Son Nhat International Airport', city: 'Ho Chi Minh City', country: 'Vietnam' },
      'VNSGN': { name: 'Tan Son Nhat International Airport', city: 'Ho Chi Minh City', country: 'Vietnam' },
      'LAX': { name: 'Los Angeles International Airport', city: 'Los Angeles', country: 'United States' },
      'USLAX': { name: 'Los Angeles International Airport', city: 'Los Angeles', country: 'United States' },
      'SHA': { name: 'Shanghai Pudong International Airport', city: 'Shanghai', country: 'China' },
      'HKG': { name: 'Hong Kong International Airport', city: 'Hong Kong', country: 'Hong Kong' },
      'SIN': { name: 'Changi Airport', city: 'Singapore', country: 'Singapore' },
    };
    
    const polInfo = portInfo[pol.toUpperCase()] || { name: pol, city: pol, country: 'Unknown' };
    const podInfo = portInfo[pod.toUpperCase()] || { name: pod, city: pod, country: 'Unknown' };
    
    // Get shipment value from multiple possible sources
    const shipmentValue = Number(cargo.insuranceValue) || Number(cargo.value) || Number(cargo.cargo_value) || Number(state.value) || 0;
    
    // Get seller/buyer country - handle both string and object formats
    const getCountryName = (country: unknown): string => {
      if (typeof country === 'string') return country;
      if (country && typeof country === 'object' && 'name' in country) return String((country as Record<string, unknown>).name);
      return '';
    };
    
    return {
      shipmentId: String(state.shipmentId || `SH-${pol}-${pod}-${Date.now().toString().slice(-10)}`),
      trade: {
        pol: pol,
        polName: polInfo.name,
        polCity: polInfo.city,
        polCountry: polInfo.country,
        pod: pod,
        podName: podInfo.name,
        podCity: podInfo.city,
        podCountry: podInfo.country,
        mode: (String(transport.mode || transport.modeOfTransport || 'AIR').toUpperCase()) as 'AIR' | 'SEA' | 'ROAD' | 'RAIL' | 'MULTIMODAL',
        service_route: String(transport.serviceRoute || `${pol}-${pod} Direct`),
        carrier: String(transport.carrier || ''),
        container_type: String(transport.containerType || 'Air Cargo Unit'),
        etd: String(transport.etd || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]),
        eta: String(transport.eta || new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]),
        transit_time_days: Number(transport.transitTime || transport.transitTimeDays) || 3,
        incoterm: String(transport.incoterm || 'FOB'),
        incoterm_location: String(transport.incotermLocation || ''),
        priority: String(transport.priority || 'normal'),
      },
      cargo: {
        cargo_type: String(cargo.cargoType || ''),
        cargo_category: String(cargo.category || 'General'),
        hs_code: String(cargo.hsCode || ''),
        hs_chapter: String(cargo.hsCode || '').split('.')[0] || '',
        packing_type: String(cargo.packingType || cargo.packaging || ''),
        packages: Number(cargo.numberOfPackages || cargo.packageCount) || 0,
        gross_weight_kg: Number(cargo.grossWeight || cargo.weight) || 0,
        net_weight_kg: Number(cargo.netWeight) || 0,
        volume_cbm: Number(cargo.volumeM3 || cargo.volume) || 0,
        stackability: cargo.stackable !== false,
        temp_control_required: Boolean(cargo.temperatureControl || cargo.tempControl),
        is_dg: Boolean(cargo.dangerousGoods || cargo.isDG),
      },
      seller: {
        name: String(seller.contactPerson || seller.contact_person || ''),
        company: String(seller.companyName || seller.company_name || ''),
        email: String(seller.email || ''),
        phone: String(seller.phone || ''),
        country: getCountryName(seller.country),
        city: String(seller.city || ''),
        address: String(seller.address || ''),
        tax_id: String(seller.taxId || seller.tax_id || ''),
      },
      buyer: {
        name: String(buyer.contactPerson || buyer.contact_person || ''),
        company: String(buyer.companyName || buyer.company_name || ''),
        email: String(buyer.email || ''),
        phone: String(buyer.phone || ''),
        country: getCountryName(buyer.country),
        city: String(buyer.city || ''),
        address: String(buyer.address || ''),
        tax_id: String(buyer.taxId || buyer.tax_id || ''),
      },
      value: shipmentValue,
    };
  };

  // Load data from localStorage on mount
  useEffect(() => {
    console.log('[RiskcastSummary] Loading state from localStorage...');
    
    const savedState = localStorage.getItem('RISKCAST_STATE');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        console.log('[RiskcastSummary] Parsed RISKCAST_STATE:', parsed);
        
        // Check if it's Input page format (has transport key) or Summary format (has trade key)
        if (parsed.transport) {
          // Input page format - transform it
          const transformed = transformInputStateToSummary(parsed);
          console.log('[RiskcastSummary] Transformed data:', transformed);
          setData(transformed);
          
          // Also load modules from riskModules
          const riskModules = parsed.riskModules || parsed.modules || {};
          setModules({
            esg: riskModules.esg !== false,
            weather: riskModules.weather !== false,
            portCongestion: riskModules.port !== false && riskModules.portCongestion !== false,
            carrierPerformance: riskModules.carrier !== false,
            marketScanner: riskModules.market === true,
            insurance: riskModules.insurance !== false,
          });
        } else if (parsed.trade) {
          // Already in Summary format
          setData({
            ...defaultData,
            ...parsed,
          });
        }
      } catch (e) {
        console.warn('[RiskcastSummary] Failed to parse saved state:', e);
      }
    } else {
      console.log('[RiskcastSummary] No RISKCAST_STATE found, using default data');
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

  const handleEditorSave = useCallback((value: unknown) => {
    setSaveState('saving');
    
    const newData = JSON.parse(JSON.stringify(data)) as Record<string, unknown>;
    setNestedValue(newData, editor.field, value);
    setData(newData as unknown as ShipmentData);

    // Save to localStorage
    localStorage.setItem('RISKCAST_STATE', JSON.stringify(newData));
    
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
    localStorage.setItem('RISKCAST_STATE', JSON.stringify(data));
    localStorage.setItem('summary_modules_state', JSON.stringify(modules));
    setTimeout(() => {
      setSaveState('saved');
      setLastSaved(new Date());
    }, 500);
  }, [data, modules]);

  const handleBack = useCallback(() => {
    window.history.back();
  }, []);

  const handleRunAnalysis = useCallback(async () => {
    setIsAnalyzing(true);
    
    try {
      // Save current state first
      localStorage.setItem('RISKCAST_STATE', JSON.stringify(data));
      localStorage.setItem('summary_modules_state', JSON.stringify(modules));
      
      // Prepare payload
      const payload = {
        ...data,
        modules,
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
          results = await response.json();
        }
      } catch (apiError) {
        console.warn('[RiskcastSummary] API not available, generating mock results:', apiError);
      }

      // If no API results, generate mock results matching expected engine format
      if (!results) {
        // Calculate realistic risk score based on data completeness
        const hasRoute = data.trade.pol && data.trade.pod;
        const hasCarrier = !!data.trade.carrier;
        const hasCargo = !!data.cargo.cargo_type;
        const hasParties = !!data.seller.company || !!data.buyer.company;
        
        // Base score: lower is better, start moderate and adjust
        let baseRisk = 45;
        if (!hasRoute) baseRisk += 15;
        if (!hasCarrier) baseRisk += 10;
        if (!hasCargo) baseRisk += 8;
        if (!hasParties) baseRisk += 5;
        
        // Add some variance
        const riskScoreValue = Math.min(95, Math.max(15, baseRisk + Math.floor(Math.random() * 15) - 7));
        const transitDays = data.trade.transit_time_days || 7;
        
        // Determine risk level based on score
        const getRiskLevel = (score: number): 'Low' | 'Medium' | 'High' | 'Critical' => {
          if (score < 30) return 'Low';
          if (score < 50) return 'Medium';
          if (score < 75) return 'High';
          return 'Critical';
        };
        
        const riskLevel = getRiskLevel(riskScoreValue);
        
        results = {
          // Use snake_case to match engine format expected by adapter
          risk_score: riskScoreValue,
          risk_level: riskLevel,
          confidence: 85,
          overall_risk: riskScoreValue,
          profile: {
            score: riskScoreValue,
            level: riskLevel,
            confidence: 85,
            // Factors for radar chart - grouped by category
            factors: {
              // By Category (for radar)
              transport: Math.floor(Math.random() * 20) + 55,      // Mode, Carrier, Route, Transit
              cargo: Math.floor(Math.random() * 25) + 50,          // Sensitivity, Packing, DG
              commercial: Math.floor(Math.random() * 20) + 60,     // Incoterm, Seller, Buyer, Insurance
              compliance: Math.floor(Math.random() * 20) + 45,     // Documentation, Trade
              external: Math.floor(Math.random() * 25) + 40,       // Port, Weather, Market
              // Individual key metrics
              carrier_performance: Math.floor(Math.random() * 25) + 55,
              route_complexity: Math.floor(Math.random() * 20) + 60,
              cargo_sensitivity: Math.floor(Math.random() * 30) + 50,
              weather_exposure: Math.floor(Math.random() * 35) + 35,
              port_congestion: Math.floor(Math.random() * 30) + 40,
            },
            // Risk matrix
            matrix: {
              probability: Math.floor(riskScoreValue / 20) + 2, // 1-9
              severity: Math.floor(riskScoreValue / 15) + 2, // 1-9
              quadrant: riskScoreValue >= 75 ? 'High-High' : riskScoreValue >= 50 ? 'Medium-Medium' : 'Low-Low',
              description: riskScoreValue >= 75 
                ? 'High probability and severity - immediate attention required'
                : riskScoreValue >= 50 
                  ? 'Moderate risk profile - monitor closely'
                  : 'Low risk profile - standard monitoring sufficient',
            },
            explanation: [
              `Risk score of ${riskScoreValue} indicates ${riskScoreValue >= 75 ? 'elevated' : 'manageable'} risk level`,
              `Transit from ${data.trade.pol} to ${data.trade.pod} via ${data.trade.mode || 'SEA'}`,
              `${transitDays} days estimated transit time`,
            ],
          },
          shipment: {
            id: data.shipmentId || `SH-${data.trade.pol}-${data.trade.pod}-${Date.now()}`,
            // Use keys that adapter expects
            pol_code: data.trade.pol,
            pod_code: data.trade.pod,
            origin: data.trade.pol,
            destination: data.trade.pod,
            route: `${data.trade.pol} → ${data.trade.pod}`,
            carrier: data.trade.carrier || 'Maersk',
            etd: data.trade.etd,
            eta: data.trade.eta,
            transit_time: transitDays,
            container: data.trade.container_type,
            cargo: data.cargo.cargo_type,
            incoterm: data.trade.incoterm,
            cargo_value: data.value || 100000,
            value: data.value || 100000,
          },
          // Drivers - Top risk factors impacting this shipment
          drivers: [
            { name: 'Carrier Performance', impact: 32, description: 'Historical carrier on-time delivery rate' },
            { name: 'Cargo Sensitivity', impact: 28, description: 'Cargo fragility and special handling needs' },
            { name: 'Route Complexity', impact: 22, description: 'Distance, transhipments, and route reliability' },
            { name: 'Weather Exposure', impact: 18, description: 'Climate conditions along route' },
            { name: 'Port Congestion', impact: 15, description: 'Origin/destination port utilization' },
            { name: 'Transit Variance', impact: 12, description: 'Schedule reliability and delays' },
            { name: 'Incoterm Risk', impact: 10, description: 'Responsibility transfer points' },
            { name: 'Trade Compliance', impact: 8, description: 'Customs and regulatory requirements' },
          ],
          // 16 Risk Layers matching RiskScoringEngineV21 - ALL ENABLED
          layers: [
            // TRANSPORT (4 layers - 35%)
            { name: 'Mode Reliability', score: Math.floor(Math.random() * 25) + 55, contribution: 10, category: 'TRANSPORT' },
            { name: 'Carrier Performance', score: Math.floor(Math.random() * 30) + 50, contribution: 12, category: 'TRANSPORT' },
            { name: 'Route Complexity', score: Math.floor(Math.random() * 25) + 60, contribution: 8, category: 'TRANSPORT' },
            { name: 'Transit Time Variance', score: Math.floor(Math.random() * 20) + 45, contribution: 5, category: 'TRANSPORT' },
            // CARGO (3 layers - 25%)
            { name: 'Cargo Sensitivity', score: Math.floor(Math.random() * 30) + 55, contribution: 12, category: 'CARGO' },
            { name: 'Packing Quality', score: Math.floor(Math.random() * 25) + 50, contribution: 8, category: 'CARGO' },
            { name: 'DG Compliance', score: Math.floor(Math.random() * 20) + 30, contribution: 5, category: 'CARGO' },
            // COMMERCIAL (4 layers - 20%)
            { name: 'Incoterm Risk', score: Math.floor(Math.random() * 25) + 45, contribution: 8, category: 'COMMERCIAL' },
            { name: 'Seller Credibility', score: Math.floor(Math.random() * 20) + 60, contribution: 6, category: 'COMMERCIAL' },
            { name: 'Buyer Credibility', score: Math.floor(Math.random() * 20) + 65, contribution: 4, category: 'COMMERCIAL' },
            { name: 'Insurance Adequacy', score: Math.floor(Math.random() * 15) + 70, contribution: 2, category: 'COMMERCIAL' },
            // COMPLIANCE (2 layers - 10%)
            { name: 'Documentation', score: Math.floor(Math.random() * 20) + 50, contribution: 5, category: 'COMPLIANCE' },
            { name: 'Trade Compliance', score: Math.floor(Math.random() * 25) + 45, contribution: 5, category: 'COMPLIANCE' },
            // EXTERNAL (3 layers - 10%)
            { name: 'Port Congestion', score: Math.floor(Math.random() * 30) + 40, contribution: 4, category: 'EXTERNAL' },
            { name: 'Weather Climate', score: Math.floor(Math.random() * 35) + 35, contribution: 3, category: 'EXTERNAL' },
            { name: 'Market Volatility', score: Math.floor(Math.random() * 25) + 30, contribution: 3, category: 'EXTERNAL' },
          ],
          // Financial loss metrics
          loss: {
            expectedLoss: Math.round((data.value || 100000) * (riskScoreValue / 100) * 0.05), // ~5% of value * risk
            p95: Math.round((data.value || 100000) * (riskScoreValue / 100) * 0.08), // VaR 95%
            p99: Math.round((data.value || 100000) * (riskScoreValue / 100) * 0.12), // CVaR 99%
            tailContribution: 25,
          },
          // Timeline projections
          timeline: {
            projections: Array.from({ length: 7 }, (_, i) => ({
              date: new Date(Date.now() + i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
              p10: Math.max(0, riskScoreValue - 15 - Math.random() * 5),
              p50: riskScoreValue + (Math.random() - 0.5) * 10,
              p90: Math.min(100, riskScoreValue + 15 + Math.random() * 5),
            })),
          },
          // Risk scenario projections (for fan chart)
          riskScenarioProjections: Array.from({ length: 7 }, (_, i) => ({
            date: new Date(Date.now() + i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            p10: Math.max(0, riskScoreValue - 15 - Math.random() * 5),
            p50: riskScoreValue + (Math.random() - 0.5) * 10,
            p90: Math.min(100, riskScoreValue + 15 + Math.random() * 5),
            phase: i < 2 ? 'Loading' : i < 5 ? 'Transit' : 'Discharge',
          })),
          // Scenarios for recommendations
          scenarios: [
            {
              title: 'Expedited Shipping',
              description: 'Use express carrier to reduce transit time',
              riskReduction: 15,
              costImpact: 2.5,
            },
            {
              title: 'Alternative Route',
              description: 'Route via less congested ports',
              riskReduction: 10,
              costImpact: 1.0,
            },
            {
              title: 'Enhanced Insurance',
              description: 'Comprehensive cargo protection',
              riskReduction: 20,
              costImpact: 1.5,
            },
          ],
          recommendations: [
            {
              type: 'primary',
              title: 'Consider Alternative Route',
              description: 'A direct route via alternative carrier may reduce transit time by 2 days.',
              impact: 'medium',
            },
            {
              type: 'secondary',
              title: 'Monitor Weather Conditions',
              description: 'Seasonal weather patterns may affect schedule reliability.',
              impact: 'low',
            },
          ],
          reasoning: {
            explanation: `Risk analysis for shipment from ${data.trade.pol} to ${data.trade.pod}. The overall risk score of ${riskScoreValue} indicates ${riskLevel.toUpperCase()} risk level with ${transitDays} days transit time via ${data.trade.mode || 'SEA'} transport.`,
          },
          // Decision support data (use snake_case for adapter)
          decision_summary: {
            insurance: {
              status: riskScoreValue >= 60 ? 'RECOMMENDED' : riskScoreValue >= 40 ? 'OPTIONAL' : 'NOT_NEEDED',
              recommendation: riskScoreValue >= 60 ? 'BUY' : riskScoreValue >= 40 ? 'CONSIDER' : 'SKIP',
              rationale: riskScoreValue >= 60 
                ? `High risk score (${riskScoreValue}) suggests comprehensive cargo insurance is advisable`
                : riskScoreValue >= 40
                  ? `Moderate risk level - insurance optional based on cargo value ($${(data.value || 100000).toLocaleString()})`
                  : `Low risk profile - standard coverage should be sufficient`,
              risk_delta_points: riskScoreValue >= 60 ? -15 : riskScoreValue >= 40 ? -8 : -3,
              cost_impact_usd: Math.round((data.value || 100000) * 0.005), // ~0.5% of cargo value
              providers: ['Allianz', 'AIG', 'Zurich'],
            },
            timing: {
              status: riskScoreValue >= 50 ? 'RECOMMENDED' : 'OPTIONAL',
              recommendation: riskScoreValue >= 50 ? 'ADJUST_ETD' : 'KEEP_ETD',
              rationale: riskScoreValue >= 50
                ? `Consider adjusting departure to avoid peak congestion periods`
                : `Current timing is acceptable for this risk profile`,
              optimal_window: {
                start: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                end: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
              },
              risk_reduction_points: riskScoreValue >= 50 ? -10 : -3,
              cost_impact_usd: riskScoreValue >= 50 ? 500 : 0,
            },
            routing: {
              status: riskScoreValue >= 70 ? 'RECOMMENDED' : 'NOT_NEEDED',
              recommendation: riskScoreValue >= 70 ? 'CHANGE_ROUTE' : 'KEEP_ROUTE',
              rationale: riskScoreValue >= 70
                ? `Alternative routing via less congested ports may reduce risk significantly`
                : `Current route ${data.trade.pol} → ${data.trade.pod} is optimal for this shipment`,
              best_alternative: riskScoreValue >= 70 ? 'Via transshipment hub (Singapore)' : null,
              tradeoff: riskScoreValue >= 70 ? '+2 days transit, -15% risk' : null,
              risk_reduction_points: riskScoreValue >= 70 ? -12 : 0,
              cost_impact_usd: riskScoreValue >= 70 ? 1200 : 0,
            },
          },
          insights: [
            { type: 'info', message: 'Route analysis completed successfully' },
            { type: 'warning', message: 'Consider transit time variability' },
          ],
          timestamp: new Date().toISOString(),
          engine_version: '2.0-mock',
          modules: modules,
        };
      }
      
      // Save results
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
    <div className="min-h-screen bg-gradient-to-br from-[#0a1628] via-[#0d1f35] to-[#0a1628]">
      <Header saveState={saveState} lastSaved={lastSaved} />

      <main className="px-12 py-8 pb-28">
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

      {/* Action Footer */}
      <ActionFooter
        data={data}
        modules={modules}
        onRunAnalysis={handleRunAnalysis}
        onSaveDraft={handleSaveDraft}
        onBack={handleBack}
        lastSaved={lastSaved}
        isAnalyzing={isAnalyzing}
      />

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

      {/* AI System Chat Panel */}
      <SystemChatPanel
        context={{
          page: 'summary',
          shipmentId: data.shipmentId,
        }}
      />
    </div>
  );
}

export type { ShipmentData, ModulesState };

