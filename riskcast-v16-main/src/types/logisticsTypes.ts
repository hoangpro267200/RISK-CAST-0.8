/**
 * Logistics Realism Types
 * 
 * Types for cargo-container validation, route seasonality, and port congestion
 */

export interface CargoContainerWarning {
  code: string;
  message: string;
  severity: 'warning' | 'error';
}

export interface CargoContainerValidation {
  isValid: boolean;
  warnings: CargoContainerWarning[];
}

export interface ClimaticIndex {
  name: string;
  value: number;
  interpretation: string;
}

export interface RouteSeasonalityFactor {
  factor: string;
  impact: string;
}

export interface RouteSeasonalityData {
  season: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  factors: RouteSeasonalityFactor[];
  climaticIndices: ClimaticIndex[];
}

export interface PortCongestionData {
  name: string;
  dwellTime: number;
  normalDwellTime: number;
  status: string;
}

export interface DelayProbabilities {
  p7days: number;   // Probability of delay > 7 days
  p14days: number;  // Probability of delay > 14 days
  p21days: number;  // Probability of delay > 21 days
}

export interface PackagingRecommendation {
  item: string;
  cost: number;
  riskReduction: number;  // Percentage
  rationale: string;
}

export interface LogisticsRealismData {
  cargoContainerValidation: CargoContainerValidation;
  routeSeasonality: RouteSeasonalityData;
  portCongestion: {
    pol: PortCongestionData;
    pod: PortCongestionData;
    transshipments: PortCongestionData[];
  };
  delayProbabilities: DelayProbabilities;
  packagingRecommendations: PackagingRecommendation[];
}
