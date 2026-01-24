/**
 * Risk Assessment Page
 * Form to create new assessment and list existing assessments
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '@/components/GlassCard';
import { RunStatusBadge, RunStatus } from '@/components/RunStatusBadge';
import { api } from '@/services/apiClient';

interface RiskAssessment {
  id: string;
  tenant_id: string;
  input_hash: string;
  schema_version: string;
  shipment_id?: string;
  corridor_id?: string;
  created_by_user_id?: string;
  created_at: string;
  updated_at: string;
}

interface RiskAssessmentCreateRequest {
  shipment_data: Record<string, any>;
  corridor_id?: string;
  schema_version?: string;
}

interface RiskAssessmentDetail extends RiskAssessment {
  input_snapshot: Record<string, any>;
  runs: Array<{
    id: string;
    status: string;
    engine_version: string;
    iterations: number;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    result_hash?: string;
  }>;
}

export const RiskAssessmentPage: React.FC = () => {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<RiskAssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Form state
  const [formData, setFormData] = useState<RiskAssessmentCreateRequest>({
    shipment_data: {
      cargo_value: 100000,
      distance: 5000,
      origin: '',
      destination: '',
    },
    schema_version: 'v1',
  });

  // Fetch assessments list
  const fetchAssessments = async () => {
    try {
      const response = await api.get<RiskAssessment[]>('/api/v3/risk/assessments');
      if (response.error) {
        setError(response.error.userMessage);
        return;
      }
      if (response.data) {
        setAssessments(response.data);
      }
    } catch (err) {
      setError('Failed to load assessments');
    } finally {
      setLoading(false);
    }
  };

  // Fetch assessment details
  const fetchAssessmentDetails = async (assessmentId: string) => {
    try {
      const response = await api.get<RiskAssessmentDetail>(`/api/v3/risk/assessments/${assessmentId}`);
      if (response.data) {
        setSelectedAssessment(response.data);
      }
    } catch (err) {
      setError('Failed to load assessment details');
    }
  };

  // Create assessment
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);

    try {
      const response = await api.post<RiskAssessment>('/api/v3/risk/assessments', formData);
      if (response.error) {
        setError(response.error.userMessage);
        return;
      }
      if (response.data) {
        setShowCreateForm(false);
        setFormData({
          shipment_data: {
            cargo_value: 100000,
            distance: 5000,
            origin: '',
            destination: '',
          },
          schema_version: 'v1',
        });
        fetchAssessments();
      }
    } catch (err) {
      setError('Failed to create assessment');
    } finally {
      setCreating(false);
    }
  };

  // Create run for assessment
  const handleCreateRun = async (assessmentId: string) => {
    try {
      const response = await api.post<{ id: string; status: string; status_url: string }>(
        `/api/v3/risk/assessments/${assessmentId}/runs`,
        {}
      );
      if (response.data) {
        navigate(`/risk/runs/${response.data.id}`);
      }
    } catch (err) {
      setError('Failed to create run');
    }
  };

  useEffect(() => {
    fetchAssessments();
  }, []);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Risk Assessments</h1>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition-colors"
          >
            {showCreateForm ? 'Cancel' : '+ New Assessment'}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <GlassCard padding="md" className="border-red-500/50">
            <p className="text-red-400">{error}</p>
          </GlassCard>
        )}

        {/* Create Form */}
        {showCreateForm && (
          <GlassCard padding="lg">
            <h2 className="text-xl font-semibold text-white mb-4">Create New Assessment</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Cargo Value</label>
                  <input
                    type="number"
                    value={formData.shipment_data.cargo_value || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        shipment_data: {
                          ...formData.shipment_data,
                          cargo_value: parseFloat(e.target.value),
                        },
                      })
                    }
                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Distance (km)</label>
                  <input
                    type="number"
                    value={formData.shipment_data.distance || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        shipment_data: {
                          ...formData.shipment_data,
                          distance: parseFloat(e.target.value),
                        },
                      })
                    }
                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Origin</label>
                  <input
                    type="text"
                    value={formData.shipment_data.origin || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        shipment_data: {
                          ...formData.shipment_data,
                          origin: e.target.value,
                        },
                      })
                    }
                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="e.g., USNYC"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Destination</label>
                  <input
                    type="text"
                    value={formData.shipment_data.destination || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        shipment_data: {
                          ...formData.shipment_data,
                          destination: e.target.value,
                        },
                      })
                    }
                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="e.g., GBLON"
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 bg-gray-500/20 hover:bg-gray-500/30 text-gray-400 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition-colors disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Assessment'}
                </button>
              </div>
            </form>
          </GlassCard>
        )}

        {/* Assessments List */}
        <GlassCard padding="lg">
          <h2 className="text-xl font-semibold text-white mb-4">Existing Assessments</h2>
          {assessments.length === 0 ? (
            <p className="text-gray-400 text-center py-8">No assessments found</p>
          ) : (
            <div className="space-y-2">
              {assessments.map((assessment) => (
                <div
                  key={assessment.id}
                  className="p-4 bg-black/20 rounded-lg hover:bg-black/30 transition-colors cursor-pointer"
                  onClick={() => fetchAssessmentDetails(assessment.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-white font-semibold">Assessment {assessment.id.slice(0, 8)}...</h3>
                        <code className="text-xs text-gray-400 font-mono">
                          Hash: {assessment.input_hash.slice(0, 16)}...
                        </code>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-400">
                        <span>Schema: {assessment.schema_version}</span>
                        <span>Created: {new Date(assessment.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCreateRun(assessment.id);
                        }}
                        className="px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded text-sm transition-colors"
                      >
                        Create Run
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/risk/assessments/${assessment.id}`);
                        }}
                        className="px-3 py-1 bg-gray-500/20 hover:bg-gray-500/30 text-gray-400 rounded text-sm transition-colors"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Assessment Details Modal */}
        {selectedAssessment && (
          <GlassCard padding="lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Assessment Details</h2>
              <button
                onClick={() => setSelectedAssessment(null)}
                className="px-3 py-1 bg-gray-500/20 hover:bg-gray-500/30 text-gray-400 rounded text-sm transition-colors"
              >
                Close
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Input Hash</label>
                <code className="text-sm text-white font-mono bg-black/20 px-2 py-1 rounded block">
                  {selectedAssessment.input_hash}
                </code>
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Input Snapshot</label>
                <pre className="bg-black/20 p-4 rounded-lg overflow-auto text-sm text-gray-300 max-h-64">
                  {JSON.stringify(selectedAssessment.input_snapshot, null, 2)}
                </pre>
              </div>
              {selectedAssessment.runs.length > 0 && (
                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Runs ({selectedAssessment.runs.length})</label>
                  <div className="space-y-2">
                    {selectedAssessment.runs.map((run) => (
                      <div
                        key={run.id}
                        className="p-3 bg-black/20 rounded-lg flex items-center justify-between"
                      >
                        <div className="flex items-center space-x-3">
                          <RunStatusBadge status={run.status as RunStatus} />
                          <span className="text-sm text-gray-400">
                            {run.iterations.toLocaleString()} iterations
                          </span>
                          {run.result_hash && (
                            <code className="text-xs text-gray-500 font-mono">
                              {run.result_hash.slice(0, 16)}...
                            </code>
                          )}
                        </div>
                        <button
                          onClick={() => navigate(`/risk/runs/${run.id}`)}
                          className="px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded text-sm transition-colors"
                        >
                          View Run
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  );
};
