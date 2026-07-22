# Client Scaling & Deployment Checklist

Engineering gates from sandbox → production for Operational Automation clients.

## Milestone 1 — Pre-launch sanity & assets

- [ ] Production build clean: `npm run build` (zero TypeScript / import errors)
- [ ] Images encoded as WebP/AVIF where practical
- [ ] PageSpeed mobile + desktop ≥ 90
- [ ] Managed SSL provisioned; DNS records staged (not cut over yet)

## Milestone 2 — Telemetry & error orchestration

- [ ] Production env vars injected (HubSpot, Cal.com, Slack webhook, secrets)
- [ ] Credential audit passes: `cd ops/client-integration && npm run validate`
- [ ] Edge/exception tracking wired to triage Lambda
- [ ] Sandbox intentional exception reaches on-call Slack
- [ ] JSON-LD / rich snippet schemas validated

## Milestone 3 — Scaling & load gateways

- [ ] DB connection pooling limits set for traffic spikes
- [ ] Stale-While-Revalidate / ISR caching rules verified on edge
- [ ] Rate limits on public intake/form APIs
- [ ] Daily database backup schedule confirmed

## Milestone 4 — Operational handover

- [ ] Live test lead lands in correct HubSpot pipeline / properties
- [ ] Calendar availability sync confirmed (Cal.com or equivalent)
- [ ] Client admin invites issued; infrastructure keys withheld
- [ ] Performance gates signed; DNS cutover to production

## Commands (reference)

```bash
# Client sites gate
cd reliantai-client-sites
npm run build && npm run typecheck && npm run lint && npm run test

# Credential integrity
cd ops/client-integration
npm ci && npm test && npm run validate
```
