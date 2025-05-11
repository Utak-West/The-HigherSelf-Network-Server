-- Agent & System Support Databases Migration
-- This script creates the tables for the 7 agent and system support databases

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types if not already created
CREATE TYPE agent_status AS ENUM ('Deployed', 'Development', 'Inactive', 'Deprecated');
CREATE TYPE integration_status AS ENUM ('Active', 'Deprecated', 'Planned', 'Under Test');
CREATE TYPE runtime_environment AS ENUM ('Docker (HigherSelf Network Server)', 'Serverless');
CREATE TYPE notification_channel AS ENUM ('Email', 'SMS', 'Slack', 'Push Notification');

-- 10. Agent Communication Patterns
CREATE TABLE IF NOT EXISTS agent_communication_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_name TEXT NOT NULL,
    description TEXT NOT NULL,
    source_agent TEXT NOT NULL,
    target_agent TEXT NOT NULL,
    message_format TEXT NOT NULL,
    communication_protocol TEXT DEFAULT 'HTTP',
    sample_payload JSONB NOT NULL,
    active_workflows_using JSONB DEFAULT '[]'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Agent Registry
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    version TEXT DEFAULT '1.0.0',
    status agent_status NOT NULL,
    capabilities JSONB DEFAULT '[]'::JSONB,
    primary_apis_utilized JSONB DEFAULT '[]'::JSONB,
    business_entity_association JSONB DEFAULT '[]'::JSONB,
    runtime_environment runtime_environment NOT NULL,
    source_code_location TEXT,
    last_execution TIMESTAMPTZ,
    execution_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 2) DEFAULT 0,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. API Integrations Catalog
CREATE TABLE IF NOT EXISTS api_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    api_platform TEXT NOT NULL,
    status integration_status NOT NULL,
    api_version TEXT,
    auth_method TEXT,
    api_key_reference TEXT,
    base_url TEXT,
    documentation_url TEXT,
    business_entities JSONB DEFAULT '[]'::JSONB,
    agents_using JSONB DEFAULT '[]'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. Data Transformations Registry
CREATE TABLE IF NOT EXISTS data_transformations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transformation_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    source_format TEXT NOT NULL,
    target_format TEXT NOT NULL,
    transformation_logic TEXT NOT NULL,
    sample_input JSONB,
    sample_output JSONB,
    business_entities JSONB DEFAULT '[]'::JSONB,
    agents_using JSONB DEFAULT '[]'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. Notifications Templates
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    channel notification_channel NOT NULL,
    content_template TEXT NOT NULL,
    subject_template TEXT,
    supported_placeholders JSONB DEFAULT '[]'::JSONB,
    business_entities JSONB DEFAULT '[]'::JSONB,
    creator TEXT NOT NULL,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 15. Use Cases Library
CREATE TABLE IF NOT EXISTS use_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    use_case_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    business_value TEXT NOT NULL,
    implementation_status TEXT DEFAULT 'Planned',
    business_entities JSONB DEFAULT '[]'::JSONB,
    related_workflows JSONB DEFAULT '[]'::JSONB,
    required_integrations JSONB DEFAULT '[]'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 16. Workflows Library
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status workflow_status NOT NULL,
    business_entities JSONB DEFAULT '[]'::JSONB,
    trigger_type TEXT NOT NULL,
    trigger_conditions JSONB DEFAULT '{}'::JSONB,
    workflow_steps JSONB DEFAULT '[]'::JSONB,
    required_integrations JSONB DEFAULT '[]'::JSONB,
    active_instances_count INTEGER DEFAULT 0,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_agent_comm_source ON agent_communication_patterns(source_agent);
CREATE INDEX idx_agent_comm_target ON agent_communication_patterns(target_agent);
CREATE INDEX idx_agent_status ON agents(status);
CREATE INDEX idx_api_platform ON api_integrations(api_platform);
CREATE INDEX idx_api_status ON api_integrations(status);
CREATE INDEX idx_notification_channel ON notification_templates(channel);
CREATE INDEX idx_workflow_status ON workflows(status);
