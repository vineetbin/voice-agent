-- =============================================================================
-- AI Voice Agent Database Schema
-- =============================================================================
-- Run this in your Supabase SQL Editor to set up the database
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Agent Configurations
-- -----------------------------------------------------------------------------
-- Stores prompt templates and Retell AI settings for different scenarios

CREATE TABLE IF NOT EXISTS agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    scenario_type VARCHAR(50) NOT NULL, -- 'dispatch_checkin' | 'emergency'
    
    -- Agent prompt configuration
    system_prompt TEXT NOT NULL,
    initial_message TEXT,
    
    -- Retell AI advanced settings (Task A requirements)
    enable_backchanneling BOOLEAN DEFAULT true,
    enable_filler_words BOOLEAN DEFAULT true,
    interruption_sensitivity DECIMAL(3,2) DEFAULT 0.5, -- 0.0 to 1.0
    
    -- Metadata
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Calls
-- -----------------------------------------------------------------------------
-- Records of all calls made through the system

CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Retell identifiers
    retell_call_id VARCHAR(255),
    
    -- Call context (from UI input)
    driver_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    load_number VARCHAR(100) NOT NULL,
    
    -- Which config was used
    agent_config_id UUID REFERENCES agent_configs(id),
    
    -- Call status lifecycle: pending -> in_progress -> completed | failed
    status VARCHAR(50) DEFAULT 'pending',
    call_type VARCHAR(50) DEFAULT 'phone', -- 'phone' | 'web'
    
    -- Timing
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Transcripts
-- -----------------------------------------------------------------------------
-- Raw conversation data from calls

CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    
    -- Full transcript
    raw_transcript TEXT,
    
    -- Individual utterances (JSONB array)
    utterances JSONB DEFAULT '[]',
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Structured Summaries
-- -----------------------------------------------------------------------------
-- Post-processed extraction from transcripts (key-value pairs for UI)

CREATE TABLE IF NOT EXISTS structured_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    
    -- Common fields
    call_outcome VARCHAR(100), -- 'In-Transit Update' | 'Arrival Confirmation' | 'Emergency Escalation'
    
    -- Dispatch Check-in fields (Scenario 1)
    driver_status VARCHAR(50), -- 'Driving' | 'Delayed' | 'Arrived' | 'Unloading'
    current_location TEXT,
    eta TEXT,
    delay_reason VARCHAR(100), -- 'Heavy Traffic' | 'Weather' | 'None'
    unloading_status VARCHAR(100), -- 'In Door 42' | 'Waiting for Lumper' | 'Detention' | 'N/A'
    pod_reminder_acknowledged BOOLEAN,
    
    -- Emergency fields (Scenario 2)
    emergency_type VARCHAR(50), -- 'Accident' | 'Breakdown' | 'Medical' | 'Other'
    safety_status TEXT,
    injury_status TEXT,
    emergency_location TEXT,
    load_secure BOOLEAN,
    escalation_status VARCHAR(100), -- 'Connected to Human Dispatcher'
    
    -- Raw extraction data (full JSON from LLM)
    raw_extraction JSONB,
    
    -- Extraction completeness flag
    partial BOOLEAN DEFAULT false, -- True when extraction is incomplete
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Indexes for Performance
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_configs_scenario ON agent_configs(scenario_type);
CREATE INDEX IF NOT EXISTS idx_agent_configs_active ON agent_configs(is_active);

-- -----------------------------------------------------------------------------
-- Updated At Trigger
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agent_configs_updated_at
    BEFORE UPDATE ON agent_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calls_updated_at
    BEFORE UPDATE ON calls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- Row Level Security (RLS) - Disabled for simplicity
-- -----------------------------------------------------------------------------
-- For this demo, RLS is disabled. In production, you would enable RLS
-- and create appropriate policies.

ALTER TABLE agent_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE structured_summaries ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (demo mode)
CREATE POLICY "Allow all for service role" ON agent_configs FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON calls FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON transcripts FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON structured_summaries FOR ALL USING (true);

