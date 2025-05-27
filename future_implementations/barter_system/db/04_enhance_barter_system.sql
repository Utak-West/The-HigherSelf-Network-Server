-- Enhanced Barter System Migration for HigherSelf Network
-- This migration adds multi-language support, user integration, and enhanced features

-- Add multi-language support
CREATE TABLE IF NOT EXISTS barter_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('listing', 'request', 'profile', 'category')),
    entity_id UUID NOT NULL,
    language_code VARCHAR(5) NOT NULL, -- ISO 639-1 with optional country code (e.g., 'en', 'en-US')
    field_name VARCHAR(100) NOT NULL,
    translated_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(entity_type, entity_id, language_code, field_name)
);

-- Create indexes for translations
CREATE INDEX idx_barter_translations_entity ON barter_translations (entity_type, entity_id);
CREATE INDEX idx_barter_translations_language ON barter_translations (language_code);
CREATE INDEX idx_barter_translations_field ON barter_translations (field_name);

-- Add user integration table
CREATE TABLE IF NOT EXISTS barter_user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL UNIQUE, -- Links to main user system
    barter_profile_id UUID REFERENCES barter_profiles(id),
    preferred_language VARCHAR(5) DEFAULT 'en',
    timezone_name VARCHAR(50),
    notification_preferences JSONB DEFAULT '{}',
    privacy_settings JSONB DEFAULT '{}',
    verification_status VARCHAR(20) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected')),
    verification_documents JSONB DEFAULT '[]',
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for user profiles
CREATE INDEX idx_barter_user_profiles_user_id ON barter_user_profiles (user_id);
CREATE INDEX idx_barter_user_profiles_verification ON barter_user_profiles (verification_status);
CREATE INDEX idx_barter_user_profiles_language ON barter_user_profiles (preferred_language);

-- Add enhanced location features
ALTER TABLE barter_locations ADD COLUMN IF NOT EXISTS geocoding_accuracy VARCHAR(20);
ALTER TABLE barter_locations ADD COLUMN IF NOT EXISTS privacy_level VARCHAR(20) DEFAULT 'normal' CHECK (privacy_level IN ('exact', 'approximate', 'city_only'));
ALTER TABLE barter_locations ADD COLUMN IF NOT EXISTS location_source VARCHAR(50) DEFAULT 'manual';

-- Add search optimization table
CREATE TABLE IF NOT EXISTS barter_search_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_hash VARCHAR(64) NOT NULL UNIQUE, -- Hash of search parameters
    search_params JSONB NOT NULL,
    results JSONB NOT NULL,
    result_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes for search cache
CREATE INDEX idx_barter_search_cache_hash ON barter_search_cache (search_hash);
CREATE INDEX idx_barter_search_cache_expires ON barter_search_cache (expires_at);

-- Add performance metrics table
CREATE TABLE IF NOT EXISTS barter_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    dimensions JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for metrics
CREATE INDEX idx_barter_metrics_type_name ON barter_metrics (metric_type, metric_name);
CREATE INDEX idx_barter_metrics_timestamp ON barter_metrics (timestamp);

-- Add enhanced cultural adaptations
ALTER TABLE cultural_adaptations ADD COLUMN IF NOT EXISTS time_zone_preferences TEXT[] DEFAULT '{}';
ALTER TABLE cultural_adaptations ADD COLUMN IF NOT EXISTS business_hours JSONB DEFAULT '{}';
ALTER TABLE cultural_adaptations ADD COLUMN IF NOT EXISTS holiday_calendar JSONB DEFAULT '{}';
ALTER TABLE cultural_adaptations ADD COLUMN IF NOT EXISTS communication_styles JSONB DEFAULT '{}';

-- Add notification preferences table
CREATE TABLE IF NOT EXISTS barter_notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    channels TEXT[] DEFAULT ARRAY['in_app'],
    frequency VARCHAR(20) DEFAULT 'immediate' CHECK (frequency IN ('immediate', 'hourly', 'daily', 'weekly')),
    quiet_hours JSONB DEFAULT '{}', -- {"start": "22:00", "end": "08:00"}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, notification_type)
);

-- Create indexes for notification preferences
CREATE INDEX idx_barter_notification_prefs_user ON barter_notification_preferences (user_id);
CREATE INDEX idx_barter_notification_prefs_type ON barter_notification_preferences (notification_type);

-- Add audit trail table
CREATE TABLE IF NOT EXISTS barter_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audit log
CREATE INDEX idx_barter_audit_entity ON barter_audit_log (entity_type, entity_id);
CREATE INDEX idx_barter_audit_user ON barter_audit_log (user_id);
CREATE INDEX idx_barter_audit_created ON barter_audit_log (created_at);

-- Add triggers for audit logging
CREATE OR REPLACE FUNCTION barter_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO barter_audit_log (entity_type, entity_id, action, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO barter_audit_log (entity_type, entity_id, action, old_values, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO barter_audit_log (entity_type, entity_id, action, old_values)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to main tables
CREATE TRIGGER barter_listings_audit AFTER INSERT OR UPDATE OR DELETE ON barter_listings
    FOR EACH ROW EXECUTE FUNCTION barter_audit_trigger();
CREATE TRIGGER barter_requests_audit AFTER INSERT OR UPDATE OR DELETE ON barter_requests
    FOR EACH ROW EXECUTE FUNCTION barter_audit_trigger();
CREATE TRIGGER barter_transactions_audit AFTER INSERT OR UPDATE OR DELETE ON barter_transactions
    FOR EACH ROW EXECUTE FUNCTION barter_audit_trigger();
CREATE TRIGGER barter_profiles_audit AFTER INSERT OR UPDATE OR DELETE ON barter_profiles
    FOR EACH ROW EXECUTE FUNCTION barter_audit_trigger();

-- Add update triggers for new tables
CREATE TRIGGER update_barter_translations_updated_at BEFORE UPDATE ON barter_translations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_barter_user_profiles_updated_at BEFORE UPDATE ON barter_user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_barter_notification_preferences_updated_at BEFORE UPDATE ON barter_notification_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add enhanced search functions
CREATE OR REPLACE FUNCTION search_barter_listings_enhanced(
    search_lat DECIMAL,
    search_lon DECIMAL,
    search_radius_km DECIMAL DEFAULT 50,
    search_category service_category DEFAULT NULL,
    search_language VARCHAR(5) DEFAULT 'en',
    search_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    listing_id UUID,
    title TEXT,
    description TEXT,
    category service_category,
    distance_km DECIMAL,
    provider_name TEXT,
    skill_level skill_level,
    base_value_per_hour DECIMAL,
    cultural_region cultural_region
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        bl.id,
        COALESCE(bt.translated_text, bl.title) as title,
        COALESCE(bt_desc.translated_text, bl.description) as description,
        bl.category,
        ST_Distance(
            ST_Point(search_lon, search_lat)::geography,
            loc.coordinates
        ) / 1000 as distance_km,
        bp.name as provider_name,
        bl.skill_level,
        bl.base_value_per_hour,
        loc.cultural_region
    FROM barter_listings bl
    JOIN barter_locations loc ON bl.location_id = loc.id
    LEFT JOIN barter_profiles bp ON bl.provider_id = bp.entity_id
    LEFT JOIN barter_translations bt ON (
        bt.entity_type = 'listing' AND
        bt.entity_id = bl.id AND
        bt.field_name = 'title' AND
        bt.language_code = search_language
    )
    LEFT JOIN barter_translations bt_desc ON (
        bt_desc.entity_type = 'listing' AND
        bt_desc.entity_id = bl.id AND
        bt_desc.field_name = 'description' AND
        bt_desc.language_code = search_language
    )
    WHERE
        bl.status = 'active' AND
        (bl.expires_at IS NULL OR bl.expires_at > NOW()) AND
        ST_DWithin(
            ST_Point(search_lon, search_lat)::geography,
            loc.coordinates,
            search_radius_km * 1000
        ) AND
        (search_category IS NULL OR bl.category = search_category)
    ORDER BY distance_km ASC
    LIMIT search_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get cultural recommendations
CREATE OR REPLACE FUNCTION get_cultural_recommendations(
    user_region cultural_region,
    user_language VARCHAR(5) DEFAULT 'en'
)
RETURNS TABLE (
    category service_category,
    weight DECIMAL,
    seasonal_relevance JSONB,
    cultural_practices TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        unnest(ca.preferred_categories) as category,
        1.0 as weight, -- This would be calculated based on cultural preferences
        ca.seasonal_services as seasonal_relevance,
        ca.cultural_practices
    FROM cultural_adaptations ca
    WHERE ca.region = user_region;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM barter_search_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to clean up cache (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-barter-cache', '0 */6 * * *', 'SELECT cleanup_expired_cache();');
