/**
 * API Client
 * Axios-based API client for RISKCAST V3
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v3',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    const tenantId = localStorage.getItem('tenant_id');
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    if (tenantId && config.headers) {
      config.headers['X-Tenant-Id'] = tenantId;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear auth and redirect to login
      localStorage.removeItem('auth_token');
      localStorage.removeItem('tenant_id');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Risk API
export const riskApi = {
  listAssessments: (params?: { limit?: number; offset?: number }) => {
    const queryParams = params ? new URLSearchParams({
      ...(params.limit && { limit: params.limit.toString() }),
      ...(params.offset && { offset: params.offset.toString() }),
    }).toString() : '';
    return apiClient.get(`/risk/assessments${queryParams ? `?${queryParams}` : ''}`);
  },
  getAssessment: (id: string) => apiClient.get(`/risk/assessments/${id}`),
  createAssessment: (data: any) => apiClient.post('/risk/assessments', data),
  createRun: (assessmentId: string, data: any) => 
    apiClient.post(`/risk/assessments/${assessmentId}/runs`, data),
  getRun: (runId: string) => apiClient.get(`/risk/runs/${runId}`)
};

// Policy API
export const policyApi = {
  listPolicies: (params?: { search?: string; status?: string }) => {
    const queryParams = params ? new URLSearchParams({
      ...(params.search && { search: params.search }),
      ...(params.status && { status: params.status }),
    }).toString() : '';
    return apiClient.get(`/policies${queryParams ? `?${queryParams}` : ''}`);
  },
  getPolicy: (id: string) => apiClient.get(`/policies/${id}`),
  verifyPolicy: (id: string) => apiClient.get(`/policies/${id}/verify`),
};

// Underwriting API
export const underwritingApi = {
  listSubmissions: () => apiClient.get('/underwriting/submissions'),
  getSubmission: (id: string) => apiClient.get(`/underwriting/submissions/${id}`),
  createSubmission: (data: any) => apiClient.post('/underwriting/submissions', data),
  createDecision: (id: string, data: any) => 
    apiClient.post(`/underwriting/submissions/${id}/decisions`, data),
  bindPolicy: (data: any) => apiClient.post('/policies', data),
  // Transition submission by creating a decision
  transitionSubmission: (submissionId: string, action: string, data?: any) => {
    // Map actions to decision types
    const decisionMap: Record<string, string> = {
      'submit': 'QUOTE', // Submit moves to UNDER_REVIEW, then decision creates quote
      'review': 'QUOTE', // Review leads to quote decision
      'quote': 'QUOTE',
      'decline': 'DECLINE',
      'request_info': 'REQUEST_INFO',
      'provide_info': 'QUOTE', // Providing info allows review to continue
    };
    
    const decisionType = decisionMap[action] || 'QUOTE';
    return apiClient.post(`/underwriting/submissions/${submissionId}/decisions`, {
      decision: decisionType,
      ...data,
    });
  },
};

// Claims API
export const claimsApi = {
  listClaims: (params?: { policy_id?: string; status?: string; assigned_to?: string; limit?: number; offset?: number }) => {
    const queryParams = params ? new URLSearchParams({
      ...(params.policy_id && { policy_id: params.policy_id }),
      ...(params.status && { status: params.status }),
      ...(params.assigned_to && { assigned_to: params.assigned_to }),
      ...(params.limit && { limit: params.limit.toString() }),
      ...(params.offset && { offset: params.offset.toString() }),
    }).toString() : '';
    return apiClient.get(`/claims${queryParams ? `?${queryParams}` : ''}`);
  },
  getClaim: (id: string) => apiClient.get(`/claims/${id}`),
  getClaimHistory: (id: string) => apiClient.get(`/claims/${id}/history`),
  fileClaim: (policyId: string, fnol: any) => apiClient.post(`/claims?policy_id=${policyId}`, { fnol }),
  assignAdjuster: (claimId: string, adjusterId: string) => apiClient.post(`/claims/${claimId}/assign?adjuster_id=${adjusterId}`),
  beginInvestigation: (claimId: string) => apiClient.post(`/claims/${claimId}/investigate`),
  requestEvidence: (claimId: string, evidenceRequest: string) => apiClient.post(`/claims/${claimId}/evidence/request`, evidenceRequest),
  submitEvidence: (claimId: string, evidenceBundleId: string) => apiClient.post(`/claims/${claimId}/evidence?evidence_bundle_id=${evidenceBundleId}`),
  adjudicate: (claimId: string, adjudication: any) => apiClient.post(`/claims/${claimId}/adjudicate`, adjudication),
  authorize: (claimId: string, notes?: string) => apiClient.post(`/claims/${claimId}/authorize`, null, { params: notes ? { notes } : {} }),
  getClaimsStats: () => apiClient.get('/claims/stats').catch(() => ({ data: { open_claims: 0, pending_review: 0, under_investigation: 0, total_paid_mtd: 0, total_reserved: 0 } })),
};

// Evidence API
export const evidenceApi = {
  getBundle: (id: string) => apiClient.get(`/evidence-bundles/${id}`)
};

// Audit API
export const auditApi = {
  listEvents: (filters?: {
    entity_type?: string;
    entity_id?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }) => {
    const queryParams = filters ? new URLSearchParams({
      ...(filters.entity_type && { entity_type: filters.entity_type }),
      ...(filters.entity_id && { entity_id: filters.entity_id }),
      ...(filters.from_date && { from_date: filters.from_date }),
      ...(filters.to_date && { to_date: filters.to_date }),
      ...(filters.limit && { limit: filters.limit.toString() }),
      ...(filters.offset && { offset: filters.offset.toString() }),
    }).toString() : '';
    return apiClient.get(`/audit/events${queryParams ? `?${queryParams}` : ''}`);
  },
  verifyChain: (fromSequence?: number) => {
    const queryParams = fromSequence !== undefined
      ? `?from_sequence=${fromSequence}`
      : '';
    return apiClient.get(`/audit/verify${queryParams}`);
  },
  exportChain: (params?: {
    from_sequence?: number;
    to_sequence?: number;
    format?: 'json' | 'csv';
  }) => {
    const queryParams = params ? new URLSearchParams({
      ...(params.from_sequence !== undefined && { from_sequence: params.from_sequence.toString() }),
      ...(params.to_sequence !== undefined && { to_sequence: params.to_sequence.toString() }),
      ...(params.format && { format: params.format }),
    }).toString() : '';
    return apiClient.get(`/audit/export${queryParams ? `?${queryParams}` : ''}`);
  },
};

// Model Versions API
export const modelVersionsApi = {
  listVersions: (params?: { status?: string; include_deprecated?: boolean; skip?: number; limit?: number }) => {
    const queryParams = params ? new URLSearchParams({
      ...(params.status && { status: params.status }),
      ...(params.include_deprecated !== undefined && { include_deprecated: String(params.include_deprecated) }),
      ...(params.skip !== undefined && { skip: params.skip.toString() }),
      ...(params.limit !== undefined && { limit: params.limit.toString() }),
    }).toString() : '';
    return apiClient.get(`/models/versions${queryParams ? `?${queryParams}` : ''}`);
  },
  getActive: () => apiClient.get('/models/active'),
  getVersion: (id: string) => apiClient.get(`/models/versions/${id}`),
  getParameters: (id: string) => apiClient.get(`/models/versions/${id}/parameters`),
  getCalibration: (id: string) => apiClient.get(`/models/versions/${id}/calibration`),
  getUsageStats: (id: string, days?: number) =>
    apiClient.get(`/models/versions/${id}/usage-stats${days != null ? `?days=${days}` : ''}`),
  compare: (id1: string, id2: string) => apiClient.get(`/models/compare/${id1}/${id2}`),
  setActive: (modelVersionId: string) =>
    apiClient.post('/models/set-active', { model_version_id: modelVersionId }),
  publish: (id: string, approvalNotes?: string) =>
    apiClient.post(`/models/versions/${id}/publish${approvalNotes != null ? `?approval_notes=${encodeURIComponent(approvalNotes)}` : ''}`),
  deprecate: (id: string, body: { reason: string; replacement_version_id?: string }) =>
    apiClient.post(`/models/versions/${id}/deprecate`, body),
};

// Analytics API
export const analyticsApi = {
  getPortfolioROI: (params: { period?: string; start_date?: string; end_date?: string }) => {
    // Calculate dates based on period
    const endDate = new Date();
    let startDate = new Date();
    if (params.period) {
      const months = parseInt(params.period.replace('m', ''));
      startDate.setMonth(startDate.getMonth() - months);
    }
    const queryParams = new URLSearchParams({
      start_date: params.start_date || startDate.toISOString().split('T')[0] || '',
      end_date: params.end_date || endDate.toISOString().split('T')[0] || '',
    } as Record<string, string>).toString();
    return apiClient.get(`/analytics/roi/portfolio?${queryParams}`);
  },
  getLossRatios: (params: { period?: string; start_date?: string; end_date?: string }) => {
    const endDate = new Date();
    let startDate = new Date();
    if (params.period) {
      const months = parseInt(params.period.replace('m', ''));
      startDate.setMonth(startDate.getMonth() - months);
    }
    const queryParams = new URLSearchParams({
      start_date: params.start_date || startDate.toISOString().split('T')[0] || '',
      end_date: params.end_date || endDate.toISOString().split('T')[0] || '',
      dimensions: 'corridor,cargo_type',
    } as Record<string, string>).toString();
    return apiClient.get(`/analytics/loss-ratio/report?${queryParams}`);
  },
  getModelPerformance: (modelVersionId?: string) => {
    // For now, get overall model performance - can be enhanced later
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 12);
    const queryParams = new URLSearchParams({
      start_date: startDate.toISOString().split('T')[0] || '',
      end_date: endDate.toISOString().split('T')[0] || '',
    } as Record<string, string>).toString();
    if (modelVersionId) {
      return apiClient.get(`/analytics/model-performance/${modelVersionId}?${queryParams}`);
    }
    // Return a mock/placeholder for overall performance
    return Promise.resolve({ data: null });
  },
  getLossTrend: (params: { months?: number }) => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - (params.months || 12));
    const queryParams = new URLSearchParams({
      start_date: startDate.toISOString().split('T')[0] || '',
      end_date: endDate.toISOString().split('T')[0] || '',
    } as Record<string, string>).toString();
    return apiClient.get(`/analytics/roi/portfolio/trend?${queryParams}`);
  },
};

export default apiClient;
