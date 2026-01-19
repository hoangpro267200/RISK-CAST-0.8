/**
 * Risk Disclosure Panel
 * 
 * Houses all risk disclosure components: latent risks, tail events, and actionable mitigations.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import { LatentRisksTable } from './LatentRisksTable';
import { TailEventsExplainer } from './TailEventsExplainer';
import { ActionableMitigations } from './ActionableMitigations';
import type { RiskDisclosureData } from '../types/riskDisclosureTypes';
import { Shield, Info } from 'lucide-react';

interface RiskDisclosurePanelProps {
  riskDisclosure: RiskDisclosureData;
}

export const RiskDisclosurePanel: React.FC<RiskDisclosurePanelProps> = ({ riskDisclosure }) => {
  // Defensive guard
  if (!riskDisclosure) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Shield className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Risk disclosure data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not provide risk disclosure data. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <GlassCard variant="hero" className="border-2 border-amber-500/20">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center flex-shrink-0">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-2">Risk Disclosure</h2>
            <p className="text-white/70 text-sm mb-3">
              Comprehensive disclosure of latent risks, tail events, thresholds, and actionable mitigations. 
              This transparency enables informed decision-making and risk management.
            </p>
            <div className="flex items-center gap-2 text-xs text-white/50">
              <Info className="w-4 h-4" />
              <span>Review these risks before finalizing shipping and insurance decisions.</span>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Latent Risks */}
      {riskDisclosure.latentRisks.length > 0 && (
        <LatentRisksTable latentRisks={riskDisclosure.latentRisks} />
      )}

      {/* Tail Events */}
      <TailEventsExplainer
        tailEvents={riskDisclosure.tailEvents}
        thresholds={riskDisclosure.thresholds}
      />

      {/* Actionable Mitigations */}
      {riskDisclosure.actionableMitigations.length > 0 && (
        <ActionableMitigations mitigations={riskDisclosure.actionableMitigations} />
      )}
    </div>
  );
};
