# Show HN: I built a $300/mo SaaS replacement for outbound lead generation

**TL;DR:** I got tired of paying $149/mo for Clay, $25/mo for Durable, and $37/mo for Instantly just to generate leads and send emails. So I built Citadel—a local-first pipeline that does website scraping, lead scoring, static site generation, and email outreach. Zero API costs. Zero data leaving your machine. SQLite + Python + 34 tests.

**Live Demo:** [GitHub repo link]

---

## What it does

1. **Scout** - Crawls a business website, extracts name, contact info, vertical, ratings
2. **Qualify** - Scores leads 1-10 using a custom algorithm (bonus: integrates free Census CBP data for market density)
3. **Build** - Generates a production-ready static site (HTML/CSS/JS) tailored to the business vertical
4. **Outreach** - Drafts a structured 7-beat email with compliance footer
5. **Deploy** - Local filesystem (default) or push to any host
6. **Track** - Full event sourcing in SQLite—every state change logged

---

## The tech stack (boring but practical)

- Python 3.12 + FastAPI for the dashboard
- SQLite (WAL mode) for persistence
- BeautifulSoup + httpx for scraping
- No cloud dependencies. No API keys required. Works offline.

---

## Why I built this

I run a small agency. We target local service businesses—plumbers, HVAC, electricians. Every month:
- Clay for enrichment: $149
- Durable for site previews: $25  
- Instantly for email: $37
- **Total: $211/mo**

That's $2,500/year for what is essentially: scrape → score → generate → email.

Citadel does the same pipeline for **$0** (after the ~3 hours I spent building it).

---

## The controversial parts

**"But Apollo/ZoomInfo has better data"**
True. If you need Fortune 500 contacts, use those. But for local businesses? The website *is* the data. You don't need a $10K data subscription to find a plumber's email.

**"What about deliverability?"**
Fair concern. I use local `.eml` files or SMTP (Bring Your Own Mailgun/SendGrid). No built-in warmup, but also no "account suspended because a prospect marked you spam."

**"SQLite doesn't scale"**
Correct. For my use case (hundreds of leads), it's perfect. At 10K+ leads, I'd graduate to Postgres. The code is standard SQL—migration is trivial.

---

## What's unique

- **Census CBP integration** - Free market density data. Most people don't know this exists.
- **7-beat outreach schema** - Enforced email structure (pattern break → cost of inaction → belief shift → mechanism → proof → offer → action)
- **Event sourcing** - Complete audit trail of every pipeline state change
- **Schema-as-contract** - All inter-stage data validated against JSON Schema

---

## The code

```python
# Run the full pipeline
python orchestrator.py https://example.com --approve --send-email

# Start the dashboard
make dashboard  # localhost:8888

# Run tests
make test  # 34 tests, all passing
```

---

## Who this is for

- Solo growth hackers who don't want tool fatigue
- Agencies targeting local service verticals
- Developers who want to own their lead gen stack

## Who this is NOT for

- Enterprise sales teams (use Outreach)
- People who need LinkedIn automation (use Apollo)
- Anyone who wants a SaaS with a support phone number

---

## The ask

Try it. Break it. Open an issue if you hate it.

If you're an agency using this commercially, I'd love a case study. Email me: [your email]

---

**GitHub:** [repo link]

**License:** MIT (do whatever, just don't sue me)

---

*P.S. - Yes, I used Citadel to generate sites for the agencies I'm now selling Citadel to. It's turtles all the way down.*
