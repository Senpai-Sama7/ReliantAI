# ReliantAI Platform — Implementation Checklist

**Generated from:**
- `claude-code-implementation-prompt.md` (Phases 1-6)
- `synthesized-architecture (1).md` (Critical flaws & ADRs)

**How to use this checklist:**
- [ ] Unchecked = Not started
- [-] In progress
- [x] Complete (with commit hash or date)

---

## Phase 0: Critical Architecture Fixes (Pre-Implementation)

These are the 7 critical flaws from `synthesized-architecture (1).md` that must be verified before proceeding:

### FLAW 1: No Per-Site Builds (ISR Architecture)
- [ ] Verified: Sites render via Next.js ISR from DB content (not per-site builds)
- [ ] Verified: `reliantai-client-sites` uses dynamic `[slug]` route
- [ ] Verified: Deploy = `INSERT INTO generated_sites` + revalidate (not `npm build`)

### FLAW 2: Slug Generation (Not From place_id)
- [ ] Verified: `generate_slug(business_name, city)` uses regex + uuid4()[:4]
- [ ] Verified: Never uses `place_id` for slug generation
- [ ] Test: `'John\'s HVAC' + 'Houston'` → `'johns-hvac-houston-a3f1'`

### FLAW 3: Celery Beat (No Django Scheduler)
- [ ] Verified: `celery_app.py` uses `beat_schedule` (not django_celery_beat)
- [ ] Verified: `process_scheduled_followups()` runs every 5 minutes via crontab
- [ ] Verified: No Django dependency in Celery configuration

### FLAW 4: Preview Domain (Separate Subdomain)
- [ ] Verified: `preview.reliantai.org/{slug}` (NOT `reliantai.org/preview/{slug}`)
- [ ] Verified: `reliantai.org` remains Vite SPA
- [ ] Verified: Client sites deployed to separate Vercel project

### FLAW 5: Synchronous Tools (Async/Sync Fix)
- [ ] Verified: All tool `_run()` methods are synchronous
- [ ] Verified: Uses `httpx.Client` (not `AsyncClient`) in tools
- [ ] Verified: No `async def _run()` declarations in any tool

### FLAW 6: Remove Dead Code (prospect_scout)
- [ ] Verified: `prospect_scout` agent removed from `home_services_crew.py`
- [ ] Verified: Scan happens at API layer (`ProspectService.scan()`), not in Crew

### FLAW 7: Followup State Machine (Advance current_step)
- [ ] Verified: `process_scheduled_followups()` advances `current_step` atomically
- [ ] Verified: `next_send_at` updated after each send
- [ ] Verified: Uses `with_for_update(skip_locked=True)` to prevent double-firing

---

## Phase 1: Infrastructure + Schema (Week 1)

**Goal:** Database, models, FastAPI skeleton, Docker, Celery all running

### Step 1: Database Migration
- [ ] File: `reliantai/db/migrations/001_platform.sql` created
- [ ] All 7 tables defined:
  - [ ] `prospects` (with UUID PK, trade, city, status)
  - [ ] `research_jobs` (linked to prospects, CASCADE delete)
  - [ ] `business_intelligence` (instagram_url, gbp_review_response_rate, etc.)
  - [ ] `competitor_intelligence` (linked to prospects)
  - [ ] `generated_sites` (client_id → SET NULL)
  - [ ] `outreach_sequences` (with `next_send_at` partial index WHERE status='active')
  - [ ] `outreach_messages` (history)
  - [ ] `lead_events` (audit trail)
- [ ] Indexes created:
  - [ ] `idx_prospects_trade_city`
  - [ ] `idx_prospects_status`
  - [ ] `idx_outreach_next_send` (partial)
- [ ] FK cascade rules correct:
  - [ ] prospects → CASCADE on research_jobs, business_intelligence, competitor_intelligence, outreach_sequences
  - [ ] generated_sites.client_id → SET NULL

### Step 2: SQLAlchemy ORM Models
- [ ] File: `reliantai/db/models.py` created
- [ ] Uses `declarative_base()` (not SQLAlchemy 2.x DeclarativeBase)
- [ ] UUID primary keys as `String` with `default=lambda: str(uuid.uuid4())`
- [ ] All `relationship()` calls with correct `back_populates`
- [ ] `cascade="all, delete-orphan"` where applicable
- [ ] `BusinessIntelligence` includes all fields from spec:
  - [ ] `instagram_url`
  - [ ] `gbp_review_response_rate`
  - [ ] `site_last_updated`
  - [ ] `site_mobile_friendly`
  - [ ] `owner_title`
- [ ] `OutreachSequence` supports `with_for_update()`
- [ ] Each model has `to_dict()` method

### Step 3: DB Session Factory
- [ ] File: `reliantai/db/__init__.py` created
- [ ] `get_db_session()` as context manager using `@contextmanager`
- [ ] Connection pool: `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`
- [ ] `DATABASE_URL` from environment only (no hardcoded values)
- [ ] Configurable via env vars:
  - [ ] `DB_POOL_SIZE`
  - [ ] `DB_POOL_MAX_OVERFLOW`
  - [ ] `DB_POOL_TIMEOUT`

### Step 4: Celery App (No Django)
- [ ] File: `reliantai/celery_app.py` created
- [ ] Uses Redis as broker and result backend
- [ ] `beat_schedule` configured:
  - [ ] `process_scheduled_followups`: every 5 min (300s)
  - [ ] `generate_weekly_gbp_posts`: Monday 9am UTC (crontab)
- [ ] Settings:
  - [ ] `task_acks_late=True`
  - [ ] `task_reject_on_worker_lost=True`
  - [ ] `worker_prefetch_multiplier=1`
- [ ] `autodiscover_tasks(["reliantai.tasks"])`

### Step 5: FastAPI Skeleton
- [ ] File: `reliantai/main.py` created
- [ ] CORS configured for `reliantai.org` and `preview.reliantai.org`
- [ ] `/health` endpoint returns `{"status": "ok", "db": bool, "redis": bool}`
- [ ] `verify_api_key` dependency with HTTPBearer + constant-time compare
- [ ] Placeholder routers included:
  - [ ] `api/v2/prospects`
  - [ ] `api/v2/webhooks`
  - [ ] `api/v2/generated-sites`
- [ ] Startup event verifies DB connection and logs migration drift

### Step 6: Docker Compose
- [ ] File: `docker-compose.yml` created
- [ ] Services defined:
  - [ ] `api` (FastAPI)
  - [ ] `celery_agents` (2 workers, queues: agents, agents_high)
  - [ ] `celery_outreach` (4 workers, queues: outreach, provisioning)
  - [ ] `celery_beat` (scheduler)
  - [ ] `postgres` (PostgreSQL 16-alpine, healthcheck pg_isready)
  - [ ] `redis` (Redis 7-alpine, maxmemory 256mb, allkeys-lru)
- [ ] All services: `restart: unless-stopped`
- [ ] `api` depends_on postgres and redis with `condition: service_healthy`
- [ ] Volume for postgres data persistence

### Step 7: Alembic Setup
- [ ] File: `alembic.ini` configured
- [ ] File: `alembic/env.py` created
- [ ] Target metadata from `reliantai.db.models Base`
- [ ] `DATABASE_URL` from environment variable
- [ ] Autogenerate support enabled

### Step 8: Smoke Test
- [ ] File: `tests/test_models.py` created
- [ ] Test creates full chain:
  - [ ] `Prospect` → `ResearchJob` → `BusinessIntelligence` → `GeneratedSite` → `OutreachSequence`
- [ ] Reads back with all relationships loaded
- [ ] Assertions:
  - [ ] `prospect.business_intel is not None`
  - [ ] `prospect.generated_site is not None`
- [ ] **PHASE GATE:** Test passes before proceeding to Phase 2

### Phase 1 Exit Criteria
- [ ] `pytest tests/test_models.py` passes
- [ ] `docker-compose up --build` → all services healthy
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok","db":true,"redis":true}`

---

## Phase 2: Agent Crew (Week 2)

**Goal:** All 5 agents, tools, SiteRegistrationService, Celery pipeline working

### Step 1: LLM Factory
- [ ] File: `reliantai/agents/llm.py` created
- [ ] `gemini_pro = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.5, max_output_tokens=4096)`
- [ ] `gemini_flash = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3, max_output_tokens=2048)`
- [ ] Both initialized from `GOOGLE_AI_API_KEY` env var

### Step 2: GooglePlacesTool
- [ ] File: `reliantai/agents/tools/google_places.py` created
- [ ] Inherits `BaseTool` from `crewai_tools`
- [ ] `_run()` is **SYNCHRONOUS** (uses `httpx.Client`, not `AsyncClient`)
- [ ] Supports both `query=` (Text Search) and `place_id=` (Details) in single method
- [ ] Details fields requested:
  - [ ] `reviews`, `name`, `rating`, `user_ratings_total`
  - [ ] `formatted_phone_number`, `website`, `opening_hours`
  - [ ] `address_components`, `geometry`, `photos`
  - [ ] `business_status`, `editorial_summary`
- [ ] `reviews_sort: most_relevant`
- [ ] `_format_details()` extracts top 5 reviews with author, rating, text, time
- [ ] Exponential backoff on HTTP 429: 1s, 2s, 4s, 8s (max 3 retries)
- [ ] Returns `str(dict)` (not JSON) — CrewAI receives string output

### Step 3: PageSpeedTool
- [ ] File: `reliantai/agents/tools/pagespeed.py` created
- [ ] `_run(url: str)` → **SYNCHRONOUS**
- [ ] Calls PageSpeed Insights API with `strategy=mobile`
- [ ] Returns: `{score: int, lcp: float, fid: float, cls: float, has_ssl: bool}`
- [ ] Returns `{"score": 0, "error": "no_url"}` if url is None (never crashes)
- [ ] Timeout: 20s

### Step 4: GBPScraperTool
- [ ] File: `reliantai/agents/tools/gbp_scraper.py` created
- [ ] `_run(place_id: str)` → **SYNCHRONOUS**
- [ ] Calls Places Details API for photos, editorial_summary, opening_hours
- [ ] `_estimate_completeness()` scores 0-100 based on populated fields
- [ ] `_estimate_review_response_rate()` from reviews list
- [ ] Does NOT scrape Google Maps HTML (uses API only)

### Step 5: SchemaValidatorTool
- [ ] File: `reliantai/agents/tools/schema_validator.py` created
- [ ] `validate_schema_org(schema: dict) → bool`
- [ ] Calls Google Rich Results Test API (POST to searchconsole.googleapis.com)
- [ ] Falls back to local structural validation if API fails
- [ ] Non-fatal: returns `False` with warning log on failure (does not raise)

### Step 6: Schema Builder
- [ ] File: `reliantai/agents/tools/schema_builder.py` created
- [ ] `build_local_business_schema(business_data, review_data, competitor_keywords) → dict`
- [ ] `TRADE_TO_SCHEMA_TYPE` mapping:
  - [ ] `hvac` → `HVACBusiness`
  - [ ] `plumbing` → `Plumber`
  - [ ] `electrical` → `Electrician`
  - [ ] `roofing` → `RoofingContractor`
  - [ ] `painting` → `HousePainter`
  - [ ] `landscaping` → `LandscapingBusiness`
- [ ] `@type` is a LIST: `[schema_type, "LocalBusiness"]`
- [ ] Includes all required fields: @id, name, description, url, telephone, image, logo, priceRange, address, geo, areaServed, aggregateRating, review, sameAs, hasOfferCatalog, mainEntity (FAQ)
- [ ] `foundingDate` only if `years_in_business` known

### Step 7: SiteRegistrationService
- [ ] File: `reliantai/services/site_registration_service.py` created
- [ ] Exact implementation from synthesized-architecture.md Component 1
- [ ] `generate_slug()` uses regex + uuid4()[:4] suffix
- [ ] `_get_theme()` returns all 6 trade themes with colors/fonts
- [ ] `_revalidate_preview_cache()` catches ALL exceptions (non-fatal)
- [ ] `register()` is idempotent: if `GeneratedSite` exists for prospect_id, update it

### Step 8: Twilio SMS Tool
- [ ] File: `reliantai/agents/tools/twilio_sms.py` created
- [ ] `_run(to: str, body: str)` → **SYNCHRONOUS**
- [ ] Validates E.164 format: `re.match(r'^\+1\d{10}$', to)`
- [ ] Returns `{"sid": str, "status": str}` on success
- [ ] Returns `{"error": "invalid_number"}` on format fail (does not raise)
- [ ] Logs to structlog with to_number (last 4 digits only), body_length, status

### Step 9: Resend Email Tool
- [ ] File: `reliantai/agents/tools/resend_email.py` created
- [ ] `_run(to: str, subject: str, body: str)` → **SYNCHRONOUS**
- [ ] Plain text email (no HTML templating yet)
- [ ] Returns `{"id": str, "status": "sent"}` on success
- [ ] Returns `{"error": str}` on failure (does not raise)

### Step 10: Agent Crew
- [ ] File: `reliantai/agents/home_services_crew.py` created
- [ ] 5 agents defined:
  - [ ] `business_researcher` (gemini_pro)
  - [ ] `competitor_analyst` (gemini_flash)
  - [ ] `copy_agent` (gemini_pro)
  - [ ] `site_builder_agent` (gemini_flash — calls SiteRegistrationService)
  - [ ] `outreach_agent` (gemini_flash)
- [ ] `prospect_scout` is NOT defined here (scan at API layer)
- [ ] Agent backstories from Plan B (evocative)
- [ ] Task descriptions from Plan A (mechanically precise)
- [ ] `site_builder_agent` task calls `SiteRegistrationService.register()` (not VercelDeployTool)
- [ ] Crew configuration:
  - [ ] `Process.sequential`
  - [ ] `memory=True`
  - [ ] `embedder=google/text-embedding-004`
  - [ ] `max_rpm=10`
- [ ] `create_prospect_crew(prospect_data: dict) → Crew` function

### Step 11: Celery Task Wrapper
- [ ] File: `reliantai/tasks/prospect_tasks.py` created
- [ ] `run_prospect_pipeline`:
  - [ ] `bind=True`
  - [ ] `autoretry_for=(Exception,)`
  - [ ] `retry_kwargs`: max_retries=3, countdown=60
  - [ ] `soft_time_limit=900`, `time_limit=1200`
  - [ ] `queue="agents"`
  - [ ] Creates `ResearchJob` record BEFORE `crew.kickoff()`
  - [ ] Updates `ResearchJob.step` at each agent transition
  - [ ] On completion: sets `prospect.status="outreach_sent"`
  - [ ] On failure: sets `job.status="failed"`, `job.error_message=str(exc)[:500]`
- [ ] `process_inbound_response`:
  - [ ] Stop words: "stop", "unsubscribe", "quit", "cancel", "end", "no more", "opt out"
- [ ] `process_scheduled_followups`:
  - [ ] Uses `with_for_update(skip_locked=True)`
  - [ ] Advances `current_step` AND `next_send_at` atomically

### Step 12: Prospects API Router
- [ ] File: `reliantai/api/v2/prospects.py` created
- [ ] Exact implementation from synthesized-architecture.md Component 2
- [ ] Routes:
  - [ ] `POST /` (inbound, deduplicates by place_id)
  - [ ] `POST /scan` (outbound batch)
  - [ ] `GET /{prospect_id}/status`
  - [ ] `GET /` (list with filters: status, trade, city, page, page_size)
- [ ] All routes require `verify_api_key` dependency

### Step 13: Integration Test
- [ ] File: `tests/test_pipeline_integration.py` created
- [ ] Mocks `GooglePlacesTool` to return fixture data for "Apex HVAC Houston TX"
- [ ] Mocks Twilio + Resend to return success responses
- [ ] Runs `create_prospect_crew(fixture_data).kickoff()`
- [ ] Assertions:
  - [ ] `GeneratedSite` created in DB
  - [ ] `status="preview_live"`
  - [ ] `preview_url` contains "preview.reliantai.org"
  - [ ] `OutreachMessage` created with `channel="sms"`, `status="sent"`

### Phase 2 Exit Criteria
- [ ] `pytest tests/ -x -v` passes (unit + integration with mocks)
- [ ] Pipeline runs manually against one real Houston HVAC prospect
- [ ] DB shows: `prospect.status == "outreach_sent"`, `GeneratedSite.preview_url` is set
- [ ] `preview.reliantai.org/{slug}` returns 404 (expected — Next.js not built yet)

---

## Phase 3: Client Sites (Next.js) (Week 3)

**Goal:** ISR dynamic routes, hvac template, revalidation, preview banner

### Step 1: Project Scaffold
- [ ] Command: `npx create-next-app@latest reliantai-client-sites --typescript --tailwind --app --no-src-dir --import-alias "@/*"`
- [ ] Install dependencies: `npm install framer-motion lucide-react`
- [ ] File: `reliantai-client-sites/next.config.ts`
  - [ ] `output` is NOT 'export' (uses ISR, not static export)
  - [ ] `images.domains` includes `['preview.reliantai.org', 'api.reliantai.org']`
  - [ ] env: `PLATFORM_API_URL` and `PLATFORM_API_KEY`

### Step 2: SiteContent TypeScript Interface
- [ ] File: `reliantai-client-sites/types/SiteContent.ts` created
- [ ] Exact interface from synthesized-architecture.md Component 4
- [ ] All sub-types exported:
  - [ ] `BusinessInfo`
  - [ ] `HeroSection`
  - [ ] `ServiceItem`
  - [ ] `AboutSection`
  - [ ] `ReviewsSection`
  - [ ] `FAQItem`
  - [ ] `SEOMeta`
  - [ ] `AEOSignals`
  - [ ] `ThemeConfig`

### Step 3: API Fetcher
- [ ] File: `reliantai-client-sites/lib/api.ts` created
- [ ] `getSiteContent(slug: string): Promise<SiteContent | null>`
- [ ] Fetches from `PLATFORM_API_URL/api/v2/generated-sites/{slug}`
- [ ] Authorization: Bearer `PLATFORM_API_KEY`
- [ ] `next: { revalidate: 3600 }` on fetch call
- [ ] Returns `null` on any non-200 response (does not throw)
- [ ] `getTemplate(templateId: string)` for dynamic imports

### Step 4: Dynamic Route Page
- [ ] File: `reliantai-client-sites/app/[slug]/page.tsx` created
- [ ] `export const revalidate = 3600`
- [ ] `getSiteContent` call — if null, return `notFound()`
- [ ] Dynamic template import via `getTemplate(content.site_config.template_id)`
- [ ] `generateMetadata`:
  - [ ] title from `seo.title`
  - [ ] description from `seo.description`
  - [ ] JSON-LD injected via `other: { 'script:ld+json': JSON.stringify(content.schema_org) }`
- [ ] `isPreview = content.status === "preview_live"`
- [ ] Renders `<Template content={content} />` then `PreviewBanner` if `isPreview`

### Step 5: Revalidation API Route
- [ ] File: `reliantai-client-sites/app/api/revalidate/route.ts` created
- [ ] POST handler only
- [ ] Verifies Authorization header against `REVALIDATE_SECRET` using `crypto.timingSafeEqual`
- [ ] Calls `revalidatePath('/[slug]', 'page')` and `revalidateTag(slug)`
- [ ] Returns `{revalidated: true, slug}` on success
- [ ] Returns 401 on auth failure (no detail in body for security)

### Step 6: Preview Banner Component
- [ ] File: `reliantai-client-sites/components/PreviewBanner.tsx` created
- [ ] Fixed bottom bar, z-50, dark slate background
- [ ] Left text: "This is your free preview site. It expires in 30 days." + Lighthouse score + city
- [ ] Right CTAs:
  - [ ] "Get This Site — $497" (blue filled)
  - [ ] "Growth Plan — $297/mo" (outlined)
- [ ] Links use `href={`/checkout?slug=${slug}&package=starter`}` and `growth`
- [ ] Mobile: stack vertically, CTAs full width

### Step 7: hvac-reliable-blue Template
- [ ] File: `reliantai-client-sites/templates/hvac-reliable-blue/index.tsx` created
- [ ] Default export: `HvacTemplate({ content: SiteContent })`
- [ ] Import and compose all section components
- [ ] Sections in order:
  1. [ ] ContactBar (sticky top)
  2. [ ] Hero
  3. [ ] Services
  4. [ ] About
  5. [ ] Reviews
  6. [ ] FAQ
  7. [ ] Footer
- [ ] Theme tokens:
  - [ ] Primary: #1d4ed8
  - [ ] Accent: #93c5fd
  - [ ] Fonts: Outfit (display) + Inter (body)

### Step 8: Hero Section
- [ ] File: `reliantai-client-sites/templates/hvac-reliable-blue/sections/Hero.tsx`
- [ ] Exact implementation from synthesized-architecture.md Component 3C
- [ ] Framer Motion: opacity+y fade-in on headline, subheadline, CTA group, trust bar
- [ ] Star rating bar above headline using `content.business.review_count` and `google_rating`
- [ ] Primary CTA: `<a href="tel:{phone}">` with Phone icon
- [ ] Trust bar: map `content.hero.trust_bar` with Shield icon
- [ ] Background: gradient from slate-900 via blue-950 to slate-900 + subtle grid overlay

### Step 9: Remaining Section Components
- [ ] File: `reliantai-client-sites/templates/hvac-reliable-blue/sections/Services.tsx`
  - [ ] 3-column grid on desktop, 1-column mobile
  - [ ] Each card: icon + title + description + CTA link
- [ ] File: `reliantai-client-sites/templates/hvac-reliable-blue/sections/About.tsx`
  - [ ] 2-column (text left, trust bullets right)
  - [ ] Owner story paragraph
  - [ ] 3 trust_points as checkmark list
- [ ] File: `reliantai-client-sites/templates/hvac-reliable-blue/sections/Reviews.tsx`
  - [ ] 3-column grid of review cards
  - [ ] aggregate_line below
  - [ ] Google logo/stars attribution
- [ ] File: `reliantai-client-sites/templates/hvac-reliable-blue/sections/FAQ.tsx`
  - [ ] Accordion (useState for open/close, no external library)
  - [ ] Schema-friendly (question in `<dt>`, answer in `<dd>`)
- [ ] File: `reliantai-client-sites/templates/hvac-reliable-blue/sections/Footer.tsx`
  - [ ] Business name, phone, address, copyright
  - [ ] Social links from `schema_org.sameAs`
- [ ] File: `reliantai-client-sites/templates/hvac-reliable-blue/sections/ContactBar.tsx`
  - [ ] Sticky top, compact
  - [ ] Phone number + "Call Now" text

### Step 10: Generated Sites API Endpoint
- [ ] File: `reliantai/api/v2/generated_sites.py` (ADD to existing platform)
- [ ] `GET /api/v2/generated-sites/{slug}`
- [ ] Returns full `GeneratedSite.site_content` JSON merged with business data
- [ ] No auth required (public endpoint)
- [ ] Redis caching with `SITE_CACHE_TTL` (3600s default)

### Phase 3 Exit Criteria
- [ ] `npm run build` succeeds in `reliantai-client-sites/`
- [ ] `npm run test:e2e` passes (Playwright)
- [ ] Run pipeline → DB write → visit `preview.reliantai.org/{slug}` → renders
- [ ] 3 real sites live with 90+ Lighthouse score

---

## Phase 4: Remaining Templates + Outreach (Week 4)

**Goal:** All 6 templates, outreach scheduler, Stripe webhooks

### Templates
- [ ] `plumbing-trustworthy-navy` template
  - [ ] Primary: #1e3a5f, Accent: #60a5fa
  - [ ] Fonts: Sora (display) + Inter (body)
  - [ ] All 7 sections
- [ ] `electrical-sharp-gold` template
  - [ ] Primary: #1a1a1a, Accent: #fbbf24
  - [ ] Fonts: Outfit + Inter
- [ ] `roofing-bold-copper` template
  - [ ] Primary: #292524, Accent: #c2713a
  - [ ] Fonts: Sora + Inter
- [ ] `painting-clean-minimal` template
  - [ ] Primary: #f8fafc, Accent: #3b82f6
  - [ ] Fonts: Playfair Display + Inter
- [ ] `landscaping-earthy-green` template
  - [ ] Primary: #14532d, Accent: #86efac
  - [ ] Fonts: Outfit + Inter

### Outreach Scheduler
- [ ] `process_scheduled_followups()` implemented with state machine
- [ ] `SEQUENCE_STEP_DELAYS` config (e.g., {1: 3, 2: 7, 3: 14} days)
- [ ] On completion: `seq.status = "completed"`
- [ ] On next step: queue `send_follow_up_message` with `seq.current_step + 1`

### Stripe Webhooks
- [ ] `POST /api/v2/webhooks/stripe` endpoint
- [ ] Signature verification using `STRIPE_WEBHOOK_SECRET`
- [ ] `checkout.session.completed` handler
- [ ] `provision_client_site` task (async, idempotent)
- [ ] Custom domain assignment via Vercel API
- [ ] Idempotency key: `f"{prospect_id}:{stripe_session_id}"`

### Phase 4 Exit Criteria
- [ ] All 6 templates pass 90+ mobile Lighthouse
- [ ] Follow-up sequence fires on schedule (every 5 min)
- [ ] Stripe webhook provisions custom domain

---

## Phase 5: Marketing Integration (Week 5)

**Goal:** Website integration, pricing, demo widgets

### Website Forms
- [ ] QuickPreviewForm on `reliantai.org` homepage
- [ ] LivePreviewDemo widget (animated demo for above-the-fold)
- [ ] Form submits to `POST /api/v2/prospects`
- [ ] Returns preview URL in < 3 seconds (async)

### Pricing Page
- [ ] 3-tier pricing with decoy psychology:
  - [ ] Starter: $497 (one-time)
  - [ ] Growth: $297/mo (target)
  - [ ] Premium: $697/mo (anchor)
- [ ] Loss Calculator component (existing, wired to real data)

### SEO
- [ ] Schema.org on `reliantai.org`:
  - [ ] Service
  - [ ] Organization
  - [ ] FAQPage

### Phase 5 Exit Criteria
- [ ] Inbound form → pipeline → preview URL returned in < 3 seconds
- [ ] Pricing page converts (test with beta users)

---

## Phase 6: Production Hardening (Week 6)

**Goal:** Load testing, security audit, monitoring, first campaign

### Load Testing
- [ ] 10 concurrent pipelines
- [ ] Celery concurrency 2 (watch Gemini rate limits)
- [ ] Response times < 200ms p95

### Security Audit
- [ ] Twilio signature verification
- [ ] Stripe signature verification
- [ ] Rate limiting (100 req/min per IP, 1000 per API key)
- [ ] TCPA opt-out handling verified
- [ ] No PII in logs (phone last 4 only)

### Monitoring
- [ ] Sentry DSN in all services
- [ ] Celery Flower dashboard
- [ ] PostgreSQL slow query log
- [ ] Redis memory alerts

### Internal Dashboard
- [ ] Prospect pipeline status
- [ ] Outreach delivery rates
- [ ] Site generation queue depth
- [ ] Revenue tracking

### First Real Campaign
- [ ] 20 Houston HVAC prospects
- [ ] SMS delivery > 95%
- [ ] 0 TCPA violations
- [ ] 1+ hot lead generated

### Phase 6 Exit Criteria
- [ ] All 20 pipelines complete
- [ ] Zero critical errors in Sentry
- [ ] First paying customer

---

## Appendix: Model Assignment (Per synthesized-architecture)

| Agent/Task | Model | Rationale |
|------------|-------|-----------|
| BusinessResearcher | gemini-1.5-flash | Structured extraction, binary outputs |
| CompetitorAnalyst | gemini-1.5-flash | Pattern recognition, no synthesis |
| CopyAgent | gemini-1.5-pro | Multi-constraint synthesis — quality is the deliverable |
| SiteBuilder | gemini-1.5-flash | Tool calling, deterministic output |
| OutreachAgent | gemini-1.5-flash | Template-based, low creativity needed |

---

**Checklist Version:** 1.0  
**Last Updated:** 2026-04-25  
**Next Review:** After Phase 3 completion
