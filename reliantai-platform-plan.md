# ReliantAI Platform — Full Integration & Build Plan
## Home Services Website Factory + Autonomous Agent Pipeline

**Version:** 1.0 — April 2026  
**Scope:** End-to-end architecture, implementation sequence, code contracts, and security posture  
**Runtime decision (locked):** CrewAI + FastAPI + Celery + Redis (Python). LangGraph flagged as v2 migration path.

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RELIANTAI PLATFORM (reliantai/)                  │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │  API Layer  │  │  Agent Crew  │  │     Site Factory          │  │
│  │  FastAPI    │  │  CrewAI +    │  │   Next.js 15 templates    │  │
│  │  /api/v2    │  │  Gemini 1.5  │  │   Vercel deploy API       │  │
│  └──────┬──────┘  └──────┬───────┘  └────────────┬──────────────┘  │
│         │                │                        │                 │
│  ┌──────▼──────────────▼─────────────────────────▼──────────────┐  │
│  │              Celery Task Queue (Redis broker)                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Postgres    │  │    Redis     │  │   Cloudflare R2          │  │
│  │  (prospects, │  │  (cache +    │  │   (assets, photos,       │  │
│  │   jobs,sites)│  │   sessions)  │  │    generated bundles)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         ▲ API calls (internal)
         │
┌────────┴───────────────────────────────────────────────────────────┐
│              RELIANTAI MARKETING SITE (reliantai-website/)         │
│              reliantai.org  (Vite + React 19, Vercel)              │
│                                                                    │
│  Hero → Loss Calculator → Demo Preview → Pricing → CTA            │
└────────────────────────────────────────────────────────────────────┘
         │
         │ /preview/{slug}  (ISR page in reliantai-website)
         │
┌────────▼───────────────────────────────────────────────────────────┐
│              CLIENT PREVIEW + PRODUCTION SITES                     │
│                                                                    │
│  Preview:    reliantai.org/preview/{slug}                          │
│  Production: {slug}.clients.reliantai.org  (or custom domain)     │
│                                                                    │
│  Built by SiteBuilderAgent, deployed via Vercel Deploy API         │
└────────────────────────────────────────────────────────────────────┘
```

---

## PHASE 0: DATA SCHEMA — THE FOUNDATION

Build this first. Everything else writes to or reads from it.

### 0A. Postgres Schema (`reliantai/db/migrations/001_platform.sql`)

```sql
-- ============================================================
-- PROSPECTS: businesses identified as targets
-- ============================================================
CREATE TABLE prospects (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  place_id        TEXT UNIQUE NOT NULL,          -- Google Places ID
  business_name   TEXT NOT NULL,
  trade           TEXT NOT NULL,                 -- hvac|plumbing|electrical|roofing|painting|landscaping
  phone           TEXT,
  address         TEXT,
  city            TEXT NOT NULL,
  state           TEXT NOT NULL,
  zip             TEXT,
  lat             DECIMAL(9,6),
  lng             DECIMAL(9,6),
  google_rating   DECIMAL(2,1),
  review_count    INT DEFAULT 0,
  website_url     TEXT,                          -- NULL or weak = target
  website_score   SMALLINT,                      -- 0-100, lower = more opportunity
  status          TEXT NOT NULL DEFAULT 'identified',
                  -- identified | researched | site_built | outreach_sent
                  -- | responded | converted | disqualified
  disqualify_reason TEXT,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_prospects_trade_city ON prospects(trade, city);
CREATE INDEX idx_prospects_status ON prospects(status);
CREATE INDEX idx_prospects_place_id ON prospects(place_id);

-- ============================================================
-- RESEARCH JOBS: agent pipeline executions
-- ============================================================
CREATE TABLE research_jobs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id     UUID REFERENCES prospects(id) ON DELETE CASCADE,
  celery_task_id  TEXT,
  status          TEXT NOT NULL DEFAULT 'queued',
                  -- queued | running | completed | failed | retrying
  step            TEXT,  -- which agent is currently active
  retry_count     SMALLINT DEFAULT 0,
  error_message   TEXT,
  started_at      TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- BUSINESS INTELLIGENCE: research agent output
-- ============================================================
CREATE TABLE business_intelligence (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id     UUID REFERENCES prospects(id) ON DELETE CASCADE,
  
  -- Review intelligence
  top_review_themes     TEXT[],              -- ['fast response', 'clean work', 'fair price']
  sentiment_score       DECIMAL(3,2),        -- 0.0 to 1.0
  star_distribution     JSONB,              -- {"5": 40, "4": 12, "3": 2, "2": 1, "1": 0}
  notable_quotes        TEXT[],             -- verbatim review excerpts (max 5)
  
  -- Business profile
  years_in_business     INT,
  certifications        TEXT[],
  service_areas         TEXT[],
  services_offered      TEXT[],
  owner_name            TEXT,
  
  -- Social/digital footprint
  facebook_url          TEXT,
  instagram_url         TEXT,
  yelp_url              TEXT,
  bbb_url               TEXT,
  has_photos            BOOLEAN DEFAULT false,
  photo_count           INT DEFAULT 0,
  
  -- GBP data
  gbp_posts_count       INT DEFAULT 0,
  gbp_qa_count          INT DEFAULT 0,
  gbp_completeness_pct  SMALLINT,          -- 0-100
  
  -- Current website weakness analysis
  site_page_speed       SMALLINT,          -- PageSpeed Insights mobile score
  site_has_ssl          BOOLEAN,
  site_has_schema       BOOLEAN,
  site_has_gmb          BOOLEAN,
  site_word_count       INT,
  site_has_mobile       BOOLEAN,
  
  raw_data              JSONB,             -- full scraped payload
  created_at            TIMESTAMPTZ DEFAULT now(),
  updated_at            TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- COMPETITOR INTELLIGENCE
-- ============================================================
CREATE TABLE competitor_intelligence (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id     UUID REFERENCES prospects(id) ON DELETE CASCADE,
  competitor_place_id   TEXT NOT NULL,
  competitor_name       TEXT NOT NULL,
  competitor_rating     DECIMAL(2,1),
  competitor_review_count INT,
  competitor_website    TEXT,
  
  -- Weakness gaps we can exploit
  missing_schema        BOOLEAN DEFAULT false,
  missing_reviews_response BOOLEAN DEFAULT false,
  missing_aeo           BOOLEAN DEFAULT false,
  site_speed_score      SMALLINT,
  
  top_keywords          TEXT[],
  gap_opportunities     TEXT[],
  
  created_at            TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- GENERATED SITES: the deliverable
-- ============================================================
CREATE TABLE generated_sites (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id     UUID REFERENCES prospects(id) ON DELETE CASCADE,
  client_id       UUID REFERENCES clients(id) ON DELETE SET NULL,
  
  slug            TEXT UNIQUE NOT NULL,        -- e.g. 'apex-hvac-houston'
  template_id     TEXT NOT NULL,              -- 'hvac-premium' | 'plumbing-bold' etc.
  
  -- URLs
  preview_url     TEXT,                       -- reliantai.org/preview/{slug}
  production_url  TEXT,                       -- {slug}.clients.reliantai.org
  custom_domain   TEXT,                       -- after upgrade
  
  -- Vercel deployment
  vercel_project_id     TEXT,
  vercel_deployment_id  TEXT,
  vercel_deploy_status  TEXT,
  
  -- Generated content (stored as JSON for version history)
  site_content    JSONB NOT NULL,             -- all copy, structured data, schema
  site_config     JSONB NOT NULL,             -- theme, colors, fonts, trade
  
  -- SEO/GEO/AEO metadata
  schema_org_json JSONB,
  meta_title      TEXT,
  meta_description TEXT,
  
  -- State
  status          TEXT NOT NULL DEFAULT 'building',
                  -- building | preview_live | purchased | production_live | suspended
  
  build_time_sec  SMALLINT,
  lighthouse_score SMALLINT,
  
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- CLIENTS: converted prospects
-- ============================================================
CREATE TABLE clients (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id     UUID REFERENCES prospects(id),
  stripe_customer_id    TEXT UNIQUE,
  stripe_subscription_id TEXT,
  
  package         TEXT NOT NULL,             -- starter | growth | premium
  package_price   INT NOT NULL,              -- cents
  
  business_name   TEXT NOT NULL,
  owner_name      TEXT,
  email           TEXT NOT NULL,
  phone           TEXT,
  
  onboard_status  TEXT DEFAULT 'pending',
  onboard_completed_at TIMESTAMPTZ,
  
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- OUTREACH: multi-touch sequences
-- ============================================================
CREATE TABLE outreach_sequences (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id     UUID REFERENCES prospects(id) ON DELETE CASCADE,
  
  channel         TEXT NOT NULL,             -- sms | email
  sequence_template TEXT NOT NULL,           -- which sequence variant
  
  status          TEXT NOT NULL DEFAULT 'active',
                  -- active | completed | unsubscribed | converted | paused
  
  current_step    SMALLINT DEFAULT 0,
  max_steps       SMALLINT NOT NULL,
  
  next_send_at    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE outreach_messages (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sequence_id     UUID REFERENCES outreach_sequences(id) ON DELETE CASCADE,
  prospect_id     UUID REFERENCES prospects(id) ON DELETE CASCADE,
  
  step_number     SMALLINT NOT NULL,
  channel         TEXT NOT NULL,
  direction       TEXT NOT NULL DEFAULT 'outbound',  -- outbound | inbound
  
  to_address      TEXT NOT NULL,             -- phone or email
  from_address    TEXT NOT NULL,
  subject         TEXT,                      -- email only
  body            TEXT NOT NULL,
  
  -- Delivery tracking
  provider_message_id TEXT,                  -- Twilio SID or Resend ID
  status          TEXT NOT NULL DEFAULT 'queued',
                  -- queued | sent | delivered | failed | opened | clicked | replied
  sent_at         TIMESTAMPTZ,
  delivered_at    TIMESTAMPTZ,
  opened_at       TIMESTAMPTZ,
  clicked_at      TIMESTAMPTZ,
  replied_at      TIMESTAMPTZ,
  
  -- Inbound response
  response_body   TEXT,
  
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_outreach_next_send ON outreach_sequences(next_send_at, status)
  WHERE status = 'active';
CREATE INDEX idx_outreach_messages_prospect ON outreach_messages(prospect_id);

-- ============================================================
-- LEAD EVENTS: actions taken on preview/production sites
-- ============================================================
CREATE TABLE lead_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id         UUID REFERENCES generated_sites(id),
  client_id       UUID REFERENCES clients(id),
  
  event_type      TEXT NOT NULL,
                  -- page_view | cta_click | form_submit | phone_click | preview_viewed
  visitor_id      TEXT,                      -- anonymous fingerprint
  
  page            TEXT,
  referrer        TEXT,
  utm_source      TEXT,
  utm_campaign    TEXT,
  
  metadata        JSONB,
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- INDEXES for common queries
-- ============================================================
CREATE INDEX idx_generated_sites_slug ON generated_sites(slug);
CREATE INDEX idx_lead_events_client ON lead_events(client_id, created_at DESC);
```

---

## PHASE 1: AGENT CREW ARCHITECTURE

### 1A. Crew Definition (`reliantai/agents/home_services_crew.py`)

```python
# reliantai/agents/home_services_crew.py
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from .tools import (
    GooglePlacesTool,
    PageSpeedTool,
    GBPScraperTool,
    SchemaValidatorTool,
    VercelDeployTool,
    TwilioSMSTool,
    ResendEmailTool,
)
from .llm import gemini_flash  # google/gemini-1.5-flash for speed-critical tasks
from .llm import gemini_pro    # google/gemini-1.5-pro for copy/synthesis tasks
import structlog

log = structlog.get_logger()


# ─── AGENT DEFINITIONS ──────────────────────────────────────────────

prospect_scout = Agent(
    role="ProspectScout",
    goal=(
        "Identify home service businesses with strong review ratings (4.0+, 10+ reviews) "
        "but weak or absent web presence in a target city and trade. "
        "Score each prospect by opportunity gap: higher score = better target."
    ),
    backstory=(
        "You are a data-driven business intelligence analyst specializing in local market gaps. "
        "You use Google Places API to find businesses, then assess their digital footprint. "
        "You think like a sales hunter: low-hanging fruit = high reviews, no website."
    ),
    tools=[GooglePlacesTool(), PageSpeedTool()],
    llm=gemini_flash,
    verbose=True,
    allow_delegation=False,
    max_iter=3,
)

business_researcher = Agent(
    role="BusinessResearcher",
    goal=(
        "Build a complete intelligence profile on a specific home service business: "
        "their best reviews, unique selling points, service areas, owner information, "
        "GBP completeness, social presence, and current website weaknesses."
    ),
    backstory=(
        "You are a marketing researcher who can extract the soul of a business from its digital footprint. "
        "You read reviews to find recurring themes, spot missed opportunities, "
        "and identify the emotional reasons customers love them. "
        "This data becomes the foundation for everything built on top of it."
    ),
    tools=[
        GooglePlacesTool(),
        GBPScraperTool(),
        ScrapeWebsiteTool(),
        SerperDevTool(),
        PageSpeedTool(),
    ],
    llm=gemini_pro,
    verbose=True,
    allow_delegation=False,
    max_iter=5,
)

competitor_analyst = Agent(
    role="CompetitorAnalyst",
    goal=(
        "Find the top 3-5 local competitors for a given business, "
        "analyze their digital strengths and weaknesses, "
        "and identify specific gaps our client can dominate: "
        "schema markup, AEO signals, GBP optimization, review response rate, speed."
    ),
    backstory=(
        "You are a competitive intelligence specialist. You see websites as battlefields. "
        "You are looking for what competitors are NOT doing — those gaps are your client's opportunity. "
        "You think in terms of search intent: what is a homeowner asking Google or ChatGPT "
        "when their furnace breaks at midnight, and who wins that moment?"
    ),
    tools=[GooglePlacesTool(), ScrapeWebsiteTool(), SerperDevTool(), PageSpeedTool()],
    llm=gemini_flash,
    verbose=True,
    allow_delegation=False,
    max_iter=5,
)

copy_agent = Agent(
    role="CopyAgent",
    goal=(
        "Using the business intelligence and competitor analysis, write all copy for a premium home service website: "
        "hero headline, subheadline, service descriptions, about section, trust signals, FAQ, "
        "meta titles, meta descriptions, schema.org JSON-LD, voice-search FAQ pairs, "
        "GBP post content, and the initial outreach SMS/email message. "
        "Every word must be specific to THIS business — zero generic filler."
    ),
    backstory=(
        "You are a direct-response copywriter trained on Ogilvy, Halbert, and Cialdini. "
        "You understand that a homeowner with a burst pipe is not buying a website — "
        "they are buying certainty that this contractor will show up, fix the problem, and not rip them off. "
        "You activate the RISK lever (loss aversion, safety) as the dominant frame, "
        "with STATUS (reviews, credentials) as the secondary proof structure. "
        "You write at a 7th-grade reading level. You never use the word 'solutions'."
    ),
    tools=[SerperDevTool()],
    llm=gemini_pro,
    verbose=True,
    allow_delegation=False,
    max_iter=3,
)

site_builder_agent = Agent(
    role="SiteBuilderAgent",
    goal=(
        "Select the appropriate site template for this trade, inject all generated content, "
        "build the Next.js static site, deploy to Vercel at the preview URL, "
        "and return the deployment URL and Lighthouse score."
    ),
    backstory=(
        "You are a senior full-stack engineer who builds premium local business websites. "
        "You select templates by trade aesthetic (HVAC = reliable blue/grey, Plumbing = trustworthy navy, "
        "Roofing = bold dark + copper accents, Electrical = sharp yellow/black, Painting = clean white + accent). "
        "You inject structured data, schema markup, and AEO signals as first-class requirements, not afterthoughts. "
        "A site that doesn't pass 90+ Lighthouse mobile is not done."
    ),
    tools=[VercelDeployTool(), SchemaValidatorTool()],
    llm=gemini_flash,
    verbose=True,
    allow_delegation=False,
    max_iter=3,
)

outreach_agent = Agent(
    role="OutreachAgent",
    goal=(
        "Send the personalized first-touch outreach message to the prospect. "
        "For SMS: under 160 chars, cite a specific review, mention the preview URL. "
        "For email: subject line under 9 words, body under 150 words, cite specific evidence from their profile. "
        "Record the message ID and schedule follow-up step 2 for 3 days out."
    ),
    backstory=(
        "You are a sales development rep who has sent thousands of cold messages. "
        "You know the first message must do three things in three seconds: "
        "prove you've done your homework, make a specific credible claim, offer a low-risk next step. "
        "You never pitch. You create curiosity and reduce friction."
    ),
    tools=[TwilioSMSTool(), ResendEmailTool()],
    llm=gemini_flash,
    verbose=True,
    allow_delegation=False,
    max_iter=2,
)


# ─── TASK DEFINITIONS ───────────────────────────────────────────────

def build_pipeline_tasks(prospect_data: dict) -> list[Task]:
    """Build the sequential task chain for a single prospect."""
    
    t_research = Task(
        description=f"""
        Research this home service business completely:
        
        Business: {prospect_data['business_name']}
        Place ID: {prospect_data['place_id']}
        Trade: {prospect_data['trade']}
        Location: {prospect_data['city']}, {prospect_data['state']}
        Phone: {prospect_data.get('phone', 'unknown')}
        Current website: {prospect_data.get('website_url', 'none')}
        
        Steps:
        1. Fetch full Google Places details (reviews, photos, categories, hours, Q&A)
        2. Extract top 5 recurring themes from reviews with representative quotes
        3. Score sentiment 0.0–1.0
        4. If website exists: run PageSpeed Insights (mobile), check SSL, check schema presence
        5. Check Facebook, Yelp, BBB presence
        6. Estimate years in business from review history
        
        Output: BusinessIntelligenceReport (structured JSON matching DB schema)
        """,
        agent=business_researcher,
        expected_output="JSON: BusinessIntelligenceReport with all fields populated",
    )
    
    t_competitors = Task(
        description=f"""
        Find and analyze the top 3-5 local competitors for:
        
        Business: {prospect_data['business_name']}
        Trade: {prospect_data['trade']}
        City: {prospect_data['city']}, {prospect_data['state']}
        
        Steps:
        1. Search Google Places for same trade in same city, by rating
        2. Exclude our target business
        3. For each competitor: scrape their website, run PageSpeed, check schema
        4. Identify gaps: no schema, poor mobile speed, no FAQ content, no AEO signals
        5. Extract their top organic keywords via Serper
        
        Output: CompetitorReport with gap_opportunities for each competitor
        """,
        agent=competitor_analyst,
        expected_output="JSON: CompetitorReport array with gaps identified",
        context=[t_research],
    )
    
    t_copy = Task(
        description=f"""
        Write all website copy AND outreach messages for:
        Business: {prospect_data['business_name']}
        Trade: {prospect_data['trade']}
        City: {prospect_data['city']}, {prospect_data['state']}
        
        Using the BusinessIntelligenceReport and CompetitorReport from previous tasks.
        
        REQUIRED OUTPUTS (all as structured JSON):
        
        1. HERO SECTION
           - headline: specific, outcome-oriented, < 12 words
           - subheadline: elaborates on primary proof, < 25 words  
           - cta_primary: "Get Your Free Quote" or trade-specific equivalent
           - hero_trust_bar: ["Licensed & Insured", "{X}-Star Google Reviews", "Serving {City} Since {Year}"]
        
        2. SERVICES SECTION (3–6 services)
           For each: title, short_description (2 sentences), icon_keyword, cta_text
        
        3. ABOUT SECTION
           - story: 80–120 words, uses owner name if known, references local community
           - trust_points: 3 specific bullets (certifications, years, guarantee)
        
        4. REVIEWS SHOWCASE
           - featured_reviews: top 3 review excerpts with first name + initial only
           - aggregate_line: "{N} homeowners in {City} give us {X} stars"
        
        5. FAQ SCHEMA (voice-search optimized)
           - 6 question/answer pairs
           - Questions must start with: "How do I...", "What does...", "Can you...", "How much...", "Do you...", "Why..."
           - Answers: conversational, 30–60 words, include business name naturally
        
        6. AEO ENTITY SIGNALS
           - entity_description: 2-sentence factual business description for knowledge graph
           - service_area_description: which neighborhoods/suburbs served
           - primary_service_query: the most common question a homeowner asks for this trade
        
        7. SCHEMA.ORG JSON-LD
           - LocalBusiness + trade-specific subtype
           - Include: name, address, phone, geo, openingHours, priceRange, aggregateRating, 
             sameAs (all found social/directory URLs), areaServed
        
        8. META TAGS
           - title: < 60 chars, includes city + trade keyword
           - description: < 155 chars, includes city, trade, review count, primary CTA word
        
        9. OUTREACH SMS (< 155 chars)
           - Must reference a specific review theme
           - Must include preview URL placeholder: {{PREVIEW_URL}}
           - Must feel human, not automated
        
        10. OUTREACH EMAIL
            - subject: < 9 words, specific, curiosity-opening
            - body: < 150 words, 3 paragraphs: proof they're good → gap they have → low-friction offer
            - ps_line: one extra hook or social proof
        
        PSYCHOLOGICAL FRAMEWORK:
        - Primary lever: RISK (homeowner fears wasting money on unreliable contractor)
        - Secondary lever: STATUS (neighbors trust them, Google reviews prove it)
        - Awareness stage: PROBLEM AWARE (they know they need a website, don't know how good it can be)
        - Zero use of: "solutions", "cutting-edge", "seamless", "leverage", "journey"
        """,
        agent=copy_agent,
        expected_output="JSON: SiteCopyPackage with all 10 sections",
        context=[t_research, t_competitors],
    )
    
    t_build = Task(
        description=f"""
        Build and deploy the preview site for:
        Business: {prospect_data['business_name']}
        Slug: {prospect_data['slug']}
        Trade: {prospect_data['trade']}
        
        Steps:
        1. Select template: trade → template_id mapping (see TEMPLATE_REGISTRY)
        2. Render the Next.js template with SiteCopyPackage content injected
        3. Validate Schema.org JSON-LD via Google Rich Results Test API
        4. Build: `next build && next export` → static output
        5. Deploy to Vercel via Deploy API → preview URL
        6. Run Lighthouse CI on the deployed URL (must score 90+ mobile)
        7. Return: preview_url, vercel_deployment_id, lighthouse_score
        
        TEMPLATE_REGISTRY:
        - hvac: hvac-reliable-blue
        - plumbing: plumbing-trustworthy-navy  
        - electrical: electrical-sharp-gold
        - roofing: roofing-bold-copper
        - painting: painting-clean-minimal
        - landscaping: landscaping-earthy-green
        
        FAIL if Lighthouse mobile < 90. Re-optimize images, reduce JS, then retry once.
        """,
        agent=site_builder_agent,
        expected_output="JSON: {preview_url, vercel_deployment_id, lighthouse_score, build_time_sec}",
        context=[t_copy],
    )
    
    t_outreach = Task(
        description=f"""
        Send first-touch outreach to:
        Business: {prospect_data['business_name']}
        Phone: {prospect_data.get('phone', 'none')}
        
        Using the outreach_sms and outreach_email from SiteCopyPackage.
        Using the preview_url from the site build output.
        
        Steps:
        1. Replace {{PREVIEW_URL}} in SMS/email with actual preview_url
        2. If phone available: send SMS via Twilio from ReliantAI number
        3. If email available: send via Resend from DouglasMitchell@reliantai.org
        4. Record Twilio SID / Resend message ID
        5. Write to outreach_messages table
        6. Schedule follow-up step 2 for 3 days from now
        
        Return: {sent_sms: bool, sms_sid: str, sent_email: bool, email_id: str}
        """,
        agent=outreach_agent,
        expected_output="JSON: {sent_sms, sms_sid, sent_email, email_id, follow_up_scheduled_at}",
        context=[t_copy, t_build],
    )
    
    return [t_research, t_competitors, t_copy, t_build, t_outreach]


def create_prospect_crew(prospect_data: dict) -> Crew:
    tasks = build_pipeline_tasks(prospect_data)
    return Crew(
        agents=[
            business_researcher,
            competitor_analyst,
            copy_agent,
            site_builder_agent,
            outreach_agent,
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=True,                       # CrewAI memory for intra-crew context
        embedder={
            "provider": "google",
            "config": {"model": "models/text-embedding-004"},
        },
        max_rpm=10,                        # Gemini rate limit guard
    )
```

### 1B. Celery Task Wrappers (`reliantai/tasks/prospect_tasks.py`)

```python
# reliantai/tasks/prospect_tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from ..agents.home_services_crew import create_prospect_crew
from ..db import get_db_session
from ..models import ResearchJob, Prospect, GeneratedSite
import structlog
from datetime import datetime

log = get_task_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    soft_time_limit=900,    # 15 min soft kill
    time_limit=1200,        # 20 min hard kill
    queue="agents",
)
def run_prospect_pipeline(self, prospect_id: str):
    """
    Full agent pipeline for one prospect.
    Runs: research → competitors → copy → build → outreach
    """
    with get_db_session() as db:
        prospect = db.query(Prospect).filter_by(id=prospect_id).first()
        if not prospect:
            log.error("prospect_not_found", prospect_id=prospect_id)
            return {"error": "prospect_not_found"}
        
        job = db.query(ResearchJob).filter_by(
            prospect_id=prospect_id, 
            celery_task_id=self.request.id
        ).first()
        
        if not job:
            job = ResearchJob(
                prospect_id=prospect_id,
                celery_task_id=self.request.id,
                status="running",
                step="business_research",
                started_at=datetime.utcnow(),
            )
            db.add(job)
            db.commit()
        
        prospect_data = {
            "place_id": prospect.place_id,
            "business_name": prospect.business_name,
            "trade": prospect.trade,
            "city": prospect.city,
            "state": prospect.state,
            "phone": prospect.phone,
            "address": prospect.address,
            "website_url": prospect.website_url,
            "slug": prospect.place_id[:30].lower().replace(" ", "-"),
        }
    
    try:
        crew = create_prospect_crew(prospect_data)
        result = crew.kickoff()
        
        with get_db_session() as db:
            job = db.query(ResearchJob).filter_by(
                celery_task_id=self.request.id
            ).first()
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            prospect.status = "outreach_sent"
            prospect.updated_at = datetime.utcnow()
            db.commit()
        
        log.info("pipeline_completed", prospect_id=prospect_id, result=str(result)[:200])
        return {"status": "completed", "prospect_id": prospect_id}
    
    except Exception as exc:
        with get_db_session() as db:
            job = db.query(ResearchJob).filter_by(
                celery_task_id=self.request.id
            ).first()
            if job:
                job.status = "failed"
                job.error_message = str(exc)[:500]
                job.retry_count = self.request.retries
                db.commit()
        
        log.error("pipeline_failed", 
                  prospect_id=prospect_id, 
                  error=str(exc),
                  retry_count=self.request.retries)
        raise


@shared_task(
    bind=True,
    queue="outreach",
    soft_time_limit=120,
)
def send_follow_up_message(self, sequence_id: str, step_number: int):
    """
    Execute a scheduled follow-up step.
    Called by Celery Beat at the scheduled time.
    """
    from ..services.outreach_service import OutreachService
    OutreachService.execute_step(sequence_id=sequence_id, step=step_number)


@shared_task(queue="outreach")
def process_inbound_response(phone: str, body: str, provider_message_id: str):
    """
    Handle inbound SMS replies from Twilio webhook.
    Routes to: unsubscribe | hot_lead | auto_response
    """
    from ..services.outreach_service import OutreachService
    OutreachService.handle_inbound(
        phone=phone, 
        body=body, 
        message_id=provider_message_id
    )
```

---

## PHASE 2: TOOL IMPLEMENTATIONS

### 2A. Google Places Tool (`reliantai/agents/tools/google_places.py`)

```python
# reliantai/agents/tools/google_places.py
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
import httpx
import os
from typing import Optional


class PlacesSearchInput(BaseModel):
    query: str = Field(description="Search query, e.g. 'HVAC repair Houston Texas'")
    location: Optional[str] = Field(default=None, description="lat,lng e.g. '29.7604,-95.3698'")
    radius: int = Field(default=16000, description="Search radius in meters (max 50000)")
    min_rating: float = Field(default=4.0)
    min_reviews: int = Field(default=10)
    max_results: int = Field(default=20)


class GooglePlacesTool(BaseTool):
    name: str = "google_places_search"
    description: str = (
        "Search Google Places for local businesses. Returns business details "
        "including name, address, phone, rating, review count, website URL, and place_id. "
        "Use for finding prospects and competitors."
    )
    
    def _run(self, query: str, location: str = None, radius: int = 16000,
             min_rating: float = 4.0, min_reviews: int = 10, max_results: int = 20) -> str:
        
        api_key = os.environ["GOOGLE_PLACES_API_KEY"]
        
        # Text Search endpoint
        params = {
            "query": query,
            "key": api_key,
            "fields": "place_id,name,formatted_address,formatted_phone_number,"
                      "rating,user_ratings_total,website,geometry,opening_hours,"
                      "photos,business_status",
        }
        if location:
            params["location"] = location
            params["radius"] = radius
        
        results = []
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params=params
            )
            data = resp.json()
        
        for place in data.get("results", [])[:max_results]:
            rating = place.get("rating", 0)
            reviews = place.get("user_ratings_total", 0)
            
            if rating < min_rating or reviews < min_reviews:
                continue
            
            # Score opportunity gap: high reviews + no/weak website = high score
            website = place.get("website", "")
            website_score = 0 if not website else 50  # full analysis done by researcher
            
            results.append({
                "place_id": place["place_id"],
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "phone": place.get("formatted_phone_number"),
                "rating": rating,
                "review_count": reviews,
                "website": website,
                "website_score": website_score,
                "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                "lng": place.get("geometry", {}).get("location", {}).get("lng"),
                "has_photos": len(place.get("photos", [])) > 0,
            })
        
        return str(results)
    
    def _get_place_details(self, place_id: str) -> dict:
        """Fetch full place details including reviews."""
        api_key = os.environ["GOOGLE_PLACES_API_KEY"]
        
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={
                    "place_id": place_id,
                    "key": api_key,
                    "fields": "reviews,name,rating,user_ratings_total,formatted_phone_number,"
                              "website,opening_hours,address_components,geometry,"
                              "editorial_summary,price_level",
                    "reviews_sort": "most_relevant",
                }
            )
        return resp.json().get("result", {})
```

### 2B. Vercel Deploy Tool (`reliantai/agents/tools/vercel_deploy.py`)

```python
# reliantai/agents/tools/vercel_deploy.py
from crewai_tools import BaseTool
import httpx
import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path


class VercelDeployTool(BaseTool):
    name: str = "vercel_deploy_site"
    description: str = (
        "Deploy a Next.js static site to Vercel. "
        "Accepts a slug, template_id, and site_content JSON. "
        "Returns preview_url, deployment_id, and Lighthouse score."
    )
    
    TEMPLATES_DIR = Path("/opt/reliantai/site-templates")
    
    def _run(self, slug: str, template_id: str, site_content: dict) -> str:
        """
        1. Copy template to temp dir
        2. Inject content into template data files
        3. Build with next build
        4. Deploy via Vercel CLI
        5. Run Lighthouse on deployed URL
        """
        import json
        
        template_path = self.TEMPLATES_DIR / template_id
        if not template_path.exists():
            return json.dumps({"error": f"Template {template_id} not found"})
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            site_dir = Path(tmp_dir) / slug
            shutil.copytree(str(template_path), str(site_dir))
            
            # Write content to data file that template reads
            content_file = site_dir / "src" / "data" / "site-content.json"
            content_file.parent.mkdir(parents=True, exist_ok=True)
            content_file.write_text(json.dumps(site_content, indent=2))
            
            # Build
            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(site_dir),
                capture_output=True,
                text=True,
                timeout=300,
            )
            if build_result.returncode != 0:
                return json.dumps({
                    "error": "build_failed",
                    "stderr": build_result.stderr[-2000:]
                })
            
            # Deploy via Vercel CLI
            deploy_result = subprocess.run(
                ["vercel", "deploy", "--prod", "--yes",
                 "--name", f"client-{slug}",
                 "--token", os.environ["VERCEL_TOKEN"]],
                cwd=str(site_dir),
                capture_output=True,
                text=True,
                timeout=180,
            )
            if deploy_result.returncode != 0:
                return json.dumps({
                    "error": "deploy_failed",
                    "stderr": deploy_result.stderr[-2000:]
                })
            
            deployment_url = deploy_result.stdout.strip().split("\n")[-1]
            
            # Run Lighthouse
            lh_result = subprocess.run(
                ["lighthouse", deployment_url,
                 "--output=json", "--quiet",
                 "--chrome-flags='--headless --no-sandbox'",
                 "--only-categories=performance,seo,accessibility"],
                capture_output=True, text=True, timeout=120,
            )
            
            lighthouse_score = 0
            if lh_result.returncode == 0:
                try:
                    lh_data = json.loads(lh_result.stdout)
                    lighthouse_score = int(
                        lh_data["categories"]["performance"]["score"] * 100
                    )
                except Exception:
                    pass
            
            return json.dumps({
                "preview_url": deployment_url,
                "vercel_deployment_id": deployment_url.split("/")[-1],
                "lighthouse_score": lighthouse_score,
                "build_success": True,
            })
```

---

## PHASE 3: SITE TEMPLATE SYSTEM

### 3A. Template Architecture

Each template is a standalone Next.js 15 project (static export) that reads from `src/data/site-content.json`. The SiteBuilderAgent injects this file and rebuilds.

```
site-templates/
├── hvac-reliable-blue/          # Next.js 15 project
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Reads site-content.json for meta
│   │   │   ├── page.tsx         # Assembles sections
│   │   │   └── globals.css      # Trade-specific design tokens
│   │   ├── components/
│   │   │   ├── Hero.tsx
│   │   │   ├── Services.tsx
│   │   │   ├── About.tsx
│   │   │   ├── Reviews.tsx
│   │   │   ├── FAQ.tsx
│   │   │   ├── ContactBar.tsx
│   │   │   └── Footer.tsx
│   │   └── data/
│   │       └── site-content.json  ← INJECTED BY AGENT
│   ├── next.config.ts            # output: 'export'
│   └── package.json
├── plumbing-trustworthy-navy/
├── electrical-sharp-gold/
├── roofing-bold-copper/
├── painting-clean-minimal/
└── landscaping-earthy-green/
```

### 3B. Template Content Contract (`site-content.json` schema)

```typescript
// types/SiteContent.ts — used by ALL templates
export interface SiteContent {
  business: {
    name: string;
    trade: string;
    phone: string;
    address: string;
    city: string;
    state: string;
    zip: string;
    founded_year?: number;
    owner_name?: string;
    license_number?: string;
    google_rating: number;
    review_count: number;
    google_maps_url: string;
  };
  
  hero: {
    headline: string;
    subheadline: string;
    cta_primary: string;
    cta_secondary?: string;
    trust_bar: string[];            // ["Licensed & Insured", "4.9-Star Google Reviews", ...]
    background_tone: "light" | "dark";
  };
  
  services: Array<{
    title: string;
    short_description: string;
    icon_keyword: string;
    cta_text: string;
    is_emergency?: boolean;
  }>;
  
  about: {
    story: string;
    trust_points: string[];
    photo_placeholder: boolean;
  };
  
  reviews: {
    featured: Array<{
      text: string;
      author_display: string;   // "John S." — never full last name
      rating: number;
      date_relative: string;    // "3 months ago"
    }>;
    aggregate_line: string;
  };
  
  faq: Array<{
    question: string;
    answer: string;
  }>;
  
  seo: {
    title: string;
    description: string;
    canonical_url: string;
    og_title: string;
    og_description: string;
  };
  
  schema_org: object;             // Full JSON-LD LocalBusiness object
  
  aeo: {
    entity_description: string;
    primary_service_query: string;
    service_area_description: string;
    knowledge_panel_description: string;
  };
  
  theme: {
    template_id: string;
    primary_color: string;
    accent_color: string;
    font_display: string;
    font_body: string;
  };
}
```

### 3C. Hero Component — Framer Motion + Trade Design (`components/Hero.tsx`)

```tsx
// site-templates/hvac-reliable-blue/src/components/Hero.tsx
"use client";
import { motion } from "framer-motion";
import { Phone, Shield, Star } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface HeroProps {
  content: SiteContent["hero"];
  business: SiteContent["business"];
}

export function Hero({ content, business }: HeroProps) {
  return (
    <section className="relative min-h-[85vh] flex items-center overflow-hidden
                        bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900">
      
      {/* Subtle grid overlay */}
      <div className="absolute inset-0 opacity-10"
           style={{ backgroundImage: "url('/grid.svg')", backgroundSize: "48px 48px" }} />
      
      <div className="relative z-10 container mx-auto px-6 py-24 max-w-6xl">
        <div className="max-w-3xl">
          
          {/* Trust signal above headline */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center gap-2 mb-6"
          >
            <div className="flex">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
              ))}
            </div>
            <span className="text-amber-400 text-sm font-medium">
              {business.review_count} reviews · {business.google_rating} stars on Google
            </span>
          </motion.div>
          
          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-white leading-[1.08]
                       tracking-tight mb-6"
          >
            {content.headline}
          </motion.h1>
          
          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-slate-300 leading-relaxed mb-10 max-w-xl"
          >
            {content.subheadline}
          </motion.p>
          
          {/* CTA Group */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 mb-12"
          >
            <a
              href={`tel:${business.phone}`}
              className="inline-flex items-center justify-center gap-3 px-8 py-4
                         bg-blue-500 hover:bg-blue-400 text-white font-semibold text-lg
                         rounded-xl transition-all duration-200 hover:scale-[1.02]
                         shadow-lg shadow-blue-500/25"
            >
              <Phone className="w-5 h-5" />
              {content.cta_primary}
            </a>
            {content.cta_secondary && (
              <a href="#contact"
                 className="inline-flex items-center justify-center gap-2 px-8 py-4
                            border border-slate-600 hover:border-slate-400
                            text-slate-200 hover:text-white font-medium text-lg
                            rounded-xl transition-all duration-200">
                {content.cta_secondary}
              </a>
            )}
          </motion.div>
          
          {/* Trust Bar */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="flex flex-wrap gap-6"
          >
            {content.trust_bar.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-slate-400 text-sm">
                <Shield className="w-4 h-4 text-blue-400 flex-shrink-0" />
                <span>{item}</span>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
```

---

## PHASE 4: SEO + GEO + AEO IMPLEMENTATION

### 4A. Schema.org JSON-LD Generator (`reliantai/agents/tools/schema_builder.py`)

```python
# reliantai/agents/tools/schema_builder.py
"""
Generates full Schema.org JSON-LD for LocalBusiness.
This is the core AEO/GEO signal: Google, ChatGPT, Perplexity, 
Bing Copilot all read this to understand and cite local businesses.
"""

TRADE_TO_SCHEMA_TYPE = {
    "hvac": "HVACBusiness",
    "plumbing": "Plumber",
    "electrical": "Electrician",
    "roofing": "RoofingContractor",
    "painting": "HousePainter",
    "landscaping": "LandscapingBusiness",
    "general_contractor": "GeneralContractor",
}


def build_local_business_schema(
    business_data: dict,
    review_data: dict,
    competitor_keywords: list[str],
) -> dict:
    """
    Returns a complete JSON-LD schema object.
    Designed to maximize:
    - Google rich results (LocalBusiness, Review, FAQ)
    - AEO (AI engine citation): entity clarity, service disambiguation
    - GEO (geographic signals): areaServed, address precision
    """
    trade = business_data.get("trade", "general_contractor")
    schema_type = TRADE_TO_SCHEMA_TYPE.get(trade, "LocalBusiness")
    
    base = {
        "@context": "https://schema.org",
        "@type": [schema_type, "LocalBusiness"],
        "@id": f"https://{business_data['slug']}.clients.reliantai.org/#business",
        "name": business_data["business_name"],
        "description": business_data["aeo"]["entity_description"],
        "url": f"https://{business_data['slug']}.clients.reliantai.org",
        "telephone": business_data["phone"],
        "image": f"https://{business_data['slug']}.clients.reliantai.org/og-image.jpg",
        "logo": f"https://{business_data['slug']}.clients.reliantai.org/logo.png",
        "priceRange": "$$",
        
        "address": {
            "@type": "PostalAddress",
            "streetAddress": business_data.get("address", ""),
            "addressLocality": business_data["city"],
            "addressRegion": business_data["state"],
            "postalCode": business_data.get("zip", ""),
            "addressCountry": "US",
        },
        
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": business_data.get("lat"),
            "longitude": business_data.get("lng"),
        },
        
        "areaServed": [
            {"@type": "City", "name": business_data["city"]},
            # Add suburbs from service_areas
            *[
                {"@type": "Place", "name": area}
                for area in business_data.get("service_areas", [])
            ],
        ],
        
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": str(business_data["google_rating"]),
            "reviewCount": str(business_data["review_count"]),
            "bestRating": "5",
            "worstRating": "1",
        },
        
        "review": [
            {
                "@type": "Review",
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": str(r["rating"]),
                },
                "author": {"@type": "Person", "name": r["author_display"]},
                "reviewBody": r["text"],
                "datePublished": r.get("date_iso", ""),
            }
            for r in review_data.get("featured", [])[:3]
        ],
        
        # AEO: sameAs links help AI engines merge entity knowledge
        "sameAs": [
            url for url in [
                business_data.get("google_maps_url"),
                business_data.get("facebook_url"),
                business_data.get("yelp_url"),
                business_data.get("bbb_url"),
            ] if url
        ],
        
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": f"{business_data['business_name']} Services",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "name": service["title"],
                        "description": service["short_description"],
                    }
                }
                for service in business_data.get("services", [])
            ],
        },
        
        # FAQ schema: critical for voice search + AI citations
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"],
                },
            }
            for faq in business_data.get("faq", [])
        ],
    }
    
    # Add founding year if known
    if business_data.get("years_in_business"):
        year = 2025 - business_data["years_in_business"]
        base["foundingDate"] = str(year)
    
    return base
```

### 4B. AEO Strategy — Ranking in AI Engines

AI Answer Engine Optimization is the differentiation that competitors lack. Every generated site includes:

**1. Entity Disambiguation Block** (injected in `<head>` as JSON-LD)
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{Business Name}",
  "description": "{2-sentence factual description with city + trade + differentiator}",
  "knowsAbout": ["{trade} repair", "{trade} installation", "emergency {trade} service", "{city} {trade}"],
  "serviceArea": "{city}, {state} and surrounding areas",
  "slogan": "{hero subheadline repurposed as brand statement}"
}
```

**2. Speakable Schema** (for voice assistants)
```json
{
  "@type": "WebPage",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".hero-headline", ".emergency-cta", ".aggregate-rating"]
  }
}
```

**3. FAQ Content Rules for AI Citation**
Every FAQ answer must:
- Name the business in the first sentence
- Be factually checkable (no claims that can't be verified)
- Include the city name
- Be 40-70 words (optimal for featured snippet length)
- Answer the literal question asked, then add one credibility signal

**4. GBP Optimization Checklist** (automated via agent, verified post-deployment)
- All 9 business attributes filled
- Primary category + 3 secondary categories
- Service menu fully populated
- Q&A section seeded with 6 FAQs (same as website FAQ)
- Photos: logo, interior, team, 3 project photos minimum
- Posts: weekly via PostAgent (separate scheduled task)

---

## PHASE 5: OUTREACH + FOLLOW-UP PIPELINE

### 5A. Follow-Up Sequence (`reliantai/services/outreach_service.py`)

```python
# reliantai/services/outreach_service.py
"""
Multi-touch, multi-channel follow-up orchestration.
All personalization variables resolved at send time against live DB data.
"""
from datetime import datetime, timedelta
from ..db import get_db_session
from ..models import OutreachSequence, OutreachMessage, Prospect, GeneratedSite
from .sms_service import SMSService
from .email_service import EmailService
import structlog

log = structlog.get_logger()

# ─── SEQUENCE TEMPLATES ────────────────────────────────────────────

SMS_SEQUENCE = [
    # Step 0: Initial (sent by OutreachAgent immediately after site build)
    None,  # handled by agent
    
    # Step 1: Day 3 — different angle, add a new detail
    {
        "delay_days": 3,
        "template": (
            "Hey {owner_first_name}, wanted to follow up re: {business_name}. "
            "Added your {review_count} Google reviews to the preview at {preview_url}. "
            "Takes 30 sec to look. Worth it?"
        ),
    },
    
    # Step 2: Day 7 — value add, low commitment
    {
        "delay_days": 7,
        "template": (
            "{business_name} is showing up on Google Maps — "
            "but not when people say \"Hey Siri, find an {trade} near me.\" "
            "I can change that. Free look: {preview_url}"
        ),
    },
    
    # Step 3: Day 14 — final touch, scarcity signal
    {
        "delay_days": 14,
        "template": (
            "Last message. Taking on one more {trade} client in {city} this month. "
            "Your site ({preview_url}) is ready if you want it. Otherwise I'll offer it to someone else."
        ),
    },
]

EMAIL_SEQUENCE = [
    # Step 0: Initial (sent by OutreachAgent)
    None,
    
    # Step 1: Day 3 — educational angle
    {
        "delay_days": 3,
        "subject": "Why {business_name} is invisible to AI search",
        "body": """Hi {owner_first_name},

Quick follow-up.

You have {review_count} Google reviews averaging {google_rating} stars. That's genuinely strong — most of your competitors don't come close.

The problem: when someone asks ChatGPT or Siri "who's the best {trade} in {city}?" you don't exist. Because AI tools read websites, not just Google listings.

I built {business_name} a site that fixes that. Took me about 4 hours to research you, write everything specific to your business, and build it. Preview here: {preview_url}

Happy to walk you through it on a quick call if you want.

— Douglas
ReliantAI""",
    },
    
    # Step 2: Day 10 — social proof angle
    {
        "delay_days": 10,
        "subject": "What {competitor_name} is doing that you aren't",
        "body": """Hi {owner_first_name},

I've been looking at {trade} businesses in {city} this week.

{competitor_name} ranks above you on Google even though they have fewer reviews. Their secret: structured data and a mobile site that loads in under 2 seconds.

Yours could too. Everything is already built: {preview_url}

Worth 30 seconds?

— Douglas""",
    },
    
    # Step 3: Day 18 — final, direct
    {
        "delay_days": 18,
        "subject": "Closing the {business_name} file",
        "body": """Hi {owner_first_name},

I'm moving on from this outreach, but wanted to send one last note.

The site I built for you ({preview_url}) will stay live for another 30 days. After that I'll repurpose the template for someone else in {city}.

If the timing ever works, you know where to find me.

Either way — {review_count} reviews at {google_rating} stars is something to be proud of. Good luck.

— Douglas
DouglasMitchell@reliantai.org""",
    },
]


class OutreachService:
    
    @staticmethod
    def start_sequence(prospect_id: str, channel: str = "both"):
        """Initialize outreach sequences for a prospect post-site-build."""
        with get_db_session() as db:
            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            site = db.query(GeneratedSite).filter_by(prospect_id=prospect_id).first()
            
            if not prospect or not site:
                log.error("missing_data_for_sequence", prospect_id=prospect_id)
                return
            
            if channel in ("sms", "both") and prospect.phone:
                seq = OutreachSequence(
                    prospect_id=prospect_id,
                    channel="sms",
                    sequence_template="home_services_v1",
                    max_steps=len([s for s in SMS_SEQUENCE if s is not None]),
                    current_step=1,  # step 0 already sent by agent
                    next_send_at=datetime.utcnow() + timedelta(days=3),
                    status="active",
                )
                db.add(seq)
            
            if channel in ("email", "both"):
                email = prospect.email  # populated from research or GBP
                if email:
                    seq = OutreachSequence(
                        prospect_id=prospect_id,
                        channel="email",
                        sequence_template="home_services_v1",
                        max_steps=len([s for s in EMAIL_SEQUENCE if s is not None]),
                        current_step=1,
                        next_send_at=datetime.utcnow() + timedelta(days=3),
                        status="active",
                    )
                    db.add(seq)
            
            db.commit()
    
    @staticmethod
    def resolve_template(template: str, prospect: "Prospect", site: "GeneratedSite",
                         competitors: list) -> str:
        """Replace all template variables with actual values."""
        competitor_name = competitors[0]["name"] if competitors else "a competitor"
        owner_name = prospect.business_intelligence.owner_name or "there"
        owner_first = owner_name.split()[0] if owner_name != "there" else "there"
        
        return template.format(
            owner_first_name=owner_first,
            business_name=prospect.business_name,
            trade=prospect.trade,
            city=prospect.city,
            review_count=prospect.review_count,
            google_rating=prospect.google_rating,
            preview_url=site.preview_url,
            competitor_name=competitor_name,
        )
    
    @staticmethod
    def handle_inbound(phone: str, body: str, message_id: str):
        """
        Route inbound SMS replies.
        'STOP' | 'UNSUBSCRIBE' → mark unsubscribed
        Positive intent → flag as hot_lead, notify Douglas
        """
        body_lower = body.lower().strip()
        
        stop_words = {"stop", "unsubscribe", "quit", "cancel", "end"}
        if any(word in body_lower for word in stop_words):
            OutreachService._handle_unsubscribe(phone)
            return
        
        # Flag as interested — escalate to human
        OutreachService._flag_hot_lead(phone, body)
    
    @staticmethod
    def _flag_hot_lead(phone: str, body: str):
        """Send notification to Douglas via SMS when a prospect replies positively."""
        SMSService.send(
            to=os.environ["OWNER_PHONE"],
            body=f"HOT LEAD: {phone} replied: '{body[:120]}'"
        )
```

---

## PHASE 6: API LAYER

### 6A. FastAPI Router (`reliantai/api/v2/prospects.py`)

```python
# reliantai/api/v2/prospects.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from ..tasks.prospect_tasks import run_prospect_pipeline
from ..services.prospect_service import ProspectService
from ..db import get_db_session
import structlog

router = APIRouter(prefix="/api/v2/prospects", tags=["prospects"])
security = HTTPBearer()
log = structlog.get_logger()


class ScanRequest(BaseModel):
    trade: str      # hvac | plumbing | electrical | roofing | painting | landscaping
    city: str
    state: str
    radius_miles: int = 10
    max_prospects: int = 50
    min_rating: float = 4.0
    min_reviews: int = 10


class PipelineRequest(BaseModel):
    prospect_id: str
    priority: str = "normal"  # normal | high


@router.post("/scan")
async def scan_for_prospects(request: ScanRequest, token=Depends(security)):
    """
    Trigger a Google Places scan for new prospects.
    Returns immediately; prospects are saved to DB.
    """
    prospects = await ProspectService.scan(
        trade=request.trade,
        city=request.city,
        state=request.state,
        radius_miles=request.radius_miles,
        max_results=request.max_prospects,
        min_rating=request.min_rating,
        min_reviews=request.min_reviews,
    )
    return {"scanned": len(prospects), "new": sum(1 for p in prospects if p["is_new"])}


@router.post("/{prospect_id}/pipeline")
async def start_pipeline(prospect_id: str, request: PipelineRequest,
                          token=Depends(security)):
    """
    Launch the full agent pipeline for a prospect.
    Queues to Celery. Returns task_id for polling.
    """
    queue = "agents_high" if request.priority == "high" else "agents"
    task = run_prospect_pipeline.apply_async(
        args=[prospect_id],
        queue=queue,
    )
    return {"task_id": task.id, "status": "queued"}


@router.get("/{prospect_id}/status")
async def get_pipeline_status(prospect_id: str, token=Depends(security)):
    """Poll pipeline status. Polled by reliantai.org dashboard."""
    with get_db_session() as db:
        from ..models import ResearchJob
        job = db.query(ResearchJob).filter_by(
            prospect_id=prospect_id
        ).order_by(ResearchJob.created_at.desc()).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="No pipeline job found")
        
        return {
            "status": job.status,
            "step": job.step,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error": job.error_message,
        }


@router.get("/")
async def list_prospects(
    status: str = None,
    trade: str = None,
    city: str = None,
    page: int = 1,
    page_size: int = 50,
    token=Depends(security),
):
    """List prospects with filters. Used by internal dashboard."""
    with get_db_session() as db:
        from ..models import Prospect
        q = db.query(Prospect)
        if status:
            q = q.filter(Prospect.status == status)
        if trade:
            q = q.filter(Prospect.trade == trade)
        if city:
            q = q.filter(Prospect.city.ilike(f"%{city}%"))
        
        total = q.count()
        prospects = q.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "results": [p.to_dict() for p in prospects],
        }
```

### 6B. Stripe Webhook → Site Provisioning (`reliantai/api/v2/webhooks.py`)

```python
# reliantai/api/v2/webhooks.py
from fastapi import APIRouter, Request, HTTPException
import stripe
import os
import structlog
from ..tasks.provisioning_tasks import provision_client_site

router = APIRouter(prefix="/api/v2/webhooks", tags=["webhooks"])
log = structlog.get_logger()


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ["STRIPE_WEBHOOK_SECRET"]
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        prospect_id = session["metadata"].get("prospect_id")
        package = session["metadata"].get("package")  # starter | growth | premium
        
        if not prospect_id:
            log.warning("stripe_session_missing_prospect_id", session_id=session["id"])
            return {"status": "ok"}
        
        # Queue site provisioning
        provision_client_site.apply_async(
            args=[prospect_id, package, session["customer"], session["subscription"]],
            queue="provisioning",
        )
        log.info("client_purchase_received", 
                 prospect_id=prospect_id, package=package)
    
    elif event["type"] == "customer.subscription.deleted":
        # Suspend client site
        from ..services.client_service import ClientService
        ClientService.suspend_by_stripe_sub(event["data"]["object"]["id"])
    
    return {"status": "ok"}


@router.post("/twilio/inbound-sms")
async def twilio_inbound_sms(request: Request):
    """Twilio sends POST to this URL when a prospect replies to our SMS."""
    form = await request.form()
    
    from ..tasks.prospect_tasks import process_inbound_response
    process_inbound_response.apply_async(
        args=[
            form.get("From"),
            form.get("Body"),
            form.get("MessageSid"),
        ],
        queue="outreach",
    )
    
    # Twilio expects empty TwiML response to not auto-reply
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )
```

---

## PHASE 7: RELIANTAI MARKETING SITE UPGRADES

### 7A. Interactive Demo Widget (`reliantai-website/src/components/LivePreviewDemo.tsx`)

The single highest-leverage addition to the marketing site. A prospect enters a business name. The widget hits the API, shows a 10-second "researching" animation, then reveals a mock preview of their potential site.

```tsx
// reliantai-website/src/components/LivePreviewDemo.tsx
"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Loader2, ExternalLink } from "lucide-react";

type DemoState = "idle" | "searching" | "building" | "ready" | "error";

export function LivePreviewDemo() {
  const [state, setState] = useState<DemoState>("idle");
  const [businessName, setBusinessName] = useState("");
  const [city, setCity] = useState("");
  const [previewData, setPreviewData] = useState<any>(null);
  
  const steps = [
    { label: "Scanning Google reviews...", duration: 2000 },
    { label: "Analyzing 47 competitors...", duration: 2500 },
    { label: "Writing your copy...", duration: 2000 },
    { label: "Building your site...", duration: 3000 },
  ];
  const [currentStep, setCurrentStep] = useState(0);
  
  async function handleSearch() {
    if (!businessName.trim() || !city.trim()) return;
    
    setState("searching");
    
    // Run through visual steps
    for (let i = 0; i < steps.length; i++) {
      setCurrentStep(i);
      await new Promise(r => setTimeout(r, steps[i].duration));
    }
    
    setState("building");
    
    // Hit the demo API (returns cached/simulated data for marketing site)
    try {
      const res = await fetch("/api/demo-preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ business_name: businessName, city }),
      });
      
      if (!res.ok) throw new Error("API error");
      const data = await res.json();
      setPreviewData(data);
      setState("ready");
    } catch {
      setState("error");
    }
  }
  
  return (
    <div className="max-w-2xl mx-auto">
      
      {state === "idle" && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/5 border border-white/10 rounded-2xl p-8"
        >
          <p className="text-slate-400 text-sm mb-6 text-center">
            See what your site could look like — in 10 seconds
          </p>
          
          <div className="flex flex-col gap-3 mb-4">
            <input
              type="text"
              placeholder="Your business name"
              value={businessName}
              onChange={e => setBusinessName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/20
                         text-white placeholder:text-slate-500 focus:outline-none
                         focus:border-blue-400 transition-colors"
            />
            <input
              type="text"
              placeholder="City, State"
              value={city}
              onChange={e => setCity(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/20
                         text-white placeholder:text-slate-500 focus:outline-none
                         focus:border-blue-400 transition-colors"
              onKeyDown={e => e.key === "Enter" && handleSearch()}
            />
          </div>
          
          <button
            onClick={handleSearch}
            disabled={!businessName.trim() || !city.trim()}
            className="w-full py-3 rounded-xl bg-blue-500 hover:bg-blue-400
                       text-white font-semibold transition-all duration-200
                       disabled:opacity-40 disabled:cursor-not-allowed
                       flex items-center justify-center gap-2"
          >
            <Search className="w-4 h-4" />
            Build My Preview Site
          </button>
        </motion.div>
      )}
      
      {(state === "searching" || state === "building") && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center"
        >
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-4" />
          
          <div className="space-y-3">
            {steps.map((step, i) => (
              <div key={i}
                   className={`flex items-center gap-3 text-sm transition-colors
                               ${i < currentStep ? "text-green-400" :
                                 i === currentStep ? "text-white" : "text-slate-600"}`}>
                <div className={`w-2 h-2 rounded-full flex-shrink-0
                                 ${i < currentStep ? "bg-green-400" :
                                   i === currentStep ? "bg-blue-400 animate-pulse" :
                                   "bg-slate-700"}`} />
                {step.label}
              </div>
            ))}
          </div>
        </motion.div>
      )}
      
      {state === "ready" && previewData && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden"
        >
          {/* Mock site preview iframe or card */}
          <div className="p-6 border-b border-white/10">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-white font-semibold text-lg mb-1">
                  {previewData.business_name}
                </h3>
                <p className="text-slate-400 text-sm">
                  {previewData.google_rating} stars · {previewData.review_count} Google reviews
                </p>
              </div>
              <a
                href={previewData.preview_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 rounded-lg
                           bg-blue-500 hover:bg-blue-400 text-white text-sm font-medium
                           transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                View Full Preview
              </a>
            </div>
          </div>
          
          <div className="p-6">
            <p className="text-slate-300 text-sm mb-4">
              {previewData.hero_headline}
            </p>
            
            <div className="flex flex-wrap gap-2">
              {previewData.trust_signals?.map((sig: string, i: number) => (
                <span key={i}
                      className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-300
                                 text-xs border border-blue-500/20">
                  {sig}
                </span>
              ))}
            </div>
          </div>
          
          <div className="px-6 pb-6">
            <a href="/pricing"
               className="block w-full py-3 rounded-xl bg-white text-slate-900
                          font-semibold text-center hover:bg-slate-100 transition-colors">
              Get This Site — Starting at $497
            </a>
          </div>
        </motion.div>
      )}
    </div>
  );
}
```

### 7B. Pricing Page Architecture

```
Packages (price psychology: anchor → decoy → target):

STARTER — $497 one-time
- Premium 5-page site (Home, Services, About, Reviews, Contact)
- Mobile-first, 90+ Lighthouse
- Schema.org + FAQ schema
- 1 GBP optimization pass
- Delivered in 48 hours
- 30-day preview → your domain after purchase

GROWTH — $297/month  ← TARGET PACKAGE (decoy above makes this feel cheap)
- Everything in Starter
- Ongoing AEO updates (as AI engines evolve)
- Monthly GBP posts (4/month)
- Monthly citation building (10 new directories/month)
- Rank tracking for 10 local keywords
- Monthly report: calls, clicks, rankings

PREMIUM — $697/month  ← ANCHOR (makes Growth feel like the obvious choice)
- Everything in Growth
- Weekly GBP posts
- Automated review request sequences (Twilio)
- Competitor monitoring alerts
- Quarterly site redesign
- Priority support (4hr response)
- Custom domain included
```

---

## PHASE 8: SECURITY + INFRASTRUCTURE

### 8A. Environment Variables Contract

```bash
# ─── CORE ────────────────────────────────────────────
DATABASE_URL=postgresql://reliantai:${DB_PASS}@localhost:5432/reliantai
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<64-byte random hex>

# ─── GOOGLE ──────────────────────────────────────────
GOOGLE_PLACES_API_KEY=<key>          # Places Text Search + Details
GOOGLE_PAGESPEED_API_KEY=<key>       # PageSpeed Insights
GOOGLE_SEARCH_CONSOLE_CREDENTIALS=<json path>

# ─── AI ──────────────────────────────────────────────
GOOGLE_AI_API_KEY=<key>              # Gemini 1.5 Flash + Pro
SERPER_API_KEY=<key>                 # Web search for agents

# ─── COMMS ───────────────────────────────────────────
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_FROM_NUMBER=<+1XXXXXXXXXX>
OWNER_PHONE=<Douglas's number for hot-lead alerts>

RESEND_API_KEY=<key>
FROM_EMAIL=DouglasMitchell@reliantai.org

# ─── PAYMENTS ────────────────────────────────────────
STRIPE_SECRET_KEY=<sk_live_...>
STRIPE_WEBHOOK_SECRET=<whsec_...>
STRIPE_STARTER_PRICE_ID=<price_...>
STRIPE_GROWTH_PRICE_ID=<price_...>
STRIPE_PREMIUM_PRICE_ID=<price_...>

# ─── DEPLOYMENT ──────────────────────────────────────
VERCEL_TOKEN=<token>
VERCEL_TEAM_ID=<team_id>
VERCEL_ORG_ID=<org_id>

# ─── INTERNAL API AUTH ───────────────────────────────
API_SECRET_KEY=<32-byte random hex>   # shared between website + platform
```

### 8B. Docker Compose (`reliantai/docker-compose.yml`)

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped
  
  celery_agents:
    build:
      context: .
      dockerfile: Dockerfile.celery
    command: celery -A reliantai.celery_app worker -Q agents,agents_high
             --concurrency 2 --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY}
      - SERPER_API_KEY=${SERPER_API_KEY}
      - VERCEL_TOKEN=${VERCEL_TOKEN}
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
  
  celery_outreach:
    build:
      context: .
      dockerfile: Dockerfile.celery
    command: celery -A reliantai.celery_app worker -Q outreach,provisioning
             --concurrency 4 --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - RESEND_API_KEY=${RESEND_API_KEY}
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
  
  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile.celery
    command: celery -A reliantai.celery_app beat --loglevel=info
             --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
  
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: reliantai
      POSTGRES_USER: reliantai
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U reliantai"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
  
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASS} --maxmemory 256mb
             --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASS}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 8C. Security Checklist

**API Layer**
- All internal API endpoints require `Authorization: Bearer {API_SECRET_KEY}` header
- Stripe webhook verified via `stripe.Webhook.construct_event` — not just checking event type
- Twilio inbound SMS verified via X-Twilio-Signature header before processing
- Rate limiting: 100 req/min per IP on public endpoints, 1000 req/min on authenticated
- All DB queries use parameterized statements (SQLAlchemy ORM enforces this)

**Agent Outputs**
- All agent-generated copy is sanitized before DB write: strip HTML tags, validate field lengths
- Schema.org JSON-LD validated via Google API before injection into live pages
- Site builds run in isolated temp directories; no shell injection possible via content fields

**Secrets**
- All secrets in environment variables; never in code or config files committed to git
- `.env` files in `.gitignore` at root level; GitHub secret scanning enabled
- Rotate STRIPE_WEBHOOK_SECRET, TWILIO_AUTH_TOKEN, and API_SECRET_KEY quarterly

**GDPR / CAN-SPAM / TCPA Compliance**
- Every SMS sequence checks `opt_out` status before sending
- Opt-out processed within 1 message (no delay)
- `STOP` keyword detection is keyword-based AND regex-based (catches "stop it", "no more", etc.)
- All outreach messages include business identity disclosure: "— Douglas, ReliantAI"
- Email footer includes physical address + unsubscribe link
- Inbound opt-outs recorded in `outreach_sequences.status = 'unsubscribed'` and never reversed

---

## PHASE 9: EXECUTION SEQUENCE

### Sprint Map (working solo, 2-4 hours/day)

```
WEEK 1: Foundation
  Day 1-2: Postgres migrations + SQLAlchemy models
  Day 3:   Celery + Redis setup, health checks pass
  Day 4-5: GooglePlacesTool + ProspectService (scan + save)
  Day 6-7: Test scan for Houston HVAC, verify DB writes

WEEK 2: Agent Core
  Day 1-3: BusinessResearcher agent + unit tests
  Day 4-5: CompetitorAnalyst agent + unit tests
  Day 6-7: CopyAgent prompt refinement (iterate on 5 real prospects)

WEEK 3: Site Factory
  Day 1-2: hvac-reliable-blue template (production quality)
  Day 3:   SiteContent injection + Next.js static export
  Day 4-5: VercelDeployTool + Lighthouse CI verification
  Day 6-7: End-to-end test: scan → research → copy → build → preview URL live

WEEK 4: Outreach Pipeline
  Day 1-2: TwilioSMSTool + OutreachAgent
  Day 3:   Follow-up sequence scheduler (Celery Beat)
  Day 4:   Inbound SMS routing + hot-lead notifications
  Day 5:   Stripe webhook → provisioning task
  Day 6-7: Full E2E test with real Houston prospect

WEEK 5: Marketing Site
  Day 1-2: LivePreviewDemo widget
  Day 3:   Pricing page (3-package architecture)
  Day 4:   FAQ schema + AEO signals on reliantai.org itself
  Day 5-7: Integration: website → API → database → response

WEEK 6: Remaining 5 Templates + Polish
  Day 1-2: plumbing-trustworthy-navy + electrical-sharp-gold
  Day 3-4: roofing-bold-copper + painting-clean-minimal
  Day 5:   landscaping-earthy-green
  Day 6-7: Dashboard page for Douglas (prospect list + pipeline status)

WEEK 7: Production Hardening
  Day 1:   Load test Celery workers with 20 concurrent pipelines
  Day 2:   Lighthouse audit all 6 templates (target 95+ desktop, 90+ mobile)
  Day 3:   Security review: TCPA compliance, rate limits, secret rotation
  Day 4:   Monitoring: Sentry errors, Celery Flower, Postgres slow query log
  Day 5-7: First real outreach campaign: 20 prospects in Houston HVAC
```

---

## FAILURE MODE REGISTER

| Component | Failure Mode | Blast Radius | Mitigation |
|---|---|---|---|
| Google Places API | Rate limit (1 QPS) | Scan pauses | Exponential backoff + cached results |
| Gemini API | Rate limit / timeout | Agent task fails | Retry 3x with 60s backoff |
| Vercel Deploy API | Build failure | Site not created | Log error, notify, manual trigger |
| Twilio | Invalid/landline number | SMS not sent | Validate E.164 before send, fallback to email |
| Celery worker restart | In-flight task lost | 1 prospect pipeline | `acks_late=True` + `reject_on_worker_lost=True` |
| CopyAgent hallucination | Wrong business name in copy | Wrong site delivered | Post-generation validator: assert business_name appears in hero |
| Stripe webhook replay | Double-provisioning | 2x site created | Idempotency key on provision task: `prospect_id + session_id` |
| TCPA violation | Texting after opt-out | Legal exposure | Pre-send check against `opt_out` table, real-time not cached |

---

## CONNECTORS + SKILLS ACTIVATED FOR THIS BUILD

**Connected MCP Servers in use:**
- **Stripe MCP** — price ID lookup, subscription management, webhook config
- **Vercel MCP** — project creation, domain assignment, deployment monitoring
- **Notion MCP** — prospect pipeline kanban (optional CRM layer)
- **Zapier MCP** — fallback outreach automation if Twilio is down

**Skills loaded for this plan:**
- `agentic-ops-architect` — system decomposition, failure mode analysis
- `multi-agent-orchestration` — CrewAI crew design + task dependency chains
- `revenue-architecture-generator` — psychological pricing + copy framework
- `elite-full-stack-web-guide` — template design standards
- `strategic-execution-advisor` — sprint sequencing
- `freight-ar-domain-expert` — NOT activated (wrong domain, kept isolated)
- `autonomous-prospect-engine` — Google Places scan logic
- `threat-modeler` — TCPA/security checklist

---

*Plan generated April 2026. LangGraph migration path: after Week 7, the CrewAI crew can be ported to LangGraph StateGraph with minimal agent prompt changes. The main gain is conditional edge routing — e.g., if a prospect already has a 90+ scoring website, skip to outreach_only lane instead of running the full build pipeline.*
