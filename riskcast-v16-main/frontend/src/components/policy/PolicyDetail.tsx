/**
 * Policy Detail Component
 *
 * Displays full policy details with tabs.
 */

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Shield,
  FileText,
  Download,
  CheckCircle,
  AlertTriangle,
  Clock,
  DollarSign,
  MapPin,
  Truck,
  Calendar,
} from 'lucide-react';

import { policyApi, claimsApi } from '../../api/client';
import { formatCurrency, formatDate } from '../../utils/format';
import { StatusBadge } from '../common/StatusBadge';

interface Policy {
  id: string;
  policy_number: string;
  status: 'ACTIVE' | 'EXPIRED' | 'CANCELLED' | 'CLAIMED';
  effective_from: string;
  effective_to: string;
  terms: {
    coverage_type: string;
    insured_value_cents: number;
    deductible_cents: number;
    cargo_type?: string;
    container_count?: number;
    origin_port?: string;
    destination_port?: string;
    carrier_code?: string;
    extensions?: string[];
    exclusions?: string[];
  };
  premium: {
    total_premium_cents: number;
    currency: string;
  };
  policyholder: {
    company_name: string;
    contact_email?: string;
    address?: string;
  };
  risk_snapshot?: {
    overall_risk_score: number;
  };
  model_version_id?: string;
  quote_id?: string;
  risk_run_id?: string;
  policy_hash?: string;
}

interface PolicyVerification {
  valid: boolean;
  stored_hash?: string;
  computed_hash?: string;
  verified_at?: string;
}

export function PolicyDetail() {
  const { policyId } = useParams<{ policyId: string }>();
  const [activeTab, setActiveTab] = useState<'details' | 'coverage' | 'claims' | 'timeline' | 'provenance'>('details');

  const { data: policy, isLoading, error } = useQuery<Policy | undefined>({
    queryKey: ['policy', policyId],
    queryFn: async () => {
      const response = await policyApi.getPolicy(policyId!);
      return response.data;
    },
    enabled: !!policyId,
  });

  const { data: verificationResult } = useQuery<PolicyVerification | undefined>({
    queryKey: ['policy-verify', policyId],
    queryFn: async () => {
      const response = await policyApi.verifyPolicy(policyId!);
      return response.data;
    },
    enabled: !!policyId,
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60">Loading policy...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-red-200 mb-2">Error Loading Policy</h2>
          <p className="text-red-300">
            {error instanceof Error ? error.message : 'Failed to load policy details'}
          </p>
        </div>
      </div>
    );
  }

  if (!policy) {
    return (
      <div className="p-6">
        <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-6">
          <p className="text-yellow-200">Policy not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white">{policy.policy_number}</h1>
            <StatusBadge status={policy.status} />
            {verificationResult?.valid && (
              <span className="px-3 py-1 rounded-full text-xs font-medium border border-green-500/60 text-green-300 inline-flex items-center">
                <CheckCircle className="h-3 w-3 mr-1" />
                Verified
              </span>
            )}
          </div>
          <p className="text-white/60 mt-1">
            {policy.policyholder.company_name}
          </p>
        </div>

        <div className="flex gap-2">
          <a
            href={`/api/v3/policies/${policy.id}/document`}
            className="inline-flex items-center px-3 py-2 rounded-lg border border-white/20 text-white text-sm bg-white/5 hover:bg-white/10"
          >
            <FileText className="mr-2 h-4 w-4" />
            Policy Document
          </a>
          <a
            href={`/api/v3/compliance/policies/${policy.id}/decision-pack`}
            className="inline-flex items-center px-3 py-2 rounded-lg border border-white/20 text-white text-sm bg-white/5 hover:bg-white/10"
          >
            <Download className="mr-2 h-4 w-4" />
            Decision Pack
          </a>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
          <div className="flex items-center mb-2 text-white/60 text-sm">
            <DollarSign className="h-4 w-4 mr-2" />
            Insured Value
          </div>
          <div className="text-2xl font-bold text-white">
            {formatCurrency(policy.terms.insured_value_cents / 100)}
          </div>
          <p className="text-xs text-white/60 mt-1">
            {policy.terms.coverage_type}
          </p>
        </div>

        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
          <div className="flex items-center mb-2 text-white/60 text-sm">
            <Shield className="h-4 w-4 mr-2" />
            Premium
          </div>
          <div className="text-2xl font-bold text-white">
            {formatCurrency(policy.premium.total_premium_cents / 100)}
          </div>
          <p className="text-xs text-white/60 mt-1">
            {policy.premium.currency}
          </p>
        </div>

        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
          <div className="flex items-center mb-2 text-white/60 text-sm">
            <Calendar className="h-4 w-4 mr-2" />
            Coverage Period
          </div>
          <div className="text-lg font-bold text-white">
            {formatDate(policy.effective_from)}
          </div>
          <p className="text-xs text-white/60 mt-1">
            to {formatDate(policy.effective_to)}
          </p>
        </div>

        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
          <div className="flex items-center mb-2 text-white/60 text-sm">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Risk Score
          </div>
          <div className="text-2xl font-bold text-white">
            {policy.risk_snapshot
              ? `${(policy.risk_snapshot.overall_risk_score * 100).toFixed(1)}%`
              : 'N/A'}
          </div>
          <p className="text-xs text-white/60 mt-1">
            At time of binding
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div>
        <div className="flex gap-2 border-b border-white/10 mb-4">
          {['details', 'coverage', 'claims', 'timeline', 'provenance'].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                activeTab === tab
                  ? 'text-white border-blue-500'
                  : 'text-white/60 border-transparent hover:text-white'
              }`}
            >
              {tab === 'details' && 'Details'}
              {tab === 'coverage' && 'Coverage'}
              {tab === 'claims' && 'Claims'}
              {tab === 'timeline' && 'Timeline'}
              {tab === 'provenance' && 'Provenance'}
            </button>
          ))}
        </div>

        {activeTab === 'details' && <PolicyDetailsTab policy={policy} />}
        {activeTab === 'coverage' && <PolicyCoverageTab policy={policy} />}
        {activeTab === 'claims' && <PolicyClaims policyId={policy.id} />}
        {activeTab === 'timeline' && <PolicyTimeline policyId={policy.id} />}
        {activeTab === 'provenance' && (
          <PolicyProvenance policy={policy} verification={verificationResult} />
        )}
      </div>
    </div>
  );
}

function PolicyDetailsTab({ policy }: { policy: Policy }) {
  return (
    <div className="space-y-4">
      <div className="bg-white/5 border border-white/10 rounded-lg p-4 grid md:grid-cols-2 gap-6">
        <div className="space-y-3">
          <h4 className="font-medium text-white flex items-center">
            <Truck className="h-4 w-4 mr-2" />
            Shipment
          </h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-white/60">Cargo Type</span>
            <span className="text-white">
              {policy.terms.cargo_type || 'N/A'}
            </span>
            <span className="text-white/60">Containers</span>
            <span className="text-white">
              {policy.terms.container_count ?? 'N/A'}
            </span>
          </div>
        </div>

        <div className="space-y-3">
          <h4 className="font-medium text-white flex items-center">
            <MapPin className="h-4 w-4 mr-2" />
            Route
          </h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-white/60">Origin</span>
            <span className="text-white">
              {policy.terms.origin_port || 'N/A'}
            </span>
            <span className="text-white/60">Destination</span>
            <span className="text-white">
              {policy.terms.destination_port || 'N/A'}
            </span>
            <span className="text-white/60">Carrier</span>
            <span className="text-white">
              {policy.terms.carrier_code || 'Any'}
            </span>
          </div>
        </div>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-lg p-4">
        <h4 className="font-medium text-white mb-3">Policyholder</h4>
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-white/60">Company</span>
            <p className="font-medium text-white">
              {policy.policyholder.company_name}
            </p>
          </div>
          {policy.policyholder.contact_email && (
            <div>
              <span className="text-white/60">Contact</span>
              <p className="font-medium text-white">
                {policy.policyholder.contact_email}
              </p>
            </div>
          )}
          {policy.policyholder.address && (
            <div className="md:col-span-2">
              <span className="text-white/60">Address</span>
              <p className="font-medium text-white">
                {policy.policyholder.address}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PolicyCoverageTab({ policy }: { policy: Policy }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-6">
      <div className="grid md:grid-cols-3 gap-4">
        <div>
          <span className="text-sm text-white/60">Coverage Type</span>
          <p className="text-lg font-medium text-white mt-1">
            {policy.terms.coverage_type}
          </p>
        </div>
        <div>
          <span className="text-sm text-white/60">Insured Value</span>
          <p className="text-lg font-medium text-white mt-1">
            {formatCurrency(policy.terms.insured_value_cents / 100)}
          </p>
        </div>
        <div>
          <span className="text-sm text_white/60">Deductible</span>
          <p className="text-lg font-medium text-white mt-1">
            {formatCurrency(policy.terms.deductible_cents / 100)}
          </p>
        </div>
      </div>

      {policy.terms.extensions && policy.terms.extensions.length > 0 && (
        <div>
          <h4 className="font-medium text-white mb-2">Extensions</h4>
          <div className="flex flex-wrap gap-2">
            {policy.terms.extensions.map((ext) => (
              <span
                key={ext}
                className="px-2 py-1 rounded-full text-xs bg-white/10 text-white border border-white/20"
              >
                {ext}
              </span>
            ))}
          </div>
        </div>
      )}

      {policy.terms.exclusions && policy.terms.exclusions.length > 0 && (
        <div>
          <h4 className="font-medium text-white mb-2">Exclusions</h4>
          <ul className="list-disc list-inside text-sm text-white/70">
            {policy.terms.exclusions.map((excl, idx) => (
              <li key={idx}>{excl}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PolicyClaims({ policyId }: { policyId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['policy-claims', policyId],
    queryFn: async () => {
      const response = await claimsApi.listClaims({ policy_id: policyId });
      return response.data;
    },
    enabled: !!policyId,
  });

  const claims = data?.items || [];

  if (isLoading) {
    return <div className="text-white/60">Loading claims...</div>;
  }

  if (!claims.length) {
    return <div className="text-white/60">No claims filed on this policy.</div>;
  }

  return (
    <div className="space-y-3">
      {claims.map((claim: any) => (
        <div
          key={claim.id}
          className="bg-white/5 border border-white/10 rounded-lg p-4 flex justify-between items-center"
        >
          <div>
            <p className="text-white font-medium">Claim {claim.id}</p>
            <p className="text-xs text-white/60">
              Status: {claim.status} • Created {formatDate(claim.created_at)}
            </p>
          </div>
          <StatusBadge status={claim.status} />
        </div>
      ))}
    </div>
  );
}

function PolicyTimeline({ policyId }: { policyId: string }) {
  // Placeholder timeline for now – can be wired to audit events later
  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-4 text-white/70 text-sm">
      <p>
        Timeline view for policy <span className="font-mono">{policyId}</span> will
        show underwriting, binding, and claims events based on audit logs.
      </p>
    </div>
  );
}

function PolicyProvenance({
  policy,
  verification,
}: {
  policy: Policy;
  verification?: PolicyVerification;
}) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-4 text-sm text-white">
      <div>
        <h4 className="font-medium text-white mb-2">Hashes</h4>
        <div className="space-y-1 font-mono text-xs">
          <div className="flex justify-between gap-4">
            <span className="text-white/60">Policy Hash</span>
            <span className="truncate">
              {policy.policy_hash || verification?.stored_hash || 'N/A'}
            </span>
          </div>
          {verification?.computed_hash && (
            <div className="flex justify-between gap-4">
              <span className="text-white/60">Computed Hash</span>
              <span className="truncate">
                {verification.computed_hash}
              </span>
            </div>
          )}
        </div>
        {verification && (
          <p className="text-xs mt-2">
            Integrity:{' '}
            <span
              className={
                verification.valid
                  ? 'text-green-300'
                  : 'text-red-300'
              }
            >
              {verification.valid ? 'Valid' : 'Invalid'}
            </span>
            {verification.verified_at && (
              <span className="text-white/60">
                {' '}
                • Verified {formatDate(verification.verified_at)}
              </span>
            )}
          </p>
        )}
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div>
          <span className="text-white/60">Model Version</span>
          <p className="font-mono text-xs text-white mt-1">
            {policy.model_version_id || 'N/A'}
          </p>
        </div>
        <div>
          <span className="text_white/60">Risk Run</span>
          <p className="font-mono text-xs text-white mt-1">
            {policy.risk_run_id || 'N/A'}
          </p>
        </div>
        <div>
          <span className="text-white/60">Quote</span>
          <p className="font-mono text-xs text_white mt-1">
            {policy.quote_id || 'N/A'}
          </p>
        </div>
      </div>

      <p className="text-xs text-white/60">
        Provenance chains policy to the exact model version, risk run, and quote used at
        binding time for auditability.
      </p>
    </div>
  );
}

