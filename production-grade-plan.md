# 🎯 **COMPREHENSIVE INTEGRATION PLAN: ReliantAI Platform + Website**
## *Home Services AI Marketing & Sales Automation Engine*

I'm going to build this **real-world applicable, production-grade plan** based on deep analysis of both repos. This is a **6-week, 3-phase execution roadmap** with specific code, API contracts, and workflows.

---

# **PART 0: ARCHITECTURE DECISIONS LOCKED IN** ✅

Based on your stack and my analysis:

| Decision | Rationale | Implementation |
|----------|-----------|-----------------|
| **Separate repos, API-driven integration** | Reduces coupling, allows independent deployment/scaling of website vs. platform | Website calls `reliantai/api/v2/*` endpoints via Bearer token |
| **Home services vertical only** | Highest margin, proven demand (hvac, plumbing, electrical, roofing, painting, landscaping) | Hard-code 6 trades; add new trades as data-driven expansion |
| **Preview at website, production at `.clients` subdomain** | SEO separation + lead magnet vs. client retention | Preview = ISR on reliantai.org; Prod = custom domain or *.clients.reliantai.org |
| **CrewAI + FastAPI + Celery** | Already in platform; proven for HVAC dispatch; scales horizontally | Reuse `hvac_dispatch_crew.py` pattern; extend to research/copy/build agents |

---

# **PART 1: SYSTEM ARCHITECTURE** 

## **1.1 End-to-End Data Flow**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         RELIANTAI MARKETING FUNNEL                           │
└──────────────────────────────────────────────────────────────────────────────┘

STAGE 0: AWARENESS (reliantai.org — Website Repo)
┌─────────────────────────────────────────────────────────────┐
│  Hero (trade selector) → Loss Calculator → Audit Tool       │
│  "See what {your-business} is missing on search"            │
│  ↓ CTA: "Get Your Free Preview Site"                        │
└─────────────────────────────────────────────────────────────┘
         ↓
         │ POST /api/v2/prospects/scan
         │ {trade, city, business_name, phone, email}
         ↓

STAGE 1: PROSPECT IDENTIFICATION & QUALIFICATION (Platform API)
┌─────────────────────────────────────────────────────────────┐
│ Endpoint: POST /api/v2/prospects                            │
│ ├─ Google Places lookup (verify business exists)            │
│ ├─ Extract: place_id, rating, review_count, website_url     │
│ ├─ Score opportunity gap (high reviews + weak web = high)    │
│ ├─ Save to prospects table (status=identified)              │
│ └─ Return: prospect_id, preview_url stub                    │
└─────────────────────────────────────────────────────────────┘
         ↓

STAGE 2: AUTONOMOUS RESEARCH (CrewAI Crew + Celery)
┌─────────────────────────────────────────────────────────────┐
│ Celery Task: run_prospect_pipeline(prospect_id)             │
│ ├─ Task 1: BusinessResearcher Agent                         │
│ │  └─ Google Places (reviews, photos, hours, Q&A)           │
│ │  └─ Review sentiment + themes + owner extraction          │
│ │  └─ GBP optimization score                                │
│ │  └─ Current website: PageSpeed, SSL, schema, mobile       │
│ │  └─ Social presence (Facebook, Instagram, Yelp, BBB)      │
│ │                                                            │
│ ├─ Task 2: CompetitorAnalyst Agent                          │
│ │  └─ Find top 3-5 local competitors (same trade, city)     │
│ │  └─ Gap analysis: schema, speed, AEO, review response     │
│ │  └─ Extract competitor keywords (Serper)                  │
│ │                                                            │
│ ├─ Task 3: CopyAgent (Gemini Pro)                           │
│ │  └─ Hero headline + subheadline (psychological framing)    │
│ │  └─ Service descriptions (2 sentences each, outcome-focus) │
│ │  └─ About section (owner story + trust points)            │
│ │  └─ FAQ schema (voice-search optimized)                   │
│ │  └─ Schema.org JSON-LD (LocalBusiness + trade subtype)    │
│ │  └─ Meta tags (title < 60 chars, desc < 155 chars)        │
│ │  └─ Outreach SMS + Email templates (personalized)         │
│ │  └─ All psychology: RISK lever + STATUS proof             │
│ │                                                            │
│ ├─ Task 4: SiteBuilderAgent                                 │
│ │  └─ Select trade template (hvac-reliable-blue, etc.)      │
│ │  └─ Inject all copy + schema into Next.js template        │
│ │  └─ Build: npm run build (static export)                  │
│ │  └─ Deploy to Vercel at preview_url                       │
│ │  └─ Run Lighthouse (must score 90+ mobile)                │
│ │  └─ Validate schema via Google Rich Results API           │
│ │                                                            │
│ └─ Task 5: OutreachAgent                                    │
│    └─ Send SMS + Email (Twilio + Resend)                    │
│    └─ Track delivery (SID/message ID)                       │
│    └─ Schedule follow-ups (3, 7, 14, 21 days)               │
└─────────────────────────────────────────────────────────────┘
         ↓
         │ UPDATE prospects: status=site_built → outreach_sent
         ↓

STAGE 3: PROSPECT CONVERSION (Website Preview + Stripe)
┌─────────────────────────────────────────────────────────────┐
│ Website: reliantai.org/preview/{slug}                       │
│ ├─ Embedded iframe or full-page preview of generated site    │
│ ├─ Prospect reviews preview ("See your reviews on the web")  │
│ ├─ CTA: "Get This Site — $497 One-Time" or               │
│ │        "Upgrade to Growth Plan — $297/mo"                │
│ ├─ Stripe checkout integration                              │
│ ├─ Webhook: charge_succeeded → provision_client_site        │
│ └─ Redirect to setup flow (custom domain, branding)         │
└─────────────────────────────────────────────────────────────┘
         ↓
         │ POST /webhooks/stripe
         │ ├─ Create client (stripe_customer_id, package)
         │ ├─ Update generated_site (status=purchased)
         │ ├─ Deploy production site to {slug}.clients.reliantai.org
         │ └─ Setup auto-billing
         ↓

STAGE 4: ONGOING OPTIMIZATION (Celery Beat + Scheduled Tasks)
┌─────────────────────────────────────────────────────────────┐
│ Client Site Live: {slug}.clients.reliantai.org              │
│ ├─ Weekly: GBP Post Generation (automated via CrewAI)        │
│ ├─ Monthly: SEO monitoring (keyword rankings)                │
│ ├─ Monthly: Review Response Auto-Reply (Twilio/Resend)      │
│ ├─ Ongoing: Lead Tracking (form submits, phone clicks)       │
│ ├─ Quarterly: Site Redesign Recommendations (AI analysis)    │
│ └─ Alerts: If Lighthouse drops < 85, SEO ranking declines   │
└─────────────────────────────────────────────────────────────┘
         ↓
         │ Metrics dashboard: leads, conversions, ROI
         │ (visible to both ReliantAI and client)
         ↓

STAGE 5: EXPANSION & UPSELL
┌─────────────────────────────────────────────────────────────┐
│ If client is happy (leads > threshold, site speed good):     │
│ ├─ Email: "Ready to scale? Try Premium ($697/mo)"           │
│ ├─ Include: Lead volume, keyword rankings, case study        │
│ ├─ Offer: Weekly GBP posts, phone lead routing, CRM sync     │
│ └─ One-click upgrade in dashboard                           │
└─────────────────────────────────────────────────────────────┘
```

## **1.2 Request/Response Contracts**

### **Endpoint 1: POST /api/v2/prospects**

```python
# reliantai/api/v2/prospects.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v2/prospects", tags=["prospects"])

class ProspectCreateRequest(BaseModel):
    trade: str = Field(..., description="hvac|plumbing|electrical|roofing|painting|landscaping")
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)  # US state abbrev
    business_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(None, regex=r"^\+?1?\d{10}$")
    email: EmailStr = Field(None)
    website_url: str = Field(None)
    
    # Optional: user context (for attribution)
    utm_source: str = Field(None)
    utm_campaign: str = Field(None)

class ProspectCreateResponse(BaseModel):
    prospect_id: str
    status: str  # "identified"
    preview_url: str  # reliantai.org/preview/{slug}
    created_at: datetime

@router.post("/", response_model=ProspectCreateResponse)
async def create_prospect(
    request: ProspectCreateRequest,
    background_tasks: BackgroundTasks,
    token = Depends(verify_api_key),  # Bearer token from website
):
    """
    1. Validate business exists on Google Places
    2. Save prospect record
    3. Queue research pipeline (async)
    4. Return preview URL to website
    """
    
    # Step 1: Verify via Google Places API
    places_result = await verify_place_exists(
        business_name=request.business_name,
        city=request.city,
        state=request.state,
    )
    if not places_result:
        raise HTTPException(status_code=404, detail="Business not found on Google Places")
    
    place_id = places_result["place_id"]
    rating = places_result.get("rating", 0)
    review_count = places_result.get("review_count", 0)
    website_url = places_result.get("website", request.website_url)
    
    # Step 2: Save to DB
    prospect_id = str(uuid.uuid4())
    slug = generate_slug(request.business_name, request.city)
    
    with get_db_session() as db:
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
            google_rating=rating,
            review_count=review_count,
            website_url=website_url,
            status="identified",
            created_at=datetime.utcnow(),
        )
        db.add(prospect)
        db.commit()
    
    # Step 3: Queue research pipeline
    from reliantai.tasks.prospect_tasks import run_prospect_pipeline
    background_tasks.add_task(
        run_prospect_pipeline.apply_async,
        args=[prospect_id],
        queue="agents",
    )
    
    # Step 4: Return response
    return ProspectCreateResponse(
        prospect_id=prospect_id,
        status="identified",
        preview_url=f"https://reliantai.org/preview/{slug}",
        created_at=datetime.utcnow(),
    )

def generate_slug(business_name: str, city: str) -> str:
    """Convert 'John's HVAC' + 'Houston, TX' → 'johns-hvac-houston'"""
    import re
    slug = f"{business_name.lower()}-{city.lower()}"
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:60]  # Max slug length

@router.get("/{prospect_id}/status")
async def get_prospect_status(
    prospect_id: str,
    token = Depends(verify_api_key),
):
    """Poll pipeline progress"""
    with get_db_session() as db:
        prospect = db.query(Prospect).filter_by(id=prospect_id).first()
        if not prospect:
            raise HTTPException(status_code=404)
        
        job = db.query(ResearchJob).filter_by(prospect_id=prospect_id)\
            .order_by(ResearchJob.created_at.desc()).first()
        
        return {
            "prospect_id": prospect_id,
            "status": prospect.status,
            "job_status": job.status if job else None,
            "job_step": job.step if job else None,
            "preview_url": f"https://reliantai.org/preview/{prospect.place_id[:30].lower()}",
            "error": job.error_message if job and job.status == "failed" else None,
        }
```

### **Endpoint 2: GET /preview/{slug}**

```python
# reliantai-website/src/pages/Preview.tsx
# Fetches the generated site preview from platform API

import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

export function Preview() {
  const { slug } = useParams<{ slug: string }>();
  const [generatedSite, setGeneratedSite] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // Call platform API to get preview data
    fetch(`https://api.reliantai.org/api/v2/generated-sites/${slug}`, {
      headers: {
        'Authorization': `Bearer ${process.env.REACT_APP_API_KEY}`,
      },
    })
      .then(r => r.json())
      .then(data => {
        setGeneratedSite(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [slug]);
  
  if (loading) return <div>Building your preview site...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div className="space-y-8">
      {/* Embed preview as iframe OR full render */}
      {generatedSite.preview_url && (
        <iframe 
          src={generatedSite.preview_url}
          className="w-full h-screen border-0"
          title="Preview Site"
        />
      )}
      
      {/* Metrics sidebar */}
      <div className="p-6 bg-slate-50 rounded-lg">
        <h2 className="font-bold text-lg mb-4">Your Site Metrics</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-slate-600">Lighthouse Score</p>
            <p className="text-3xl font-bold text-green-600">{generatedSite.lighthouse_score}</p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Google Rating</p>
            <p className="text-3xl font-bold text-amber-500">★ {generatedSite.google_rating}</p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Reviews</p>
            <p className="text-3xl font-bold">{generatedSite.review_count}</p>
          </div>
        </div>
      </div>
      
      {/* CTA to purchase */}
      <div className="flex gap-4">
        <button 
          onClick={() => window.location.href = `/checkout?slug=${slug}&package=starter`}
          className="flex-1 px-6 py-3 bg-blue-600 text-white font-bold rounded-lg"
        >
          Get This Site — $497 One-Time
        </button>
        <button 
          onClick={() => window.location.href = `/checkout?slug=${slug}&package=growth`}
          className="flex-1 px-6 py-3 border-2 border-blue-600 text-blue-600 font-bold rounded-lg"
        >
          Upgrade to Growth — $297/mo
        </button>
      </div>
    </div>
  );
}
```

---

# **PART 2: AGENT ARCHITECTURE** (CrewAI Crew Design)

## **2.1 The Home Services Research & Build Crew**

```python
# reliantai/agents/home_services_crew.py
"""
5-agent sequential crew for home service business site generation.
One crew instance per prospect; runs in Celery task with 15-min timeout.
"""

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
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

log = structlog.get_logger()

# ─── LLM INSTANCES ───────────────────────────────────────────
gemini_flash = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
gemini_pro = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.5)

# ─── AGENT 1: BUSINESS RESEARCHER ────────────────────────────

business_researcher = Agent(
    role="Business Intelligence Specialist",
    goal=(
        "Extract complete business profile from Google Places, reviews, and web presence. "
        "Identify emotional selling points, owner personality, service differentiation, "
        "and gaps vs. competitors. This foundation drives all subsequent copy and positioning."
    ),
    backstory=(
        "You're a marketing researcher who reads between the lines. "
        "You don't just see '47 5-star reviews' — you see the customer anxiety "
        "(burst pipe at midnight, don't know if they'll get ripped off) that those "
        "reviews solve. You extract owner names, years in business, certifications, "
        "and the specific emotional promises customers make about them. "
        "Your output is the DNA of their brand."
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

# ─── AGENT 2: COMPETITOR ANALYST ─────────────────────────────

competitor_analyst = Agent(
    role="Competitive Intelligence Specialist",
    goal=(
        "Find top 3-5 local competitors. Analyze their digital presence gaps: "
        "schema markup, mobile speed, FAQ richness, AEO signals, review response rate. "
        "Identify the specific battles {business_name} can win online that competitors "
        "are neglecting."
    ),
    backstory=(
        "You think like a battle strategist. You see websites as competitive battlefields. "
        "Most local contractors' sites are broken — slow, no schema, outdated. "
        "That's not a bug; it's an opportunity. You find the exact gaps where "
        "{business_name} can dominate search, Siri, ChatGPT, and Google Maps."
    ),
    tools=[GooglePlacesTool(), ScrapeWebsiteTool(), SerperDevTool(), PageSpeedTool()],
    llm=gemini_flash,
    verbose=True,
    allow_delegation=False,
    max_iter=5,
)

# ─── AGENT 3: COPY AGENT ─────────────────────────────────────

copy_agent = Agent(
    role="Direct-Response Copywriter",
    goal=(
        "Write all website copy, meta tags, schema.org JSON-LD, FAQ pairs, "
        "and initial outreach messages. Every word must be SPECIFIC to this business — "
        "zero template filler. Psychology framework: activate RISK (loss aversion) as primary lever, "
        "STATUS (proof) as secondary. 7th-grade reading level. Never use 'solutions'."
    ),
    backstory=(
        "You're trained on Ogilvy, Halbert, Cialdini. You understand that a homeowner "
        "with a burst pipe isn't buying a website — they're buying certainty: "
        "'This contractor will show up, fix it right, not rip me off.' "
        "Your job: make that promise unmistakable in every headline, "
        "every subheading, every schema snippet. You convert fear into confidence."
    ),
    tools=[SerperDevTool()],
    llm=gemini_pro,
    verbose=True,
    allow_delegation=False,
    max_iter=3,
)

# ─── AGENT 4: SITE BUILDER ───────────────────────────────────

site_builder_agent = Agent(
    role="Full-Stack Site Engineer",
    goal=(
        "Select the perfect trade template, inject all copy + schema, build static HTML, "
        "deploy to Vercel, run Lighthouse audit (must score 90+ mobile). "
        "Ensure AEO signals are injected as first-class features, not afterthoughts."
    ),
    backstory=(
        "You're a senior engineer who builds premium local business sites. "
        "You know that a site that scores 78 Lighthouse is a wasted opportunity. "
        "You select templates by trade (HVAC = reliable blue, Plumbing = trustworthy navy). "
        "You inject structured data like it's code, not decoration. "
        "A deployed site that doesn't pass 90+ mobile doesn't get shipped."
    ),
    tools=[VercelDeployTool(), SchemaValidatorTool()],
    llm=gemini_flash,
    verbose=True,
    allow_delegation=False,
    max_iter=3,
)

# ─── AGENT 5: OUTREACH AGENT ─────────────────────────────────

outreach_agent = Agent(
    role="Sales Development Rep",
    goal=(
        "Send personalized first-touch SMS + email to prospect. "
        "SMS < 160 chars, cite a specific review. Email < 150 words, 3 paragraphs: "
        "proof (they're good) → gap (they're missing something) → offer (low friction). "
        "Schedule follow-ups at 3, 7, 14, 21 days."
    ),
    backstory=(
        "You've sent 10,000 cold messages. You know the first message must do three things "
        "in three seconds: prove you've done homework, make a specific claim, offer next step. "
        "You don't pitch. You create curiosity and remove friction. "
        "Your 3-day follow-up feels like a helpful friend, not spam."
    ),
    tools=[TwilioSMSTool(), ResendEmailTool()],
    llm=gemini_flash,
    verbose=True,
    allow_delegation=False,
    max_iter=2,
)

# ─── TASKS ───────────────────────────────────────────────────

def build_crew_tasks(prospect_data: dict) -> list:
    """Build 5 sequential tasks for one prospect"""
    
    t_research = Task(
        description=f"""
Research {prospect_data['business_name']} ({prospect_data['trade']}) in {prospect_data['city']}, {prospect_data['state']}.

Fetch:
1. Full Google Places profile (reviews, photos, hours, Q&A)
2. Extract top 5 review themes + sentiment score (0.0-1.0)
3. Notable review quotes (max 5, verbatim)
4. Owner name (if available)
5. Years in business (estimate from review history)
6. Certifications (from website or GBP)
7. Service areas (neighborhoods served)
8. GBP completeness score
9. If website exists:
   - PageSpeed Insights (mobile score)
   - SSL certificate present?
   - Schema markup present?
   - Mobile responsive?
   - Word count, page count
10. Social presence: Facebook, Yelp, BBB, Instagram URLs (if exist)

Output: Structured JSON with all fields, verbatim quotes, and sentiment score.
        """,
        agent=business_researcher,
        expected_output="JSON: BusinessIntelligenceReport with complete profile",
    )
    
    t_competitors = Task(
        description=f"""
Find and analyze top 3-5 local competitors for {prospect_data['business_name']} ({prospect_data['trade']}) 
in {prospect_data['city']}, {prospect_data['state']}.

For each competitor:
1. Scrape their website
2. Run PageSpeed Insights (mobile + desktop)
3. Check for schema.org markup
4. Identify gaps: no schema, poor mobile speed, no FAQ, no AEO signals
5. Extract top 10 organic keywords they rank for (via Serper)
6. Score their website 1-100 (lower = more opportunity)

Identify specific gaps {prospect_data['business_name']} can exploit to rank above them.

Output: CompetitorReport array with gap_opportunities for each.
        """,
        agent=competitor_analyst,
        expected_output="JSON: CompetitorReport with gaps identified",
        context=[t_research],
    )
    
    t_copy = Task(
        description=f"""
Write ALL copy for {prospect_data['business_name']} premium website using research + competitor data.

REQUIRED SECTIONS (ALL as JSON):

1. HERO
   - headline: < 12 words, specific outcome, psychological RISK frame
   - subheadline: < 25 words, proof element (reviews, years, guarantee)
   - hero_trust_bar: ["Licensed & Insured", "{review_count}-Star Google Reviews", "Serving {city} Since {year}"]

2. SERVICES (3-6 services)
   For each: title, description (2 sentences), icon, CTA

3. ABOUT
   - story: 80-120 words, use owner name, local community reference
   - trust_points: 3 bullets (certifications, years, guarantee)

4. REVIEWS SHOWCASE
   - featured_reviews: top 3 excerpts (name + first initial only)
   - aggregate_line: "{N} homeowners in {city} give us {rating} stars"

5. FAQ (voice-search optimized, 6 QA pairs)
   - Start with: "How do I...", "What does...", "Can you...", "How much...", "Do you...", "Why..."
   - Answers: 30-60 words, conversational, include business name naturally

6. AEO ENTITY SIGNALS
   - entity_description: 2 sentences for knowledge graph
   - service_area_description: neighborhoods served
   - primary_service_query: most common question for this trade

7. SCHEMA.ORG JSON-LD (full LocalBusiness + trade subtype)
   - Include: name, address, phone, geo, hours, priceRange, aggregateRating, 
     sameAs (all social URLs), areaServed, mainEntity (FAQ schema)

8. META TAGS
   - title: < 60 chars, city + trade + keyword
   - description: < 155 chars, city, trade, review count, CTA verb

9. OUTREACH SMS (< 155 chars)
   - Reference specific review theme
   - Include: {{PREVIEW_URL}} placeholder
   - Feel human, not automated
   Example: "Hey {owner_first_name}, {review_theme} is why {city} trusts {business_name}. 
             See how your site could look: {preview_url}"

10. OUTREACH EMAIL
    - subject: < 9 words, specific, curiosity-opening
    - body: 3 paragraphs (proof → gap → offer)
    - ps: extra hook or social proof

PSYCHOLOGY FRAMEWORK:
- Primary lever: RISK (homeowner's fear of wrong contractor)
- Secondary lever: STATUS (neighbors' trust, reviews prove it)
- Awareness: PROBLEM AWARE (they know they need a site, don't know how good yours can be)

Output: JSON: SiteCopyPackage with all 10 sections.
        """,
        agent=copy_agent,
        expected_output="JSON: SiteCopyPackage with all 10 sections",
        context=[t_research, t_competitors],
    )
    
    t_build = Task(
        description=f"""
Build and deploy preview site for {prospect_data['business_name']} ({prospect_data['slug']}).

Steps:
1. Select template by trade:
   hvac → hvac-reliable-blue
   plumbing → plumbing-trustworthy-navy
   electrical → electrical-sharp-gold
   roofing → roofing-bold-copper
   painting → painting-clean-minimal
   landscaping → landscaping-earthy-green

2. Copy template to temp directory

3. Inject SiteCopyPackage into template data file (site-content.json)

4. Validate Schema.org JSON-LD via Google Rich Results Test API

5. Build: npm run build (static export)

6. Deploy to Vercel via Deploy API
   - Project name: client-{slug}
   - URL: https://reliantai.org/preview/{slug}

7. Run Lighthouse CI on deployed URL
   - Must score 90+ on mobile performance
   - If < 90: optimize images/JS, retry once
   - If still < 90: FAIL and report errors

8. Return: preview_url, vercel_deployment_id, lighthouse_score, build_time_sec

Output: JSON deployment result.
        """,
        agent=site_builder_agent,
        expected_output="JSON: {preview_url, vercel_deployment_id, lighthouse_score, build_time_sec}",
        context=[t_copy],
    )
    
    t_outreach = Task(
        description=f"""
Send first-touch outreach to {prospect_data['business_name']}.

Using:
- Outreach SMS + Email from SiteCopyPackage
- Preview URL from site build
- Phone: {prospect_data.get('phone', 'none')}
- Email: {prospect_data.get('email', 'none')}

Steps:
1. Replace {{PREVIEW_URL}} in SMS/email with actual preview_url

2. If phone: Send SMS via Twilio
   - From: {TWILIO_FROM_NUMBER}
   - Track: message SID

3. If email: Send via Resend
   - From: DouglasMitchell@reliantai.org (or your brand email)
   - Track: message ID

4. Write to outreach_messages table (status=sent)

5. Create outreach_sequence for follow-ups:
   - Step 0: sent (just now)
   - Step 1: 3 days
   - Step 2: 7 days
   - Step 3: 14 days
   - Step 4: 21 days
   Schedule each as Celery Beat task

Output: JSON: {{sent_sms, sms_sid, sent_email, email_id, follow_up_scheduled_at}}
        """,
        agent=outreach_agent,
        expected_output="JSON: {sent_sms, sms_sid, sent_email, email_id, follow_up_scheduled_at}",
        context=[t_copy, t_build],
    )
    
    return [t_research, t_competitors, t_copy, t_build, t_outreach]

def create_home_services_crew(prospect_data: dict) -> Crew:
    """Instantiate and return the crew"""
    tasks = build_crew_tasks(prospect_data)
    return Crew(
        agents=[business_researcher, competitor_analyst, copy_agent, site_builder_agent, outreach_agent],
        tasks=tasks,
        process=Process.sequential,  # Run in order: research → competitors → copy → build → outreach
        verbose=True,
        memory=True,  # CrewAI's internal context passing
        embedder={"provider": "google", "config": {"model": "models/text-embedding-004"}},
        max_rpm=10,  # Rate limit for Gemini API
    )
```

---

# **PART 3: TOOL IMPLEMENTATIONS** (Real Code)

## **3.1 Google Places Tool**

```python
# reliantai/agents/tools/google_places.py

from crewai_tools import BaseTool
import httpx
import os
from typing import Optional

class GooglePlacesTool(BaseTool):
    name: str = "google_places_search"
    description: str = (
        "Search Google Places for businesses. Returns: place_id, name, address, "
        "phone, rating, review_count, website, hours, photos, Q&A. "
        "Use for finding prospects and competitors."
    )
    
    async def _run(
        self,
        query: Optional[str] = None,
        place_id: Optional[str] = None,
        location: Optional[str] = None,
        radius: int = 16000,
    ) -> str:
        """
        Search by query OR fetch details by place_id.
        Example query: "HVAC repair Houston TX"
        """
        api_key = os.environ["GOOGLE_PLACES_API_KEY"]
        
        if place_id:
            # Get full place details (reviews, Q&A, hours, etc.)
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://maps.googleapis.com/maps/api/place/details/json",
                    params={
                        "place_id": place_id,
                        "key": api_key,
                        "fields": (
                            "reviews,name,rating,user_ratings_total,"
                            "formatted_phone_number,website,opening_hours,"
                            "address_components,geometry,photos,business_status,"
                            "editorial_summary,price_level,formatted_address"
                        ),
                        "reviews_sort": "most_relevant",
                    }
                )
            result = resp.json().get("result", {})
            
            return self._format_details(result)
        
        elif query:
            # Text search
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://maps.googleapis.com/maps/api/place/textsearch/json",
                    params={
                        "query": query,
                        "key": api_key,
                        "fields": (
                            "place_id,name,formatted_address,formatted_phone_number,"
                            "rating,user_ratings_total,website,geometry,photos,business_status"
                        ),
                        "location": location,
                        "radius": radius,
                    }
                )
            
            results = resp.json().get("results", [])
            return self._format_search_results(results)
        
        return "Error: provide query or place_id"
    
    def _format_details(self, place: dict) -> str:
        """Format place details for agent consumption"""
        reviews = place.get("reviews", [])
        top_reviews = []
        for r in reviews[:5]:
            top_reviews.append({
                "author": r.get("author_name"),
                "rating": r.get("rating"),
                "text": r.get("text"),
                "time": r.get("relative_time_description"),
            })
        
        return str({
            "place_id": place.get("place_id"),
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "phone": place.get("formatted_phone_number"),
            "website": place.get("website"),
            "rating": place.get("rating"),
            "review_count": place.get("user_ratings_total"),
            "top_reviews": top_reviews,
            "hours": place.get("opening_hours", {}).get("weekday_text", []),
            "photos_count": len(place.get("photos", [])),
            "price_level": place.get("price_level"),
            "status": place.get("business_status"),
        })
    
    def _format_search_results(self, results: list) -> str:
        """Format search results for agent"""
        formatted = []
        for r in results[:20]:
            formatted.append({
                "place_id": r.get("place_id"),
                "name": r.get("name"),
                "address": r.get("formatted_address"),
                "rating": r.get("rating", 0),
                "review_count": r.get("user_ratings_total", 0),
                "lat": r.get("geometry", {}).get("location", {}).get("lat"),
                "lng": r.get("geometry", {}).get("location", {}).get("lng"),
            })
        return str(formatted)
```

## **3.2 Vercel Deploy Tool**

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
from datetime import datetime

class VercelDeployTool(BaseTool):
    name: str = "vercel_deploy_site"
    description: str = (
        "Deploy a Next.js static site to Vercel. "
        "Returns: preview_url, deployment_id, lighthouse_score, build_time_sec"
    )
    
    TEMPLATES_DIR = Path(os.environ.get("SITE_TEMPLATES_DIR", "/opt/reliantai/site-templates"))
    
    async def _run(self, slug: str, template_id: str, site_content: dict) -> str:
        """
        1. Copy template to temp dir
        2. Inject site_content.json
        3. Build with Next.js
        4. Deploy to Vercel
        5. Run Lighthouse
        """
        
        template_path = self.TEMPLATES_DIR / template_id
        if not template_path.exists():
            return json.dumps({"error": f"Template {template_id} not found"})
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            site_dir = Path(tmp_dir) / slug
            
            # Copy template
            shutil.copytree(str(template_path), str(site_dir))
            
            # Inject content
            content_file = site_dir / "src" / "data" / "site-content.json"
            content_file.parent.mkdir(parents=True, exist_ok=True)
            content_file.write_text(json.dumps(site_content, indent=2))
            
            # Build
            build_start = datetime.utcnow()
            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(site_dir),
                capture_output=True,
                text=True,
                timeout=300,
            )
            build_time_sec = (datetime.utcnow() - build_start).total_seconds()
            
            if build_result.returncode != 0:
                return json.dumps({
                    "error": "build_failed",
                    "stderr": build_result.stderr[-1000:],
                    "build_time_sec": build_time_sec,
                })
            
            # Deploy via Vercel CLI
            deploy_result = subprocess.run(
                [
                    "vercel", "deploy", "--prod", "--yes",
                    "--name", f"client-{slug}",
                    "--token", os.environ["VERCEL_TOKEN"],
                    "--project", os.environ["VERCEL_PROJECT_NAME"],
                ],
                cwd=str(site_dir),
                capture_output=True,
                text=True,
                timeout=180,
            )
            
            if deploy_result.returncode != 0:
                return json.dumps({
                    "error": "deploy_failed",
                    "stderr": deploy_result.stderr[-1000:],
                })
            
            # Extract URL from vercel output
            deployment_url = deploy_result.stdout.strip().split("\n")[-1]
            
            # Run Lighthouse
            lighthouse_score = await self._run_lighthouse(deployment_url)
            
            if lighthouse_score < 90:
                # Retry once with optimization
                await self._optimize_and_rebuild(site_dir)
                lighthouse_score = await self._run_lighthouse(deployment_url)
            
            return json.dumps({
                "preview_url": deployment_url,
                "vercel_deployment_id": deployment_url.split("/")[-1],
                "lighthouse_score": lighthouse_score,
                "build_time_sec": build_time_sec,
                "build_success": lighthouse_score >= 90,
            })
    
    async def _run_lighthouse(self, url: str) -> int:
        """Run Lighthouse audit and return mobile performance score"""
        try:
            result = subprocess.run(
                [
                    "lighthouse",
                    url,
                    "--output=json",
                    "--quiet",
                    "--chrome-flags=--headless --no-sandbox",
                    "--only-categories=performance",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                score = int(data["categories"]["performance"]["score"] * 100)
                return score
        except Exception as e:
            print(f"Lighthouse error: {e}")
        
        return 0
    
    async def _optimize_and_rebuild(self, site_dir: Path):
        """Compress images, minify JS, reduce bundle size"""
        # Placeholder: real implementation would use sharp, terser, etc.
        pass
```

## **3.3 GBP Scraper Tool**

```python
# reliantai/agents/tools/gbp_scraper.py

from crewai_tools import BaseTool
import httpx
import os
from bs4 import BeautifulSoup

class GBPScraperTool(BaseTool):
    name: str = "gbp_scraper"
    description: str = (
        "Extract Google Business Profile data: posts, Q&A, photos, "
        "completeness score, review response rate."
    )
    
    async def _run(self, place_id: str) -> str:
        """
        Fetch GBP data for a place_id.
        Since Google Business API is restricted, we scrape public GBP page.
        """
        
        # Get place details first
        api_key = os.environ["GOOGLE_PLACES_API_KEY"]
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={
                    "place_id": place_id,
                    "key": api_key,
                    "fields": "website,photos,editorial_summary",
                }
            )
            place = resp.json().get("result", {})
        
        # Construct Google Maps URL for this place
        gmaps_url = f"https://maps.google.com/maps?cid={place_id}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(gmaps_url)
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Extract: posts count, Q&A count, photo count, completeness
        gbp_data = {
            "posts_count": self._extract_posts_count(soup),
            "qa_count": self._extract_qa_count(soup),
            "photo_count": len(place.get("photos", [])),
            "completeness_pct": self._estimate_completeness(place),
            "review_response_rate": self._estimate_review_response_rate(place),
        }
        
        return str(gbp_data)
    
    def _extract_posts_count(self, soup: BeautifulSoup) -> int:
        # Parse GBP posts section
        return 0  # Placeholder
    
    def _extract_qa_count(self, soup: BeautifulSoup) -> int:
        # Parse Q&A section
        return 0  # Placeholder
    
    def _estimate_completeness(self, place: dict) -> int:
        """Estimate GBP profile completeness (0-100)"""
        score = 0
        if place.get("name"): score += 10
        if place.get("formatted_address"): score += 10
        if place.get("formatted_phone_number"): score += 10
        if place.get("website"): score += 10
        if place.get("opening_hours"): score += 10
        if place.get("photos"): score += 20
        if place.get("editorial_summary"): score += 20
        return min(score, 100)
    
    def _estimate_review_response_rate(self, place: dict) -> float:
        """Estimate % of reviews with owner response"""
        reviews = place.get("reviews", [])
        if not reviews:
            return 0.0
        responded = sum(1 for r in reviews if r.get("reviewer_response"))
        return (responded / len(reviews)) * 100
```

---

# **PART 4: DATABASE SCHEMA** (Enhanced)

```python
# reliantai/db/models.py
"""SQLAlchemy models for home services lead generation"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean,
    ForeignKey, ARRAY, JSON, DECIMAL, Index, CheckConstraint,
    create_engine, event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Prospect(Base):
    __tablename__ = "prospects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    place_id = Column(String, unique=True, nullable=False)
    
    # Business info
    business_name = Column(String(200), nullable=False)
    trade = Column(String(50), nullable=False)  # hvac|plumbing|electrical|roofing|painting|landscaping
    phone = Column(String(20))
    email = Column(String(120))
    address = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zip = Column(String(10))
    lat = Column(DECIMAL(9, 6))
    lng = Column(DECIMAL(9, 6))
    
    # Google signals
    google_rating = Column(DECIMAL(2, 1))
    review_count = Column(Integer, default=0)
    website_url = Column(String(500))
    website_score = Column(Integer)  # 0-100, lower = more opportunity
    
    # Status tracking
    status = Column(String(50), default="identified")  # identified → researched → site_built → outreach_sent → responded → converted
    disqualify_reason = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    research_jobs = relationship("ResearchJob", back_populates="prospect", cascade="all, delete-orphan")
    business_intel = relationship("BusinessIntelligence", uselist=False, back_populates="prospect", cascade="all, delete-orphan")
    competitors = relationship("CompetitorIntelligence", back_populates="prospect", cascade="all, delete-orphan")
    generated_site = relationship("GeneratedSite", uselist=False, back_populates="prospect", cascade="all, delete-orphan")
    outreach_sequences = relationship("OutreachSequence", back_populates="prospect", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_prospects_trade_city", "trade", "city"),
        Index("ix_prospects_status", "status"),
    )

class ResearchJob(Base):
    __tablename__ = "research_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    celery_task_id = Column(String, unique=True)
    
    status = Column(String(50), default="queued")  # queued | running | completed | failed | retrying
    step = Column(String(100))  # which agent is active
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    prospect = relationship("Prospect", back_populates="research_jobs")

class BusinessIntelligence(Base):
    __tablename__ = "business_intelligence"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Review analysis
    top_review_themes = Column(ARRAY(String))  # ['fast response', 'clean work', ...]
    sentiment_score = Column(DECIMAL(3, 2))  # 0.0 to 1.0
    star_distribution = Column(JSON)  # {"5": 40, "4": 12, "3": 2, ...}
    notable_quotes = Column(ARRAY(String))  # Top 5 review excerpts
    
    # Business profile
    years_in_business = Column(Integer)
    certifications = Column(ARRAY(String))
    service_areas = Column(ARRAY(String))
    services_offered = Column(ARRAY(String))
    owner_name = Column(String(200))
    owner_title = Column(String(100))
    
    # Digital footprint
    facebook_url = Column(String(500))
    instagram_url = Column(String(500))
    yelp_url = Column(String(500))
    bbb_url = Column(String(500))
    has_photos = Column(Boolean, default=False)
    photo_count = Column(Integer, default=0)
    
    # GBP signals
    gbp_posts_count = Column(Integer, default=0)
    gbp_qa_count = Column(Integer, default=0)
    gbp_completeness_pct = Column(Integer)  # 0-100
    gbp_review_response_rate = Column(DECIMAL(5, 2))  # 0-100%
    
    # Website analysis
    site_page_speed = Column(Integer)  # PageSpeed mobile score
    site_has_ssl = Column(Boolean)
    site_has_schema = Column(Boolean)
    site_has_gmb = Column(Boolean)
    site_word_count = Column(Integer)
    site_has_mobile = Column(Boolean)
    site_last_updated = Column(String(100))  # "Updated 3 years ago" etc.
    
    # Full payload (for audit trail)
    raw_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    prospect = relationship("Prospect", back_populates="business_intel")

class CompetitorIntelligence(Base):
    __tablename__ = "competitor_intelligence"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    
    competitor_place_id = Column(String, nullable=False)
    competitor_name = Column(String(200), nullable=False)
    competitor_rating = Column(DECIMAL(2, 1))
    competitor_review_count = Column(Integer)
    competitor_website = Column(String(500))
    competitor_rank_position = Column(Integer)  # Where they rank on local search
    
    # Gap analysis
    missing_schema = Column(Boolean, default=False)
    missing_reviews_response = Column(Boolean, default=False)
    missing_aeo_signals = Column(Boolean, default=False)
    site_speed_score = Column(Integer)
    site_mobile_friendly = Column(Boolean)
    
    # Opportunities
    top_keywords = Column(ARRAY(String))
    gap_opportunities = Column(ARRAY(String))  # ["Add FAQ schema", "Mobile optimization", ...]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    prospect = relationship("Prospect", back_populates="competitors")

class GeneratedSite(Base):
    __tablename__ = "generated_sites"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("prospects.id", ondelete="CASCADE"), unique=True)
    client_id = Column(String, ForeignKey("clients.id", ondelete="SET NULL"))
    
    slug = Column(String(100), unique=True, nullable=False)
    template_id = Column(String(100), nullable=False)  # hvac-reliable-blue, etc.
    
    # URLs
    preview_url = Column(String(500))
    production_url = Column(String(500))
    custom_domain = Column(String(500))
    
    # Vercel deployment
    vercel_project_id = Column(String(100))
    vercel_deployment_id = Column(String(100))
    vercel_deploy_status = Column(String(50))  # ready | building | error
    
    # Content (stored as JSON for versioning)
    site_content = Column(JSON, nullable=False)
    site_config = Column(JSON, nullable=False)
    
    # SEO metadata
    schema_org_json = Column(JSON)
    meta_title = Column(String(60))
    meta_description = Column(String(155))
    
    # Metrics
    status = Column(String(50), default="building")  # building | preview_live | purchased | production_live | suspended
    build_time_sec = Column(Integer)
    lighthouse_score = Column(Integer)
    page_speed_mobile = Column(Integer)
    page_speed_desktop = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    prospect = relationship("Prospect", back_populates="generated_site")
    client = relationship("Client")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("prospects.id"))
    
    stripe_customer_id = Column(String(100), unique=True)
    stripe_subscription_id = Column(String(100))
    
    package = Column(String(50), nullable=False)  # starter | growth | premium
    package_price = Column(Integer, nullable=False)  # cents
    
    business_name = Column(String(200), nullable=False)
    owner_name = Column(String(200))
    email = Column(String(120), nullable=False)
    phone = Column(String(20))
    
    onboard_status = Column(String(50), default="pending")  # pending | completed
    onboard_completed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String, ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False)
    
    channel = Column(String(50), nullable=False)  # sms | email
    sequence_template = Column(String(100), nullable=False)
    
    status = Column(String(50), default="active")  # active | completed | unsubscribed | converted | paused
    
    current_step = Column(Integer, default=0)
    max_steps = Column(Integer, nullable=False)
    
    next_send_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    prospect = relationship("Prospect", back_populates="outreach_sequences")
    messages = relationship("OutreachMessage", back_populates="sequence")

class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_id = Column(String, ForeignKey("outreach_sequences.id", ondelete="CASCADE"))
    prospect_id = Column(String, ForeignKey("prospects.id", ondelete="CASCADE"))
    
    step_number = Column(Integer, nullable=False)
    channel = Column(String(50), nullable=False)  # sms | email
    direction = Column(String(50), default="outbound")  # outbound | inbound
    
    to_address = Column(String(500), nullable=False)
    from_address = Column(String(500), nullable=False)
    subject = Column(String(200))
    body = Column(Text, nullable=False)
    
    # Delivery tracking
    provider_message_id = Column(String(200))  # Twilio SID or Resend ID
    status = Column(String(50), default="queued")  # queued | sent | delivered | failed | opened | clicked | replied
    
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)
    
    response_body = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sequence = relationship("OutreachSequence", back_populates="messages")

class LeadEvent(Base):
    __tablename__ = "lead_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("generated_sites.id"))
    client_id = Column(String, ForeignKey("clients.id"))
    
    event_type = Column(String(50), nullable=False)  # page_view | cta_click | form_submit | phone_click
    visitor_id = Column(String(200))  # Anonymous fingerprint
    
    page = Column(String(500))
    referrer = Column(String(500))
    utm_source = Column(String(100))
    utm_campaign = Column(String(100))
    
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

# **PART 5: CELERY TASK ORCHESTRATION**

```python
# reliantai/tasks/prospect_tasks.py
"""Celery tasks for autonomous prospect pipeline"""

from celery import shared_task, chain, group
from celery.utils.log import get_task_logger
from reliantai.agents.home_services_crew import create_home_services_crew
from reliantai.db import get_db_session
from reliantai.models import ResearchJob, Prospect, GeneratedSite, OutreachSequence
from datetime import datetime, timedelta
import structlog

log = get_task_logger(__name__)
logger = structlog.get_logger()

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    soft_time_limit=900,    # 15 min soft kill
    time_limit=1200,        # 20 min hard kill
    queue="agents",
    name="prospect_tasks.run_prospect_pipeline",
)
def run_prospect_pipeline(self, prospect_id: str):
    """
    FULL AUTONOMOUS PIPELINE: research → competitors → copy → build → outreach
    
    Timeline: ~12-15 minutes per prospect (dominated by Vercel build + Lighthouse)
    Error handling: Retry 3x on failure, capture error_message
    """
    
    with get_db_session() as db:
        prospect = db.query(Prospect).filter_by(id=prospect_id).first()
        if not prospect:
            logger.error("prospect_not_found", prospect_id=prospect_id)
            return {"error": "prospect_not_found"}
        
        # Create research job record
        job = ResearchJob(
            prospect_id=prospect_id,
            celery_task_id=self.request.id,
            status="running",
            step="business_research",
            started_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
    
    try:
        # Prepare prospect data for crew
        prospect_data = {
            "place_id": prospect.place_id,
            "business_name": prospect.business_name,
            "trade": prospect.trade,
            "city": prospect.city,
            "state": prospect.state,
            "phone": prospect.phone,
            "email": prospect.email,
            "address": prospect.address,
            "website_url": prospect.website_url,
            "slug": prospect.place_id[:30].lower().replace(" ", "-"),
        }
        
        # Instantiate and run crew
        crew = create_home_services_crew(prospect_data)
        result = crew.kickoff()
        
        # Parse crew output (each agent's output flows to next)
        # Result structure:
        # {
        #   "research": {...BusinessIntelligenceReport...},
        #   "competitors": {...CompetitorReport...},
        #   "copy": {...SiteCopyPackage...},
        #   "build": {...DeploymentResult...},
        #   "outreach": {...OutreachResult...},
        # }
        
        # Update DB
        with get_db_session() as db:
            job = db.query(ResearchJob).filter_by(celery_task_id=self.request.id).first()
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
            prospect = db.query(Prospect).filter_by(id=prospect_id).first()
            prospect.status = "outreach_sent"
            prospect.updated_at = datetime.utcnow()
            db.commit()
        
        logger.info(
            "pipeline_completed",
            prospect_id=prospect_id,
            task_id=self.request.id,
            result_summary=str(result)[:200],
        )
        
        return {
            "status": "completed",
            "prospect_id": prospect_id,
            "preview_url": result.get("build", {}).get("preview_url"),
        }
    
    except Exception as exc:
        with get_db_session() as db:
            job = db.query(ResearchJob).filter_by(celery_task_id=self.request.id).first()
            if job:
                job.status = "failed"
                job.error_message = str(exc)[:500]
                job.retry_count = self.request.retries
                db.commit()
        
        logger.error(
            "pipeline_failed",
            prospect_id=prospect_id,
            task_id=self.request.id,
            error=str(exc),
            retry_count=self.request.retries,
        )
        raise


@shared_task(
    bind=True,
    queue="outreach",
    soft_time_limit=120,
    name="prospect_tasks.send_follow_up_message",
)
def send_follow_up_message(self, sequence_id: str, step_number: int):
    """
    Send follow-up message (step 1, 2, 3, or 4).
    Scheduled via Celery Beat at next_send_at time.
    """
    from reliantai.services.outreach_service import OutreachService
    
    with get_db_session() as db:
        sequence = db.query(OutreachSequence).filter_by(id=sequence_id).first()
        if not sequence:
            logger.error("sequence_not_found", sequence_id=sequence_id)
            return
        
        if sequence.status != "active":
            logger.info("sequence_not_active", sequence_id=sequence_id, status=sequence.status)
            return
        
        OutreachService.execute_step(db, sequence_id, step_number)


@shared_task(
    queue="outreach",
    name="prospect_tasks.process_inbound_response",
)
def process_inbound_response(phone: str, body: str, provider_message_id: str):
    """
    Inbound SMS reply from Twilio webhook.
    Route: unsubscribe | hot_lead | auto_response
    """
    from reliantai.services.outreach_service import OutreachService
    
    body_lower = body.lower().strip()
    
    # Check for unsubscribe
    stop_words = {"stop", "unsubscribe", "quit", "cancel", "end", "no"}
    if any(word in body_lower for word in stop_words):
        OutreachService.handle_unsubscribe(phone)
        return
    
    # Flag as hot lead
    OutreachService.flag_hot_lead(phone, body)


# Scheduled tasks (via Celery Beat)

@shared_task(queue="outreach", name="prospect_tasks.process_scheduled_followups")
def process_scheduled_followups():
    """
    Run every 5 minutes. Find all sequences with next_send_at <= now and status=active.
    Queue follow-up message tasks.
    """
    from datetime import datetime
    
    with get_db_session() as db:
        now = datetime.utcnow()
        due_sequences = db.query(OutreachSequence).filter(
            OutreachSequence.next_send_at <= now,
            OutreachSequence.status == "active",
        ).all()
        
        for seq in due_sequences:
            logger.info(
                "queuing_followup",
                sequence_id=seq.id,
                step=seq.current_step + 1,
            )
            send_follow_up_message.apply_async(
                args=[seq.id, seq.current_step + 1],
                queue="outreach",
            )
```

---

# **PART 6: WEBSITE INTEGRATION (React Component)**

```typescript
// reliantai-website/src/components/QuickPreviewForm.tsx
/**
 * Home page form: "See what you're missing on search"
 * Collects: trade, city, business name, phone/email
 * Calls: POST /api/v2/prospects
 * Returns: preview_url
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const TRADES = [
  { value: 'hvac', label: 'HVAC/Heating & Cooling' },
  { value: 'plumbing', label: 'Plumbing' },
  { value: 'electrical', label: 'Electrical' },
  { value: 'roofing', label: 'Roofing' },
  { value: 'painting', label: 'Painting' },
  { value: 'landscaping', label: 'Landscaping' },
];

const US_STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', ...]; // All 50

export function QuickPreviewForm() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [form, setForm] = useState({
    trade: '',
    business_name: '',
    city: '',
    state: '',
    phone: '',
    email: '',
  });
  
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v2/prospects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.REACT_APP_API_KEY}`,
        },
        body: JSON.stringify(form),
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to create preview');
      }
      
      const data = await response.json();
      
      // Redirect to preview page
      navigate(`/preview/${data.preview_url.split('/').pop()}`);
    
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }
  
  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto space-y-4 p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold">See Your Free Preview Site</h2>
      <p className="text-gray-600">Takes 2-3 minutes. No credit card required.</p>
      
      <div>
        <label className="block text-sm font-medium">Trade</label>
        <select
          value={form.trade}
          onChange={(e) => setForm({...form, trade: e.target.value})}
          required
          className="w-full px-3 py-2 border rounded"
        >
          <option value="">Select your trade...</option>
          {TRADES.map(t => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </div>
      
      <div>
        <label className="block text-sm font-medium">Business Name</label>
        <input
          type="text"
          value={form.business_name}
          onChange={(e) => setForm({...form, business_name: e.target.value})}
          placeholder="e.g., John's HVAC"
          required
          className="w-full px-3 py-2 border rounded"
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium">City</label>
          <input
            type="text"
            value={form.city}
            onChange={(e) => setForm({...form, city: e.target.value})}
            placeholder="Houston"
            required
            className="w-full px-3 py-2 border rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">State</label>
          <select
            value={form.state}
            onChange={(e) => setForm({...form, state: e.target.value})}
            required
            className="w-full px-3 py-2 border rounded"
          >
            <option value="">State</option>
            {US_STATES.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium">Phone (optional)</label>
        <input
          type="tel"
          value={form.phone}
          onChange={(e) => setForm({...form, phone: e.target.value})}
          placeholder="(555) 123-4567"
          className="w-full px-3 py-2 border rounded"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium">Email (optional)</label>
        <input
          type="email"
          value={form.email}
          onChange={(e) => setForm({...form, email: e.target.value})}
          placeholder="owner@business.com"
          className="w-full px-3 py-2 border rounded"
        />
      </div>
      
      {error && <div className="p-3 bg-red-100 text-red-700 rounded">{error}</div>}
      
      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-3 bg-blue-600 text-white font-bold rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Building your preview...' : 'Get My Free Preview Site'}
      </button>
    </form>
  );
}
```

---

# **PART 7: EXECUTION ROADMAP** (6 Weeks)

## **Week 1: Foundation & Integration Setup**

- [ ] **Day 1-2**: Create API layer (`reliantai/api/v2/prospects.py`, `/preview/{slug}`)
- [ ] **Day 2-3**: Implement Prospect model + migration (`reliantai/db/models.py`)
- [ ] **Day 3-4**: Build GooglePlacesTool + GBPScraperTool
- [ ] **Day 4-5**: Wire website form → platform API (QuickPreviewForm.tsx)
- [ ] **Day 5**: Test end-to-end: website form → API → DB ✅

**Deliverable**: Website can create prospect records; API validates business exists

---

## **Week 2: Agent Crew Architecture**

- [ ] **Day 1-2**: Implement BusinessResearcher agent + tests
- [ ] **Day 2-3**: Implement CompetitorAnalyst agent
- [ ] **Day 3**: Implement CopyAgent (copy generation)
- [ ] **Day 4**: Implement SiteBuilderAgent (template injection + Vercel deploy)
- [ ] **Day 5**: Implement OutreachAgent (SMS + email templates)
- [ ] **Day 5**: Test crew on 3 real prospects (Houston HVAC, San Antonio plumbing, Dallas roofing)

**Deliverable**: Full crew runs end-to-end; generates preview URLs

---

## **Week 3: Site Templates & Theme System**

- [ ] **Day 1**: Build `hvac-reliable-blue` template (Next.js static, Framer-quality)
- [ ] **Day 2**: Build `plumbing-trustworthy-navy` template
- [ ] **Day 3**: Build `electrical-sharp-gold`, `roofing-bold-copper` templates
- [ ] **Day 4**: Build `painting-clean-minimal`, `landscaping-earthy-green` templates
- [ ] **Day 5**: Test SiteContent injection into all 6 templates; verify Lighthouse 90+

**Deliverable**: 6 trade-specific templates; all pass Lighthouse; preview sites live at reliantai.org/preview/{slug}

---

## **Week 4: Outreach & Follow-Up Automation**

- [ ] **Day 1-2**: Implement Twilio SMS integration (OutreachAgent)
- [ ] **Day 2-3**: Implement Resend email integration
- [ ] **Day 3-4**: Build OutreachSequence + multi-touch scheduler (Celery Beat)
- [ ] **Day 4-5**: Implement inbound SMS routing (Twilio webhook → process_inbound_response)
- [ ] **Day 5**: Test: send SMS + email, verify delivery tracking, schedule follow-ups

**Deliverable**: Autonomous outreach pipeline works; prospects receive SMS + email; follow-ups scheduled

---

## **Week 5: Stripe Integration & Client Conversion**

- [ ] **Day 1**: Design pricing page (3 tiers: Starter/$497, Growth/$297mo, Premium/$697mo)
- [ ] **Day 2**: Implement Stripe checkout (reliantai-website)
- [ ] **Day 3**: Wire Stripe webhooks → provision_client_site task
- [ ] **Day 4**: Implement post-purchase client onboarding flow
- [ ] **Day 5**: Deploy production site to `{slug}.clients.reliantai.org` on purchase

**Deliverable**: Full funnel: preview → checkout → production site live

---

## **Week 6: Polish, Testing & Launch**

- [ ] **Day 1-2**: End-to-end testing (20 prospects across 3 cities, 6 trades)
- [ ] **Day 2-3**: Security audit (API auth, Twilio/Stripe secrets, GDPR compliance)
- [ ] **Day 3**: Load test: 10 concurrent pipelines
- [ ] **Day 4**: Dashboard: client metrics, lead tracking, ROI
- [ ] **Day 5**: Launch! 🚀

**Deliverable**: Production-ready system; launch to first 50 prospects

---

# **PART 8: SECURITY & COMPLIANCE CHECKLIST**

- [ ] **API Auth**: All endpoints require Bearer token (JWT from integration/auth service)
- [ ] **Twilio Verification**: Validate X-Twilio-Signature header on all inbound SMS
- [ ] **Stripe Verification**: Validate stripe-signature header on all webhooks
- [ ] **GDPR/TCPA Compliance**:
  - [ ] Phone number validation (E.164 format, no landlines)
  - [ ] Pre-send opt-out check (STOP, UNSUBSCRIBE, etc.)
  - [ ] Automatic unsubscribe on inbound STOP
  - [ ] Business identity in all SMS ("— Douglas, ReliantAI")
  - [ ] Unsubscribe link in all emails
- [ ] **Data Encryption**: All API calls use HTTPS; secrets in Vault
- [ ] **Rate Limiting**: 100 req/min per IP (public); 1000 req/min (authenticated)
- [ ] **Audit Logging**: All prospect creates/updates logged with correlation_id

---

# **PART 9: KEY SUCCESS METRICS**

| Metric | Target | How Measured |
|--------|--------|--------------|
| **Prospect → Preview** | < 3 min | Celery task duration |
| **Preview → Checkout** | 10-15% conversion | Google Analytics event |
| **Checkout → Live Production** | 100% | Stripe webhook trigger |
| **SMS Delivery** | > 98% | Twilio delivery receipts |
| **Email Delivery** | > 95% | Resend delivery tracking |
| **Follow-up Open Rate** | > 25% | Email open tracking |
| **Hot Lead Response** | < 5% | Manual reply to SMS/email |
| **Lighthouse Score** | 90+ mobile | Lighthouse CI per deployment |
| **Site Speed (mobile)** | < 2.5s LCP | PageSpeed Insights |
| **Prospect Close Rate** | 5-10% | Converted to paid client |
| **Customer Lifetime Value** | $2,400+ | Avg 12-month subscription |

---

# **FINAL RECOMMENDATIONS**

1. **Start with Week 1** — Get API + website integration working first. Everything flows from there.
2. **Test agents early** — By end of Week 2, you should have generated 3 real sites. Iterate on copy prompts.
3. **Template quality over quantity** — One perfect HVAC template beats 6 mediocre ones. Ship HVAC + Plumbing first.
4. **Monitor Twilio/Gemini costs** — Set budget alerts. Prospect research is API-heavy.
5. **Track everything** — Add correlation_id to every Celery task, API request, and outreach message. Debugging is 10x easier.

---