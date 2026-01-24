/**
 * Type Definitions
 * Shared types for RISKCAST V3 frontend
 */

// Risk Assessment Types
export interface RiskAssessment {
  id: string;
  tenant_id: string;
  status: string;
  input_schema_version: string;
  input_hash: string;
  created_at: string;
  updated_at: string;
}

export interface RiskRun {
  id: string;
  risk_assessment_id: string;
  status: 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
  result_json?: {
    overall_risk_score: number;
    distribution_summary: {
      mean: number;
      var_95: number;
      cvar_95: number;
    };
    layer_contributions: Array<{
      layer_name: string;
      contribution: number;
    }>;
  };
  error_json?: any;
  engine_version?: string;
  model_version_id?: string;
  seed?: number;
  iterations?: number;
  result_hash?: string;
  created_at: string;
  updated_at: string;
}

// Underwriting Types
export interface UnderwritingSubmission {
  id: string;
  tenant_id: string;
  status: 'DRAFT' | 'SUBMITTED' | 'UNDER_REVIEW' | 'QUOTED' | 'DECLINED' | 'BOUND';
  risk_assessment_id: string;
  risk_run_id?: string;
  evidence_bundle_id?: string;
  product_type?: string;
  created_at: string;
  updated_at: string;
}

export interface UnderwritingDecision {
  id: string;
  submission_id: string;
  decision: string;
  terms_json?: any;
  notes?: string;
  created_at: string;
}

export interface Policy {
  id: string;
  policy_number: string;
  status: string;
  effective_from: string;
  effective_to: string;
  created_at: string;
}

// Claims Types
export interface Claim {
  id: string;
  tenant_id: string;
  policy_id: string;
  status: string;
  fnol_json?: any;
  created_at: string;
  updated_at: string;
}

export interface ClaimEvent {
  id: string;
  claim_id: string;
  event_type: string;
  from_state?: string;
  to_state: string;
  created_at: string;
}

// Evidence Types
export interface EvidenceBundle {
  id: string;
  tenant_id: string;
  schema_version: string;
  bundle_hash: string;
  created_at: string;
}

// Model Versioning Types
export interface ModelVersion {
  id: string;
  tenant_id?: string;
  scope: string;
  name: string;
  status: string;
  immutable_hash?: string;
  created_at: string;
}

// Parametric Types
export interface TriggerDefinition {
  id: string;
  tenant_id: string;
  type: string;
  version: number;
  status: string;
  params_json: any;
  immutable_hash?: string;
}

export interface OracleEvent {
  id: string;
  tenant_id?: string;
  source: string;
  captured_at: string;
  payload_json: any;
}

export interface TriggerEvent {
  id: string;
  trigger_definition_id: string;
  policy_id: string;
  status: string;
  matched_at?: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}
