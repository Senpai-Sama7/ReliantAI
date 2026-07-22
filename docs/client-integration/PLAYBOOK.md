# Reliant AI — Client Growth & Integration Playbook

Internal GTM + delivery reference for Operational Automation (Tier 3) engagements.

## Positioning

**Doing right**
- High-signal stack: React, TypeScript, Next.js ISR — no per-site builds
- Anti-AI-slop craft: cinematic, bespoke local storefronts
- Ops integration: intake, triage, and data routing beyond brochure sites

**Gaps to close**
- Own-domain search footprint is weak — reframe as client-first SEO focus
- Need prominent, verifiable case studies on reliantai.org
- Prefer retainers tied to automation value over flat maintenance

## Sales framing: “Invisible search”

When cold emailing trade owners:

> We do not burn budget ranking our agency for generic “web design” keywords. We spend that engineering focus ranking clients locally for queries like “emergency AC repair.” Here is the local SEO blueprint we use.

## Outreach sequence (email)

### Touchpoint 1 — Day 0 (blunt reality check)

**Subject:** Quick question about [Company Name]’s site performance

```
Hi [First Name],

I looked at [Company Name]’s digital storefront today. To be frank, it looks
exactly like your competitors — because it is likely built on the same generic,
bloated software builders.

Most agencies push drag-and-drop templates. They load slowly, break under the
hood, and local search is punishing sites that look like interchangeable AI
templates.

We hand-code high-performance infrastructure with React and TypeScript for local
trade companies. Our sites target 90+ PageSpeed scores. We do not waste capital
ranking our own agency site globally for generic keywords; we use that focus to
dominate local search for clients.

I ran a quick performance audit on your current site. Do you have 60 seconds to
see the engineering flaws costing you leads?

Best,
[Your Name]
Reliant AI
```

### Touchpoint 2 — Day 3 (proof of performance)

**Subject:** Re: [Company Name]’s site performance

```
Hi [First Name],

Following up. While templates hide behind heavy visual plugins, clean code wins
local search.

How we structure local storefronts:
- Custom React infrastructure — zero template bloat, fast load times
- Semantic architecture — so search engines can read and recommend natively
- Managed integrity — code, security, and deployment with zero technical overhead

When someone searches for emergency services in your area, a split-second load
difference often decides who gets the call.

Worth a brief 5-minute chat this week to look at the audit numbers?

Best,
[Your Name]
```

### Touchpoint 3 — Day 7 (automation pivot)

**Subject:** Fixing the administrative leaks at [Company Name]

```
Hi [First Name],

Most owners I talk to do not just want a prettier website — they want fewer
administrative headaches.

Beyond hand-coded speed, we build autonomous data integrations into the
storefront. Instead of chaotic contact forms and manual entry, builds can
qualify leads, triage requests, and pipe clean data into your operational tools.

If your website is not actively reducing admin workload, it is costing money.

Open to a brief call on automating front-end operations?

Best,
[Your Name]
```

## Value-based pricing

| Tier | Setup | Recurring | Target |
|------|-------|-----------|--------|
| Starter Presence | $2,500 | $199/mo | Micro-businesses needing local credibility + speed |
| Professional Growth | $5,500 | $299/mo | Established trades scaling lead acquisition |
| Operational Automation | $4,500 | $399/mo | High-volume ops cutting admin overhead |
| Enterprise Systems | $12,000+ | Custom | Multi-system orchestration |

### Operational Automation deliverables
- High-signal intake briefs that pre-qualify intent
- Front-end triage pipelines that categorize requests
- Secure webhooks into CRM / scheduling systems
- Core ops dashboard for system health and volume

### Stack diagram (Tier 3)

```
Custom Next.js frontend
        │
        ▼
Secure JSON webhook API (payload routing)
        │
   ┌────┴────┐
   ▼         ▼
CRM sync   Scheduling sync
(HubSpot / Jobber / Housecall Pro)
(Cal.com / Google Calendar)
   │         │
   └────┬────┘
        ▼
Agentic triage & data processing
(urgency scoring → dispatch / Slack / SMS)
```

## Proposal outline (Tier 3)

1. **Problem** — Template speed penalty + manual intake
2. **Solution** — Hand-coded Next.js + operational automation
3. **Scope** — Frontend, webhook routing, urgency intake, continuous optimization
4. **Investment** — Setup $4,500 / retainer $399; 50% init + 50% deployment
5. **Next steps** — Confirm workflow preferences + credential intake

### Example milestone calendar (adjust per kickoff)

| Phase | Window | Focus |
|-------|--------|-------|
| 1 Technical initialization | Weeks 1–2 | Field mapping, HubSpot hooks, UI prototype, Next.js scaffold |
| 2 Automation & routing | Weeks 3–4 | Webhooks, lead scoring, sandbox security tests |
| 3 Speed tuning & production | Weeks 5–6 | Media/PageSpeed, JSON-LD, DNS cutover |

## CRM integration specs (HubSpot example)

- Server-side JSON payloads into HubSpot (no client-side plugin bloat)
- Agentic lead scoring: contract value proxies, geography, technical needs
- Emergency routes → Slack/SMS after validation checks
- Preserve 90+ PageSpeed by keeping integrations off the critical path

Credential validation tooling lives in `ops/client-integration/` — see package README.
