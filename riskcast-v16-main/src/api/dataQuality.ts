/**
 * Data Quality API Client
 */

import { api } from '@/services/apiClient';

export interface DataSourceStatus {
  source_name: string;
  source_type: string;
  status: 'HEALTHY' | 'DEGRADED' | 'OFFLINE';
  last_updated: string | null;
  data_quality: string;
  confidence: number;
  next_refresh: string | null;
  error_message: string | null;
}

export interface DataQualityOverview {
  overall_status: string;
  overall_confidence: number;
  sources: DataSourceStatus[];
  warnings: string[];
  last_check: string;
}

export interface DataQualityCheck {
  origin_port: string;
  destination_port: string;
  cargo_type: string;
  cargo_value_usd: number;
  container_count?: number;
  carrier_code?: string | null;
  purpose?: string;
}

export interface DataQualityCheckResult {
  can_proceed: boolean;
  overall_quality: string;
  overall_confidence: number;
  sources: Array<{
    name: string;
    type: string;
    quality: string;
    is_fallback: boolean;
    confidence: number;
  }>;
  missing_sources: string[];
  fallback_sources: string[];
  warnings: string[];
  block_reason: string | null;
  recommendations: string[];
}

export interface RefreshJobStatus {
  job_id: string;
  source_name: string;
  priority: string;
  interval_minutes: number;
  last_run: string | null;
  last_status: string;
  consecutive_failures: number;
  success_rate: number;
  is_enabled: boolean;
}

class DataQualityApi {
  private baseUrl = '/api/v3/data-quality';

  async getOverview(): Promise<DataQualityOverview> {
    const response = await api.get<DataQualityOverview>(this.baseUrl + '/overview');
    if (response.error || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch data quality overview');
    }
    return response.data;
  }

  async checkQuality(request: DataQualityCheck): Promise<DataQualityCheckResult> {
    const response = await api.post<DataQualityCheckResult>(
      this.baseUrl + '/check',
      request
    );
    if (response.error || !response.data) {
      throw new Error(response.error?.message || 'Failed to check data quality');
    }
    return response.data;
  }

  async getSourceHistory(
    sourceType: string,
    days: number = 7
  ): Promise<{
    source_type: string;
    period_days: number;
    total_fetches: number;
    successful_fetches: number;
    success_rate: number;
    history: Array<{
      timestamp: string;
      quality: string;
      duration_ms?: number;
      error?: string | null;
      source?: string;
    }>;
  }> {
    const response = await api.get(
      `${this.baseUrl}/sources/${sourceType}/history?days=${days}`
    );
    if (response.error || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch source history');
    }
    return response.data as any;
  }

  async getRefreshJobs(): Promise<RefreshJobStatus[]> {
    const response = await api.get<RefreshJobStatus[]>(this.baseUrl + '/refresh-jobs');
    if (response.error || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch refresh jobs');
    }
    return response.data;
  }

  async triggerRefresh(sourceType: string): Promise<{
    status: string;
    source_type: string;
    job_id: string;
    triggered_at: string;
    message: string;
  }> {
    const response = await api.post(
      `${this.baseUrl}/refresh/${sourceType}`
    );
    if (response.error || !response.data) {
      throw new Error(response.error?.message || 'Failed to trigger refresh');
    }
    return response.data as any;
  }
}

export const dataQualityApi = new DataQualityApi();
