/**
 * Submission Detail Page
 * View underwriting submission details with decision making
 */
import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { underwritingApi, riskApi, evidenceApi } from '../../api/client';
import { StatusBadge } from '../../components/common/StatusBadge';
import { RiskRun } from '../../types';

export function SubmissionDetail() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const queryClient = useQueryClient();
  
  const [decisionForm, setDecisionForm] = useState({
    decision: '',
    terms_json: {} as Record<string, any>,
    notes: ''
  });

  const { data: submission, isLoading: submissionLoading } = useQuery({
    queryKey: ['submission', submissionId],
    queryFn: () => underwritingApi.getSubmission(submissionId!).then(res => res.data),
    enabled: !!submissionId
  });

  const { data: riskRun, isLoading: riskRunLoading } = useQuery<RiskRun>({
    queryKey: ['risk-run', submission?.risk_run_id],
    queryFn: () => riskApi.getRun(submission!.risk_run_id!).then(res => res.data),
    enabled: !!submission?.risk_run_id
  });

  const decisionMutation = useMutation({
    mutationFn: (data: any) => 
      underwritingApi.createDecision(submissionId!, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submission', submissionId] });
      setDecisionForm({ decision: '', terms_json: {}, notes: '' });
    }
  });

  const bindMutation = useMutation({
    mutationFn: (data: any) => 
      underwritingApi.bindPolicy(data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submission', submissionId] });
    }
  });

  if (submissionLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60">Loading submission...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!submission) {
    return (
      <div className="p-6">
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6">
          <p className="text-red-200">Submission not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-white">
        Submission {submissionId?.slice(0, 8)}...
      </h1>

      {/* Status and timeline */}
      <div className="mb-6">
        <StatusBadge status={submission.status} />
      </div>

      {/* Risk Run Summary */}
      {riskRunLoading ? (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 mb-6">
          <p className="text-white/60">Loading risk assessment...</p>
        </div>
      ) : riskRun ? (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 mb-6">
          <h2 className="font-semibold mb-4 text-white text-lg">Risk Assessment</h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-white/60 mb-1">Risk Score</div>
              <div className="text-3xl font-bold text-white">
                {riskRun.result_json?.overall_risk_score?.toFixed(2) || 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-white/60 mb-1">Model Version</div>
              <div className="font-mono text-white">
                {riskRun.model_version_id || 'default'}
              </div>
            </div>
            {riskRun.result_json?.distribution_summary && (
              <>
                <div>
                  <div className="text-sm text-white/60 mb-1">VaR 95%</div>
                  <div className="text-lg font-semibold text-white">
                    {riskRun.result_json.distribution_summary.var_95.toFixed(4)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-white/60 mb-1">CVaR 95%</div>
                  <div className="text-lg font-semibold text-white">
                    {riskRun.result_json.distribution_summary.cvar_95.toFixed(4)}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      ) : null}

      {/* Evidence Bundle */}
      {submission.evidence_bundle_id && (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 mb-6">
          <h2 className="font-semibold mb-3 text-white text-lg">Evidence Bundle</h2>
          <Link 
            to={`/app/compliance/evidence/${submission.evidence_bundle_id}`}
            className="text-blue-400 hover:text-blue-300 hover:underline transition-colors"
          >
            View Evidence Bundle →
          </Link>
        </div>
      )}

      {/* Decision Actions */}
      {submission.status === 'UNDER_REVIEW' && (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 mb-6">
          <h2 className="font-semibold mb-4 text-white text-lg">Make Decision</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-white/80">Decision</label>
              <select
                value={decisionForm.decision}
                onChange={(e) => setDecisionForm({...decisionForm, decision: e.target.value})}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select...</option>
                <option value="QUOTE">Quote</option>
                <option value="DECLINE">Decline</option>
                <option value="REQUEST_INFO">Request More Info</option>
              </select>
            </div>

            {decisionForm.decision === 'QUOTE' && (
              <div>
                <label className="block text-sm font-medium mb-2 text-white/80">Premium (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  onChange={(e) => setDecisionForm({
                    ...decisionForm,
                    terms_json: {...decisionForm.terms_json, premium: parseFloat(e.target.value) || 0}
                  })}
                  className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2 text-white/80">Notes</label>
              <textarea
                value={decisionForm.notes}
                onChange={(e) => setDecisionForm({...decisionForm, notes: e.target.value})}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="Add decision notes..."
              />
            </div>

            <button
              onClick={() => decisionMutation.mutate(decisionForm)}
              disabled={decisionMutation.isPending || !decisionForm.decision}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {decisionMutation.isPending ? 'Submitting...' : 'Submit Decision'}
            </button>

            {decisionMutation.isError && (
              <div className="p-3 bg-red-500/20 border border-red-500/50 rounded text-red-200 text-sm">
                {decisionMutation.error instanceof Error 
                  ? decisionMutation.error.message 
                  : 'Failed to submit decision'}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bind Policy */}
      {submission.status === 'QUOTED' && (
        <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-6">
          <h2 className="font-semibold mb-4 text-green-200 text-lg">Bind Policy</h2>
          <p className="text-green-300/80 mb-4 text-sm">
            Create an active policy from this quoted submission.
          </p>
          
          <button
            onClick={() => bindMutation.mutate({
              submission_id: submissionId,
              effective_from: new Date().toISOString(),
              effective_to: new Date(Date.now() + 365*24*60*60*1000).toISOString()
            })}
            disabled={bindMutation.isPending}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {bindMutation.isPending ? 'Binding...' : 'Bind Policy'}
          </button>

          {bindMutation.isError && (
            <div className="mt-4 p-3 bg-red-500/20 border border-red-500/50 rounded text-red-200 text-sm">
              {bindMutation.error instanceof Error 
                ? bindMutation.error.message 
                : 'Failed to bind policy'}
            </div>
          )}
        </div>
      )}

      {/* Submission Info */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 mt-6">
        <h2 className="font-semibold mb-4 text-white text-lg">Submission Details</h2>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-white/60 mb-1">Submission ID</dt>
            <dd className="font-mono text-white break-all">{submission.id}</dd>
          </div>
          <div>
            <dt className="text-white/60 mb-1">Assessment ID</dt>
            <dd className="font-mono text-white break-all">{submission.risk_assessment_id}</dd>
          </div>
          {submission.risk_run_id && (
            <div>
              <dt className="text-white/60 mb-1">Risk Run ID</dt>
              <dd className="font-mono text-white break-all">{submission.risk_run_id}</dd>
            </div>
          )}
          <div>
            <dt className="text-white/60 mb-1">Created At</dt>
            <dd className="text-white">{new Date(submission.created_at).toLocaleString()}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

export default SubmissionDetail;
