/**
 * Shared TypeScript types for the AI Voice Agent application.
 * These types mirror the backend Pydantic schemas for type safety.
 */

// =============================================================================
// Enums
// =============================================================================

export type ScenarioType = 'dispatch_checkin' | 'emergency';

export type CallStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

export type CallOutcome = 
  | 'In-Transit Update' 
  | 'Arrival Confirmation' 
  | 'Emergency Escalation'
  | null;

// =============================================================================
// Agent Configuration
// =============================================================================

export interface AgentConfig {
  id: string;
  name: string;
  description: string | null;
  scenario_type: ScenarioType;
  system_prompt: string;
  initial_message: string | null;
  
  // Retell AI Advanced Settings (Task A requirements)
  enable_backchanneling: boolean;
  enable_filler_words: boolean;
  interruption_sensitivity: number; // 0.0 to 1.0
  
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentConfigCreate {
  name: string;
  description?: string | null;
  scenario_type: ScenarioType;
  system_prompt: string;
  initial_message?: string | null;
  enable_backchanneling?: boolean;
  enable_filler_words?: boolean;
  interruption_sensitivity?: number;
  is_active?: boolean;
}

export interface AgentConfigUpdate {
  name?: string;
  description?: string | null;
  scenario_type?: ScenarioType;
  system_prompt?: string;
  initial_message?: string | null;
  enable_backchanneling?: boolean;
  enable_filler_words?: boolean;
  interruption_sensitivity?: number;
  is_active?: boolean;
}

// =============================================================================
// Calls
// =============================================================================

export interface Call {
  id: string;
  agent_config_id: string | null;
  retell_call_id: string | null;
  
  // Call context
  driver_name: string | null;
  driver_phone: string | null;
  load_number: string | null;
  
  // Status tracking
  status: CallStatus;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  
  created_at: string;
  updated_at: string;
}

export interface CallCreate {
  agent_config_id?: string | null;
  driver_name?: string | null;
  driver_phone?: string | null;
  load_number?: string | null;
}

// =============================================================================
// Transcripts
// =============================================================================

export interface TranscriptUtterance {
  role: 'agent' | 'user';
  content: string;
}

export interface Transcript {
  id: string;
  call_id: string;
  raw_transcript: string | null;
  utterances: TranscriptUtterance[];
  created_at: string;
}

// =============================================================================
// Structured Summaries
// =============================================================================

// Dispatch Check-in Summary
export interface DispatchSummary {
  call_outcome: 'In-Transit Update' | 'Arrival Confirmation';
  driver_status: 'Driving' | 'Delayed' | 'Arrived' | 'Unloading';
  current_location: string;
  eta: string;
  delay_reason: 'Heavy Traffic' | 'Weather' | 'None' | string;
  unloading_status: 'In Door 42' | 'Waiting for Lumper' | 'Detention' | 'N/A' | string;
  pod_reminder_acknowledged: boolean;
}

// Emergency Escalation Summary
export interface EmergencySummary {
  call_outcome: 'Emergency Escalation';
  emergency_type: 'Accident' | 'Breakdown' | 'Medical' | 'Other';
  safety_status: string;
  injury_status: string;
  emergency_location: string;
  load_secure: boolean;
  escalation_status: 'Connected to Human Dispatcher';
}

export type StructuredSummaryData = DispatchSummary | EmergencySummary;

export interface StructuredSummary {
  id: string;
  call_id: string;
  summary_data: StructuredSummaryData;
  extraction_method: 'openai' | 'fallback';
  confidence_score: number | null;
  created_at: string;
}

// =============================================================================
// Call with Details (for results display)
// =============================================================================

export interface CallWithDetails extends Call {
  transcript: Transcript | null;
  summary: StructuredSummary | null;
  config: AgentConfig | null;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface ApiError {
  detail: string;
}

// =============================================================================
// Preset Templates
// =============================================================================

export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  scenario_type: ScenarioType;
  system_prompt: string;
  initial_message: string;
}

