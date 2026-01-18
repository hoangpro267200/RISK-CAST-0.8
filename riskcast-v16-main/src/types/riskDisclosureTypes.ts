/**
 * Risk Disclosure Types
 * 
 * Types for latent risks, tail events, thresholds, and actionable mitigations
 */

export interface LatentRisk {
  id: string;
  name: string;
  category: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  probability: number;  // 0-1
  impact: string;
  mitigation: string;
}

export interface TailEvent {
  event: string;
  probability: number;  // 0-1
  potentialLoss: number;
  historicalPrecedent: string | null;
}

export interface RiskThresholds {
  p95: number;
  p99: number;
  maxLoss: number;
}

export interface ActionableMitigation {
  action: string;
  cost: number;
  riskReductionPercent: number;
  paybackPeriod: string;
}

export interface RiskDisclosureData {
  latentRisks: LatentRisk[];
  tailEvents: TailEvent[];
  thresholds: RiskThresholds;
  actionableMitigations: ActionableMitigation[];
}
