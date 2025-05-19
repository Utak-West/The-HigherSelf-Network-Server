-- Core Operational Databases Migration
-- This script creates the tables for the 9 core operational databases

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE entity_type AS ENUM ('CONSULTING_FIRM', 'ART_GALLERY', 'WELLNESS_CENTER');
CREATE TYPE task_status AS ENUM ('To Do', 'In Progress', 'On Hold', 'Done', 'Cancelled');
CREATE TYPE workflow_status AS ENUM ('Draft', 'Implemented', 'Active');
CREATE TYPE instance_status AS ENUM ('Active', 'Completed', 'Error', 'On Hold');

-- 1. Business Entities Registry
CREATE TABLE IF NOT EXISTS business_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    entity_type entity_type NOT NULL,
    api_keys_reference TEXT NOT NULL,
    primary_workflows JSONB DEFAULT '[]'::JSONB,
    active_agents JSONB DEFAULT '[]'::JSONB,
    integration_status TEXT DEFAULT 'Active',
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Contacts & Profiles
CREATE TABLE IF NOT EXISTS contacts_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    contact_type TEXT,
    business_entity_id UUID REFERENCES business_entities(id),
    tags JSONB DEFAULT '[]'::JSONB,
    lead_source TEXT,
    lead_status TEXT,
    last_interaction_date TIMESTAMPTZ,
    custom_fields JSONB DEFAULT '{}'::JSONB,
    source_record_id TEXT,
    hubspot_contact_id TEXT,
    airtable_record_id TEXT,
    key_data_payload JSONB,
    history_log JSONB DEFAULT '[]'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Community Hub
CREATE TABLE IF NOT EXISTS community_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts_profiles(id),
    username TEXT UNIQUE,
    display_name TEXT,
    membership_level TEXT,
    join_date TIMESTAMPTZ,
    last_active_date TIMESTAMPTZ,
    engagement_score INTEGER,
    interests JSONB DEFAULT '[]'::JSONB,
    badges JSONB DEFAULT '[]'::JSONB,
    bettermode_member_id TEXT,
    circle_member_id TEXT,
    discord_user_id TEXT,
    slack_user_id TEXT,
    primary_platform TEXT DEFAULT 'BetterMode',
    custom_fields JSONB DEFAULT '{}'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Products & Services
CREATE TABLE IF NOT EXISTS products_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id TEXT UNIQUE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'Active',
    inventory_count INTEGER,
    business_entity_id UUID REFERENCES business_entities(id),
    woocommerce_product_id TEXT,
    amelia_service_id TEXT,
    acuity_service_id TEXT,
    custom_fields JSONB DEFAULT '{}'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Workflow Instances
CREATE TABLE IF NOT EXISTS workflow_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instance_id TEXT UNIQUE,
    workflow_id UUID,
    status instance_status NOT NULL,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    business_entity_id UUID REFERENCES business_entities(id),
    contact_id UUID REFERENCES contacts_profiles(id),
    current_step TEXT,
    step_history JSONB DEFAULT '[]'::JSONB,
    data_payload JSONB DEFAULT '{}'::JSONB,
    related_tasks JSONB DEFAULT '[]'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Marketing Campaigns
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'Draft',
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    business_entity_id UUID REFERENCES business_entities(id),
    target_audience JSONB DEFAULT '[]'::JSONB,
    channels JSONB DEFAULT '[]'::JSONB,
    content_pieces JSONB DEFAULT '[]'::JSONB,
    performance_metrics JSONB DEFAULT '{}'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Feedback & Surveys
CREATE TABLE IF NOT EXISTS feedback_surveys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    survey_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    business_entity_id UUID REFERENCES business_entities(id),
    typeform_id TEXT,
    response_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3, 2),
    survey_data JSONB DEFAULT '{}'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Rewards & Bounties
CREATE TABLE IF NOT EXISTS rewards_bounties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reward_id TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    reward_type TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    points_value INTEGER,
    monetary_value DECIMAL(10, 2),
    business_entity_id UUID REFERENCES business_entities(id),
    eligibility_criteria JSONB DEFAULT '{}'::JSONB,
    redemption_count INTEGER DEFAULT 0,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Master Tasks Database
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id TEXT UNIQUE,
    task_name TEXT NOT NULL,
    status task_status NOT NULL,
    description TEXT NOT NULL,
    priority TEXT DEFAULT 'Medium',
    due_date TIMESTAMPTZ,
    assigned_to TEXT,
    related_workflow_instance UUID REFERENCES workflow_instances(id),
    related_business_entity UUID REFERENCES business_entities(id),
    created_by TEXT,
    created_date TIMESTAMPTZ DEFAULT NOW(),
    last_edited_date TIMESTAMPTZ DEFAULT NOW(),
    tags JSONB DEFAULT '[]'::JSONB,
    notion_page_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_contacts_email ON contacts_profiles(email);
CREATE INDEX idx_contacts_business ON contacts_profiles(business_entity_id);
CREATE INDEX idx_community_contact ON community_members(contact_id);
CREATE INDEX idx_products_business ON products_services(business_entity_id);
CREATE INDEX idx_workflow_business ON workflow_instances(business_entity_id);
CREATE INDEX idx_workflow_contact ON workflow_instances(contact_id);
CREATE INDEX idx_marketing_business ON marketing_campaigns(business_entity_id);
CREATE INDEX idx_feedback_business ON feedback_surveys(business_entity_id);
CREATE INDEX idx_rewards_business ON rewards_bounties(business_entity_id);
CREATE INDEX idx_tasks_workflow ON tasks(related_workflow_instance);
CREATE INDEX idx_tasks_business ON tasks(related_business_entity);
