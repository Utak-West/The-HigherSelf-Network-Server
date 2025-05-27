-- Barter System Database Schema for The HigherSelf Network
-- This schema supports location-based service exchanges with cultural adaptation

-- Enable PostGIS extension for geographic operations
CREATE EXTENSION IF NOT EXISTS postgis;

-- Service Categories Enum
CREATE TYPE service_category AS ENUM (
    'wellness_consultation',
    'massage_therapy',
    'yoga_instruction',
    'meditation_guidance',
    'nutrition_counseling',
    'energy_healing',
    'art_creation',
    'art_curation',
    'photography',
    'graphic_design',
    'creative_workshops',
    'art_installation',
    'business_strategy',
    'marketing_consultation',
    'financial_planning',
    'legal_consultation',
    'technology_consulting',
    'project_management',
    'skill_training',
    'language_instruction',
    'professional_development',
    'mentorship',
    'workshop_facilitation',
    'traditional_healing',
    'cultural_practices',
    'spiritual_guidance',
    'ceremonial_services',
    'web_development',
    'digital_marketing',
    'content_creation',
    'social_media_management',
    'personal_styling',
    'home_organization',
    'gardening',
    'cooking_instruction',
    'other'
);

-- Skill Levels Enum
CREATE TYPE skill_level AS ENUM (
    'beginner',
    'intermediate',
    'advanced',
    'expert',
    'master'
);

-- Barter Status Enum
CREATE TYPE barter_status AS ENUM (
    'draft',
    'active',
    'pending_approval',
    'matched',
    'in_progress',
    'completed',
    'cancelled',
    'expired'
);

-- Cultural Regions Enum
CREATE TYPE cultural_region AS ENUM (
    'north_america',
    'south_america',
    'europe',
    'asia_pacific',
    'middle_east',
    'africa',
    'oceania'
);

-- Locations Table
CREATE TABLE barter_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address TEXT,
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    country VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    coordinates GEOGRAPHY(POINT, 4326), -- PostGIS geography type for lat/lng
    cultural_region cultural_region NOT NULL,
    timezone_name VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create spatial index for geographic queries
CREATE INDEX idx_barter_locations_coordinates ON barter_locations USING GIST (coordinates);
CREATE INDEX idx_barter_locations_cultural_region ON barter_locations (cultural_region);
CREATE INDEX idx_barter_locations_city_country ON barter_locations (city, country);

-- Cultural Adaptations Table
CREATE TABLE cultural_adaptations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region cultural_region NOT NULL UNIQUE,
    preferred_categories service_category[] DEFAULT '{}',
    seasonal_services JSONB DEFAULT '{}', -- JSON object with season -> categories mapping
    cultural_practices TEXT[] DEFAULT '{}',
    local_customs JSONB DEFAULT '{}',
    language_preferences TEXT[] DEFAULT '{}',
    currency_equivalent_base VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Barter Profiles Table
CREATE TABLE barter_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(255) NOT NULL UNIQUE,
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('individual', 'business', 'organization')),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location_id UUID REFERENCES barter_locations(id),

    -- Service Capabilities
    offered_services service_category[] DEFAULT '{}',
    skill_levels JSONB DEFAULT '{}', -- JSON object mapping categories to skill levels
    service_descriptions JSONB DEFAULT '{}', -- JSON object mapping categories to descriptions

    -- Service Needs
    needed_services service_category[] DEFAULT '{}',
    service_priorities JSONB DEFAULT '{}', -- JSON object mapping categories to priority numbers

    -- Preferences & Constraints
    max_travel_distance_km DECIMAL(8,2) DEFAULT 25.0,
    virtual_service_preference BOOLEAN DEFAULT TRUE,
    preferred_exchange_duration VARCHAR(20) DEFAULT 'medium' CHECK (preferred_exchange_duration IN ('short', 'medium', 'long')),
    cultural_adaptation_id UUID REFERENCES cultural_adaptations(id),

    -- Capacity & Availability
    available_hours_per_week DECIMAL(5,2) DEFAULT 10.0 CHECK (available_hours_per_week > 0 AND available_hours_per_week <= 168),
    max_concurrent_transactions INTEGER DEFAULT 3 CHECK (max_concurrent_transactions >= 1),

    -- Performance Metrics
    total_transactions INTEGER DEFAULT 0 CHECK (total_transactions >= 0),
    average_rating DECIMAL(3,2) CHECK (average_rating >= 1.0 AND average_rating <= 5.0),
    completion_rate DECIMAL(3,2) DEFAULT 1.0 CHECK (completion_rate >= 0.0 AND completion_rate <= 1.0),
    response_time_hours DECIMAL(6,2),

    -- Status
    active BOOLEAN DEFAULT TRUE,
    verified BOOLEAN DEFAULT FALSE,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Integration
    notion_page_id VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for barter profiles
CREATE INDEX idx_barter_profiles_entity_id ON barter_profiles (entity_id);
CREATE INDEX idx_barter_profiles_entity_type ON barter_profiles (entity_type);
CREATE INDEX idx_barter_profiles_location_id ON barter_profiles (location_id);
CREATE INDEX idx_barter_profiles_offered_services ON barter_profiles USING GIN (offered_services);
CREATE INDEX idx_barter_profiles_needed_services ON barter_profiles USING GIN (needed_services);
CREATE INDEX idx_barter_profiles_active ON barter_profiles (active);

-- Barter Listings Table
CREATE TABLE barter_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id VARCHAR(255) NOT NULL,
    provider_type VARCHAR(50) NOT NULL CHECK (provider_type IN ('individual', 'business')),

    -- Service Details
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category service_category NOT NULL,
    subcategory VARCHAR(100),
    skill_level skill_level NOT NULL,

    -- Location & Cultural Context
    location_id UUID REFERENCES barter_locations(id),
    service_radius_km DECIMAL(8,2), -- Service delivery radius in kilometers
    virtual_available BOOLEAN DEFAULT FALSE,
    cultural_adaptation_id UUID REFERENCES cultural_adaptations(id),

    -- Availability & Capacity
    available_hours_per_week DECIMAL(5,2) NOT NULL CHECK (available_hours_per_week > 0 AND available_hours_per_week <= 168),
    estimated_session_duration DECIMAL(4,2) NOT NULL, -- Duration in hours
    max_concurrent_exchanges INTEGER DEFAULT 3 CHECK (max_concurrent_exchanges >= 1),

    -- Valuation
    base_value_per_hour DECIMAL(10,2) NOT NULL, -- Base monetary equivalent per hour
    preferred_exchange_types service_category[] DEFAULT '{}',

    -- Status & Metadata
    status barter_status DEFAULT 'draft',
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Integration
    notion_page_id VARCHAR(255),
    tags TEXT[] DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for barter listings
CREATE INDEX idx_barter_listings_provider_id ON barter_listings (provider_id);
CREATE INDEX idx_barter_listings_category ON barter_listings (category);
CREATE INDEX idx_barter_listings_skill_level ON barter_listings (skill_level);
CREATE INDEX idx_barter_listings_location_id ON barter_listings (location_id);
CREATE INDEX idx_barter_listings_status ON barter_listings (status);
CREATE INDEX idx_barter_listings_virtual_available ON barter_listings (virtual_available);
CREATE INDEX idx_barter_listings_preferred_exchange_types ON barter_listings USING GIN (preferred_exchange_types);
CREATE INDEX idx_barter_listings_expires_at ON barter_listings (expires_at);

-- Barter Requests Table
CREATE TABLE barter_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id VARCHAR(255) NOT NULL,
    requester_type VARCHAR(50) NOT NULL CHECK (requester_type IN ('individual', 'business')),

    -- Service Requirements
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category service_category NOT NULL,
    preferred_skill_level skill_level DEFAULT 'intermediate',

    -- Location Preferences
    preferred_location_id UUID REFERENCES barter_locations(id),
    max_distance_km DECIMAL(8,2) DEFAULT 50.0,
    virtual_acceptable BOOLEAN DEFAULT TRUE,

    -- Exchange Offer
    offered_service_category service_category NOT NULL,
    offered_service_description TEXT NOT NULL,
    offered_value_per_hour DECIMAL(10,2) NOT NULL,
    offered_total_hours DECIMAL(6,2) NOT NULL,

    -- Requirements
    required_total_hours DECIMAL(6,2) NOT NULL,
    flexible_scheduling BOOLEAN DEFAULT TRUE,
    urgency_level VARCHAR(20) DEFAULT 'normal' CHECK (urgency_level IN ('low', 'normal', 'high', 'urgent')),

    -- Status & Metadata
    status barter_status DEFAULT 'active',
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Integration
    notion_page_id VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for barter requests
CREATE INDEX idx_barter_requests_requester_id ON barter_requests (requester_id);
CREATE INDEX idx_barter_requests_category ON barter_requests (category);
CREATE INDEX idx_barter_requests_preferred_skill_level ON barter_requests (preferred_skill_level);
CREATE INDEX idx_barter_requests_preferred_location_id ON barter_requests (preferred_location_id);
CREATE INDEX idx_barter_requests_status ON barter_requests (status);
CREATE INDEX idx_barter_requests_offered_service_category ON barter_requests (offered_service_category);
CREATE INDEX idx_barter_requests_urgency_level ON barter_requests (urgency_level);

-- Barter Matches Table
CREATE TABLE barter_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID REFERENCES barter_listings(id),
    request_id UUID REFERENCES barter_requests(id),

    -- Match Quality Metrics
    compatibility_score DECIMAL(3,2) NOT NULL CHECK (compatibility_score >= 0 AND compatibility_score <= 1),
    distance_km DECIMAL(8,2),
    category_match BOOLEAN DEFAULT FALSE,
    skill_level_match BOOLEAN DEFAULT FALSE,
    value_balance_ratio DECIMAL(3,2) NOT NULL,

    -- Cultural Compatibility
    cultural_compatibility_score DECIMAL(3,2) DEFAULT 1.0 CHECK (cultural_compatibility_score >= 0 AND cultural_compatibility_score <= 1),
    language_compatibility BOOLEAN DEFAULT TRUE,

    -- Match Details
    suggested_exchange_structure JSONB DEFAULT '{}',
    estimated_completion_time VARCHAR(50),

    -- Status
    status VARCHAR(20) DEFAULT 'suggested' CHECK (status IN ('suggested', 'viewed', 'contacted', 'negotiating', 'accepted', 'declined')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for barter matches
CREATE INDEX idx_barter_matches_listing_id ON barter_matches (listing_id);
CREATE INDEX idx_barter_matches_request_id ON barter_matches (request_id);
CREATE INDEX idx_barter_matches_compatibility_score ON barter_matches (compatibility_score DESC);
CREATE INDEX idx_barter_matches_status ON barter_matches (status);
CREATE INDEX idx_barter_matches_created_at ON barter_matches (created_at DESC);

-- Barter Transactions Table
CREATE TABLE barter_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES barter_matches(id),
    provider_id VARCHAR(255) NOT NULL,
    requester_id VARCHAR(255) NOT NULL,

    -- Service Details
    provider_service JSONB NOT NULL, -- Details of provided service
    requester_service JSONB NOT NULL, -- Details of requested service

    -- Agreement Terms
    agreed_provider_hours DECIMAL(6,2) NOT NULL,
    agreed_requester_hours DECIMAL(6,2) NOT NULL,
    total_value_exchanged DECIMAL(12,2) NOT NULL,

    -- Schedule & Delivery
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    estimated_completion_date TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_completion_date TIMESTAMP WITH TIME ZONE,

    -- Progress Tracking
    provider_progress_percentage DECIMAL(5,2) DEFAULT 0 CHECK (provider_progress_percentage >= 0 AND provider_progress_percentage <= 100),
    requester_progress_percentage DECIMAL(5,2) DEFAULT 0 CHECK (requester_progress_percentage >= 0 AND requester_progress_percentage <= 100),
    milestones JSONB DEFAULT '[]',

    -- Communication
    communication_log JSONB DEFAULT '[]',

    -- Status & Completion
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'cancelled', 'disputed')),
    completion_notes TEXT,

    -- Reviews & Ratings
    provider_rating DECIMAL(3,2) CHECK (provider_rating >= 1.0 AND provider_rating <= 5.0),
    requester_rating DECIMAL(3,2) CHECK (requester_rating >= 1.0 AND requester_rating <= 5.0),
    provider_review TEXT,
    requester_review TEXT,

    -- Integration
    notion_page_id VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for barter transactions
CREATE INDEX idx_barter_transactions_match_id ON barter_transactions (match_id);
CREATE INDEX idx_barter_transactions_provider_id ON barter_transactions (provider_id);
CREATE INDEX idx_barter_transactions_requester_id ON barter_transactions (requester_id);
CREATE INDEX idx_barter_transactions_status ON barter_transactions (status);
CREATE INDEX idx_barter_transactions_start_date ON barter_transactions (start_date);
CREATE INDEX idx_barter_transactions_estimated_completion_date ON barter_transactions (estimated_completion_date);

-- Create triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to all tables
CREATE TRIGGER update_barter_locations_updated_at BEFORE UPDATE ON barter_locations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cultural_adaptations_updated_at BEFORE UPDATE ON cultural_adaptations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_barter_profiles_updated_at BEFORE UPDATE ON barter_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_barter_listings_updated_at BEFORE UPDATE ON barter_listings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_barter_requests_updated_at BEFORE UPDATE ON barter_requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_barter_matches_updated_at BEFORE UPDATE ON barter_matches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_barter_transactions_updated_at BEFORE UPDATE ON barter_transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default cultural adaptations
INSERT INTO cultural_adaptations (region, preferred_categories, seasonal_services, cultural_practices, language_preferences, currency_equivalent_base) VALUES
('north_america',
 ARRAY['wellness_consultation', 'business_strategy', 'technology_consulting', 'yoga_instruction']::service_category[],
 '{"winter": ["meditation_guidance", "energy_healing"], "spring": ["gardening", "nutrition_counseling"], "summer": ["yoga_instruction", "photography"], "fall": ["art_creation", "skill_training"]}',
 ARRAY['mindfulness', 'holistic_wellness', 'work_life_balance'],
 ARRAY['english', 'spanish'],
 'USD'),

('europe',
 ARRAY['art_creation', 'traditional_healing', 'language_instruction', 'cultural_practices']::service_category[],
 '{"winter": ["art_creation", "skill_training"], "spring": ["gardening", "cultural_practices"], "summer": ["photography", "creative_workshops"], "fall": ["traditional_healing", "mentorship"]}',
 ARRAY['traditional_arts', 'cultural_heritage', 'community_focus'],
 ARRAY['english', 'french', 'german', 'spanish', 'italian'],
 'EUR'),

('asia_pacific',
 ARRAY['traditional_healing', 'meditation_guidance', 'spiritual_guidance']::service_category[],
 '{"winter": ["meditation_guidance", "traditional_healing"], "spring": ["energy_healing", "spiritual_guidance"], "summer": ["cultural_practices"], "fall": ["skill_training", "mentorship"]}',
 ARRAY['harmony', 'balance', 'ancestral_wisdom'],
 ARRAY['english', 'mandarin', 'japanese', 'korean'],
 'USD'),

('south_america',
 ARRAY['traditional_healing', 'art_creation', 'cultural_practices', 'spiritual_guidance']::service_category[],
 '{"winter": ["traditional_healing", "spiritual_guidance"], "spring": ["art_creation", "cultural_practices"], "summer": ["creative_workshops", "photography"], "fall": ["skill_training", "mentorship"]}',
 ARRAY['community_spirit', 'traditional_wisdom', 'artistic_expression'],
 ARRAY['spanish', 'portuguese', 'english'],
 'USD'),

('middle_east',
 ARRAY['traditional_healing', 'spiritual_guidance', 'cultural_practices', 'business_strategy']::service_category[],
 '{"winter": ["spiritual_guidance", "traditional_healing"], "spring": ["cultural_practices", "art_creation"], "summer": ["business_strategy", "skill_training"], "fall": ["mentorship", "language_instruction"]}',
 ARRAY['hospitality', 'traditional_values', 'spiritual_connection'],
 ARRAY['arabic', 'english', 'persian', 'turkish'],
 'USD'),

('africa',
 ARRAY['traditional_healing', 'cultural_practices', 'art_creation', 'spiritual_guidance']::service_category[],
 '{"winter": ["traditional_healing", "spiritual_guidance"], "spring": ["cultural_practices", "art_creation"], "summer": ["creative_workshops", "skill_training"], "fall": ["mentorship", "language_instruction"]}',
 ARRAY['ubuntu', 'community_healing', 'ancestral_wisdom'],
 ARRAY['english', 'french', 'arabic', 'swahili'],
 'USD'),

('oceania',
 ARRAY['wellness_consultation', 'traditional_healing', 'art_creation', 'spiritual_guidance']::service_category[],
 '{"winter": ["meditation_guidance", "traditional_healing"], "spring": ["wellness_consultation", "art_creation"], "summer": ["photography", "creative_workshops"], "fall": ["skill_training", "spiritual_guidance"]}',
 ARRAY['connection_to_nature', 'holistic_wellness', 'indigenous_wisdom'],
 ARRAY['english'],
 'AUD');

-- Create views for common queries

-- Active listings with location details
CREATE VIEW active_barter_listings_with_location AS
SELECT
    bl.*,
    loc.city,
    loc.state_province,
    loc.country,
    loc.cultural_region,
    ST_X(loc.coordinates::geometry) as longitude,
    ST_Y(loc.coordinates::geometry) as latitude
FROM barter_listings bl
JOIN barter_locations loc ON bl.location_id = loc.id
WHERE bl.status = 'active' AND (bl.expires_at IS NULL OR bl.expires_at > NOW());

-- Active requests with location details
CREATE VIEW active_barter_requests_with_location AS
SELECT
    br.*,
    loc.city,
    loc.state_province,
    loc.country,
    loc.cultural_region,
    ST_X(loc.coordinates::geometry) as longitude,
    ST_Y(loc.coordinates::geometry) as latitude
FROM barter_requests br
JOIN barter_locations loc ON br.preferred_location_id = loc.id
WHERE br.status = 'active' AND (br.expires_at IS NULL OR br.expires_at > NOW());

-- Profile performance summary
CREATE VIEW barter_profile_performance AS
SELECT
    bp.*,
    COALESCE(completed_transactions.count, 0) as completed_transaction_count,
    COALESCE(active_transactions.count, 0) as active_transaction_count,
    COALESCE(avg_ratings.avg_provider_rating, 0) as avg_provider_rating,
    COALESCE(avg_ratings.avg_requester_rating, 0) as avg_requester_rating
FROM barter_profiles bp
LEFT JOIN (
    SELECT provider_id, COUNT(*) as count
    FROM barter_transactions
    WHERE status = 'completed'
    GROUP BY provider_id
) completed_transactions ON bp.entity_id = completed_transactions.provider_id
LEFT JOIN (
    SELECT provider_id, COUNT(*) as count
    FROM barter_transactions
    WHERE status IN ('active', 'in_progress')
    GROUP BY provider_id
) active_transactions ON bp.entity_id = active_transactions.provider_id
LEFT JOIN (
    SELECT
        provider_id,
        AVG(provider_rating) as avg_provider_rating,
        AVG(requester_rating) as avg_requester_rating
    FROM barter_transactions
    WHERE provider_rating IS NOT NULL OR requester_rating IS NOT NULL
    GROUP BY provider_id
) avg_ratings ON bp.entity_id = avg_ratings.provider_id;
