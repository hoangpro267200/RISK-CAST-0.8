import React from 'react';
import { Lightbulb, AlertCircle, CheckCircle2, TrendingUp } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { safeArray, safeString } from '../utils/safeData';
import type { AINarrative } from '../types';

export interface ExecutiveNarrativeProps {
  narrative: AINarrative | null;
  className?: string;
}

export const ExecutiveNarrative: React.FC<ExecutiveNarrativeProps> = ({
  narrative,
  className = '',
}) => {
  if (!narrative) {
    return (
      <GlassCard className={className}>
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wide">
              Executive Summary
            </h3>
          </div>
          <p className="text-white/60 text-sm leading-relaxed">
            AI narrative analysis is being generated. Please check back shortly for detailed insights.
          </p>
        </div>
      </GlassCard>
    );
  }

  const summary = safeString(narrative.executiveSummary, 'No summary available');
  const insights = safeArray<string>(narrative.keyInsights);
  const actions = safeArray<string>(narrative.actionItems);
  const drivers = safeArray<string>(narrative.riskDrivers);
  const notes = safeString(narrative.confidenceNotes, '');

  return (
    <GlassCard className={className}>
      <div className="space-y-6">
        {/* Executive Summary */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wide">
              Executive Summary
            </h3>
          </div>
          <p className="text-white/80 leading-relaxed">{summary}</p>
        </section>

        {/* Key Insights */}
        {insights.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wide">
                Key Insights
              </h3>
            </div>
            <ul className="space-y-2">
              {insights.slice(0, 5).map((insight, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-amber-400/60 mt-1">•</span>
                  <span className="text-white/70 text-sm leading-relaxed flex-1">
                    {insight}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Action Items */}
        {actions.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wide">
                Recommended Actions
              </h3>
            </div>
            <ul className="space-y-2">
              {actions.slice(0, 5).map((action, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-400/20 border border-emerald-400/30 flex items-center justify-center text-emerald-400 text-xs font-semibold mt-0.5">
                    {idx + 1}
                  </span>
                  <span className="text-white/70 text-sm leading-relaxed flex-1">
                    {action}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Risk Drivers */}
        {drivers.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wide">
                Primary Risk Drivers
              </h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {drivers.slice(0, 8).map((driver, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1.5 rounded-full bg-red-400/10 border border-red-400/20 text-red-400 text-xs font-medium"
                >
                  {driver}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Confidence Notes */}
        {notes && (
          <section className="pt-4 border-t border-white/10">
            <p className="text-xs text-white/40 italic">{notes}</p>
          </section>
        )}
      </div>
    </GlassCard>
  );
};
