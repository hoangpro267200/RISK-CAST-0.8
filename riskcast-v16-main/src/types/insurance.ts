/**
 * RISKCAST Insurance Module V2 - Type Definitions
 * 
 * Enterprise-Grade Insurtech Integration System
 * Version: 2.0.0
 * Date: January 15, 2026
 */

// ============================================================================
// ENUMS & CONSTANTS
// ============================================================================

export type InsuranceProductCategory = 
  | 'classical'      // Traditional cargo insurance
  | 'parametric'     // Trigger-based parametric products
  | 'specialty'      // High-value, pharma, cold chain
  | 'embedded';      // Embedded specialty products

export type InsuranceProductTier = 
  | 'A'  // Classical Insurance (Foundation Layer)
  | 'B'  // Parametric Products (Innovation Layer)
  | 'C'  // Embedded Specialty Products
  | 'D'  // Transactional API-Backed Products
  | 'E'; // Future Risk Hedging (Financialized)

export type ProductStatus = 
  | 'concept'           // V1 Simulation
  | 'api_parametric'    // V2 API+Parametric
  | 'transactional'     // V3 Transactional
  | 'financialized';   // V4 Financialized

export type TransactionState = 
  | 'quote_requested'
  | 'quote_generated'
  | 'configuring'
  | 'configured'
  | 'kyc_required'
  | 'kyc_in_progress'
  | 'kyc_approved'
  | 'kyc_failed'
  | 'payment_pending'
  | 'payment_processing'
  | 'payment_completed'
  | 'payment_failed'
  | 'binding'
  | 'bound'
  | 'policy_delivered'
  | 'active'
  | 'claim_filed'
  | 'claim_settled'
  | 'expired'
  | 'cancelled';

export type ClaimType = 
  | 'parametric_automatic'
  | 'classical_manual';

export type PaymentMethod = 
  | 'credit_card'
  | 'wire_transfer'
  | 'net_30'
  | 'net_60';

export type Carrier = 
  | 'allianz'
  | 'axa_xl'
  | 'lloyds'
  | 'swiss_re'
  | 'munich_re'
  | 'tokio_marine'
  | 'riskcast'; // For parametric products where RISKCAST is risk bearer

// ============================================================================
// PRODUCT DEFINITIONS
// ============================================================================

export interface InsuranceProduct {
  product_id: string;
  name: string;
  category: InsuranceProductCategory;
  tier: InsuranceProductTier;
  status: ProductStatus;
  
  // Product details
  description: string;
  coverage_type: string; // e.g., 'ICC_A', 'ICC_B', 'ICC_C' for classical
  carrier?: Carrier;
  
  // Pricing
  base_rate?: number; // Base rate as % of cargo value
  pricing_model: 'classical' | 'parametric' | 'hybrid';
  
  // Parametric-specific (if applicable)
  trigger?: ParametricTrigger;
  payout_structure?: PayoutStructure;
  
  // Coverage limits
  min_sum_insured?: number;
  max_sum_insured?: number;
  default_deductible?: number;
  
  // Metadata
  available_regions: string[];
  requires_kyc: boolean;
  requires_license?: boolean;
  documentation_url?: string;
}

export interface ParametricTrigger {
  product_id: string;
  trigger_type: 'weather' | 'port_congestion' | 'natcat' | 'strike' | 'routing';
  
  // Location
  location: {
    port_code?: string;
    coordinates?: { lat: number; lon: number };
    radius_km?: number;
    measurement_station?: string;
  };
  
  // Trigger conditions
  metric: string; // e.g., 'cumulative_rainfall_mm', 'container_dwell_time'
  threshold: number;
  threshold_unit?: string;
  calculation_method?: string;
  data_source: string; // e.g., 'tomorrow_io', 'port_authority_api'
  
  // Observation period
  observation_period?: {
    start_date: Date;
    duration_days: number;
  };
  
  // Verification
  verification_requirement?: string;
  secondary_data_source?: string;
}

export interface PayoutStructure {
  type: 'per_mm_excess' | 'per_day_excess' | 'binary' | 'tiered';
  payout_per_unit?: number; // e.g., $50/mm, $1000/day
  minimum_payout?: number;
  maximum_payout?: number;
  maximum_days?: number; // For per-day products
  franchise_deductible?: number; // Days/units before payout starts
}

// ============================================================================
// QUOTE & PRICING
// ============================================================================

export interface InsuranceQuote {
  quote_id: string;
  product_id: string;
  transaction_id?: string;
  
  // Pricing breakdown
  premium: {
    base_premium: number;
    risk_adjustment: number; // RISKCAST discount/surcharge
    surcharges: Array<{ name: string; amount: number }>;
    total_premium: number;
    currency: string;
  };
  
  // Coverage details
  coverage: {
    sum_insured: number;
    deductible: number;
    coverage_type: string;
    territorial_scope: string;
    effective_date: Date;
    expiry_date: Date;
  };
  
  // Parametric-specific
  trigger?: ParametricTrigger;
  payout_structure?: PayoutStructure;
  expected_payout?: number;
  trigger_probability?: number; // 0-1
  basis_risk_score?: number; // 0-1 (lower = better)
  
  // Pricing transparency
  pricing_breakdown: {
    expected_loss: number;
    load_factor: number;
    administrative_costs: number;
    risk_adjustments: Array<{
      factor: string;
      score: number;
      adjustment: string;
      reasoning: string;
    }>;
  };
  
  // Market comparison
  market_comparison?: {
    industry_avg_rate: number;
    premium_vs_market: number; // % difference
  };
  
  // Validity
  valid_until: Date;
  bind_endpoint?: string;
  
  // Carrier reference (if applicable)
  carrier_quote_id?: string;
  carrier?: Carrier;
}

export interface QuoteComparison {
  quotes: InsuranceQuote[];
  recommended_quote_id?: string;
  comparison_metrics: {
    price: { best: string; worst: string };
    speed: { fastest: string; slowest: string };
    coverage: { best: string; worst: string };
  };
  ai_recommendation?: string;
}

// ============================================================================
// TRANSACTION & POLICY
// ============================================================================

export interface Transaction {
  transaction_id: string;
  state: TransactionState;
  created_at: Date;
  updated_at: Date;
  
  // References
  riskcast_assessment_id: string;
  shipment_reference: string;
  
  // Insurance details
  product: InsuranceProduct;
  coverage_config: CoverageConfig;
  quote: InsuranceQuote;
  
  // Party details
  insured: InsuredParty;
  beneficiary?: BeneficiaryParty;
  
  // Compliance
  kyc_result?: KYCResult;
  sanctions_check?: SanctionsCheck;
  
  // Payment
  payment_method?: PaymentMethod;
  payment_result?: PaymentResult;
  
  // Policy
  policy_number?: string;
  policy_document_url?: string;
  certificate_url?: string;
  
  // Audit
  state_history: StateTransition[];
}

export interface CoverageConfig {
  sum_insured: number;
  deductible: number;
  effective_date: Date;
  expiry_date: Date;
  
  // Parametric-specific
  trigger_threshold?: number;
  payout_per_day?: number;
  max_payout_days?: number;
  max_payout_amount?: number;
  
  // Extensions
  extensions?: string[]; // e.g., ['war_risk', 'strikes']
}

export interface InsuredParty {
  legal_name: string;
  registration_number: string;
  country: string;
  address: {
    street: string;
    city: string;
    state?: string;
    postal_code: string;
    country: string;
  };
  contact: {
    name: string;
    email: string;
    phone: string;
  };
  industry?: string;
  beneficial_owner?: {
    name: string;
    id_type: string;
    id_number: string;
    ownership_pct: number;
  };
}

export interface BeneficiaryParty {
  name: string;
  relationship: string;
  contact: {
    email: string;
    phone: string;
  };
}

export interface KYCResult {
  status: 'approved' | 'requires_manual_review' | 'failed' | 'requires_enhanced_due_diligence';
  risk_score: number; // 0-100
  flags: string[];
  sanctions_matches: number;
  pep_matches: number;
  adverse_media: number;
  approved_at?: Date;
  reason?: string;
  details?: Record<string, any>;
}

export interface SanctionsCheck {
  approved: boolean;
  reason?: string;
  embargoed_countries?: string[];
  export_license_required?: boolean;
}

export interface PaymentResult {
  status: 'completed' | 'failed' | 'requires_action';
  payment_id?: string;
  amount: number;
  currency: string;
  paid_at?: Date;
  payment_method_details?: {
    type: string;
    last4?: string;
  };
  error?: string;
  client_secret?: string; // For 3D Secure
  next_action?: any;
}

export interface StateTransition {
  from_state: TransactionState;
  to_state: TransactionState;
  timestamp: Date;
  reason?: string;
  actor?: string; // 'system' | 'user' | 'carrier'
}

// ============================================================================
// POLICY
// ============================================================================

export interface Policy {
  policy_number: string;
  transaction_id: string;
  product: InsuranceProduct;
  coverage_config: CoverageConfig;
  insured: InsuredParty;
  premium: number;
  effective_date: Date;
  expiry_date: Date;
  status: 'active' | 'expired' | 'cancelled' | 'claim_settled';
  
  // Carrier details (if applicable)
  carrier?: Carrier;
  carrier_policy_id?: string;
  
  // Parametric-specific
  trigger?: ParametricTrigger;
  payout_structure?: PayoutStructure;
  monitoring_enabled: boolean;
  
  // Documents
  policy_document_url?: string;
  certificate_url?: string;
  
  // Container/shipment reference (for parametric monitoring)
  container_reference?: {
    container_number: string;
    bol_number: string;
  };
}

// ============================================================================
// CLAIMS
// ============================================================================

export interface Claim {
  claim_number: string;
  policy_number: string;
  claim_type: ClaimType;
  
  // Incident details (for classical)
  incident_date?: Date;
  loss_type?: string;
  estimated_loss?: number;
  description?: string;
  
  // Trigger details (for parametric)
  trigger_date?: Date;
  trigger_event?: any;
  payout_amount?: number;
  
  // Status
  status: 'submitted' | 'under_review' | 'verified' | 'payout_initiated' | 'paid' | 'rejected';
  
  // Evidence
  evidence?: {
    documents?: Array<{ type: string; url: string }>;
    trigger_data?: any;
    verification?: any;
  };
  
  // Processing
  adjuster_name?: string;
  adjuster_contact?: string;
  carrier_claim_number?: string;
  carrier_claim_id?: string;
  
  // Payout
  paid_at?: Date;
  payment_reference?: string;
  payment_amount?: number;
  
  // Timeline
  created_at: Date;
  updated_at: Date;
}

// ============================================================================
// AI ADVISOR
// ============================================================================

export interface AIAdvisorResponse {
  mode: 'recommendation' | 'explanation' | 'education' | 'compliance';
  confidence: number; // 0-1
  reasoning: string[];
  data_sources: string[];
  disclaimers: string[];
  next_actions: string[];
  
  // Visualizations
  comparison_table?: any;
  visual_breakdown?: any;
  payout_curve?: PayoutCurve;
  scenario_analysis?: ScenarioAnalysis[];
}

export interface PayoutCurve {
  distribution: {
    p0: number;
    p10: number;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
    p99: number;
    max: number;
    expected_payout: number;
    payout_probability: number;
  };
  histogram?: Array<{ bucket: string; count: number }>;
  cumulative_distribution?: Array<{ payout: number; probability: number }>;
}

export interface ScenarioAnalysis {
  scenario_name: string;
  probability: number;
  outcomes: {
    delay_days: number;
    total_cost_without_insurance: number;
    parametric_payout: number;
    net_cost_with_insurance: number;
    financial_benefit: number;
  };
}

// ============================================================================
// CARRIER API
// ============================================================================

export interface CarrierQuoteRequest {
  request_id: string;
  shipment: {
    origin: { port_code: string; country: string };
    destination: { port_code: string; country: string };
    cargo: {
      description: string;
      hs_code?: string;
      declared_value: number;
      currency: string;
      packaging: string;
      container_type?: string;
    };
    voyage: {
      departure_date: string;
      estimated_arrival: string;
      vessel_name?: string;
      imo_number?: string;
    };
  };
  coverage: {
    type: string;
    deductible: number;
    extensions?: string[];
  };
  risk_data: {
    riskcast_score: number;
    riskcast_assessment_id: string;
    risk_factors: Record<string, number>;
  };
}

export interface CarrierQuoteResponse {
  quote_id: string;
  status: 'quoted' | 'declined';
  premium: {
    base_premium: number;
    risk_adjustment: number;
    surcharges: Array<{ name: string; amount: number }>;
    total_premium: number;
    currency: string;
  };
  coverage_details: {
    sum_insured: number;
    deductible: number;
    policy_type: string;
    territorial_scope: string;
  };
  valid_until: string;
  bind_endpoint?: string;
}

export interface CarrierBindRequest {
  quote_id: string;
  payment_method: string;
  insured_party: InsuredParty;
  compliance: {
    kyc_verified: boolean;
    sanctions_screened: boolean;
    beneficial_owner_disclosed: boolean;
  };
}

export interface CarrierBindResponse {
  policy_number: string;
  status: 'bound' | 'failed';
  policy_document_url?: string;
  certificate_of_insurance?: string;
  payment_instructions?: any;
  effective_date: string;
  error?: string;
}

// ============================================================================
// UTILITY & PRICING
// ============================================================================

export interface UtilityParameters {
  wealth: number;
  risk_aversion: number; // 0-10
  shipment_value: number;
  expected_loss: number;
  loss_distribution: number[];
}

export interface OptimalCoverage {
  optimal_coverage_ratio: number; // 0-1
  optimal_limit: number;
  estimated_premium: number;
  certainty_equivalent: number;
  utility_gain: number;
}

// ============================================================================
// MONITORING & WEBHOOKS
// ============================================================================

export interface ParametricMonitoringJob {
  policy_number: string;
  trigger: ParametricTrigger;
  check_frequency: string; // e.g., '1h', '1d'
  expiry_date: Date;
}

export interface TriggerEvaluation {
  triggered: boolean;
  payout_amount?: number;
  trigger_evidence?: any;
  reason?: string;
  escalate_to_manual?: boolean;
}

export interface PortUpdateWebhook {
  container_number: string;
  port_code: string;
  arrival_date: string;
  current_date: string;
  dwell_days: number;
  status: string;
}

export interface WeatherAlertWebhook {
  event_type: string;
  location: { lat: number; lon: number };
  timestamp: string;
  severity: string;
  data: any;
}
