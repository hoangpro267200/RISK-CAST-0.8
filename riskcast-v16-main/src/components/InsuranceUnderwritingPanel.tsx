/**
 * Insurance Underwriting Panel
 * 
 * Houses all insurance underwriting components for comprehensive insurance analysis.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import { LossDistributionHistogram } from './LossDistributionHistogram';
import { BasisRiskScore } from './BasisRiskScore';
import { TriggerProbabilityTable } from './TriggerProbabilityTable';
import { CoverageRecommendations } from './CoverageRecommendations';
import { PremiumLogicExplainer } from './PremiumLogicExplainer';
import { ExclusionsDisclosure } from './ExclusionsDisclosure';
import { DeductibleRecommendation } from './DeductibleRecommendation';
import type { InsuranceUnderwritingData } from '../types/insuranceTypes';
import { Shield, Info } from 'lucide-react';

interface InsuranceUnderwritingPanelProps {
  insuranceData: InsuranceUnderwritingData;
  cargoValue: number;
  expectedLoss: number;
  p95: number;
  p99: number;
}

export const InsuranceUnderwritingPanel: React.FC<InsuranceUnderwritingPanelProps> = ({
  insuranceData,
  cargoValue,
  expectedLoss,
  p95,
  p99,
}) => {
  // Defensive guard
  if (!insuranceData) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Shield className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Insurance underwriting data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not provide insurance underwriting data. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <GlassCard variant="hero" className="border-2 border-blue-500/20">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-2">Insurance Underwriting Analysis</h2>
            <p className="text-white/70 text-sm mb-3">
              Comprehensive insurance analysis for underwriting decisions. Includes loss distribution, 
              basis risk assessment, trigger probabilities, coverage recommendations, and premium calculation logic.
            </p>
            <div className="flex items-center gap-2 text-xs text-white/50">
              <Info className="w-4 h-4" />
              <span>This data enables insurance underwriters to quote policies within 5 minutes.</span>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Loss Distribution Histogram */}
      <LossDistributionHistogram
        lossDistribution={insuranceData.lossDistribution}
        expectedLoss={expectedLoss}
        p95={p95}
        p99={p99}
      />

      {/* Basis Risk Score */}
      <BasisRiskScore basisRisk={insuranceData.basisRisk} />

      {/* Trigger Probability Table */}
      {insuranceData.triggerProbabilities.length > 0 && (
        <TriggerProbabilityTable triggers={insuranceData.triggerProbabilities} />
      )}

      {/* Coverage Recommendations */}
      {insuranceData.coverageRecommendations.length > 0 && (
        <CoverageRecommendations recommendations={insuranceData.coverageRecommendations} />
      )}

      {/* Premium Logic Explainer */}
      <PremiumLogicExplainer premiumLogic={insuranceData.premiumLogic} />

      {/* Deductible Recommendation */}
      <DeductibleRecommendation
        recommendation={insuranceData.deductibleRecommendation}
        cargoValue={cargoValue}
        expectedLoss={expectedLoss}
      />

      {/* Exclusions Disclosure */}
      {insuranceData.exclusions.length > 0 && (
        <ExclusionsDisclosure exclusions={insuranceData.exclusions} />
      )}
    </div>
  );
};
