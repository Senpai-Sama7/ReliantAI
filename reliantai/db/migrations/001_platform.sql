-- ReliantAI Platform Schema
-- Initial migration: all core tables

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── PROSPECTS ───────────────────────────────────────────────────────
CREATE TABLE prospects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id VARCHAR(255) UNIQUE NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    trade VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    address VARCHAR(500),
    lat DECIMAL(10, 8),
    lng DECIMAL(11, 8),
    google_rating DECIMAL(2, 1),
    review_count INTEGER DEFAULT 0,
    website_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'identified',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prospects_trade_city ON prospects(trade, city);
CREATE INDEX idx_prospects_status ON prospects(status);
CREATE INDEX idx_prospects_place_id ON prospects(place_id);

-- ─── RESEARCH JOBS ───────────────────────────────────────────────────
CREATE TABLE research_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    step VARCHAR(50),
    error_message TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_research_jobs_prospect_id ON research_jobs(prospect_id);
CREATE INDEX idx_research_jobs_status ON research_jobs(status);

-- ─── BUSINESS INTELLIGENCE ───────────────────────────────────────────
CREATE TABLE business_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    years_in_business INTEGER,
    service_area VARCHAR(500),
    service_specialties TEXT,
    owner_name VARCHAR(255),
    owner_title VARCHAR(255),
    gbp_profile_complete BOOLEAN DEFAULT FALSE,
    gbp_review_response_rate DECIMAL(5, 2),
    site_last_updated VARCHAR(100),
    site_mobile_friendly BOOLEAN,
    instagram_url VARCHAR(500),
    facebook_url VARCHAR(500),
    linkedin_url VARCHAR(500),
    youtube_url VARCHAR(500),
    yelp_url VARCHAR(500),
    business_hours TEXT,
    payment_methods TEXT,
    certifications TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_business_intelligence_prospect_id ON business_intelligence(prospect_id);

-- ─── COMPETITOR INTELLIGENCE ────────────────────────────────────────
CREATE TABLE competitor_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    competitor_name VARCHAR(255) NOT NULL,
    competitor_website VARCHAR(500),
    top_keywords TEXT,
    content_themes TEXT,
    pricing_strategy TEXT,
    estimated_monthly_volume INTEGER,
    search_ranking_position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_competitor_intelligence_prospect_id ON competitor_intelligence(prospect_id);

-- ─── GENERATED SITES ────────────────────────────────────────────────
CREATE TABLE generated_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    template_id VARCHAR(100) NOT NULL,
    preview_url VARCHAR(500),
    production_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'preview_live',
    site_content JSONB,
    site_config JSONB,
    schema_org_json JSONB,
    meta_title VARCHAR(255),
    meta_description VARCHAR(500),
    lighthouse_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generated_sites_prospect_id ON generated_sites(prospect_id);
CREATE INDEX idx_generated_sites_slug ON generated_sites(slug);
CREATE INDEX idx_generated_sites_status ON generated_sites(status);

-- ─── CLIENTS ────────────────────────────────────────────────────────
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    package VARCHAR(50),
    custom_domain VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clients_prospect_id ON clients(prospect_id);
CREATE INDEX idx_clients_stripe_customer_id ON clients(stripe_customer_id);

-- ─── OUTREACH SEQUENCES ─────────────────────────────────────────────
CREATE TABLE outreach_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    sequence_template VARCHAR(100) DEFAULT 'home_services_v1',
    status VARCHAR(50) DEFAULT 'pending',
    current_step INTEGER DEFAULT 0,
    max_steps INTEGER DEFAULT 4,
    next_send_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_outreach_sequences_prospect_id ON outreach_sequences(prospect_id);
CREATE INDEX idx_outreach_sequences_status ON outreach_sequences(status);
CREATE INDEX idx_outreach_sequences_next_send_at ON outreach_sequences(next_send_at)
    WHERE status = 'active';

-- ─── OUTREACH MESSAGES ──────────────────────────────────────────────
CREATE TABLE outreach_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_id UUID NOT NULL REFERENCES outreach_sequences(id) ON DELETE CASCADE,
    prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    channel VARCHAR(50) NOT NULL,
    to_address VARCHAR(255) NOT NULL,
    from_address VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    body TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'queued',
    provider_message_id VARCHAR(255),
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_outreach_messages_sequence_id ON outreach_messages(sequence_id);
CREATE INDEX idx_outreach_messages_prospect_id ON outreach_messages(prospect_id);
CREATE INDEX idx_outreach_messages_status ON outreach_messages(status);

-- ─── LEAD EVENTS (for inbound replies, opt-outs, etc.) ───────────────
CREATE TABLE lead_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    from_address VARCHAR(255),
    message_body TEXT,
    is_hot_lead BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lead_events_prospect_id ON lead_events(prospect_id);
CREATE INDEX idx_lead_events_event_type ON lead_events(event_type);
