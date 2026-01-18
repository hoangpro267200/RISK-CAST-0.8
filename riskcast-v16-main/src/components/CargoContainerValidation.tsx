/**
 * Cargo-Container Validation Component
 * 
 * Validates cargo type against container type and shows warnings for mismatches.
 */

import React from 'react';
import { GlassCard } from './GlassCard';
import type { CargoContainerValidation } from '../types/logisticsTypes';
import { Package, CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react';

interface CargoContainerValidationProps {
  validation: CargoContainerValidation;
  cargoType: string;
  containerType: string;
}

// Validation rules
const VALIDATION_RULES: Record<string, { valid: string[]; invalid: string[]; message: string }> = {
  'perishable': {
    valid: ['20RF', '40RH', '40RF', 'REEFER'],
    invalid: ['20DV', '40DV', 'OT', 'FR'],
    message: 'Perishable cargo requires refrigerated container',
  },
  'electronics': {
    valid: ['20DV', '40DV', '40HC', 'DRY'],
    invalid: ['OT', 'FR', 'TANK', 'REEFER'],
    message: 'Electronics require dry container with climate control',
  },
  'liquids': {
    valid: ['TANK', 'ISO-TANK'],
    invalid: ['20DV', '40DV', 'DRY'],
    message: 'Liquid cargo requires tank container',
  },
  'oversized': {
    valid: ['FR', 'OT', '40OT', 'FLATRACK'],
    invalid: ['20DV', '40DV', 'STANDARD'],
    message: 'Oversized cargo requires flat rack or open top',
  },
  'hazmat': {
    valid: ['HAZCHEM', 'TANK', 'HAZMAT'],
    invalid: ['STANDARD', 'DRY'],
    message: 'Hazardous materials require specialized container',
  },
};

// Get cargo category from cargo type
const getCargoCategory = (cargoType: string): string | null => {
  const lower = cargoType.toLowerCase();
  if (lower.includes('perishable') || lower.includes('food') || lower.includes('frozen') || lower.includes('seafood')) {
    return 'perishable';
  }
  if (lower.includes('electronic') || lower.includes('device') || lower.includes('computer')) {
    return 'electronics';
  }
  if (lower.includes('liquid') || lower.includes('oil') || lower.includes('chemical')) {
    return 'liquids';
  }
  if (lower.includes('oversized') || lower.includes('machinery') || lower.includes('equipment')) {
    return 'oversized';
  }
  if (lower.includes('hazmat') || lower.includes('hazardous') || lower.includes('dangerous')) {
    return 'hazmat';
  }
  return null;
};

export const CargoContainerValidation: React.FC<CargoContainerValidationProps> = ({
  validation,
  cargoType,
  containerType,
}) => {
  // Defensive guard
  if (!cargoType || !containerType) {
    return (
      <GlassCard>
        <div className="text-center py-12 text-white/60">
          <Package className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm font-medium mb-2">Cargo or container type missing</p>
          <p className="text-xs text-white/40 max-w-md mx-auto">
            Please provide cargo type and container type for validation.
          </p>
        </div>
      </GlassCard>
    );
  }

  const cargoCategory = getCargoCategory(cargoType);
  const rule = cargoCategory ? VALIDATION_RULES[cargoCategory] : null;
  const containerUpper = containerType.toUpperCase();
  const isValid = validation.isValid;
  const hasWarnings = validation.warnings.length > 0;

  // Determine if there's a mismatch based on rules
  const isMismatch = rule && (
    rule.invalid.some(inv => containerUpper.includes(inv)) ||
    !rule.valid.some(val => containerUpper.includes(val))
  );

  return (
    <GlassCard>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
          <Package className="w-5 h-5 text-blue-400" />
          <span>Cargo-Container Validation</span>
        </h3>
        <p className="text-sm text-white/60">
          Validates cargo type compatibility with container type
        </p>
      </div>

      {/* Status Display */}
      <div className={`mb-6 p-6 rounded-xl border ${
        isValid && !isMismatch
          ? 'bg-emerald-500/10 border-emerald-500/30'
          : 'bg-red-500/10 border-red-500/30'
      }`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {isValid && !isMismatch ? (
              <CheckCircle2 className="w-12 h-12 text-emerald-400" />
            ) : (
              <XCircle className="w-12 h-12 text-red-400" />
            )}
            <div>
              <div className="text-sm text-white/60 mb-1">Cargo Type</div>
              <div className="text-lg font-bold text-white">{cargoType}</div>
            </div>
            <div className="text-white/30">→</div>
            <div>
              <div className="text-sm text-white/60 mb-1">Container Type</div>
              <div className="text-lg font-bold text-white">{containerType}</div>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-full border ${
            isValid && !isMismatch
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
              : 'bg-red-500/20 text-red-400 border-red-500/30'
          }`}>
            <span className="text-sm font-semibold">
              {isValid && !isMismatch ? 'VALID' : 'MISMATCH'}
            </span>
          </div>
        </div>

        {/* Mismatch Warning */}
        {isMismatch && rule && (
          <div className="pt-4 border-t border-red-500/20">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-400 mb-2">CRITICAL WARNING</h4>
                <p className="text-sm text-white/80 mb-3">
                  {cargoType} requires a {rule.valid.join(' or ')} container.
                  A {containerType} cannot maintain required conditions.
                </p>
                <div className="text-xs text-white/60">
                  <p className="font-semibold mb-1">Recommended Containers:</p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    {rule.valid.slice(0, 2).map((val, idx) => (
                      <li key={idx}>{val} — {val.includes('RF') || val.includes('RH') ? 'Maintains temperature control' : 'Suitable for cargo type'}</li>
                    ))}
                  </ul>
                </div>
                <p className="text-xs text-red-400 mt-3 font-semibold">
                  Risk Impact: Using incorrect container increases risk by 95%.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Additional Checks */}
      {cargoCategory === 'electronics' && (
        <div className="mb-6 space-y-3">
          <h4 className="text-sm font-semibold text-white mb-3">Additional Checks for Electronics</h4>
          <div className="space-y-2">
            <div className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
              <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-sm font-medium text-white mb-1">Temperature sensitivity: HIGH</div>
                <div className="text-xs text-white/60">Recommendation: Ensure desiccant packs are included</div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
              <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-sm font-medium text-white mb-1">Shock sensitivity: HIGH</div>
                <div className="text-xs text-white/60">Recommendation: Use shock indicators</div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
              <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-sm font-medium text-white mb-1">Moisture risk: MEDIUM</div>
                <div className="text-xs text-white/60">Recommendation: Vacuum pack + humidity cards</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Validation Warnings */}
      {hasWarnings && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-amber-400 mb-3">Validation Warnings</h4>
          {validation.warnings.map((warning, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border ${
                warning.severity === 'error'
                  ? 'bg-red-500/10 border-red-500/20'
                  : 'bg-amber-500/10 border-amber-500/20'
              }`}
            >
              <div className="flex items-start gap-2">
                <AlertTriangle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
                  warning.severity === 'error' ? 'text-red-400' : 'text-amber-400'
                }`} />
                <div className="flex-1">
                  <div className="text-xs font-medium text-white/80">{warning.message}</div>
                  <div className="text-xs text-white/50 mt-1">Code: {warning.code}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  );
};
