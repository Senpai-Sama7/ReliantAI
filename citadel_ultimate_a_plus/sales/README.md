# Sales Asset Structure

This folder holds GTM, vertical assets, playbooks, and reusable templates.

## Layout

- `sales/GTM.md`: 30-day go-to-market execution plan.
- `sales/BUSINESS_PLAN_FINAL.md`: synthesized final business plan (best elements of `sales/BUSINESS_PLAN.md` and `sales/business_plan.md`).
- `sales/BUSINESS_PLAN.md`: concise business plan draft.
- `sales/business_plan.md`: detailed lender/investor-style business plan draft.
- `sales/one_pagers/`: vertical-specific and ICP-specific one-pagers.
- `sales/outbound/`: vertical-specific and ICP-specific outbound copy packs.
- `sales/playbooks/`: operational playbooks (sourcing, call scripts, qualification, observation examples).
- `sales/templates/`: reusable template pack and vertical parameter map for all configured verticals.

## Current Assets

One-pagers:
- `sales/one_pagers/plumbing.md` — buyer-focused, pain-led
- `sales/one_pagers/hvac.md`
- `sales/one_pagers/roofing.md`
- `sales/one_pagers/landscaping.md`
- `sales/one_pagers/electrical.md`
- `sales/one_pagers/painting.md`
- `sales/one_pagers/agency.md` — margin/scale-focused for agency ICP

Outbound packs:
- `sales/outbound/plumbing.md` — 3-email sequence + LinkedIn DM + discovery
- `sales/outbound/hvac.md`
- `sales/outbound/roofing.md`
- `sales/outbound/landscaping.md`
- `sales/outbound/electrical.md`
- `sales/outbound/painting.md`
- `sales/outbound/agency.md` — agency-specific sequence + objection handling

Playbooks:
- `sales/playbooks/prospect_sourcing.md` — how to build a 500+ prospect list
- `sales/playbooks/call_script.md` — discovery call script (operator + agency tracks) + voicemail
- `sales/playbooks/qualification_rubric.md` — 10-point scoring rubric + disqualifiers
- `sales/playbooks/observation_examples.md` — 54 concrete `{{specific_observation}}` examples across all 6 verticals + agency

## Reusable Template Pack

Use these together:
- `sales/templates/vertical_parameters.yaml` (all 6 configured verticals)
- `sales/templates/one_pager_template.md`
- `sales/templates/outbound_template.md`

Workflow:
1. Pick a vertical entry from `vertical_parameters.yaml`.
2. Fill placeholders in both templates.
3. Save outputs under `sales/one_pagers/<vertical>.md` and `sales/outbound/<vertical>.md`.
