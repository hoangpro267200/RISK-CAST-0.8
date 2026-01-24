/**
 * IntegrityPanel - Shows analysis integrity validation issues
 * 
 * Displays when analysis data fails integrity checks:
 * - Provenance issues (missing run ID, mock data)
 * - Consistency issues (invalid metrics, broken quantiles)
 * 
 * Provides clear feedback and retry action.
 */

import { AlertTriangle, XCircle, Info, RefreshCw, ChevronDown, ChevronUp, Shield } from 'lucide-react';
import { useState } from 'react';
import type { AnalysisIntegrityInfo } from '@/types/resultsViewModel';

interface IntegrityPanelProps {
  integrity: AnalysisIntegrityInfo;
  onRetry?: () => void;
  isLoading?: boolean;
}

export function IntegrityPanel({ integrity, onRetry, isLoading }: IntegrityPanelProps) {
  const [expanded, setExpanded] = useState(false);
  
  const errorCount = integrity.issues.filter(i => i.severity === 'error').length;
  const warningCount = integrity.issues.filter(i => i.severity === 'warning').length;
  const infoCount = integrity.issues.filter(i => i.severity === 'info').length;
  
  // Determine panel styling based on status
  const panelStyles = {
    invalid: 'bg-red-500/10 border-red-500/40',
    warning: 'bg-amber-500/10 border-amber-500/40',
    ok: 'bg-green-500/10 border-green-500/40',
  };
  
  const iconColors = {
    invalid: 'text-red-400',
    warning: 'text-amber-400',
    ok: 'text-green-400',
  };
  
  const StatusIcon = integrity.status === 'invalid' ? XCircle : 
                     integrity.status === 'warning' ? AlertTriangle : Shield;
  
  return (
    <div className={`rounded-xl border ${panelStyles[integrity.status]} p-4`}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <StatusIcon className={`w-6 h-6 ${iconColors[integrity.status]}`} />
          <div>
            <h3 className="text-white font-semibold">
              {integrity.status === 'invalid' && 'Analysis Data Invalid'}
              {integrity.status === 'warning' && 'Analysis Data Incomplete'}
              {integrity.status === 'ok' && 'Analysis Data Verified'}
            </h3>
            <p className="text-white/60 text-sm">
              {integrity.status === 'invalid' && 'Cannot display results due to data integrity issues.'}
              {integrity.status === 'warning' && 'Some sections may be unavailable due to missing data.'}
              {integrity.status === 'ok' && 'All data passed integrity checks.'}
            </p>
          </div>
        </div>
        
        {/* Retry button for invalid/warning states */}
        {integrity.status !== 'ok' && onRetry && (
          <button
            onClick={onRetry}
            disabled={isLoading}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg font-medium 
                     transition-all flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Retry Analysis
          </button>
        )}
      </div>
      
      {/* Issue summary badges */}
      {integrity.issues.length > 0 && (
        <div className="flex items-center gap-2 mt-3">
          {errorCount > 0 && (
            <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-full">
              {errorCount} error{errorCount !== 1 ? 's' : ''}
            </span>
          )}
          {warningCount > 0 && (
            <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded-full">
              {warningCount} warning{warningCount !== 1 ? 's' : ''}
            </span>
          )}
          {infoCount > 0 && (
            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full">
              {infoCount} info
            </span>
          )}
          
          {/* Expand/collapse button */}
          <button
            onClick={() => setExpanded(!expanded)}
            className="ml-auto text-white/50 hover:text-white/80 transition-colors flex items-center gap-1 text-xs"
          >
            {expanded ? 'Hide details' : 'Show details'}
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        </div>
      )}
      
      {/* Expanded issue details */}
      {expanded && integrity.issues.length > 0 && (
        <div className="mt-4 space-y-2">
          {integrity.issues.map((issue, idx) => (
            <div 
              key={idx}
              className={`flex items-start gap-2 p-2 rounded-lg text-sm ${
                issue.severity === 'error' ? 'bg-red-500/10' :
                issue.severity === 'warning' ? 'bg-amber-500/10' : 'bg-blue-500/10'
              }`}
            >
              {issue.severity === 'error' && <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />}
              {issue.severity === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />}
              {issue.severity === 'info' && <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />}
              <div>
                <span className="text-white/80">{issue.message}</span>
                {issue.affectedSections.length > 0 && issue.affectedSections[0] !== 'all' && (
                  <span className="text-white/40 ml-2">
                    (affects: {issue.affectedSections.join(', ')})
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Provenance info (always visible in dev mode) */}
      {import.meta.env.DEV && integrity.provenance && (
        <div className="mt-4 pt-3 border-t border-white/10 text-xs text-white/40">
          <span className="font-mono">
            Run: {integrity.provenance.runId || 'N/A'} | 
            Engine: {integrity.provenance.engineVersion || 'N/A'} | 
            Time: {integrity.provenance.analyzedAt || 'N/A'}
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * NoDataSection - Shows when a section has no data to display
 */
interface NoDataSectionProps {
  title: string;
  message?: string;
  icon?: React.ComponentType<{ className?: string }>;
}

export function NoDataSection({ title, message, icon: Icon = Info }: NoDataSectionProps) {
  return (
    <div className="rounded-xl border border-dashed border-white/20 bg-white/5 p-6 text-center">
      <Icon className="w-8 h-8 text-white/30 mx-auto mb-2" />
      <h4 className="text-white/60 font-medium">{title}</h4>
      {message && <p className="text-white/40 text-sm mt-1">{message}</p>}
    </div>
  );
}
