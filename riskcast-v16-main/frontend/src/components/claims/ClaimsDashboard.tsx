/**
 * Claims Dashboard
 * 
 * Dashboard for managing claims workflow.
 */

import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  PlusCircle,
  AlertCircle,
  Clock,
  CheckCircle,
  XCircle,
  DollarSign,
  FileSearch,
  UserCheck,
  Banknote,
  RefreshCw,
} from 'lucide-react';

import { claimsApi } from '../../api/client';
import { formatCurrency, formatDate } from '../../utils/format';
import { StatusBadge } from '../common/StatusBadge';
import { ClaimFilingForm } from './ClaimFilingForm';
import { ClaimDetail } from './ClaimDetail';

interface Claim {
  id: string;
  claim_number: string;
  policy_id: string;
  status: string;
  fnol: {
    loss_date: string;
    loss_type: string;
    loss_description: string;
    loss_location?: string;
    estimated_loss_cents: number;
  };
  approved_amount_cents?: number;
  assigned_adjuster_id?: string;
  created_at: string;
}

const CLAIM_STATUSES = [
  'FNOL_RECEIVED',
  'UNDER_INVESTIGATION',
  'AWAITING_EVIDENCE',
  'APPROVED',
  'DECLINED',
  'AUTHORIZED',
  'PAID',
  'CLOSED',
  'WITHDRAWN',
];

export function ClaimsDashboard() {
  const queryClient = useQueryClient();
  const [isFileClaimOpen, setIsFileClaimOpen] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [activeTab, setActiveTab] = useState('all');

  const { data: claimsResponse, isLoading, refetch } = useQuery({
    queryKey: ['claims'],
    queryFn: async () => {
      const response = await claimsApi.listClaims();
      return response.data;
    },
    refetchInterval: 30000,
  });

  const claims: Claim[] = Array.isArray(claimsResponse)
    ? claimsResponse
    : claimsResponse?.items || [];

  const { data: stats } = useQuery({
    queryKey: ['claims-stats'],
    queryFn: async () => {
      const response = await claimsApi.getClaimsStats();
      return response.data;
    },
  });

  const fileClaimMutation = useMutation({
    mutationFn: async (data: { policy_id: string; fnol: any }) => {
      const response = await claimsApi.fileClaim(data.policy_id, data.fnol);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claims'] });
      queryClient.invalidateQueries({ queryKey: ['claims-stats'] });
      setIsFileClaimOpen(false);
    },
  });

  const filteredClaims = useMemo(() => {
    if (!claims || claims.length === 0) return [];

    switch (activeTab) {
      case 'open':
        return claims.filter(
          (c) => !['CLOSED', 'WITHDRAWN', 'PAID'].includes(c.status)
        );
      case 'pending_action':
        return claims.filter((c) =>
          ['FNOL_RECEIVED', 'AWAITING_EVIDENCE'].includes(c.status)
        );
      case 'approved':
        return claims.filter((c) =>
          ['APPROVED', 'AUTHORIZED', 'PAID'].includes(c.status)
        );
      default:
        return claims;
    }
  }, [claims, activeTab]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Claims</h1>
          <p className="text-white/60 mt-1">
            Manage and process insurance claims
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-colors flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            onClick={() => setIsFileClaimOpen(true)}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white transition-colors flex items-center gap-2"
          >
            <PlusCircle className="h-4 w-4" />
            File New Claim
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-5">
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <AlertCircle className="h-4 w-4 mr-2 text-orange-400" />
              Open Claims
            </div>
            <div className="text-2xl font-bold text-white">
              {stats.open_claims || 0}
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <Clock className="h-4 w-4 mr-2 text-blue-400" />
              Pending Review
            </div>
            <div className="text-2xl font-bold text-white">
              {stats.pending_review || 0}
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <FileSearch className="h-4 w-4 mr-2 text-purple-400" />
              Under Investigation
            </div>
            <div className="text-2xl font-bold text-white">
              {stats.under_investigation || 0}
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <DollarSign className="h-4 w-4 mr-2 text-green-400" />
              Total Paid (MTD)
            </div>
            <div className="text-2xl font-bold text-white">
              {formatCurrency((stats.total_paid_mtd || 0) / 100)}
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
            <div className="flex items-center mb-2 text-white/60 text-sm">
              <Banknote className="h-4 w-4 mr-2 text-yellow-400" />
              Total Reserved
            </div>
            <div className="text-2xl font-bold text-white">
              {formatCurrency((stats.total_reserved || 0) / 100)}
            </div>
          </div>
        </div>
      )}

      {/* Claims Pipeline */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Claims Pipeline</h2>
        <ClaimsPipeline claims={claims} />
      </div>

      {/* Claims List */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg">
        <div className="p-4 border-b border-white/10">
          <div className="flex gap-2">
            {['all', 'open', 'pending_action', 'approved'].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === tab
                    ? 'bg-blue-500 text-white'
                    : 'bg-white/10 text-white/60 hover:bg-white/20'
                }`}
              >
                {tab === 'all' && 'All Claims'}
                {tab === 'open' && 'Open'}
                {tab === 'pending_action' && 'Pending Action'}
                {tab === 'approved' && 'Approved/Paid'}
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 overflow-x-auto">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-white/40" />
            </div>
          ) : filteredClaims.length === 0 ? (
            <div className="text-center py-12 text-white/60">
              No claims found.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-white/60">
                  <th className="text-left py-2 px-3 font-medium">Claim Number</th>
                  <th className="text-left py-2 px-3 font-medium">Status</th>
                  <th className="text-left py-2 px-3 font-medium">Loss Type</th>
                  <th className="text-left py-2 px-3 font-medium">Estimated Loss</th>
                  <th className="text-left py-2 px-3 font-medium">Approved Amount</th>
                  <th className="text-left py-2 px-3 font-medium">Loss Date</th>
                  <th className="text-left py-2 px-3 font-medium">Adjuster</th>
                  <th className="text-left py-2 px-3 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {filteredClaims.map((claim) => (
                  <tr
                    key={claim.id}
                    className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                    onClick={() => setSelectedClaim(claim)}
                  >
                    <td className="py-2 px-3 font-medium text-white">
                      {claim.claim_number || claim.id.slice(0, 8)}
                    </td>
                    <td className="py-2 px-3">
                      <ClaimStatusBadge status={claim.status} />
                    </td>
                    <td className="py-2 px-3 text-white/90">
                      {claim.fnol?.loss_type || 'N/A'}
                    </td>
                    <td className="py-2 px-3 text-white/90">
                      {claim.fnol?.estimated_loss_cents
                        ? formatCurrency(claim.fnol.estimated_loss_cents / 100)
                        : '-'}
                    </td>
                    <td className="py-2 px-3 text-white/90">
                      {claim.approved_amount_cents
                        ? formatCurrency(claim.approved_amount_cents / 100)
                        : '-'}
                    </td>
                    <td className="py-2 px-3 text-white/80">
                      {claim.fnol?.loss_date
                        ? formatDate(claim.fnol.loss_date)
                        : formatDate(claim.created_at)}
                    </td>
                    <td className="py-2 px-3">
                      {claim.assigned_adjuster_id ? (
                        <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-300 border border-green-500/50 inline-flex items-center">
                          <UserCheck className="h-3 w-3 mr-1" />
                          Assigned
                        </span>
                      ) : (
                        <span className="px-2 py-1 rounded-full text-xs bg-white/10 text-white/60 border border-white/20">
                          Unassigned
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      <button className="text-blue-400 hover:text-blue-300 text-sm">
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* File Claim Dialog */}
      {isFileClaimOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-white/10 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-white/10">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-white">
                  File First Notice of Loss (FNOL)
                </h2>
                <button
                  onClick={() => setIsFileClaimOpen(false)}
                  className="text-white/60 hover:text-white"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6">
              <ClaimFilingForm
                onSubmit={(data) => fileClaimMutation.mutate(data)}
                isLoading={fileClaimMutation.isPending}
                error={
                  fileClaimMutation.error instanceof Error
                    ? fileClaimMutation.error.message
                    : undefined
                }
              />
            </div>
          </div>
        </div>
      )}

      {/* Claim Detail Dialog */}
      {selectedClaim && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-white/10 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-white/10">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-white">Claim Details</h2>
                <button
                  onClick={() => setSelectedClaim(null)}
                  className="text-white/60 hover:text-white"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6">
              <ClaimDetail
                claimId={selectedClaim.id}
                onClose={() => setSelectedClaim(null)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ClaimsPipeline({ claims }: { claims: Claim[] }) {
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    CLAIM_STATUSES.forEach((s) => (counts[s] = 0));
    claims.forEach((c) => {
      const currentCount = counts[c.status];
      if (currentCount !== undefined) {
        counts[c.status] = currentCount + 1;
      }
    });
    return counts;
  }, [claims]);

  const stages = [
    { status: 'FNOL_RECEIVED', label: 'FNOL', color: 'bg-blue-500' },
    {
      status: 'UNDER_INVESTIGATION',
      label: 'Investigation',
      color: 'bg-purple-500',
    },
    {
      status: 'AWAITING_EVIDENCE',
      label: 'Awaiting Evidence',
      color: 'bg-yellow-500',
    },
    { status: 'APPROVED', label: 'Approved', color: 'bg-green-500' },
    { status: 'AUTHORIZED', label: 'Authorized', color: 'bg-teal-500' },
    { status: 'PAID', label: 'Paid', color: 'bg-emerald-500' },
  ];

  const total = claims.filter(
    (c) => !['CLOSED', 'WITHDRAWN', 'DECLINED'].includes(c.status)
  ).length;

  return (
    <div className="space-y-4">
      <div className="flex justify-between text-sm text-white/60 mb-2">
        <span>Pipeline Progress</span>
        <span>{total} active claims</span>
      </div>

      <div className="flex gap-1 h-4 rounded-full overflow-hidden bg-white/10">
        {stages.map((stage) => {
          const count = statusCounts[stage.status] ?? 0;
          const width = total > 0 ? (count / total) * 100 : 0;

          return width > 0 ? (
            <div
              key={stage.status}
              className={`${stage.color} transition-all`}
              style={{ width: `${width}%` }}
              title={`${stage.label}: ${count}`}
            />
          ) : null;
        })}
      </div>

      <div className="grid grid-cols-6 gap-2 text-center text-xs">
        {stages.map((stage) => (
          <div key={stage.status}>
            <div
              className={`w-3 h-3 rounded-full ${stage.color} mx-auto mb-1`}
            />
            <div className="font-medium text-white">{statusCounts[stage.status]}</div>
            <div className="text-white/60">{stage.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ClaimStatusBadge({ status }: { status: string }) {
  return <StatusBadge status={status} />;
}
