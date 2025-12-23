/**
 * React Query hooks for agent configuration management.
 * Provides data fetching, caching, and mutation capabilities.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { configsApi } from '@/services/api';
import type { AgentConfigCreate, AgentConfigUpdate, ScenarioType } from '@/types';

// Query keys for cache management
export const configKeys = {
  all: ['configs'] as const,
  lists: () => [...configKeys.all, 'list'] as const,
  list: () => [...configKeys.lists()] as const,
  details: () => [...configKeys.all, 'detail'] as const,
  detail: (id: string) => [...configKeys.details(), id] as const,
  active: (scenarioType: ScenarioType) => [...configKeys.all, 'active', scenarioType] as const,
};

/**
 * Hook to fetch all configurations
 */
export function useConfigs() {
  return useQuery({
    queryKey: configKeys.list(),
    queryFn: configsApi.getAll,
  });
}

/**
 * Hook to fetch a single configuration by ID
 */
export function useConfig(id: string | undefined) {
  return useQuery({
    queryKey: configKeys.detail(id!),
    queryFn: () => configsApi.getById(id!),
    enabled: !!id,
  });
}

/**
 * Hook to fetch the active configuration for a scenario type
 */
export function useActiveConfig(scenarioType: ScenarioType | undefined) {
  return useQuery({
    queryKey: configKeys.active(scenarioType!),
    queryFn: () => configsApi.getActive(scenarioType!),
    enabled: !!scenarioType,
  });
}

/**
 * Hook to create a new configuration
 */
export function useCreateConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AgentConfigCreate) => configsApi.create(data),
    onSuccess: () => {
      // Invalidate all config queries to refetch
      queryClient.invalidateQueries({ queryKey: configKeys.all });
    },
  });
}

/**
 * Hook to update an existing configuration
 */
export function useUpdateConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AgentConfigUpdate }) =>
      configsApi.update(id, data),
    onSuccess: (updatedConfig) => {
      // Update cache with new data
      queryClient.setQueryData(configKeys.detail(updatedConfig.id), updatedConfig);
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: configKeys.lists() });
      // Invalidate active configs
      queryClient.invalidateQueries({ 
        queryKey: configKeys.active(updatedConfig.scenario_type) 
      });
    },
  });
}

/**
 * Hook to delete a configuration
 */
export function useDeleteConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => configsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: configKeys.all });
    },
  });
}

/**
 * Hook to activate a configuration
 */
export function useActivateConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => configsApi.activate(id),
    onSuccess: () => {
      // Invalidate all queries since activating one deactivates others
      queryClient.invalidateQueries({ queryKey: configKeys.all });
    },
  });
}

// =============================================================================
// Retell AI Sync Hooks
// =============================================================================

export const retellKeys = {
  config: ['retell', 'config'] as const,
};

/**
 * Hook to fetch current configuration from Retell AI
 */
export function useRetellConfig() {
  return useQuery({
    queryKey: retellKeys.config,
    queryFn: configsApi.getRetellConfig,
    staleTime: 30000, // Cache for 30 seconds
    retry: false, // Don't retry on failure (API key issues, etc.)
  });
}

/**
 * Hook to sync configuration FROM Retell AI to local database
 */
export function useSyncFromRetell() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (scenarioType: ScenarioType) => configsApi.syncFromRetell(scenarioType),
    onSuccess: () => {
      // Invalidate all config queries to refetch the synced config
      queryClient.invalidateQueries({ queryKey: configKeys.all });
      queryClient.invalidateQueries({ queryKey: retellKeys.config });
    },
  });
}

