/**
 * Insurance Underwriting Types
 * 
 * Types for insurance underwriting data, coverage recommendations, and premium logic
 */

export interface LossDistributionHistogram {
  bucket: string;        // "$0-$5K", "$5K-$10K", etc.
  frequency: number;     // Count or percentage
  cumulative: number;     // CDF value
}

export interface LossDistributionData {
  histogram: LossDistributionHistogram[];
  isSynthetic: boolean;
  dataPoints: number;
}

export interface BasisRiskData {
  score: number;             // 0-1
  interpretation: 'low' | 'moderate' | 'high';
  explanation: string;
}

export interface TriggerProbability {
  trigger: string;           // e.g., "delay > 7 days"
  probability: number;       // 0-1
  expectedPayout: number;
}

export interface CoverageRecommendation {
  type: string;              // e.g., "ICC(A)"
  clause: string;
  rationale: string;
  priority: 'required' | 'recommended' | 'optional';
}

export interface PremiumLogicData {
  expectedLoss: number;
  loadFactor: number;
  calculatedPremium: number;
  marketRate: number;
  riskcastRate: number;
  explanation: string;
}

export interface InsuranceRider {
  name: string;
  cost: number;
  benefit: string;
}

export interface InsuranceExclusion {
  clause: string;
  reason: string;
}

export interface DeductibleRecommendation {
  amount: number;
  rationale: string;
}

export interface InsuranceUnderwritingData {
  lossDistribution: LossDistributionData;
  basisRisk: BasisRiskData;
  triggerProbabilities: TriggerProbability[];
  coverageRecommendations: CoverageRecommendation[];
  premiumLogic: PremiumLogicData;
  riders: InsuranceRider[];
  exclusions: InsuranceExclusion[];
  deductibleRecommendation: DeductibleRecommendation;
}
