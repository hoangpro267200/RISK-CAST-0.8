/**
 * useApi Hook
 * React Query wrapper for API calls
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { riskApi } from '../api/client';

// Re-export API clients
export { riskApi, underwritingApi, claimsApi, evidenceApi, auditApi, modelVersionsApi } from '../api/client';

/**
 * Generic query hook with error handling
 */
export function useApiQuery<TData = any, TError = AxiosError>(
  queryKey: string[],
  queryFn: () => Promise<TData>,
  options?: Omit<UseQueryOptions<TData, TError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<TData, TError>({
    queryKey,
    queryFn,
    retry: 1,
    ...options
  });
}

/**
 * Generic mutation hook with error handling
 */
export function useApiMutation<TData = any, TVariables = any, TError = AxiosError>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: Omit<UseMutationOptions<TData, TError, TVariables>, 'mutationFn'>
) {
  const queryClient = useQueryClient();
  
  return useMutation<TData, TError, TVariables>({
    mutationFn,
    onSuccess: (data, variables, context) => {
      // Invalidate relevant queries
      if (options?.onSuccess) {
        // @ts-ignore - onSuccess signature may vary
        options.onSuccess(data, variables, context);
      }
    },
    ...options
  });
}

/**
 * Hook for risk assessment operations
 */
export function useRiskAssessment(assessmentId?: string) {
  return useApiQuery(
    ['risk-assessment', assessmentId!],
    () => riskApi.getRun(assessmentId!).then(res => res.data),
    {
      enabled: !!assessmentId
    }
  );
}

/**
 * Hook for risk run operations
 */
export function useRiskRun(runId?: string) {
  return useApiQuery(
    ['risk-run', runId!],
    () => riskApi.getRun(runId!).then(res => res.data),
    {
      enabled: !!runId
    }
  );
}
