import { ChevronRight, AlertCircle, AlertTriangle, Save, Clock, ArrowLeft } from 'lucide-react';
import type { ShipmentData, ModulesState } from './types';
import { getValidationIssues } from '../../lib/validation';

interface ActionFooterProps {
  data: ShipmentData;
  modules: ModulesState;
  onRunAnalysis: () => void;
  onSaveDraft: () => void;
  onBack: () => void;
  lastSaved: Date;
  isAnalyzing: boolean;
}

export function ActionFooter({ data, modules, onRunAnalysis, onSaveDraft, onBack, lastSaved, isAnalyzing }: ActionFooterProps) {
  const issues = getValidationIssues(data);
  const criticalCount = issues.filter(i => i.severity === 'critical').length;
  const warningCount = issues.filter(i => i.severity === 'warning').length;

  // Calculate completeness based on 19 required fields
  const requiredFields = [
    { value: data.trade.pol, label: 'POL' },
    { value: data.trade.pod, label: 'POD' },
    { value: data.trade.mode, label: 'Mode' },
    { value: data.trade.container_type, label: 'Container' },
    { value: data.trade.etd, label: 'ETD' },
    { value: data.trade.transit_time_days, label: 'Transit Time' },
    { value: data.cargo.cargo_type, label: 'Cargo Type' },
    { value: data.cargo.hs_code, label: 'HS Code' },
    { value: data.cargo.packages, label: 'Packages' },
    { value: data.cargo.gross_weight_kg, label: 'Gross Weight' },
    { value: data.cargo.volume_cbm, label: 'Volume' },
    { value: data.seller.company, label: 'Seller Company' },
    { value: data.seller.email, label: 'Seller Email' },
    { value: data.seller.phone, label: 'Seller Phone' },
    { value: data.seller.country, label: 'Seller Country' },
    { value: data.buyer.company, label: 'Buyer Company' },
    { value: data.buyer.email, label: 'Buyer Email' },
    { value: data.buyer.phone, label: 'Buyer Phone' },
    { value: data.buyer.country, label: 'Buyer Country' },
  ];

  const filledCount = requiredFields.filter(f => f.value && f.value !== 0).length;
  const completeness = Math.round((filledCount / requiredFields.length) * 100);
  const enabledModules = Object.values(modules).filter(Boolean).length;

  // Allow analysis even with some issues - just warn user
  const canAnalyze = completeness >= 20; // Allow analysis with partial data for testing

  const getTimeSince = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 backdrop-blur-xl bg-[#0a1628]/90 border-t border-white/10">
      <div className="px-12 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Status Pills */}
          <div className="flex items-center gap-4">
            {/* Completeness */}
            <div className="flex items-center gap-3">
              <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all ${
                    completeness === 100 
                      ? 'bg-green-500' 
                      : completeness >= 80 
                        ? 'bg-cyan-500' 
                        : 'bg-orange-500'
                  }`}
                  style={{ width: `${completeness}%` }}
                />
              </div>
              <span className="text-white/70 text-sm">{completeness}% Complete</span>
            </div>

            {/* Issues */}
            <div className="flex items-center gap-2">
              {criticalCount > 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-full">
                  <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                  <span className="text-red-300 text-xs font-medium">{criticalCount} Critical</span>
                </div>
              )}
              {warningCount > 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/20 border border-orange-500/30 rounded-full">
                  <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />
                  <span className="text-orange-300 text-xs font-medium">{warningCount} Warnings</span>
                </div>
              )}
              {criticalCount === 0 && warningCount === 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 border border-green-500/30 rounded-full">
                  <span className="text-green-300 text-xs font-medium">✓ All Clear</span>
                </div>
              )}
            </div>

            {/* Modules */}
            <div className="text-white/40 text-sm flex items-center gap-1.5">
              <span>{enabledModules} modules</span>
              <span className="text-white/20">•</span>
              <Clock className="w-3.5 h-3.5" />
              <span>Saved {getTimeSince(lastSaved)}</span>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="px-4 py-2.5 border border-white/20 rounded-xl text-white/70 hover:text-white hover:border-white/40 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>

            <button
              onClick={onSaveDraft}
              className="px-4 py-2.5 border border-white/20 rounded-xl text-white/70 hover:text-white hover:border-white/40 transition-all flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              Save Draft
            </button>

            <button
              onClick={onRunAnalysis}
              disabled={!canAnalyze || isAnalyzing}
              className={`
                px-6 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all
                ${canAnalyze && !isAnalyzing
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50'
                  : 'bg-white/10 text-white/40 cursor-not-allowed'
                }
              `}
            >
              {isAnalyzing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  Run Analysis
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

