/**
 * Shared TypeScript types for the AI Voice Agent application.
 * These types mirror the backend Pydantic schemas for type safety.
 */

// =============================================================================
// Enums
// =============================================================================

export type ScenarioType = 'dispatch_checkin' | 'emergency';

export type CallStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

export type CallType = 'phone' | 'web';

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
  driver_name: string;
  phone_number: string | null;
  load_number: string;
  call_type: CallType;
  
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
  driver_name: string;
  phone_number?: string | null;
  load_number: string;
  call_type?: CallType;
}

// =============================================================================
// Call Trigger (for "Start Test Call" button)
// =============================================================================

export interface CallTriggerRequest {
  driver_name: string;
  phone_number?: string | null;
  load_number: string;
  scenario_type: ScenarioType;
  call_type: CallType;
}

export interface CallTriggerResponse {
  call_id: string;
  retell_call_id: string;
  status: CallStatus;
  call_type: CallType;
  access_token?: string | null; // For web calls only
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

export type DriverStatusType = 'Driving' | 'Delayed' | 'Arrived' | 'Unloading';
export type EmergencyType = 'Accident' | 'Breakdown' | 'Medical' | 'Other';

export interface StructuredSummary {
  id: string;
  call_id: string;
  
  // Common field
  call_outcome: CallOutcome | null;
  
  // Dispatch Check-in fields (Scenario 1)
  driver_status: DriverStatusType | null;
  current_location: string | null;
  eta: string | null;
  delay_reason: string | null;
  unloading_status: string | null;
  pod_reminder_acknowledged: boolean | null;
  
  // Emergency fields (Scenario 2)
  emergency_type: EmergencyType | null;
  safety_status: string | null;
  injury_status: string | null;
  emergency_location: string | null;
  load_secure: boolean | null;
  escalation_status: string | null;
  
  // Raw extraction from LLM
  raw_extraction: Record<string, unknown> | null;
  
  created_at: string;
}

// =============================================================================
// Call with Details (for results display)
// =============================================================================

export interface CallWithDetails extends Call {
  transcript: Transcript | null;
  structured_summary: StructuredSummary | null;
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

// =============================================================================
// Retell AI Config (from Retell API)
// =============================================================================

export interface RetellConfig {
  agent_id: string;
  agent_name: string | null;
  llm_id?: string;
  general_prompt: string | null;
  begin_message: string | null;
  enable_backchannel: boolean;
  interruption_sensitivity: number;
  boosted_keywords: string[];
}

