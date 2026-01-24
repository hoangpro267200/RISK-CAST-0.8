/**
 * Run Detail Page
 * View risk run details with polling for status updates
 */
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { riskApi } from '../../api/client';
import { RiskRun } from '../../types';

export function RunDetail() {
  const { runId } = useParams<{ runId: string }>();

  const { data: run, isLoading, error } = useQuery<RiskRun>({
    queryKey: ['risk-run', runId],
    queryFn: async () => {
      const response = await riskApi.getRun(runId!);
      return response.data;
    },
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll until complete
      if (data?.status === 'QUEUED' || data?.status === 'RUNNING') {
        return 2000; // Poll every 2 seconds
      }
      return false; // Stop polling when complete
    }
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60">Loading run details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-red-200 mb-2">Error Loading Run</h2>
          <p className="text-red-300">
            {error instanceof Error ? error.message : 'Failed to load run details'}
          </p>
        </div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="p-6">
        <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-6">
          <p className="text-yellow-200">Run not found</p>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCEEDED':
        return 'bg-green-500/20 text-green-300 border-green-500/50';
      case 'FAILED':
        return 'bg-red-500/20 text-red-300 border-red-500/50';
      case 'RUNNING':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/50';
      case 'QUEUED':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50';
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/50';
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-white">Risk Run Details</h1>

      {/* Status badge */}
      <div className="mb-6">
        <span className={`px-4 py-2 rounded-full text-sm font-medium border ${getStatusColor(run.status)}`}>
          {run.status}
          {(run.status === 'QUEUED' || run.status === 'RUNNING') && (
            <span className="ml-2 inline-block w-2 h-2 bg-current rounded-full animate-pulse"></span>
          )}
        </span>
      </div>

      {/* Provenance section */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 mb-6">
        <h2 className="font-semibold mb-4 text-white text-lg">Provenance</h2>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-white/60 mb-1">Run ID</dt>
            <dd className="font-mono text-white break-all">{run.id}</dd>
          </div>

          <div>
            <dt className="text-white/60 mb-1">Assessment ID</dt>
            <dd className="font-mono text-white break-all">{run.risk_assessment_id}</dd>
          </div>

          {run.engine_version && (
            <div>
              <dt className="text-white/60 mb-1">Engine Version</dt>
              <dd className="font-mono text-white">{run.engine_version}</dd>
            </div>
          )}

          <div>
            <dt className="text-white/60 mb-1">Model Version</dt>
            <dd className="font-mono text-white">{run.model_version_id || 'default'}</dd>
          </div>

          {run.seed !== undefined && (
            <div>
              <dt className="text-white/60 mb-1">Seed</dt>
              <dd className="font-mono text-white">{run.seed}</dd>
            </div>
          )}

          {run.iterations !== undefined && (
            <div>
              <dt className="text-white/60 mb-1">Iterations</dt>
              <dd className="text-white">{run.iterations}</dd>
            </div>
          )}

          {run.result_hash && (
            <div className="col-span-2">
              <dt className="text-white/60 mb-1">Result Hash</dt>
              <dd className="font-mono text-white text-xs break-all">{run.result_hash}</dd>
            </div>
          )}

          <div>
            <dt className="text-white/60 mb-1">Created At</dt>
            <dd className="text-white">{new Date(run.created_at).toLocaleString()}</dd>
          </div>

          <div>
            <dt className="text-white/60 mb-1">Updated At</dt>
            <dd className="text-white">{new Date(run.updated_at).toLocaleString()}</dd>
          </div>
        </dl>
      </div>

      {/* Results section */}
      {run.status === 'SUCCEEDED' && run.result_json && (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 mb-6">
          <h2 className="font-semibold mb-4 text-white text-lg">Results</h2>

          <div className="mb-6">
            <div className="text-sm text-white/60 mb-2">Overall Risk Score</div>
            <div className="text-4xl font-bold text-white">
              {run.result_json.overall_risk_score.toFixed(2)}
            </div>
          </div>

          {/* Distribution summary */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-sm text-white/60 mb-1">Mean</div>
              <div className="font-semibold text-white text-lg">
                {run.result_json.distribution_summary.mean.toFixed(4)}
              </div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-sm text-white/60 mb-1">VaR 95%</div>
              <div className="font-semibold text-white text-lg">
                {run.result_json.distribution_summary.var_95.toFixed(4)}
              </div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-sm text-white/60 mb-1">CVaR 95%</div>
              <div className="font-semibold text-white text-lg">
                {run.result_json.distribution_summary.cvar_95.toFixed(4)}
              </div>
            </div>
          </div>

          {/* Layer contributions */}
          {run.result_json.layer_contributions && run.result_json.layer_contributions.length > 0 && (
            <div>
              <h3 className="font-medium mb-3 text-white">Layer Contributions</h3>
              <ul className="space-y-2">
                {run.result_json.layer_contributions.map((layer, i) => (
                  <li key={i} className="flex justify-between items-center bg-white/5 rounded-lg p-3">
                    <span className="text-white">{layer.layer_name}</span>
                    <span className="font-mono text-white font-semibold">
                      {(layer.contribution * 100).toFixed(1)}%
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Error section */}
      {run.status === 'FAILED' && run.error_json && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6">
          <h2 className="font-semibold text-red-200 mb-3 text-lg">Error Details</h2>
          <pre className="text-sm text-red-300 bg-black/30 p-4 rounded overflow-auto">
            {JSON.stringify(run.error_json, null, 2)}
          </pre>
        </div>
      )}

      {/* Running/Queued state */}
      {(run.status === 'QUEUED' || run.status === 'RUNNING') && (
        <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-6">
          <div className="flex items-center">
            <div className="w-4 h-4 border-2 border-blue-300 border-t-transparent rounded-full animate-spin mr-3"></div>
            <p className="text-blue-200">
              {run.status === 'QUEUED' 
                ? 'Run is queued and will start shortly...' 
                : 'Run is in progress. Results will appear when complete.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default RunDetail;
