# ReliantAI Sales Intelligence Integration

This module connects the HVAC Dispatch System with external Sales Intelligence tools to enable automatic lead capture and dispatch creation.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Gmail Scanner  │────▶│  Make.com (Rube) │────▶│  HubSpot CRM    │
│  (Sales Intel)  │     │  Automation      │     │  + Google Sheet │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              │ Webhook
                              ▼
                     ┌──────────────────┐
                     │  ReliantAI       │
                     │  /webhooks/make  │
                     └──────────────────┘
```

## Components

### 1. Sales Intelligence Connector (`sales_intelligence.py`)
Processes leads from the external Sales Intelligence System:
- Parses email content for HVAC keywords
- Calculates lead scores (0-100)
- Creates dispatch records in the database

### 2. HubSpot Sync (`hubspot_sync.py`)
Bidirectional sync with HubSpot CRM:
- Creates/updates contacts
- Updates lifecycle stages (lead → customer)
- Adds timeline notes

### 3. Google Sheets Logger (`google_sheets.py`)
Logs dispatch data to your existing Sales Intelligence spreadsheet:
- Timestamp, customer info, status
- Links Sales Intel row to dispatch ID
- Creates unified record across systems

### 4. Slack Alerts (`slack_alerts.py`)
Real-time notifications:
- Hot leads (score 70+) → Instant Slack alert
- Critical leads (score 90+) → Slack + SMS
- Cold lead escalations → Alert when cold leads heat up

## Webhook Endpoints

### POST `/webhooks/make/sales-lead`
Receives leads from Make.com automations.

**Headers:**
```
X-Webhook-Secret: your-webhook-secret
```

**Payload Example:**
```json
{
  "from_name": "John Smith",
  "from_email": "john@smithplumbing.com",
  "subject": "AC Repair Quote Request",
  "body_preview": "Hi, our AC unit is not cooling properly...",
  "received_at": "2026-03-03T21:42:00Z",
  "lead_score": 75,
  "matched_keywords": ["ac", "repair", "quote"],
  "urgency": "warm",
  "google_sheets_row": "A12",
  "hubspot_contact_id": "12345"
}
```

**Response:**
```json
{
  "status": "received",
  "dispatch_id": "SI-20260303-214200",
  "lead_score": 75
}
```

### POST `/webhooks/hubspot/contact-updated`
Receives updates when HubSpot contacts are modified.

## Environment Variables

```bash
# HubSpot
HUBSPOT_API_KEY=pat-na1-xxxxx

# Google Sheets
GOOGLE_SHEETS_ID=1jdS3oYIOQgHhWZqlza8ThIYknMmYM0TiPLNXXt_t-1Y

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Webhook Security
MAKE_WEBHOOK_SECRET=your-webhook-secret
```

## Lead Scoring

Your Sales Intelligence System assigns scores based on:

| Score | Priority | Action |
|-------|----------|--------|
| 90-100 | 🔥 Critical | Slack + SMS alert |
| 80-89 | 🔥 High | Slack alert |
| 70-79 | 🔥 Standard | Log to dashboard |
| <70 | ❄️ Cold | Track in background |

## Testing

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/webhooks/make/sales-lead \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -d '{
    "from_name": "Test Customer",
    "from_email": "test@example.com",
    "subject": "AC Not Working",
    "body_preview": "Need emergency AC repair",
    "lead_score": 85,
    "urgency": "warm"
  }'
```

## Support

For issues with the integration:
- Email: DouglasMitchell@ReliantAI.org
- Owner: Douglas Mitchell
- Phone: +1-832-947-7028
