import { AlertCircle, AlertTriangle, Lightbulb, CheckCircle, ChevronRight } from 'lucide-react';
import type { ValidationIssue } from '../../lib/validation';

interface AIAdvisorProps {
  issues: ValidationIssue[];
  onIssueClick: (issue: ValidationIssue) => void;
}

export function AIAdvisor({ issues, onIssueClick }: AIAdvisorProps) {
  const critical = issues.filter(i => i.severity === 'critical');
  const warnings = issues.filter(i => i.severity === 'warning');
  const suggestions = issues.filter(i => i.severity === 'suggestion');

  const renderIssue = (issue: ValidationIssue) => {
    const config = {
      critical: {
        icon: AlertCircle,
        bg: 'bg-red-500/20',
        border: 'border-red-500/30',
        iconColor: 'text-red-400',
        btnColor: 'bg-red-500/30 text-red-300',
      },
      warning: {
        icon: AlertTriangle,
        bg: 'bg-orange-500/20',
        border: 'border-orange-500/30',
        iconColor: 'text-orange-400',
        btnColor: 'bg-orange-500/30 text-orange-300',
      },
      suggestion: {
        icon: Lightbulb,
        bg: 'bg-blue-500/20',
        border: 'border-blue-500/30',
        iconColor: 'text-blue-400',
        btnColor: 'bg-blue-500/30 text-blue-300',
      },
    }[issue.severity];

    const Icon = config.icon;

    return (
      <div
        key={issue.id}
        className={`${config.bg} border ${config.border} rounded-xl p-4 cursor-pointer hover:scale-[1.02] transition-transform`}
        onClick={() => onIssueClick(issue)}
      >
        <div className="flex items-start gap-3">
          <Icon className={`w-5 h-5 ${config.iconColor} flex-shrink-0 mt-0.5`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <span className="text-white font-medium text-sm truncate">{issue.message}</span>
              {issue.action && (
                <button className={`${config.btnColor} px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1`}>
                  {issue.action}
                  <ChevronRight className="w-3 h-3" />
                </button>
              )}
            </div>
            <p className="text-white/50 text-xs mt-1">{issue.detail}</p>
          </div>
        </div>
      </div>
    );
  };

  if (issues.length === 0) {
    return (
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-[20px] p-6 h-full">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
            <CheckCircle className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-white font-medium">AI Advisor</h3>
            <p className="text-white/40 text-xs">Real-time validation</p>
          </div>
        </div>

        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mb-4">
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
          <h4 className="text-white font-medium mb-2">All Clear!</h4>
          <p className="text-white/50 text-sm">No validation issues detected. Your shipment data is ready for analysis.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-[20px] p-6 h-full">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
          <AlertCircle className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-white font-medium">AI Advisor</h3>
          <p className="text-white/40 text-xs">Real-time validation</p>
        </div>
      </div>

      {/* Summary Pills */}
      <div className="flex gap-2 mb-6">
        {critical.length > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-full">
            <AlertCircle className="w-3.5 h-3.5 text-red-400" />
            <span className="text-red-300 text-xs font-medium">{critical.length} Critical</span>
          </div>
        )}
        {warnings.length > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/20 border border-orange-500/30 rounded-full">
            <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />
            <span className="text-orange-300 text-xs font-medium">{warnings.length} Warnings</span>
          </div>
        )}
        {suggestions.length > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-full">
            <Lightbulb className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-blue-300 text-xs font-medium">{suggestions.length} Tips</span>
          </div>
        )}
      </div>

      {/* Issues List */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
        {critical.length > 0 && (
          <>
            <div className="text-red-400/80 text-xs uppercase tracking-wider font-medium">Critical Issues</div>
            {critical.map(renderIssue)}
          </>
        )}
        
        {warnings.length > 0 && (
          <>
            <div className="text-orange-400/80 text-xs uppercase tracking-wider font-medium mt-4">Warnings</div>
            {warnings.map(renderIssue)}
          </>
        )}
        
        {suggestions.length > 0 && (
          <>
            <div className="text-blue-400/80 text-xs uppercase tracking-wider font-medium mt-4">Suggestions</div>
            {suggestions.map(renderIssue)}
          </>
        )}
      </div>
    </div>
  );
}

