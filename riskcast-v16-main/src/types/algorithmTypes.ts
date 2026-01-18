/**
 * Algorithm Explainability Types
 * 
 * Types for FAHP, TOPSIS, and Monte Carlo algorithm explanations
 */

export interface FAHPWeight {
  layerId: string;
  layerName: string;
  weight: number;          // 0-1
  contributionPercent: number; // 0-100
}

export interface FAHPData {
  weights: FAHPWeight[];
  consistencyRatio: number;  // < 0.1 is acceptable
  consistencyStatus: 'acceptable' | 'review_needed';
}

export interface TOPSISAlternative {
  id: string;
  name: string;
  positiveIdealDistance: number;  // D+
  negativeIdealDistance: number;  // D-
  closenessCoefficient: number;   // C* = D- / (D+ + D-)
  rank: number;
}

export interface TOPSISData {
  alternatives: TOPSISAlternative[];
  methodology: string;       // Explanation text
}

export interface MonteCarloPercentiles {
  p10: number;
  p50: number;
  p90: number;
  p95: number;
  p99: number;
}

export interface MonteCarloData {
  nSamples: number;
  distributionType: string;
  parameters: Record<string, number>;
  percentiles: MonteCarloPercentiles;
  methodology: string;
}

export interface AlgorithmExplainabilityData {
  fahp: FAHPData;
  topsis: TOPSISData;
  monteCarlo: MonteCarloData;
}
