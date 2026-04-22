# Deployment Guide — Houston HVAC AI Dispatch

## Preflight, Hardening, and Pilot Launch (v1.4.0)

This guide reflects the current, verified **Industrial Gold** repository state. The architecture has been thoroughly refactored and tested for production readiness. Follow these steps carefully to launch on Render and integrate with Twilio.

---

## STEP 1: Environment Setup (10 minutes)

```bash
# Get the verified repository locally
git clone <your-repo-url>
cd hvac-ai-dispatch

# Create a virtual environment (Python 3.11 Mandatory)
py -3.11 -m venv .venv
.venv\Scripts\activate

# Install dependencies into the project environment
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`. The system uses `python-dotenv` natively to parse these keys upon boot. You **must** provide real values for:

- `GEMINI_API_KEY` (Powers the CrewAI LLM Agents)
- `LANGSMITH_API_KEY` (For observing Agent performance)
- `TWILIO_SID` & `TWILIO_TOKEN` (Required to send real SMS out of `/dispatch`)
- `TWILIO_FROM_PHONE` (Your purchased Twilio number matching "+1...")
- `COMPOSIO_API_KEY` (Required for scheduling calendar slots)
- `OWNER_PHONE` (Where LIFE_SAFETY escalations are forwarded)
- `TECH_PHONE_NUMBER` (Target technician phone)
- `DISPATCH_API_KEY` (Your custom internal secret code to hit the `/dispatch` endpoint)

---

## STEP 2: Local Validation & Smoke Testing

Run the pure logic validation first:

```bash
.venv\Scripts\python.exe tools/test_suite.py
```

### Houston Triage Routing Confirmation

Then, boot the server locally:

```bash
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8888
```

This tests your `.env` parsing and binds the `/sms`, `/whatsapp`, and `/admin` Command Hub safely. The **Neural Warm-up** sequence will execute automatically, pre-initializing the AI brain.

---

## STEP 3: Automation Orchestration (OpenClaw)

This node supports **OpenClaw** for automated QA and outreach.

1. Verify the `openclaw_integration.py` helper is pointing to port **8888**.
2. Run the OpenClaw pre-flight check:
   ```bash
   openclaw run triage-flow --message "AC smells like smoke" --temp 102
   ```

---

## STEP 4: Deploying to Render.com (Production)

This application utilizes an SQLite database and heavy background CrewAI orchestration. **Do not use "Free" tiers**, as they sleep after 15 minutes, killing active dispatch threads.

1. Create a **Web Service** on Render.com.
2. Select **Python 3.11** as your environment.
3. Configure the commands:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**: Copy all secrets into Render's Environment tab.
5. **Disk Mounting**: Secure a persistent disk at `/data` for `dispatch.db`.

---

## STEP 5: Twilio Incoming Webhook Routing

Once deployed, point your Twilio phone number to your Render URL:

1. **SMS:** `https://your-app.onrender.com/sms`
2. **WhatsApp:** `https://your-app.onrender.com/whatsapp`
3. Method: **HTTP POST**.

The system instantly returns a TwiML acknowledgment (< 0.5s), handling the AI triage in a background thread to ensure zero customer waiting.

---

## Launch Protocol & Monitoring (Day 1)

- **Admin Hub:** Monitor `https://your-app.onrender.com/admin` for real-time telemetry.
- **LangSmith:** Use the LangSmith portal to "watch the AI think" and verify tool usage.
- **ROI:** Run `python tools/roi_calculator.py` to confirm financial capture accuracy.

### Common Failure Points

| Error                          | Cause                       | Solution                                 |
| :----------------------------- | :-------------------------- | :--------------------------------------- |
| `Server Crash / Compile Error` | Python environment mismatch | Ensure Render is on Python 3.11          |
| `POST /dispatch == 401`        | Missing `x-api-key` header  | Append your `DISPATCH_API_KEY` header    |
| `Calendar Always Fails`        | Invalid Composio ID         | Verify `COMPOSIO_API_KEY` in environment |
| `First request takes 60s`      | Warm-up not triggered       | Verify `warmup_node()` call in `main.py` |

---

_Confidential Industrial Property — Houston Dispatch Node v1.4.0 (Gold)_
