/**
 * Risk Run Detail Page
 * Shows run status, results, provenance, and replay verification
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { GlassCard } from '@/components/GlassCard';
import { RunStatusBadge, RunStatus } from '@/components/RunStatusBadge';
import { ProvenanceCard, RiskRunProvenance } from '@/components/ProvenanceCard';
import { api } from '@/services/apiClient';

interface RiskRunDetail {
  id: string;
  tenant_id: string;
  assessment_id: string;
  status: RunStatus;
  seed: number;
  seed_strategy: string;
  iterations: number;
  engine_version: string;
  model_version_id?: string;
  result_json?: Record<string, any>;
  result_hash?: string;
  error_message?: string;
  error_details?: Record<string, any>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  job_id?: string;
  job_status?: string;
}

interface RiskRunStatus {
  status: RunStatus;
  progress?: number;
  eta_seconds?: number;
  started_at?: string;
  completed_at?: string;
}

export const RiskRunDetailPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<RiskRunDetail | null>(null);
  const [status, setStatus] = useState<RiskRunStatus | null>(null);
  const [provenance, setProvenance] = useState<RiskRunProvenance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replayResult, setReplayResult] = useState<any>(null);
  const [replaying, setReplaying] = useState(false);
  const [polling, setPolling] = useState(false);

  // Fetch run details
  const fetchRun = async () => {
    if (!runId) return;

    try {
      const response = await api.get<RiskRunDetail>(`/api/v3/risk/runs/${runId}`);
      if (response.error) {
        setError(response.error.userMessage);
        return;
      }
      if (response.data) {
        setRun(response.data);
        // Start polling if pending/running
        if (response.data.status === 'PENDING' || response.data.status === 'RUNNING') {
          setPolling(true);
        }
      }
    } catch (err) {
      setError('Failed to load run details');
    } finally {
      setLoading(false);
    }
  };

  // Fetch run status
  const fetchStatus = async () => {
    if (!runId) return;

    try {
      const response = await api.get<RiskRunStatus>(`/api/v3/risk/runs/${runId}/status`);
      if (response.data) {
        setStatus(response.data);
        // Stop polling if completed
        if (response.data.status === 'SUCCEEDED' || response.data.status === 'FAILED') {
          setPolling(false);
        }
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  // Fetch provenance
  const fetchProvenance = async () => {
    if (!runId) return;

    try {
      const response = await api.get<RiskRunProvenance>(`/api/v3/risk/runs/${runId}/provenance`);
      if (response.data) {
        setProvenance(response.data);
      }
    } catch (err) {
      console.error('Failed to fetch provenance:', err);
    }
  };

  // Poll for status updates
  useEffect(() => {
    if (!polling || !runId) return;

    const interval = setInterval(() => {
      fetchStatus();
      fetchRun(); // Also refresh full details
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [polling, runId]);

  // Initial load
  useEffect(() => {
    fetchRun();
    fetchStatus();
    fetchProvenance();
  }, [runId]);

  // Replay verification
  const handleReplay = async () => {
    if (!runId) return;

    setReplaying(true);
    try {
      const response = await api.post<any>(`/api/v3/risk/runs/${runId}/replay`);
      if (response.data) {
        setReplayResult(response.data);
      } else if (response.error) {
        setError(response.error.userMessage);
      }
    } catch (err) {
      setError('Failed to replay run');
    } finally {
      setReplaying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
        <div className="max-w-7xl mx-auto">
          <GlassCard padding="lg">
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-white/10 rounded w-1/3"></div>
              <div className="h-4 bg-white/10 rounded w-1/2"></div>
            </div>
          </GlassCard>
        </div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
        <div className="max-w-7xl mx-auto">
          <GlassCard padding="lg">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-white mb-4">Error</h2>
              <p className="text-gray-400">{error || 'Run not found'}</p>
              <button
                onClick={() => navigate(-1)}
                className="mt-4 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition-colors"
              >
                Go Back
              </button>
            </div>
          </GlassCard>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Risk Run Details</h1>
            <p className="text-gray-400">Run ID: {run.id}</p>
          </div>
          <RunStatusBadge status={run.status} size="lg" />
        </div>

        {/* Status Section */}
        {status && (
          <GlassCard padding="md">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Status</h3>
                {status.progress !== undefined && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-sm text-gray-400 mb-1">
                      <span>Progress</span>
                      <span>{Math.round(status.progress * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${status.progress * 100}%` }}
                      />
                    </div>
                  </div>
                )}
                {status.eta_seconds !== undefined && status.eta_seconds > 0 && (
                  <p className="text-sm text-gray-400 mt-2">
                    Estimated time remaining: {status.eta_seconds}s
                  </p>
                )}
              </div>
              <div className="text-right">
                {status.started_at && (
                  <p className="text-sm text-gray-400">
                    Started: {new Date(status.started_at).toLocaleString()}
                  </p>
                )}
                {status.completed_at && (
                  <p className="text-sm text-gray-400">
                    Completed: {new Date(status.completed_at).toLocaleString()}
                  </p>
                )}
              </div>
            </div>
          </GlassCard>
        )}

        {/* Results Section */}
        {run.status === 'SUCCEEDED' && run.result_json && (
          <GlassCard padding="lg">
            <h3 className="text-xl font-semibold text-white mb-4">Results</h3>
            {run.result_hash && (
              <div className="mb-4">
                <label className="text-sm text-gray-400 mb-1 block">Result Hash</label>
                <code className="text-sm text-white font-mono bg-black/20 px-2 py-1 rounded block truncate">
                  {run.result_hash}
                </code>
              </div>
            )}
            <pre className="bg-black/20 p-4 rounded-lg overflow-auto text-sm text-gray-300">
              {JSON.stringify(run.result_json, null, 2)}
            </pre>
          </GlassCard>
        )}

        {/* Error Section */}
        {run.status === 'FAILED' && (
          <GlassCard padding="lg" className="border-red-500/50">
            <h3 className="text-xl font-semibold text-red-400 mb-4">Error</h3>
            {run.error_message && (
              <p className="text-white mb-2">{run.error_message}</p>
            )}
            {run.error_details && (
              <pre className="bg-black/20 p-4 rounded-lg overflow-auto text-sm text-gray-300">
                {JSON.stringify(run.error_details, null, 2)}
              </pre>
            )}
          </GlassCard>
        )}

        {/* Provenance Section */}
        {provenance && (
          <ProvenanceCard
            provenance={provenance}
            onViewAssessment={(assessmentId) => navigate(`/risk/assessments/${assessmentId}`)}
          />
        )}

        {/* Replay Verification */}
        {run.status === 'SUCCEEDED' && (
          <GlassCard padding="lg">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">Reproducibility Verification</h3>
                <p className="text-sm text-gray-400">
                  Re-run this calculation to verify results match
                </p>
              </div>
              <button
                onClick={handleReplay}
                disabled={replaying}
                className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {replaying ? 'Replaying...' : 'Verify Reproducibility'}
              </button>
            </div>
            {replayResult && (
              <div className={`mt-4 p-4 rounded-lg ${
                replayResult.matches 
                  ? 'bg-green-500/20 border border-green-500/50' 
                  : 'bg-red-500/20 border border-red-500/50'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`font-semibold ${
                    replayResult.matches ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {replayResult.matches ? '✓ Match' : '✗ Mismatch'}
                  </span>
                  {replayResult.replay_duration_seconds && (
                    <span className="text-sm text-gray-400">
                      Duration: {replayResult.replay_duration_seconds.toFixed(2)}s
                    </span>
                  )}
                </div>
                {replayResult.diff_summary && (
                  <pre className="text-sm text-gray-300 mt-2">
                    {JSON.stringify(replayResult.diff_summary, null, 2)}
                  </pre>
                )}
                {replayResult.error && (
                  <p className="text-sm text-red-400 mt-2">{replayResult.error}</p>
                )}
              </div>
            )}
          </GlassCard>
        )}
      </div>
    </div>
  );
};
