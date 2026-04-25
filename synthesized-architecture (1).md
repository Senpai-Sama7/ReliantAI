# ReliantAI Platform — Synthesized Architecture
## Comparative Analysis + Definitive Build Specification

**Status:** Final synthesis of Plan A (reliantai-platform-plan.md) and Plan B (production-grade-plan.md)  
**Date:** April 2026

---

## CRITICAL FLAW REGISTER — FIX BEFORE WRITING CODE

These exist in both plans and will cause failures in production.

### FLAW 1: Build-per-site is fatally slow (BOTH PLANS)
**What both plans do:** For every prospect, copy a template directory to `/tmp`, run `npm install` + `next build`, then deploy.  
**Problem:** `npm install` alone is 30-90 seconds. `next build` is 60-120 seconds. At 50 prospects/day, you need 50 concurrent workers each holding 2-4 minutes of CPU just doing JS builds. This doesn't scale and is expensive.

**Fix — adopted in this plan:**
Remove per-site builds entirely. Deploy one Next.js App Router project to Vercel with dynamic routes. Content is fetched at request time via ISR. The "build" step becomes a DB write.

```
reliantai-client-sites/       ← Single Next.js 15 App Router project
├── src/app/
│   ├── [slug]/page.tsx        ← Dynamic route, renders any client site
│   └── api/site-content/
│       └── [slug]/route.ts    ← API route: fetches site_content from platform DB
```

```typescript
// reliantai-client-sites/src/app/[slug]/page.tsx
import { notFound } from 'next/navigation';

export const revalidate = 3600; // ISR: revalidate every 1 hour

async function getSiteContent(slug: string) {
  const res = await fetch(
    `${process.env.PLATFORM_API_URL}/api/v2/generated-sites/${slug}`,
    {
      headers: { Authorization: `Bearer ${process.env.PLATFORM_API_KEY}` },
      next: { revalidate: 3600 },
    }
  );
  if (!res.ok) return null;
  return res.json();
}

export default async function ClientSitePage({ params }: { params: { slug: string } }) {
  const content = await getSiteContent(params.slug);
  if (!content) return notFound();
  
  // Dynamically import the correct trade template
  const Template = await import(`@/templates/${content.site_config.template_id}`);
  return <Template.default content={content} />;
}

export async function generateMetadata({ params }) {
  const content = await getSiteContent(params.slug);
  if (!content) return {};
  return {
    title: content.seo.title,
    description: content.seo.description,
    other: { 'script:ld+json': JSON.stringify(content.schema_org) },
  };
}
```

**Result:** "Deploy" = one `INSERT INTO generated_sites`. Vercel ISR handles rendering. Zero `npm build` per prospect. The `VercelDeployTool` in both plans is **eliminated** and replaced with a `SiteRegistrationService` that writes to the DB and calls Vercel's `revalidatePath` API.

---

### FLAW 2: Slug generation from place_id (PLAN A only)
**Plan A code:** `prospect.place_id[:30].lower().replace(" ", "-")`  
**Problem:** Google Place IDs look like `ChIJN1t_tDeuEmsRUsoyG83frY4`. This produces `chijn1t_tdeuemsr` — not a human-readable slug, breaks URL aesthetics, breaks the outreach link.  
**Fix:** Use Plan B's `generate_slug(business_name, city)` — the correct implementation.

```python
def generate_slug(business_name: str, city: str) -> str:
    """'John\'s HVAC' + 'Houston' → 'johns-hvac-houston'"""
    import re, uuid
    raw = f"{business_name.lower()}-{city.lower()}"
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:55]
    # Collision guard
    return f"{slug}-{str(uuid.uuid4())[:4]}"
```

---

### FLAW 3: Django scheduler in a FastAPI project (PLAN A only)
**Plan A code:** `--scheduler django_celery_beat.schedulers:DatabaseScheduler`  
**Problem:** This requires Django ORM + Django installed. Your stack is FastAPI + SQLAlchemy. This will not import.  
**Fix:** Use Plan B's `process_scheduled_followups()` pattern — a Celery Beat periodic task running every 5 minutes that queries the DB directly.

```python
# reliantai/celery_config.py
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "process-scheduled-followups": {
        "task": "prospect_tasks.process_scheduled_followups",
        "schedule": 300.0,  # every 5 minutes
    },
    "weekly-gbp-post-generation": {
        "task": "client_tasks.generate_weekly_gbp_posts",
        "schedule": crontab(day_of_week=1, hour=9, minute=0),  # Monday 9 AM UTC
    },
}
```

---

### FLAW 4: Preview URL architecture mismatch (BOTH PLANS)
**Both plans say:** Preview at `reliantai.org/preview/{slug}`  
**Problem:** `reliantai.org` is a Vite + React 19 SPA. It doesn't support ISR, SSR, or file-system routing. `/preview/{slug}` would be client-rendered, losing all SEO value and having an ugly flash before content loads.  
**Fix:** Deploy the client-sites Next.js app to a subdomain.

```
Production distribution:
  reliantai.org             → Vite SPA (marketing site) — no change
  preview.reliantai.org     → Next.js App Router (preview + production client sites)
  
Preview URL:     preview.reliantai.org/{slug}
Production URL:  preview.reliantai.org/{slug}  ← same URL, just status changes
Custom domain:   client's own domain → CNAME to preview.reliantai.org (Vercel)
```

This means both preview and production sites live in the same Next.js app. Status in the DB determines whether a "buy this site" CTA overlay is shown. One deployment, zero per-prospect builds.

---

### FLAW 5: Async/sync mismatch in tools (PLAN B primarily)
**Plan B's `VercelDeployTool._run()`** is declared `async` but calls `subprocess.run()` (blocking). This will stall the entire event loop when deployed in an async context.  
**Plan B's `GBPScraperTool._run()`** same problem — async declaration, synchronous I/O.  
**Fix:** Either make all tool methods synchronous (CrewAI handles threading internally) OR use `asyncio.create_subprocess_exec` + `await` throughout. The synchronous approach is simpler and avoids event loop complexity inside agent tool execution.

```python
# CORRECT — synchronous tool (CrewAI runs tools in thread pool)
class GooglePlacesTool(BaseTool):
    def _run(self, query: str = None, place_id: str = None, ...) -> str:
        with httpx.Client(timeout=15.0) as client:  # sync httpx, not async
            ...
```

---

### FLAW 6: `prospect_scout` agent is dead code (PLAN A)
Plan A defines `prospect_scout` as an Agent but never adds it to the Crew. The scan is handled by a separate `ProspectService.scan()` method. The agent variable is defined and immediately orphaned.  
**Fix:** Delete `prospect_scout` from `home_services_crew.py`. The scan happens at the API layer, not inside a crew.

---

### FLAW 7: `process_scheduled_followups()` doesn't advance sequence state (PLAN B)
Plan B's scheduler task queues the follow-up task but never updates `current_step` or `next_send_at`, meaning it will re-queue the same step every 5 minutes forever.  
**Fix:**

```python
@shared_task(queue="outreach", name="prospect_tasks.process_scheduled_followups")
def process_scheduled_followups():
    with get_db_session() as db:
        now = datetime.utcnow()
        due = db.query(OutreachSequence).filter(
            OutreachSequence.next_send_at <= now,
            OutreachSequence.status == "active",
        ).with_for_update(skip_locked=True).all()  # skip_locked prevents double-firing
        
        for seq in due:
            next_step = seq.current_step + 1
            
            if next_step > seq.max_steps:
                seq.status = "completed"
                seq.next_send_at = None
            else:
                send_follow_up_message.apply_async(
                    args=[seq.id, next_step], queue="outreach"
                )
                seq.current_step = next_step
                # Next send date comes from the sequence template definition
                delay_days = SEQUENCE_STEP_DELAYS[seq.sequence_template][next_step]
                seq.next_send_at = now + timedelta(days=delay_days)
        
        db.commit()
```

---

## DEFINITIVE SYNTHESIZED ARCHITECTURE

### System Topology (corrected)

```
reliantai.org  (Vite SPA — marketing)
    │
    │ POST /api/v2/prospects          (inbound — user enters business from website)
    │ POST /api/v2/prospects/scan     (outbound — autonomous scan by trade+city)
    │
    ▼
api.reliantai.org  (FastAPI + Uvicorn, Railway or VPS)
    │
    ├── POST /api/v2/prospects        → saves to DB, queues Celery task
    ├── GET  /api/v2/generated-sites/{slug}  → returns site_content JSON
    ├── POST /api/v2/webhooks/stripe  → triggers provisioning task
    └── POST /api/v2/webhooks/twilio  → routes inbound SMS
    │
    ▼
Redis (broker + result backend)
    │
    ├── Queue: agents          (2 workers, concurrency 1 each — Gemini API)
    ├── Queue: outreach        (4 workers — Twilio/Resend)
    └── Queue: provisioning    (1 worker — idempotent Stripe provisioning)
    │
    ▼
Celery Workers
    │
    ├── run_prospect_pipeline(prospect_id)
    │     BusinessResearcher → CompetitorAnalyst → CopyAgent → SiteRegistration → OutreachAgent
    │
    └── process_scheduled_followups()  ← every 5 min via Beat
    │
    ▼
Postgres (single DB, no per-service isolation — solo project, not microservices)

preview.reliantai.org  (Next.js 15 App Router, Vercel)
    ├── /[slug]         → ISR page: fetches site_content from API, renders template
    └── /[slug]/buy     → Purchase overlay + Stripe checkout
```

---

## DEFINITIVE COMPONENT SPECIFICATIONS

### Component 1: Revised SiteRegistrationService (replaces VercelDeployTool)

```python
# reliantai/services/site_registration_service.py
"""
Replaces VercelDeployTool entirely.
'Deploying' a site = writing validated content to the DB.
Next.js ISR on preview.reliantai.org handles rendering.
"""
import httpx
import os
import structlog
from ..db import get_db_session
from ..models import GeneratedSite, Prospect
from ..agents.tools.schema_builder import build_local_business_schema
from ..agents.tools.schema_validator import validate_schema_org

log = structlog.get_logger()

TEMPLATE_MAP = {
    "hvac": "hvac-reliable-blue",
    "plumbing": "plumbing-trustworthy-navy",
    "electrical": "electrical-sharp-gold",
    "roofing": "roofing-bold-copper",
    "painting": "painting-clean-minimal",
    "landscaping": "landscaping-earthy-green",
}


class SiteRegistrationService:
    
    @staticmethod
    def register(
        prospect_id: str,
        copy_package: dict,
        research_data: dict,
        competitor_data: list,
    ) -> dict:
        """
        1. Build schema.org JSON-LD from research data
        2. Validate schema via Google Rich Results API
        3. Merge schema into copy_package
        4. Write GeneratedSite record to DB
        5. Revalidate ISR cache on preview.reliantai.org
        Returns: {slug, preview_url, schema_valid}
        """
        with get_db_session() as db:
            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            
            slug = generate_slug(prospect.business_name, prospect.city)
            template_id = TEMPLATE_MAP.get(prospect.trade, "hvac-reliable-blue")
            
            # Build schema
            schema = build_local_business_schema(
                business_data={**research_data, "slug": slug},
                review_data=copy_package.get("reviews", {}),
                competitor_keywords=competitor_data[0].get("top_keywords", []) if competitor_data else [],
            )
            
            schema_valid = validate_schema_org(schema)
            if not schema_valid:
                log.warning("schema_validation_failed", slug=slug)
                # Non-fatal: ship with warning, fix in post
            
            preview_url = f"https://preview.reliantai.org/{slug}"
            
            site = GeneratedSite(
                prospect_id=prospect_id,
                slug=slug,
                template_id=template_id,
                preview_url=preview_url,
                site_content={**copy_package, "schema_org": schema},
                site_config={
                    "template_id": template_id,
                    "trade": prospect.trade,
                    "theme": _get_theme(template_id),
                },
                schema_org_json=schema,
                meta_title=copy_package["seo"]["title"],
                meta_description=copy_package["seo"]["description"],
                status="preview_live",
            )
            db.add(site)
            db.commit()
        
        # Revalidate ISR cache so the slug renders immediately
        SiteRegistrationService._revalidate_preview_cache(slug)
        
        log.info("site_registered", slug=slug, preview_url=preview_url)
        return {
            "slug": slug,
            "preview_url": preview_url,
            "schema_valid": schema_valid,
        }
    
    @staticmethod
    def _revalidate_preview_cache(slug: str):
        """Tell Next.js to regenerate the ISR page for this slug immediately."""
        try:
            with httpx.Client(timeout=10.0) as client:
                client.post(
                    f"https://preview.reliantai.org/api/revalidate",
                    json={"slug": slug},
                    headers={"Authorization": f"Bearer {os.environ['REVALIDATE_SECRET']}"},
                )
        except Exception as e:
            log.warning("revalidate_failed", slug=slug, error=str(e))
            # Non-fatal: ISR will pick it up on first request anyway


def generate_slug(business_name: str, city: str) -> str:
    """'John\'s HVAC' + 'Houston' → 'johns-hvac-houston-a3f1'"""
    import re, uuid
    raw = f"{business_name.lower()}-{city.lower()}"
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:55]
    return f"{slug}-{str(uuid.uuid4())[:4]}"


def _get_theme(template_id: str) -> dict:
    themes = {
        "hvac-reliable-blue":       {"primary": "#1d4ed8", "accent": "#93c5fd", "font_display": "Outfit", "font_body": "Inter"},
        "plumbing-trustworthy-navy":{"primary": "#1e3a5f", "accent": "#60a5fa", "font_display": "Sora",   "font_body": "Inter"},
        "electrical-sharp-gold":    {"primary": "#1a1a1a", "accent": "#fbbf24", "font_display": "Outfit", "font_body": "Inter"},
        "roofing-bold-copper":      {"primary": "#292524", "accent": "#c2713a", "font_display": "Sora",   "font_body": "Inter"},
        "painting-clean-minimal":   {"primary": "#f8fafc", "accent": "#3b82f6", "font_display": "Playfair Display", "font_body": "Inter"},
        "landscaping-earthy-green": {"primary": "#14532d", "accent": "#86efac", "font_display": "Outfit", "font_body": "Inter"},
    }
    return themes.get(template_id, themes["hvac-reliable-blue"])
```

---

### Component 2: Merged API Layer (best of both plans)

Plan B correctly adds `email` to `ProspectCreateRequest` (critical for email outreach) and utm tracking. Plan A correctly separates batch-scan from single-create. Both are kept.

```python
# reliantai/api/v2/prospects.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v2/prospects", tags=["prospects"])
security = HTTPBearer()


# ─── INBOUND (from reliantai.org website form) ─────────────────────

class ProspectCreateRequest(BaseModel):
    """Used when a business owner fills out the website form themselves."""
    trade: str = Field(..., description="hvac|plumbing|electrical|roofing|painting|landscaping")
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    business_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{10}$")
    email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    utm_source: Optional[str] = None
    utm_campaign: Optional[str] = None

class ProspectCreateResponse(BaseModel):
    prospect_id: str
    status: str
    preview_url: str
    pipeline_task_id: str
    created_at: datetime

@router.post("/", response_model=ProspectCreateResponse)
async def create_prospect(
    request: ProspectCreateRequest,
    background_tasks: BackgroundTasks,
    token=Depends(verify_api_key),
):
    """
    Inbound path: business owner → website form → this endpoint.
    Deduplicates by place_id to prevent double-pipeline on same business.
    """
    places_result = await verify_place_exists(request.business_name, request.city, request.state)
    if not places_result:
        raise HTTPException(status_code=404, detail="Business not found on Google Places")
    
    place_id = places_result["place_id"]
    
    with get_db_session() as db:
        existing = db.query(Prospect).filter_by(place_id=place_id).first()
        if existing and existing.status not in ("identified",):
            # Already in pipeline — return existing preview URL
            slug = generate_slug(existing.business_name, existing.city)
            return ProspectCreateResponse(
                prospect_id=existing.id,
                status=existing.status,
                preview_url=f"https://preview.reliantai.org/{slug}",
                pipeline_task_id="already_running",
                created_at=existing.created_at,
            )
        
        prospect_id = str(uuid.uuid4())
        prospect = Prospect(
            id=prospect_id,
            place_id=place_id,
            business_name=request.business_name,
            trade=request.trade,
            city=request.city,
            state=request.state,
            phone=request.phone,
            email=request.email,
            address=places_result.get("address"),
            lat=places_result.get("lat"),
            lng=places_result.get("lng"),
            google_rating=places_result.get("rating"),
            review_count=places_result.get("review_count"),
            website_url=request.website_url or places_result.get("website"),
            status="identified",
        )
        db.add(prospect)
        db.commit()
    
    task = run_prospect_pipeline.apply_async(args=[prospect_id], queue="agents")
    slug = generate_slug(request.business_name, request.city)
    
    return ProspectCreateResponse(
        prospect_id=prospect_id,
        status="identified",
        preview_url=f"https://preview.reliantai.org/{slug}",
        pipeline_task_id=task.id,
        created_at=datetime.utcnow(),
    )


# ─── OUTBOUND (autonomous batch scan) ──────────────────────────────

class ScanRequest(BaseModel):
    """Used for autonomous scanning — Douglas triggers this, not a business owner."""
    trade: str
    city: str
    state: str
    radius_miles: int = 10
    max_prospects: int = 50
    min_rating: float = 4.0
    min_reviews: int = 10
    auto_pipeline: bool = True  # if True, queue pipeline for each new prospect found

@router.post("/scan")
async def scan_for_prospects(request: ScanRequest, token=Depends(verify_api_key)):
    """
    Autonomous outbound scanning.
    Finds businesses matching criteria, saves to DB, optionally queues pipelines.
    """
    prospects = await ProspectService.scan(
        trade=request.trade, city=request.city, state=request.state,
        radius_miles=request.radius_miles, max_results=request.max_prospects,
        min_rating=request.min_rating, min_reviews=request.min_reviews,
    )
    
    queued = 0
    if request.auto_pipeline:
        for p in prospects:
            if p["is_new"]:
                run_prospect_pipeline.apply_async(args=[p["id"]], queue="agents")
                queued += 1
    
    return {"scanned": len(prospects), "new": sum(1 for p in prospects if p["is_new"]), "queued": queued}
```

---

### Component 3: CopyAgent Task — Definitive Prompt (merged best of both)

Both plans have the same agent structure. Plan B's `backstory` fields are more evocative. Plan A's task `description` prompts are more mechanically precise. Merge: use Plan B backstories + Plan A task descriptions with Plan B's example SMS format added.

```python
# In t_copy task description, add this clarification from Plan B:
"""
9. OUTREACH SMS (< 155 chars)
   Example structure:
   "Hey {owner_first}, {specific_review_theme} is why {city} trusts {business_name}.
    See what your site could look like: {PREVIEW_URL}"
   
   Constraint: {PREVIEW_URL} must appear at end. Never shorten it — the full URL builds trust.
"""
```

---

### Component 4: Merged ORM Models (Plan B structure + Plan A fields)

Plan B's SQLAlchemy ORM is used as the base. Missing fields from Plan A are added.

```python
class BusinessIntelligence(Base):
    # ... Plan B fields ...
    
    # Added from Plan A — these are genuinely useful:
    gbp_review_response_rate = Column(DECIMAL(5, 2))  # Plan B ✓
    site_last_updated = Column(String(100))            # Plan B ✓
    site_mobile_friendly = Column(Boolean)             # Plan B ✓
    owner_title = Column(String(100))                  # Plan B ✓
    
    # These were in Plan A raw SQL but missed in Plan B ORM:
    instagram_url = Column(String(500))                # Plan A ✓ — add back
```

---

### Component 5: Definitive Celery Configuration (no Django dependency)

```python
# reliantai/celery_app.py
from celery import Celery
from celery.schedules import crontab
import os

app = Celery("reliantai")

app.config_from_object({
    "broker_url": os.environ["REDIS_URL"],
    "result_backend": os.environ["REDIS_URL"],
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC",
    "task_acks_late": True,                          # Don't ack until task completes
    "task_reject_on_worker_lost": True,              # Re-queue if worker dies mid-task
    "worker_prefetch_multiplier": 1,                 # One task at a time per worker
    "task_routes": {
        "prospect_tasks.run_prospect_pipeline": {"queue": "agents"},
        "prospect_tasks.send_follow_up_message": {"queue": "outreach"},
        "prospect_tasks.process_scheduled_followups": {"queue": "outreach"},
        "prospect_tasks.process_inbound_response": {"queue": "outreach"},
        "provisioning_tasks.provision_client_site": {"queue": "provisioning"},
    },
    "beat_schedule": {
        "process-scheduled-followups": {
            "task": "prospect_tasks.process_scheduled_followups",
            "schedule": 300.0,                       # Every 5 minutes
        },
        "weekly-gbp-posts": {
            "task": "client_tasks.generate_weekly_gbp_posts",
            "schedule": crontab(day_of_week=1, hour=9, minute=0),
        },
        "monthly-seo-report": {
            "task": "client_tasks.generate_monthly_seo_report",
            "schedule": crontab(day_of_month=1, hour=8, minute=0),
        },
    },
})

app.autodiscover_tasks(["reliantai.tasks"])
```

---

### Component 6: Complete Sequence State Machine (fixed from Plan B)

```python
# reliantai/services/outreach_service.py

SEQUENCE_STEP_DELAYS = {
    "home_services_v1": {
        # step_number: days_after_previous_step
        1: 3,
        2: 4,   # Day 7 total
        3: 7,   # Day 14 total
        4: 7,   # Day 21 total
    }
}

class OutreachService:
    
    @staticmethod
    def execute_step(db, sequence_id: str, step: int):
        """
        Execute one step of a sequence.
        Updates current_step and next_send_at in same transaction.
        Uses with_for_update() to prevent race conditions.
        """
        seq = db.query(OutreachSequence).filter_by(
            id=sequence_id, status="active"
        ).with_for_update().first()
        
        if not seq:
            return
        
        prospect = seq.prospect
        site = prospect.generated_site
        competitors = prospect.competitors
        
        if seq.channel == "sms":
            template_def = SMS_SEQUENCE[step]
        else:
            template_def = EMAIL_SEQUENCE[step]
        
        if not template_def:
            return
        
        body = OutreachService.resolve_template(
            template_def["template"] if seq.channel == "sms" else template_def["body"],
            prospect, site, competitors
        )
        
        msg = OutreachMessage(
            sequence_id=sequence_id,
            prospect_id=prospect.id,
            step_number=step,
            channel=seq.channel,
            to_address=prospect.phone if seq.channel == "sms" else prospect.email,
            from_address=os.environ["TWILIO_FROM_NUMBER"] if seq.channel == "sms" else os.environ["FROM_EMAIL"],
            subject=template_def.get("subject", ""),
            body=body,
            status="queued",
        )
        db.add(msg)
        
        # Advance sequence state
        if step >= seq.max_steps:
            seq.status = "completed"
            seq.next_send_at = None
        else:
            delay = SEQUENCE_STEP_DELAYS[seq.sequence_template].get(step + 1, 7)
            seq.next_send_at = datetime.utcnow() + timedelta(days=delay)
        
        seq.current_step = step
        db.commit()
        
        # Send outside transaction
        if seq.channel == "sms":
            result = SMSService.send(to=msg.to_address, body=msg.body)
        else:
            result = EmailService.send(
                to=msg.to_address,
                subject=msg.subject,
                body=msg.body,
            )
        
        # Update delivery status
        with get_db_session() as fresh_db:
            saved_msg = fresh_db.query(OutreachMessage).filter_by(id=msg.id).first()
            saved_msg.provider_message_id = result.get("id")
            saved_msg.status = "sent"
            saved_msg.sent_at = datetime.utcnow()
            fresh_db.commit()
```

---

### Component 7: Preview Site + Purchase CTA (merged from both)

Plan A's `LivePreviewDemo` handles the marketing homepage (shows a fast demo animation — good UX for an awareness-stage visitor). Plan B's `Preview.tsx` handles the actual `/preview/{slug}` page. Both are needed.

```tsx
// preview.reliantai.org/src/app/[slug]/page.tsx
// This is the REAL preview — reached via the outreach link sent to prospects

export default async function ClientSitePage({ params }) {
  const content = await getSiteContent(params.slug);
  if (!content) return notFound();
  
  const isPreview = content.status === "preview_live";
  const Template = await getTemplate(content.site_config.template_id);
  
  return (
    <>
      <Template content={content} />
      
      {/* Preview banner — only shown while not purchased */}
      {isPreview && (
        <div className="fixed bottom-0 inset-x-0 z-50 bg-slate-900 border-t border-slate-700
                        px-6 py-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-white font-semibold text-sm">
              This is your free preview site. It expires in 30 days.
            </p>
            <p className="text-slate-400 text-xs mt-0.5">
              Lighthouse score: {content.lighthouse_score} · Built for {content.business.city}
            </p>
          </div>
          <div className="flex gap-3 flex-shrink-0">
            <a href={`/checkout?slug=${params.slug}&package=starter`}
               className="px-4 py-2 bg-blue-500 text-white font-semibold text-sm rounded-lg
                          hover:bg-blue-400 transition-colors whitespace-nowrap">
              Get This Site — $497
            </a>
            <a href={`/checkout?slug=${params.slug}&package=growth`}
               className="px-4 py-2 border border-blue-400 text-blue-300 font-medium text-sm
                          rounded-lg hover:border-blue-300 transition-colors whitespace-nowrap">
              Growth — $297/mo
            </a>
          </div>
        </div>
      )}
    </>
  );
}
```

---

## DEFINITIVE EXECUTION SEQUENCE

Week 1 and 2 order is swapped from both plans. Infrastructure before agents.

```
WEEK 1: Infrastructure + Schema
  Day 1:   Postgres migrations (Plan A SQL) + SQLAlchemy models (Plan B ORM)
  Day 2:   FastAPI app skeleton + API auth (Bearer token) + health endpoint
  Day 3:   Celery + Redis setup (no Django; use reliantai/celery_app.py above)
  Day 4:   GooglePlacesTool (sync, not async — Plan B logic in sync wrapper)
  Day 5:   ProspectService.scan() — test against real Houston HVAC query
  Day 6-7: Docker Compose running: api + postgres + redis + celery (2 workers)
  GATE: `docker-compose up` → all services healthy → scan finds 5 real prospects

WEEK 2: Agent Crew (no templates yet — test on mock SiteRegistration)
  Day 1-2: BusinessResearcher + tests on 3 real Houston HVAC prospects
  Day 3:   CompetitorAnalyst + gap analysis output validation
  Day 4-5: CopyAgent prompt iteration (5 real prospects, evaluate output quality)
  Day 6:   SiteRegistrationService (replaces VercelDeployTool — writes to DB, no build)
  Day 7:   OutreachAgent (Twilio SMS + Resend email — test with own phone number)
  GATE: Full pipeline runs E2E on 1 real prospect → SMS received → preview URL live

WEEK 3: Client Sites App (Next.js)
  Day 1:   Create reliantai-client-sites Next.js 15 App Router project
  Day 2:   Dynamic [slug] route + ISR + site_content fetch from API
  Day 3:   `hvac-reliable-blue` template (Hero + Services + About + Reviews + FAQ)
  Day 4:   Revalidation endpoint + SiteRegistrationService._revalidate_preview_cache()
  Day 5:   Preview banner component (buy CTA at bottom of preview pages)
  Day 6-7: Test: run pipeline → DB write → visit preview.reliantai.org/{slug} → renders
  GATE: 3 real sites live at preview.reliantai.org/{slug} with 90+ Lighthouse

WEEK 4: Remaining 5 Templates + Outreach Sequences
  Day 1-2: plumbing-trustworthy-navy + electrical-sharp-gold
  Day 3:   roofing-bold-copper + painting-clean-minimal + landscaping-earthy-green
  Day 4:   OutreachSequence scheduler (process_scheduled_followups + state machine)
  Day 5:   Inbound SMS routing + hot-lead notifications to OWNER_PHONE
  Day 6-7: Stripe webhook → provision_client_site (custom domain assignment via Vercel API)
  GATE: All 6 templates pass 90+ mobile Lighthouse. Follow-up sequence fires on schedule.

WEEK 5: Marketing Site Integration + Pricing
  Day 1-2: QuickPreviewForm (Plan B) on reliantai.org homepage
  Day 3:   LivePreviewDemo widget (Plan A) — animated demo for above-the-fold
  Day 4:   Pricing page (3-tier with decoy psychology: Starter/$497 → Growth/$297 → Premium/$697)
  Day 5:   Loss Calculator component (existing in website — wire to real prospect data)
  Day 6-7: schema.org on reliantai.org itself (Service, Organization, FAQPage)
  GATE: Inbound form → pipeline → preview URL returned in < 3 seconds (async)

WEEK 6: Production Hardening
  Day 1:   Load test: 10 concurrent pipelines (Celery concurrency 2, watch Gemini rate limits)
  Day 2:   Security audit: Twilio sig verification, Stripe sig, rate limiting, TCPA opt-out
  Day 3:   Monitoring: Sentry DSN in all services, Celery Flower dashboard, slow query log
  Day 4:   Internal ops dashboard: prospect pipeline status, outreach delivery rates
  Day 5-7: First real campaign: 20 Houston HVAC prospects. Measure: SMS delivery, preview views, replies
  GATE: All 20 pipelines complete. SMS delivery > 95%. 0 TCPA violations. 1+ hot lead.
```

---

## ADR REGISTER (Architecture Decision Records)

### ADR-001: No per-site builds
**Decision:** Client sites rendered via ISR on one shared Next.js app, not per-prospect builds.  
**Rationale:** Per-build approach fails at scale (CPU cost, time cost, fragility). ISR is Vercel's native pattern for this exact use case.  
**Consequence:** Site content must be API-fetchable and cacheable. Adds `reliantai-client-sites` as a third repo.

### ADR-002: Single Postgres DB, not per-service
**Decision:** One Postgres instance, all tables in one schema.  
**Rationale:** Solo developer. Microservice DB isolation adds operational overhead without benefit at this scale. Can partition later if needed.  
**Consequence:** All services must use the same connection pool. `get_db_session()` must be configured with appropriate pool size.

### ADR-003: CrewAI now, LangGraph at v2
**Decision:** CrewAI sequential process for MVP. LangGraph for v2.  
**Rationale:** CrewAI is wired in the existing `Money` service; migration cost is low for MVP. LangGraph's conditional edges (skip build if site already exists, skip outreach if opted out) are not needed for a sequential MVP but will matter at scale.  
**Consequence:** CrewAI's `Process.sequential` means if CompetitorAnalyst fails, the whole pipeline aborts. Mitigation: instrument each agent step with DB checkpoints so retried pipelines resume from last successful step.

### ADR-004: preview.reliantai.org as separate subdomain
**Decision:** Client sites at `preview.reliantai.org/{slug}`, not `reliantai.org/preview/{slug}`.  
**Rationale:** `reliantai.org` is a Vite SPA — it cannot do ISR or SSR. Redirecting the main domain to Next.js would require a framework migration.  
**Consequence:** Must configure `preview.reliantai.org` CNAME in Vercel for the client-sites project. Cross-origin concerns handled by CORS in FastAPI API.

---

## FAILURE MODE REGISTER (merged + enhanced)

| Component | Failure Mode | Detection | Mitigation |
|---|---|---|---|
| Google Places API | Rate limit (1 QPS text search, 10 QPS details) | HTTP 429 | Exponential backoff: 1s, 2s, 4s, 8s — max 3 retries |
| Gemini API | Rate limit / output truncated | Empty JSON in agent output | Retry with reduced prompt; CopyAgent max_tokens guard |
| CopyAgent | Hallucinated business name in copy | Post-generation validator | Assert: `prospect.business_name in copy_package["hero"]["headline"]` |
| SiteRegistrationService | DB write fails | DB exception | Celery retries task; idempotent on slug collision (unique constraint) |
| ISR cache stale | Preview page shows old content | N/A (acceptable for preview) | On purchase: force revalidate + clear CDN |
| Celery worker restart | In-flight task lost | Missing `completed_at` on ResearchJob | `acks_late=True` + `reject_on_worker_lost=True` ensures requeue |
| Twilio | Texting a landline | HTTP 400 from Twilio | Validate number format before send; check Twilio Lookup API for line type |
| Stripe webhook replay | Double-provisioning | Provision task fires twice | Idempotency key: `f"{prospect_id}:{stripe_session_id}"` on Celery task |
| TCPA violation | Text after STOP | Missing opt-out check | `with_for_update()` lock on outreach_sequences before every send |
| process_scheduled_followups | Race condition (2 workers both fire same step) | Duplicate messages | `with_for_update(skip_locked=True)` in scheduler query |

---

## ENVIRONMENT VARIABLES (complete, authoritative)

```bash
# ─── CORE ────────────────────────────────────────────────────────
DATABASE_URL=postgresql://reliantai:${DB_PASS}@localhost:5432/reliantai
REDIS_URL=redis://:${REDIS_PASS}@localhost:6379/0
SECRET_KEY=<64-byte hex>

# ─── GOOGLE ──────────────────────────────────────────────────────
GOOGLE_PLACES_API_KEY=<key>         # Places Text Search + Details
GOOGLE_PAGESPEED_API_KEY=<key>      # PageSpeed Insights API
SERPER_API_KEY=<key>                # Web search for agents

# ─── AI ──────────────────────────────────────────────────────────
GOOGLE_AI_API_KEY=<key>             # Gemini 1.5 Flash + Pro

# ─── COMMUNICATIONS ──────────────────────────────────────────────
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
OWNER_PHONE=+1XXXXXXXXXX            # Douglas's phone for hot-lead alerts

RESEND_API_KEY=<key>
FROM_EMAIL=DouglasMitchell@reliantai.org

# ─── PAYMENTS ────────────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_PRICE_ID=price_...   # $497 one-time
STRIPE_GROWTH_PRICE_ID=price_...    # $297/month recurring
STRIPE_PREMIUM_PRICE_ID=price_...   # $697/month recurring

# ─── DEPLOYMENT ──────────────────────────────────────────────────
VERCEL_TOKEN=<token>
VERCEL_TEAM_ID=<team_id>
REVALIDATE_SECRET=<32-byte hex>     # Shared between API and client-sites Next.js app

# ─── INTERNAL API ────────────────────────────────────────────────
API_SECRET_KEY=<32-byte hex>        # Used by website to call platform API
PLATFORM_API_URL=https://api.reliantai.org

# ─── SITE TEMPLATES (client-sites Next.js app only) ──────────────
PLATFORM_API_KEY=<API_SECRET_KEY above>
```

---

## WHAT TO BUILD FIRST (SINGLE DECISION)

Both plans correctly identify the bottleneck but bury it. State it directly:

**The first thing you build is not an agent. It is `reliantai/db/migrations/001_platform.sql` + the SQLAlchemy models. Every single component in this system — agents, API, outreach, site factory — writes to or reads from these tables. If the schema is wrong, everything downstream rots.**

Run the Postgres migration. Write the models. Write one test that creates a `Prospect`, a `ResearchJob`, a `GeneratedSite`, and an `OutreachSequence`, then reads them back with relationships loaded. When that test passes cleanly: the foundation is solid. Build everything else on top.

---

## SECTION 10: IMPLEMENTATION OPERATIONS

### Model Assignment Strategy

Never use Haiku for this build's generation tasks. The decision is architectural, not preferential.

Your pipeline has three properties that collapse Haiku's 70% quota savings advantage: (1) CopyAgent's task prompt is ~2,000 tokens of nested multi-constraint requirements — Haiku's instruction-following fidelity on deep structured JSON degrades and produces partially-correct outputs requiring correction turns that exceed original Sonnet cost; (2) SQLAlchemy ORM patterns, Next.js 15 RSC boundaries, and CrewAI tool contracts are architecturally sensitive — a single boundary violation cascades into 3-5 debug cycles; (3) agent-to-agent JSON passing requires schema conformance — Haiku's conformance rate on nested conditional fields is lower, and a malformed intermediate output aborts the sequential pipeline entirely.

**Definitive model assignment:**

| Task | Model | Rationale |
|---|---|---|
| BusinessResearcher agent | `gemini-1.5-flash` | Structured extraction, binary outputs |
| CompetitorAnalyst agent | `gemini-1.5-flash` | Pattern recognition, no synthesis |
| CopyAgent | `gemini-1.5-pro` | Multi-constraint synthesis — quality is the deliverable |
| SiteRegistrationService | `gemini-1.5-flash` | Schema assembly, deterministic |
| OutreachAgent | `gemini-1.5-flash` | Template variable substitution |
| Haiku-equivalent | Phone format validation, E.164 checks, character counts | Binary outputs only |

```python
# reliantai/agents/llm.py
from langchain_google_genai import ChatGoogleGenerativeAI

# Synthesis tasks — quality non-negotiable
gemini_pro = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.5,
    max_output_tokens=4096,
)

# Research and extraction — Sonnet-equivalent quality, faster
gemini_flash = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.3,
    max_output_tokens=2048,
)
```

---

### Claude Code Session Architecture

One Claude Code session = one sprint phase. Never span phase boundaries in a single session. Context accumulation across unrelated files degrades agent performance non-linearly past ~70% window capacity.

**Session structure — enforced for every coding session:**

```
START:  /clear       → wipe prior conversation history
        /context     → note baseline token count before first prompt
WORK:   ≤20 turns    → hard limit
        ≤80% window  → stop complex multi-file work at this threshold
END:    /compact     → structured summary of what was built
        copy output  → paste into new chat as session handoff
```

**Token profile for this build at steady-state (per session):**

```
Baseline context load (before first prompt):
  CLAUDE.md:                    ~150 tokens    (constant, every turn)
  Active MCP tool schemas:      ~2,000 tokens  (disable unused MCPs)
  Opened file set:              ~8,000 tokens  (2-3 files typical)
  ─────────────────────────────────────────────
  Pre-prompt baseline:          ~10,150 tokens

Growth per turn:
  Each assistant response adds  ~500-2,000 tokens to history
  Turn 20 history overhead:     ~15,000-25,000 tokens accumulated
  ─────────────────────────────────────────────
  Session cost at turn 20:      ~35,000-50,000 tokens total context
```

At ~45 Sonnet messages per 5-hour window, a disciplined 20-turn session uses less than half a window. Six phase sessions per week = well within the 40-80 hour weekly cap.

---

### `.claudeignore` — Create Before First Session

Place in `reliantai/` repo root. Without this, Claude Code reads `site-templates/*/node_modules/` on every file exploration — silently adding 30,000+ tokens to early turns.

```gitignore
# reliantai/.claudeignore
node_modules/
.next/
dist/
build/
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
.pytest_cache/
celery_*.db
*.log
logs/
.env
.env.*
secrets/
*.pem
*.key

# Client site template build artifacts
site-templates/*/node_modules/
site-templates/*/dist/
site-templates/*/.next/
site-templates/*/.out/
```

---

### `.claude/settings.json` — Configure Before First Session

```json
{
  "availableModels": ["sonnet", "haiku"],
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./.venv/**)",
      "Read(./node_modules/**)",
      "Read(./site-templates/*/node_modules/**)",
      "Read(./site-templates/*/.next/**)"
    ]
  }
}
```

`availableModels` prevents accidental Opus burns — a single complex multi-file refactor on Opus costs 5x Sonnet quota and can burn a 5-hour window in 9-12 turns.

---

### CLAUDE.md — The Repo-Level Context File

Keep this under 200 lines. It is loaded on every turn. Every token here is taxed on every request — a 5,000-token CLAUDE.md costs 5,000 tokens × 20 turns × 6 sessions = 600,000 tokens per week of build work, purely from the instruction file.

```markdown
# ReliantAI Platform — CLAUDE.md

## Repos
- reliantai/                → FastAPI + Celery + SQLAlchemy (Python 3.12)
- reliantai-website/        → Vite + React 19 (marketing, reliantai.org)
- reliantai-client-sites/   → Next.js 15 App Router (ISR sites, preview.reliantai.org)

## Hard architectural constraints — do not deviate
- No per-site builds. Client sites render via Next.js ISR from DB content only.
- Slug generation: generate_slug(business_name, city) — NEVER from place_id
- Celery Beat: reliantai/celery_app.py beat_schedule — NOT django_celery_beat
- Tool _run() methods: SYNCHRONOUS (sync httpx.Client, not async)
- Preview domain: preview.reliantai.org — NOT reliantai.org/preview/
- CopyAgent model: gemini-1.5-pro. All other agents: gemini-1.5-flash.

## Current sprint (update each session)
Phase: [fill in before each session]
Files in scope: [fill in before each session]

## Run commands
api:        uvicorn reliantai.main:app --reload --port 8000
workers:    celery -A reliantai.celery_app worker -Q agents --concurrency 2
beat:       celery -A reliantai.celery_app beat
tests:      pytest tests/ -x -v
migrate:    alembic upgrade head
```

---

### Phase Context Loading — What to Load Per Sprint Week

Never load the full `synthesized-architecture.md` into a session. It is ~25,000 tokens. Load only the section relevant to the current phase.

| Sprint Week | Section to reference | Files in scope per session |
|---|---|---|
| Week 1 — DB + Infrastructure | Flaw Register + Component 4 (ORM models) + Env vars | `reliantai/db/`, `reliantai/main.py`, `docker-compose.yml` |
| Week 2 — Agent Crew | Component 1 (SiteRegistration) + Component 3 (CopyAgent) + Component 5 (Celery) | `reliantai/agents/`, `reliantai/tasks/`, `reliantai/services/site_registration_service.py` |
| Week 3 — Client Sites | Flaw 1 fix (ISR architecture) + Component 7 (preview page) | `reliantai-client-sites/src/`, `reliantai-client-sites/src/templates/` |
| Week 4 — Outreach + Sequences | Component 6 (state machine) + Flaw 7 fix | `reliantai/services/outreach_service.py`, `reliantai/tasks/prospect_tasks.py` |
| Week 5 — Marketing Site | Component 2 (API layer) + pricing psychology section | `reliantai-website/src/components/`, `reliantai-website/src/pages/` |
| Week 6 — Hardening | Failure Mode Register + Security checklist + Env vars | All services — read-only audit |

---

### Peak-Hour Schedule for This Build

Anthropic throttles Pro quota during peak hours (5-11 AM PT weekdays). Observed allowance drops from 50-60 messages/window to 35-40 during peak.

```
Optimal session timing:
  Planning, architecture review, reading docs:   Any time (low quota use)
  Active Claude Code generation sessions:        11 AM PT onwards or weekends
  Complex multi-file refactors:                  Nights / weekends
  Agent pipeline testing (Gemini API calls):     Off-peak (Gemini has its own rate limits)
```

---

### Session Handoff Format (use at end of every session via /compact)

After `/compact`, Claude Code produces a summary. Paste it into the next session with this wrapper:

```
PREVIOUS SESSION HANDOFF:
[paste /compact output here]

CURRENT SESSION GOAL:
[single sentence — what specifically gets built today]

FILES TO TOUCH THIS SESSION:
[explicit list — 2-4 files max]

DO NOT:
[one specific anti-pattern relevant to today's work]
```

This pattern costs ~300 tokens of overhead per session and saves 15-20 turns of re-orientation.

