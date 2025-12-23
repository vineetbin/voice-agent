/**
 * API client for communicating with the FastAPI backend.
 * Uses axios for HTTP requests with centralized error handling.
 */

import axios, { AxiosError } from 'axios';
import type { 
  AgentConfig, 
  AgentConfigCreate, 
  AgentConfigUpdate,
  Call,
  CallCreate,
  CallWithDetails,
  CallTriggerRequest,
  CallTriggerResponse,
  CallStatus,
  ScenarioType,
  RetellConfig,
  ApiError,
} from '@/types';

// =============================================================================
// API Client Configuration
// =============================================================================

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handler
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

// =============================================================================
// Agent Configurations API
// =============================================================================

export const configsApi = {
  /**
   * Get all agent configurations
   */
  getAll: async (): Promise<AgentConfig[]> => {
    const response = await api.get<AgentConfig[]>('/configs');
    return response.data;
  },

  /**
   * Get a single agent configuration by ID
   */
  getById: async (id: string): Promise<AgentConfig> => {
    const response = await api.get<AgentConfig>(`/configs/${id}`);
    return response.data;
  },

  /**
   * Get the active configuration for a scenario type
   */
  getActive: async (scenarioType: string): Promise<AgentConfig | null> => {
    try {
      const response = await api.get<AgentConfig>(`/configs/active/${scenarioType}`);
      return response.data;
    } catch (error) {
      // Return null if no active config found
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  },

  /**
   * Create a new agent configuration
   */
  create: async (data: AgentConfigCreate): Promise<AgentConfig> => {
    const response = await api.post<AgentConfig>('/configs', data);
    return response.data;
  },

  /**
   * Update an existing agent configuration
   */
  update: async (id: string, data: AgentConfigUpdate): Promise<AgentConfig> => {
    const response = await api.patch<AgentConfig>(`/configs/${id}`, data);
    return response.data;
  },

  /**
   * Delete an agent configuration
   */
  delete: async (id: string): Promise<void> => {
    await api.delete(`/configs/${id}`);
  },

  /**
   * Activate a configuration (deactivates others of same scenario type)
   */
  activate: async (id: string): Promise<AgentConfig> => {
    const response = await api.patch<AgentConfig>(`/configs/${id}`, { is_active: true });
    return response.data;
  },

  /**
   * Get current configuration from Retell AI
   */
  getRetellConfig: async (): Promise<RetellConfig> => {
    const response = await api.get<RetellConfig>('/configs/retell/current');
    return response.data;
  },

  /**
   * Sync configuration FROM Retell AI to local database
   */
  syncFromRetell: async (scenarioType: ScenarioType): Promise<AgentConfig> => {
    const response = await api.post<AgentConfig>(`/configs/retell/sync?scenario_type=${scenarioType}`);
    return response.data;
  },
};

// =============================================================================
// Calls API
// =============================================================================

export const callsApi = {
  /**
   * Get all calls with optional status filter
   */
  getAll: async (status?: CallStatus): Promise<Call[]> => {
    const params = status ? { status } : {};
    const response = await api.get<Call[]>('/calls', { params });
    return response.data;
  },

  /**
   * Get a single call by ID with full details
   */
  getById: async (id: string): Promise<CallWithDetails> => {
    const response = await api.get<CallWithDetails>(`/calls/${id}`);
    return response.data;
  },

  /**
   * Get recent completed calls with details
   */
  getRecent: async (limit = 10): Promise<CallWithDetails[]> => {
    const response = await api.get<CallWithDetails[]>('/calls/recent/completed', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Trigger a new call (main endpoint for "Start Test Call")
   */
  trigger: async (data: CallTriggerRequest): Promise<CallTriggerResponse> => {
    const response = await api.post<CallTriggerResponse>('/calls/trigger', data);
    return response.data;
  },

  /**
   * Create a new call record (internal use)
   */
  create: async (data: CallCreate): Promise<Call> => {
    const response = await api.post<Call>('/calls', data);
    return response.data;
  },

  /**
   * Update call status
   */
  updateStatus: async (id: string, status: string): Promise<Call> => {
    const response = await api.patch<Call>(`/calls/${id}`, { status });
    return response.data;
  },
};

// =============================================================================
// Health Check
// =============================================================================

export const healthApi = {
  check: async (): Promise<{ status: string; app: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;

