/**
 * Exclusions Disclosure Component
 * 
 * Lists potential policy exclusions with mitigation recommendations.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { InsuranceExclusion } from '../types/insuranceTypes';
import { AlertTriangle, Shield, Info } from 'lucide-react';

interface ExclusionsDisclosureProps {
  exclusions: InsuranceExclusion[];
}

export const ExclusionsDisclosure: React.FC<ExclusionsDisclosureProps> = ({ exclusions }) => {
  // Defensive guard
  if (!exclusions || exclusions.length === 0) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Shield className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Exclusions data unavailable</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            The analysis could not determine potential exclusions. Please re-run analysis with complete data.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <span>Potential Policy Exclusions</span>
        </h3>
        <p className="text-sm text-white/60">
          Review these exclusions before finalizing coverage
        </p>
      </div>

      <div className="space-y-4">
        {exclusions.map((exclusion, idx) => (
          <div
            key={idx}
            className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/20"
          >
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-amber-400 mb-2">{exclusion.clause}</h4>
                <p className="text-sm text-white/80">{exclusion.reason}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* General Note */}
      <div className="mt-6 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-white/80">
            <p>
              <strong className="text-white">Note:</strong> Review your policy document carefully 
              for all exclusions. Some exclusions may be waived with additional documentation or 
              premium adjustments.
            </p>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
