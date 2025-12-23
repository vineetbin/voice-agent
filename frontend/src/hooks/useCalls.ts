/**
 * React Query hooks for call management.
 * Provides data fetching, triggering calls, and real-time updates.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { callsApi } from '@/services/api';
import type { CallTriggerRequest, CallStatus } from '@/types';

// Query keys for cache management
export const callKeys = {
  all: ['calls'] as const,
  lists: () => [...callKeys.all, 'list'] as const,
  list: (filters?: { status?: CallStatus }) => [...callKeys.lists(), filters] as const,
  details: () => [...callKeys.all, 'detail'] as const,
  detail: (id: string) => [...callKeys.details(), id] as const,
  recent: () => [...callKeys.all, 'recent'] as const,
};

/**
 * Hook to fetch all calls with optional filtering
 */
export function useCalls(status?: CallStatus) {
  return useQuery({
    queryKey: callKeys.list({ status }),
    queryFn: () => callsApi.getAll(status),
  });
}

/**
 * Hook to fetch a single call by ID with full details
 */
export function useCall(id: string | undefined) {
  return useQuery({
    queryKey: callKeys.detail(id!),
    queryFn: () => callsApi.getById(id!),
    enabled: !!id,
    // Refetch every 3 seconds while call is in progress
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && data.status === 'in_progress') {
        return 3000;
      }
      return false;
    },
  });
}

/**
 * Hook to fetch recent completed calls
 */
export function useRecentCalls(limit = 10) {
  return useQuery({
    queryKey: callKeys.recent(),
    queryFn: () => callsApi.getRecent(limit),
  });
}

/**
 * Hook to trigger a new call
 */
export function useTriggerCall() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CallTriggerRequest) => callsApi.trigger(request),
    onSuccess: () => {
      // Invalidate call lists to refetch
      queryClient.invalidateQueries({ queryKey: callKeys.lists() });
    },
  });
}

