# Product Hunt Launch: Citadel

---

## Tagline (60 chars max)

> Open-source outbound lead gen. Scrape, score, build sites, email—locally.

---

## Description (260 chars max)

> Citadel automates outbound for local service businesses. Scrape websites, score leads with Census data, generate custom sites, and draft structured outreach—all local, zero SaaS costs. Python + SQLite + 34 tests. The agency stack you actually own.

---

## Full Description

**The $3,000/year problem:**

Lead generation shouldn't require 5 SaaS subscriptions. But that's what agencies pay: Clay for enrichment, Durable for sites, Instantly for email, Apollo for data. Your customer data lives in 5 clouds. Your costs scale with your success.

**Citadel is the alternative.**

One Python pipeline. Local SQLite. Zero mandatory cloud dependencies. Scrape websites, score leads using free Census market data, generate production-ready static sites, and draft 7-beat structured outreach emails.

**What makes it different:**

🔒 **Privacy-first** - All data stays on your machine. No cloud uploads. No "account reviews."

💰 **Zero SaaS costs** - No per-seat pricing. No API limits. Run 10 leads or 10,000.

📊 **Census data integration** - Free market density scores from the US Census Bureau. Most people don't know this data exists.

📧 **7-beat outreach framework** - Structured email schema (pattern break → cost of inaction → belief shift → mechanism → proof → offer → action). Every email follows proven persuasion psychology.

🧪 **Production-ready** - 34 tests. CI/CD. Docker. Event sourcing. Schema validation.

**Who it's for:**

- Solo growth hackers tired of tool fatigue
- Agencies targeting local service verticals (HVAC, plumbing, electrical)
- Developers who want to own their lead gen stack
- Privacy-conscious teams avoiding cloud lock-in

**How it works:**

```bash
# Scout → Qualify → Build → Outreach
python orchestrator.py https://example.com --approve --send-email

# Track everything in the dashboard
make dashboard  # localhost:8888
```

**The stack:**

- Python 3.12 + FastAPI
- SQLite (WAL mode for concurrent access)
- BeautifulSoup + httpx
- JSON Schema validation
- GitHub Actions CI/CD

**Open source:**

MIT licensed. Self-host. Fork. Customize for your vertical. No restrictions.

---

## Maker Comment (Sticky Comment)

Hi Product Hunt! 👋

I built Citadel because I was paying $260/month for a stack of tools (Clay, Durable, Instantly, Apollo) just to generate leads for my agency. It felt ridiculous—my data was scattered across 5 clouds, costs kept climbing, and I was one "account suspension" away from losing everything.

So I spent a weekend building a local-first alternative. SQLite instead of cloud databases. Static file generation instead of hosted sites. Local `.eml` files instead of expensive email platforms.

**What surprised me:** The free US Census Bureau data is incredibly powerful for scoring local business opportunities. Most people don't know this exists.

**The 7-beat framework** is something I learned from copywriting—every email follows the same psychological sequence. Citadel enforces this structure through JSON Schema validation.

**Current status:** 34 tests passing. Docker support. Used by 3 agencies in beta. Looking for feedback, contributors, and case studies.

Happy to answer questions!

— [Your name]

P.S. - I'm especially interested in hearing from agencies using this commercially. Email me: [your email]

---

## Topics/Tags

- Developer Tools
- Open Source
- Sales
- Marketing
- Lead Generation
- Automation

---

## Media Assets Needed

### Thumbnail (1024x576)

**Design:**
- Dark background (#0d1117 GitHub dark)
- Large text: "CITADEL" in monospace font
- Subtitle: "Open-source lead gen"
- Small icons representing: scrape → score → build → email
- "$0/mo" badge in corner (green)

### Gallery Images (5-7 slides)

1. **Hero slide** - Logo + tagline + dashboard screenshot
2. **The Problem** - SaaS cost comparison ($260/mo vs $0)
3. **The Pipeline** - 6-step flow diagram
4. **Dashboard** - Funnel metrics + lead table
5. **Code** - Terminal showing `python orchestrator.py` command
6. **Architecture** - Simple diagram: Python → SQLite → Static files
7. **Tech stack** - Logos: Python, FastAPI, SQLite, Docker

### Video/GIF

- 30-second demo GIF showing terminal → dashboard → generated site
- Loop infinitely
- No audio needed

---

## First Commenters (Engagement Strategy)

**Line up these comments to seed discussion:**

1. **The Question:** "How does this compare to Clay?"
   - Your answer: Detailed comparison of data sources vs. privacy

2. **The Use Case:** "Could this work for SaaS companies?"
   - Your answer: Currently optimized for local service, but forkable

3. **The Technical:** "Why SQLite over Postgres?"
   - Your answer: Simplicity for 90% use case. Migration path documented.

4. **The Skeptic:** "No ML for content generation?"
   - Your answer: Planned for v2. Current 7-beat templates work well.

---

## Launch Day Checklist

**24 hours before:**
- [ ] Post scheduled at 12:01 AM PT (optimal for early upvotes)
- [ ] Notify email list / Twitter followers
- [ ] Prepare responses to common questions

**Launch day:**
- [ ] Monitor comments, respond within 15 minutes
- [ ] Post on Twitter with PH link
- [ ] Share in relevant communities (Indie Hackers, Reddit r/marketing)
- [ ] Email 10 friends to upvote (not ask—share genuinely)

**Post-launch:**
- [ ] Analyze top questions for FAQ updates
- [ ] Follow up with interested agencies
- [ ] Post "lessons learned" thread on Twitter

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Upvotes | 200+ (top 5 of day) |
| Comments | 50+ |
| GitHub stars (launch day) | 100+ |
| Email signups | 50+ |
| Agency inquiries | 3-5 |
