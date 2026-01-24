import { ArrowLeft, Save, ChevronRight, AlertTriangle } from 'lucide-react';
import { useState } from 'react';

interface HeaderActionsProps {
  onBack: () => void;
  onSaveDraft: () => void;
  onRunAnalysis: () => void;
  canAnalyze: boolean;
  isAnalyzing: boolean;
  // Optional: for mobile collapse
  showLabels?: boolean;
  // Optional: reason why analysis is blocked
  blockReason?: string;
}

/**
 * Header Actions Component
 * 
 * Moves Back/Save Draft/Run Analysis from footer to header
 * Premium UI with consistent spacing and responsive design
 * Shows validation feedback when analysis is blocked
 */
export function HeaderActions({
  onBack,
  onSaveDraft,
  onRunAnalysis,
  canAnalyze,
  isAnalyzing,
  showLabels = true,
  blockReason,
}: HeaderActionsProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  
  return (
    <div className="flex items-center gap-2">
      {/* Back Button - Secondary */}
      <button
        onClick={onBack}
        className="px-3 py-2 border border-white/20 rounded-lg text-white/70 hover:text-white hover:border-white/40 transition-all flex items-center gap-2 text-sm"
        aria-label="Go back"
      >
        <ArrowLeft className="w-4 h-4" />
        {showLabels && <span className="hidden sm:inline">Back</span>}
      </button>

      {/* Save Draft Button - Secondary */}
      <button
        onClick={onSaveDraft}
        className="px-3 py-2 border border-white/20 rounded-lg text-white/70 hover:text-white hover:border-white/40 transition-all flex items-center gap-2 text-sm"
        aria-label="Save draft"
      >
        <Save className="w-4 h-4" />
        {showLabels && <span className="hidden sm:inline">Save Draft</span>}
      </button>

      {/* Run Analysis Button - Primary CTA with validation tooltip */}
      <div className="relative">
        <button
          onClick={canAnalyze ? onRunAnalysis : undefined}
          onMouseEnter={() => !canAnalyze && setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          disabled={!canAnalyze || isAnalyzing}
          className={`
            px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all text-sm
            ${canAnalyze && !isAnalyzing
              ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50 hover:scale-[1.02]'
              : 'bg-white/10 text-white/40 cursor-not-allowed'
            }
          `}
          aria-label={canAnalyze ? 'Run analysis' : `Cannot analyze: ${blockReason || 'Missing required data'}`}
        >
          {isAnalyzing ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span className="hidden sm:inline">Analyzing...</span>
            </>
          ) : !canAnalyze ? (
            <>
              <AlertTriangle className="w-4 h-4 text-orange-400" />
              <span className="hidden sm:inline">Complete Data First</span>
              <span className="sm:hidden">Incomplete</span>
            </>
          ) : (
            <>
              <span className="hidden sm:inline">Run Analysis</span>
              <span className="sm:hidden">Analyze</span>
              <ChevronRight className="w-4 h-4" />
            </>
          )}
        </button>
        
        {/* Validation Tooltip */}
        {showTooltip && !canAnalyze && (
          <div className="absolute top-full right-0 mt-2 w-72 p-3 bg-slate-900/95 backdrop-blur-xl border border-orange-500/30 rounded-xl shadow-2xl z-50">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-orange-300 mb-1">Cannot Run Analysis</div>
                <div className="text-xs text-white/70">
                  {blockReason || 'Please complete all required fields before running risk analysis. Check the validation warnings for details.'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
