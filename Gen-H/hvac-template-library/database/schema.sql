CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Shared users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HVAC template library
CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    framework VARCHAR(100),
    status VARCHAR(50),
    version VARCHAR(50),
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    accent_color VARCHAR(7),
    typography_headline VARCHAR(100),
    typography_body VARCHAR(100),
    has_3d_viewer BOOLEAN DEFAULT false,
    has_calculator BOOLEAN DEFAULT false,
    has_before_after BOOLEAN DEFAULT false,
    has_testimonials BOOLEAN DEFAULT false,
    has_case_studies BOOLEAN DEFAULT false,
    has_service_map BOOLEAN DEFAULT false,
    frontend_repo_url VARCHAR(500),
    frontend_branch VARCHAR(100),
    backend_repo_url VARCHAR(500),
    backend_branch VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    preview_image_url VARCHAR(500),
    preview_video_url VARCHAR(500),
    documentation_url VARCHAR(500),
    config JSONB DEFAULT '{}'::jsonb,
    customizable_sections JSONB DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    website_url VARCHAR(500),
    service_areas JSONB,
    business_type VARCHAR(100),
    years_in_business INT,
    logo_url VARCHAR(500),
    brand_color_primary VARCHAR(7),
    brand_color_secondary VARCHAR(7),
    owner_name VARCHAR(255),
    owner_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES templates(id) NOT NULL,
    company_id UUID REFERENCES companies(id) NOT NULL,
    domain VARCHAR(255) NOT NULL UNIQUE,
    subdomain VARCHAR(255),
    status VARCHAR(50),
    deployment_date TIMESTAMP,
    customizations JSONB DEFAULT '{}'::jsonb,
    custom_content JSONB DEFAULT '{}'::jsonb,
    lighthouse_score INT,
    page_speed_score INT,
    last_performance_check TIMESTAMP,
    total_visits INT DEFAULT 0,
    total_leads INT DEFAULT 0,
    lead_conversion_rate DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_by UUID REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS template_customizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id UUID REFERENCES deployments(id) NOT NULL,
    component_name VARCHAR(255),
    custom_settings JSONB,
    custom_content JSONB,
    custom_styles JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id UUID REFERENCES deployments(id),
    event_type VARCHAR(100),
    event_data JSONB,
    user_ip VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lead generator
CREATE TABLE IF NOT EXISTS lead_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    target_locations TEXT[] NOT NULL DEFAULT '{}',
    min_rating DECIMAL(2, 1) DEFAULT 4.0,
    min_review_count INT DEFAULT 20,
    results_per_location INT DEFAULT 50,
    google_sheet_id VARCHAR(255),
    source_artifact_file VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES lead_campaigns(id),
    company_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    rating DECIMAL(2, 1),
    review_count INT,
    years_in_business VARCHAR(50),
    services_offered VARCHAR(255),
    specialties TEXT,
    service_area TEXT,
    unique_selling_points TEXT,
    google_maps_url TEXT,
    research_sources TEXT,
    location_searched VARCHAR(255),
    outreach_status VARCHAR(50) DEFAULT 'new',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_templates_framework ON templates(framework);
CREATE INDEX IF NOT EXISTS idx_templates_status ON templates(status);
CREATE INDEX IF NOT EXISTS idx_companies_slug ON companies(slug);
CREATE INDEX IF NOT EXISTS idx_deployments_template_id ON deployments(template_id);
CREATE INDEX IF NOT EXISTS idx_deployments_company_id ON deployments(company_id);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);
CREATE INDEX IF NOT EXISTS idx_customizations_deployment_id ON template_customizations(deployment_id);
CREATE INDEX IF NOT EXISTS idx_analytics_deployment_id ON analytics_events(deployment_id);
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_leads_campaign ON leads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_leads_outreach_status ON leads(outreach_status);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON lead_campaigns(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_campaigns_source_artifact_file ON lead_campaigns(source_artifact_file) WHERE source_artifact_file IS NOT NULL;
