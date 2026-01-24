/**
 * Risk Assessment Dashboard
 * 
 * Main dashboard for creating and viewing risk assessments.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  PlusCircle, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  FileText,
  TrendingUp,
  Shield
} from 'lucide-react';

import { riskApi } from '../../api/client';
import { RiskAssessmentForm } from './RiskAssessmentForm';
import { RiskScoreGauge } from './RiskScoreGauge';
import { RiskFactorsChart } from './RiskFactorsChart';
import { StatusBadge } from '../common/StatusBadge';
import { formatCurrency, formatDate } from '../../utils/format';

interface RiskAssessment {
  id: string;
  input_hash: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  result?: {
    risk_score: number;
    var_95: number;
    var_99: number;
    expected_loss: number;
    risk_factors: Record<string, number>;
  };
  provenance?: {
    model_version_id: string;
    model_version_name: string;
    risk_run_id: string;
    result_hash: string;
  };
}

export function RiskAssessmentDashboard() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState<RiskAssessment | null>(null);

  // Fetch assessments
  const { 
    data: assessmentsResponse, 
    isLoading, 
    error,
    refetch
  } = useQuery({
    queryKey: ['risk-assessments'],
    queryFn: async () => {
      const response = await riskApi.listAssessments({ limit: 50 });
      return response.data;
    },
    refetchInterval: 10000, // Refresh every 10s for running assessments
  });

  const assessments: RiskAssessment[] = Array.isArray(assessmentsResponse) 
    ? assessmentsResponse 
    : assessmentsResponse?.items || [];

  // Create assessment mutation
  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await riskApi.createAssessment(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk-assessments'] });
      setIsCreateOpen(false);
    },
  });

  // Stats
  const stats = React.useMemo(() => {
    if (!assessments || assessments.length === 0) return null;
    
    const completed = assessments.filter(a => a.status === 'COMPLETED');
    const avgRiskScore = completed.length > 0
      ? completed.reduce((sum, a) => sum + (a.result?.risk_score || 0), 0) / completed.length
      : 0;
    
    return {
      total: assessments.length,
      completed: completed.length,
      running: assessments.filter(a => a.status === 'RUNNING').length,
      avgRiskScore,
    };
  }, [assessments]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Risk Assessments</h1>
          <p className="text-white/60 mt-1">
            Create and manage cargo insurance risk assessments
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
            onClick={() => setIsCreateOpen(true)}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white transition-colors flex items-center gap-2"
          >
            <PlusCircle className="h-4 w-4" />
            New Assessment
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-white/60">Total Assessments</h3>
              <FileText className="h-4 w-4 text-white/40" />
            </div>
            <div className="text-2xl font-bold text-white">{stats.total}</div>
          </div>
          
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-white/60">Completed</h3>
              <CheckCircle className="h-4 w-4 text-green-400" />
            </div>
            <div className="text-2xl font-bold text-white">{stats.completed}</div>
          </div>
          
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-white/60">Running</h3>
              <Clock className="h-4 w-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white">{stats.running}</div>
          </div>
          
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-white/60">Avg Risk Score</h3>
              <TrendingUp className="h-4 w-4 text-white/40" />
            </div>
            <div className="text-2xl font-bold text-white">
              {(stats.avgRiskScore * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Assessments List */}
        <div className="lg:col-span-2 bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-white">Recent Assessments</h2>
            <p className="text-sm text-white/60 mt-1">
              View and manage your risk assessments
            </p>
          </div>
          
          {isLoading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-white/40" />
            </div>
          ) : error ? (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-red-300" />
                <h3 className="text-red-200 font-medium">Error</h3>
              </div>
              <p className="text-red-300 text-sm">
                Failed to load assessments: {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          ) : assessments.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-white/20 mx-auto mb-4" />
              <p className="text-white/60">No assessments yet. Create your first assessment to get started.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/60">ID</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Risk Score</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/60">VaR 95%</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Created</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/60"></th>
                  </tr>
                </thead>
                <tbody>
                  {assessments.map((assessment) => (
                    <tr 
                      key={assessment.id}
                      className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                      onClick={() => setSelectedAssessment(assessment)}
                    >
                      <td className="py-3 px-4">
                        <span className="font-mono text-sm text-white/80">
                          {assessment.id.slice(0, 8)}...
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge status={assessment.status} />
                      </td>
                      <td className="py-3 px-4">
                        {assessment.result ? (
                          <RiskScoreBadge score={assessment.result.risk_score} />
                        ) : (
                          <span className="text-white/40">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {assessment.result ? (
                          <span className="text-white/80">
                            {formatCurrency(assessment.result.var_95)}
                          </span>
                        ) : (
                          <span className="text-white/40">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-white/60 text-sm">
                          {formatDate(assessment.created_at)}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <button className="text-blue-400 hover:text-blue-300 text-sm">
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Assessment Detail */}
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Assessment Details</h2>
          {selectedAssessment ? (
            <AssessmentDetail assessment={selectedAssessment} />
          ) : (
            <div className="text-center py-8 text-white/40">
              Select an assessment to view details
            </div>
          )}
        </div>
      </div>

      {/* Create Dialog */}
      {isCreateOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-white/10 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-white/10">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-white">Create Risk Assessment</h2>
                <button
                  onClick={() => setIsCreateOpen(false)}
                  className="text-white/60 hover:text-white"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6">
              <RiskAssessmentForm
                onSubmit={(data) => createMutation.mutate(data)}
                isLoading={createMutation.isPending}
                error={createMutation.error instanceof Error ? createMutation.error.message : undefined}
              />
            </div>
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
  
  return (
    <span className={className}>
      {percentage.toFixed(1)}%
    </span>
  );
}

function AssessmentDetail({ assessment }: { assessment: RiskAssessment }) {
  return (
    <div className="space-y-6">
      {/* Risk Score Gauge */}
      {assessment.result && (
        <div className="flex justify-center">
          <RiskScoreGauge score={assessment.result.risk_score} />
        </div>
      )}
      
      {/* Key Metrics */}
      {assessment.result && (
        <div className="space-y-3">
          <div className="flex justify-between py-2 border-b border-white/10">
            <span className="text-white/60">Expected Loss</span>
            <span className="font-medium text-white">
              {formatCurrency(assessment.result.expected_loss)}
            </span>
          </div>
          <div className="flex justify-between py-2 border-b border-white/10">
            <span className="text-white/60">VaR 95%</span>
            <span className="font-medium text-white">
              {formatCurrency(assessment.result.var_95)}
            </span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-white/60">VaR 99%</span>
            <span className="font-medium text-white">
              {formatCurrency(assessment.result.var_99)}
            </span>
          </div>
        </div>
      )}
      
      {/* Risk Factors */}
      {assessment.result?.risk_factors && (
        <div>
          <h4 className="font-medium text-white mb-3">Risk Factors</h4>
          <RiskFactorsChart factors={assessment.result.risk_factors} />
        </div>
      )}
      
      {/* Provenance */}
      {assessment.provenance && (
        <div className="pt-4 border-t border-white/10">
          <h4 className="font-medium text-white mb-3 flex items-center">
            <Shield className="h-4 w-4 mr-2" />
            Provenance
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-white/60">Model</span>
              <span className="font-mono text-white/80">
                {assessment.provenance.model_version_name || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/60">Input Hash</span>
              <span className="font-mono text-xs text-white/60">
                {assessment.input_hash.slice(0, 16)}...
              </span>
            </div>
            {assessment.provenance.result_hash && (
              <div className="flex justify-between">
                <span className="text-white/60">Result Hash</span>
                <span className="font-mono text-xs text-white/60">
                  {assessment.provenance.result_hash.slice(0, 16)}...
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
