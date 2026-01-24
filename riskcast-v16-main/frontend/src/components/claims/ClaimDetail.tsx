/**
 * Claim Detail Component
 * 
 * Shows full claim details with workflow actions.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  UserPlus,
  Play,
  FileUp,
  CheckCircle,
  XCircle,
  CreditCard,
  Lock,
  History,
  AlertTriangle,
} from 'lucide-react';

import { claimsApi } from '../../api/client';
import { formatCurrency, formatDate, formatDateTime } from '../../utils/format';
import { StatusBadge } from '../common/StatusBadge';

interface ClaimDetailProps {
  claimId: string;
  onClose: () => void;
}

export function ClaimDetail({ claimId, onClose }: ClaimDetailProps) {
  const queryClient = useQueryClient();
  const [adjudicationData, setAdjudicationData] = useState({
    decision: 'APPROVED' as 'APPROVED' | 'DECLINED',
    decision_reason: '',
    deductible_cents: 0,
  });
  const [showAdjudicateConfirm, setShowAdjudicateConfirm] = useState(false);
  const [showAuthorizeConfirm, setShowAuthorizeConfirm] = useState(false);

  const { data: claim, isLoading } = useQuery({
    queryKey: ['claim', claimId],
    queryFn: async () => {
      const response = await claimsApi.getClaim(claimId);
      return response.data;
    },
    enabled: !!claimId,
  });

  const { data: history } = useQuery({
    queryKey: ['claim-history', claimId],
    queryFn: async () => {
      const response = await claimsApi.getClaimHistory(claimId);
      return response.data;
    },
    enabled: !!claimId,
  });

  const assignMutation = useMutation({
    mutationFn: (adjusterId: string) =>
      claimsApi.assignAdjuster(claimId, adjusterId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claim', claimId] });
      queryClient.invalidateQueries({ queryKey: ['claims'] });
    },
  });

  const investigateMutation = useMutation({
    mutationFn: () => claimsApi.beginInvestigation(claimId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claim', claimId] });
      queryClient.invalidateQueries({ queryKey: ['claims'] });
    },
  });

  const adjudicateMutation = useMutation({
    mutationFn: (data: typeof adjudicationData) =>
      claimsApi.adjudicate(claimId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claim', claimId] });
      queryClient.invalidateQueries({ queryKey: ['claims'] });
      setShowAdjudicateConfirm(false);
    },
  });

  const authorizeMutation = useMutation({
    mutationFn: () => claimsApi.authorize(claimId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claim', claimId] });
      queryClient.invalidateQueries({ queryKey: ['claims'] });
      setShowAuthorizeConfirm(false);
    },
  });

  if (isLoading || !claim) {
    return (
      <div className="flex justify-center py-8">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const canAssign =
    claim.status === 'FNOL_RECEIVED' && !claim.assigned_adjuster_id;
  const canInvestigate =
    claim.status === 'FNOL_RECEIVED' && claim.assigned_adjuster_id;
  const canAdjudicate =
    claim.status === 'UNDER_INVESTIGATION' && claim.evidence_bundle_id;
  const canAuthorize = claim.status === 'APPROVED';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-white">
            {claim.claim_number || claim.id.slice(0, 8)}
          </h2>
          <p className="text-white/60 mt-1">
            Filed on {formatDateTime(claim.created_at)}
          </p>
        </div>
        <StatusBadge status={claim.status} />
      </div>

      {/* FNOL Details - Immutable */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-4">
        <div className="flex items-center mb-4">
          <Lock className="h-4 w-4 mr-2 text-white/60" />
          <h3 className="font-semibold text-white">
            First Notice of Loss (Immutable)
          </h3>
        </div>
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-white/60">Loss Date</span>
            <p className="font-medium text-white mt-1">
              {claim.fnol?.loss_date
                ? formatDate(claim.fnol.loss_date)
                : 'N/A'}
            </p>
          </div>
          <div>
            <span className="text-white/60">Loss Type</span>
            <p className="font-medium text-white mt-1">
              {claim.fnol?.loss_type || 'N/A'}
            </p>
          </div>
          <div>
            <span className="text-white/60">Loss Location</span>
            <p className="font-medium text-white mt-1">
              {claim.fnol?.loss_location || 'N/A'}
            </p>
          </div>
          <div>
            <span className="text-white/60">Estimated Loss</span>
            <p className="font-medium text-white mt-1">
              {claim.fnol?.estimated_loss_cents
                ? formatCurrency(claim.fnol.estimated_loss_cents / 100)
                : 'N/A'}
            </p>
          </div>
          <div className="md:col-span-2">
            <span className="text-white/60">Description</span>
            <p className="font-medium text-white mt-1">
              {claim.fnol?.loss_description || 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Workflow Actions */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-4">
        <h3 className="font-semibold text-white mb-4">Workflow Actions</h3>

        {/* Assign Adjuster */}
        {canAssign && (
          <div className="flex items-center justify-between p-4 border border-white/10 rounded-lg">
            <div>
              <h4 className="font-medium text-white">Assign Adjuster</h4>
              <p className="text-sm text-white/60">
                Assign an adjuster to handle this claim
              </p>
            </div>
            <button
              onClick={() => assignMutation.mutate('current-user-id')}
              disabled={assignMutation.isPending}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <UserPlus className="h-4 w-4" />
              Assign to Me
            </button>
          </div>
        )}

        {/* Begin Investigation */}
        {canInvestigate && (
          <div className="flex items-center justify-between p-4 border border-white/10 rounded-lg">
            <div>
              <h4 className="font-medium text-white">Begin Investigation</h4>
              <p className="text-sm text-white/60">
                Start the investigation process
              </p>
            </div>
            <button
              onClick={() => investigateMutation.mutate()}
              disabled={investigateMutation.isPending}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <Play className="h-4 w-4" />
              Begin Investigation
            </button>
          </div>
        )}

        {/* Submit Evidence */}
        {claim.status === 'UNDER_INVESTIGATION' && !claim.evidence_bundle_id && (
          <div className="flex items-center justify-between p-4 border border-yellow-500/50 rounded-lg bg-yellow-500/10">
            <div>
              <h4 className="font-medium text-white flex items-center">
                <AlertTriangle className="h-4 w-4 mr-2 text-yellow-400" />
                Evidence Required
              </h4>
              <p className="text-sm text-white/60">
                Create and attach an evidence bundle before adjudication
              </p>
            </div>
            <button className="px-4 py-2 border border-white/20 text-white rounded-lg hover:bg-white/10 transition-colors flex items-center gap-2">
              <FileUp className="h-4 w-4" />
              Attach Evidence
            </button>
          </div>
        )}

        {/* Adjudicate */}
        {canAdjudicate && (
          <div className="p-4 border border-white/10 rounded-lg space-y-4">
            <h4 className="font-medium text-white">Adjudicate Claim</h4>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Decision
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      setAdjudicationData((d) => ({ ...d, decision: 'APPROVED' }))
                    }
                    className={`flex-1 px-4 py-2 rounded-lg transition-colors flex items-center justify-center gap-2 ${
                      adjudicationData.decision === 'APPROVED'
                        ? 'bg-green-500 text-white'
                        : 'bg-white/10 text-white/60 hover:bg-white/20'
                    }`}
                  >
                    <CheckCircle className="h-4 w-4" />
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setAdjudicationData((d) => ({ ...d, decision: 'DECLINED' }))
                    }
                    className={`flex-1 px-4 py-2 rounded-lg transition-colors flex items-center justify-center gap-2 ${
                      adjudicationData.decision === 'DECLINED'
                        ? 'bg-red-500 text-white'
                        : 'bg-white/10 text-white/60 hover:bg-white/20'
                    }`}
                  >
                    <XCircle className="h-4 w-4" />
                    Decline
                  </button>
                </div>
              </div>

              {adjudicationData.decision === 'APPROVED' && (
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Deductible Amount (USD)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={adjudicationData.deductible_cents / 100}
                    onChange={(e) =>
                      setAdjudicationData((d) => ({
                        ...d,
                        deductible_cents: parseFloat(e.target.value) * 100,
                      }))
                    }
                    className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Decision Reason
              </label>
              <textarea
                value={adjudicationData.decision_reason}
                onChange={(e) =>
                  setAdjudicationData((d) => ({
                    ...d,
                    decision_reason: e.target.value,
                  }))
                }
                placeholder="Explain the decision..."
                rows={3}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {showAdjudicateConfirm ? (
              <div className="p-4 bg-white/5 border border-white/20 rounded-lg space-y-3">
                <p className="text-white">
                  You are about to {adjudicationData.decision.toLowerCase()} this
                  claim.
                </p>
                {adjudicationData.decision === 'APPROVED' && (
                  <p className="text-white/80 text-sm">
                    Approved amount:{' '}
                    {formatCurrency(
                      (claim.fnol?.estimated_loss_cents || 0 -
                        adjudicationData.deductible_cents) /
                        100
                    )}
                  </p>
                )}
                <p className="text-white/60 text-sm">
                  This action cannot be undone.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowAdjudicateConfirm(false)}
                    className="flex-1 px-4 py-2 border border-white/20 text-white rounded-lg hover:bg-white/10"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => adjudicateMutation.mutate(adjudicationData)}
                    disabled={adjudicateMutation.isPending}
                    className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 text-white rounded-lg"
                  >
                    Confirm
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAdjudicateConfirm(true)}
                className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
              >
                Submit Adjudication
              </button>
            )}
          </div>
        )}

        {/* Authorize Payout */}
        {canAuthorize && (
          <div className="flex items-center justify-between p-4 border border-green-500/50 rounded-lg bg-green-500/10">
            <div>
              <h4 className="font-medium text-white">Authorize Payout</h4>
              <p className="text-sm text-white/60">
                Approved amount:{' '}
                {claim.approved_amount_cents
                  ? formatCurrency(claim.approved_amount_cents / 100)
                  : 'N/A'}
              </p>
            </div>
            {showAuthorizeConfirm ? (
              <div className="flex gap-2">
                <button
                  onClick={() => setShowAuthorizeConfirm(false)}
                  className="px-4 py-2 border border-white/20 text-white rounded-lg hover:bg-white/10"
                >
                  Cancel
                </button>
                <button
                  onClick={() => authorizeMutation.mutate()}
                  disabled={authorizeMutation.isPending}
                  className="px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-green-500/50 text-white rounded-lg"
                >
                  Confirm
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowAuthorizeConfirm(true)}
                className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg flex items-center gap-2"
              >
                <CreditCard className="h-4 w-4" />
                Authorize Payout
              </button>
            )}
          </div>
        )}

        {/* Claim Closed */}
        {claim.status === 'CLOSED' && (
          <div className="p-4 border border-white/10 rounded-lg bg-white/5 text-center">
            <CheckCircle className="h-8 w-8 text-green-400 mx-auto mb-2" />
            <h4 className="font-medium text-white">Claim Closed</h4>
            <p className="text-sm text-white/60">
              This claim has been closed.
            </p>
          </div>
        )}
      </div>

      {/* History */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-4">
        <div className="flex items-center mb-4">
          <History className="h-4 w-4 mr-2 text-white/60" />
          <h3 className="font-semibold text-white">Claim History</h3>
        </div>
        <div className="space-y-4">
          {history && Array.isArray(history) && history.length > 0 ? (
            history.map((event: any, index: number) => (
              <div key={event.id || index} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                  {index < history.length - 1 && (
                    <div className="w-px h-full bg-white/20" />
                  )}
                </div>
                <div className="flex-1 pb-4">
                  <div className="flex justify-between">
                    <span className="font-medium text-white">
                      {event.event_type || 'Event'}
                    </span>
                    <span className="text-sm text-white/60">
                      {event.created_at
                        ? formatDateTime(event.created_at)
                        : 'N/A'}
                    </span>
                  </div>
                  {event.from_status && event.to_status && (
                    <p className="text-sm text-white/60">
                      {event.from_status} → {event.to_status}
                    </p>
                  )}
                  {event.payload?.notes && (
                    <p className="text-sm text-white/70 mt-1">
                      {event.payload.notes}
                    </p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-white/60 text-sm">No history available.</p>
          )}
        </div>
      </div>
    </div>
  );
}
