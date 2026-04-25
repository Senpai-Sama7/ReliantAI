# ReliantAI Platform — Claude Code Implementation Prompt System
## Master prompt + per-phase session kickoffs

---

## HOW TO USE THIS FILE

This file has two parts:

**Part 1 — CLAUDE.md** (copy into `reliantai/CLAUDE.md` before your first session)
**Part 2 — Phase Prompts** (one per sprint week — paste the relevant one as your first message in each Claude Code session after `/clear`)

The CLAUDE.md loads every turn (~150 tokens). The phase prompt fires once per session (~400-600 tokens). Together they give Claude Code full architectural context with zero redundancy.

---

# PART 1: CLAUDE.md

Copy this verbatim into `reliantai/CLAUDE.md`:

```markdown
# ReliantAI Platform — CLAUDE.md

## Repos
- reliantai/                → FastAPI + Celery + SQLAlchemy (Python 3.12)
- reliantai-website/        → Vite + React 19 (marketing, reliantai.org)
- reliantai-client-sites/   → Next.js 15 App Router (ISR sites, preview.reliantai.org)

## Hard constraints — never deviate
- NO per-site builds. Sites render via Next.js ISR from DB content.
- Slug: generate_slug(business_name, city) — never from place_id
- Celery Beat: celery_app.py beat_schedule — NOT django_celery_beat
- Tool _run(): SYNCHRONOUS only (sync httpx.Client)
- Preview domain: preview.reliantai.org — NOT reliantai.org/preview/
- CopyAgent LLM: gemini-1.5-pro. All other agents: gemini-1.5-flash.
- All tool _run() are sync. CrewAI threads them internally.

## Commands
api:      uvicorn reliantai.main:app --reload --port 8000
workers:  celery -A reliantai.celery_app worker -Q agents --concurrency 2
beat:     celery -A reliantai.celery_app beat
tests:    pytest tests/ -x -v
migrate:  alembic upgrade head

## Current sprint
Phase: [update before each session]
In scope: [update before each session]
```

---

# PART 2: PHASE PROMPTS

Each prompt is designed to be pasted as your **first message** after `/clear`.
Run `/context` after pasting to verify baseline token count before any file reads.

---

## PHASE 1 PROMPT — Week 1: Infrastructure + Schema
**Covers:** Postgres schema, SQLAlchemy models, FastAPI skeleton, Docker Compose, Celery/Redis setup

```
PHASE 1: Infrastructure + Schema
Reference spec: synthesized-architecture.md → "PHASE 0: DATA SCHEMA" + "Component 4: ORM Models" + "Component 5: Celery Config" + "ENVIRONMENT VARIABLES"

BUILD IN THIS ORDER — do not skip steps or reorder:

STEP 1: Database migration file
File: reliantai/db/migrations/001_platform.sql
Requirements:
- All 7 tables: prospects, research_jobs, business_intelligence, competitor_intelligence, generated_sites, clients, outreach_sequences, outreach_messages, lead_events
- UUID primary keys using gen_random_uuid()
- All indexes from the spec: idx_prospects_trade_city, idx_prospects_status, idx_outreach_next_send (partial WHERE status='active')
- Correct FK cascade rules: prospects → CASCADE delete on research_jobs, business_intelligence, competitor_intelligence, outreach_sequences
- generated_sites.client_id → SET NULL (client can be deleted without losing site)
- outreach_sequences.next_send_at index is PARTIAL — only where status = 'active'

STEP 2: SQLAlchemy ORM models
File: reliantai/db/models.py
Requirements:
- Use declarative_base(), not DeclarativeBase (SQLAlchemy 1.x pattern, not 2.x)
- UUID primary keys as String type with default=lambda: str(uuid.uuid4())
- All relationship() calls with correct back_populates + cascade="all, delete-orphan" where applicable
- BusinessIntelligence includes: instagram_url (missing from Plan B), gbp_review_response_rate, site_last_updated, site_mobile_friendly, owner_title
- OutreachSequence has: with_for_update() used in scheduler — model must support this (standard SQLAlchemy, no special config needed)
- Each model gets a to_dict() method returning JSON-serializable dict

STEP 3: DB session factory
File: reliantai/db/__init__.py
Requirements:
- get_db_session() as context manager using contextlib.contextmanager
- Connection pool: pool_size=5, max_overflow=10, pool_pre_ping=True
- DATABASE_URL from environment only — no hardcoded values

STEP 4: Celery app (no Django dependency)
File: reliantai/celery_app.py
Requirements:
- Use celery_app.py from synthesized-architecture.md Component 5 verbatim
- beat_schedule uses crontab and float schedule — no DatabaseScheduler
- task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1
- autodiscover_tasks(["reliantai.tasks"])

STEP 5: FastAPI skeleton
File: reliantai/main.py
Requirements:
- App with CORS configured for reliantai.org and preview.reliantai.org origins
- /health endpoint returning {"status": "ok", "db": bool, "redis": bool}
- verify_api_key dependency using HTTPBearer + constant-time compare against API_SECRET_KEY env var
- Include placeholder routers: api/v2/prospects, api/v2/webhooks, api/v2/generated-sites
- Startup event that verifies DB connection and logs any migration drift

STEP 6: Docker Compose
File: docker-compose.yml
Requirements:
- Services: api, celery_agents, celery_outreach, celery_beat, postgres, redis
- postgres: image postgres:16-alpine, healthcheck pg_isready, volume for data persistence
- redis: image redis:7-alpine, requirepass via env var, maxmemory 256mb allkeys-lru
- celery_agents: concurrency 2, queues agents + agents_high
- celery_outreach: concurrency 4, queues outreach + provisioning
- All services: restart unless-stopped
- api depends_on postgres and redis with condition: service_healthy

STEP 7: Alembic setup
File: alembic.ini, alembic/env.py
Requirements:
- Target metadata from reliantai.db.models Base
- DATABASE_URL from environment variable
- autogenerate support

STEP 8: Smoke test
File: tests/test_models.py
Requirements:
- Uses pytest + pytest-postgresql or in-memory SQLite for CI
- Creates Prospect → ResearchJob → BusinessIntelligence → GeneratedSite → OutreachSequence in one test
- Reads them back with all relationships loaded
- Asserts: prospect.business_intel is not None, prospect.generated_site is not None
- This test is the PHASE GATE — do not proceed to Phase 2 until it passes

CONSTRAINTS FOR THIS PHASE:
- Do NOT create any agent files yet
- Do NOT create site templates
- Do NOT install crewai or google-generativeai yet — keep requirements.txt minimal
- Required packages this phase only: fastapi, uvicorn, sqlalchemy, alembic, celery, redis, psycopg2-binary, pydantic[email], httpx, structlog, python-dotenv

EXIT CRITERIA:
1. pytest tests/test_models.py passes
2. docker-compose up --build → all 6 services show healthy in docker ps
3. curl http://localhost:8000/health returns {"status":"ok","db":true,"redis":true}
```

---

## PHASE 2 PROMPT — Week 2: Agent Crew
**Covers:** All 5 agents, GooglePlacesTool, GBPScraperTool, SiteRegistrationService, OutreachAgent tools, Celery pipeline task

```
PHASE 2: Agent Crew
Reference spec: synthesized-architecture.md → "Component 1: SiteRegistrationService" + "Component 2: API Layer" + "Component 3: CopyAgent Task" + "PHASE 1: AGENT CREW ARCHITECTURE"

PREREQUISITES: Phase 1 smoke test passes. DB is running.

BUILD IN THIS ORDER:

STEP 1: LLM factory
File: reliantai/agents/llm.py
Requirements:
- gemini_pro = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.5, max_output_tokens=4096)
- gemini_flash = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3, max_output_tokens=2048)
- Both initialized from GOOGLE_AI_API_KEY env var

STEP 2: GooglePlacesTool
File: reliantai/agents/tools/google_places.py
Requirements:
- Inherits BaseTool from crewai_tools
- _run() is SYNCHRONOUS — uses httpx.Client (not AsyncClient)
- Supports both query= and place_id= parameters in single method
- Text Search endpoint for query, Details endpoint for place_id
- Details fields: reviews,name,rating,user_ratings_total,formatted_phone_number,website,opening_hours,address_components,geometry,photos,business_status,editorial_summary
- reviews_sort: most_relevant
- _format_details() extracts top 5 reviews with author, rating, text, time
- Exponential backoff on HTTP 429: 1s, 2s, 4s, 8s — max 3 retries
- Returns str(dict) — not JSON — CrewAI agents receive string tool outputs

STEP 3: PageSpeedTool
File: reliantai/agents/tools/pagespeed.py
Requirements:
- _run(url: str) → SYNCHRONOUS
- Calls PageSpeed Insights API with strategy=mobile
- Returns: {score: int, lcp: float, fid: float, cls: float, has_ssl: bool}
- Returns {"score": 0, "error": "no_url"} if url is None or empty — never crash
- Timeout: 20s

STEP 4: GBPScraperTool
File: reliantai/agents/tools/gbp_scraper.py
Requirements:
- _run(place_id: str) → SYNCHRONOUS
- Calls Places Details API for photos, editorial_summary, opening_hours
- _estimate_completeness() scores 0-100 based on which fields are populated
- _estimate_review_response_rate() from reviews list: count reviews with owner_response / total
- Does NOT scrape Google Maps HTML (unreliable) — use API data only

STEP 5: SchemaValidatorTool
File: reliantai/agents/tools/schema_validator.py
Requirements:
- validate_schema_org(schema: dict) → bool
- Calls Google Rich Results Test API (POST https://searchconsole.googleapis.com/v1/urlTestingTools/mobileFriendlyTest:run)
- Falls back to local structural validation if API fails: checks @context, @type, name, address fields exist
- Non-fatal: return False with warning log on API failure, do not raise

STEP 6: Schema builder
File: reliantai/agents/tools/schema_builder.py
Requirements:
- build_local_business_schema(business_data, review_data, competitor_keywords) → dict
- TRADE_TO_SCHEMA_TYPE mapping: hvac→HVACBusiness, plumbing→Plumber, electrical→Electrician, roofing→RoofingContractor, painting→HousePainter, landscaping→LandscapingBusiness
- @type is a LIST: [schema_type, "LocalBusiness"]
- Include: @id, name, description, url, telephone, image, logo, priceRange, address (PostalAddress), geo (GeoCoordinates), areaServed (list), aggregateRating, review (top 3), sameAs (all social URLs), hasOfferCatalog, mainEntity (FAQ as Question/Answer pairs)
- Add foundingDate only if years_in_business is known

STEP 7: SiteRegistrationService
File: reliantai/services/site_registration_service.py
Requirements:
- Exact implementation from synthesized-architecture.md Component 1
- generate_slug() uses regex + uuid4()[:4] suffix
- _get_theme() returns all 6 trade themes
- _revalidate_preview_cache() catches ALL exceptions — non-fatal
- register() is idempotent: if GeneratedSite already exists for prospect_id, update it, don't duplicate

STEP 8: Twilio SMS tool
File: reliantai/agents/tools/twilio_sms.py
Requirements:
- _run(to: str, body: str) → SYNCHRONOUS
- Validates E.164 format before send: re.match(r'^\+1\d{10}$', to)
- Returns {"sid": str, "status": str} on success
- Returns {"error": "invalid_number"} on format fail — do not raise
- Logs to structlog with to_number (last 4 digits only), body_length, status

STEP 9: Resend email tool
File: reliantai/agents/tools/resend_email.py
Requirements:
- _run(to: str, subject: str, body: str) → SYNCHRONOUS
- Plain text email (no HTML templating yet)
- Returns {"id": str, "status": "sent"} on success
- Returns {"error": str} on failure — do not raise

STEP 10: Agent crew
File: reliantai/agents/home_services_crew.py
Requirements:
- 5 agents: business_researcher (gemini_pro), competitor_analyst (gemini_flash), copy_agent (gemini_pro), site_builder_agent (gemini_flash — now calls SiteRegistrationService not Vercel CLI), outreach_agent (gemini_flash)
- prospect_scout is NOT defined here — scan happens at API layer
- All agent backstories from Plan B (more evocative)
- All task descriptions from Plan A (more mechanically precise) with Plan B's SMS example added to t_outreach
- site_builder_agent task description calls SiteRegistrationService.register() not VercelDeployTool
- Crew: Process.sequential, memory=True, embedder google/text-embedding-004, max_rpm=10
- create_prospect_crew(prospect_data: dict) → Crew

STEP 11: Celery task wrapper
File: reliantai/tasks/prospect_tasks.py
Requirements:
- run_prospect_pipeline: bind=True, autoretry_for=(Exception,), retry_kwargs max_retries=3 countdown=60, soft_time_limit=900, time_limit=1200, queue="agents"
- Creates ResearchJob record BEFORE crew.kickoff()
- Updates ResearchJob.step at each agent transition (use crew callbacks if available, else update after kickoff)
- On completion: sets prospect.status="outreach_sent"
- On failure: sets job.status="failed", job.error_message=str(exc)[:500], raises to trigger retry
- process_inbound_response: stops_words set includes "stop","unsubscribe","quit","cancel","end","no more","opt out"
- process_scheduled_followups: with_for_update(skip_locked=True), advances current_step AND next_send_at atomically

STEP 12: Prospects API router
File: reliantai/api/v2/prospects.py
Requirements:
- Exact implementation from synthesized-architecture.md Component 2
- POST / (inbound, deduplicates by place_id)
- POST /scan (outbound batch)
- GET /{prospect_id}/status
- GET / (list with filters: status, trade, city, page, page_size)
- All routes require verify_api_key dependency

STEP 13: Integration test
File: tests/test_pipeline_integration.py
Requirements:
- Mocks GooglePlacesTool to return fixture data for "Apex HVAC Houston TX"
- Mocks Twilio + Resend to return success responses
- Runs create_prospect_crew(fixture_data).kickoff()
- Asserts: GeneratedSite created in DB, status="preview_live", preview_url contains "preview.reliantai.org"
- Asserts: OutreachMessage created with channel="sms", status="sent"

CONSTRAINTS:
- Do NOT build site templates yet (Week 3)
- Do NOT build the Next.js client sites project yet
- Real Gemini API calls are allowed in integration test but wrap in pytest.mark.integration so CI can skip

EXIT CRITERIA:
1. pytest tests/ -x -v passes (unit tests + integration with mocks)
2. Run pipeline manually against one real Houston HVAC prospect
3. Check DB: prospect.status == "outreach_sent", GeneratedSite.preview_url is set
4. preview.reliantai.org/{slug} returns 404 (expected — Next.js not built yet)
```

---

## PHASE 3 PROMPT — Week 3: Client Sites (Next.js)
**Covers:** reliantai-client-sites Next.js 15 app, ISR dynamic routes, hvac-reliable-blue template, revalidation endpoint, preview banner

```
PHASE 3: Client Sites — Next.js App
Reference spec: synthesized-architecture.md → "Flaw 1 fix (ISR architecture)" + "Component 7: Preview Site + Purchase CTA" + trade theme map in Component 1

This phase creates the THIRD REPO: reliantai-client-sites/
Working directory for this session: reliantai-client-sites/

STEP 1: Project scaffold
Command: npx create-next-app@latest reliantai-client-sites --typescript --tailwind --app --no-src-dir --import-alias "@/*"
Then install: npm install framer-motion lucide-react

File: reliantai-client-sites/next.config.ts
Requirements:
- output is NOT 'export' — we use ISR, not static export
- images.domains includes ['preview.reliantai.org', 'api.reliantai.org']
- env: PLATFORM_API_URL and PLATFORM_API_KEY from process.env

STEP 2: SiteContent TypeScript interface
File: reliantai-client-sites/types/SiteContent.ts
Requirements:
- Exact interface from synthesized-architecture.md Component 4 (SiteContent type)
- Export all sub-types: BusinessInfo, HeroSection, ServiceItem, AboutSection, ReviewsSection, FAQItem, SEOMeta, AEOSignals, ThemeConfig

STEP 3: API fetcher
File: reliantai-client-sites/lib/api.ts
Requirements:
- getSiteContent(slug: string): Promise<SiteContent | null>
- Fetches from PLATFORM_API_URL/api/v2/generated-sites/{slug}
- Authorization: Bearer PLATFORM_API_KEY
- next: { revalidate: 3600 } on the fetch call
- Returns null on any non-200 response (do not throw)
- getTemplate(templateId: string): Promise<React.ComponentType<{content: SiteContent}>>
- Dynamic imports: import('@/templates/hvac-reliable-blue') etc.

STEP 4: Dynamic route page
File: reliantai-client-sites/app/[slug]/page.tsx
Requirements:
- export const revalidate = 3600
- getSiteContent call — if null, return notFound()
- Dynamic template import via getTemplate(content.site_config.template_id)
- generateMetadata: title from seo.title, description from seo.description, JSON-LD injected via: other: { 'script:ld+json': JSON.stringify(content.schema_org) }
- isPreview = content.status === "preview_live"
- Renders <Template content={content} /> then PreviewBanner if isPreview

STEP 5: Revalidation API route
File: reliantai-client-sites/app/api/revalidate/route.ts
Requirements:
- POST handler only
- Verifies Authorization header against REVALIDATE_SECRET env var using crypto.timingSafeEqual
- Calls revalidatePath('/[slug]', 'page') and revalidateTag(slug)
- Returns {revalidated: true, slug} on success
- Returns 401 on auth failure — no detail in body (security)

STEP 6: Preview banner component
File: reliantai-client-sites/components/PreviewBanner.tsx
Requirements:
- Fixed bottom bar, z-50, dark slate background
- Left: "This is your free preview site. It expires in 30 days." + Lighthouse score + city
- Right: two CTAs — "Get This Site — $497" (blue filled) + "Growth Plan — $297/mo" (outlined)
- Both links use href={`/checkout?slug=${slug}&package=starter`} and growth
- Mobile: stack vertically, CTAs full width

STEP 7: hvac-reliable-blue template
File: reliantai-client-sites/templates/hvac-reliable-blue/index.tsx
Requirements:
- Default export: HvacTemplate({ content: SiteContent })
- Import and compose all section components
- Sections in order: ContactBar (sticky top), Hero, Services, About, Reviews, FAQ, Footer
- Theme tokens: primary #1d4ed8, accent #93c5fd, fonts Outfit (display) + Inter (body)
- ContactBar: fixed top, dark bg, phone number as <a href="tel:...">, visible on mobile first

STEP 8: Hero section component
File: reliantai-client-sites/templates/hvac-reliable-blue/sections/Hero.tsx
Requirements:
- Exact implementation from synthesized-architecture.md Component 3C
- Framer Motion: opacity+y fade-in on headline, subheadline, CTA group, trust bar
- Star rating bar above headline using content.business.review_count and google_rating
- Primary CTA: <a href="tel:{phone}"> with Phone icon
- Trust bar: map content.hero.trust_bar with Shield icon
- Background: gradient from slate-900 via blue-950 to slate-900 + subtle grid overlay

STEP 9: Remaining section components (all in hvac-reliable-blue/sections/)
Files: Services.tsx, About.tsx, Reviews.tsx, FAQ.tsx, Footer.tsx, ContactBar.tsx
Requirements:
- Services: 3-column grid on desktop, 1-column mobile, each card has icon + title + description + CTA link
- About: 2-column (text left, trust bullets right), owner story paragraph, 3 trust_points as checkmark list
- Reviews: 3-column grid of review cards, aggregate_line below, Google logo/stars attribution
- FAQ: Accordion (no external library — use useState for open/close), schema-friendly (question in <dt>, answer in <dd>)
- Footer: business name, phone, address, copyright, social links from schema_org.sameAs
- ContactBar: sticky top, compact — phone number + "Call Now" text

STEP 10: Generated sites API endpoint (FastAPI)
File: reliantai/api/v2/generated_sites.py (ADD to existing platform)
Requirements:
- GET /api/v2/generated-sites/{slug}
- Returns full GeneratedSite.site_content JSON merged with business data
- No auth required — this is public (preview pages are public)
- Adds to FastAPI app router

CONSTRAINTS:
- Build only hvac-reliable-blue template this week — other 5 templates are Week 4
- Do NOT add checkout/Stripe logic yet — PreviewBanner CTAs can be placeholder links
- Tailwind only — no CSS modules, no styled-components

EXIT CRITERIA:
1. npm run build in reliantai-client-sites/ succeeds with 0 TypeScript errors
2. Run pipeline against Houston HVAC prospect → site registered in DB
3. Visit preview.reliantai.org/{slug} → renders with real business data, 90+ Lighthouse mobile
4. PreviewBanner visible, Lighthouse score shows in banner
5. curl -X POST https://preview.reliantai.org/api/revalidate with correct secret → {revalidated: true}
```

---

## PHASE 4 PROMPT — Week 4: Templates + Outreach + Stripe
**Covers:** 5 remaining trade templates, outreach sequence state machine, inbound SMS routing, Stripe webhook → provisioning

```
PHASE 4: Remaining Templates + Outreach Pipeline + Stripe
Reference spec: synthesized-architecture.md → "Component 6: OutreachService" + "Flaw 7 fix" + "PHASE 5: OUTREACH + FOLLOW-UP PIPELINE" + "Stripe Webhook" from API layer

BUILD IN THIS ORDER:

STEP 1: Template factory pattern
Before building 5 more templates, extract shared components:

File: reliantai-client-sites/components/shared/
- TradeHero.tsx        → parameterized Hero (accepts theme tokens)
- TradeServices.tsx    → parameterized Services grid
- TradeAbout.tsx       → parameterized About section
- TradeReviews.tsx     → parameterized Reviews
- TradeFAQ.tsx         → parameterized FAQ accordion
- TradeFooter.tsx      → parameterized Footer
- PreviewBanner.tsx    → already built, move here

Each shared component accepts: content: SiteContent + theme: ThemeConfig
Theme tokens override via CSS custom properties injected at template root via style={{}} tag.

STEP 2: Remaining 5 templates
Files (each is a thin wrapper importing shared components with its own theme):
- reliantai-client-sites/templates/plumbing-trustworthy-navy/index.tsx
  Theme: primary #1e3a5f, accent #60a5fa, display font Sora
  Differentiator: emergency contact bar in red above ContactBar, "24/7 Emergency" badge on Hero

- reliantai-client-sites/templates/electrical-sharp-gold/index.tsx
  Theme: primary #1a1a1a, accent #fbbf24, display font Outfit
  Differentiator: dark mode throughout, gold accent CTAs, "Licensed Electrician" badge

- reliantai-client-sites/templates/roofing-bold-copper/index.tsx
  Theme: primary #292524, accent #c2713a, display font Sora
  Differentiator: full-bleed before/after image placeholder section, financing badge

- reliantai-client-sites/templates/painting-clean-minimal/index.tsx
  Theme: primary #f8fafc (light), accent #3b82f6, display font Playfair Display
  Differentiator: light theme (only one), color swatch section, portfolio grid placeholder

- reliantai-client-sites/templates/landscaping-earthy-green/index.tsx
  Theme: primary #14532d, accent #86efac, display font Outfit
  Differentiator: seasonal services toggle (Spring/Summer/Fall/Winter tabs — useState)

All 6 templates must pass 90+ Lighthouse mobile individually.

STEP 3: Outreach sequence state machine (the fixed version)
File: reliantai/services/outreach_service.py
Requirements:
- Exact implementation from synthesized-architecture.md Component 6
- execute_step() uses with_for_update() (not skip_locked — single prospect lock)
- Advances current_step AND next_send_at in SAME transaction as OutreachMessage creation
- Sends OUTSIDE transaction — message delivery failure doesn't roll back state advance
- Updates provider_message_id + status in separate session after send
- resolve_template() handles missing owner_name gracefully: owner_first = "there" if unknown
- start_sequence() called by run_prospect_pipeline after OutreachAgent sends step 0

STEP 4: Process scheduled followups task (the fixed version)
File: reliantai/tasks/prospect_tasks.py (update existing)
Requirements:
- process_scheduled_followups() uses with_for_update(skip_locked=True) — THIS is where skip_locked belongs (multiple workers competing for sequence locks)
- Advances current_step AND sets next_send_at before queuing Celery task
- Commits state change BEFORE queuing — if Celery queue is full, state is already advanced (no duplicate fire on next cron run)
- If next_step > max_steps: set status="completed", next_send_at=None — do not queue

STEP 5: Inbound SMS webhook handler
File: reliantai/api/v2/webhooks.py (update existing)
Requirements:
- POST /api/v2/webhooks/twilio validates X-Twilio-Signature header using twilio.request_validator.RequestValidator
- Signature validation is NOT optional — reject invalid signatures with 403
- Routes body to process_inbound_response Celery task
- stop_words regex: catches "stop", "unsubscribe", "quit", "cancel", "end", "no more", "opt out", "remove me"
- Hot lead path: SMSService.send(to=OWNER_PHONE, body=f"HOT LEAD reply from {phone[-4:]}: {body[:100]}")
- Return TwiML empty response on all paths: <?xml version="1.0"?><Response></Response>

STEP 6: Stripe webhook → site provisioning
File: reliantai/api/v2/webhooks.py (update same file)
File: reliantai/tasks/provisioning_tasks.py (new)
Requirements:
- Stripe signature verified via stripe.Webhook.construct_event — not just event type check
- checkout.session.completed: extract prospect_id + package from session.metadata
- Missing prospect_id → log warning, return 200 (do not 500 on bad metadata)
- provision_client_site task: idempotency key = f"{prospect_id}:{stripe_session_id}" as Celery task ID
- Provisioning: creates Client record, updates GeneratedSite.status="purchased", assigns production_url
- customer.subscription.deleted: sets GeneratedSite.status="suspended"
- provision_client_site calls Vercel API to add custom domain if client.custom_domain is set

STEP 7: Stripe service
File: reliantai/services/stripe_service.py
Requirements:
- create_checkout_session(prospect_id, package, slug) → Stripe session URL
- package maps to price IDs from env vars: starter→STRIPE_STARTER_PRICE_ID, growth→STRIPE_GROWTH_PRICE_ID, premium→STRIPE_PREMIUM_PRICE_ID
- starter is mode="payment" (one-time), growth/premium are mode="subscription"
- success_url: https://preview.reliantai.org/{slug}?purchased=true
- cancel_url: https://preview.reliantai.org/{slug}
- metadata: {"prospect_id": prospect_id, "package": package, "slug": slug}

STEP 8: Checkout endpoint
File: reliantai/api/v2/checkout.py
Requirements:
- POST /api/v2/checkout with {prospect_id, package, slug}
- No auth required — public endpoint (Stripe handles payment security)
- Returns {checkout_url: str}
- Rate limit: 10 requests per minute per IP (use slowapi)

CONSTRAINTS:
- Do NOT add any GBP post generation yet (Week 6 backlog)
- Do NOT add Twilio phone lookup (landline detection) yet — add to Week 6 hardening

EXIT CRITERIA:
1. All 6 trade templates render with real content and pass 90+ Lighthouse mobile
2. Follow-up sequence fires correctly: create test sequence with next_send_at = now, run process_scheduled_followups(), verify current_step advances and new next_send_at is set
3. Stripe test webhook (stripe trigger checkout.session.completed) → GeneratedSite.status changes to "purchased"
4. Inbound STOP SMS → OutreachSequence.status = "unsubscribed"
```

---

## PHASE 5 PROMPT — Week 5: Marketing Site Integration
**Covers:** QuickPreviewForm on reliantai.org, LivePreviewDemo widget, Pricing page, schema.org on marketing site

```
PHASE 5: Marketing Site Integration
Working directory: reliantai-website/
Reference spec: synthesized-architecture.md → "Component 2: API Layer (inbound path)" + "PHASE 7: MARKETING SITE UPGRADES" + pricing psychology section

STEP 1: Environment config
File: reliantai-website/.env.local (add to .gitignore)
VITE_API_URL=https://api.reliantai.org
VITE_API_KEY=[your API_SECRET_KEY]

STEP 2: API client
File: reliantai-website/src/lib/api.ts
Requirements:
- createProspect(data: ProspectFormData) → Promise<{prospect_id, preview_url, pipeline_task_id}>
- getPipelineStatus(prospect_id: str) → Promise<{status, job_status, job_step}>
- Uses fetch with Authorization: Bearer ${import.meta.env.VITE_API_KEY}
- Typed with Zod schemas for both request and response

STEP 3: QuickPreviewForm component
File: reliantai-website/src/components/QuickPreviewForm.tsx
Requirements:
- Controlled form: trade (select), business_name, city, state (select), phone (optional), email (optional)
- TRADES array: hvac, plumbing, electrical, roofing, painting, landscaping with display labels
- On submit: POST to /api/v2/prospects via api.ts
- On success: redirect to preview.reliantai.org/{slug} using window.location.href (cross-origin)
- Loading state: "Building your preview..." with spinner
- Error state: show error.detail from API response
- Validation: trade required, business_name min 2 chars, city required, state required

STEP 4: LivePreviewDemo widget (homepage above-the-fold)
File: reliantai-website/src/components/LivePreviewDemo.tsx
Requirements:
- Exact implementation from synthesized-architecture.md Component 7 / PHASE 7A
- 4-step animated progress: "Scanning Google reviews..." → "Analyzing competitors..." → "Writing your copy..." → "Building your site..."
- Steps are VISUAL ONLY (timed animation, not real pipeline — marketing homepage)
- After animation completes: calls /api/demo-preview to get cached mock preview data
- Shows: business_name, google_rating, review_count, hero_headline, trust_signals
- CTA at bottom: "Get This Site — Starting at $497" → href="/pricing"
- DemoState type: "idle" | "searching" | "building" | "ready" | "error"

STEP 5: Demo preview API endpoint (FastAPI)
File: reliantai/api/v2/demo.py
Requirements:
- GET /api/v2/demo-preview?business_name=&city=
- Looks up a real GeneratedSite from DB matching the city/trade if one exists
- Falls back to a seeded fixture (Houston HVAC example) if no match
- Returns: {business_name, google_rating, review_count, hero_headline, trust_signals[], preview_url}
- No auth required — public marketing endpoint
- Rate limited: 20 req/min per IP

STEP 6: Pricing page
File: reliantai-website/src/pages/Pricing.tsx (or /pricing route)
Requirements:
3-tier architecture with deliberate decoy psychology:

STARTER — $497 one-time (BOTTOM — establishes price floor, loss-averse entry)
Features: Premium 5-page site, 90+ Lighthouse, Schema.org + FAQ, 1 GBP pass, 48hr delivery, 30-day preview
CTA: "Get My Site"

GROWTH — $297/month (TARGET — decoy above makes this feel cheap by contrast)
Features: Everything in Starter + ongoing AEO updates, 4 GBP posts/mo, 10 citation builds/mo, rank tracking, monthly report
CTA: "Start Growing" (primary, most prominent)
Badge: "Most Popular"

PREMIUM — $697/month (ANCHOR — makes Growth look like obvious value)
Features: Everything in Growth + weekly GBP posts, review request automation, competitor alerts, quarterly redesign, priority support, custom domain
CTA: "Go Premium"

Visual: Growth card is 10% larger, has the badge, slightly different background — pricing psychology demands this visual hierarchy

On CTA click: POST to /api/v2/checkout with {package} — requires prospect context
If no prospect_id in context: show QuickPreviewForm inline before checkout

STEP 7: schema.org on reliantai.org
File: reliantai-website/index.html (update <head>)
Requirements:
- Organization schema: ReliantAI, reliantai.org, DouglasMitchell@reliantai.org
- Service schema: "Website Design for Home Services Businesses", serviceType, areaServed: United States
- FAQPage schema: 4 questions about the product (what is it, how fast, what's included, how is it different from regular web design)
- Inject as <script type="application/ld+json"> in <head>

EXIT CRITERIA:
1. QuickPreviewForm submits → API creates prospect → redirects to preview.reliantai.org/{slug}
2. Pipeline status polling works (poll GET /{prospect_id}/status from frontend)
3. Pricing page renders, all 3 tiers visible, GROWTH is visually dominant
4. LivePreviewDemo animation completes → shows mock preview data
5. Google Rich Results Test passes for reliantai.org schema
```

---

## PHASE 6 PROMPT — Week 6: Production Hardening
**Covers:** Security audit, monitoring, load testing, TCPA compliance verification, first real campaign

```
PHASE 6: Production Hardening
Reference spec: synthesized-architecture.md → "FAILURE MODE REGISTER" + "ENVIRONMENT VARIABLES" + "Section 10: Security checklist"

This phase is AUDIT MODE, not feature mode. You are hardening existing code, not adding features.

SECURITY AUDIT CHECKLIST — verify each, fix if failing:

STEP 1: Twilio webhook signature verification
File: reliantai/api/v2/webhooks.py
Verify: twilio.request_validator.RequestValidator is called on every inbound SMS
Verify: 403 returned on signature mismatch — NOT 200 with error body
Test: send POST with wrong signature → expect 403
Add: if RequestValidator import fails (Twilio not installed), raise ImportError at module load — fail loud

STEP 2: Stripe webhook signature
Verify: stripe.Webhook.construct_event called BEFORE any event processing
Verify: SignatureVerificationError → 400, not 500
Test: stripe trigger checkout.session.completed with wrong secret → expect 400

STEP 3: Rate limiting
File: reliantai/main.py
Add: slowapi rate limiter
- /api/v2/prospects/ POST: 20/minute per IP
- /api/v2/prospects/scan POST: 5/minute per IP (autonomous scan — low volume expected)
- /api/v2/demo-preview: 20/minute per IP
- /api/v2/checkout: 10/minute per IP
- All webhook endpoints: 100/minute (Twilio/Stripe can burst)

STEP 4: TCPA pre-send validation
File: reliantai/services/outreach_service.py
Verify: execute_step() queries OutreachSequence.status = 'active' BEFORE building message
Verify: with_for_update() prevents concurrent sends
Add: check prospect.email is not None before email send — do not fail silently
Add: all SMS bodies end with "\n\nReply STOP to unsubscribe" if not already present

STEP 5: Sentry integration
File: reliantai/main.py, reliantai/celery_app.py
Add: sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], traces_sample_rate=0.1)
Add: SentryAsgiMiddleware on FastAPI app
Add: Celery Sentry integration: sentry_sdk.init + celery_app.conf.update(...)
Every unhandled exception in Celery tasks automatically reports to Sentry.

STEP 6: Structured logging audit
Verify: every Celery task logs with structlog.get_logger(), not print()
Verify: no sensitive data in logs (phone numbers logged as last-4 only, emails as domain only)
Add: correlation_id to every API request via middleware, passed to Celery task kwargs

STEP 7: Load test
Run: locust -f tests/locustfile.py --headless --users 10 --spawn-rate 2 --run-time 5m
File: tests/locustfile.py
- Simulate: 10 concurrent users each triggering 1 prospect pipeline
- Assert: no Celery task failures, all 10 GeneratedSite records created
- Assert: Gemini API does not return HTTP 429 (if it does: lower max_rpm in Crew config)
- Note: real pipeline takes 12-15 min — load test uses mocked Gemini responses

STEP 8: Twilio Lookup for landline detection
File: reliantai/services/sms_service.py
Add before every send:
client.lookups.v2.phone_numbers(to).fetch(fields="line_type_intelligence")
If line_type_intelligence.type in ("landline", "voip"): skip SMS, log warning, return {"skipped": "landline"}
This is Week 6 because Twilio Lookup costs $0.005/number — add only now after core pipeline confirmed working

STEP 9: Celery Flower dashboard
Add to docker-compose.yml:
  flower:
    image: mher/flower
    command: celery --broker=${REDIS_URL} flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
Flower shows: active tasks, task history, worker status, queue depths

STEP 10: First real campaign
Script: scripts/launch_campaign.py
```python
import httpx

PROSPECTS = [
    {"trade": "hvac", "city": "Houston", "state": "TX"},
    {"trade": "plumbing", "city": "Houston", "state": "TX"},
    # Add 20 total targets
]

for p in PROSPECTS:
    r = httpx.post(
        "http://localhost:8000/api/v2/prospects/scan",
        headers={"Authorization": f"Bearer {API_SECRET_KEY}"},
        json={**p, "max_prospects": 5, "auto_pipeline": True, "min_rating": 4.2}
    )
    print(r.json())
```
Monitor: Celery Flower for pipeline progress, Sentry for any errors

EXIT CRITERIA — GO / NO-GO GATES:
1. All 20 Celery pipeline tasks complete (status=completed in research_jobs)
2. SMS delivery rate > 95% (check Twilio console)
3. Zero TCPA violations: no SMS sent after STOP (test manually)
4. Sentry: 0 unhandled exceptions in production run
5. Flower: 0 task failures, queue depth returns to 0 after all pipelines complete
6. At least 1 hot lead reply received (or acknowledged as acceptable outcome)
7. Lighthouse: spot-check 3 generated sites — all 90+ mobile

LAUNCH = all 7 gates pass.
```

---

## QUICK REFERENCE: Session Start Checklist

Run these before every coding session:

```bash
# 1. Clear prior session
/clear

# 2. Check baseline token usage
/context

# 3. Disable MCP servers not needed for this session
# (check which are active in /context output, disable in Claude Code settings)

# 4. Confirm you're on Sonnet, not Opus
# (check model selector — Opus burns 5x quota)

# 5. Paste the phase prompt for the current week
# (one of the 6 prompts above)
```

Stop at 18-20 turns regardless of progress. Run `/compact`. Copy the output. Start a new session with the handoff format from Section 10 of the architecture doc.
