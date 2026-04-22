# Citadel for {{display_name}} Operators ({{geo_label}})

## What It Is

Citadel is a local-first outbound pipeline for {{display_name}} businesses that need more qualified conversations and better pipeline visibility.

It takes a target business URL and runs:
- lead qualification
- static preview generation
- outreach draft generation
- full funnel tracking in a single SQLite-backed workflow

## Problem We Solve

Most {{display_name}} outbound efforts break in three places:
- {{pain_point_1}}
- {{pain_point_2}}
- {{pain_point_3}}

## How Citadel Works

1. Scout and qualify a lead from a public business website.
2. Enforce structured contracts with JSON schema validation gates.
3. Generate preview artifacts for outreach context.
4. Draft 7-beat outreach copy and persist event/state history.
5. Expose operator visibility through dashboard APIs and lead timeline views.

## Why This Fits {{display_name}}

- `{{vertical_slug}}` is a configured target vertical in this repo (`market/target_verticals.json`).
- GTM angle: {{proof_angle}}.
- The system is built to produce repeatable, auditable lead-to-outreach execution.

## Security and Reliability Highlights

- HMAC-verified webhook endpoint (`/api/webhooks/openclaw`)
- Timestamp skew enforcement and idempotent webhook receipts
- Per-IP rate limiting for read APIs and webhook
- Health check endpoint (`/health`)
- CI workflow + automated test suite coverage

## Pilot Scope (Recommended)

Timeline:
- Week 1 setup + first runs
- Weeks 2-4 optimization and reporting

Deliverables:
- Qualified target list runs
- Outreach draft outputs
- Funnel and timeline reporting snapshots
- Weekly metrics review

## Pilot Pricing (Suggested)

- Setup: $1,500-$3,000
- Pilot month: $1,000-$2,500
- Optional performance component: per qualified reply or share of closed revenue

## Success Criteria

For pilot acceptance, define numeric targets up front:
- Qualified leads produced
- Reply rate
- Meetings booked
- Deal progression signals

## CTA

If you want, we can run a 7-day {{display_name}} pilot and review results in a single weekly dashboard.
