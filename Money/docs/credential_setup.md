# Credential Setup Guide

Step-by-step instructions for obtaining all required API keys and credentials.

---

## 1. Gemini API Key (LLM)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign up / log in
3. Navigate to API Keys → Create API Key
4. Copy the key
5. Add to `.env`: `GEMINI_API_KEY=...`

## 2. Twilio (SMS/WhatsApp)

1. Go to [twilio.com/console](https://www.twilio.com/console)
2. Sign up / log in
3. From the dashboard, copy:
   - Account SID → `TWILIO_SID`
   - Auth Token → `TWILIO_TOKEN`
4. Buy a phone number (or use trial number)
   - Copy it → `TWILIO_FROM_PHONE=+1XXXXXXXXXX`
5. Configure webhooks:
   - SMS webhook URL: `https://your-domain.com/sms` (POST)
   - WhatsApp: Enable WhatsApp sandbox, set webhook to `https://your-domain.com/whatsapp`

## 3. Composio (Google Calendar)

1. Go to [composio.dev](https://composio.dev)
2. Sign up / log in
3. Create an API key → `COMPOSIO_API_KEY`
4. Connect your Google Calendar integration in the Composio dashboard

## 4. LangSmith (Tracing — Optional)

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign up / log in
3. Settings → API Keys → Create
4. Copy → `LANGSMITH_API_KEY=lsv2_...`

## 5. Application Keys

- `DISPATCH_API_KEY` — Choose a strong random string (e.g., `openssl rand -hex 32`)
- `OWNER_PHONE` — Shop owner's real phone number (for safety escalations)
- `TECH_PHONE_NUMBER` — Default technician's phone number

## 6. Final .env

```bash
# Required
GEMINI_API_KEY=...
TWILIO_SID=AC...
TWILIO_TOKEN=...
TWILIO_FROM_PHONE=+1...
OWNER_PHONE=+1...
TECH_PHONE_NUMBER=+1...
COMPOSIO_API_KEY=...
DISPATCH_API_KEY=...

# Optional
LANGSMITH_API_KEY=lsv2_...
ENV=production
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
DATABASE_PATH=dispatch.db
```

## 7. Verify

```bash
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 &
bash tools/e2e_test.sh
```
