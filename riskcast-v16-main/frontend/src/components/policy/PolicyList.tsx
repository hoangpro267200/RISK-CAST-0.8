/**
 * Policy List Component
 *
 * Displays list of policies with filtering and actions.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Search,
  MoreHorizontal,
  Eye,
  FileText,
  Download,
  AlertCircle,
} from 'lucide-react';

import { policyApi } from '../../api/client';
import { formatCurrency, formatDate } from '../../utils/format';
import { StatusBadge } from '../common/StatusBadge';

interface Policy {
  id: string;
  policy_number: string;
  status: 'ACTIVE' | 'EXPIRED' | 'CANCELLED' | 'CLAIMED';
  terms: {
    coverage_type: string;
    insured_value_cents: number;
    cargo_type?: string;
    container_count?: number;
    origin_port?: string;
    destination_port?: string;
    carrier_code?: string;
    deductible_cents?: number;
    extensions?: string[];
    exclusions?: string[];
  };
  premium: {
    total_premium_cents: number;
    currency: string;
  };
  effective_from: string;
  effective_to: string;
  policyholder: {
    company_name: string;
    contact_email?: string;
    address?: string;
  };
}

export function PolicyList() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const { data, isLoading, error } = useQuery({
    queryKey: ['policies', { search, status: statusFilter }],
    queryFn: async () => {
      const response = await policyApi.listPolicies({
        search: search || undefined,
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
      });
      return response.data;
    },
  });

  const policies: Policy[] = Array.isArray(data)
    ? data
    : data?.items || [];

  const filteredPolicies = policies.filter((p) => {
    if (search) {
      const searchLower = search.toLowerCase();
      return (
        p.policy_number.toLowerCase().includes(searchLower) ||
        p.policyholder.company_name.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg">
      <div className="p-4 border-b border-white/10 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-white">Policies</h2>
        <div className="flex gap-3 items-center">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
            <input
              placeholder="Search policies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 w-64 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Status</option>
            <option value="ACTIVE">Active</option>
            <option value="EXPIRED">Expired</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="CLAIMED">Claimed</option>
          </select>
        </div>
      </div>

      <div className="p-4 overflow-x-auto">
        {isLoading ? (
          <div className="flex justify-center py-6 text-white/60">
            Loading policies...
          </div>
        ) : error ? (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 flex items-center gap-2 text-sm text-red-200">
            <AlertCircle className="h-4 w-4" />
            <span>Failed to load policies.</span>
          </div>
        ) : filteredPolicies.length === 0 ? (
          <div className="flex justify-center py-6 text-white/60">
            No policies found.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 text-white/60">
                <th className="text-left py-2 px-3 font-medium">Policy Number</th>
                <th className="text-left py-2 px-3 font-medium">Policyholder</th>
                <th className="text-left py-2 px-3 font-medium">Status</th>
                <th className="text-left py-2 px-3 font-medium">Coverage</th>
                <th className="text-left py-2 px-3 font-medium">Premium</th>
                <th className="text-left py-2 px-3 font-medium">Effective Period</th>
                <th className="text-left py-2 px-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {filteredPolicies.map((policy) => (
                <tr
                  key={policy.id}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="py-2 px-3">
                    <Link
                      to={`/app/policies/${policy.id}`}
                      className="text-blue-400 hover:text-blue-300 hover:underline font-medium"
                    >
                      {policy.policy_number}
                    </Link>
                  </td>
                  <td className="py-2 px-3 text-white/90">
                    {policy.policyholder.company_name}
                  </td>
                  <td className="py-2 px-3">
                    <PolicyStatusBadge status={policy.status} />
                  </td>
                  <td className="py-2 px-3 text-white/90">
                    <div>{policy.terms.coverage_type}</div>
                    <div className="text-xs text-white/60">
                      {formatCurrency(policy.terms.insured_value_cents / 100)}
                    </div>
                  </td>
                  <td className="py-2 px-3 text-white/90">
                    {formatCurrency(policy.premium.total_premium_cents / 100)}
                  </td>
                  <td className="py-2 px-3 text-white/80">
                    <div>{formatDate(policy.effective_from)}</div>
                    <div className="text-xs text-white/60">
                      to {formatDate(policy.effective_to)}
                    </div>
                  </td>
                  <td className="py-2 px-3 text-right">
                    <PolicyActions policy={policy} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function PolicyStatusBadge({ status }: { status: string }) {
  // Reuse generic StatusBadge color logic and rely on status text
  return <StatusBadge status={status} />;
}

function PolicyActions({ policy }: { policy: Policy }) {
  return (
    <div className="inline-flex items-center gap-1">
      <Link
        to={`/app/policies/${policy.id}`}
        className="inline-flex items-center px-2 py-1 text-xs rounded-md bg-white/10 text-white hover:bg-white/20"
      >
        <Eye className="h-3 w-3 mr-1" />
        View
      </Link>
      <button
        type="button"
        className="inline-flex items-center px-2 py-1 text-xs rounded-md bg-white/5 text-white/80 hover:bg-white/10"
        onClick={() => {
          window.open(`/api/v3/policies/${policy.id}/document`, '_blank');
        }}
      >
        <FileText className="h-3 w-3 mr-1" />
        Doc
      </button>
      <button
        type="button"
        className="inline-flex items-center px-2 py-1 text-xs rounded-md bg-white/5 text-white/80 hover:bg-white/10"
        onClick={() => {
          window.open(
            `/api/v3/compliance/policies/${policy.id}/decision-pack`,
            '_blank'
          );
        }}
      >
        <Download className="h-3 w-3 mr-1" />
        Pack
      </button>
      {policy.status === 'ACTIVE' && (
        <Link
          to={`/app/claims/new?policy_id=${policy.id}`}
          className="inline-flex items-center px-2 py-1 text-xs rounded-md bg-red-500/20 text-red-200 hover:bg-red-500/30"
        >
          <AlertCircle className="h-3 w-3 mr-1" />
          Claim
        </Link>
      )}
      <button
        type="button"
        className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-white/5 text-white/60 hover:bg-white/10"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>
    </div>
  );
}

