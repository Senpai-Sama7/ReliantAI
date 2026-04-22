# Citadel Demo Video Script

**Target Length:** 4-5 minutes  
**Format:** Screen recording + voiceover  
**Style:** Fast-paced, technical but accessible, show don't tell

---

## Scene 1: Hook (0:00 - 0:30)

**Visual:** Terminal screen with monthly SaaS bills

```
$149 - Clay (lead enrichment)
$25  - Durable (AI website builder)
$37  - Instantly (cold email)
$49  - Apollo (contact data)
---
$260/month
$3,120/year
```

**VO:** "I was paying over $3,000 a year for lead generation tools. So I built a replacement that costs zero. And keeps all my data local."

**Transition:** Hard cut to terminal

---

## Scene 2: The Problem (0:30 - 1:00)

**Visual:** Browser tabs opening: Clay → Durable → Instantly → Apollo

**VO:** "Here's my workflow. Find a local business. Enrich the data. Generate a site preview. Draft outreach. Track everything in spreadsheets. Five tools. Five logins. Five places my data lives."

**Visual:** Show fragmented workflow, copy-pasting between tools

**VO:** "I wanted one command that does it all. Meet Citadel."

---

## Scene 3: The Scout (1:00 - 1:45)

**Visual:** Terminal command

```bash
$ python orchestrator.py https://joesplumbing.com --dry-run

[INFO] Scouting https://joesplumbing.com...
[INFO] Business: Joe's Plumbing & HVAC
[INFO] Email: contact@joesplumbing.com
[INFO] Phone: (555) 123-4567
[INFO] Vertical: plumbing
[INFO] City: Houston, TX
[INFO] GBP: Found (google.com/maps/...)
[INFO] Web presence score: 2/5
[INFO] Opportunity score: 8/10
```

**VO:** "First, Citadel scouts the website. It extracts business name, contact info, infers the vertical—even pulls Google Business Profile signals. This business scored 8 out of 10. High opportunity."

**Visual:** Show JSON output briefly

---

## Scene 4: The Build (1:45 - 2:30)

**Visual:** Terminal continues

```bash
[INFO] Building site preview...
[INFO] Generated workspace/builds/joes-plumbing-houston/index.html
[INFO] Generated workspace/builds/joes-plumbing-houston/styles.css
[INFO] Generated workspace/builds/joes-plumbing-houston/app.js
[INFO] Lighthouse estimate: 92/100
```

**VO:** "Then it builds a complete static site. Customized for plumbing services. Mobile-first. Form capture. SEO-ready."

**Visual:** Browser opens the generated site

**Show:** 
- Hero section: "Joe's Plumbing - Fast, Reliable Service in Houston"
- Services grid: Drain cleaning, Pipe repair, Water heater, Emergency
- Quote form
- Trust badges

**VO:** "This is what Joe's Plumbing could look like. Generated in under a second."

---

## Scene 5: The Outreach (2:30 - 3:15)

**Visual:** Terminal shows email generation

```bash
[INFO] Drafting outreach...

Subject: Quick question about Joe's Plumbing site

Hey Joe,

I was looking for a plumber in Houston and noticed your website is hard to find on mobile...

[Pattern break] Most plumbing businesses lose 40% of leads to slow websites.
[Cost of inaction] That's 12-15 customers every month going to competitors.
[Belief shift] But it's not about redesigning—it's about being findable.
[Mechanism] We build mobile-first sites that rank locally in under 24 hours.
[Proof] Helped 3 Houston plumbers add $8K/month in new bookings.
[Offer] Want me to build you a preview? No cost, no commitment.
[Action] Just reply "show me" and I'll send it over.

Best,
[Name]

---
Unsubscribe: optout@example.com
```

**VO:** "Then it drafts the outreach. Structured using a 7-beat persuasion framework. Every email has the same psychological structure."

**Visual:** Show the `beat_audit` JSON validating structure

---

## Scene 6: The Dashboard (3:15 - 4:00)

**Visual:** Terminal

```bash
$ make dashboard

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8888
```

**Visual:** Browser opens dashboard

**Show:**
- Funnel metrics: 47 scouted → 32 qualified → 18 built → 12 approved → 8 deployed → 5 replied
- Revenue: $12,400 potential
- Beat compliance: 100%
- Recent leads table

**VO:** "And there's a full dashboard. Track every lead through the funnel. See revenue potential. Monitor outreach compliance. All local. All private."

**Visual:** Click into a lead timeline

**Show:** Event log - scouted → qualified → built → outreach drafted → deployed → email sent

**VO:** "Every state change is logged. Complete audit trail."

---

## Scene 7: The Deployment (4:00 - 4:30)

**Visual:** Back to terminal

```bash
$ python orchestrator.py https://joesplumbing.com --approve --send-email

[INFO] Deploying to local filesystem...
[INFO] Site live at: workspace/deploys/joes-plumbing-houston/index.html
[INFO] Email written to: workspace/outbox/joes-plumbing-20240224.eml
[INFO] Lead status: deployed → emailed

✓ Pipeline complete for joes-plumbing-houston
```

**VO:** "Approve and deploy. Site goes live. Email goes to outbox. Or configure SMTP to send directly."

---

## Scene 8: The Stack (4:30 - 4:50)

**Visual:** Terminal - show test suite

```bash
$ make test
python3 -m pytest -q
..................
34 passed, 5 warnings in 1.45s
```

**VO:** "34 tests. CI/CD. Docker support. SQLite. Python. No cloud dependencies required."

**Visual:** Show GitHub repo, star count (aspirational), README

---

## Scene 9: CTA (4:50 - 5:00)

**Visual:** Terminal with repo link

```
GitHub: github.com/[user]/citadel
License: MIT

$ git clone [repo]
$ make install
$ make init-db
$ python orchestrator.py [your-target-url]
```

**VO:** "Open source. MIT licensed. Try it. Break it. Fork it. Link in the description."

**Visual:** Fade to logo

---

## Production Notes

**Tools:**
- Recording: OBS or Loom
- Terminal: iTerm2 with Tokyo Night theme (dark blue background)
- Font: JetBrains Mono or Fira Code (for ligatures)
- Browser: Arc or Chrome with minimal UI

**Pacing:**
- Keep terminal typing minimal—use copy-paste for long commands
- Use `type` command instead of `cat` to simulate typing
- Speed up boring parts (pip installs) with jump cuts

**Audio:**
- Clear, conversational tone
- No background music (HN audience hates it)
- Normalize audio to -16 LUFS

**Accessibility:**
- Add captions (YouTube auto-captions are fine)
- Ensure contrast ratio meets WCAG AA

---

## Alternative: 60-Second Short

**For Twitter/TikTok/Shorts:**

1. Hook: "I built a $300/mo SaaS for $0" (5s)
2. Problem: Show 5 tool tabs (5s)
3. Solution: One command `python orchestrator.py URL` (10s)
4. Demo: Site generation (15s)
5. Demo: Email draft (15s)
6. CTA: GitHub link (10s)
