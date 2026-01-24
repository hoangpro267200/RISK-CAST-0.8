/**
 * Provenance Card Component
 * Displays all provenance fields for risk run reproducibility
 */
import React, { useState } from 'react';
import { GlassCard } from './GlassCard';
import { RunStatusBadge } from './RunStatusBadge';

export interface RiskRunProvenance {
  run_id: string;
  assessment_id: string;
  input_hash: string;
  seed: number;
  seed_strategy: string;
  iterations: number;
  engine_version: string;
  model_version_id?: string;
  result_hash?: string;
  computed_at?: string;
}

interface ProvenanceCardProps {
  provenance: RiskRunProvenance;
  onViewAssessment?: (assessmentId: string) => void;
}

export const ProvenanceCard: React.FC<ProvenanceCardProps> = ({ 
  provenance,
  onViewAssessment 
}) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = async (text: string, fieldName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(fieldName);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const CopyButton: React.FC<{ text: string; fieldName: string }> = ({ text, fieldName }) => (
    <button
      onClick={() => copyToClipboard(text, fieldName)}
      className="ml-2 rounded px-2 py-1 text-xs bg-white/10 hover:bg-white/20 transition-colors"
      title="Copy to clipboard"
    >
      {copiedField === fieldName ? '✓ Copied' : '📋 Copy'}
    </button>
  );

  return (
    <GlassCard padding="lg" className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-white">Provenance</h3>
        <span className="text-sm text-gray-400">Reproducibility Information</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Run ID */}
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Run ID</label>
          <div className="flex items-center">
            <code className="text-sm text-white font-mono bg-black/20 px-2 py-1 rounded flex-1 truncate">
              {provenance.run_id}
            </code>
            <CopyButton text={provenance.run_id} fieldName="run_id" />
          </div>
        </div>

        {/* Assessment ID */}
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Assessment ID</label>
          <div className="flex items-center">
            <code className="text-sm text-white font-mono bg-black/20 px-2 py-1 rounded flex-1 truncate">
              {provenance.assessment_id}
            </code>
            {onViewAssessment && (
              <button
                onClick={() => onViewAssessment(provenance.assessment_id)}
                className="ml-2 rounded px-2 py-1 text-xs bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 transition-colors"
                title="View assessment"
              >
                View
              </button>
            )}
          </div>
        </div>

        {/* Input Hash */}
        <div className="md:col-span-2">
          <label className="text-sm text-gray-400 mb-1 block">Input Hash</label>
          <div className="flex items-center">
            <code className="text-sm text-white font-mono bg-black/20 px-2 py-1 rounded flex-1 truncate">
              {provenance.input_hash}
            </code>
            <CopyButton text={provenance.input_hash} fieldName="input_hash" />
          </div>
        </div>

        {/* Seed */}
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Seed</label>
          <div className="flex items-center">
            <code className="text-sm text-white font-mono bg-black/20 px-2 py-1 rounded flex-1">
              {provenance.seed}
            </code>
            <CopyButton text={provenance.seed.toString()} fieldName="seed" />
          </div>
        </div>

        {/* Seed Strategy */}
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Seed Strategy</label>
          <span className="text-sm text-white">{provenance.seed_strategy}</span>
        </div>

        {/* Iterations */}
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Iterations</label>
          <span className="text-sm text-white">{provenance.iterations.toLocaleString()}</span>
        </div>

        {/* Engine Version */}
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Engine Version</label>
          <span className="text-sm text-white">{provenance.engine_version}</span>
        </div>

        {/* Model Version ID */}
        {provenance.model_version_id && (
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Model Version ID</label>
            <div className="flex items-center">
              <code className="text-sm text-white font-mono bg-black/20 px-2 py-1 rounded flex-1 truncate">
                {provenance.model_version_id}
              </code>
              <CopyButton text={provenance.model_version_id} fieldName="model_version_id" />
            </div>
          </div>
        )}

        {/* Result Hash */}
        {provenance.result_hash && (
          <div className="md:col-span-2">
            <label className="text-sm text-gray-400 mb-1 block">Result Hash</label>
            <div className="flex items-center">
              <code className="text-sm text-white font-mono bg-black/20 px-2 py-1 rounded flex-1 truncate">
                {provenance.result_hash}
              </code>
              <CopyButton text={provenance.result_hash} fieldName="result_hash" />
            </div>
          </div>
        )}

        {/* Computed At */}
        {provenance.computed_at && (
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Computed At</label>
            <span className="text-sm text-white">
              {new Date(provenance.computed_at).toLocaleString()}
            </span>
          </div>
        )}
      </div>
    </GlassCard>
  );
};
