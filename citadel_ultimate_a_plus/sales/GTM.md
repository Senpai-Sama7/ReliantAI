# Citadel GTM Plan (30 Days)

## Objective

- Close 3 paid pilots in 30 days.
- Produce 1 publishable case study with real funnel metrics.
- Stand up a repeatable outbound motion for local-service operators and agencies.

## ICP and Vertical Focus

Primary ICP:
- Local service businesses with clear lead value and short sales cycles.
- Small agencies that manage outbound/web presence for local service clients.

Configured verticals in this repo (`market/target_verticals.json`):
- `plumbing`
- `hvac`
- `roofing`
- `landscaping`
- `electrical`
- `painting`

Initial focus:
- Start with `plumbing` (primary) and `hvac` (secondary) in Harris County, TX.

## Core Offer

Positioning:
- "From target URL to qualified lead, site preview, outreach draft, and tracked pipeline state in one local-first system."

Pilot offer (recommended):
- Setup fee: $1,500-$3,000
- Pilot month: $1,000-$2,500
- Optional performance component: per qualified reply or percent of closed revenue

Scope in pilot:
- Targeting + qualification pipeline run
- Generated preview artifacts
- Outreach draft generation and send flow
- Dashboard visibility on funnel and lead timeline

## Weekly Execution Plan

### Week 1: Packaging and Sales Assets

- Finalize one vertical one-pager (`plumbing`) and outbound sequence.
- Record a short demo (5-8 min) of full workflow.
- Build first prospect list (500+ accounts): 250 plumbing, 250 HVAC. See `sales/playbooks/prospect_sourcing.md` for sourcing methodology.
- Define call script, qualification rubric, and pilot SOW template.

Exit criteria:
- Messaging and offer locked.
- Prospect list and scripts ready.

### Week 2: Outbound and Discovery

- Send 25-40 personalized outbound messages per day (email first, volume ramps with warmup).
- Run daily response triage and book discovery calls.
- Hold 8-12 discovery calls this week.

Exit criteria:
- At least 6 qualified discovery calls completed.
- At least 2 pilot proposals sent.

### Week 3: Demo and Pilot Closures

- Run live demos using target-specific examples.
- Close first 2 pilots.
- Launch first pilot within 72 hours of signature.

Exit criteria:
- 2 signed pilots.
- First live execution reports delivered.

### Week 4: Delivery, Evidence, and Scale

- Execute pilots with weekly metrics report.
- Capture baseline vs. current funnel metrics.
- Publish one short case study and use it in outbound wave 2.

Exit criteria:
- 3rd pilot closed or in final procurement stage.
- 1 case study approved for external sharing.

## Channel and Activity Targets

Primary channel:
- Cold email with vertical-specific personalization.

Secondary channels:
- Referral asks from agencies.
- Direct LinkedIn DM for owner/operators.

Daily activity targets:
- 25-40 first-touch outbound emails (limited by warmup schedule in weeks 1-2)
- 15-25 follow-ups
- 5-10 personalized account notes

At 30 first touches/day × 10 sending days in weeks 2-3, that's 300 first touches — well within the 500+ prospect list. Follow-ups recycle from prior sends.

## Funnel Targets (Operating Benchmarks)

- Reply rate: 5%-12%
- Meeting rate: 2%-6%
- Demo-to-pilot close: 20%-35%

Track daily:
- `first_touches`
- `replies`
- `meetings_booked`
- `meetings_held`
- `proposals_sent`
- `pilots_closed`

## Sales Process

1. Outbound message with concrete pain + mechanism.
2. 15-20 minute discovery call.
3. Live demo with vertical example.
4. Pilot proposal (fixed scope, timeline, success criteria).
5. 72-hour onboarding to first execution.

## Risk Controls

- If no qualified replies by day 14, tighten ICP and messaging by sub-vertical.
- If meeting rate is weak, increase personalization depth and improve proof assets.
- If close rate is weak, shorten pilot scope and reduce onboarding friction.

## Email Infrastructure Requirements

Must be in place before Week 1 outbound begins. See also `PROGRESS_TRACKER_v2.md` Phase 7 (Email Deliverability) for automated warmup implementation.

Domain setup:
- Register a dedicated sending domain (e.g., `outbound.yourdomain.com`) — never send cold email from your primary domain.
- Configure SPF record: `v=spf1 include:<sending_tool_spf> -all`
- Configure DKIM: generate key pair via sending tool, publish public key as TXT record.
- Configure DMARC: `v=DMARC1; p=quarantine; rua=mailto:<your_reporting_email>` (start with `p=none` during warmup, move to `quarantine` after 2 weeks).

Warmup schedule:
- Days 1-3: 5 emails/day (manual sends to known contacts who will reply)
- Days 4-7: 10-15 emails/day (mix of warm contacts and first cold sends)
- Days 8-14: 20-30 emails/day (ramp cold sends, monitor bounce rate)
- Days 15+: 30-40 emails/day (full volume, maintain <2% bounce rate)

If bounce rate exceeds 3% at any point, pause and clean the list.

Sending tool options:
- Instantly.ai or Smartlead (purpose-built for cold outbound, built-in warmup)
- Amazon SES + Citadel's `smtp` backend (lower cost, more control, requires manual warmup)
- Citadel `local_outbox` for testing (writes `.eml` files, no actual sends)

Monitoring:
- Track daily: sends, bounces, replies, spam complaints
- If spam complaint rate exceeds 0.1%, stop immediately and audit copy + list quality
- Use mail-tester.com to score deliverability before going live

## Immediate Next Artifacts

- Vertical one-pager: `sales/one_pagers/plumbing.md`
- Outbound sequence: `sales/outbound/plumbing.md`
