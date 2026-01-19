// Minimal stub types for insurance to unblock typechecking after cleanup.
// These are intentionally permissive (all fields optional) and should be
// replaced with full definitions in a proper refactor.
export interface LossDistributionHistogram {
  bucket?: string;
  frequency?: number;
  cumulative?: number;
}

export interface DeductibleRecommendation {
  amount?: number;
  rationale?: string;
}

export interface PremiumLogic {
  loadFactor?: number;
  calculatedPremium?: number;
  marketRate?: number;
  riskcastRate?: number;
  explanation?: string;
}

export interface CoverageRecommendation {
  type?: string;
  clause?: string;
  rationale?: string;
  priority?: 'required' | 'recommended' | 'optional';
}

export interface Rider {
  name?: string;
  cost?: number;
  benefit?: string;
}

export interface Exclusion {
  clause?: string;
  reason?: string;
}

export interface InsuranceUnderwritingData {
  lossDistribution?: {
    histogram?: LossDistributionHistogram[];
    isSynthetic?: boolean;
    dataPoints?: number;
  };
  basisRisk?: {
    score?: number;
    interpretation?: 'low' | 'moderate' | 'high';
    explanation?: string;
  };
  triggerProbabilities?: Array<{ trigger?: string; probability?: number; expectedPayout?: number }>;
  coverageRecommendations?: CoverageRecommendation[];
  premiumLogic?: PremiumLogic;
  riders?: Rider[];
  exclusions?: Exclusion[];
  deductibleRecommendation?: DeductibleRecommendation;
}







