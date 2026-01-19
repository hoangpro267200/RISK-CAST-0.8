import { ArrowLeft, Save, ChevronRight } from 'lucide-react';

interface HeaderActionsProps {
  onBack: () => void;
  onSaveDraft: () => void;
  onRunAnalysis: () => void;
  canAnalyze: boolean;
  isAnalyzing: boolean;
  // Optional: for mobile collapse
  showLabels?: boolean;
}

/**
 * Header Actions Component
 * 
 * Moves Back/Save Draft/Run Analysis from footer to header
 * Premium UI with consistent spacing and responsive design
 */
export function HeaderActions({
  onBack,
  onSaveDraft,
  onRunAnalysis,
  canAnalyze,
  isAnalyzing,
  showLabels = true,
}: HeaderActionsProps) {
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

      {/* Run Analysis Button - Primary CTA */}
      <button
        onClick={onRunAnalysis}
        disabled={!canAnalyze || isAnalyzing}
        className={`
          px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all text-sm
          ${canAnalyze && !isAnalyzing
            ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50 hover:scale-[1.02]'
            : 'bg-white/10 text-white/40 cursor-not-allowed'
          }
        `}
        aria-label="Run analysis"
      >
        {isAnalyzing ? (
          <>
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <span className="hidden sm:inline">Analyzing...</span>
          </>
        ) : (
          <>
            <span className="hidden sm:inline">Run Analysis</span>
            <span className="sm:hidden">Analyze</span>
            <ChevronRight className="w-4 h-4" />
          </>
        )}
      </button>
    </div>
  );
}
