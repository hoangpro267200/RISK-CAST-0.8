/**
 * Underwriting Dashboard
 * 
 * Kanban-style board for managing underwriting submissions.
 */

import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  PlusCircle,
  Clock,
  AlertTriangle,
  CheckCircle,
  FileText,
  DollarSign,
  User,
  RefreshCw,
} from 'lucide-react';

import { underwritingApi } from '../../api/client';
import { formatCurrency, formatDate, formatRelativeTime } from '../../utils/format';
import { StatusBadge } from '../common/StatusBadge';

interface Submission {
  id: string;
  submission_number?: string;
  status: string;
  requested_coverage_json?: {
    coverage_type?: string;
    insured_value_cents?: number;
  };
  applicant?: {
    company_name?: string;
  };
  risk_assessment?: {
    risk_score?: number;
  };
  risk_assessment_id?: string;
  assigned_to_user_id?: string;
  expires_at?: string;
  created_at: string;
}

const COLUMNS = [
  { id: 'DRAFT', title: 'Draft', color: 'bg-gray-500/20', borderColor: 'border-gray-500/50' },
  { id: 'SUBMITTED', title: 'Submitted', color: 'bg-blue-500/20', borderColor: 'border-blue-500/50' },
  { id: 'UNDER_REVIEW', title: 'Under Review', color: 'bg-purple-500/20', borderColor: 'border-purple-500/50' },
  { id: 'REQUESTED_INFO', title: 'Info Requested', color: 'bg-yellow-500/20', borderColor: 'border-yellow-500/50' },
  { id: 'QUOTED', title: 'Quoted', color: 'bg-green-500/20', borderColor: 'border-green-500/50' },
];

export function UnderwritingDashboard() {
  const queryClient = useQueryClient();

  const { data: submissionsResponse, isLoading, refetch } = useQuery({
    queryKey: ['underwriting-submissions'],
    queryFn: async () => {
      const response = await underwritingApi.listSubmissions();
      return response.data;
    },
    refetchInterval: 30000,
  });

  const submissions: Submission[] = Array.isArray(submissionsResponse)
    ? submissionsResponse
    : submissionsResponse?.items || [];

  const transitionMutation = useMutation({
    mutationFn: ({ submissionId, action, data }: { submissionId: string; action: string; data?: any }) =>
      underwritingApi.transitionSubmission(submissionId, action, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['underwriting-submissions'] });
    },
  });

  const columnSubmissions = useMemo(() => {
    const grouped: Record<string, Submission[]> = {};
    COLUMNS.forEach((col) => (grouped[col.id] = []));

    submissions.forEach((sub: Submission) => {
      if (grouped[sub.status]) {
        grouped[sub.status]!.push(sub);
      } else {
        // Put in DRAFT if status doesn't match any column
        grouped['DRAFT']!.push(sub);
      }
    });

    return grouped;
  }, [submissions]);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60">Loading submissions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Underwriting</h1>
          <p className="text-white/60 mt-1">
            Manage submissions and quotes
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
          <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white transition-colors flex items-center gap-2">
            <PlusCircle className="h-4 w-4" />
            New Submission
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-5">
        {COLUMNS.map((col) => (
          <div
            key={col.id}
            className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4"
          >
            <div className="flex items-center mb-2 text-white/60 text-sm">
              {col.title}
            </div>
            <div className="text-2xl font-bold text-white">
              {columnSubmissions[col.id]?.length || 0}
            </div>
          </div>
        ))}
      </div>

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {COLUMNS.map((column) => (
          <div key={column.id} className="flex-shrink-0 w-80">
            <div
              className={`rounded-t-lg px-4 py-2 ${column.color} border ${column.borderColor}`}
            >
              <h3 className="font-medium text-white flex items-center justify-between">
                {column.title}
                <span className="px-2 py-1 rounded-full text-xs bg-white/20 text-white">
                  {columnSubmissions[column.id]?.length || 0}
                </span>
              </h3>
            </div>

            <div
              className={`min-h-[500px] p-2 rounded-b-lg border border-t-0 ${column.borderColor} bg-white/5`}
            >
              {columnSubmissions[column.id]?.map((submission) => (
                <SubmissionCard
                  key={submission.id}
                  submission={submission}
                  onTransition={(action, data) =>
                    transitionMutation.mutate({
                      submissionId: submission.id,
                      action,
                      data,
                    })
                  }
                />
              ))}
              {(!columnSubmissions[column.id] || columnSubmissions[column.id]?.length === 0) && (
                <div className="text-center py-8 text-white/40 text-sm">
                  No submissions
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SubmissionCard({
  submission,
  onTransition,
}: {
  submission: Submission;
  onTransition: (action: string, data?: any) => void;
}) {
  const [showDetails, setShowDetails] = useState(false);
  const isExpiringSoon =
    submission.expires_at &&
    new Date(submission.expires_at) < new Date(Date.now() + 24 * 60 * 60 * 1000);

  const submissionNumber =
    submission.submission_number || submission.id.slice(0, 8);
  const companyName =
    submission.applicant?.company_name ||
    submission.requested_coverage_json?.coverage_type ||
    'N/A';
  const insuredValue =
    submission.requested_coverage_json?.insured_value_cents || 0;
  const riskScore = submission.risk_assessment?.risk_score;

  return (
    <div
      className={`mb-2 bg-white/5 border rounded-lg p-3 cursor-pointer hover:bg-white/10 transition-all ${
        isExpiringSoon ? 'border-orange-500/50 bg-orange-500/10' : 'border-white/10'
      }`}
      onClick={() => setShowDetails(!showDetails)}
    >
      <div className="flex justify-between items-start mb-2">
        <span className="font-mono text-sm font-medium text-white">
          {submissionNumber}
        </span>
        {riskScore !== undefined && (
          <RiskScoreBadge score={riskScore} />
        )}
      </div>

      <p className="text-sm font-medium text-white truncate mb-2">
        {companyName}
      </p>

      <div className="flex items-center justify-between text-xs text-white/60 mb-2">
        <span className="flex items-center">
          <DollarSign className="h-3 w-3 mr-1" />
          {insuredValue > 0
            ? formatCurrency(insuredValue / 100)
            : 'N/A'}
        </span>
        <span className="flex items-center">
          <Clock className="h-3 w-3 mr-1" />
          {formatRelativeTime(submission.created_at)}
        </span>
      </div>

      {isExpiringSoon && (
        <div className="flex items-center mt-2 text-xs text-orange-300">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Expires {formatRelativeTime(submission.expires_at!)}
        </div>
      )}

      {submission.assigned_to_user_id && (
        <div className="flex items-center mt-2">
          <div className="h-5 w-5 rounded-full bg-blue-500/20 border border-blue-500/50 flex items-center justify-center">
            <User className="h-3 w-3 text-blue-300" />
          </div>
          <span className="ml-2 text-xs text-white/60">
            Assigned
          </span>
        </div>
      )}

      {/* Expanded Details */}
      {showDetails && (
        <div className="mt-3 pt-3 border-t border-white/10 space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-white/60">Coverage:</span>
              <p className="text-white">
                {submission.requested_coverage_json?.coverage_type || 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-white/60">Value:</span>
              <p className="text-white">
                {insuredValue > 0
                  ? formatCurrency(insuredValue / 100)
                  : 'N/A'}
              </p>
            </div>
            {riskScore !== undefined && (
              <div>
                <span className="text-white/60">Risk Score:</span>
                <p className="text-white">
                  {(riskScore * 100).toFixed(1)}%
                </p>
              </div>
            )}
          </div>

          <div className="flex gap-2 mt-3">
            <Link
              to={`/app/underwriting/submissions/${submission.id}`}
              className="flex-1 px-3 py-1.5 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-center transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              View Details
            </Link>
            
            {/* Quick Actions */}
            {submission.status === 'DRAFT' && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onTransition('submit');
                }}
                className="px-3 py-1.5 text-xs bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
              >
                Submit
              </button>
            )}
            {submission.status === 'SUBMITTED' && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onTransition('review');
                }}
                className="px-3 py-1.5 text-xs bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
              >
                Review
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function RiskScoreBadge({ score }: { score: number }) {
  const percentage = score * 100;
  let className = 'px-2 py-1 rounded text-xs font-medium ';

  if (percentage > 70) {
    className += 'bg-red-500/20 text-red-300 border border-red-500/50';
  } else if (percentage > 40) {
    className += 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50';
  } else {
    className += 'bg-green-500/20 text-green-300 border border-green-500/50';
  }

  return <span className={className}>{percentage.toFixed(0)}%</span>;
}
