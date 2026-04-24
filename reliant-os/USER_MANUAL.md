# Reliant JIT OS — User Manual

## Welcome

Welcome to **Reliant JIT OS** — the first autonomous operations platform that configures itself. You don't need to edit `.env` files, read documentation, or understand Docker. Just open your browser, tell the system what you need, and it handles the rest.

---

## What is Reliant JIT OS?

JIT OS is your **24/7 autonomous operations engineer**. It can:

- **Answer questions** about any part of the system
- **Write and deploy code** to modify services
- **Find leads** for your business
- **Monitor and heal** the platform automatically
- **Handle billing and SMS** communications
- **Generate compliance reports** and cost analyses

All through a simple chat interface. No technical knowledge required.

---

## Getting Started

### Step 1: Open the Interface

Navigate to **http://localhost:8085** in your web browser.

You'll see a beautiful dark interface with a **Setup Wizard**.

### Step 2: Enter Your API Keys

The wizard will ask for 5 API keys, one at a time:

| Step | What | Why It's Needed | Where to Get It |
|------|------|-----------------|-----------------|
| 1 | **Google Gemini API Key** | Powers the AI brain | [Google AI Studio](https://aistudio.google.com) |
| 2 | **Stripe Secret Key** | Handles billing and payments | [Stripe Dashboard](https://dashboard.stripe.com) |
| 3 | **Twilio Account SID** | Sends SMS messages to leads | [Twilio Console](https://console.twilio.com) |
| 4 | **Twilio Auth Token** | Secures SMS sending | Same Twilio page as above |
| 5 | **Google Places API Key** | Finds businesses to pitch | [Google Cloud Console](https://console.cloud.google.com) |

> 💡 **Don't have these keys yet?** No problem. The system will prompt you again later. You can skip setup and explore the interface, though the AI won't be able to perform external operations until keys are provided.

### Step 3: Initialize

After entering all keys, click **"Initialize Platform"**.

The system will:
1. ✅ Encrypt and store your keys securely
2. ✅ Restart all platform services
3. ✅ Activate the AI core
4. ✅ Load the main chat interface

This takes about 10-15 seconds. You'll see a loading animation, then the chat dashboard appears.

---

## The Chat Interface

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Reliant OS  │  Mode: Auto           Secure Execution  🔒  │
│  ────────────┼──────────────────────────────────────────────│
│  ⚡ Auto     │                                              │
│  💬 Support  │  🤖 Welcome to Reliant JIT OS!               │
│  💻 Engineer │                                              │
│  💰 Sales    │  I can help you with anything. Just ask!    │
│              │                                              │
│  ────────────┤  You: How do I find leads?                  │
│  📜 History  │                                              │
│  ⚙️ Settings │  🤖 I can scan Google Places for businesses   │
│              │     in your area. Would you like me to        │
│              │     search for HVAC companies in Atlanta?     │
│              │                                              │
│              ├──────────────────────────────────────────────│
│              │  Ask a question or request a change...        │
│              │  [____________________________________] [⚡] │
└───────────────────┬─────────────────────────────────────────┘
                    │  Shift+Enter for new line
```

### Mode Selection

On the left sidebar, you can switch between **4 AI modes**:

#### ⚡ Auto Mode (Default)
The AI automatically detects what you want and chooses the right approach.

**Best for:** Mixed tasks, quick questions, general operations

**Example prompts:**
```
"Show me system status"
"Scale up the Money service"
"Find leads and send them a message"
"Fix the bug in billing"
```

#### 💬 Support Mode
The AI acts as a friendly support agent, explaining how things work.

**Best for:** Learning the platform, understanding features, getting guidance

**Example prompts:**
```
"How does the GrowthEngine work?"
"What's the difference between ComplianceOne and FinOps360?"
"How do I add a new service to the platform?"
"Can you explain the event bus architecture?"
```

#### 💻 Engineer Mode
The AI writes production-quality code with full type hints, error handling, and comments.

**Best for:** Code modifications, new features, bug fixes, refactors

**Example prompts:**
```
"Add a refund endpoint to the Money service"
"Fix the healthcheck in the dashboard"
"Update the pricing tiers for enterprise customers"
"Create a new API endpoint for lead scoring"
"Refactor the billing module to use async database calls"
```

The AI will output Python code inside ` ```python ` blocks, which will be automatically executed and the results shown to you.

#### 💰 Sales Mode
The AI acts as a lead generation specialist, finding prospects and crafting pitches.

**Best for:** Finding leads, generating outreach messages, market research

**Example prompts:**
```
"Find HVAC companies in Atlanta with 4+ star ratings"
"Search for plumbing services in Miami without websites"
"Generate a pitch message for a roofing company"
"Find dentists in Chicago who don't have online booking"
"Create a list of 50 electricians in Houston"
```

The AI will search Google Places, filter by criteria (rating, reviews, website presence), and can even generate personalized SMS pitches.

---

## Common Tasks

### Checking System Status

```
You: "What's the system status?"

🤖: All services are operational:
   • Money (8000): Healthy
   • GrowthEngine (8003): Healthy
   • Orchestrator (9000): Healthy
   • 15 leads found today
   • 3 SMS pitches sent
   • $1,247 MRR active
```

### Modifying Code

```
You: "Add a new endpoint to Money for refunds"

🤖: I'll add a refund endpoint to the Money service.

```python
# Adding /api/refund endpoint to Money/main.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/api/refund")
async def create_refund(charge_id: str, amount: int):
    try:
        refund = stripe.Refund.create(
            charge=charge_id,
            amount=amount
        )
        return {"status": "success", "refund": refund.id}
    except stripe.error.StripeError as e:
        return {"status": "error", "message": str(e)}
```

[Execution Output]: ✅ Added refund endpoint successfully
```

### Finding Leads

```
You: "Find HVAC companies in Atlanta"

🤖: Searching Google Places for HVAC companies in Atlanta...

Found 15 companies:
1. Cool Air HVAC — 4.8★ (124 reviews) — No website
2. Atlanta Heating & Cooling — 4.6★ (89 reviews) — Has website
3. ...

Would you like me to:
• Send SMS pitches to those without websites?
• Generate a mockup website preview for them?
• Add them to the CRM?
```

### Generating Reports

```
You: "Generate a compliance report for SOC2"

🤖: I'll pull data from ComplianceOne and generate a report.

```python
# Fetching compliance data...
report = {
    "framework": "SOC2",
    "date": "2026-04-23",
    "controls_passed": 47,
    "controls_failed": 3,
    "remediation_needed": [
        "CC6.1 - Access Logging (Missing 2 days)",
        "CC7.2 - Vulnerability Scanning (Overdue)",
        "CC8.1 - Change Management (3 unapproved)"
    ]
}
```

[Execution Output]: Report generated: /workspace/reports/soc2-2026-04-23.json
```

---

## Understanding Execution Output

When the AI generates code, you'll see three possible outcomes:

### ✅ Success
```
[Execution Output]: ✅ File updated successfully
                 Service restarted. New endpoint available at /api/refund
```

### ❌ Error
```
[Execution Output]: ❌ ERROR: Module 'stripe' not found
                 Suggestion: Install with `pip install stripe`
```

The AI will usually detect errors and attempt to fix them automatically.

### 🚫 Blocked
```
[Execution Output]: 🚫 BLOCKED: Dangerous command detected: rm -rf /
                 Reason: System protection triggered
```

This means the AI generated code that could harm the system. It was automatically blocked for your safety.

---

## Monitoring & History

### Execution History Panel

Click **"Execution History"** in the left sidebar to see:

- **Timestamp**: When the operation occurred
- **Prompt**: What you asked for
- **Code Hash**: Security verification fingerprint
- **Status**: Success / Error / Blocked / Timeout
- **Duration**: How long it took (milliseconds)

This is useful for:
- Auditing what changes were made
- Debugging failed operations
- Tracking system modifications
- Compliance reporting

### Color Coding

| Color | Meaning | Action Needed |
|-------|---------|---------------|
| 🟢 Green | Success | None — operation completed |
| 🔴 Red | Error | Check the error message, retry |
| 🟡 Yellow | Blocked | Rephrase your request |
| ⚫ Gray | Timeout | Try a simpler request |

---

## Security & Privacy

### Where Are My API Keys Stored?

Your API keys are stored in an **encrypted SQLite database** inside the Reliant OS container. Specifically:

- **Location**: `/secure_data/reliant_os.db` inside the container
- **Encryption**: AES-256 (SQLCipher)
- **Persistence**: Docker volume (survives restarts)
- **Access**: Only the Reliant OS backend can read them

**They are NEVER:**
- ❌ Written to `.env` files
- ❌ Logged to console or files
- ❌ Returned in API responses
- ❌ Sent to external services except the intended API (Gemini, Stripe, etc.)

### Can the AI Delete My Data?

The AI has safety guardrails:

- ✅ **Can modify** application code in `/workspace`
- ✅ **Can read** logs and configuration files
- ✅ **Can create** new files in `/tmp` and `/workspace`
- ❌ **Cannot delete** files outside allowed paths
- ❌ **Cannot format** disks or restart the server
- ❌ **Cannot access** other containers' data directly

### What If the AI Does Something Wrong?

1. **Check Execution History** — see exactly what code was run
2. **Code is version controlled** — all changes are in Git (if configured)
3. **Docker containers are isolated** — one service can't break others
4. **Database has backups** — PostgreSQL volumes are persistent

---

## Tips for Best Results

### Be Specific

✅ **Good:** "Add a POST endpoint to Money/main.py at line 150 that creates Stripe refunds"

❌ **Vague:** "Fix billing"

### Use Engineer Mode for Code

Switch to **💻 Engineer Mode** before asking for code changes. This tells the AI to use the more powerful Gemini Pro model and focus on production-quality output.

### Check History Before Repeating

If something didn't work, check the **Execution History** first. The error message often tells you exactly what went wrong.

### Start Simple

If you're new to the platform:
1. Ask "What can you do?" in Support mode
2. Try a simple status check: "Show system status"
3. Then move to more complex tasks

### Use Sales Mode for Outreach

When finding leads, switch to **💰 Sales Mode**. The AI will:
- Use Google Places API to find businesses
- Filter by quality (ratings, reviews)
- Identify those without websites (best prospects)
- Generate personalized SMS pitches
- Send them via Twilio (with your approval)

---

## Troubleshooting

### "Connection to Core AI failed"

**Problem:** Frontend can't reach backend

**Solutions:**
1. Wait 10 seconds and refresh
2. Check if backend is running: `docker compose ps | grep reliant-os-backend`
3. Check backend logs: `docker compose logs -f reliant-os-backend`

### "Gemini API Key not set"

**Problem:** AI can't function without API keys

**Solutions:**
1. Look for the "Initialize Platform" button or wizard
2. Complete all 5 steps of setup
3. If you already did setup, check that keys were saved: `docker compose logs reliant-os-backend | grep "setup"`

### Code Execution Blocked

**Problem:** AI generated potentially dangerous code

**Solutions:**
1. Read the block reason in the execution output
2. Rephrase your request (e.g., use specific paths)
3. If you're sure it's safe, you can modify the safety rules (advanced)

### High Memory Usage

**Problem:** System running slowly

**Solutions:**
1. Restart the Reliant OS containers: `docker compose restart reliant-os-backend reliant-os-frontend`
2. Check other services: `docker compose ps` — stop non-essential ones
3. Free up host memory: close other applications

### Lost My API Keys

**Problem:** System asking for setup again

**Solutions:**
1. The vault file may have been lost — re-enter keys in the wizard
2. To prevent future loss, backup the volume: `docker cp reliantai-os-backend:/secure_data/reliant_os.db ./backup.db`

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift + Enter` | New line in message |
| `Ctrl + 1` | Switch to Auto mode |
| `Ctrl + 2` | Switch to Support mode |
| `Ctrl + 3` | Switch to Engineer mode |
| `Ctrl + 4` | Switch to Sales mode |
| `Ctrl + H` | Toggle History panel |
| `Ctrl + /` | Focus message input |

---

## Next Steps

Now that you understand the basics, try these common workflows:

### 🎯 Find Your First Lead
1. Switch to **💰 Sales Mode**
2. Type: `"Find HVAC companies in [your city] with 4+ stars and no website"`
3. Review the list
4. Type: `"Send SMS pitch to #1, #3, and #5"`

### 🔧 Fix Your First Bug
1. Switch to **💻 Engineer Mode**
2. Type: `"Show me recent errors in the Money service"`
3. Review the logs
4. Type: `"Fix the [specific error] in Money/main.py"`

### 📊 Generate Your First Report
1. Switch to **⚡ Auto Mode**
2. Type: `"Generate a system health report"`
3. Review the output
4. Type: `"Email this report to my team"`

---

## Support

If you need help:

1. **Use Support Mode** — ask the AI: "How do I...?"
2. **Check Execution History** — see what went wrong
3. **Read the Technical README** — `reliant-os/README.md` for API docs
4. **Check Docker logs** — `docker compose logs -f [service]`

---

**Reliant JIT OS v2.0**  
**Built for:** Non-technical users, operators, business owners  
**No coding required. No configuration files. Just chat.**
