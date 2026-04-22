# Prospect List Sourcing Playbook

How to build a qualified prospect list of 500+ local service businesses for outbound.

## Target Per Vertical

| Vertical | Target Count | Primary Geo |
|----------|-------------|-------------|
| Plumbing | 250 | Harris County, TX |
| HVAC | 250 | Harris County, TX |
| Total | 500+ | |

Scale to roofing, landscaping, electrical, painting after first pilot closes.

## Source 1: Google Maps (Primary — 60% of list)

Tool: Google Maps manual search or SerpAPI / Outscraper for bulk export.

Search queries:
- `plumber near Houston TX`
- `plumbing company Harris County`
- `emergency plumber Houston`
- `HVAC repair Houston TX`
- `AC installation Harris County`

What to capture per result:
- Business name
- Website URL (required — skip if no website)
- Phone number
- Address (verify service area)
- Google rating + review count
- Business category

Filter criteria:
- Must have a website (no website = can't run the pipeline)
- Must be in Harris County or adjacent (Fort Bend, Montgomery, Brazoria)
- Must show signs of active operation (reviews in last 6 months)
- Skip franchises (Roto-Rooter, Mr. Rooter, etc.) — target independents

Expected yield: 300-400 results across both verticals.

## Source 2: Yelp (Secondary — 20% of list)

Search: `Plumbers` and `HVAC` in `Houston, TX` on Yelp.

Capture same fields. Deduplicate against Google Maps list by domain name.

Yelp-specific signals:
- "Request a Quote" button active = they're paying for Yelp leads (good — they spend on lead gen)
- Low review count + old reviews = may be struggling for visibility (good — they need help)

Expected yield: 80-120 unique additions after dedup.

## Source 3: BBB and Trade Associations (Supplemental — 10% of list)

Sources:
- BBB Houston directory: `bbb.org/us/tx/houston`
- PHCC of Texas member directory
- Texas State Board of Plumbing Examiners license lookup

These tend to be more established businesses. Good for higher-ticket pilots.

Expected yield: 40-60 unique additions.

## Source 4: Competitor Ad Research (Supplemental — 10% of list)

Check who's running Google Ads for plumbing/HVAC keywords in Houston:
- Search `plumber Houston` in an incognito browser, note the advertisers
- Use SpyFu or SEMrush free tier to see who bids on `plumber near me` in Houston

These businesses are already spending on lead gen — they're pre-qualified buyers.

Expected yield: 20-40 unique additions.

## Qualification Filter (Before Pipeline Entry)

Every prospect must pass these checks before entering Citadel:

1. Has a working website (HTTP 200, not parked/under construction)
2. Website shows plumbing/HVAC services (not a directory or aggregator)
3. Located in target geography (Harris County + adjacent)
4. Independent operator or small chain (<10 locations)
5. Shows signs of active business (recent reviews, updated site content, active phone)

Disqualify:
- National franchises
- Businesses with no website
- Businesses outside service area
- Aggregator/directory listings
- Businesses that appear closed (no reviews in 12+ months, disconnected phone)

## List Hygiene

Before loading into the pipeline:
- Deduplicate by domain (not business name — same owner may have multiple brands)
- Verify email deliverability if you have email addresses (use NeverBounce or ZeroBounce)
- Remove any businesses you've personally worked with or have a conflict with

## Output Format

CSV with columns:
```
business_name, website_url, phone, city, state, zip, google_rating, review_count, source, vertical, notes
```

Load into Citadel via:
```bash
# One at a time
python orchestrator.py https://example-plumber.com --dry-run

# Bulk (when Phase 4 queue system is implemented)
python orchestrator.py --bulk prospects.csv --dry-run
```

## Refresh Cadence

- Rebuild list every 60 days (new businesses open, old ones close)
- Track which prospects have been contacted in the pipeline — don't re-source them
- Expand to adjacent counties (Fort Bend, Montgomery) when Harris County is saturated
