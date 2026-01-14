/**
 * RISKCAST Results v1.0 — Final Type System (single source of truth)
 *
 * Non-negotiables:
 * - Engine-first: UI consumes these types and renders; computation stays in engine/adapter layers.
 * - Trace-driven: key decision elements can carry normalized TraceMeta.
 * - Defensive: fields that can be missing are optional to avoid runtime crashes.
 */

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export type TraceSource = 'rule' | 'model' | 'external';

export interface TraceMeta {
  source: TraceSource;
  evidence: string;
  /** 0..1 confidence (optional) */
  confidence?: number;
  /** Optional reference IDs / URLs */
  refs?: string[];
}

export interface ShipmentData {
  shipmentId: string;
  route: {
    pol: string;
    pod: string;
  };
  carrier: string;
  etd: string;
  eta: string;

  /** Optional shipment attributes (may be absent in partial payloads). */
  incoterm?: string;
  cargoValue?: number;
  dataConfidence?: number; // 0-1
  lastUpdated?: string;

  trace?: TraceMeta;
}

export interface RiskScoreData {
  overallScore: number; // 0-100
  riskLevel: RiskLevel;
  verdict: string;

  /** Optional calibration bounds (not always provided). */
  confidenceLower?: number;
  confidenceUpper?: number;

  /** Overall data confidence (0-1). */
  dataConfidence?: number;

  /** Optional engine metadata. */
  engineVersion?: string;

  trace?: TraceMeta;
}

export type LayerStatus = 'NORMAL' | 'OK' | 'WARNING' | 'ALERT';

export interface LayerData {
  id?: string; // Unique identifier
  name: string;
  score: number; // 0-100
  contribution: number; // 0-100
  weight?: number; // Layer weight in % (0-100)
  category?: string; // TRANSPORT, CARGO, COMMERCIAL, COMPLIANCE, EXTERNAL
  color?: string; // Hex color for visualization
  enabled?: boolean;
  status?: LayerStatus;
  notes?: string;
  description?: string; // Layer description
  confidence?: number; // 0-100 (layer-specific confidence)
  dataSource?: string;
  lastUpdated?: string;
  trace?: TraceMeta;
}

export interface DecisionSignal {
  recommendation: 'BUY' | 'SKIP' | 'OPTIONAL';
  rationale: string;
  providers: Array<{
    name: string;
    premium: number;
    fitScore: number; // 0-1
    trace?: TraceMeta;
  }>;
  trace?: TraceMeta;
}

export interface TimingRecommendation {
  optimalWindow: string;
  riskReduction: number;
  trace?: TraceMeta;
}

export interface FinancialHistogramBin {
  bucket: string;
  probability: number;
  loss: number;
}

export interface FinancialMetrics {
  expectedLoss: number;
  var95: number;
  cvar95: number;
  stdDev: number;
  histogram: FinancialHistogramBin[];
  lossCurve?: Array<{ loss: number; probability: number }>;
  trace?: TraceMeta;
}

export interface AINarrative {
  executiveSummary: string;
  keyInsights: string[];
  actionItems: string[];
  riskDrivers: string[];
  confidenceNotes: string;
  trace?: TraceMeta;
}

export interface TimelineData {
  phase: string;
  status: 'completed' | 'current' | 'pending';
  riskLevel: RiskLevel;
  events: Array<{ time: string; description: string }>;
  confidence?: number; // 0-1
  evidenceSources?: string[];
  trace?: TraceMeta;
}

export type TimelineEvent = TimelineData;

export interface Scenario {
  title: string;
  riskReduction: number;
  costImpact: number;
  description: string;
  feasibility: number; // 0-100
  trace?: TraceMeta;
}

export type ScenarioData = Scenario;

export interface RiskOverTimePoint {
  date: string;
  risk: number;
  phase: string;
  event?: string;
}

export interface ScenarioDataPoint {
  date: string;
  p10: number;
  p50: number;
  p90: number;
  expected: number;
}

export interface DataDomain {
  domain: string;
  confidence: number;
  completeness: number;
  freshness: number;
  notes: string;
  trace?: TraceMeta;
}

export interface RiskDriverAttribution {
  id: string;
  layerName: string;
  label: string;
  contributionPct: number;
  direction: 'increase' | 'decrease';
  confidence?: number; // 0-1 optional
  evidence?: {
    source: string;
    note: string;
    lastUpdated?: string;
  };
  trace?: TraceMeta;
}

/** Trace method is open-ended; keep known values discoverable but allow engine expansion. */
export type TraceMethod =
  | 'aggregation'
  | 'geo_risk_lookup'
  | 'congestion_model'
  | 'weather_model'
  | 'reroute_simulation'
  | 'supplier_risk_model'
  | 'port_congestion_model'
  | 'financial_loss_model'
  | (string & {});

export interface TraceInput {
  name: string;
  value: string;
  source?: string;
  timestamp?: string;
  confidence?: number; // 0-1
  refs?: string[];
}

export interface LayerTraceStep {
  stepId: string;
  method: TraceMethod;
  inputs?: TraceInput[];
  output?: unknown;
  summary: string;
  /** Optional step-level evidence as normalized trace meta */
  evidence?: TraceMeta;
}

export interface LayerTrace {
  layerName: string;
  steps: LayerTraceStep[];
  /** Optional: sensitivity drivers at this layer */
  sensitivity?: Array<{ name: string; impact: number }>;
  /** Optional: normalized trace meta for the layer */
  trace?: TraceMeta;
}

export interface RiskAnalysisResult {
  shipment: ShipmentData;
  riskScore: RiskScoreData;
  layers: LayerData[];

  /** Optional decision outputs (may be missing for partial analyses). */
  decisionSignal?: DecisionSignal;
  timing?: TimingRecommendation;
  scenarios?: Scenario[];

  /** Optional evidence modules */
  financial?: FinancialMetrics | null;
  aiNarrative?: AINarrative;

  /**
   * Timeline is an array of events.
   * (array vs object mismatch fixed)
   */
  timeline?: TimelineData[];

  riskOverTime?: RiskOverTimePoint[];
  riskScenarioProjections?: ScenarioDataPoint[];
  dataReliability?: DataDomain[];

  // Traceability extensions
  drivers?: RiskDriverAttribution[];
  traces?: Record<string, LayerTrace>; // key = layerName
}

export interface RiskFactor {
  name: string;
  description: string;
  impact: number;
}

export interface RiskAnalysisDetails {
  factors: RiskFactor[];
  mitigation: string[];
  riskContributions?: Array<{ category: string; value: number }>;
  sensitivity?: Array<{ variable: string; impact: number }>;
  confidenceBreakdown?: Array<{ component: string; score: number; notes: string }>;
}

export interface HistoricalRiskData {
  date: string;
  score: number;
  keyEvents?: string[];
}

export interface PredictionRange {
  lower: number;
  upper: number;
  median: number;
  confidence: number;
}

export interface RiskScenario {
  scenario: string;
  probability: number;
  impact: number;
}

export interface RiskModelMetadata {
  modelVersion: string;
  lastUpdated: string;
  dataSources: string[];
  assumptions: string[];
  limitations: string[];
}

export interface RiskAnalysisReport {
  summary: string;
  detailedAnalysis: RiskAnalysisDetails;
  historicalData: HistoricalRiskData[];
  prediction: PredictionRange;
  scenarios: RiskScenario[];
  metadata: RiskModelMetadata;
}




