# Client Integration Validation

Production tooling for Tier 3 Operational Automation credential checks, triage alerting, and ops handoff.

## Package layout

```
ops/client-integration/
  src/
    validate-credentials.ts   # CLI audit entrypoint
    triage-alerting.ts        # AWS Lambda exception gateway
    validators/               # HubSpot, Cal.com, Slack
  dashboard/
    TokenValidationDashboard.tsx
  terraform/main.tf
  tests/
```

## Quick start

```bash
cd ops/client-integration
npm install
npm test
npm run typecheck
```

### Live credential audit

```bash
export HUBSPOT_APP_ACCESS_TOKEN=...
export SCHEDULING_API_KEY=...
export NOTIFICATION_ROUTING_WEBHOOK=https://hooks.slack.com/services/...
# Default: Slack URL shape only (no handshake post)
export VALIDATE_SLACK_DRY_RUN=true
npm run validate
```

Set `VALIDATE_SLACK_DRY_RUN=false` to post a real Slack handshake.

### Environment variables

| Variable | Purpose |
|----------|---------|
| `HUBSPOT_APP_ACCESS_TOKEN` | HubSpot private app token (contacts read) |
| `SCHEDULING_API_KEY` | Cal.com API key (`GET /v1/me`) |
| `NOTIFICATION_ROUTING_WEBHOOK` | Slack incoming webhook URL |
| `VALIDATE_SLACK_DRY_RUN` | `true` (default) skips Slack POST |

### GitHub Actions

Workflow: `.github/workflows/validate-credentials.yml`

- PR/push: unit tests + typecheck
- `workflow_dispatch`: optional live audit using repository secrets

### Terraform

```bash
cd ops/client-integration
npm run build
cd terraform
terraform init
terraform apply \
  -var="notification_routing_webhook=$NOTIFICATION_ROUTING_WEBHOOK" \
  -var="environment=production"
```

Lambda handler: `triage-alerting.handler` (compiled under `dist/`).

### Dashboard

`dashboard/TokenValidationDashboard.tsx` expects `POST /api/credential-audit` to return:

```json
{
  "auditedAt": "2026-07-22T12:00:00.000Z",
  "services": [
    {
      "name": "HubSpot CRM Access API",
      "category": "Data Pipeline",
      "isValid": true,
      "message": "...",
      "latency": 142
    }
  ]
}
```

Wire that route to `runCredentialAudit()` from this package.

## Related docs

- [`docs/client-integration/PLAYBOOK.md`](../../docs/client-integration/PLAYBOOK.md) — GTM, outreach, pricing, proposals
- [`docs/client-integration/SCALING_CHECKLIST.md`](../../docs/client-integration/SCALING_CHECKLIST.md) — launch gates
- [`docs/client-integration/EMAIL_TEMPLATES.md`](../../docs/client-integration/EMAIL_TEMPLATES.md) — credential intake + post-launch report
